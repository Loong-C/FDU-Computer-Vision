from __future__ import annotations

import json
import shutil
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "report" / "assets"


def copy_asset(source: str, target: str | None = None) -> None:
    source_path = ROOT / source
    target_path = ASSET_DIR / (target or source_path.name)
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    shutil.copy2(source_path, target_path)


def build_fusion_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(14, 5.4))
    ax.set_xlim(0, 14)
    ax.set_ylim(-0.25, 5.4)
    ax.axis("off")

    groups = [
        (0.35, 3.75, 3.0, 1.05, "#dbeafe", "Object A: real capture", "Phone multiview + COLMAP + 2DGS"),
        (0.35, 2.45, 3.0, 1.05, "#fee2e2", "Object B: text-to-3D", "Prompt + threestudio + SD SDS"),
        (0.35, 1.15, 3.0, 1.05, "#fef3c7", "Object C: image-to-3D", "Foreground RGBA + Magic123"),
        (0.35, -0.15, 3.0, 1.05, "#dcfce7", "Background: counter scene", "Mip-NeRF 360 + 2DGS"),
    ]
    for x, y, w, h, color, title, subtitle in groups:
        box = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.04,rounding_size=0.08",
            linewidth=1.2,
            edgecolor="#334155",
            facecolor=color,
        )
        ax.add_patch(box)
        ax.text(x + 0.15, y + 0.69, title, fontsize=11, fontweight="bold", color="#0f172a")
        ax.text(x + 0.15, y + 0.30, subtitle, fontsize=9.5, color="#334155")

    middle = FancyBboxPatch(
        (5.0, 1.44),
        3.65,
        2.08,
        boxstyle="round,pad=0.06,rounding_size=0.10",
        linewidth=1.4,
        edgecolor="#334155",
        facecolor="#ede9fe",
    )
    ax.add_patch(middle)
    ax.text(6.825, 2.99, "Unified exchange representation", ha="center", fontsize=12, fontweight="bold")
    ax.text(6.825, 2.53, "Textured / colored mesh", ha="center", fontsize=15, fontweight="bold", color="#6d28d9")
    ax.text(6.825, 2.08, "2DGS surfaces: bounded TSDF extraction", ha="center", fontsize=9.5)
    ax.text(6.825, 1.73, "AIGC assets: OBJ export from generation frameworks", ha="center", fontsize=9.5)

    right = FancyBboxPatch(
        (10.2, 1.44),
        3.45,
        2.08,
        boxstyle="round,pad=0.06,rounding_size=0.10",
        linewidth=1.4,
        edgecolor="#334155",
        facecolor="#e0f2fe",
    )
    ax.add_patch(right)
    ax.text(11.925, 2.98, "Blender composition", ha="center", fontsize=12, fontweight="bold")
    ax.text(11.925, 2.51, "Scale + pose + camera path", ha="center", fontsize=11)
    ax.text(11.925, 2.08, "Occlusion-aware mesh rendering", ha="center", fontsize=10)
    ax.text(11.925, 1.72, "180 frames, 640 x 480, 30 fps", ha="center", fontsize=10)

    for y in [4.275, 2.975, 1.675, 0.375]:
        arrow = FancyArrowPatch(
            (3.38, y),
            (4.94, 2.48),
            arrowstyle="-|>",
            mutation_scale=15,
            linewidth=1.3,
            color="#64748b",
            connectionstyle="arc3,rad=0.0",
        )
        ax.add_patch(arrow)
    ax.add_patch(
        FancyArrowPatch(
            (8.72, 2.48),
            (10.14, 2.48),
            arrowstyle="-|>",
            mutation_scale=18,
            linewidth=1.7,
            color="#475569",
        )
    )
    ax.set_title("Task 1 fusion pipeline: heterogeneous assets are unified as meshes before rendering", fontsize=15)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "task1_fusion_pipeline.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_zero_shot_chart() -> None:
    labels = ["First-action MAE", "Chunk-action MAE"]
    b_only = np.array([0.22625148172179857, 0.2594750017548601])
    abc = np.array([0.18771157413721085, 0.22914512909483165])
    improvement = (b_only - abc) / b_only * 100

    x = np.arange(len(labels))
    width = 0.34
    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    bars_b = ax.bar(x - width / 2, b_only, width, label="B-only", color="#3b82f6")
    bars_abc = ax.bar(x + width / 2, abc, width, label="A+B+C", color="#10b981")
    ax.set_ylabel("Mean absolute error (lower is better)")
    ax.set_title("Zero-shot CALVIN environment D: action-error comparison")
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 0.30)
    ax.grid(axis="y", alpha=0.28)
    ax.legend()
    for bars in [bars_b, bars_abc]:
        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.006,
                f"{bar.get_height():.4f}",
                ha="center",
                va="bottom",
                fontsize=9.5,
            )
    for index, percent in enumerate(improvement):
        ax.text(index, 0.285, f"A+B+C improves {percent:.1f}%", ha="center", fontsize=10, fontweight="bold")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "task2_zero_shot_grouped.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def _load_square_image(path: Path, crop_box: tuple[int, int, int, int] | None = None) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if crop_box is not None:
        image = image.crop(crop_box)
    return ImageOps.fit(image, (800, 800), method=Image.Resampling.LANCZOS, centering=(0.5, 0.55))


