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

## 2026-05-31 / Magic123 Official Weight Download Complete

Goal:
Verify that both official Magic123 pretrained-model downloads completed and were atomically promoted from resumable `.part` files.

Result:
Succeeded.

Downloaded files:
Zero123 `pretrained/zero123/105000.ckpt`: `15465973531` bytes
MiDaS `pretrained/midas/dpt_beit_large_512.pt`: `1581966003` bytes

Notes:
The downloader process exited after both final paths existed. No `.part` file remains for either model.

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

## 2026-05-31 / Blender Portable Runtime Attempt 1

Goal:
Install and validate the fixed Blender `4.2.15` Linux x64 portable runtime for the final fusion render.

Result:
Runtime archive download, checksum verification, and extraction succeeded. The first launch failed because the base WSL image does not yet provide `libSM.so.6` and `libICE.so.6`.

Follow-up:
Added `scripts/install_blender_wsl_deps.sh` for the minimal `libsm6` and `libice6` system packages. Updated the Blender installer to explain this recovery path when an extracted runtime cannot launch.

## 2026-05-31 / WSL Storage Incident and D-Drive Recovery

Goal:
Recover the Task 1 workspace after the Windows system drive filled during model download and training, then prevent package caches from regrowing on `C:`.

Incident:
The Windows `C:` drive reached `0 GB` free space while the Ubuntu WSL virtual disk was stored under `C:\Users\hp\AppData\Local\wsl`. WSL began returning `Input/output error` for repository writes and basic files such as `/etc/passwd`.

Impact:
The formal Object A run `object-a-2dgs-full` stopped before its `30000`-iteration checkpoint. The last readable training-log line is iteration `22120 / 30000`, with `219306` Gaussian points. Its valid iteration-`7000` checkpoint and TensorBoard metrics remain available.

Recovery:
Removed the verified Windows pip cache directory, recovering approximately `8.75 GB`.

Moved the complete Ubuntu distribution with `wsl --manage Ubuntu --move D:\WSL\Ubuntu`. The WSL VHD is now `D:\WSL\Ubuntu\ext4.vhdx`; Miniforge, both AIGC Conda environments, downloaded Magic123 weights, and repository-local tooling moved with it.

Verified root and user WSL launches, `/etc/passwd` reads, and a temporary-file write probe after relocation. Windows drive free space changed from approximately `0 GB` to `65.77 GB` on `C:`. The destination `D:` drive retained approximately `63.38 GB` free after receiving the WSL VHD.

Cache policy:
Configured Windows user-level `PIP_CACHE_DIR=D:\PackageCache\pip`, `TORCH_HOME=D:\PackageCache\torch`, and `CONDA_PKGS_DIRS=D:\PackageCache\conda-pkgs`. Preserved the existing `HF_HOME=D:\huggingface_cache`. Moved the small Windows Torch cache to `D:\PackageCache\torch` and left a compatibility junction at its original user-cache path.

Notes:
The application-managed `C:\Users\hp\.cache\codex-runtimes` directory remains in place because the active desktop application is using it. Installed Windows applications were not manually moved because that could invalidate registrations or update paths.

## 2026-05-31 / Blender WSL Dependencies and Launch Validation

Goal:
Finish validating the portable Blender runtime after the storage recovery.

Result:
Succeeded.

Installed packages:
`libsm6`
`libice6`

Validation:
`bash scripts/install_blender_wsl_deps.sh` completed with `Blender 4.2.15 LTS`.

`bash scripts/setup_blender.sh` now recognizes the existing runtime and completes with the same version output.

The updated readiness checker executes `external/blender/blender --version` instead of accepting file existence alone. The post-install snapshot reports `7 / 13` Task 1 checks ready, including the runnable Blender runtime.

## 2026-05-31 / Object A Formal 2DGS Clean Rerun Started

Goal:
Restart the formal Object A `30000`-iteration run after restoring reliable WSL storage.

Restart policy:
The interrupted run produced a valid iteration-`7000` PLY asset but no optimizer `.pth` checkpoint. A clean rerun is required for a rigorous final checkpoint.

