from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import torch

from hw3_calvin_act.data import (
    CalvinRawDataset,
    fit_normalization_stats,
    group_sample_indices_by_sequence,
    split_sample_indices,
)
from hw3_calvin_act.remote_subset import choose_window_frames, parse_frame_filename, safe_output_path


def generate_smoke_data(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    output_root = tmp_path / "smoke"
    subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "generate_smoke_data.py"),
            "--output-root",
            str(output_root),
            "--frames-per-env",
            "6",
        ],
        check=True,
    )
    return output_root


def test_b_only_and_abc_scene_filtering(tmp_path: Path) -> None:
    smoke_root = generate_smoke_data(tmp_path)
    kwargs = {
        "dataset_root": smoke_root / "task_ABC_D",
        "split": "training",
        "chunk_size": 4,
        "image_size": 64,
    }
    b_dataset = CalvinRawDataset(environments="B", **kwargs)
    abc_dataset = CalvinRawDataset(environments="ABC", **kwargs)

    assert len(b_dataset) == 6
    assert len(abc_dataset) == 18
    assert b_dataset.sample_indices == [0, 1, 2, 23, 24, 25]


def test_batch_shape_and_padding(tmp_path: Path) -> None:
    smoke_root = generate_smoke_data(tmp_path)
    dataset = CalvinRawDataset(
        dataset_root=smoke_root / "task_ABC_D",
        split="training",
        environments="B",
        chunk_size=4,
        image_size=64,
    )
    stats = fit_normalization_stats(dataset)
    batch = dataset.with_stats(stats)[-1]

    assert batch["observation.images.top"].shape == (3, 64, 64)
    assert batch["observation.state"].shape == (15,)
    assert batch["action"].shape == (4, 7)
    assert torch.equal(batch["action_is_pad"], torch.tensor([False, True, True, True]))


def test_train_validation_split_is_disjoint(tmp_path: Path) -> None:
    smoke_root = generate_smoke_data(tmp_path)
    dataset = CalvinRawDataset(
        dataset_root=smoke_root / "task_ABC_D",
        split="training",
        environments="ABC",
        chunk_size=4,
        image_size=64,
    )
    train_indices, validation_indices = split_sample_indices(
        dataset.sample_indices,
        0.2,
        seed=7,
        available_frame_indices=dataset.frame_files,
        scene_ranges=dataset.scene_ranges,
    )
    train_action_frames = {
        action_index for sample_index in train_indices for action_index in dataset.action_frame_indices(sample_index)
    }
    validation_action_frames = {
        action_index
        for sample_index in validation_indices
        for action_index in dataset.action_frame_indices(sample_index)
    }

    assert set(train_indices).isdisjoint(validation_indices)
    assert sorted(train_indices + validation_indices) == dataset.sample_indices
    assert train_action_frames.isdisjoint(validation_action_frames)
    assert {len(groups) for groups in group_sample_indices_by_sequence(
        dataset.sample_indices,
        available_frame_indices=dataset.frame_files,
        scene_ranges=dataset.scene_ranges,
    ).values()} == {2}


def test_remote_subset_window_selection_and_paths(tmp_path: Path) -> None:
    frames = choose_window_frames(list(range(20)), ranges=[(0, 9), (10, 19)], windows_per_range=2, window_size=3)

    assert frames == [0, 1, 2, 7, 8, 9, 10, 11, 12, 17, 18, 19]
    assert parse_frame_filename("task_ABC_D/training/episode_0000012.npz", "task_ABC_D", "training") == 12
    assert safe_output_path(tmp_path, "task_ABC_D/training/episode_0000012.npz").is_relative_to(tmp_path)


def test_remote_subset_skips_trajectory_gaps() -> None:
    frames = choose_window_frames([0, 1, 2, 10, 11, 12], ranges=[(0, 12)], windows_per_range=2, window_size=3)

    assert frames == [0, 1, 2, 10, 11, 12]
