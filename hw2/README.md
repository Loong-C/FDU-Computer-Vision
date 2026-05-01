# 复旦大学计算机视觉 HW2

本仓库为计算机视觉 HW2 的完整工程与报告材料，包含三个实验任务：

1. 使用 ImageNet 预训练的 ResNet-18 在 Oxford-IIIT Pet 数据集上完成宠物品种分类，并进行超参数分析、预训练消融和注意力机制实验。
2. 使用 VisDrone 数据集训练 YOLOv8n，并在自采校园视频上完成目标检测、多目标跟踪、遮挡分析和越线计数。
3. 从零搭建 U-Net，在 Oxford-IIIT Pet trimap 分割任务上比较 CE、Dice 和 CE + Dice 三种损失配置。

最终报告位于 `report/report.pdf`。大体积数据、生成视频和模型权重可通过下方网盘链接恢复：

https://drive.google.com/drive/folders/1wvPcY7D8VMv1gOKWnwm_0SI5o_KIZYzv?usp=drive_link

## 仓库结构

```text
.
├── README.md
├── HW2_计算机视觉.pdf
├── report/
│   ├── report.pdf
│   ├── report.tex
│   ├── build_report_assets.py
│   ├── log_to_swanlab.py
│   ├── capture_swanlab_screenshots.py
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

## 环境配置

建议使用 Python 3.10 或更新版本。可以按需安装三个任务的依赖：

```bash
conda create -n cv-hw2 python=3.10
conda activate cv-hw2

pip install -r task1/requirements.txt
pip install -r task2/requirements.txt
pip install -r task3/requirements.txt
```

如果使用 CUDA，请先安装与本机显卡驱动匹配的 PyTorch 版本，再安装其余依赖。

## 任务一：宠物分类

任务一在 Oxford-IIIT Pet 分类数据集上微调 ResNet-18。代码会在需要时自动下载数据集到 `task1/data`。

运行预训练 baseline：

```bash
cd task1
python main.py --config configs/resnet18_pretrained.yaml
```

运行超参数搜索：

```bash
cd task1
python grid_search.py --base_config configs/resnet18_pretrained.yaml
```

运行预训练消融和注意力机制实验：

```bash
cd task1
python main.py --config configs/resnet18_scratch_ablation.yaml
python main.py --config configs/resnet18_se_pretrained.yaml
```

主要输出：

- 模型权重：`task1/checkpoints/*.pth`
- 实验摘要与训练历史：`task1/results/*.json`、`task1/results/experiment_summary.csv`
- 曲线图：`task1/results/figures/*.png`

## 任务二：检测、跟踪与越线计数

任务二使用 VisDrone 数据集训练 YOLOv8n，并将训练后的检测器应用到校园道路视频。

期望的 VisDrone 数据目录结构如下：

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

YOLO 数据集配置文件为 `task2/configs/VisDrone.yaml`。如果数据集位置不同，请修改其中的 `path` 字段。

训练 YOLOv8n：

```bash
cd task2
python scripts/train.py --config configs/train_visdrone_yolov8n.yaml
```

验证训练好的模型：

```bash
cd task2
python scripts/validate.py --weights runs/detect/visdrone_yolov8n_e50/weights/best.pt
```

在测试视频上运行多目标跟踪：

```bash
cd task2
python scripts/track_video.py --weights runs/detect/visdrone_yolov8n_e50/weights/best.pt --source data/videos/test_video.mp4 --output outputs/videos/tracked_video.mp4
```

运行越线计数：

```bash
cd task2
python scripts/line_count.py --weights runs/detect/visdrone_yolov8n_e50/weights/best.pt --source data/videos/test_video.mp4 --output outputs/videos/line_count_video.mp4
```

提取遮挡分析所需的连续帧：

```bash
cd task2
python scripts/extract_occlusion_frames.py --source outputs/videos/tracked_video.mp4 --start 586 --num 5 --output_dir outputs/frames/occlusion
```

主要输出：

- 训练权重：`task2/runs/detect/visdrone_yolov8n_e50/weights/best.pt`
- 训练曲线与指标：`task2/runs/detect/visdrone_yolov8n_e50/results.csv`、`results.png`
- 跟踪与计数视频：`task2/outputs/videos/*.mp4`
- 遮挡分析连续帧：`task2/outputs/frames/occlusion/*.jpg`

## 任务三：U-Net 分割

任务三从零训练 U-Net，在 Oxford-IIIT Pet trimap 分割任务上比较 CE、Dice 和 CE + Dice 三种损失函数。代码会在需要时自动下载数据集到 `task3/data`。

训练三种损失配置：

```bash
cd task3
python main.py --config configs/unet_ce.yaml
python main.py --config configs/unet_dice.yaml
python main.py --config configs/unet_ce_dice.yaml
```

生成对比曲线：

```bash
cd task3
python plot_results.py
```

生成预测可视化：

```bash
cd task3
python predict.py
```

主要输出：

- 模型权重与日志：`task3/runs/*/`
- 损失曲线与 mIoU 曲线：`task3/results/*.png`
- 预测可视化：`task3/results/predictions/*.png`

## SwanLab 可视化

报告中已经加入 SwanLab 本地看板截图，以满足作业对 WandB 或 SwanLab 可视化截图的要求。已有的 JSON/CSV 训练历史会被补录为本地 SwanLab runs，因此不需要在线 SwanLab 账号。

截图脚本会启动本地看板，并调用已安装的 Chrome 或 Edge 浏览器以无头模式截图：

```bash
pip install "swanlab[dashboard]"
python report/log_to_swanlab.py
python report/capture_swanlab_screenshots.py
```

生成的截图会保存到 `report/assets/swanlab_dashboard_*.png`，并嵌入 `report/report.pdf`。

## 报告构建

已生成的提交版报告位于 `report/report.pdf`。如果修改了实验结果或报告内容，可以按下面流程重新构建：

```bash
python report/build_report_assets.py
cd report
xelatex -interaction=nonstopmode report.tex
```

如果目录或交叉引用没有更新，请再运行一次 `xelatex`。

## 主要结果

任务一：

- 超参数搜索中的最佳测试准确率为 0.8820。
- ImageNet 预训练 ResNet-18 明显优于随机初始化训练。
- 手动实现的 SE-block 在当前设置下未超过 baseline。

任务二：

- YOLOv8n 在 VisDrone 验证集上的结果为 Precision 0.412、Recall 0.318、mAP50 0.287、mAP50-95 0.162。
- 模型能够在校园视频中输出检测框、类别和 Tracking ID。
- 遮挡片段主要表现为目标短时丢失，未观察到明显 ID switch。
- 越线计数程序统计到 1 次穿越，人工观察约为 3 次，说明检测与跟踪不稳定会影响计数准确性。

任务三：

- CE 的最佳验证 mIoU 为 0.763213。
- Dice 的最佳验证 mIoU 为 0.767711。
- CE + Dice 的最佳验证 mIoU 为 0.770272，是三种配置中最高的结果。
