import os
import time
import torch
from tqdm import tqdm

from datasets.oxford_pet import build_dataloaders
from models.unet import UNet
from losses.dice_loss import build_loss
from utils.metrics import SegmentationMetric
from utils.logger import save_history, save_summary


def train_one_epoch(model, train_loader, criterion, optimizer, device):
    model.train()

    total_loss = 0.0
    total_samples = 0

    progress_bar = tqdm(train_loader, desc="Training", leave=False)

    for images, masks in progress_bar:
        images = images.to(device)
        masks = masks.to(device)

        optimizer.zero_grad()

        logits = model(images)
        loss = criterion(logits, masks)

        loss.backward()
        optimizer.step()

        batch_size = images.size(0)
        total_loss += loss.item() * batch_size
        total_samples += batch_size

        progress_bar.set_postfix(loss=loss.item())

    avg_loss = total_loss / total_samples

    return avg_loss


@torch.no_grad()
def validate_one_epoch(model, val_loader, criterion, device, num_classes):
    model.eval()

    total_loss = 0.0
    total_samples = 0

    metric = SegmentationMetric(num_classes=num_classes)

    progress_bar = tqdm(val_loader, desc="Validation", leave=False)

    for images, masks in progress_bar:
        images = images.to(device)
        masks = masks.to(device)

        logits = model(images)
        loss = criterion(logits, masks)

        batch_size = images.size(0)
        total_loss += loss.item() * batch_size
        total_samples += batch_size

        metric.update(logits, masks)

        progress_bar.set_postfix(loss=loss.item())

    avg_loss = total_loss / total_samples
    results = metric.get_results()

    return avg_loss, results


def run_training(config: dict, run_dir: str):
    device = torch.device(config["device"])

    train_loader, val_loader = build_dataloaders(config)

    model = UNet(
        in_channels=config["model"]["in_channels"],
        num_classes=config["model"]["num_classes"],
        base_channels=config["model"]["base_channels"],
    ).to(device)

    criterion = build_loss(config)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config["train"]["lr"],
        weight_decay=config["train"]["weight_decay"],
    )

    epochs = config["train"]["epochs"]
    num_classes = config["model"]["num_classes"]

    history = {
        "train_loss": [],
        "val_loss": [],
        "val_pixel_acc": [],
        "val_miou": [],
        "val_class_iou": [],
    }

    best_miou = 0.0
    best_epoch = 0
    best_model_path = os.path.join(run_dir, "best_model.pth")
    last_model_path = os.path.join(run_dir, "last_model.pth")

    print()
    print("Start training")
    print(f"Device: {device}")
    print(f"Epochs: {epochs}")
    print(f"Loss type: {config['train']['loss_type']}")
    print(f"Run directory: {run_dir}")
    print()

    start_time = time.time()

    for epoch in range(1, epochs + 1):
        print(f"Epoch [{epoch}/{epochs}]")

        train_loss = train_one_epoch(
            model=model,
            train_loader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device,
        )

        val_loss, val_results = validate_one_epoch(
            model=model,
            val_loader=val_loader,
            criterion=criterion,
            device=device,
            num_classes=num_classes,
        )

        val_pixel_acc = val_results["pixel_acc"]
        val_miou = val_results["miou"]
        val_class_iou = val_results["class_iou"]

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_pixel_acc"].append(val_pixel_acc)
        history["val_miou"].append(val_miou)
        history["val_class_iou"].append(val_class_iou)

        print(f"Train Loss: {train_loss:.6f}")
        print(f"Val Loss: {val_loss:.6f}")
        print(f"Val Pixel Acc: {val_pixel_acc:.6f}")
        print(f"Val mIoU: {val_miou:.6f}")
        print(f"Val Class IoU: {[round(x, 6) for x in val_class_iou]}")

        if val_miou > best_miou:
            best_miou = val_miou
            best_epoch = epoch

            best_path = os.path.join(run_dir, "best_model.pth")

            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "best_miou": best_miou,
                    "config": config,
                },
                best_model_path,
            )

            print(f"Saved best model to {best_model_path}")

            print(f"Saved best model to {best_path}")

        last_path = os.path.join(run_dir, "last_model.pth")

        torch.save(
            {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "best_miou": best_miou,
                "config": config,
            },
            last_model_path,
        )

        save_history(history, run_dir)

        print("-" * 60)

    total_time = time.time() - start_time
    total_time_minutes = total_time / 60

    summary = {
        "experiment_name": config["experiment_name"],
        "loss_type": config["train"]["loss_type"],
        "best_val_miou": best_miou,
        "best_epoch": best_epoch,
        "total_time_minutes": total_time_minutes,
        "final_train_loss": history["train_loss"][-1],
        "final_val_loss": history["val_loss"][-1],
        "final_val_pixel_acc": history["val_pixel_acc"][-1],
        "final_val_miou": history["val_miou"][-1],
        "final_val_class_iou": history["val_class_iou"][-1],
        "best_model_path": best_model_path,
        "last_model_path": last_model_path,
    }

    save_summary(summary, run_dir)

    print()
    print("Training finished")
    print(f"Best Val mIoU: {best_miou:.6f}")
    print(f"Best Epoch: {best_epoch}")
    print(f"Total time: {total_time_minutes:.2f} minutes")
    print(f"Summary saved to {os.path.join(run_dir, 'summary.json')}")