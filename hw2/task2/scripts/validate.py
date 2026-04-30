from pathlib import Path
import argparse
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Validate a trained YOLO model on VisDrone.")
    parser.add_argument(
        "--weights",
        type=str,
        required=True,
        help="Path to trained model weights, such as runs/detect/.../weights/best.pt",
    )
    parser.add_argument(
        "--data",
        type=str,
        default="configs/VisDrone.yaml",
        help="Dataset yaml file.",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Validation image size.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="0",
        help="Device id, such as 0 or cpu.",
    )
    args = parser.parse_args()

    weights_path = Path(args.weights)
    if not weights_path.exists():
        raise FileNotFoundError(f"Weights file not found: {weights_path}")

    model = YOLO(str(weights_path))

    metrics = model.val(
        data=args.data,
        imgsz=args.imgsz,
        device=args.device,
        plots=True,
    )

    print(metrics)


if __name__ == "__main__":
    main()
