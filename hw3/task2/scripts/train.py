from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import torch
from torch.utils.data import DataLoader

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from hw3_calvin_act.config import load_yaml, resolve_paths
from hw3_calvin_act.data import (
    CalvinRawDataset,
    fit_normalization_stats,
    move_batch_to_device,
    split_sample_indices,
)
from hw3_calvin_act.model import build_act_policy, load_checkpoint, save_checkpoint
from hw3_calvin_act.tracking import ExperimentTracker


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def select_device(requested: str | None) -> torch.device:
    if requested:
        return torch.device(requested)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def repeat_loader(loader: DataLoader) -> Iterator[dict[str, torch.Tensor]]:
    while True:
        yield from loader


@torch.no_grad()
def validation_loss(policy, loader: DataLoader, device: torch.device, batches: int) -> dict[str, float]:
    policy.eval()
    metrics: dict[str, list[float]] = {"validation/loss": [], "validation/l1_loss": []}
    for batch_index, batch in enumerate(loader):
        if batch_index >= batches:
            break
        batch = move_batch_to_device(batch, device)
        predicted = policy.predict_action_chunk(batch)
        absolute_error = (predicted - batch["action"]).abs()
        valid = (~batch["action_is_pad"]).unsqueeze(-1).expand_as(absolute_error)
        l1_loss = absolute_error[valid].mean()
        metrics["validation/loss"].append(float(l1_loss.item()))
        metrics["validation/l1_loss"].append(float(l1_loss.item()))
    return {name: float(np.mean(values)) for name, values in metrics.items() if values}


