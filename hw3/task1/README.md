# CV HW3 Task 1: 2DGS and AIGC Asset Fusion

This repository is for Task 1 of the final computer vision assignment: multi-source 3D asset generation and real-scene fusion based on 2D Gaussian Splatting and AIGC.

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

This project will use SwanLab or WandB to record training and optimization curves. The final report will include exported visualization figures, including loss curves and validation or evaluation metrics when available.

## Repository Structure

```text
configs/        configuration files for reconstruction and generation
data/           raw and processed datasets, not tracked by Git
docs/           report materials and exported figures
external/       third-party repositories
notes/          experiment logs and time-cost records
outputs/        trained models, generated assets, rendered images, and videos
scripts/        runnable scripts for each stage