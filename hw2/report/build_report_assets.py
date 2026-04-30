from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "report" / "assets"


def ensure_dirs() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)


def copy_asset(src: str, dst_name: str) -> None:
    src_path = ROOT / src
    dst_path = ASSET_DIR / dst_name
    if not src_path.exists():
        raise FileNotFoundError(src_path)
    shutil.copy2(src_path, dst_path)


def load_json(path: str) -> dict:
    with open(ROOT / path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(path: str) -> list[dict[str, str]]:
    with open(ROOT / path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [{k.strip(): v for k, v in row.items()} for row in reader]


def plot_task1_grid() -> None:
    rows = load_csv("task1/results/experiment_summary.csv")
    rows = [r for r in rows if r["experiment_name"].startswith("resnet18_grid_ep15")]

    points = []
    for row in rows:
        points.append(
            (
                float(row["backbone_lr"]),
                float(row["classifier_lr"]),
                float(row["test_acc"]),
                row["experiment_name"],
            )
        )

    backbones = sorted({p[0] for p in points})
    classifiers = sorted({p[1] for p in points})
    values = [[None for _ in classifiers] for _ in backbones]

    for b_lr, c_lr, acc, _ in points:
        values[backbones.index(b_lr)][classifiers.index(c_lr)] = acc

    fig, ax = plt.subplots(figsize=(7, 4.8))
    matrix = [[v if v is not None else 0.0 for v in row] for row in values]
    im = ax.imshow(matrix, cmap="YlGnBu", vmin=0.82, vmax=0.89)

    ax.set_xticks(range(len(classifiers)))
    ax.set_xticklabels([f"{x:g}" for x in classifiers])
    ax.set_yticks(range(len(backbones)))
    ax.set_yticklabels([f"{x:g}" for x in backbones])
    ax.set_xlabel("Classifier learning rate")
    ax.set_ylabel("Backbone learning rate")
    ax.set_title("Task 1 Hyperparameter Search: Test Accuracy")

    for i, row in enumerate(values):
        for j, value in enumerate(row):
            if value is not None:
                ax.text(j, i, f"{value:.4f}", ha="center", va="center", fontsize=9)

    fig.colorbar(im, ax=ax, label="Test Acc")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "task1_hparam_heatmap.png", dpi=220)
    plt.close(fig)


def plot_task1_summary() -> None:
    labels = ["Pretrained\nResNet-18", "Scratch\nResNet-18", "Pretrained\nSE-ResNet-18"]
    values = [0.8724, 0.4424, 0.8621]
    colors = ["#2F80ED", "#E07A5F", "#3D9970"]

    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    bars = ax.bar(labels, values, color=colors, width=0.58)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Test Accuracy")
    ax.set_title("Task 1 Core Experiment Comparison")
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.02,
            f"{value:.4f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    fig.tight_layout()
    fig.savefig(ASSET_DIR / "task1_core_comparison.png", dpi=220)
    plt.close(fig)


def plot_task2_curves() -> None:
    rows = load_csv("task2/runs/detect/visdrone_yolov8n_e50/results.csv")

    def series(column: str) -> list[float]:
        return [float(row[column]) for row in rows if row.get(column, "") != ""]

    epochs = [int(float(row["epoch"])) + 1 for row in rows]
    train_box = series("train/box_loss")
    val_box = series("val/box_loss")
    map50 = series("metrics/mAP50(B)")
    map5095 = series("metrics/mAP50-95(B)")
    precision = series("metrics/precision(B)")
    recall = series("metrics/recall(B)")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    axes[0].plot(epochs, train_box, label="Train box loss", color="#2F80ED")
    axes[0].plot(epochs, val_box, label="Val box loss", color="#E07A5F")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].set_title("YOLOv8n Loss")
    axes[0].grid(True, linestyle="--", alpha=0.35)
    axes[0].legend()

    axes[1].plot(epochs, map50, label="mAP50", color="#3D9970")
    axes[1].plot(epochs, map5095, label="mAP50-95", color="#9467BD")
    axes[1].plot(epochs, precision, label="Precision", color="#FFB000", alpha=0.9)
    axes[1].plot(epochs, recall, label="Recall", color="#555555", alpha=0.9)
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Metric")
    axes[1].set_title("Validation Metrics")
    axes[1].grid(True, linestyle="--", alpha=0.35)
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(ASSET_DIR / "task2_training_curves.png", dpi=220)
    plt.close(fig)


