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

## 2026-05-31 / Background Download Strategy Update

Goal:
Avoid spending hours downloading unused Mip-NeRF 360 scenes.

Observation:
The official `360_v2.zip` archive download slowed to roughly 100-230 KB/s. The complete archive is approximately 11.7 GiB, while only `counter` is needed.

Decision:
Stopped the official whole-archive download after approximately 13 MB. Updated `scripts/download_background_counter.sh` to download only `counter/**` from the `nvs-bench/mipnerf360` Hugging Face mirror using `huggingface_hub.snapshot_download`.

Reproducibility:
The selected scene remains the Mip-NeRF 360 `counter` dataset. The mirror source and selective-download implementation are recorded in Git, and Hugging Face caching supports interrupted-download recovery.

Network note:
WSL direct access to `huggingface.co` timed out, while access through the Windows host proxy succeeded. The downloader derives the WSL gateway from the default route, exports `HTTP_PROXY` and `HTTPS_PROXY` with port `7890`, and disables Xet so the Hub client uses conventional HTTP transfers.

## 2026-05-31 / Background Download Complete

Goal:
Validate the selective `counter` scene download.

Result:
The proxy-enabled Hugging Face download completed successfully in approximately 24 seconds. The processed-data symlink resolves to `data/raw/mipnerf360/counter`.

Downloaded scene:
Images: 240
COLMAP sparse model files: 3
Total files: 243
Total bytes: 319622230

Tracking:
Recorded the successful completion as the `background-counter-download-success` SwanLab milestone.

## 2026-05-31 / AIGC Environment Bootstrap

Goal:
Create isolated and reproducible environments for the text-to-3D and single-image-to-3D routes without disturbing the running Object A experiment.

Host inspection:
The WSL host exposes an NVIDIA GeForce RTX 4060 Ti with 8188 MiB VRAM. It provides GCC 13.3.0, CMake 3.28.3, and Ninja, but no system `nvcc` or `/usr/local/cuda` installation.

Result:
Created the Python 3.10 Conda environments `cv_hw3_threestudio` and `cv_hw3_magic123`. Added `scripts/setup_aigc_envs.sh` so environment creation, local CUDA toolchain installation, PyTorch installation, and dependency installation are explicit reproducible stages.

Decision:
Use Conda-local CUDA 11.8 compiler packages and GCC 11 for extension builds. This avoids modifying the WSL system toolchain and matches the CUDA 11.8 PyTorch wheels used by the project.

## 2026-05-31 / AIGC Conda Toolchain Install

Goal:
Install a reproducible CUDA extension build toolchain for threestudio and Magic123.

Command:
`bash scripts/setup_aigc_envs.sh toolchain`

Result:
Succeeded for both `cv_hw3_threestudio` and `cv_hw3_magic123`.

Verified toolchain:
CUDA compiler: `nvcc V11.8.89`
Conda C++ compiler: `x86_64-conda-linux-gnu-c++ 11.4.0`
Build helper: `ninja`

Notes:
The toolchain is environment-local. No system package installation or global CUDA path modification was required.

## 2026-05-31 / AIGC PyTorch Install

Goal:
Install a shared CUDA-enabled PyTorch baseline for the isolated threestudio and Magic123 environments.

Command:
`bash scripts/setup_aigc_envs.sh torch`

Result:
Succeeded for both `cv_hw3_threestudio` and `cv_hw3_magic123`.

Verified packages:
PyTorch: `2.0.1+cu118`
Torchvision: `0.15.2+cu118`
PyTorch CUDA build: `11.8`
NumPy: `1.26.4`

Compatibility correction:
The initial PyTorch installation resolved NumPy `2.2.6`. This is newer than the ABI expected by several dependencies in the pinned AIGC repositories. Updated `scripts/setup_aigc_envs.sh` to install `numpy<2` and downgraded both environments to NumPy `1.26.4` before continuing.

## 2026-05-31 / AIGC Execution Scaffolding

Goal:
Replace the Object B and Object C placeholders with reproducible local execution entry points and SwanLab tracking.

Implementation:
Added `scripts/run_tracked_experiment.py`, a common subprocess wrapper that tees terminal output, parses Magic123 step losses, recursively imports TensorBoard scalars when available, records timing and exit status, and writes metrics to SwanLab local mode.

Added the threestudio DreamFusion SDS entry point in `scripts/generate_text3d_object_b.sh` with separate smoke and full modes.

Added the Magic123 model downloader, Object C input assembly and MiDaS preprocessing helper, and coarse/fine generation entry point. The Magic123 smoke mode lowers render and marching-cubes resolution for 8 GiB VRAM validation; the full mode preserves the official 5000-step coarse and 5000-step fine schedule.

Tracking dependency:
Added a dedicated `bash scripts/setup_aigc_envs.sh tracking` stage so both isolated environments receive SwanLab, TensorBoard, and PyYAML without mixing project dependencies into the system Python installation.