Preserved evidence:
Moved the interrupted output directory to `outputs/object_a_2dgs/object-a-2dgs-full-interrupted-eio-20260531`.

Moved its terminal log to `logs/object-a-2dgs-full-interrupted-eio-20260531.log`.

New run:
`object-a-2dgs-full`

SwanLab local run:
`run-20260531_151420-jyj0y12ibvekjlf6u9rw0`

Validation:
The new run passed initialization and reached at least iteration `270 / 30000`.

The RTX 4060 Ti reported approximately `2634 / 8188 MiB` GPU memory in use and `93%` GPU utilization during the early training phase.

## 2026-05-31 / Magic123 Dependency Installation Attempt 1

Goal:
Install the official Magic123 Python and CUDA-extension dependencies while the Object A rerun uses the GPU.

Result:
Failed early during `nvdiffrast` metadata preparation.

Observed error:
`ERROR! Cannot compile nvdiffrast CUDA extension. Please ensure that ... you run 'pip install' with --no-build-isolation flag`

Diagnosis:
The current `nvdiffrast` package uses a PEP 517 build path. Its isolated build environment cannot import the PyTorch package already installed in `cv_hw3_magic123`.

Fix:
Updated `scripts/setup_aigc_envs.sh` to pass `--no-build-isolation` for both Magic123 and threestudio requirements installs. The same script now defaults WSL pip caching to `/mnt/d/PackageCache/wsl/pip` when the `D:` mount exists.

## 2026-05-31 / Magic123 Dependency Installation Attempt 2

Goal:
Retry the official Magic123 dependency installation after enabling non-isolated package builds.

Result:
Failed early during the same `nvdiffrast` metadata step.

Diagnosis:
The upstream `nvdiffrast` error message catches a broad import error. Reproducing its import directly exposed the missing module:
`ModuleNotFoundError: No module named 'pkg_resources'`

PyTorch `2.0.1` imports `pkg_resources` from setuptools inside `torch.utils.cpp_extension`. The AIGC environment did not yet include this build prerequisite.

Fix:
Added an explicit build-prerequisite bootstrap to `scripts/setup_aigc_envs.sh`: `setuptools<81`, `wheel`, and `packaging` are installed before either Magic123 or threestudio extension requirements.

## 2026-05-31 / Magic123 Dependency Installation Attempt 3

Goal:
Retry the official Magic123 dependency installation after bootstrapping compatible extension-build prerequisites.

Result:
Progressed past the earlier `nvdiffrast` metadata failure, downloaded the Python requirements, and entered CUDA-extension compilation. Failed while building `cubvh`.

Observed error:
`fatal error: cusparse.h: No such file or directory`

Diagnosis:
The initial AIGC toolchain intentionally installed a small CUDA `11.8` subset: `cuda-nvcc` and `cuda-cudart-dev`. Building Magic123's transitive CUDA extensions also requires CUDA libraries development headers.

Fix:
Added `cuda-libraries-dev=11.8` to the reproducible AIGC toolchain. Conda confirmed that `cuda-libraries-dev 11.8.0` is available from `nvidia/label/cuda-11.8.0`.

## 2026-05-31 / AIGC CUDA Libraries Development Toolchain Patch

Goal:
Install the complete CUDA libraries development headers needed by Magic123 and threestudio extension builds.

Result:
Succeeded.

Command:
`bash scripts/setup_aigc_envs.sh toolchain`

Installed aggregate:
`cuda-libraries-dev=11.8`

Validation:
Verified `include/cusparse.h` inside both `cv_hw3_magic123` and `cv_hw3_threestudio`.

## 2026-05-31 / Object A Clean Rerun Iteration 7000

Goal:
Record the first evaluation checkpoint from the post-recovery Object A clean rerun.

Run:
`object-a-2dgs-full`

TensorBoard metrics at iteration `7000`:
Validation PSNR: `31.827529907226562 dB`
Validation L1 loss: `0.015615569427609444`
Total Gaussian points: `149488`
Patch total loss: `0.016165414825081825`
Patch normal loss: `0.0`

Status:
The iteration-`7000` PLY checkpoint exists and training continues toward iteration `30000`.

## 2026-05-31 / Magic123 Dependency Installation Attempt 4 Started

