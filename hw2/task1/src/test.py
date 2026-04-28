import argparse
import os
import sys
import json
import torch
import torch.nn as nn

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.datasets import build_dataloaders
from src.models import build_model
from src.engine import evaluate
from src.utils import load_config, get_device, ensure_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        default="configs/resnet18_pretrained.yaml"
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None
    )
    args = parser.parse_args()

    config = load_config(args.config)
    device = get_device(config["device"])

    print("Using device:", device)

    _, _, test_loader, class_names = build_dataloaders(
        root=config["data"]["root"],
        image_size=config["data"]["image_size"],
        batch_size=config["data"]["batch_size"],
        num_workers=config["data"]["num_workers"],
        val_ratio=config["data"]["val_ratio"],
        seed=config["seed"]
    )

    model = build_model(
        model_name=config["model"]["name"],
        num_classes=config["data"]["num_classes"],
        pretrained=False,
        attention=config["model"]["attention"]
    )

    if args.checkpoint is None:
        checkpoint_path = os.path.join(
            config["save"]["checkpoint_dir"],
            f"{config['experiment_name']}_best.pth"
        )
    else:
        checkpoint_path = args.checkpoint

    print("Loading checkpoint:", checkpoint_path)

    checkpoint = torch.load(
        checkpoint_path,
        map_location=device
    )

    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()

    test_loss, test_acc = evaluate(
        model=model,
        dataloader=test_loader,
        criterion=criterion,
        device=device,
        desc="Test"
    )

    print(f"Test Loss: {test_loss:.4f}")
    print(f"Test Acc: {test_acc:.4f}")

    result_dir = config["save"]["result_dir"]
    ensure_dir(result_dir)

    summary = {
        "experiment_name": config["experiment_name"],
        "model": config["model"]["name"],
        "pretrained": config["model"]["pretrained"],
        "attention": config["model"]["attention"],

        "epochs": config["train"]["epochs"],
        "optimizer": config["train"]["optimizer"],
        "backbone_lr": config["train"]["backbone_lr"],
        "classifier_lr": config["train"]["classifier_lr"],
        "weight_decay": config["train"]["weight_decay"],
        "batch_size": config["data"]["batch_size"],
        "image_size": config["data"]["image_size"],

        "num_classes": len(class_names),
        "best_val_acc": checkpoint.get("best_val_acc", None),
        "test_loss": test_loss,
        "test_acc": test_acc,
        "checkpoint": checkpoint_path
    }

    summary_path = os.path.join(
        result_dir,
        f"{config['experiment_name']}_summary.json"
    )

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)

    print("Summary saved to:", summary_path)


if __name__ == "__main__":
    main()