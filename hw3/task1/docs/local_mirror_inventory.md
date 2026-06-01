# Windows Local Mirror Inventory

Generated on `2026-06-01` after the Task 1 finalization run.

## Locations

- Canonical Git workspace in WSL:
  `/home/hp/cv_hw3/FDU-Computer-Vision/hw3/task1`
- Browsable Windows mirror:
  `F:\Personal\Code\Computer Vision\hw3\task1`
- Release-package source cache:
  `D:\PackageCache\cv-hw3-task1-release`

## Mirrored to Windows

The Windows mirror contains the complete reviewable and reproducible Task 1
artifact set:

- `outputs/`: all formal runs, smoke runs, exported meshes, renders, and fusion
  outputs (`3363` files, about `4.15 GiB`).
- `logs/`: all wrapper metadata, terminal logs, readiness audits, and recovery
  records.
- `swanlog/`: local SwanLab runs and imported metric histories.
- `data/`: phone images, COLMAP inputs, Mip-NeRF360 counter data, and Object C
  raw/processed images.
- `report/`, `docs/`, and `notes/`: final PDF, plots, previews, report metadata,
  experiment log, runtime table, and report outline.
- `configs/`, `scripts/`, `patches/`, and `tools/`: reproducibility helpers and
  tracked configurations.
- `external/`: source mirrors for `2d-gaussian-splatting`, `threestudio`, and
  `Magic123`, plus the prepared Object C medicine-box input.
- `release/`: unpacked best weights, the public release archive, SHA-256,
  manifest, public URLs, and release notes.

The Windows path
`data\processed\background_counter` is a junction to
`data\raw\mipnerf360\counter`, matching the WSL symlink without duplicating the
background dataset.

## Deliberately Kept in WSL

The following Linux-specific or redownloadable dependencies remain in WSL to
avoid redundant copies:

- `external/Magic123/pretrained/zero123` (about `15 GiB`)
- `external/Magic123/pretrained/midas` (about `1.5 GiB`)
- `external/blender` portable Linux runtime (about `1.3 GiB`)
- vendored repository `.git` metadata, build caches, and temporary files

These are dependencies rather than Task 1 submission artifacts. Setup and
download helpers remain available under `scripts/`.

## Direct Deliverables

- Final PDF:
  `F:\Personal\Code\Computer Vision\hw3\task1\report\cv_hw3_task1_report.pdf`
- Walkthrough MP4:
  `F:\Personal\Code\Computer Vision\hw3\task1\outputs\fusion\task1-walkthrough.mp4`
- Release package:
  `F:\Personal\Code\Computer Vision\hw3\task1\release\cv-hw3-task1-best-weights.tar.gz`

