#!/usr/bin/env python3
"""Run a subprocess with terminal, TensorBoard, and SwanLab tracking."""

import argparse
import json
import re
import shlex
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import swanlab

try:
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
except ModuleNotFoundError:
    EventAccumulator = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
MAGIC123_STEP = re.compile(r"==> Train \[Step\] (?P<step>\d+)/(?P<total>\d+)(?P<metrics>.*)")
KEY_VALUE = re.compile(r", (?P<key>[A-Za-z0-9_./-]+)=(?P<value>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")


def key_value_pair(value):
    key, separator, raw_value = value.partition("=")
    if not separator:
        raise argparse.ArgumentTypeError("Expected KEY=VALUE")
    try:
        parsed_value = json.loads(raw_value)
    except json.JSONDecodeError:
        parsed_value = raw_value
    return key, parsed_value


def collect_tensorboard_scalars(output_dir, prefix):
    by_step = defaultdict(dict)
    if EventAccumulator is None:
        return by_step
    for event_file in sorted(output_dir.rglob("events.out.tfevents.*")):
        accumulator = EventAccumulator(str(event_file))
        accumulator.Reload()
        for tag in accumulator.Tags().get("scalars", []):
            for event in accumulator.Scalars(tag):
                by_step[event.step][f"{prefix}/{tag}"] = event.value
    return by_step


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metric-prefix", required=True)
    parser.add_argument("--config", action="append", type=key_value_pair, default=[])
    parser.add_argument("--swanlab-mode", default="local", choices=["cloud", "local", "disabled"])
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("A subprocess command is required after --")

    args.cwd = args.cwd.resolve()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / f"{args.run_name}.log"
    metadata_path = logs_dir / f"{args.run_name}.json"
    started_at = datetime.now(timezone.utc)
    started_clock = time.monotonic()
    parsed_steps = set()

    config = {
        "stage": args.stage,
        "cwd": str(args.cwd),
        "output": str(args.output),
        "command": args.command,
        "tracker": "SwanLab local mode with terminal parsing and recursive TensorBoard import",
        **dict(args.config),
    }
    swanlab.init(
        project="cv-hw3-task1",
        experiment_name=args.run_name,
        config=config,
        logdir=str(PROJECT_ROOT / "swanlog"),
        mode=args.swanlab_mode,
    )

    exit_code = 0
    try:
        with log_path.open("w", encoding="utf-8") as log_file:
            log_file.write(f"$ {shlex.join(args.command)}\n")
            log_file.flush()
            process = subprocess.Popen(
                args.command,
                cwd=str(args.cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
                bufsize=1,
            )
            assert process.stdout is not None
            for line in process.stdout:
                print(line, end="")
                log_file.write(line)
                clean_line = ANSI_ESCAPE.sub("", line)
                match = MAGIC123_STEP.search(clean_line)
                if match:
                    step = int(match.group("step"))
                    metrics = {
                        f"{args.metric_prefix}/{item.group('key')}": float(item.group("value"))
                        for item in KEY_VALUE.finditer(match.group("metrics"))
                    }
                    if metrics:
                        swanlab.log(metrics, step=step)
                        parsed_steps.add(step)
            exit_code = process.wait()

        scalar_history = collect_tensorboard_scalars(args.output, args.metric_prefix)
        for step in sorted(scalar_history):
            swanlab.log(scalar_history[step], step=step)

        elapsed_seconds = time.monotonic() - started_clock
        final_step = max([0, *parsed_steps, *scalar_history])
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
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": elapsed_seconds,
            "exit_code": exit_code,
            "terminal_steps_imported": len(parsed_steps),
            "tensorboard_steps_imported": len(scalar_history),
        }
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    finally:
        swanlab.finish()

    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
