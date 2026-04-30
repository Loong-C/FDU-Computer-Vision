from __future__ import annotations

import csv
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOGDIR = ROOT / "report" / "swanlog_hw2"
SAVEDIR = ROOT / "report" / "swanlab_home"


def setup_env() -> None:
    SAVEDIR.mkdir(parents=True, exist_ok=True)
    LOGDIR.mkdir(parents=True, exist_ok=True)
    os.environ["SWANLAB_SAVE_DIR"] = str(SAVEDIR)
    os.environ["SWANLAB_LOG_DIR"] = str(LOGDIR)
    os.environ["SWANLAB_MODE"] = "local"


def read_json(path: str) -> dict:
    with open(ROOT / path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_csv(path: str) -> list[dict[str, str]]:
    with open(ROOT / path, "r", encoding="utf-8-sig", newline="") as f:
        return [{k.strip(): v for k, v in row.items()} for row in csv.DictReader(f)]


def log_task1(swanlab) -> None:
    runs = [
        (
            "task1_resnet18_pretrained_baseline",
            "task1/results/resnet18_pretrained_baseline_history.json",
            {
                "task": "Task 1",
                "model": "ResNet-18",
                "pretrained": True,
                "attention": "none",
                "test_acc": 0.8800763151,
            },
        ),
        (
            "task1_resnet18_scratch_ablation",
            "task1/results/resnet18_scratch_ablation_history.json",
            {
                "task": "Task 1",
                "model": "ResNet-18",
                "pretrained": False,
                "attention": "none",
                "test_acc": 0.4423548651,
            },
        ),
        (
            "task1_resnet18_se_pretrained",
            "task1/results/resnet18_se_pretrained_history.json",
            {
                "task": "Task 1",
                "model": "SE-ResNet-18",
                "pretrained": True,
                "attention": "se",
                "test_acc": 0.8620877623,
            },
        ),
    ]

    for name, history_path, config in runs:
        history = read_json(history_path)
        swanlab.init(
            project="CV-HW2",
            experiment_name=name,
            group="Task 1 Classification",
            config=config,
            mode="local",
            logdir=str(LOGDIR),
            reinit=True,
        )
        for idx in range(len(history["train_loss"])):
            swanlab.log(
                {
                    "task1/train_loss": history["train_loss"][idx],
                    "task1/val_loss": history["val_loss"][idx],
                    "task1/train_accuracy": history["train_acc"][idx],
                    "task1/val_accuracy": history["val_acc"][idx],
                },
                step=idx + 1,
            )
        swanlab.log({"task1/test_accuracy": config["test_acc"]}, step=len(history["train_loss"]))
        swanlab.finish()


def log_task2(swanlab) -> None:
    rows = read_csv("task2/runs/detect/visdrone_yolov8n_e50/results.csv")
    swanlab.init(
        project="CV-HW2",
        experiment_name="task2_yolov8n_visdrone_e50",
        group="Task 2 Detection Tracking",
        config={
            "task": "Task 2",
            "model": "YOLOv8n",
            "dataset": "VisDrone",
            "epochs": 50,
            "imgsz": 640,
            "batch": 4,
            "workers": 0,
        },
        mode="local",
        logdir=str(LOGDIR),
        reinit=True,
    )

    for row in rows:
        step = int(float(row["epoch"])) + 1
        swanlab.log(
            {
                "task2/train_box_loss": float(row["train/box_loss"]),
                "task2/train_cls_loss": float(row["train/cls_loss"]),
                "task2/train_dfl_loss": float(row["train/dfl_loss"]),
                "task2/val_box_loss": float(row["val/box_loss"]),
                "task2/val_cls_loss": float(row["val/cls_loss"]),
                "task2/val_dfl_loss": float(row["val/dfl_loss"]),
                "task2/precision": float(row["metrics/precision(B)"]),
                "task2/recall": float(row["metrics/recall(B)"]),
                "task2/mAP50": float(row["metrics/mAP50(B)"]),
                "task2/mAP50_95": float(row["metrics/mAP50-95(B)"]),
            },
            step=step,
        )
    swanlab.finish()


def log_task3(swanlab) -> None:
    runs = [
        ("task3_unet_ce", "task3/runs/unet_ce_20260428_160024/history.json", "CE"),
        ("task3_unet_dice", "task3/runs/unet_dice_20260428_175418/history.json", "Dice"),
        ("task3_unet_ce_dice", "task3/runs/unet_ce_dice_20260428_194303/history.json", "CE + Dice"),
    ]

    for name, history_path, loss_name in runs:
        history = read_json(history_path)
        swanlab.init(
            project="CV-HW2",
            experiment_name=name,
            group="Task 3 Segmentation",
            config={
                "task": "Task 3",
                "model": "U-Net",
                "loss": loss_name,
                "dataset": "Oxford-IIIT Pet trimap",
                "epochs": 50,
                "image_size": 256,
                "batch_size": 8,
            },
            mode="local",
            logdir=str(LOGDIR),
            reinit=True,
        )
        for idx in range(len(history["train_loss"])):
            swanlab.log(
                {
                    "task3/train_loss": history["train_loss"][idx],
                    "task3/val_loss": history["val_loss"][idx],
                    "task3/val_pixel_accuracy": history["val_pixel_acc"][idx],
                    "task3/val_mIoU": history["val_miou"][idx],
                },
                step=idx + 1,
            )
        swanlab.finish()


def main() -> None:
    setup_env()
    import swanlab

    log_task1(swanlab)
    log_task2(swanlab)
    log_task3(swanlab)
    print(f"SwanLab logs written to {LOGDIR}")


if __name__ == "__main__":
    main()
