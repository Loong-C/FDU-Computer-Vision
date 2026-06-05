from __future__ import annotations

import csv
import importlib.util
import json
import math
import os
import sys
import types
from collections import Counter, deque
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import torch
import torch.nn.functional as F

from hw3_calvin_act.config import load_yaml, resolve_paths
from hw3_calvin_act.data import IMAGE_KEY, STATE_KEY, NormalizationStats, denormalize_actions
from hw3_calvin_act.model import load_policy_from_checkpoint
from hw3_calvin_act.tracking import ExperimentTracker

REPO_ROOT = Path(__file__).resolve().parents[2]
CALVIN_ROOT = REPO_ROOT / "external" / "calvin"
CALVIN_MODELS_ROOT = CALVIN_ROOT / "calvin_models"
CALVIN_ENV_ROOT = CALVIN_ROOT / "calvin_env"


def add_calvin_paths() -> None:
    for path in (CALVIN_MODELS_ROOT, CALVIN_ENV_ROOT):
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))


def required_rollout_modules() -> list[str]:
    return [
        "cv2",
        "git",
        "gym",
        "hydra",
        "omegaconf",
        "pybullet",
        "quaternion",
        "rich",
        "scipy",
    ]


def missing_rollout_modules() -> list[str]:
    add_calvin_paths()
    missing = [name for name in required_rollout_modules() if importlib.util.find_spec(name) is None]
    for name in ("calvin_agent", "calvin_env"):
        if importlib.util.find_spec(name) is None:
            missing.append(name)
    return missing


def image_tensor_from_rgb(image: np.ndarray, image_size: int) -> torch.Tensor:
    if image.ndim != 3 or image.shape[-1] != 3:
        raise ValueError(f"Expected HWC RGB image with 3 channels, got shape={image.shape}")
    tensor = torch.from_numpy(image.astype(np.float32)).permute(2, 0, 1) / 255.0
    tensor = F.interpolate(
        tensor.unsqueeze(0),
        size=(image_size, image_size),
        mode="bilinear",
        align_corners=False,
    ).squeeze(0)
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
    return (tensor - mean) / std


def normalize_state(state: np.ndarray, stats: NormalizationStats) -> np.ndarray:
    return (state.astype(np.float32) - np.asarray(stats.state_mean, dtype=np.float32)) / np.asarray(
        stats.state_std, dtype=np.float32
    )


class ACTRolloutPolicy:
    """CALVIN reset/step adapter for the homework ACT checkpoints."""

    def __init__(
        self,
        *,
        policy: Any,
        stats: NormalizationStats,
        image_size: int,
        device: torch.device,
        n_action_steps: int,
    ) -> None:
        self.policy = policy
        self.stats = stats
        self.image_size = image_size
        self.device = device
        self.n_action_steps = n_action_steps
        self._queued_actions: deque[np.ndarray] = deque()
        self.model_config: dict[str, Any] = {}

    @classmethod
    def from_checkpoint(cls, checkpoint_path: str | Path, device: torch.device) -> "ACTRolloutPolicy":
        policy, stats, checkpoint = load_policy_from_checkpoint(checkpoint_path, device)
        model_config = checkpoint["model_config"]
        rollout_policy = cls(
            policy=policy,
            stats=stats,
            image_size=int(model_config["image_size"]),
            device=device,
            n_action_steps=int(model_config.get("n_action_steps", model_config["chunk_size"])),
        )
        rollout_policy.model_config = dict(model_config)
        rollout_policy.policy.eval()
        return rollout_policy

    def reset(self) -> None:
        self._queued_actions.clear()
        if hasattr(self.policy, "reset"):
            self.policy.reset()

    @torch.no_grad()
    def step(self, obs: dict[str, Any], goal: str | None = None) -> np.ndarray:
        del goal
        if not self._queued_actions:
            self._enqueue_action_chunk(obs)
        return self._queued_actions.popleft().astype(np.float32)

    def _enqueue_action_chunk(self, obs: dict[str, Any]) -> None:
        image = obs["rgb_obs"]["rgb_static"]
        state = obs["robot_obs"]
        batch = {
            IMAGE_KEY: image_tensor_from_rgb(np.asarray(image), self.image_size).unsqueeze(0).to(self.device),
            STATE_KEY: torch.from_numpy(normalize_state(np.asarray(state), self.stats))
            .float()
            .unsqueeze(0)
            .to(self.device),
        }
        predicted = self.policy.predict_action_chunk(batch)
        actions = denormalize_actions(predicted, self.stats)[0].detach().cpu().numpy()
        for action in actions[: self.n_action_steps]:
            env_action = np.asarray(action, dtype=np.float32).copy()
            env_action[-1] = 1.0 if env_action[-1] >= 0.0 else -1.0
            self._queued_actions.append(env_action)


