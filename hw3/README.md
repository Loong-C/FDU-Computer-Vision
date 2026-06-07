# 计算机视觉 HW3

本目录是复旦大学计算机视觉课程 HW3 的最终交付版本，包含两道题目的代码、配置、报告材料和复现说明。

## 目录

```text
report/   统一实验报告、图表生成脚本和上传清单
task1/    2DGS 与 AIGC 多源 3D 资产融合
task2/    LeRobot ACT 在 CALVIN 上的跨环境泛化实验
```

## 交付物

- 最终报告：`report/HW3_Report_ChenJialong_24300980041.pdf`
- 题目一代码：`task1/`
- 题目二代码：`task2/`
- 题目一权重与视频：GitHub Release `hw3-task1-weights`
- 题目二权重：GitHub Release `hw3-task2-formal-partial-v1`，Google Drive 提供镜像

大数据集、训练输出、缓存、模型权重和视频不直接提交到 Git；仓库只保留源码、配置、报告、图表和校验信息。

## 快速复现

题目一：

```bash
cd task1
bash scripts/train_2dgs_object_a.sh
bash scripts/train_2dgs_background.sh
MODE=full bash scripts/generate_text3d_object_b.sh
MODE=full STAGE=coarse bash scripts/generate_image3d_object_c.sh
MODE=full STAGE=fine bash scripts/generate_image3d_object_c.sh
MODE=formal bash scripts/render_fusion_tracked.sh
```

题目二：

```powershell
cd task2
.\scripts\bootstrap.ps1
.\scripts\run_partial_formal.ps1
.\scripts\bootstrap.ps1 -WithCalvinRollout
.\scripts\run_zero_shot_d_rollout.ps1 -MaxSequences 3 -EpisodeLength 360 -Device cuda
```

报告：

```powershell
.\report\build_report.ps1
```

## 公开链接

- 代码仓库：`https://github.com/Loong-C/FDU-Computer-Vision/tree/main/hw3`
- 题目一权重：`https://github.com/Loong-C/FDU-Computer-Vision/releases/download/hw3-task1-weights/cv-hw3-task1-best-weights.tar.gz`
- 题目一视频：`https://github.com/Loong-C/FDU-Computer-Vision/releases/download/hw3-task1-weights/task1-walkthrough.mp4`
- 题目二权重 Release：`https://github.com/Loong-C/FDU-Computer-Vision/releases/tag/hw3-task2-formal-partial-v1`
- 题目二 B-only 权重：`https://github.com/Loong-C/FDU-Computer-Vision/releases/download/hw3-task2-formal-partial-v1/hw3-task2-act-b-only-best.pt`
- 题目二 A+B+C 权重：`https://github.com/Loong-C/FDU-Computer-Vision/releases/download/hw3-task2-formal-partial-v1/hw3-task2-act-abc-joint-best.pt`
- 题目二权重镜像：`https://drive.google.com/drive/folders/1v9oc1uTbZS31SaDJaT7sYV8m5dutMo1y?usp=drive_link`
- 题目二 SwanLab：`https://swanlab.cn/@Linkukai/hw3-calvin-act`
