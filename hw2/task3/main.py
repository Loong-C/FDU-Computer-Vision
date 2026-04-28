import argparse
import os
import yaml
import torch

from utils.seed import set_seed
from utils.logger import create_run_dir, save_config, print_config
from train import run_training


def load_config(config_path: str):
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def main():
    parser = argparse.ArgumentParser(description="Task 3: U-Net Segmentation Training")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to config yaml file."
    )
    args = parser.parse_args()

    config = load_config(args.config)

    set_seed(config["seed"])

    if config["device"] == "cuda" and not torch.cuda.is_available():
        print("CUDA is not available. Falling back to CPU.")
        config["device"] = "cpu"

    os.makedirs(config["save"]["run_dir"], exist_ok=True)
    os.makedirs(config["save"]["result_dir"], exist_ok=True)

    run_dir = create_run_dir(
        base_dir=config["save"]["run_dir"],
        experiment_name=config["experiment_name"]
    )

    save_config(config, run_dir)
    print_config(config)

    run_training(config, run_dir)


if __name__ == "__main__":
    main()