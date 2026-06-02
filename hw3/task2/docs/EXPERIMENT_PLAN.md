# Experiment Plan

## Required comparison

Train two policies with exactly the same ACT architecture and optimizer
hyperparameters:

| Run | Training environments | Evaluation environment |
| --- | --- | --- |
| `act_b_only` | B | D |
| `act_abc_joint` | A+B+C | D |

Use `configs/calvin_act.yaml` for both runs. Only the `--environments` argument
changes.

## Resource-aware progression

1. Run `scripts/run_smoke.ps1`.
2. Fetch an official partial dataset with `scripts/download_calvin_subset.py`.
3. Inspect GPU memory and step time with a short formal run using
   `--max-steps 20`.
4. Keep `image_size: 128`, `batch_size: 4`, and `max_train_samples: 50000` as
   the initial 8 GB GPU profile.
5. Increase `max_steps` or the subset size only after the profile is stable.
6. Save final best checkpoints to cloud storage instead of Git.

## Metrics

- `train/l1_loss`: ACT reconstruction Action L1 Loss.
- `train/kld_loss`: VAE regularization term.
- `validation/loss`: held-out in-distribution training-scene loss.
- `zero_shot/first_action_mae`: D-environment first predicted action error.
- `zero_shot/chunk_action_mae`: D-environment full valid action-chunk error.

## Interpretation prompts

- Does ABC joint training reduce D action MAE relative to B-only training?
- Does the training curve become noisier when multiple visual layouts are mixed?
- Does chunk-level MAE diverge more strongly than first-action MAE under visual
  shift?
- Is the chunk size long enough to smooth short-term prediction noise without
  becoming brittle when the D scene differs visually?
