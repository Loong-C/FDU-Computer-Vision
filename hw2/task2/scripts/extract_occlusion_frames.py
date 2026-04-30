from pathlib import Path
import argparse
import cv2


def main():
    parser = argparse.ArgumentParser(description="Extract consecutive frames from a video.")
    parser.add_argument(
        "--source",
        type=str,
        default="outputs/videos/tracked_video.mp4",
        help="Path to input video.",
    )
    parser.add_argument(
        "--start",
        type=int,
        required=True,
        help="Start frame index.",
    )
    parser.add_argument(
        "--num",
        type=int,
        default=4,
        help="Number of consecutive frames to extract.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="outputs/frames/occlusion",
        help="Directory to save extracted frames.",
    )
    args = parser.parse_args()

    video_path = Path(args.source)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"Video: {video_path}")
    print(f"FPS: {fps}")
    print(f"Total frames: {total_frames}")

    cap.set(cv2.CAP_PROP_POS_FRAMES, args.start)

    saved = 0
    current_frame = args.start

    while saved < args.num:
        success, frame = cap.read()
        if not success:
            break

        output_path = output_dir / f"frame_{current_frame:06d}.jpg"
        cv2.imwrite(str(output_path), frame)

        print(f"Saved: {output_path}")

        saved += 1
        current_frame += 1

    cap.release()

    print(f"Done. Extracted {saved} frames.")


if __name__ == "__main__":
    main()