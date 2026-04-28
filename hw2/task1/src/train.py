import argparse
import os
import sys
import json
import torch
import torch.nn as nn
import torch.optim as optim

from torch.optim.lr_scheduler import CosineAnnealingLR

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.datasets import build_dataloaders
from src.models import build_model, build_param_groups
from src.engine import train_one_epoch, evaluate
from src.utils import set_seed, load_config, ensure_dir, get_device


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        default="configs/resnet18_pretrained.yaml"
    )
    args = parser.parse_args()

    config = load_config(args.config)

    set_seed(config["seed"])


    if torch.cuda.is_available():
        print("CUDA device name:", torch.cuda.get_device_name(0))

    device = get_device(config["device"])
    print("Using device:", device)

    train_loader, val_loader, test_loader, class_names = build_dataloaders(
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
        pretrained=config["model"]["pretrained"],
        attention=config["model"]["attention"]
    )

    model = model.to(device)

    criterion = nn.CrossEntropyLoss()

    param_groups = build_param_groups(
        model,
        backbone_lr=config["train"]["backbone_lr"],
        classifier_lr=config["train"]["classifier_lr"],
        weight_decay=config["train"]["weight_decay"]
    )

    optimizer_name = config["train"]["optimizer"].lower()

    if optimizer_name == "adamw":
        optimizer = optim.AdamW(param_groups)
    elif optimizer_name == "sgd":
        optimizer = optim.SGD(
            param_groups,
            momentum=0.9
        )
    else:
        raise ValueError(f"Unsupported optimizer: {optimizer_name}")

    scheduler = None

    if config["scheduler"]["name"].lower() == "cosine":
        scheduler = CosineAnnealingLR(
            optimizer,
            T_max=config["train"]["epochs"],
            eta_min=config["scheduler"]["min_lr"]
        )

    checkpoint_dir = config["save"]["checkpoint_dir"]
    result_dir = config["save"]["result_dir"]

    ensure_dir(checkpoint_dir)
    ensure_dir(result_dir)

    experiment_name = config["experiment_name"]

    best_val_acc = 0.0

    history = {
        "train_loss": [],
        "train_acc": [],
        "val_loss": [],
        "val_acc": []
    }

    for epoch in range(1, config["train"]["epochs"] + 1):
        print(f"\nEpoch [{epoch}/{config['train']['epochs']}]")

        train_loss, train_acc = train_one_epoch(
            model=model,
            dataloader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device
        )

        val_loss, val_acc = evaluate(
            model=model,
            dataloader=val_loader,
            criterion=criterion,
            device=device,
            desc="Val"
        )

        if scheduler is not None:
            scheduler.step()

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        print(
            f"Train Loss: {train_loss:.4f} | "
            f"Train Acc: {train_acc:.4f} | "
            f"Val Loss: {val_loss:.4f} | "
            f"Val Acc: {val_acc:.4f}"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc

            checkpoint_path = os.path.join(
                checkpoint_dir,
                f"{experiment_name}_best.pth"
            )

            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "best_val_acc": best_val_acc,
                    "class_names": class_names,
                    "config": config
                },
                checkpoint_path
            )

            print(f"Saved best checkpoint to {checkpoint_path}")

    history_path = os.path.join(
        result_dir,
        f"{experiment_name}_history.json"
    )

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

    print("\nTraining finished.")
    print(f"Best Val Acc: {best_val_acc:.4f}")
    print(f"History saved to {history_path}")
    summary = {
    "experiment_name": experiment_name,
    "model": config["model"]["name"],
    "pretrained": config["model"]["pretrained"],
    "attention": config["model"]["attention"],
    "epochs": config["train"]["epochs"],
    "optimizer": config["train"]["optimizer"],
    "backbone_lr": config["train"]["backbone_lr"],
    "classifier_lr": config["train"]["classifier_lr"],
    "weight_decay": config["train"]["weight_decay"],
    "best_val_acc": best_val_acc
}

    summary_path = os.path.join(
        result_dir,
        f"{experiment_name}_train_summary.json"
    )

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)

    print(f"Train summary saved to {summary_path}")


if __name__ == "__main__":
    main()