from pathlib import Path
import argparse
import cv2
from ultralytics import YOLO


def get_side_of_vertical_line(x, line_x):
    if x < line_x:
        return -1
    if x > line_x:
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description="YOLO tracking with line-crossing counting.")
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
        default="outputs/videos/line_count_video.mp4",
        help="Path to output video.",
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
    parser.add_argument(
        "--line_ratio",
        type=float,
        default=0.5,
        help="Vertical line position ratio. 0.5 means the center of the frame.",
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

    line_x = int(width * args.line_ratio)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    previous_side = {}
    counted_ids = set()
    total_count = 0
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

        result = results[0]
        annotated_frame = result.plot()

        cv2.line(
            annotated_frame,
            (line_x, 0),
            (line_x, height),
            (0, 0, 255),
            3,
        )

        boxes = result.boxes

        if boxes is not None and boxes.id is not None:
            track_ids = boxes.id.cpu().numpy().astype(int)
            xyxy = boxes.xyxy.cpu().numpy()

            for box, track_id in zip(xyxy, track_ids):
                x1, y1, x2, y2 = box
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                current_side = get_side_of_vertical_line(cx, line_x)

                cv2.circle(
                    annotated_frame,
                    (cx, cy),
                    5,
                    (255, 0, 0),
                    -1,
                )

                if track_id in previous_side:
                    old_side = previous_side[track_id]

                    if (
                        old_side != 0
                        and current_side != 0
                        and old_side != current_side
                        and track_id not in counted_ids
                    ):
                        total_count += 1
                        counted_ids.add(track_id)

                previous_side[track_id] = current_side

        cv2.rectangle(
            annotated_frame,
            (10, 10),
            (420, 90),
            (0, 0, 0),
            -1,
        )
        cv2.putText(
            annotated_frame,
            f"Line Crossing Count: {total_count}",
            (25, 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            annotated_frame,
            f"Frame: {frame_idx}",
            (25, 85),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        writer.write(annotated_frame)
        frame_idx += 1

    cap.release()
    writer.release()

    print(f"Line-counting video saved to: {output_path}")
    print(f"Total crossing count: {total_count}")
    print(f"Counted tracking IDs: {sorted(counted_ids)}")


if __name__ == "__main__":
    main()