# HW3 Task 2 Report Draft: Cross-environment Generalization with LeRobot ACT

> Submission note: replace the member placeholders below before submitting the
> PDF. The technical content and experiment links are populated from the
> verified formal run.

## Group Information

| Item | Value |
| --- | --- |
| Member name(s) | `TODO: fill before submission` |
| Student ID(s) | `TODO: fill before submission` |
| Responsibility split | `TODO: fill before submission` |

## External Links

- Public GitHub repository:
  https://github.com/Loong-C/FDU-Computer-Vision/tree/hw3/hw3/task2
- Model-weight release:
  https://github.com/Loong-C/computer-vision-hw3-task2-calvin-act/releases/tag/formal-partial-v1
- SwanLab project:
  https://swanlab.cn/@Linkukai/hw3-calvin-act

## 1. Background

This task evaluates whether visual diversity during policy training improves
cross-environment generalization. We train a LeRobot ACT policy on CALVIN
environment B and compare it against the same policy architecture trained on a
mixed A+B+C dataset. Both policies are evaluated zero-shot on the unseen D
environment.

## 2. Dataset

The official CALVIN metadata defines the following inclusive training-frame
ranges:

| Environment | Frame range |
| --- | ---: |
| B | `0..598909` |
| C | `598910..1191338` |
| A | `1191339..1795044` |

The complete A+B+C archive is 517 GB and the D archive is 166 GB. To keep the
experiment feasible on local hardware, we implement an HTTP-Range downloader
that fetches only evenly sampled consecutive official frame windows while
preserving the CALVIN directory format and validating CRC checksums.

The reported run uses 2304 A+B+C training frames and 768 D evaluation frames.
With `stride: 3` and a 90/10 train-validation split, the B-only policy uses 230
training samples and the A+B+C policy uses 691 training samples.

## 3. Method

ACT predicts a chunk of future actions from the current visual observation and
robot state. Instead of selecting a single action independently at each step,
the policy models a short action sequence. This can reduce sensitivity to
single-frame noise and support temporally coherent control.

We use the upstream LeRobot `ACTPolicy` from release `v0.5.1`. Both experiments
use identical architecture and optimizer settings. Only the selected training
environments differ.

| Item | Value |
| --- | --- |
| Vision backbone | ResNet-18 |
| Image size | 128 |
| Transformer model dimension | 256 |
| Encoder / decoder layers | 3 / 1 |
| Action chunk size | 20 |
| VAE latent dimension | 32 |
| Batch size | 4 |
| Optimizer | AdamW |
| Learning rate | `1e-5` |
| Weight decay | `1e-4` |
| Training steps | 5000 |
| GPU | NVIDIA GeForce RTX 4060 Ti, 8 GB |

## 4. Results

![Formal training and validation curves](images/formal_training_curves.svg)

| Run | Final held-out validation L1 | D first-action MAE | D chunk MAE |
| --- | ---: | ---: | ---: |
| B-only | 0.324629 | 0.226251 | 0.259475 |
| A+B+C | 0.386954 | 0.187712 | 0.229145 |

![Formal unseen-D first-action error](images/formal_zero_shot_d_action_error.svg)

Formal SwanLab runs:

| Run | URL |
| --- | --- |
| B-only training | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/y34dmlyk6ol06me1f1ig0 |
| A+B+C training | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/t3kfag5dsiipp3wwxy4te |
| B-only to D evaluation | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/b1hdsdo4vgrodwkk3syr7 |
| A+B+C to D evaluation | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/5ooypxeqhgp4xja928tpk |

## 5. Analysis

The A+B+C model has a higher held-out validation L1 loss than the B-only model
because it must fit three visually distinct scenes. Despite this more difficult
training distribution, it generalizes better to unseen D: first-action MAE
drops from 0.226251 to 0.187712 (`17.0%`), and chunk-action MAE drops from
0.259475 to 0.229145 (`11.7%`).

The chunk-level improvement is smaller than the first-action improvement. This
is expected: longer-horizon predictions accumulate more uncertainty under
visual distribution shift. However, the A+B+C model still improves at chunk
level, indicating that its 20-step action chunks remain robust on the sampled D
frames instead of becoming brittle.

## 6. Limitations

This resource-aware experiment evaluates action error on sampled official D
frames, as permitted by the homework specification. It does not report CALVIN
simulator rollout success rate. A full simulator evaluation can be added from
WSL or Linux if required. The sampled subset is intentionally much smaller than
the complete archives, so the conclusions apply to the reported protocol.

## 7. Reproducibility

Run:

```powershell
.\scripts\bootstrap.ps1
.\scripts\run_partial_formal.ps1
```

The formal wrapper downloads the bounded subset, trains both policies with the
same config, resumes from `latest.pt` when present, evaluates D action error,
and regenerates plots.

Final checkpoints:

| Run | Download | SHA256 |
| --- | --- | --- |
| B-only | [best.pt](https://github.com/Loong-C/computer-vision-hw3-task2-calvin-act/releases/download/formal-partial-v1/hw3-task2-act-b-only-best.pt) | `58AFAE052EF2CE029F92C9258E1B5012A9C44FAC5753C1C8330B7D196A976131` |
| A+B+C | [best.pt](https://github.com/Loong-C/computer-vision-hw3-task2-calvin-act/releases/download/formal-partial-v1/hw3-task2-act-abc-joint-best.pt) | `1B1F182E61026929F0A5FFDC5EE096D15E4771FEBD111D9EFE3D88BC4A9ADCFF` |

The source tree is consolidated in `FDU-Computer-Vision`. These verified weight
files remain on the legacy release temporarily until the assets are copied to
an FDU repository release.
The migration helper is `scripts/publish_fdu_release.ps1`; run it after
GitHub CLI authentication is restored.
