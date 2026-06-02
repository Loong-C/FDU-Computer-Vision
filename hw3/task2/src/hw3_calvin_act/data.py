from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset

IMAGE_KEY = "observation.images.top"
STATE_KEY = "observation.state"
ACTION_KEY = "action"
PAD_KEY = "action_is_pad"
FRAME_PATTERN = re.compile(r"episode_(\d+)\.npz$")
ENVIRONMENT_KEYS = {
    "A": "calvin_scene_A",
    "B": "calvin_scene_B",
    "C": "calvin_scene_C",
    "D": "calvin_scene_D",
}


@dataclass(frozen=True)
class SceneRange:
    environment: str
    start: int
    end: int

    def contains(self, frame_index: int) -> bool:
        return self.start <= frame_index <= self.end


@dataclass(frozen=True)
class NormalizationStats:
    state_mean: list[float]
    state_std: list[float]
    action_mean: list[float]
    action_std: list[float]

    @classmethod
    def from_arrays(cls, states: np.ndarray, actions: np.ndarray) -> "NormalizationStats":
        return cls(
            state_mean=states.mean(axis=0).tolist(),
            state_std=np.maximum(states.std(axis=0), 1e-6).tolist(),
            action_mean=actions.mean(axis=0).tolist(),
            action_std=np.maximum(actions.std(axis=0), 1e-6).tolist(),
        )

    @classmethod
    def from_dict(cls, payload: dict) -> "NormalizationStats":
        return cls(**payload)

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


def parse_frame_index(path: str | Path) -> int:
    match = FRAME_PATTERN.search(Path(path).name)
    if not match:
        raise ValueError(f"Not a CALVIN frame file: {path}")
    return int(match.group(1))


def discover_frame_files(split_root: str | Path) -> dict[int, Path]:
    split_root = Path(split_root)
    paths = sorted(split_root.glob("episode_*.npz"))
    if not paths:
        paths = sorted(split_root.rglob("episode_*.npz"))
    frames = {parse_frame_index(path): path for path in paths}
    if not frames:
        raise FileNotFoundError(f"No episode_*.npz CALVIN frames found under {split_root}")
    return frames


def load_scene_ranges(split_root: str | Path, environments: str) -> list[SceneRange]:
    split_root = Path(split_root)
    requested = list(dict.fromkeys(environments.upper()))
    invalid = sorted(set(requested) - set(ENVIRONMENT_KEYS))
    if invalid:
        raise ValueError(f"Unsupported environments: {invalid}. Expected a subset of ABCD.")

    scene_info_path = split_root / "scene_info.npy"
    if not scene_info_path.exists():
        if requested == ["D"]:
            return [SceneRange(environment="D", start=0, end=2**63 - 1)]
        raise FileNotFoundError(
            f"Missing {scene_info_path}. Download the official scene_info fix or provide scene_info.npy."
        )

    payload = np.load(scene_info_path, allow_pickle=True).item()
    ranges = []
    for environment in requested:
        key = ENVIRONMENT_KEYS[environment]
        if key not in payload:
            if environment == "D" and len(payload) == 1:
                only_value = next(iter(payload.values()))
                ranges.append(SceneRange(environment=environment, start=int(only_value[0]), end=int(only_value[1])))
                continue
            raise KeyError(f"Scene metadata does not contain {key}: {scene_info_path}")
        start, end = payload[key]
        ranges.append(SceneRange(environment=environment, start=int(start), end=int(end)))
    return ranges


def _evenly_spaced(values: Sequence[int], max_items: int | None) -> list[int]:
    if max_items is None or len(values) <= max_items:
        return list(values)
    if max_items <= 0:
        raise ValueError("max_items must be positive when provided.")
    positions = np.linspace(0, len(values) - 1, num=max_items, dtype=np.int64)
    return [values[position] for position in positions]


