import argparse
import json
import os
import subprocess
import sys


def run_command(command):
    print("\nRunning command:")
    print(" ".join(command))

    result = subprocess.run(command)

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with return code {result.returncode}: "
            f"{' '.join(command)}"
        )


def load_config_name(config_path):
    import yaml

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config["experiment_name"], config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        required=True
    )
    parser.add_argument(
        "--skip_train",
        action="store_true"
    )
    parser.add_argument(
        "--skip_test",
        action="store_true"
    )
    parser.add_argument(
        "--skip_plot",
        action="store_true"
    )

    args = parser.parse_args()

    experiment_name, config = load_config_name(args.config)

    print("=" * 60)
    print("Experiment:", experiment_name)
    print("Config:", args.config)
    print("=" * 60)

    if not args.skip_train:
        run_command([
            sys.executable,
            "src/train.py",
            "--config",
            args.config
        ])

    if not args.skip_test:
        checkpoint_path = os.path.join(
            config["save"]["checkpoint_dir"],
            f"{experiment_name}_best.pth"
        )

        run_command([
            sys.executable,
            "src/test.py",
            "--config",
            args.config,
            "--checkpoint",
            checkpoint_path
        ])

    if not args.skip_plot:
        run_command([
            sys.executable,
            "src/plot_history.py",
            "--config",
            args.config
        ])

    print("\nExperiment pipeline finished.")


if __name__ == "__main__":
    main()