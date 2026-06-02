from __future__ import annotations

from pathlib import Path
from typing import Any

import torch

from hw3_calvin_act.compat import ensure_lerobot_importable
from hw3_calvin_act.data import ACTION_KEY, IMAGE_KEY, STATE_KEY, NormalizationStats


def build_act_policy(config: dict[str, Any], device: torch.device):
    ensure_lerobot_importable()
    from lerobot.configs.types import FeatureType, PolicyFeature
    from lerobot.policies.act.configuration_act import ACTConfig
    from lerobot.policies.act.modeling_act import ACTPolicy

    act_config = ACTConfig(
        input_features={
            IMAGE_KEY: PolicyFeature(type=FeatureType.VISUAL, shape=(3, config["image_size"], config["image_size"])),
            STATE_KEY: PolicyFeature(type=FeatureType.STATE, shape=(15,)),
        },
        output_features={
            ACTION_KEY: PolicyFeature(type=FeatureType.ACTION, shape=(7,)),
        },
        device=str(device),
        use_amp=bool(config.get("use_amp", False)),
        chunk_size=int(config["chunk_size"]),
        n_action_steps=int(config.get("n_action_steps", config["chunk_size"])),
        vision_backbone=config.get("vision_backbone", "resnet18"),
        pretrained_backbone_weights=config.get("pretrained_backbone_weights"),
        dim_model=int(config.get("dim_model", 256)),
        n_heads=int(config.get("n_heads", 8)),
        dim_feedforward=int(config.get("dim_feedforward", 1024)),
        n_encoder_layers=int(config.get("n_encoder_layers", 3)),
        n_decoder_layers=int(config.get("n_decoder_layers", 1)),
        use_vae=bool(config.get("use_vae", True)),
        latent_dim=int(config.get("latent_dim", 32)),
        n_vae_encoder_layers=int(config.get("n_vae_encoder_layers", 2)),
        dropout=float(config.get("dropout", 0.1)),
        kl_weight=float(config.get("kl_weight", 10.0)),
        optimizer_lr=float(config.get("optimizer_lr", 1e-5)),
        optimizer_weight_decay=float(config.get("optimizer_weight_decay", 1e-4)),
        optimizer_lr_backbone=float(config.get("optimizer_lr_backbone", config.get("optimizer_lr", 1e-5))),
    )
    return ACTPolicy(act_config).to(device)


def save_checkpoint(
    path: str | Path,
    *,
    policy,
    optimizer: torch.optim.Optimizer,
    step: int,
    model_config: dict[str, Any],
    normalization_stats: NormalizationStats,
    run_config: dict[str, Any],
    best_validation_loss: float,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "policy_state_dict": policy.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "step": step,
            "model_config": model_config,
            "normalization_stats": normalization_stats.to_dict(),
            "run_config": run_config,
            "best_validation_loss": best_validation_loss,
        },
        path,
    )


def load_checkpoint(path: str | Path, device: torch.device) -> dict[str, Any]:
    return torch.load(Path(path), map_location=device, weights_only=False)


def load_policy_from_checkpoint(path: str | Path, device: torch.device):
    checkpoint = load_checkpoint(path, device)
    policy = build_act_policy(checkpoint["model_config"], device)
    policy.load_state_dict(checkpoint["policy_state_dict"])
    stats = NormalizationStats.from_dict(checkpoint["normalization_stats"])
    return policy, stats, checkpoint
