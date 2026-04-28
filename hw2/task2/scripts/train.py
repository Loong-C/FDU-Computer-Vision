from pathlib import Path
import argparse
import yaml
from ultralytics import YOLO


def load_config(config_path: str) -> dict:
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if config is None:
        raise ValueError(f"Config file is empty: {config_path}")

    return config


def main():
    parser = argparse.ArgumentParser(description="Train YOLO model on VisDrone dataset.")
    parser.add_argument(
        "--config",
        type=str,
        default="configs/train_visdrone_yolov8n.yaml",
        help="Path to training config yaml file.",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)

    model_name = cfg.pop("model")
    model = YOLO(model_name)

    print("Starting training with config:")
    for key, value in cfg.items():
        print(f"{key}: {value}")

    model.train(**cfg)


if __name__ == "__main__":
    main()