def _load_colored_triangle_ply(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with path.open("rb") as stream:
        header = []
        while True:
            line = stream.readline().decode("ascii").strip()
            header.append(line)
            if line == "end_header":
                break
        vertex_count = int(next(line.split()[2] for line in header if line.startswith("element vertex ")))
        face_count = int(next(line.split()[2] for line in header if line.startswith("element face ")))
        vertex_dtype = np.dtype(
            [("x", "<f8"), ("y", "<f8"), ("z", "<f8"), ("r", "u1"), ("g", "u1"), ("b", "u1")]
        )
        vertices = np.fromfile(stream, dtype=vertex_dtype, count=vertex_count)
        face_dtype = np.dtype([("count", "u1"), ("indices", "<u4", (3,))])
        faces = np.fromfile(stream, dtype=face_dtype, count=face_count)
    if not np.all(faces["count"] == 3):
        raise ValueError(f"Expected a triangle-only PLY mesh: {path}")
    positions = np.column_stack([vertices["x"], vertices["y"], vertices["z"]])
    colors = np.column_stack([vertices["r"], vertices["g"], vertices["b"]]).astype(float) / 255.0
    return positions, colors, faces["indices"]


def _render_colored_mesh_view(
    positions: np.ndarray,
    colors: np.ndarray,
    faces: np.ndarray,
    camera_direction: np.ndarray,
    right_direction: np.ndarray,
    up_direction: np.ndarray,
) -> Image.Image:
    triangles = positions[faces]
    base_colors = colors[faces].mean(axis=1)
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-8)
    light_direction = np.array([-0.45, -0.55, 0.70])
    light_direction /= np.linalg.norm(light_direction)
    shading = 0.72 + 0.28 * np.abs(normals @ light_direction)
    face_colors = np.clip(base_colors * shading[:, None], 0.0, 1.0)

    projected = np.stack([triangles @ right_direction, triangles @ up_direction], axis=2)
    depth = triangles @ camera_direction
    order = np.argsort(depth.mean(axis=1))

    fig = plt.figure(figsize=(4.0, 4.0))
    ax = fig.add_axes([0.01, 0.01, 0.98, 0.98])
    ax.add_collection(PolyCollection(projected[order], facecolors=face_colors[order], edgecolors="none"))
    ax.set_aspect("equal")
    ax.set_facecolor("#eef2f5")
    ax.autoscale_view()
    ax.margins(0.04)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    with BytesIO() as buffer:
        fig.savefig(buffer, format="png", dpi=180, facecolor="#eef2f5")
        plt.close(fig)
        buffer.seek(0)
        return Image.open(buffer).convert("RGB")


