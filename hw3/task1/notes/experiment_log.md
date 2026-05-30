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