def ensure_validation_hydra_config(
    dataset_root: str | Path,
    *,
    scene: str = "calvin_scene_D",
    cameras: str = "static_and_gripper",
    use_egl: bool = False,
) -> Path:
    """Create the small `.hydra/merged_config.yaml` that CALVIN env expects."""

    add_calvin_paths()
    dataset_root = Path(dataset_root)
    validation_root = dataset_root / "validation"
    if not validation_root.exists():
        raise FileNotFoundError(f"Missing CALVIN validation directory: {validation_root}")
    merged_config = validation_root / ".hydra" / "merged_config.yaml"
    if merged_config.exists():
        return merged_config

    from hydra import compose, initialize_config_dir
    from hydra.core.global_hydra import GlobalHydra
    from omegaconf import OmegaConf

    config_dir = CALVIN_ENV_ROOT / "conf"
    if not config_dir.exists():
        raise FileNotFoundError(
            f"Missing CALVIN env config directory: {config_dir}. Run `git -C external/calvin submodule update --init --recursive`."
        )
    if GlobalHydra.instance().is_initialized():
        GlobalHydra.instance().clear()
    with initialize_config_dir(version_base=None, config_dir=str(config_dir)):
        cfg = compose(
            config_name="config_data_collection",
            overrides=[
                f"scene={scene}",
                f"cameras={cameras}",
                "use_vr=false",
                "record=false",
            ],
        )
    cfg.data_path = str((CALVIN_ENV_ROOT / "data").resolve()).replace("\\", "/")
    cfg.env.use_egl = bool(use_egl)
    cfg.env.use_scene_info = True
    merged_config.parent.mkdir(parents=True, exist_ok=True)
    OmegaConf.save(config=cfg, f=str(merged_config), resolve=False)
    return merged_config


@contextmanager
def temporary_numpy_seed(seed: int):
    state = np.random.get_state()
    np.random.seed(seed)
    try:
        yield
    finally:
        np.random.set_state(state)


def _fnv1_32(text: str) -> int:
    value = 0x811C9DC5
    for byte in text.encode("utf-8"):
        value = (value * 0x01000193) & 0xFFFFFFFF
        value ^= byte
    return value


