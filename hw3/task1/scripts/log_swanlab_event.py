#!/usr/bin/env python3
"""Record a lightweight Task 1 milestone in SwanLab."""

import argparse
import json
from pathlib import Path

import swanlab


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def key_value_pair(value):
    key, separator, raw_value = value.partition("=")
    if not separator:
        raise argparse.ArgumentTypeError("Expected KEY=VALUE")
    try:
        parsed_value = json.loads(raw_value)
    except json.JSONDecodeError:
        parsed_value = raw_value
    return key, parsed_value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--event", required=True)
    parser.add_argument("--config", action="append", type=key_value_pair, default=[])
    parser.add_argument("--swanlab-mode", default="local", choices=["cloud", "local", "disabled"])
    args = parser.parse_args()

    config = {"event": args.event, **dict(args.config)}
    swanlab.init(
        project="cv-hw3-task1",
        experiment_name=args.run_name,
        config=config,
        logdir=str(PROJECT_ROOT / "swanlog"),
        mode=args.swanlab_mode,
    )
    swanlab.log({"milestone/completed": 1}, step=0)
    swanlab.finish()


if __name__ == "__main__":
    main()