def make_occlusion_montage() -> None:
    frame_paths = [
        ROOT / "task2/outputs/frames/occlusion/frame_000586.jpg",
        ROOT / "task2/outputs/frames/occlusion/frame_000587.jpg",
        ROOT / "task2/outputs/frames/occlusion/frame_000588.jpg",
        ROOT / "task2/outputs/frames/occlusion/frame_000589.jpg",
    ]
    images = [Image.open(p).convert("RGB") for p in frame_paths]
    thumb_w = 560
    thumbs = []

    for image in images:
        ratio = thumb_w / image.width
        thumb_h = int(image.height * ratio)
        thumbs.append(image.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS))

    gap = 16
    label_h = 40
    total_w = thumb_w * 2 + gap
    total_h = (thumbs[0].height + label_h) * 2 + gap
    canvas = Image.new("RGB", (total_w, total_h), "white")
    draw = ImageDraw.Draw(canvas)

    for idx, thumb in enumerate(thumbs):
        row = idx // 2
        col = idx % 2
        x = col * (thumb_w + gap)
        y = row * (thumb.height + label_h + gap)
        canvas.paste(thumb, (x, y + label_h))
        draw.text((x + 10, y + 10), f"Frame {586 + idx}", fill=(20, 20, 20))

    canvas.save(ASSET_DIR / "task2_occlusion_montage.jpg", quality=92)


def make_line_count_schematic() -> None:
    width, height = 1200, 520
    canvas = Image.new("RGB", (width, height), "#f7f8fb")
    draw = ImageDraw.Draw(canvas)

    try:
        font_title = ImageFont.truetype("arial.ttf", 34)
        font = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        font_title = font = font_small = ImageFont.load_default()

    line_x = width // 2
    draw.line((line_x, 70, line_x, height - 70), fill="#d62728", width=6)
    draw.text((40, 24), "Line-crossing counting logic", fill="#222222", font=font_title)
    draw.text((line_x + 16, 72), "virtual line", fill="#d62728", font=font_small)

    tracks = [
        ((160, 170), (680, 170), "#2F80ED", "ID 7 counted"),
        ((190, 310), (745, 360), "#3D9970", "ID 12 counted"),
        ((900, 235), (470, 260), "#9467BD", "ID 19 counted once"),
    ]

    for start, end, color, label in tracks:
        draw.line((start[0], start[1], end[0], end[1]), fill=color, width=5)
        draw.ellipse((start[0] - 12, start[1] - 12, start[0] + 12, start[1] + 12), fill=color)
        draw.ellipse((end[0] - 16, end[1] - 16, end[0] + 16, end[1] + 16), outline=color, width=5)
        draw.text((min(start[0], end[0]) + 20, min(start[1], end[1]) - 38), label, fill="#222222", font=font_small)

    draw.rectangle((720, 52, 1130, 125), fill="#111111")
    draw.text((745, 74), "Line Crossing Count: 1", fill="#ffdf5d", font=font)
    draw.text(
        (40, height - 58),
        "A target is counted when the same Tracking ID moves from one side of the line to the other; each ID is counted at most once.",
        fill="#333333",
        font=font_small,
    )

    canvas.save(ASSET_DIR / "task2_line_count_logic.png")


def main() -> None:
    ensure_dirs()

    copies = {
        "task1/results/figures/resnet18_pretrained_baseline_loss_curve.png": "task1_baseline_loss_curve.png",
        "task1/results/figures/resnet18_pretrained_baseline_accuracy_curve.png": "task1_baseline_accuracy_curve.png",
        "task1/results/figures/resnet18_scratch_ablation_accuracy_curve.png": "task1_scratch_accuracy_curve.png",
        "task1/results/figures/resnet18_se_pretrained_accuracy_curve.png": "task1_se_accuracy_curve.png",
        "task2/runs/detect/visdrone_yolov8n_e50/results.png": "task2_yolo_results.png",
        "task2/runs/detect/visdrone_yolov8n_e50/BoxPR_curve.png": "task2_box_pr_curve.png",
        "task2/runs/detect/visdrone_yolov8n_e50/val_batch0_pred.jpg": "task2_val_prediction.jpg",
        "task3/results/train_loss_comparison.png": "task3_train_loss_comparison.png",
        "task3/results/val_loss_comparison.png": "task3_val_loss_comparison.png",
        "task3/results/val_miou_comparison.png": "task3_val_miou_comparison.png",
        "task3/results/predictions/prediction_5.png": "task3_prediction_example.png",
    }

    for src, dst in copies.items():
        copy_asset(src, dst)

    plot_task1_grid()
    plot_task1_summary()
    plot_task2_curves()
    make_occlusion_montage()
    make_line_count_schematic()

    print(f"Report assets written to {ASSET_DIR}")


if __name__ == "__main__":
    main()