def make_dataset(config: dict[str, Any], dataset_root: Path, environments: str) -> CalvinRawDataset:
    data_config = config["data"]
    return CalvinRawDataset(
        dataset_root=dataset_root,
        split=data_config["train_split"],
        environments=environments,
        chunk_size=config["model"]["chunk_size"],
        image_size=data_config["image_size"],
        max_samples=data_config.get("max_train_samples"),
        stride=data_config.get("stride", 1),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Train LeRobot ACT on raw CALVIN frames.")
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "configs" / "calvin_act.yaml")
    parser.add_argument("--dataset-root", type=Path, required=True, help="Path containing the CALVIN split folders.")
    parser.add_argument("--environments", choices=["B", "ABC"], required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--device")
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args()

    config = load_yaml(args.config)
    config["model"]["image_size"] = config["data"]["image_size"]
    seed = int(config["seed"])
    set_seed(seed)
    device = select_device(args.device)
    paths = resolve_paths()
    output_root = args.output_root or paths.output_root
    run_dir = output_root / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    if not args.resume:
        (run_dir / "metrics.csv").unlink(missing_ok=True)

    raw_dataset = make_dataset(config, args.dataset_root, args.environments)
    train_indices, validation_indices = split_sample_indices(
        raw_dataset.sample_indices,
        validation_fraction=float(config["data"]["validation_fraction"]),
        seed=seed,
    )
    raw_train_dataset = raw_dataset.subset(train_indices)

    if args.resume:
        checkpoint = load_checkpoint(args.resume, device)
        from hw3_calvin_act.data import NormalizationStats

        stats = NormalizationStats.from_dict(checkpoint["normalization_stats"])
        policy = build_act_policy(checkpoint["model_config"], device)
        policy.load_state_dict(checkpoint["policy_state_dict"])
    else:
        checkpoint = None
        stats = fit_normalization_stats(raw_train_dataset, max_samples=int(config["data"]["stats_samples"]))
        policy = build_act_policy(config["model"], device)

    train_dataset = raw_train_dataset.with_stats(stats)
    validation_dataset = raw_dataset.subset(validation_indices).with_stats(stats)
    train_loader = DataLoader(
        train_dataset,
        batch_size=int(config["train"]["batch_size"]),
        shuffle=True,
        num_workers=int(config["train"]["num_workers"]),
        pin_memory=device.type == "cuda",
    )
    validation_loader = DataLoader(
        validation_dataset,
        batch_size=int(config["train"]["batch_size"]),
        shuffle=False,
        num_workers=int(config["train"]["num_workers"]),
        pin_memory=device.type == "cuda",
    )
    optimizer = torch.optim.AdamW(
        policy.get_optim_params(),
        lr=float(config["model"]["optimizer_lr"]),
        weight_decay=float(config["model"]["optimizer_weight_decay"]),
    )
    start_step = 0
    best_validation_loss = float("inf")
    if checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        start_step = int(checkpoint["step"])
        best_validation_loss = float(checkpoint.get("best_validation_loss", float("inf")))

    max_steps = args.max_steps or int(config["train"]["max_steps"])
    run_config = {
        "config": config,
        "dataset_root": str(args.dataset_root.resolve()),
        "environments": args.environments,
        "device": str(device),
        "train_samples": len(train_dataset),
        "validation_samples": len(validation_dataset),
    }
    (run_dir / "run_config.json").write_text(json.dumps(run_config, indent=2), encoding="utf-8")
    stats.save(run_dir / "normalization_stats.json")
    tracker = ExperimentTracker(
        run_dir=run_dir,
        project=config["swanlab"]["project"],
        experiment_name=args.run_name,
        config=run_config,
        mode=config["swanlab"].get("mode"),
    )

    use_amp = bool(config["model"].get("use_amp", False) and device.type == "cuda")
    scaler = torch.amp.GradScaler(device.type, enabled=use_amp)
    batches = repeat_loader(train_loader)
    try:
        for step in range(start_step + 1, max_steps + 1):
            policy.train()
            optimizer.zero_grad(set_to_none=True)
            batch = move_batch_to_device(next(batches), device)
            with torch.autocast(device_type=device.type, enabled=use_amp):
                loss, details = policy(batch)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            grad_norm = torch.nn.utils.clip_grad_norm_(
                policy.parameters(), float(config["train"]["grad_clip_norm"])
            )
            scaler.step(optimizer)
            scaler.update()

            metrics = {
                "train/loss": float(loss.item()),
                "train/grad_norm": float(grad_norm.item()),
                "train/lr": float(optimizer.param_groups[0]["lr"]),
                **{f"train/{name}": float(value) for name, value in details.items()},
            }
            if step % int(config["train"]["validation_interval"]) == 0 or step == max_steps:
                metrics.update(
                    validation_loss(
                        policy,
                        validation_loader,
                        device,
                        batches=int(config["train"]["validation_batches"]),
                    )
                )
                current_validation_loss = metrics["validation/loss"]
                if current_validation_loss < best_validation_loss:
                    best_validation_loss = current_validation_loss
                    save_checkpoint(
                        run_dir / "checkpoints" / "best.pt",
                        policy=policy,
                        optimizer=optimizer,
                        step=step,
                        model_config=config["model"],
                        normalization_stats=stats,
                        run_config=run_config,
                        best_validation_loss=best_validation_loss,
                    )
            if step % int(config["train"]["checkpoint_interval"]) == 0 or step == max_steps:
                save_checkpoint(
                    run_dir / "checkpoints" / "latest.pt",
                    policy=policy,
                    optimizer=optimizer,
                    step=step,
                    model_config=config["model"],
                    normalization_stats=stats,
                    run_config=run_config,
                    best_validation_loss=best_validation_loss,
                )
            if step % int(config["train"]["log_interval"]) == 0 or step == max_steps:
                tracker.log(metrics, step=step)
                print(
                    f"step={step}/{max_steps} train_loss={metrics['train/loss']:.6f} "
                    f"validation_loss={metrics.get('validation/loss', float('nan')):.6f}"
                )
    finally:
        tracker.finish()

    print(f"Finished run: {run_dir}")


if __name__ == "__main__":
    main()
