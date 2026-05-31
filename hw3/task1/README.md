# CV HW3 Task 1: 2DGS and AIGC Asset Fusion

This directory implements Task 1 of the final computer vision assignment:
multi-source 3D asset generation and real-scene fusion based on 2D Gaussian
Splatting (2DGS) and AIGC.

## Objective

The goal is to reconstruct or generate three independent 3D object assets using different technical routes, reconstruct a real background scene using 2D Gaussian Splatting, insert the three assets into the same scene, and render a multi-view walkthrough video.

## Pipeline

The project contains the following stages:

- Object A: real multi-view reconstruction using phone-captured images or video, COLMAP, and 2DGS.
- Object B: text-to-3D generation using threestudio and SDS-based optimization.
- Object C: single-image-to-3D generation using a phone-captured image and Magic123.
- Background: reconstruction of an open-source real scene, such as a Mip-NeRF 360 scene, using 2DGS.
- Fusion: alignment, scaling, insertion, and rendering of the three object assets inside the reconstructed background scene.
- Evaluation: comparison of multi-view reconstruction, text-to-3D generation, and single-image-to-3D generation in terms of geometry, texture, and computational cost.

## Experiment Tracking

SwanLab is the default tracker. `scripts/run_2dgs_experiment.py` runs the
official 2DGS trainer, tees terminal output to `logs/`, imports TensorBoard
scalars, and records them in `swanlog/`. Generated logs remain local and are
excluded from Git. Non-training setup milestones are recorded with
`scripts/log_pipeline_event.py`.

## Repository Structure

```text
configs/        configuration files for reconstruction and generation
data/           raw and processed datasets, not tracked by Git
docs/           report materials and exported figures
external/       third-party repositories
notes/          experiment logs and time-cost records
outputs/        trained models, generated assets, rendered images, and videos
scripts/        runnable scripts for each stage
```

## WSL Environment

GPU training is run in WSL. The verified Object A environment uses Python 3.8,
PyTorch 2.1.2 with CUDA 11.8, TensorBoard 2.14, SwanLab 0.7.19, and Open3D
0.19. Install the official 2DGS repository separately:

```bash
git clone https://github.com/hbb1/2d-gaussian-splatting.git \
  external/2d-gaussian-splatting --recursive
conda env create --file external/2d-gaussian-splatting/environment.yml
conda activate surfel_splatting
pip install 'swanlab[dashboard]' tensorboard open3d
```

The current machine uses an equivalent environment named `cv_hw3_2dgs`.

The AIGC methods use isolated Python 3.10 environments. The helper script keeps
the CUDA compiler and GCC toolchain inside Conda because the WSL host does not
provide a system `nvcc`:

```bash
bash scripts/setup_aigc_envs.sh bootstrap
bash scripts/setup_aigc_envs.sh toolchain
bash scripts/setup_aigc_envs.sh torch
bash scripts/setup_aigc_envs.sh threestudio-deps
bash scripts/setup_aigc_envs.sh magic123-deps
```

The two environments are named `cv_hw3_threestudio` and `cv_hw3_magic123`.
CUDA 11.8 and GCC 11 are used for locally compiled PyTorch extensions.

## Object A

Place phone-captured multi-view images in `data/raw/object_a_images/`. Prepare
the undistorted COLMAP dataset and train 2DGS:

```bash
conda activate cv_hw3_2dgs
bash scripts/prepare_colmap_object_a.sh --force
bash scripts/train_2dgs_object_a.sh
```

Render images separately from mesh extraction:

```bash
bash scripts/render_2dgs_asset.sh outputs/object_a_2dgs/object-a-2dgs-full 30000
bash scripts/export_2dgs_mesh.sh outputs/object_a_2dgs/object-a-2dgs-full 30000
```

The mesh helper uses coarse bounded TSDF defaults because the official inferred
defaults exceeded the available WSL memory on the baseline run.

## Background

Download one Mip-NeRF 360 scene and place it at
`data/processed/background_counter/`. The selected `counter` scene can be
downloaded from a selective Hugging Face mirror with resume support:

```bash
bash scripts/download_background_counter.sh
```

Train it with:

```bash
conda activate cv_hw3_2dgs
bash scripts/train_2dgs_background.sh
```

## AIGC Assets

- Object B: generate a mesh from a text prompt using threestudio and SDS loss.
- Object C: prepare the RGB checkerboard input, then generate a full 3D asset
  with Magic123:
  `python scripts/prepare_object_c_image.py --swanlab-mode local`.
- Fusion: export assets as meshes and compose them with the background in
  Blender for the final walkthrough video.
