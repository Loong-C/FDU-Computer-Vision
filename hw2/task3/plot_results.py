import json
import os

import matplotlib.pyplot as plt


RUN_DIRS = {
    "CE": "runs/unet_ce_20260428_160024",
    "Dice": "runs/unet_dice_20260428_175418",
    "CE + Dice": "runs/unet_ce_dice_20260428_194303",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def plot_metric(histories, metric_name, ylabel, save_path):
    plt.figure(figsize=(8, 5))

    for label, history in histories.items():
        values = history[metric_name]
        epochs = range(1, len(values) + 1)
        plt.plot(epochs, values, label=label)

    plt.xlabel("Epoch")
    plt.ylabel(ylabel)
    plt.title(ylabel)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def main():
    result_dir = "results"
    ensure_dir(result_dir)

    histories = {}
    summaries = {}

    for label, run_dir in RUN_DIRS.items():
        history_path = os.path.join(run_dir, "history.json")
        summary_path = os.path.join(run_dir, "summary.json")

        histories[label] = load_json(history_path)
        summaries[label] = load_json(summary_path)

    plot_metric(
        histories=histories,
        metric_name="train_loss",
        ylabel="Train Loss",
        save_path=os.path.join(result_dir, "train_loss_comparison.png"),
    )

    plot_metric(
        histories=histories,
        metric_name="val_loss",
        ylabel="Validation Loss",
        save_path=os.path.join(result_dir, "val_loss_comparison.png"),
    )

    plot_metric(
        histories=histories,
        metric_name="val_miou",
        ylabel="Validation mIoU",
        save_path=os.path.join(result_dir, "val_miou_comparison.png"),
    )

    summary_table_path = os.path.join(result_dir, "summary_table.txt")

    with open(summary_table_path, "w", encoding="utf-8") as f:
        f.write("Loss Config\tBest Val mIoU\tBest Epoch\tFinal Val mIoU\tFinal Pixel Acc\n")

        for label, summary in summaries.items():
            f.write(
                f"{label}\t"
                f"{summary['best_val_miou']:.6f}\t"
                f"{summary['best_epoch']}\t"
                f"{summary['final_val_miou']:.6f}\t"
                f"{summary['final_val_pixel_acc']:.6f}\n"
            )

    print("Plots saved to results/")
    print(f"Summary table saved to {summary_table_path}")

    print()
    print("Summary:")
    for label, summary in summaries.items():
        print(
            f"{label}: "
            f"Best Val mIoU = {summary['best_val_miou']:.6f}, "
            f"Best Epoch = {summary['best_epoch']}, "
            f"Final Val mIoU = {summary['final_val_miou']:.6f}"
        )


if __name__ == "__main__":
    main()