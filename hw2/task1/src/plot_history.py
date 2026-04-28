import argparse
import json
import os
import sys
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import load_config, ensure_dir


def plot_history(history_path, output_dir, experiment_name):
    with open(history_path, "r", encoding="utf-8") as f:
        history = json.load(f)

    epochs = range(1, len(history["train_loss"]) + 1)

    ensure_dir(output_dir)

    plt.figure()
    plt.plot(epochs, history["train_loss"], label="Train Loss")
    plt.plot(epochs, history["val_loss"], label="Val Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title(f"{experiment_name} Loss Curve")
    plt.legend()
    plt.grid(True)
    loss_path = os.path.join(
        output_dir,
        f"{experiment_name}_loss_curve.png"
    )
    plt.savefig(loss_path, dpi=300, bbox_inches="tight")
    plt.close()

    plt.figure()
    plt.plot(epochs, history["train_acc"], label="Train Accuracy")
    plt.plot(epochs, history["val_acc"], label="Val Accuracy")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.title(f"{experiment_name} Accuracy Curve")
    plt.legend()
    plt.grid(True)
    acc_path = os.path.join(
        output_dir,
        f"{experiment_name}_accuracy_curve.png"
    )
    plt.savefig(acc_path, dpi=300, bbox_inches="tight")
    plt.close()

    print("Saved loss curve to:", loss_path)
    print("Saved accuracy curve to:", acc_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        default="configs/resnet18_pretrained.yaml"
    )
    parser.add_argument(
        "--history",
        type=str,
        default=None
    )
    args = parser.parse_args()

    config = load_config(args.config)

    experiment_name = config["experiment_name"]

    if args.history is None:
        history_path = os.path.join(
            config["save"]["result_dir"],
            f"{experiment_name}_history.json"
        )
    else:
        history_path = args.history

    output_dir = os.path.join(
        config["save"]["result_dir"],
        "figures"
    )

    plot_history(
        history_path=history_path,
        output_dir=output_dir,
        experiment_name=experiment_name
    )


if __name__ == "__main__":
    main()