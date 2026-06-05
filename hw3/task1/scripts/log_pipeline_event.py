#!/usr/bin/env python3
"""Record a non-training Task 1 milestone in SwanLab local mode."""

import argparse
import json
from datetime import datetime, timezone
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
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--status", choices=["success", "failure", "info"], required=True)
    parser.add_argument("--note", default="")
    parser.add_argument("--config", action="append", type=key_value_pair, default=[])
    parser.add_argument("--metric", action="append", type=key_value_pair, default=[])
    parser.add_argument("--swanlab-mode", default="local", choices=["cloud", "local", "disabled"])
    args = parser.parse_args()

    config = {
        "stage": args.stage,
        "status": args.status,
        "note": args.note,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        **dict(args.config),
    }
    metrics = {
        "pipeline/success": int(args.status == "success"),
        **dict(args.metric),
    }
    swanlab.init(
        project="cv-hw3-task1",
        experiment_name=args.experiment_name,
        config=config,
        logdir=str(PROJECT_ROOT / "swanlog"),
        mode=args.swanlab_mode,
    )
    swanlab.log(metrics)
    swanlab.finish()
    print(json.dumps({"config": config, "metrics": metrics}, indent=2))


if __name__ == "__main__":
    main()