class CalvinRawDataset(Dataset):
    """Lazy adapter for the official CALVIN per-frame npz format."""

    def __init__(
        self,
        dataset_root: str | Path,
        split: str,
        environments: str,
        chunk_size: int,
        image_size: int,
        max_samples: int | None = None,
        stride: int = 1,
        stats: NormalizationStats | None = None,
        sample_indices: Sequence[int] | None = None,
    ) -> None:
        self.dataset_root = Path(dataset_root)
        self.split = split
        self.split_root = self.dataset_root / split
        self.environments = environments.upper()
        self.chunk_size = chunk_size
        self.image_size = image_size
        self.stats = stats
        self.frame_files = discover_frame_files(self.split_root)
        self.scene_ranges = load_scene_ranges(self.split_root, self.environments)

        if sample_indices is None:
            eligible = [
                index
                for index in sorted(self.frame_files)
                if any(scene_range.contains(index) for scene_range in self.scene_ranges)
            ]
            eligible = eligible[::stride]
            self.sample_indices = _evenly_spaced(eligible, max_samples)
        else:
            self.sample_indices = list(sample_indices)
        if not self.sample_indices:
            raise ValueError(f"No frames selected from {self.split_root} for environments={self.environments}")

    def __len__(self) -> int:
        return len(self.sample_indices)

    def subset(self, sample_indices: Sequence[int]) -> "CalvinRawDataset":
        return CalvinRawDataset(
            dataset_root=self.dataset_root,
            split=self.split,
            environments=self.environments,
            chunk_size=self.chunk_size,
            image_size=self.image_size,
            stats=self.stats,
            sample_indices=sample_indices,
        )

    def with_stats(self, stats: NormalizationStats) -> "CalvinRawDataset":
        return CalvinRawDataset(
            dataset_root=self.dataset_root,
            split=self.split,
            environments=self.environments,
            chunk_size=self.chunk_size,
            image_size=self.image_size,
            stats=stats,
            sample_indices=self.sample_indices,
        )

    @lru_cache(maxsize=256)
    def _load_frame(self, frame_index: int) -> dict[str, np.ndarray]:
        path = self.frame_files[frame_index]
        with np.load(path) as frame:
            return {key: frame[key].copy() for key in frame.files}

    def _same_scene(self, source: int, target: int) -> bool:
        return any(scene_range.contains(source) and scene_range.contains(target) for scene_range in self.scene_ranges)

    def raw_state_action(self, frame_index: int) -> tuple[np.ndarray, np.ndarray]:
        frame = self._load_frame(frame_index)
        return frame["robot_obs"].astype(np.float32), frame["rel_actions"].astype(np.float32)

    def _normalized_state(self, state: np.ndarray) -> np.ndarray:
        if self.stats is None:
            return state
        return (state - np.asarray(self.stats.state_mean)) / np.asarray(self.stats.state_std)

    def _normalized_action(self, action: np.ndarray) -> np.ndarray:
        if self.stats is None:
            return action
        return (action - np.asarray(self.stats.action_mean)) / np.asarray(self.stats.action_std)

    def _image_tensor(self, image: np.ndarray) -> torch.Tensor:
        tensor = torch.from_numpy(image.astype(np.float32)).permute(2, 0, 1) / 255.0
        tensor = F.interpolate(
            tensor.unsqueeze(0),
            size=(self.image_size, self.image_size),
            mode="bilinear",
            align_corners=False,
        ).squeeze(0)
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        return (tensor - mean) / std

    def __getitem__(self, item: int) -> dict[str, torch.Tensor]:
        frame_index = self.sample_indices[item]
        frame = self._load_frame(frame_index)
        actions = []
        is_pad = []
        for offset in range(self.chunk_size):
            target_index = frame_index + offset
            if target_index in self.frame_files and self._same_scene(frame_index, target_index):
                action = self._load_frame(target_index)["rel_actions"].astype(np.float32)
                actions.append(self._normalized_action(action))
                is_pad.append(False)
            else:
                actions.append(np.zeros_like(frame["rel_actions"], dtype=np.float32))
                is_pad.append(True)
        state = self._normalized_state(frame["robot_obs"].astype(np.float32))
        return {
            IMAGE_KEY: self._image_tensor(frame["rgb_static"]),
            STATE_KEY: torch.from_numpy(np.asarray(state, dtype=np.float32)),
            ACTION_KEY: torch.from_numpy(np.asarray(actions, dtype=np.float32)),
            PAD_KEY: torch.tensor(is_pad, dtype=torch.bool),
        }


def fit_normalization_stats(dataset: CalvinRawDataset, max_samples: int = 2048) -> NormalizationStats:
    indices = _evenly_spaced(dataset.sample_indices, min(max_samples, len(dataset)))
    states = []
    actions = []
    for frame_index in indices:
        state, action = dataset.raw_state_action(frame_index)
        states.append(state)
        actions.append(action)
    return NormalizationStats.from_arrays(np.asarray(states), np.asarray(actions))


def split_sample_indices(
    sample_indices: Sequence[int], validation_fraction: float, seed: int
) -> tuple[list[int], list[int]]:
    if not 0.0 < validation_fraction < 1.0:
        raise ValueError("validation_fraction must be between 0 and 1.")
    rng = np.random.default_rng(seed)
    indices = np.asarray(sample_indices)
    rng.shuffle(indices)
    validation_size = max(1, int(round(len(indices) * validation_fraction)))
    if validation_size >= len(indices):
        validation_size = len(indices) - 1
    return indices[validation_size:].tolist(), indices[:validation_size].tolist()


def denormalize_actions(actions: torch.Tensor, stats: NormalizationStats) -> torch.Tensor:
    mean = torch.tensor(stats.action_mean, dtype=actions.dtype, device=actions.device)
    std = torch.tensor(stats.action_std, dtype=actions.dtype, device=actions.device)
    return actions * std + mean


def move_batch_to_device(batch: dict[str, torch.Tensor], device: torch.device) -> dict[str, torch.Tensor]:
    return {key: value.to(device, non_blocking=True) for key, value in batch.items()}


def iter_frame_indices(dataset: CalvinRawDataset) -> Iterable[int]:
    return iter(dataset.sample_indices)