Goal:
Retry the complete Magic123 requirements and CUDA-extension installation after adding CUDA libraries development headers.

Status:
Running in the background with the WSL pip cache under `/mnt/d/PackageCache/wsl/pip`.

## 2026-05-31 / Magic123 Dependency Installation Attempt 4

Goal:
Retry the complete Magic123 dependency installation after adding CUDA libraries development headers.

Result:
The official Python requirements, including `nvdiffrast` and `cubvh`, built and installed successfully. The final repository-local extension step failed because the upstream `scripts/install_ext.sh` uses paths such as `./raymarching`, but the setup wrapper invoked it from the Task 1 project root.

Compatibility finding:
The official requirements are intentionally broad. The resolver upgraded NumPy to `2.2.6`, Transformers to `5.9.0`, and Diffusers to `0.38.0`. That combination is not compatible with the verified PyTorch `2.0.1+cu118` runtime: Transformers disables PyTorch versions below `2.4`, and Diffusers expects `torch.xpu`.

Fix:
Added `requirements-magic123-compatibility.txt` to restore a compatible stack after the official requirements install: `numpy<2`, `diffusers<0.20`, `transformers==4.28.1`, `huggingface_hub<0.26`, and `accelerate<0.21`.

Updated `scripts/setup_aigc_envs.sh` to run the local-extension installer from `external/Magic123`, pass non-isolated pip builds, and limit local extension compilation to two concurrent jobs.

## 2026-05-31 / Magic123 Dependency Installation Attempt 5

Goal:
Apply the compatibility constraints and compile Magic123's four repository-local CUDA extensions.

Result:
The compatibility pins were applied successfully. The local extension step still failed because pip continued to isolate each build, hiding PyTorch from `raymarching`, `shencoder`, `freqencoder`, and `gridencoder`.

Observed error:
`ModuleNotFoundError: No module named 'torch'`

Additional compatibility finding:
OpenCV `4.13` requires NumPy `>=2` on Python `3.9+`, conflicting with the verified PyTorch `2.0.1` environment and the new `numpy<2` pin.

Fix:
Replaced the upstream shell-script invocation with an explicit non-isolated install:
`python -m pip install --no-build-isolation ./raymarching ./shencoder ./freqencoder ./gridencoder`

Pinned `opencv-python<4.12` and `opencv-python-headless<4.12` in the Magic123 compatibility requirements.

## 2026-05-31 / Magic123 Dependency Installation Attempt 6

Goal:
Complete the Magic123 environment with explicit non-isolated builds for the four repository-local CUDA extensions.

Result:
Succeeded.

Validated runtime:
NumPy: `1.26.4`
PyTorch: `2.0.1+cu118`
CUDA available: `True`
OpenCV: `4.11.0`
Diffusers: `0.19.3`
Transformers: `4.28.1`
Hugging Face Hub: `0.25.2`

Validated local extensions from the real Magic123 module path:
`raymarching`
`shencoder`
`freqencoder`
`gridencoder`

Validation:
`python -m pip check` reports `No broken requirements found.`

## 2026-05-31 / threestudio Compatibility Constraints Prepared

Goal:
Prevent the threestudio requirements resolver from replacing the verified PyTorch `2.0.1+cu118` stack through its broad `xformers` dependency.

Implementation:
Added `requirements-threestudio-compatibility.txt` with PyTorch `2.0.1`, Torchvision `0.15.2`, XFormers `0.0.20`, `numpy<2`, `opencv-python<4.12`, and `huggingface_hub<0.26`.

Updated the threestudio dependency installer to resolve the upstream requirements under these constraints.

## 2026-05-31 / threestudio Dependency Installation Attempt 1

Goal:
Install the official threestudio requirements under the verified PyTorch `2.0.1+cu118` compatibility constraints.

Result:
The resolver entered CUDA-extension compilation and built much of `nerfacc` and `tiny-cuda-nn`, then failed on two missing build inputs.

Observed errors:
`cannot find -lcuda: No such file or directory`

`ModuleNotFoundError: No module named 'pybind11'`

