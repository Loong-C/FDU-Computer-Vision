from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
IMAGES_ROOT = DOCS_ROOT / "images"
RELEASE_URL = (
    "https://github.com/Loong-C/FDU-Computer-Vision/"
    "releases/tag/hw3-task2-formal-partial-v1"
)
GITHUB_URL = "https://github.com/Loong-C/FDU-Computer-Vision/tree/main/hw3/task2"
SWANLAB_URL = "https://swanlab.cn/@Linkukai/hw3-calvin-act"


def add_page_number(fig: plt.Figure, page: int) -> None:
    fig.text(0.5, 0.025, f"HW3 Task 2 Report Draft  |  Page {page}", ha="center", fontsize=8)


def add_wrapped_text(
    fig: plt.Figure,
    text: str,
    *,
    x: float,
    y: float,
    width: int = 95,
    fontsize: float = 10,
    line_spacing: float = 0.025,
) -> float:
    lines: list[str] = []
    for paragraph in text.splitlines():
        if paragraph:
            lines.extend(textwrap.wrap(paragraph, width=width))
        else:
            lines.append("")
    fig.text(x, y, "\n".join(lines), va="top", fontsize=fontsize)
    return y - line_spacing * len(lines)


def add_table(
    fig: plt.Figure,
    *,
    bbox: tuple[float, float, float, float],
    columns: list[str],
    rows: list[list[str]],
    font_size: float = 8.5,
) -> None:
    ax = fig.add_axes(bbox)
    ax.axis("off")
    table = ax.table(cellText=rows, colLabels=columns, cellLoc="left", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    table.scale(1, 1.4)
    for (row, _), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight="bold")
            cell.set_facecolor("#dbeafe")