def _build_object_a_mesh_views() -> list[Image.Image]:
    mesh_path = (
        ROOT
        / "task1"
        / "outputs"
        / "object_a_2dgs"
        / "object-a-2dgs-full"
        / "train"
        / "ours_30000"
        / "fuse_post.ply"
    )
    positions, colors, faces = _load_colored_triangle_ply(mesh_path)

    # TSDF extraction contains nearby floor fragments. Keep the figurine region and
    # trim the outer floor strip while preserving the visible reconstruction residue.
    minimum = np.array([0.02, -0.16, 1.76])
    maximum = np.array([1.16, 2.12, 3.22])
    inside = np.all((positions >= minimum) & (positions <= maximum), axis=1)
    faces = faces[np.all(inside[faces], axis=1)]
    centroids = positions[faces].mean(axis=1)
    floor_strip = (centroids[:, 1] > 1.94) & ((centroids[:, 0] < 0.34) | (centroids[:, 0] > 0.86))
    faces = faces[~floor_strip]

    views = [
        (np.array([0.0, 0.0, -1.0]), np.array([1.0, 0.0, 0.0]), np.array([0.0, -1.0, 0.0])),
        (np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0]), np.array([0.0, -1.0, 0.0])),
        (np.array([0.0, 0.0, 1.0]), np.array([-1.0, 0.0, 0.0]), np.array([0.0, -1.0, 0.0])),
    ]
    return [_render_colored_mesh_view(positions, colors, faces, *view) for view in views]


def build_task1_triviews() -> None:
    object_b_dir = (
        ROOT
        / "task1"
        / "outputs"
        / "object_b_text3d"
        / "object-b-dreamfusion-sd-full"
        / "object-b-dreamfusion-sd-full"
        / "full@20260531-180217"
        / "save"
        / "it10000-test"
    )
    object_c_dir = (
        ROOT
        / "task1"
        / "outputs"
        / "object_c_magic123"
        / "object-c-magic123-fine-full"
        / "results"
        / "images"
    )

    object_a = _build_object_a_mesh_views()
    object_b = []
    for index in (0, 30, 60):
        source = object_b_dir / f"{index}.png"
        with Image.open(source) as image:
            object_b.append(_load_square_image(source, (0, 0, image.height, image.height)))
    object_c = [
        _load_square_image(object_c_dir / f"object-c-magic123-fine-full_ep0005_{index:04d}_lambertian.jpg")
        for index in (0, 25, 50)
    ]

    rows = [
        ("A: cropped PLY mesh", object_a),
        ("B: text-to-3D", object_b),
        ("C: image-to-3D", object_c),
    ]
    fig, axes = plt.subplots(3, 3, figsize=(11.5, 10.2))
    for row_index, (row_label, images) in enumerate(rows):
        for column_index, image in enumerate(images):
            ax = axes[row_index, column_index]
            ax.imshow(image)
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_color("#cbd5e1")
                spine.set_linewidth(1.2)
            if row_index == 0:
                ax.set_title(f"Representative view {column_index + 1}", fontsize=12, fontweight="bold")
            if column_index == 0:
                ax.set_ylabel(row_label, fontsize=11, fontweight="bold", labelpad=12)
    fig.suptitle(
        "Task 1 representative three-view comparison from formal outputs",
        fontsize=15,
        fontweight="bold",
        y=0.995,
    )
    fig.tight_layout(rect=(0.02, 0.01, 1, 0.975))
    fig.savefig(ASSET_DIR / "task1_method_triviews.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def write_manifest() -> None:
    files = sorted(path.name for path in ASSET_DIR.iterdir() if path.is_file())
    manifest = {
        "generated_by": "report/build_report_assets.py",
        "assets": files,
        "task2_zero_shot_values": {
            "b_only": {"first_action_mae": 0.22625148172179857, "chunk_action_mae": 0.2594750017548601},
            "abc": {"first_action_mae": 0.18771157413721085, "chunk_action_mae": 0.22914512909483165},
        },
    }
    (ASSET_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    copy_asset("task1/report/assets/asset_preview_montage.jpg")
    copy_asset("task1/report/assets/2dgs_validation_metrics.png")
    copy_asset("task1/report/assets/object_b_sds_curve.png")
    copy_asset("task1/report/assets/object_c_magic123_losses.png")
    copy_asset("task1/report/assets/fusion_walkthrough_preview.png")
    copy_asset("task1/report/assets/runtime_comparison.png")
    copy_asset("task2/docs/images/formal_training_curves.png")
    build_fusion_pipeline()
    build_task1_triviews()
    build_zero_shot_chart()
    write_manifest()
    print(f"Prepared report assets under {ASSET_DIR}")


if __name__ == "__main__":
    main()
