# FDU Computer Vision HW2

本仓库是计算机视觉 HW2 的完整实验工程，包含三个任务：

1. 使用 ImageNet 预训练 ResNet-18 微调 Oxford-IIIT Pet 宠物品种分类。
2. 使用 VisDrone 训练 YOLOv8n，并在自采视频上完成多目标跟踪、遮挡分析和越线计数。
3. 从零搭建 U-Net，在 Oxford-IIIT Pet 三分类分割任务上比较 CE、Dice、CE + Dice 三种损失。

最终实验报告位于 `report/report.pdf`。训练好的模型权重已上传到 Google Drive：

https://drive.google.com/drive/folders/1wvPcY7D8VMv1gOKWnwm_0SI5o_KIZYzv?usp=drive_link

## Repository Layout

```text
.
├── README.md
├── HW2_计算机视觉.pdf
├── report/
│   ├── report.pdf
│   ├── report.tex
│   ├── build_report_assets.py
│   └── assets/
├── task1/
│   ├── configs/
│   ├── src/
│   ├── checkpoints/
│   └── results/
├── task2/
│   ├── configs/
│   ├── scripts/
│   ├── datasets/
│   ├── runs/
│   └── outputs/
└── task3/
    ├── configs/
    ├── datasets/
    ├── losses/
    ├── models/
    ├── runs/
    └── results/
```

Large datasets, generated videos, and model checkpoints can be restored from local training outputs or the Google Drive link above.

## Environment

Python 3.10+ is recommended. Install the dependencies for the task you want to run:

```bash
conda create -n cv-hw2 python=3.10
conda activate cv-hw2

pip install -r task1/requirements.txt
pip install -r task2/requirements.txt
pip install -r task3/requirements.txt
```

If you use CUDA, install the PyTorch build matching your GPU driver first, then install the remaining requirements.

## Task 1: Pet Classification

Task 1 fine-tunes ResNet-18 on Oxford-IIIT Pet classification. The code automatically downloads Oxford-IIIT Pet into `task1/data` when needed.

Run the pretrained baseline:

```bash
cd task1
python main.py --config configs/resnet18_pretrained.yaml
```

Run hyperparameter search:

```bash
cd task1
python grid_search.py --base_config configs/resnet18_pretrained.yaml
```

Run the ablation and attention experiments:

```bash
cd task1
python main.py --config configs/resnet18_scratch_ablation.yaml
python main.py --config configs/resnet18_se_pretrained.yaml
```

Useful outputs:

- Checkpoints: `task1/checkpoints/*.pth`
- Summaries and histories: `task1/results/*.json`, `task1/results/experiment_summary.csv`
- Curves: `task1/results/figures/*.png`

## Task 2: Detection, Tracking, and Line Counting

Task 2 trains YOLOv8n on VisDrone and applies the trained detector to a campus video.

Expected VisDrone layout:

```text
task2/datasets/VisDrone/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

The YOLO dataset config is `task2/configs/VisDrone.yaml`. If your dataset is elsewhere, edit its `path` field.

Train YOLOv8n:

```bash
cd task2
python scripts/train.py --config configs/train_visdrone_yolov8n.yaml
```

Validate the trained model:

```bash
cd task2
python scripts/validate.py --weights runs/detect/visdrone_yolov8n_e50/weights/best.pt
```

Run multi-object tracking on the test video:

```bash
cd task2
python scripts/track_video.py --weights runs/detect/visdrone_yolov8n_e50/weights/best.pt --source data/videos/test_video.mp4 --output outputs/videos/tracked_video.mp4
```

Run line-crossing counting:

```bash
cd task2
python scripts/line_count.py --weights runs/detect/visdrone_yolov8n_e50/weights/best.pt --source data/videos/test_video.mp4 --output outputs/videos/line_count_video.mp4
```

Extract consecutive frames for occlusion analysis:

```bash
cd task2
python scripts/extract_occlusion_frames.py --source outputs/videos/tracked_video.mp4 --start 586 --num 4 --output_dir outputs/frames/occlusion
```

Useful outputs:

- Trained weights: `task2/runs/detect/visdrone_yolov8n_e50/weights/best.pt`
- Training curves and metrics: `task2/runs/detect/visdrone_yolov8n_e50/results.csv`, `results.png`
- Tracking videos: `task2/outputs/videos/*.mp4`
- Occlusion frames: `task2/outputs/frames/occlusion/*.jpg`

## Task 3: U-Net Segmentation

Task 3 trains a U-Net from scratch on Oxford-IIIT Pet trimap segmentation. The dataset is downloaded automatically into `task3/data` when needed.

Train the three loss configurations:

```bash
cd task3
python main.py --config configs/unet_ce.yaml
python main.py --config configs/unet_dice.yaml
python main.py --config configs/unet_ce_dice.yaml
```

Generate comparison plots:

```bash
cd task3
python plot_results.py
```

Generate prediction visualizations:

```bash
cd task3
python predict.py
```

Useful outputs:

- Checkpoints and logs: `task3/runs/*/`
- Loss and mIoU curves: `task3/results/*.png`
- Prediction examples: `task3/results/predictions/*.png`

## Build the Report

The submitted PDF is already generated at `report/report.pdf`. To rebuild it after changing results:

```bash
python report/build_report_assets.py
cd report
xelatex -interaction=nonstopmode report.tex
```

Run `xelatex` a second time if the table of contents needs updating.

## Main Results

Task 1:

- Best hyperparameter-search test accuracy: 0.8820.
- Pretrained ResNet-18 greatly outperforms random initialization.
- SE-block was implemented manually, but did not improve over the baseline under the current setting.

Task 2:

- YOLOv8n validation result on VisDrone: Precision 0.412, Recall 0.318, mAP50 0.287, mAP50-95 0.162.
- The model produces bounding boxes, categories, and Tracking IDs on the campus video.
- Occlusion mainly caused short target loss; obvious ID switch was not observed in the selected segment.
- Line counting counted 1 crossing while manual observation found about 3, showing the impact of unstable detection and tracking.

Task 3:

- CE best validation mIoU: 0.763213.
- Dice best validation mIoU: 0.767711.
- CE + Dice best validation mIoU: 0.770272, the best among the three settings.