def create_report(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(output_path) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.93, "HW3 Task 2", fontsize=24, weight="bold")
        fig.text(
            0.08,
            0.89,
            "Cross-environment Generalization with LeRobot ACT",
            fontsize=16,
            weight="bold",
        )
        fig.text(0.08, 0.84, "Technical report draft", fontsize=12, color="#b91c1c")
        add_wrapped_text(
            fig,
            "Before submission, replace the member placeholders on this page. "
            "The technical content is populated from the verified formal run.",
            x=0.08,
            y=0.80,
        )
        add_table(
            fig,
            bbox=(0.08, 0.62, 0.84, 0.14),
            columns=["Item", "Value"],
            rows=[
                ["Member name(s)", "TODO: fill before submission"],
                ["Student ID(s)", "TODO: fill before submission"],
                ["Responsibility split", "TODO: fill before submission"],
            ],
        )
        fig.text(0.08, 0.56, "Abstract", fontsize=13, weight="bold")
        add_wrapped_text(
            fig,
            "We compare a CALVIN environment-B-only ACT policy against the same "
            "LeRobot ACT architecture trained jointly on environments A, B, and C. "
            "Both models are evaluated zero-shot on unseen environment D using "
            "action error and a small CALVIN simulator rollout. A bounded HTTP-Range "
            "subset keeps the experiment practical without downloading the complete "
            "517 GB archive. Joint A+B+C training reduces D first-action MAE by "
            "17.0% and chunk-action MAE by 11.7%; both policies score 0.0% SR@1 in "
            "the three-sequence D rollout because the trained ACT model is not "
            "language-conditioned.",
            x=0.08,
            y=0.53,
        )
        fig.text(0.08, 0.35, "External links", fontsize=13, weight="bold")
        add_wrapped_text(
            fig,
            f"Public GitHub: {GITHUB_URL}\n"
            f"Model weights: {RELEASE_URL}\n"
            f"SwanLab dashboard: {SWANLAB_URL}",
            x=0.08,
            y=0.32,
            width=105,
            fontsize=9,
        )
        add_page_number(fig, 1)
        pdf.savefig(fig)
        plt.close(fig)

        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.94, "1. Background and Dataset", fontsize=16, weight="bold")
        y = add_wrapped_text(
            fig,
            "This task studies visual distribution shift in embodied policy "
            "learning. We train a visual-action policy on CALVIN environment B and "
            "compare it against a policy trained on mixed environments A+B+C. Both "
            "are tested zero-shot on unseen environment D using sampled-frame action "
            "error and simulator rollout.",
            x=0.08,
            y=0.90,
        )
        y = add_wrapped_text(
            fig,
            "The official A+B+C archive is 517 GB and the D archive is 166 GB. "
            "The repository therefore includes an HTTP-Range downloader that fetches "
            "evenly distributed consecutive frame windows from the official ZIPs, "
            "validates CRC checksums, and preserves the CALVIN directory format.",
            x=0.08,
            y=y - 0.03,
        )
        add_table(
            fig,
            bbox=(0.08, 0.55, 0.84, 0.13),
            columns=["Environment", "Official inclusive frame range"],
            rows=[
                ["B", "0..598909"],
                ["C", "598910..1191338"],
                ["A", "1191339..1795044"],
            ],
        )
        fig.text(0.08, 0.51, "Reported partial-data protocol", fontsize=13, weight="bold")
        add_table(
            fig,
            bbox=(0.08, 0.34, 0.84, 0.13),
            columns=["Split", "Selected frames", "Usage"],
            rows=[
                ["A+B+C training", "2304", "16 x 48-frame windows per environment"],
                ["D evaluation", "768", "16 x 48-frame windows"],
                ["On-disk partial tree", "888 MB", "No full archive downloaded"],
            ],
        )
        add_wrapped_text(
            fig,
            "After stride 3 and a 90/10 train-validation split, B-only training "
            "uses 230 samples and A+B+C training uses 691 samples.",
            x=0.08,
            y=0.28,
        )
        add_page_number(fig, 2)
        pdf.savefig(fig)
        plt.close(fig)

        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.94, "2. Method and Experiment Settings", fontsize=16, weight="bold")
        add_wrapped_text(
            fig,
            "ACT predicts a chunk of future actions from the current image and robot "
            "state. A short action sequence can reduce sensitivity to single-frame "
            "noise and provide temporally coherent control. We use the upstream "
            "LeRobot ACTPolicy from v0.5.1. Both conditions share exactly the same "
            "architecture and optimizer settings; only the selected training scenes differ.",
            x=0.08,
            y=0.90,
        )
        add_table(
            fig,
            bbox=(0.08, 0.48, 0.84, 0.30),
            columns=["Item", "Value", "Item", "Value"],
            rows=[
                ["Policy", "ACT", "Vision backbone", "ResNet-18"],
                ["Image size", "128", "Action chunk size", "20"],
                ["Model dimension", "256", "Encoder / decoder", "3 / 1"],
                ["VAE latent size", "32", "Batch size", "4"],
                ["Optimizer", "AdamW", "Learning rate", "1e-5"],
                ["Weight decay", "1e-4", "Training steps", "5000"],
                ["Validation interval", "250", "GPU", "RTX 4060 Ti 8 GB"],
            ],
        )
        fig.text(0.08, 0.42, "Evaluation metrics", fontsize=13, weight="bold")
        add_wrapped_text(
            fig,
            "We report training Action L1 loss, held-out validation loss, unseen-D "
            "first-action MAE, unseen-D chunk-action MAE, and CALVIN simulator rollout "
            "success. The rollout wraps each ACT checkpoint as a CALVIN reset/step "
            "policy and projects the gripper action back to the required -1/1 space.",
            x=0.08,
            y=0.39,
        )
        add_page_number(fig, 3)
        pdf.savefig(fig)
        plt.close(fig)

        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.94, "3. Training Curves", fontsize=16, weight="bold")
        image = plt.imread(IMAGES_ROOT / "formal_training_curves.jpg")
        ax = fig.add_axes((0.05, 0.37, 0.90, 0.53))
        ax.imshow(image)
        ax.axis("off")
        add_wrapped_text(
            fig,
            "The mixed A+B+C condition is noisier and has a higher held-out "
            "validation loss because it fits three visual scenes. Both conditions "
            "show decreasing training and validation trends over 5000 steps.",
            x=0.08,
            y=0.30,
        )
        add_page_number(fig, 4)
        pdf.savefig(fig)
        plt.close(fig)

        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.94, "4. Zero-shot D Results and Analysis", fontsize=16, weight="bold")
        add_table(
            fig,
            bbox=(0.08, 0.77, 0.84, 0.11),
            columns=["Training scenes", "Validation L1", "D first-action MAE", "D chunk MAE"],
            rows=[
                ["B only", "0.324629", "0.226251", "0.259475"],
                ["A+B+C", "0.386954", "0.187712", "0.229145"],
            ],
        )
        image = plt.imread(IMAGES_ROOT / "formal_zero_shot_d_action_error.jpg")
        ax = fig.add_axes((0.17, 0.40, 0.66, 0.33))
        ax.imshow(image)
        ax.axis("off")
        add_wrapped_text(
            fig,
            "Joint A+B+C training lowers first-action MAE by 17.0% and chunk-action "
            "MAE by 11.7% relative to B-only training. The chunk-level improvement "
            "is smaller because longer-horizon predictions accumulate more uncertainty "
            "under visual shift. However, the A+B+C model still improves at chunk "
            "level, indicating that the 20-step action chunks remain robust on sampled D frames.",
            x=0.08,
            y=0.34,
        )
        fig.text(0.08, 0.20, "CALVIN D simulator rollout", fontsize=13, weight="bold")
        add_table(
            fig,
            bbox=(0.08, 0.08, 0.84, 0.10),
            columns=["Training scenes", "D sequences", "Avg solved", "SR@1", "SR@5"],
            rows=[
                ["B only", "3", "0.0", "0.0%", "0.0%"],
                ["A+B+C", "3", "0.0", "0.0%", "0.0%"],
            ],
            font_size=8,
        )
        add_page_number(fig, 5)
        pdf.savefig(fig)
        plt.close(fig)

        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.94, "5. Reproducibility and Limitations", fontsize=16, weight="bold")
        y = add_wrapped_text(
            fig,
            "Reproduction command:\n"
            r".\scripts\bootstrap.ps1" "\n"
            r".\scripts\run_partial_formal.ps1" "\n"
            r".\scripts\bootstrap.ps1 -WithCalvinRollout" "\n"
            r".\scripts\run_zero_shot_d_rollout.ps1 -MaxSequences 3 -EpisodeLength 360 -Device cuda",
            x=0.08,
            y=0.90,
            width=108,
        )
        y = add_wrapped_text(
            fig,
            "The wrapper downloads the bounded subset, trains both policies using "
            "the same config, resumes from latest.pt when present, evaluates D action "
            "error, and regenerates plots. The rollout command deploys the saved "
            "checkpoints in the unseen D simulator with the official 360-step "
            "per-subtask horizon. Data, caches, and outputs remain under ignored "
            "task2 directories.",
            x=0.08,
            y=y - 0.03,
        )
        y = add_wrapped_text(
            fig,
            "Limitations: this resource-aware experiment reports action error on "
            "sampled official D frames and simulator success on three generated D "
            "sequences, not the full 1000-sequence CALVIN benchmark. The ACT policy "
            "is not language-conditioned, so the rollout success rate verifies "
            "deployment rather than strong language-guided task completion.",
            x=0.08,
            y=y - 0.03,
        )
        fig.text(0.08, y - 0.04, "Checkpoint downloads", fontsize=13, weight="bold")
        add_wrapped_text(
            fig,
            f"Release page: {RELEASE_URL}\n"
            "B-only SHA256: 58AFAE052EF2CE029F92C9258E1B5012A9C44FAC5753C1C8330B7D196A976131\n"
            "A+B+C SHA256: 1B1F182E61026929F0A5FFDC5EE096D15E4771FEBD111D9EFE3D88BC4A9ADCFF",
            x=0.08,
            y=y - 0.08,
            width=108,
            fontsize=8.5,
        )
        add_wrapped_text(
            fig,
            f"SwanLab dashboard: {SWANLAB_URL}\nPublic GitHub: {GITHUB_URL}",
            x=0.08,
            y=0.24,
            width=108,
            fontsize=9,
        )
        add_page_number(fig, 6)
        pdf.savefig(fig)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the HW3 Task 2 PDF report draft.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DOCS_ROOT / "HW3_Task2_Report_Draft.pdf",
    )
    args = parser.parse_args()
    create_report(args.output)
    print(f"Wrote report draft to {args.output}")


if __name__ == "__main__":
    main()
