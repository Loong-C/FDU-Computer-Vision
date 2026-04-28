import os
import json
from datetime import datetime


def create_run_dir(base_dir: str, experiment_name: str):
    time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"{experiment_name}_{time_str}"
    run_dir = os.path.join(base_dir, run_name)

    os.makedirs(run_dir, exist_ok=True)
    return run_dir


def save_config(config: dict, run_dir: str):
    path = os.path.join(run_dir, "config.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def save_history(history: dict, run_dir: str):
    path = os.path.join(run_dir, "history.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)


def print_config(config: dict):
    print("=" * 60)
    print("Experiment Configuration")
    print("=" * 60)

    for key, value in config.items():
        print(f"{key}: {value}")

    print("=" * 60)