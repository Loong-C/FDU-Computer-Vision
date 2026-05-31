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

Export TensorBoard scalar summaries for report tables with:

```bash
python scripts/summarize_tensorboard.py \
  --input outputs/object_a_2dgs/object-a-2dgs-full \
  --steps 7000,30000 \
  --output logs/object-a-2dgs-full-summary.json
```

Inspect machine-readable completion status with:

```bash
python scripts/check_task1_readiness.py --output logs/task1-readiness.json
```

Build the report figures, export a PDF draft, and render its pages for visual
inspection with:

```bash
conda activate cv_hw3_threestudio
python report/build_report_assets.py
python report/generate_report.py
python report/render_report.py report/output/pdf/cv_hw3_task1_report_draft.pdf
```

The final report command is intentionally stricter: it refuses to publish
while the formal Object C mesh, fusion video, fusion preview, or cloud-weights
link is still missing.

```bash
python report/generate_report.py --final --publish
```

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
bash scripts/setup_aigc_envs.sh tracking
bash scripts/setup_aigc_envs.sh threestudio-deps
bash scripts/setup_aigc_envs.sh magic123-deps
```

The two environments are named `cv_hw3_threestudio` and `cv_hw3_magic123`.
CUDA 11.8 and GCC 11 are used for locally compiled PyTorch extensions.

On the current machine, Ubuntu's WSL VHDX lives under `D:\WSL\Ubuntu`. When
`/mnt/d` is available, the AIGC setup helper redirects pip downloads to
`/mnt/d/PackageCache/wsl/pip`. The same path is configured as the WSL user's
global pip cache to avoid regrowing `~/.cache/pip`. The Object B and Object C
generation helpers also default Hugging Face downloads to
`/mnt/d/PackageCache/wsl/huggingface`.

The official threestudio stack pins `lightning==2.0.0`, which requires
`fastapi<0.89`. SwanLab's optional local `swanboard` dashboard requires
`fastapi>=0.110.1`, so `pip check` reports that known dashboard-only conflict
inside `cv_hw3_threestudio`. SwanLab experiment logging and the verified
threestudio training imports remain available.

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

## Object B

Generate a text-only 3D asset using threestudio DreamFusion and Stable
Diffusion SDS loss:

```bash
MODE=smoke bash scripts/generate_text3d_object_b.sh
MODE=full bash scripts/generate_text3d_object_b.sh
bash scripts/export_text3d_object_b.sh
```

The exporter finds the latest full checkpoint by default and writes an OBJ
under the corresponding Object B output directory. To validate the export
path against a smoke checkpoint, set `RUN_NAME`, `TRAIN_TAG=smoke`, and a lower
diagnostic `ISOSURFACE_THRESHOLD`. Formal exports retain the official `25.0`
threshold by default.

The helper defaults to the public
`stable-diffusion-v1-5/stable-diffusion-v1-5` repository and
`HF_ENDPOINT=https://hf-mirror.com`. Override `SD_MODEL` or `HF_ENDPOINT`
explicitly when another accessible model source is preferred.

Prefetch the required SD 1.5 components with single-worker resumable downloads
before the first AIGC run:

```bash
bash scripts/prefetch_public_sd15.sh
```

When the mirror's large-file storage path is unstable from WSL, reuse a
Windows-side proxy exposed on the WSL NAT gateway. The helper keeps mirror
metadata requests direct and proxies only redirected storage requests:

```bash
WINDOWS_PROXY_PORT=7890 bash scripts/prefetch_public_sd15.sh
```

## Object C

Prepare the RGB checkerboard input, download the official Magic123 weights,
compute the MiDaS depth image, and run the two Magic123 stages:

```bash
python scripts/prepare_object_c_image.py --swanlab-mode local
bash scripts/download_magic123_models.sh
bash scripts/prepare_magic123_object_c.sh
MODE=smoke STAGE=coarse bash scripts/generate_image3d_object_c.sh
MODE=smoke STAGE=fine bash scripts/generate_image3d_object_c.sh
MODE=full STAGE=coarse bash scripts/generate_image3d_object_c.sh
MODE=full STAGE=fine bash scripts/generate_image3d_object_c.sh
```

The smoke path is intended for dependency and VRAM validation. The report asset
must use the full path. The helper explicitly passes the public
`stable-diffusion-v1-5/stable-diffusion-v1-5` repository to Magic123 so Object C
reuses the same D-drive SD 1.5 cache as Object B. It also applies an idempotent
local Magic123 compatibility patch that disables unused safety-checker
components, keeping the required cache identical to Object B's core snapshot.
The generation helper also links `~/.cache/clip` to
`/mnt/d/PackageCache/wsl/clip`, so the Zero123 `ViT-L-14.pt` auxiliary model is
stored with the other D-drive package caches.

Magic123 loads Stable Diffusion 1.5 and Zero123 into host memory together. On a
32 GB Windows host, the default WSL cap can OOM-kill the process while Zero123
is loading. Copy `configs/wslconfig.magic123.example` to
`%UserProfile%\.wslconfig`, run `wsl --shutdown`, and start WSL again before the
first Magic123 run. The template grants WSL 26 GB RAM and creates its 32 GB
swap file under `D:\WSL`, avoiding new C-drive pressure.

## Fusion

Export assets as meshes, install the fixed Blender portable runtime, compose
the scene, and render the final walkthrough video:

```bash
bash scripts/setup_blender.sh
bash scripts/install_blender_wsl_deps.sh  # Only needed when setup reports missing WSL libraries.
bash scripts/render_fusion.sh
```

The initial transforms live in `configs/fusion_scene.json`. Adjust them after
the first visual inspection if the extracted mesh coordinate ranges require it.

## Resumable Queue

For a long unattended Object B run, queue the next GPU stages without skipping
wrapper validation:

```bash
bash scripts/continue_after_object_b.sh
bash scripts/continue_object_c_full.sh
```

The helper waits for the formal Object B wrapper to finish successfully,
exports the formal OBJ, then runs Object C coarse and fine smoke checks. It
stops immediately on a failed wrapper and leaves stage logs under `logs/`.
After smoke validation, `continue_object_c_full.sh` runs the report-quality
Object C coarse and fine stages in order. It reuses verified completed stages
when resumed and checks the coarse checkpoint and final OBJ explicitly.