## 2026-05-31 / Object C Magic123 Input Assembly

Goal:
Copy the accepted checkerboard-free Object C RGBA image into the ignored Magic123 working dataset without starting a GPU depth-estimation task during Object A training.

Command:
`COPY_ONLY=1 bash scripts/prepare_magic123_object_c.sh`

Result:
Copied the prepared input to `external/Magic123/data/hw3/medicine_box/main.png` and `external/Magic123/data/hw3/medicine_box/rgba.png`.

Verification:
The source and both copied files share SHA-256 `da9e14a733047109969ddedef78990c5c08131920c56187bda592419d0b1d98a`.

## 2026-05-31 / AIGC Tracking Dependencies

Goal:
Install the local experiment-tracking packages required by the common AIGC subprocess wrapper.

Command:
`bash scripts/setup_aigc_envs.sh tracking`

Result:
Succeeded for both `cv_hw3_threestudio` and `cv_hw3_magic123`. Verified that `scripts/run_tracked_experiment.py --help` launches from both isolated environments.

Installed tracking baseline:
SwanLab: `0.7.19`
TensorBoard: `2.20.0`
PyYAML: installed

## 2026-05-31 / Magic123 Official Weight Download Started

Goal:
Download the official pretrained models required by Magic123 while the Object A GPU experiment continues.

Command:
`bash scripts/download_magic123_models.sh`

Status:
Running in the background with resumable `.part` files. The first download is the official Zero123 `105000.ckpt` from Hugging Face. The server reports approximately 14.4 GiB for this checkpoint. The MiDaS `dpt_beit_large_512.pt` download follows automatically.

Notes:
The download uses the WSL gateway proxy and `curl --continue-at -`, so an interruption can resume without discarding completed bytes.

## 2026-05-31 / TensorBoard Report Summary Helper

Goal:
Make scalar evidence exportable for the report tables without manually reading event files.

Implementation:
Added `scripts/summarize_tensorboard.py`. It recursively reads TensorBoard scalar events, reports the latest value per tag, and extracts exact requested steps such as `7000` and `30000` into JSON.

Validation:
Successfully read the live TensorBoard event file from `outputs/object_a_2dgs/object-a-2dgs-full` while training continued.

## 2026-05-31 / Object A Formal 2DGS Intermediate Evaluation

Goal:
Record the official `7000`-iteration evaluation checkpoint from the formal Object A run.

Run:
`object-a-2dgs-full`

Training configuration:
Iterations: `30000`
Resolution: `-1`
Normal regularization: `0.05`
Distortion regularization: `0.0`
Depth ratio: `0.0`

TensorBoard metrics at iteration `7000`:
Validation PSNR: `31.824914932250977 dB`
Validation L1 loss: `0.015528421849012375`
Total Gaussian points: `145973`
Patch total loss: `0.01736341044306755`
Patch normal loss: `0.0`

## 2026-05-31 / Delivery Readiness Helper and Report Outline

Goal:
Make the remaining Task 1 work explicit for both manual review and automated continuation.

Implementation:
Added `scripts/check_task1_readiness.py` to emit JSON checks for prepared data, official weights, 2DGS checkpoints, Object B and Object C meshes, fusion video, Blender, and FFmpeg.

Expanded `notes/report_outline.md` into the required report structure with dataset description, methods, hyperparameter tables, SwanLab evidence slots, comparison criteria, repository link, and cloud-weight placeholder.

Updated `notes/environment_plan.md` from the early two-environment assumption to the verified three-environment layout.

Validation:
The first readiness snapshot reports `4 / 14` checks ready: 34 Object A COLMAP images, Object A iteration-7000 checkpoint, 240 background `counter` images, and the prepared Object C RGBA input. The remaining checks correctly identify pending training checkpoints, official Magic123 weights, AIGC meshes, fusion video, Blender, and FFmpeg.

## 2026-05-31 / Fusion Runtime Scaffolding

Goal:
Replace the fusion placeholder with a reproducible mesh-composition and walkthrough-video rendering path.

Implementation:
Added `scripts/setup_blender.sh` for a fixed Blender `4.2.15` Linux x64 portable runtime from the official Blender release server with SHA-256 verification.

Added `configs/fusion_scene.json`, `scripts/blender_fuse_scene.py`, and a real `scripts/render_fusion.sh`. The Blender script imports PLY, OBJ, or GLB meshes, applies explicit transforms, adds lighting and an orbiting walkthrough camera, saves a `.blend` scene, and encodes an H.264 MP4 using Blender's FFmpeg integration.

Status:
Implementation complete. Runtime download, first render, and transform tuning remain pending until the four mesh assets are available.

Validation:
Bash syntax, Python byte-compilation, and JSON parsing passed. Running `bash scripts/render_fusion.sh` before runtime installation exits with the expected actionable message: `Missing Blender runtime. Run: bash scripts/setup_blender.sh`.
