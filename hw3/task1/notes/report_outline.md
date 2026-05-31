# CV HW3 Task 1 Report Outline

Status: work in progress. Replace each `PENDING` marker with the final measured result before PDF export.

## 1. Background and Objective

Task 1 builds one unified 3D scene from four sources:

- Object A: real phone multiview images reconstructed with COLMAP and 2DGS.
- Object B: text-only 3D generation with threestudio DreamFusion and Stable Diffusion SDS loss.
- Object C: one real phone image with background removal, reconstructed with Magic123.
- Background: the open-source Mip-NeRF 360 `counter` scene reconstructed with 2DGS.

The final result inserts the three object assets into the reconstructed real background and renders a multiview walkthrough video.

## 2. Dataset Description

| Asset | Source | Size | Preparation |
|---|---|---:|---|
| Object A | Phone multiview capture | 34 registered images | COLMAP pose extraction and 2DGS undistortion |
| Object B | Text prompt only | 1 prompt | threestudio Stable Diffusion SDS optimization |
| Object C | Phone photo `c.png` | 1448 x 1086 RGB | Checkerboard removal, RGBA alpha mask, Magic123 MiDaS depth |
| Background | Mip-NeRF 360 `counter` | 240 images | Selective Hugging Face mirror download |

Object A COLMAP sparse model:

| Metric | Value |
|---|---:|
| Registered images | 34 / 34 |
| Sparse points | 1527 |
| Observations | 5203 |
| Mean track length | 3.407335 |
| Mean observations per image | 153.029412 |
| Mean reprojection error | 1.192686 px |

## 3. Methods

### 3.1 Object A: COLMAP and 2DGS

Describe phone capture, COLMAP registration, undistortion, 2D Gaussian representation, normal regularization, render export, and bounded TSDF mesh export.

### 3.2 Object B: threestudio DreamFusion SDS

Prompt:
`A studio product photo of a small red ceramic teapot with a round body, short spout, and curved handle`

Describe the Stable Diffusion 2.1 base guidance model, SDS loss, random-camera optimization, validation render, and mesh export.

### 3.3 Object C: Magic123

Prompt:
`A high-resolution DSLR product photo of an amoxicillin capsule medicine box`

Describe checkerboard removal, convex-hull alpha extraction, MiDaS depth estimation, Stable Diffusion prior, Zero123 prior, coarse NeRF optimization, and fine DMTet optimization.

### 3.4 Background: Mip-NeRF 360 Counter and 2DGS

Describe the open-source scene, selective mirror download, COLMAP camera reuse, 2DGS reconstruction, and bounded mesh export.

### 3.5 Unified Representation and Fusion

Use textured meshes as the exchange representation for Object A, Object B, Object C, and the background surface extracted from 2DGS. Compose, scale, and position the meshes in one scene, then render a camera walkthrough. Document the chosen renderer after the local Blender or fallback rendering path is finalized.

## 4. Hyperparameters

| Stage | Iterations | Resolution | Main Parameters |
|---|---:|---:|---|
| Object A 2DGS | 30000 | native | `lambda_normal=0.05`, `lambda_dist=0.0`, `depth_ratio=0.0` |
| Background 2DGS | 30000 | half | `lambda_normal=0.05`, `lambda_dist=0.0`, `depth_ratio=0.0` |
| Object B threestudio | 10000 | 64 x 64 | Stable Diffusion SDS, `guidance_scale=100` |
| Object C Magic123 coarse | 5000 | 128 x 128 | SD + Zero123, `lambda_guidance=[1.0, 40]` |
| Object C Magic123 fine | 5000 | DMTet | SD + Zero123, `lambda_guidance=[1e-3, 0.01]` |

## 5. Results

### 5.1 Object A Intermediate Evaluation

| Iteration | Validation PSNR | Validation L1 | Gaussian Points | Patch Total Loss |
|---:|---:|---:|---:|---:|
| 7000 | 31.8275299 dB | 0.0156156 | 149488 | not retained at exact evaluation event |
| 30000 | 33.5198059 dB | 0.0112888 | 212465 | 0.0273208 |

### 5.2 Background Intermediate Evaluation

| Iteration | Validation PSNR | Validation L1 | Gaussian Points | Patch Total Loss |
|---:|---:|---:|---:|---:|
| 7000 | 28.0689182 dB | 0.0215513 | 482345 | not retained at exact evaluation event |
| 30000 | 29.9138107 dB | 0.0169862 | 533358 | 0.0242750 |

### 5.3 Final Asset Outputs

| Asset | Mesh Output | Preview / Video | Time Cost |
|---|---|---|---:|
| Object A | `outputs/object_a_2dgs/object-a-2dgs-full/train/ours_30000/fuse_post.ply` | `docs/figures/object_a_render_preview.png` | 4855.77 s training |
| Background | `outputs/background_2dgs/background-counter-2dgs-full/train/ours_30000/fuse_post.ply` | `docs/figures/background_counter_render_preview.png` | 1368.52 s training |
| Object B | PENDING | PENDING | PENDING |
| Object C | PENDING | PENDING | PENDING |
| Fusion | unified scene | PENDING | PENDING |

## 6. Comparative Analysis

Compare geometry accuracy, texture fidelity, compute time, controllability, input burden, and failure modes for multiview reconstruction, text-to-3D generation, and single-image-to-3D generation.

## 7. Experiment Tracking

Insert SwanLab curve screenshots for:

- Object A 2DGS training and validation.
- Background 2DGS training and validation.
- Object B SDS training.
- Object C Magic123 coarse and fine training.

## 8. Reproducibility and Links

- Public GitHub repository: `https://github.com/Loong-C/FDU-Computer-Vision`
- Branch: `hw3`
- Best model weights cloud link: `PENDING`
- SwanLab local dashboard command: `swanlab watch hw3/task1/swanlog`
