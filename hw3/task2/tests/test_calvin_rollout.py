from __future__ import annotations

import numpy as np
import torch

from hw3_calvin_act.calvin_rollout import ACTRolloutPolicy, image_tensor_from_rgb, normalize_state
from hw3_calvin_act.data import IMAGE_KEY, STATE_KEY, NormalizationStats


class DummyPolicy:
    def __init__(self) -> None:
        self.calls = 0

    def predict_action_chunk(self, batch):
        self.calls += 1
        assert batch[IMAGE_KEY].shape == (1, 3, 32, 32)
        assert batch[STATE_KEY].shape == (1, 15)
        return torch.tensor(
            [
                [
                    [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, -0.2],
                    [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 0.2],
                ]
            ]
        )


def unit_stats() -> NormalizationStats:
    return NormalizationStats(
        state_mean=[0.0] * 15,
        state_std=[1.0] * 15,
        action_mean=[0.0] * 7,
        action_std=[1.0] * 7,
    )


def test_image_and_state_preprocessing_shapes() -> None:
    image = np.zeros((64, 80, 3), dtype=np.uint8)
    state = np.arange(15, dtype=np.float32)

    assert image_tensor_from_rgb(image, image_size=32).shape == (3, 32, 32)
    assert normalize_state(state, unit_stats()).shape == (15,)


def test_act_rollout_policy_queues_action_chunk() -> None:
    policy = DummyPolicy()
    adapter = ACTRolloutPolicy(
        policy=policy,
        stats=unit_stats(),
        image_size=32,
        device=torch.device("cpu"),
        n_action_steps=2,
    )
    obs = {
        "rgb_obs": {"rgb_static": np.zeros((64, 64, 3), dtype=np.uint8)},
        "robot_obs": np.ones(15, dtype=np.float32),
    }

    first = adapter.step(obs, "open the drawer")
    second = adapter.step(obs, "open the drawer")

    np.testing.assert_allclose(first, np.array([1, 2, 3, 4, 5, 6, -1], dtype=np.float32))
    np.testing.assert_allclose(second, np.array([2, 3, 4, 5, 6, 7, 1], dtype=np.float32))
    assert policy.calls == 1