Diagnosis:
Conda installed the CUDA driver stub at `cv_hw3_threestudio/lib/stubs/libcuda.so`, but the extension linker did not search that directory. The non-isolated `pysdf` build also needs `pybind11` installed before requirements resolution.

Fix:
Added `pybind11` to the AIGC build-prerequisite bootstrap.

Added the Conda CUDA stub directory to `LIBRARY_PATH` and `LDFLAGS` during threestudio dependency builds.

Limited extension builds to `MAX_JOBS=2` to reduce contention with the active Object A training run.

## 2026-05-31 / threestudio Dependency Installation Attempt 2

Goal:
Retry the official threestudio dependency installation with the Conda CUDA
driver-stub linker path and the non-isolated `pybind11` prerequisite.

Result:
Succeeded for the official threestudio runtime and all required CUDA
extensions.

Validated runtime:
PyTorch: `2.0.1+cu118`
CUDA available: `True`
NerfAcc: `0.5.2`
Tiny CUDA NN: import succeeded
NVDiffRast: import succeeded
PySDF: import succeeded
XFormers: `0.0.20`
SwanLab: `0.7.19`

Validated extension builds:
`nerfacc`
`tinycudann`
`nvdiffrast`
`pysdf`

Known optional-dashboard conflict:
`pip check` reports that `swanboard 0.1.9b3` requires `fastapi>=0.110.1`,
while the official threestudio dependency `lightning==2.0.0` requires
`fastapi<0.89.0`. Those constraints do not overlap. The verified threestudio
runtime and SwanLab event logging both import successfully, so the official
Lightning runtime is preserved and the optional local SwanBoard UI conflict is
documented explicitly.

## 2026-05-31 / Object A Clean 2DGS Formal Rerun Completed

Goal:
Complete a clean 30,000-iteration Object A 2DGS training run after recovering
the WSL filesystem and moving the Ubuntu VHDX to `D:\WSL\Ubuntu`.

Result:
Succeeded with exit code `0`.

Runtime:
Start: `2026-05-31T07:14:20.150270+00:00`
Finish: `2026-05-31T08:35:15.952232+00:00`
Elapsed: `4855.769257162` seconds

Dataset and geometry:
COLMAP images: `34`
Final Gaussian points: `212465`
Iteration-30,000 point cloud:
`outputs/object_a_2dgs/object-a-2dgs-full/point_cloud/iteration_30000/point_cloud.ply`

Evaluation:
Iteration `7000`: train PSNR `31.827529907226562`, train L1
`0.015615569427609444`

Iteration `30000`: train PSNR `33.519805908203125`, train L1
`0.011288780719041824`, normal loss `0.0033516681287437677`, regularization
loss `0.012270934879779816`, total patch loss `0.027320832014083862`

Tracking:
The clean formal run logged `10001` scalar steps into SwanLab local mode and
retained its TensorBoard event stream for report-table export.

## 2026-05-31 / Object A Render Attempt 1

Goal:
Render the completed Object A `iteration_30000` 2DGS asset before TSDF mesh
export.

Result:
Failed before rendering started.

Observed error:
`FileNotFoundError: outputs/object_a_2dgs/object-a-2dgs-full/cfg_args`

Diagnosis:
Both 2DGS asset-export helpers changed directory into
`external/2d-gaussian-splatting` before invoking `render.py`, while forwarding
the model directory as a project-root-relative path. The completed model and
its `cfg_args` file exist under the Task 1 root.

Fix:
Resolve the model directory to an absolute path before changing into the
external 2DGS repository in both `scripts/render_2dgs_asset.sh` and
`scripts/export_2dgs_mesh.sh`.

## 2026-05-31 / Object A Render Attempt 2 and Mesh Export

Goal:
Render the completed Object A asset and export a mesh suitable for Blender
fusion after normalizing the model path.

Result:
Succeeded.

Render output:
Iteration: `30000`
Rendered predictions: `34`
Rendered ground-truth images: `34`
Estimated bounding radius: `3.77`

Mesh-export configuration:
Voxel size: `0.03`
Depth truncation: `7.5`
SDF truncation: `0.15`

Mesh output:
Raw vertices: `202489`
Post-processed vertices: `189968`
Post-processed mesh:
`outputs/object_a_2dgs/object-a-2dgs-full/train/ours_30000/fuse_post.ply`
Post-processed mesh bytes: `9908179`

