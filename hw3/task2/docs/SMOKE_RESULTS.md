# Synthetic Smoke Results

These numbers are implementation checks only. They come from the generated
CALVIN-shaped synthetic dataset and must not be reported as formal homework
results.

## Verification environment

| Item | Value |
| --- | --- |
| GPU | NVIDIA GeForce RTX 4060 Ti, 8 GB |
| Python | 3.12.9 |
| PyTorch | 2.11.0+cu128 |
| Torchvision | 0.26.0+cu128 |
| LeRobot | 0.5.1 |
| SwanLab | 0.7.16, offline mode |

## End-to-end checks

- B-only ACT optimization: passed.
- A+B+C ACT optimization: passed.
- SwanLab offline logging: passed.
- Best and latest checkpoint writing: passed.
- D zero-shot action-error evaluation: passed.
- Training and evaluation plot generation: passed.

## Two-step synthetic metrics

| Run | Held-out L1 loss at step 2 | D first-action MAE | D chunk MAE |
| --- | ---: | ---: | ---: |
| B-only | 0.907972 | 0.287660 | 0.285675 |
| A+B+C | 0.994025 | 0.337615 | 0.323337 |

The smoke run is deliberately tiny, so the relative ordering is not meaningful.
Its purpose is to prove that the complete workflow executes before spending
time or disk space on official CALVIN data.

## Official-frame subset smoke

`scripts/run_official_subset_smoke.ps1` was also verified against HTTP-Range
downloads from the official CALVIN ZIP files. This second check used one
consecutive four-frame window per environment: 12 ABC frames and 4 unseen-D
frames.

| Run | Held-out L1 loss at step 2 | D first-action MAE | D chunk MAE |
| --- | ---: | ---: | ---: |
| B-only | 0.941828 | 0.083004 | 0.102024 |
| A+B+C | 1.387035 | 0.073969 | 0.085186 |

These official-frame values remain smoke metrics, not final report results. The
subset and two optimization steps are intentionally too small for scientific
interpretation.
