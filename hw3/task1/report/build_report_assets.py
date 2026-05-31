#!/usr/bin/env python3
"""Build reproducible charts and preview montages for the Task 1 report."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "report"
ASSET_DIR = REPORT_DIR / "assets"
LOGS_DIR = ROOT / "logs"


def ensure_dirs() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)


def collect_tensorboard_scalars(input_dir: Path) -> dict[str, dict[int, float]]:
    by_tag: dict[str, dict[int, float]] = {}
    for event_file in sorted(input_dir.rglob("events.out.tfevents.*")):
        accumulator = EventAccumulator(str(event_file), size_guidance={"scalars": 0})
        accumulator.Reload()
        for tag in accumulator.Tags().get("scalars", []):
            values = by_tag.setdefault(tag, {})
            for event in accumulator.Scalars(tag):
                values[event.step] = event.value
    return by_tag


def series(
    by_tag: dict[str, dict[int, float]],
    tag: str,
) -> tuple[np.ndarray, np.ndarray]:
    values = by_tag.get(tag, {})
    steps = np.array(sorted(values), dtype=float)
    return steps, np.array([values[int(step)] for step in steps], dtype=float)


def smooth(values: np.ndarray, window: int) -> np.ndarray:
    if len(values) < 3:
        return values
    window = min(window, len(values))
    kernel = np.ones(window, dtype=float) / window
    return np.convolve(values, kernel, mode="same")


def save_figure(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(ASSET_DIR / name, dpi=220, bbox_inches="tight")
    plt.close(fig)


def copy_previews() -> None:
    figures = ROOT / "docs" / "figures"
    names = [
        "object_a_render_preview.png",
        "background_counter_render_preview.png",
        "object_b_final_preview.png",
        "object_c_preprocessed_preview.png",
        "object_c_magic123_smoke_preview.jpg",
        "object_c_magic123_final_preview.jpg",
        "fusion_walkthrough_preview.png",
    ]
    for name in names:
        source = figures / name
        if source.exists():
            shutil.copy2(source, ASSET_DIR / name)


def plot_2dgs_metrics() -> None:
    runs = [
        (
            "Object A",
            ROOT / "outputs" / "object_a_2dgs" / "object-a-2dgs-full",
            "#2F80ED",
        ),
        (
            "Counter background",
            ROOT / "outputs" / "background_2dgs" / "background-counter-2dgs-full",
            "#E07A5F",
        ),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.1))
    for label, path, color in runs:
        by_tag = collect_tensorboard_scalars(path)
        steps, values = series(by_tag, "train/loss_viewpoint - psnr")
        axes[0].plot(steps, values, marker="o", color=color, label=label)
        steps, values = series(by_tag, "train/loss_viewpoint - l1_loss")
        axes[1].plot(steps, values, marker="o", color=color, label=label)

    axes[0].set_title("2DGS Validation PSNR")
    axes[0].set_ylabel("PSNR (dB)")
    axes[1].set_title("2DGS Validation L1")
    axes[1].set_ylabel("L1 loss")
    for axis in axes:
        axis.set_xlabel("Iteration")
        axis.grid(True, linestyle="--", alpha=0.35)
        axis.legend()
    save_figure(fig, "2dgs_validation_metrics.png")


def plot_object_b_sds() -> None:
    path = ROOT / "outputs" / "object_b_text3d" / "object-b-dreamfusion-sd-full"
    by_tag = collect_tensorboard_scalars(path)
    steps, values = series(by_tag, "train/loss_sds")
    if not len(values):
        return

    fig, ax = plt.subplots(figsize=(8.8, 4.1))
    ax.plot(steps, values, color="#2F80ED", alpha=0.16, linewidth=0.7, label="Raw SDS")
    ax.plot(
        steps,
        smooth(values, 121),
        color="#0B4F9C",
        linewidth=1.5,
        label="121-step moving average",
    )
    ax.set_yscale("symlog", linthresh=1.0)
    ax.set_title("Object B DreamFusion SDS Optimization")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("SDS loss (symlog)")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()
    save_figure(fig, "object_b_sds_curve.png")


def plot_object_c_losses() -> None:
    stages = [
        (
            "Coarse",
            ROOT / "outputs" / "object_c_magic123" / "object-c-magic123-coarse-full",
            "#2F80ED",
        ),
        (
            "Fine",
            ROOT / "outputs" / "object_c_magic123" / "object-c-magic123-fine-full",
            "#E07A5F",
        ),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.1))
    plotted = False
    for label, path, color in stages:
        if not path.exists():
            continue
        by_tag = collect_tensorboard_scalars(path)
        steps, values = series(by_tag, "train/loss")
        if len(values):
            axes[0].plot(steps, values, color=color, linewidth=1.1, label=label)
            plotted = True
        for tag, linestyle in [
            ("train/loss_sds", "-"),
            ("train/loss_zero123", "--"),
        ]:
            steps, values = series(by_tag, tag)
            if len(values) and np.any(values):
                short_tag = tag.rsplit("_", 1)[-1]
                axes[1].plot(
                    steps,
                    values,
                    color=color,
                    linestyle=linestyle,
                    linewidth=1.1,
                    label=f"{label} {short_tag}",
                )

    if not plotted:
        plt.close(fig)
        return

    axes[0].set_title("Object C Magic123 Total Loss")
    axes[0].set_ylabel("Loss")
    axes[1].set_title("Object C Guidance Components")
    axes[1].set_ylabel("Guidance loss")
    for axis in axes:
        axis.set_xlabel("Iteration")
        axis.grid(True, linestyle="--", alpha=0.35)
        handles, _ = axis.get_legend_handles_labels()
        if handles:
            axis.legend()
    save_figure(fig, "object_c_magic123_losses.png")


def load_elapsed_seconds(run_name: str) -> float | None:
    metadata = LOGS_DIR / f"{run_name}.json"
    if not metadata.exists():
        return None
    return float(json.loads(metadata.read_text(encoding="utf-8"))["elapsed_seconds"])


def plot_runtime_comparison() -> None:
    labels = ["Object A\n2DGS", "Background\n2DGS", "Object B\nDreamFusion"]
    values = [4855.769, 1368.519, 3624.218688131 + 35.46129894600017]
    colors = ["#2F80ED", "#3D9970", "#E07A5F"]

    coarse = load_elapsed_seconds("object-c-magic123-coarse-full")
    fine = load_elapsed_seconds("object-c-magic123-fine-full")
    if coarse is not None and fine is not None:
        labels.append("Object C\nMagic123")
        values.append(coarse + fine)
        colors.append("#9467BD")

    fig, ax = plt.subplots(figsize=(8.2, 4.1))
    bars = ax.bar(labels, values, color=colors, width=0.62)
    ax.set_title("Measured End-to-End Stage Runtime")
    ax.set_ylabel("Seconds")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + max(values) * 0.02,
            f"{value:.0f}s",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    ax.set_ylim(0, max(values) * 1.18)
    save_figure(fig, "runtime_comparison.png")


def load_font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        Path("/mnt/c/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def create_preview_montage() -> None:
    candidates = [
        ("Object A: phone multiview + 2DGS", ASSET_DIR / "object_a_render_preview.png"),
        ("Object B: text prompt + SDS", ASSET_DIR / "object_b_final_preview.png"),
        (
            "Object C: single image + Magic123 smoke",
            ASSET_DIR / "object_c_magic123_smoke_preview.jpg",
        ),
        (
            "Background: Mip-NeRF 360 counter + 2DGS",
            ASSET_DIR / "background_counter_render_preview.png",
        ),
    ]
    items = [(label, path) for label, path in candidates if path.exists()]
    if not items:
        return

    width, height = 760, 430
    label_height, gap = 48, 18
    canvas = Image.new(
        "RGB",
        (width * 2 + gap, (height + label_height) * 2 + gap),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    font = load_font(22)
    for index, (label, path) in enumerate(items[:4]):
        row, column = divmod(index, 2)
        x = column * (width + gap)
        y = row * (height + label_height + gap)
        image = Image.open(path).convert("RGB")
        tile = Image.new("RGB", (width, height), "#f5f6f8")
        fitted = ImageOps.contain(image, (width, height), Image.Resampling.LANCZOS)
        tile.paste(fitted, ((width - fitted.width) // 2, (height - fitted.height) // 2))
        canvas.paste(tile, (x, y + label_height))
        draw.text((x + 8, y + 12), label, fill="#222222", font=font)
    canvas.save(ASSET_DIR / "asset_preview_montage.jpg", quality=92)


def write_manifest() -> None:
    manifest = {
        "generated_assets": sorted(path.name for path in ASSET_DIR.iterdir() if path.is_file()),
        "sources": {
            "object_a_2dgs": "outputs/object_a_2dgs/object-a-2dgs-full",
            "background_2dgs": "outputs/background_2dgs/background-counter-2dgs-full",
            "object_b_dreamfusion": "outputs/object_b_text3d/object-b-dreamfusion-sd-full",
            "object_c_magic123_coarse": "outputs/object_c_magic123/object-c-magic123-coarse-full",
            "object_c_magic123_fine": "outputs/object_c_magic123/object-c-magic123-fine-full",
        },
    }
    (ASSET_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    ensure_dirs()
    copy_previews()
    plot_2dgs_metrics()
    plot_object_b_sds()
    plot_object_c_losses()
    plot_runtime_comparison()
    create_preview_montage()
    write_manifest()
    print(f"Report assets written to {ASSET_DIR}")


if __name__ == "__main__":
    main()