Tracking:
Recorded the successful render and bounded-TSDF mesh export as separate SwanLab
pipeline milestones.

## 2026-05-31 / Object C MiDaS Depth Preprocessing

Goal:
Prepare the single-image Object C input for Magic123 by copying the processed
RGBA image into the official Magic123 data directory and generating the MiDaS
depth prior.

Result:
Succeeded.

Input:
`data/processed/object_c_image/c_rgba.png`

Generated depth prior:
`external/Magic123/data/hw3/medicine_box/depth.png`
Depth-prior bytes: `67278`
RGBA dimensions: `1448 x 1086`
Depth-prior dimensions: `1448 x 1448`

Readiness:
Task 1 machine-readable readiness increased from `8/13` to `9/13`.

Tracking:
Recorded the completion as the `object-c-midas-depth-success` SwanLab pipeline
milestone.

## 2026-05-31 / Background Counter 2DGS Formal Run Launch

Goal:
Train a clean 30,000-iteration background-scene 2DGS model from the prepared
Mip-NeRF 360 `counter` scene while retaining TensorBoard and SwanLab metrics.

Configuration:
Scene: `counter`
Images: `240`
Iterations: `30000`
Resolution divisor: `2`
Depth ratio: `0.0`
Normal-loss weight: `0.05`
Distortion-loss weight: `0.0`

Launch validation:
The run reached iteration `4860` after approximately three minutes with
`536822` Gaussian points and approximately `1.95 GiB` of GPU memory in use.

Tracking:
The formal training wrapper created SwanLab run
`run-20260531_164308-47ff9tn8kh0z7xm05goqx`.

Recorded a separate `background-counter-2dgs-full-launch` SwanLab pipeline
milestone for the validated launch.

## 2026-05-31 / Background Counter 2DGS Formal Run Completed

Goal:
Complete the 30,000-iteration background reconstruction, export report metrics,
render the training viewpoints, and extract a Blender-ready bounded-TSDF mesh.

Result:
Succeeded with exit code `0`.

Runtime:
Start: `2026-05-31T08:43:08.619239+00:00`
Finish: `2026-05-31T09:05:57.172923+00:00`
Elapsed: `1368.5191473309999` seconds

Evaluation:
Iteration `7000`: train PSNR `28.068918228149414`, train L1
`0.02155132219195366`, Gaussian points `482345`

Iteration `30000`: train PSNR `29.91381072998047`, train L1
`0.016986243426799774`, Gaussian points `533358`, normal loss
`0.00477592833340168`, regularization loss `0.014817075803875923`, total patch
loss `0.024274971336126328`

Render output:
Rendered predictions: `240`
Rendered ground-truth images: `240`
Estimated bounding radius: `3.54`

Mesh-export configuration:
Voxel size: `0.03`
Depth truncation: `7.5`
SDF truncation: `0.15`

Mesh output:
Raw vertices: `253172`
Post-processed vertices: `220950`
Post-processed mesh:
`outputs/background_2dgs/background-counter-2dgs-full/train/ours_30000/fuse_post.ply`
Post-processed mesh bytes: `11296426`

Tracking:
The formal run imported `10001` scalar steps into SwanLab local mode.

Recorded the successful training completion, render, and bounded-TSDF mesh
export as separate SwanLab pipeline milestones.

## 2026-05-31 / WSL Pip Cache Consolidation

Goal:
Keep package caches off the constrained Windows system drive and prevent
duplicate WSL pip caches from growing inside the moved Ubuntu VHDX.

Result:
Succeeded.

Validation:
Resolved cleanup target: `/home/hp/.cache/pip`
Removed legacy cache: `5.3G`
Configured WSL global pip cache: `/mnt/d/PackageCache/wsl/pip`
Current redirected cache size: `930M`
Configured AIGC Hugging Face cache:
`/mnt/d/PackageCache/wsl/huggingface`

Storage note:
The Ubuntu VHDX already resides under `D:\WSL\Ubuntu`, so Conda environments
and remaining WSL filesystem content are physically stored on `D:`.