def get_env_state_for_initial_condition(initial_condition: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """Mirror CALVIN's official initial-state conversion without importing its training stack."""

    robot_obs = np.array(
        [
            0.02586889,
            -0.2313129,
            0.5712808,
            3.09045411,
            -0.02908596,
            1.50013585,
            0.07999963,
            -1.21779124,
            1.03987629,
            2.11978254,
            -2.34205014,
            -0.87015899,
            1.64119093,
            0.55344928,
            1.0,
        ]
    )
    block_rot_z_range = (math.pi / 2 - math.pi / 8, math.pi / 2 + math.pi / 8)
    block_slider_left = np.array([-2.40851662e-01, 9.24044687e-02, 4.60990009e-01])
    block_slider_right = np.array([7.03416330e-02, 9.24044687e-02, 4.60990009e-01])
    block_table = [
        np.array([5.00000896e-02, -1.20000177e-01, 4.59990009e-01]),
        np.array([2.29995412e-01, -1.19995140e-01, 4.59990010e-01]),
    ]
    seed = _fnv1_32(str(initial_condition.values()))
    with temporary_numpy_seed(seed):
        np.random.shuffle(block_table)
        scene_obs = np.zeros(24)
        if initial_condition["slider"] == "left":
            scene_obs[0] = 0.28
        if initial_condition["drawer"] == "open":
            scene_obs[1] = 0.22
        scene_obs[3] = 0.088 if initial_condition["lightbulb"] == 1 else 0.0
        scene_obs[4] = initial_condition["lightbulb"]
        scene_obs[5] = initial_condition["led"]
        if initial_condition["red_block"] == "slider_right":
            scene_obs[6:9] = block_slider_right
        elif initial_condition["red_block"] == "slider_left":
            scene_obs[6:9] = block_slider_left
        else:
            scene_obs[6:9] = block_table[0]
        scene_obs[11] = np.random.uniform(*block_rot_z_range)
        if initial_condition["blue_block"] == "slider_right":
            scene_obs[12:15] = block_slider_right
        elif initial_condition["blue_block"] == "slider_left":
            scene_obs[12:15] = block_slider_left
        elif initial_condition["red_block"] == "table":
            scene_obs[12:15] = block_table[1]
        else:
            scene_obs[12:15] = block_table[0]
        scene_obs[17] = np.random.uniform(*block_rot_z_range)
        if initial_condition["pink_block"] == "slider_right":
            scene_obs[18:21] = block_slider_right
        elif initial_condition["pink_block"] == "slider_left":
            scene_obs[18:21] = block_slider_left
        else:
            scene_obs[18:21] = block_table[1]
        scene_obs[23] = np.random.uniform(*block_rot_z_range)
    return robot_obs, scene_obs


def generate_eval_sequences(num_sequences: int) -> list[tuple[dict[str, Any], Sequence[str]]]:
    add_calvin_paths()
    utils_stub = types.ModuleType("calvin_agent.evaluation.utils")
    utils_stub.temp_seed = temporary_numpy_seed
    sys.modules.setdefault("calvin_agent.evaluation.utils", utils_stub)
    from calvin_agent.evaluation.multistep_sequences import get_sequences_for_state2

    possible_conditions = {
        "led": [0, 1],
        "lightbulb": [0, 1],
        "slider": ["right", "left"],
        "drawer": ["closed", "open"],
        "red_block": ["table", "slider_right", "slider_left"],
        "blue_block": ["table", "slider_right", "slider_left"],
        "pink_block": ["table", "slider_right", "slider_left"],
        "grasped": [0],
    }
    from itertools import product

    def valid_locations(locations: Sequence[str]) -> bool:
        return locations.count("table") in [1, 2] and locations.count("slider_right") < 2 and locations.count(
            "slider_left"
        ) < 2

    combinations = filter(valid_locations, product(*possible_conditions.values()))
    initial_states = [dict(zip(possible_conditions.keys(), values)) for values in combinations]
    per_state = [len(chunk) for chunk in np.array_split(range(num_sequences), len(initial_states))]
    results: list[tuple[dict[str, Any], Sequence[str]]] = []
    with temporary_numpy_seed(0):
        for index, (state, count) in enumerate(zip(initial_states, per_state)):
            for sequence in get_sequences_for_state2((state, count, index)):
                results.append((state, tuple(sequence)))
        np.random.shuffle(results)
    return results[:num_sequences]


def count_success(results: Sequence[int]) -> list[float]:
    counts = Counter(results)
    return [sum(counts[j] for j in reversed(range(i, 6))) / len(results) for i in range(1, 6)]


def evaluate_sequence(
    *,
    env: Any,
    model: ACTRolloutPolicy,
    task_oracle: Any,
    initial_state: dict[str, Any],
    eval_sequence: Sequence[str],
    val_annotations: Any,
    ep_len: int,
) -> int:
    robot_obs, scene_obs = get_env_state_for_initial_condition(initial_state)
    env.reset(robot_obs=robot_obs, scene_obs=scene_obs)
    success_counter = 0
    for subtask in eval_sequence:
        obs = env.get_obs()
        lang_annotation = val_annotations[subtask][0]
        model.reset()
        start_info = env.get_info()
        success = False
        for _ in range(ep_len):
            action = model.step(obs, str(lang_annotation))
            obs, _, _, current_info = env.step(action)
            task_info = task_oracle.get_task_info_for_set(start_info, current_info, {subtask})
            if len(task_info) > 0:
                success = True
                break
        if not success:
            return success_counter
        success_counter += 1
    return success_counter


def evaluate_rollout(
    *,
    checkpoint_path: str | Path,
    dataset_root: str | Path,
    device: torch.device,
    max_sequences: int,
    ep_len: int,
    scene: str,
    use_egl: bool,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    add_calvin_paths()
    ensure_validation_hydra_config(dataset_root, scene=scene, use_egl=use_egl)

    import hydra
    from calvin_env.envs.play_table_env import get_env
    from omegaconf import OmegaConf

    conf_dir = CALVIN_MODELS_ROOT / "conf"
    task_cfg = OmegaConf.load(conf_dir / "callbacks" / "rollout" / "tasks" / "new_playtable_tasks.yaml")
    task_oracle = hydra.utils.instantiate(task_cfg)
    val_annotations = OmegaConf.load(conf_dir / "annotations" / "new_playtable_validation.yaml")
    env = get_env(Path(dataset_root) / "validation", show_gui=False)
    model = ACTRolloutPolicy.from_checkpoint(checkpoint_path, device)
    sequences = generate_eval_sequences(max_sequences)

    results = []
    details = []
    try:
        for index, (initial_state, sequence) in enumerate(sequences):
            successful = evaluate_sequence(
                env=env,
                model=model,
                task_oracle=task_oracle,
                initial_state=initial_state,
                eval_sequence=sequence,
                val_annotations=val_annotations,
                ep_len=ep_len,
            )
            results.append(successful)
            details.append(
                {
                    "sequence_index": index,
                    "initial_state": initial_state,
                    "sequence": list(sequence),
                    "successful_subtasks": successful,
                }
            )
            print(f"sequence {index + 1}/{len(sequences)}: {successful}/5 subtasks")
    finally:
        close = getattr(env, "close", None)
        if callable(close):
            close()
            if hasattr(env, "ownsPhysicsClient"):
                env.ownsPhysicsClient = False
            env.close = lambda: None

    chain_success = count_success(results) if results else [0.0] * 5
    metrics = {
        "rollout/avg_successful_sequence_length": float(np.mean(results)) if results else 0.0,
        "rollout/success_rate_1": chain_success[0],
        "rollout/success_rate_2": chain_success[1],
        "rollout/success_rate_3": chain_success[2],
        "rollout/success_rate_4": chain_success[3],
        "rollout/success_rate_5": chain_success[4],
        "rollout/evaluated_sequences": float(len(results)),
        "rollout/ep_len": float(ep_len),
    }
    return metrics, details


def write_metrics_csv(path: Path, metrics: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["step", *metrics.keys()])
        writer.writeheader()
        writer.writerow({"step": 0, **metrics})


def write_blocker(run_dir: Path, payload: dict[str, Any]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "rollout_blocker.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_metrics_csv(run_dir / "metrics.csv", {"rollout/status_blocked": 1.0})


def run_rollout_cli(args: Any) -> int:
    config = load_yaml(args.config)
    paths = resolve_paths()
    output_root = args.output_root or paths.output_root
    run_dir = output_root / args.run_name
    device = torch.device(args.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    missing = missing_rollout_modules()
    payload = {
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "dataset_root": str(Path(args.dataset_root).resolve()),
        "run_name": args.run_name,
        "max_sequences": args.max_sequences,
        "ep_len": args.ep_len,
        "device": str(device),
        "scene": args.scene,
        "use_egl": bool(args.use_egl),
        "missing_modules": missing,
    }
    if missing:
        payload.update(
            {
                "status": "blocked",
                "blocker": "missing_calvin_rollout_dependencies",
                "install_hint": "Run scripts/bootstrap.ps1 -WithCalvinRollout, then retry the same command.",
            }
        )
        write_blocker(run_dir, payload)
        tracker = ExperimentTracker(
            run_dir=run_dir,
            project=config["swanlab"]["project"],
            experiment_name=args.run_name,
            config=payload,
            mode=config["swanlab"].get("mode"),
        )
        tracker.log({"rollout/status_blocked": 1.0}, step=0)
        tracker.finish()
        print(json.dumps(payload, indent=2))
        return 0 if args.check_only else 2
    if args.check_only:
        ensure_validation_hydra_config(args.dataset_root, scene=args.scene, use_egl=bool(args.use_egl))
        payload["status"] = "ready"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "rollout_preflight.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 0

    metrics, details = evaluate_rollout(
        checkpoint_path=args.checkpoint,
        dataset_root=args.dataset_root,
        device=device,
        max_sequences=args.max_sequences,
        ep_len=args.ep_len,
        scene=args.scene,
        use_egl=bool(args.use_egl),
    )
    payload.update({"status": "completed", **metrics})
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "rollout_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (run_dir / "rollout_sequences.json").write_text(json.dumps(details, indent=2), encoding="utf-8")
    write_metrics_csv(run_dir / "metrics.csv", metrics)
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
    return 0
