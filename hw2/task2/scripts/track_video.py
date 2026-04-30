from pathlib import Path
import argparse
import cv2
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Run YOLO tracking on a video.")
    parser.add_argument(
        "--weights",
        type=str,
        default="runs/detect/visdrone_yolov8n_e50/weights/best.pt",
        help="Path to trained YOLO weights.",
    )
    parser.add_argument(
        "--source",
        type=str,
        default="data/videos/test_video.mp4",
        help="Path to input video.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs/videos/tracked_video.mp4",
        help="Path to output tracked video.",
    )
    parser.add_argument(
        "--tracker",
        type=str,
        default="botsort.yaml",
        help="Tracker config, such as botsort.yaml or bytetrack.yaml.",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold.",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Inference image size.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="0",
        help="Device, such as 0 or cpu.",
    )
    args = parser.parse_args()

    weights_path = Path(args.weights)
    video_path = Path(args.source)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not weights_path.exists():
        raise FileNotFoundError(f"Weights not found: {weights_path}")
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    model = YOLO(str(weights_path))

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    frame_idx = 0

    while True:
        success, frame = cap.read()
        if not success:
            break

        results = model.track(
            frame,
            persist=True,
            tracker=args.tracker,
            conf=args.conf,
            imgsz=args.imgsz,
            device=args.device,
            verbose=False,
        )

        annotated_frame = results[0].plot()

        cv2.putText(
            annotated_frame,
            f"Frame: {frame_idx}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

        writer.write(annotated_frame)
        frame_idx += 1

    cap.release()
    writer.release()

    print(f"Tracking video saved to: {output_path}")


if __name__ == "__main__":
    main()