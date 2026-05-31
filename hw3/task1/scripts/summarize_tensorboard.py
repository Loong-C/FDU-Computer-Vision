#!/usr/bin/env python3
"""Summarize TensorBoard scalar events for report tables and audit logs."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator


def comma_separated_ints(value):
    return [int(item) for item in value.split(",") if item]


def collect_scalars(input_dir):
    by_tag = defaultdict(dict)
    event_files = sorted(input_dir.rglob("events.out.tfevents.*"))
    for event_file in event_files:
        accumulator = EventAccumulator(str(event_file))
        accumulator.Reload()
        for tag in accumulator.Tags().get("scalars", []):
            for event in accumulator.Scalars(tag):
                by_tag[tag][event.step] = event.value
    return event_files, by_tag


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--steps", type=comma_separated_ints, default="")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    args.input = args.input.resolve()
    event_files, by_tag = collect_scalars(args.input)
    summary = {
        "input": str(args.input),
        "event_files": [str(path) for path in event_files],
        "scalar_tags": sorted(by_tag),
        "latest": {},
        "requested_steps": {},
    }

    for tag in sorted(by_tag):
        values = by_tag[tag]
        if values:
            latest_step = max(values)
            summary["latest"][tag] = {
                "step": latest_step,
                "value": values[latest_step],
            }

    for step in args.steps:
        summary["requested_steps"][str(step)] = {
            tag: values[step]
            for tag, values in sorted(by_tag.items())
            if step in values
        }

    text = json.dumps(summary, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
