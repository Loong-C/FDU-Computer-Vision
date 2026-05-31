# Experiment Log

## 2026-05-24

### Goal

Initialize the project repository and prepare the workflow for Task 1.

### Progress

The repository structure has been created. The project is divided into six main parts: real object reconstruction, background reconstruction, text-to-3D generation, image-to-3D generation, scene fusion, and report writing.

### Important Requirement

The final report must include visualization charts exported from WandB or SwanLab, including training loss curves and validation or evaluation metric curves.

### Next Step

Set up the 2DGS, COLMAP, threestudio, and experiment tracking environments.

## 2026-05-30 / Object A COLMAP Attempt 1

Goal:
Run COLMAP sparse reconstruction for Object A using phone-captured multi-view images.

Command:
powershell -ExecutionPolicy Bypass -File ".\scripts\prepare_colmap_object_a.ps1"

Result:
COLMAP successfully reconstructed the sparse model for Object A.

Key statistics from colmap model_analyzer:
Input / images: 34
Registered images: 34
Sparse points: 1527
Observations: 5203
Mean track length: 3.407335
Mean observations per image: 153.029412
Mean reprojection error: 1.192686 px

Analysis:
The reconstruction is valid because all 34 images were registered. The sparse point count is moderate, which is acceptable for the first 2DGS verification run. The mean reprojection error is around 1.19 px, indicating that the estimated camera poses are usable. If the later 2DGS result appears blurry or geometrically unstable, the object should be recaptured with more images, denser viewpoints, and stronger texture.

Next step:
Use this COLMAP result as the input for Object A 2DGS training.

## 2026-05-30 / WSL GPU Environment Check

Goal:
Check whether the WSL environment can access the NVIDIA GPU for later 2DGS training.

Result:
WSL successfully detected the NVIDIA GeForce RTX 4060 Ti through nvidia-smi.

Environment:
GPU: NVIDIA GeForce RTX 4060 Ti
Driver version: 581.57
CUDA version reported by nvidia-smi: 13.0
Python version in WSL: 3.12.3
Git version in WSL: 2.43.0
Conda status: not installed initially

Analysis:
The GPU is visible inside WSL, so 2DGS training should be performed in WSL instead of native Windows. Conda needs to be installed before creating the 2DGS environment.

Next step:
Install Miniforge, clone the GitHub repository into the WSL Linux filesystem, copy the Object A COLMAP data into the WSL repository, and install 2DGS.

## 2026-05-31 / Object A 2DGS Baseline

Goal:
Verify that the Object A COLMAP model can train and render with the official 2DGS implementation in WSL.

Result:
The WSL `cv_hw3_2dgs` environment successfully trained a baseline model for 3000 iterations and saved `point_cloud/iteration_3000/point_cloud.ply`. Rendering the training viewpoints also succeeded.

Visual analysis:
The reconstructed figure is recognizable, but the 3000-iteration baseline is visibly blurry and contains background artifacts. A full training run is required.

Mesh export issue:
The default bounded TSDF settings inferred `voxel_size=0.007367...` and caused WSL to exceed its approximately 15 GiB memory limit during fusion. Future mesh exports must use explicit coarse settings and run separately from image rendering.

## 2026-05-31 / Object C Input

Goal:
Prepare the single-image input for the Magic123 asset-generation path.

Result:
Copied the user-provided `c.png` into `data/raw/object_c_image/c.png`. The image depicts an amoxicillin capsule box with a visually isolated foreground.

Input inspection:
The PNG is `1448 x 1086`, uses `24bpp RGB`, and has no alpha channel. The checkerboard is encoded into the RGB pixels, so a reproducible background-removal preprocessing step is required before Magic123.

## 2026-05-31 / 2DGS Tracking Wrapper Smoke Test

Goal:
Verify the end-to-end Object A training wrapper before starting the full run.

Command:
`RUN_NAME=object-a-2dgs-wrapper-smoke-ok ITERATIONS=20 TEST_ITERATIONS=20 SAVE_ITERATIONS=20 bash scripts/train_2dgs_object_a.sh --swanlab-mode local`

Result:
The wrapper completed successfully. It saved a 20-iteration Gaussian point cloud, wrote the terminal log and JSON metadata under `logs/`, generated a TensorBoard event file, and imported all 20 scalar steps into a SwanLab local run.

Key metrics:
Train L1: 0.4029538274
Train PSNR: 7.0299400330 dB
Elapsed time: 20.33 seconds

Issue fixed:
The official trainer accepts `--lambda_dist`, while the upstream README refers to `--lambda_distortion`. The wrapper now uses the actual CLI parameter exposed by the checked-out implementation.

## 2026-05-31 / Object C Preprocessing Attempt 1

Goal:
Remove the baked RGB checkerboard before Magic123 generation.

Method:
Border-connected neutral checkerboard removal.

Result:
Rejected after visual inspection. The method retained only 6.65% of the image as foreground and incorrectly removed the large white packaging faces together with the gray-white checkerboard.

Next step:
Use colored and dark pixels as foreground seeds, then fill their convex hull. This is suitable for the approximately convex medicine-box silhouette while preserving its white faces.

## 2026-05-31 / Object C Preprocessing Attempt 2

Goal:
Produce a clean RGBA image for Magic123 while preserving the white packaging faces.

Method:
Treat colored or dark pixels as foreground seeds, compute their convex hull, fill it, and feather the alpha boundary with a 3-pixel radius.

Result:
Accepted after visual inspection. The medicine box is intact and the RGB checkerboard is removed. The generated RGBA file is stored at `data/processed/object_c_image/c_rgba.png`, and the report-ready white-background preview is stored at `docs/figures/object_c_preprocessed_preview.png`.

Key statistics:
Input size: 1448 x 1086
Foreground seed pixels: 210059
Convex hull area: 395398.5 px
Foreground ratio: 0.2521157016

## 2026-05-31 / External AIGC Repositories

Goal:
Pin the official implementations used by the Object B and Object C paths.

Result:
Cloned the official threestudio repository from `https://github.com/threestudio-project/threestudio.git` at commit `28d9d80d9d00f308244adfcf3be8b17ca0cb6465`.

Cloned the official Magic123 repository from `https://github.com/guochengqian/Magic123.git` at commit `c2eb289f0b9e03e5cf39cf1417f05ca33e9eb0a5`.

Both clone milestones were recorded as separate SwanLab local runs.

## 2026-05-31 / Background Scene Selection

Goal:
Prepare an open-source real scene for the unified 2DGS background.

Result:
Selected the `counter` scene from the official Mip-NeRF 360 `360_v2.zip` archive at `https://storage.googleapis.com/gresearch/refraw360/360_v2.zip`.

Archive metadata:
Content length: 12535427936 bytes
ETag: `cef2ef3aeaf0c062dbe65130bc249870`

Implementation:
Added `scripts/download_background_counter.sh`. It resumes partial downloads and extracts only the selected `counter` directory.
