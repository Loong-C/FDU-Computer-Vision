# Environment Plan

## Recommended Strategy

This project will use separate environments for different components because 2DGS, threestudio, and Magic123 may require different CUDA, PyTorch, and dependency versions.

## Environments

### Environment A: 2DGS

Used for Object A reconstruction and background reconstruction.

Main components:

- Python
- PyTorch
- CUDA toolkit compatible with PyTorch
- COLMAP
- 2D Gaussian Splatting official implementation

### Environment B: threestudio

Used for Object B text-to-3D generation and Object C image-to-3D generation.

Main components:

- Python
- PyTorch
- CUDA toolkit compatible with PyTorch
- threestudio
- diffusion model dependencies
- Magic123 / Zero123 related dependencies

### Experiment Tracking

SwanLab will be used as the default tracking tool. WandB can be used as a backup option.

The following information should be recorded for each experiment:

- experiment name
- object or scene name
- method
- training iterations
- loss curve
- validation or evaluation metrics if available
- GPU type
- time cost
- output path