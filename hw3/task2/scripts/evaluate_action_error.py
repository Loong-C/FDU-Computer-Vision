from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from hw3_calvin_act.config import load_yaml, resolve_paths
from hw3_calvin_act.data import CalvinRawDataset, denormalize_actions, move_batch_to_device
from hw3_calvin_act.model import load_policy_from_checkpoint
from hw3_calvin_act.tracking import ExperimentTracker


@torch.no_grad()
def evaluate(policy, loader: DataLoader, device: torch.device, stats) -> dict[str, float]:
    policy.eval()
    chunk_errors = []
    first_action_errors = []
    for batch in loader:
        batch = move_batch_to_device(batch, device)
        predicted = denormalize_actions(policy.predict_action_chunk(batch), stats)
        target = denormalize_actions(batch["action"], stats)
        valid = ~batch["action_is_pad"]
        absolute_error = (predicted - target).abs()
        chunk_mask = valid.unsqueeze(-1).expand_as(absolute_error)
        chunk_errors.append(float(absolute_error[chunk_mask].mean().item()))
        first_action_errors.append(float(absolute_error[:, 0].mean().item()))
    return {
        "zero_shot/chunk_action_mae": float(np.mean(chunk_errors)),
        "zero_shot/first_action_mae": float(np.mean(first_action_errors)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a trained ACT checkpoint on unseen CALVIN D frames.")
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "configs" / "calvin_act.yaml")
    parser.add_argument("--dataset-root", type=Path, required=True, help="Path containing the D validation split.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--device")
    parser.add_argument("--max-samples", type=int)
    args = parser.parse_args()

    config = load_yaml(args.config)
    device = torch.device(args.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    policy, stats, checkpoint = load_policy_from_checkpoint(args.checkpoint, device)
    max_samples = args.max_samples or int(config["data"]["max_eval_samples"])
    dataset = CalvinRawDataset(
        dataset_root=args.dataset_root,
        split=config["data"]["test_split"],
        environments="D",
        chunk_size=int(checkpoint["model_config"]["chunk_size"]),
        image_size=int(checkpoint["model_config"]["image_size"]),
        max_samples=max_samples,
        stats=stats,
    )
    loader = DataLoader(
        dataset,
        batch_size=int(config["train"]["batch_size"]),
        shuffle=False,
        num_workers=int(config["train"]["num_workers"]),
        pin_memory=device.type == "cuda",
    )
    metrics = evaluate(policy, loader, device, stats)

    paths = resolve_paths()
    output_root = args.output_root or paths.output_root
    run_dir = output_root / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "metrics.csv").unlink(missing_ok=True)
    payload = {
        "checkpoint": str(args.checkpoint.resolve()),
        "dataset_root": str(args.dataset_root.resolve()),
        "samples": len(dataset),
        **metrics,
    }
    (run_dir / "zero_shot_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tracker = ExperimentTracker(
        run_dir=run_dir,
        project=config["swanlab"]["project"],
        experiment_name=args.run_name,
        config=payload,
        mode=config["swanlab"].get("mode"),
    )
    tracker.log(metrics, step=0)
    tracker.finish()
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
