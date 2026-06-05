#!/usr/bin/env python3
"""Run official 2DGS training with terminal, TensorBoard, and SwanLab logs."""

import argparse
import json
import shlex
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import swanlab
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_SCRIPT = PROJECT_ROOT / "external" / "2d-gaussian-splatting" / "train.py"


def comma_separated_ints(value):
    return [int(item) for item in value.split(",") if item]


def collect_tensorboard_scalars(output_dir):
    by_step = defaultdict(dict)
    for event_file in sorted(output_dir.glob("events.out.tfevents.*")):
        accumulator = EventAccumulator(str(event_file))
        accumulator.Reload()
        for tag in accumulator.Tags().get("scalars", []):
            for event in accumulator.Scalars(tag):
                by_step[event.step][f"2dgs/{tag}"] = event.value
    return by_step


def log_tensorboard_scalars(output_dir):
    scalar_history = collect_tensorboard_scalars(output_dir)
    for step in sorted(scalar_history):
        swanlab.log(scalar_history[step], step=step)
    return scalar_history


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=30000)
    parser.add_argument("--resolution", type=int, default=-1)
    parser.add_argument("--test-iterations", type=comma_separated_ints, default="7000,30000")
    parser.add_argument("--save-iterations", type=comma_separated_ints, default="7000,30000")
    parser.add_argument("--depth-ratio", type=float, default=0.0)
    parser.add_argument("--lambda-normal", type=float, default=0.05)
    parser.add_argument("--lambda-distortion", type=float, default=0.0)
    parser.add_argument("--swanlab-mode", default="local", choices=["cloud", "local", "disabled"])
    parser.add_argument("--import-only", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    args.source = args.source.resolve()
    args.output = args.output.resolve()
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"{args.run_name}.log"
    metadata_path = logs_dir / f"{args.run_name}.json"
    started_at = datetime.now(timezone.utc)
    started_clock = time.monotonic()

    config = {
        "stage": args.stage,
        "source": str(args.source),
        "output": str(args.output),
        "iterations": args.iterations,
        "resolution": args.resolution,
        "test_iterations": args.test_iterations,
        "save_iterations": args.save_iterations,
        "depth_ratio": args.depth_ratio,
        "lambda_normal": args.lambda_normal,
        "lambda_distortion": args.lambda_distortion,
        "tracker": "SwanLab local mode with TensorBoard scalar import",
    }
    swanlab.init(
        project="cv-hw3-task1",
        experiment_name=args.run_name,
        config=config,
        logdir=str(PROJECT_ROOT / "swanlog"),
        mode=args.swanlab_mode,
    )

    command = [
        sys.executable,
        str(TRAIN_SCRIPT),
        "-s",
        str(args.source),
        "-m",
        str(args.output),
        "--iterations",
        str(args.iterations),
        "-r",
        str(args.resolution),
        "--depth_ratio",
        str(args.depth_ratio),
        "--lambda_normal",
        str(args.lambda_normal),
        "--lambda_dist",
        str(args.lambda_distortion),
        "--test_iterations",
        *[str(value) for value in args.test_iterations],
        "--save_iterations",
        *[str(value) for value in args.save_iterations],
    ]

    exit_code = 0
    try:
        if not args.import_only:
            with log_path.open("w", encoding="utf-8") as log_file:
                log_file.write(f"$ {shlex.join(command)}\n")
                log_file.flush()
                process = subprocess.Popen(
                    command,
                    cwd=str(TRAIN_SCRIPT.parent),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                assert process.stdout is not None
                for line in process.stdout:
                    print(line, end="")
                    log_file.write(line)
                exit_code = process.wait()
        scalar_history = log_tensorboard_scalars(args.output)
        elapsed_seconds = time.monotonic() - started_clock
        final_step = max(scalar_history, default=args.iterations)
        swanlab.log(
            {
                "system/elapsed_seconds": elapsed_seconds,
                "system/exit_code": exit_code,
                "system/success": int(exit_code == 0),
            },
            step=final_step,
        )
        metadata = {
            **config,
            "command": command,
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": elapsed_seconds,
            "exit_code": exit_code,
            "scalar_steps_imported": len(scalar_history),
        }
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    finally:
        swanlab.finish()

    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
