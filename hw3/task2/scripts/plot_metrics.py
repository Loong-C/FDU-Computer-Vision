from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt


def read_csv(path: Path) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as file:
        return [{key: float(value) for key, value in row.items() if value} for row in csv.DictReader(file)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot B-only versus ABC ACT metrics.")
    parser.add_argument("--b-run", type=Path, required=True)
    parser.add_argument("--abc-run", type=Path, required=True)
    parser.add_argument("--b-eval", type=Path, required=True)
    parser.add_argument("--abc-eval", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/plots"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    curves = {
        "B-only": read_csv(args.b_run / "metrics.csv"),
        "ABC": read_csv(args.abc_run / "metrics.csv"),
    }
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for label, rows in curves.items():
        steps = [row["step"] for row in rows]
        axes[0].plot(steps, [row["train/l1_loss"] for row in rows], marker="o", label=label)
        validation_rows = [row for row in rows if "validation/loss" in row]
        axes[1].plot(
            [row["step"] for row in validation_rows],
            [row["validation/loss"] for row in validation_rows],
            marker="o",
            label=label,
        )
    axes[0].set_title("Training Action L1 Loss")
    axes[1].set_title("Held-out Validation Loss")
    for axis in axes:
        axis.set_xlabel("Optimization Step")
        axis.grid(alpha=0.3)
        axis.legend()
    fig.tight_layout()
    fig.savefig(args.output_dir / "training_curves.png", dpi=180)
    plt.close(fig)

    evaluations = {}
    for label, eval_dir in {"B-only": args.b_eval, "ABC": args.abc_eval}.items():
        evaluations[label] = json.loads((eval_dir / "zero_shot_metrics.json").read_text(encoding="utf-8"))
    fig, axis = plt.subplots(figsize=(6, 4))
    labels = list(evaluations)
    values = [evaluations[label]["zero_shot/first_action_mae"] for label in labels]
    axis.bar(labels, values, color=["#3b82f6", "#10b981"])
    axis.set_ylabel("MAE")
    axis.set_title("Zero-shot D First-action Error")
    axis.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(args.output_dir / "zero_shot_d_action_error.png", dpi=180)
    plt.close(fig)

    print(f"Wrote plots to {args.output_dir}")


if __name__ == "__main__":
    main()
