import argparse
import itertools
import os
import subprocess
import sys
import yaml
import copy


def set_nested_value(config, key_path, value):
    keys = key_path.split(".")
    current = config

    for key in keys[:-1]:
        current = current[key]

    current[keys[-1]] = value


def format_value(value):
    if isinstance(value, float):
        return str(value).replace(".", "p")
    return str(value)


def build_experiment_name(base_name, params):
    parts = [base_name]

    short_names = {
        "train.epochs": "ep",
        "train.backbone_lr": "blr",
        "train.classifier_lr": "clr",
        "train.weight_decay": "wd",
        "data.batch_size": "bs",
        "scheduler.min_lr": "minlr"
    }

    for key, value in params.items():
        name = short_names.get(key, key.replace(".", "_"))
        parts.append(f"{name}{format_value(value)}")

    return "_".join(parts)


def run_command(command):
    print("\nRunning command:")
    print(" ".join(command))

    result = subprocess.run(command)

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with return code {result.returncode}: "
            f"{' '.join(command)}"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base_config",
        type=str,
        default="configs/resnet18_pretrained.yaml"
    )
    parser.add_argument(
        "--skip_existing",
        action="store_true"
    )
    parser.add_argument(
        "--dry_run",
        action="store_true"
    )

    args = parser.parse_args()

    with open(args.base_config, "r", encoding="utf-8") as f:
        base_config = yaml.safe_load(f)

    generated_dir = "configs/generated"
    os.makedirs(generated_dir, exist_ok=True)

    search_space = {
        "train.epochs": [15],
        "train.backbone_lr": [0.00005, 0.0001, 0.0005],
        "train.classifier_lr": [0.0005, 0.001, 0.005],
        "data.batch_size": [32]
    }

    keys = list(search_space.keys())
    values = list(search_space.values())

    combinations = list(itertools.product(*values))

    print(f"Total experiments: {len(combinations)}")

    for index, combination in enumerate(combinations, start=1):
        params = dict(zip(keys, combination))

        config = copy.deepcopy(base_config)

        experiment_name = build_experiment_name(
            base_name="resnet18_grid",
            params=params
        )

        config["experiment_name"] = experiment_name

        for key_path, value in params.items():
            set_nested_value(config, key_path, value)

        config_path = os.path.join(
            generated_dir,
            f"{experiment_name}.yaml"
        )

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                config,
                f,
                allow_unicode=True,
                sort_keys=False
            )

        summary_path = os.path.join(
            config["save"]["result_dir"],
            f"{experiment_name}_summary.json"
        )

        print("\n" + "=" * 80)
        print(f"Experiment {index}/{len(combinations)}")
        print("Experiment name:", experiment_name)
        print("Config path:", config_path)
        print("Parameters:", params)
        print("=" * 80)

        if args.skip_existing and os.path.exists(summary_path):
            print("Summary already exists. Skipping.")
            continue

        if args.dry_run:
            continue

        run_command([
            sys.executable,
            "main.py",
            "--config",
            config_path
        ])


if __name__ == "__main__":
    main()