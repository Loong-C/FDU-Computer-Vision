# 题目一：2DGS 与 AIGC 多源 3D 资产融合

本目录完成 HW3 题目一：用不同来源生成 3D 资产，并把它们融合到真实背景场景中渲染多视角漫游视频。

## 目标

- 物体 A：手机多视角拍摄，使用 COLMAP 和 2DGS 重建。
- 物体 B：文本到 3D，使用 threestudio DreamFusion 和 SDS 优化。
- 物体 C：单图到 3D，使用 Magic123。
- 背景：使用 Mip-NeRF 360 `counter` 场景训练 2DGS。
- 融合：将 A/B/C 导出为 Mesh，在 Blender 中统一尺度、位置、光照和相机路径。

## 目录

```text
configs/   训练、生成和融合配置
data/      本地数据，未纳入 Git
docs/      预览图、报告图和本地镜像说明
external/  第三方代码，未纳入 Git
notes/     实验记录和耗时统计
outputs/   训练输出和渲染结果，未纳入 Git
patches/   兼容性补丁
release/   权重包元数据和公开链接
report/    题目一报告材料
scripts/   数据准备、训练、导出、融合和发布脚本
```

## 环境

2DGS 使用 WSL + Python 3.8 + CUDA 11.8。AIGC 使用独立 Python 3.10 环境：

```bash
bash scripts/setup_aigc_envs.sh bootstrap
bash scripts/setup_aigc_envs.sh toolchain
bash scripts/setup_aigc_envs.sh torch
bash scripts/setup_aigc_envs.sh threestudio-deps
bash scripts/setup_aigc_envs.sh magic123-deps
```

大模型缓存建议放在 D 盘或 WSL 挂载盘，避免占满系统盘。当前脚本默认使用 `/mnt/d/PackageCache/wsl`。

## 数据准备

物体 A：

```bash
bash scripts/prepare_colmap_object_a.sh --force
```

背景：

```bash
bash scripts/download_background_counter.sh
```

物体 C：

```bash
python scripts/prepare_object_c_image.py --swanlab-mode local
bash scripts/download_magic123_models.sh
bash scripts/prepare_magic123_object_c.sh
```

## 训练与生成

物体 A 和背景：

```bash
bash scripts/train_2dgs_object_a.sh
bash scripts/train_2dgs_background.sh
```

物体 B：

```bash
MODE=smoke bash scripts/generate_text3d_object_b.sh
MODE=full bash scripts/generate_text3d_object_b.sh
bash scripts/export_text3d_object_b.sh
```

物体 C：

```bash
MODE=smoke STAGE=coarse bash scripts/generate_image3d_object_c.sh
MODE=smoke STAGE=fine bash scripts/generate_image3d_object_c.sh
MODE=full STAGE=coarse bash scripts/generate_image3d_object_c.sh
MODE=full STAGE=fine bash scripts/generate_image3d_object_c.sh
```

`smoke` 用于检查依赖和显存，正式报告使用 `full` 输出。

## 融合渲染

```bash
bash scripts/setup_blender.sh
python scripts/export_colmap_camera_path.py \
  --images-bin data/raw/mipnerf360/counter/sparse/0/images.bin \
  --cameras-bin data/raw/mipnerf360/counter/sparse/0/cameras.bin \
  --output configs/counter_camera_path.json
MODE=smoke bash scripts/render_fusion_tracked.sh
MODE=formal bash scripts/render_fusion_tracked.sh
```

正式融合配置在 `configs/fusion_scene.json`，短测试配置在 `configs/fusion_scene_smoke.json`。

## 报告与检查

```bash
python scripts/check_task1_readiness.py --output logs/task1-readiness.json
python report/build_report_assets.py
python report/generate_report.py --final --publish
python report/render_report.py report/cv_hw3_task1_report.pdf
```

## 公开交付物

- 代码：`https://github.com/Loong-C/FDU-Computer-Vision/tree/main/hw3/task1`
- 权重包：`https://github.com/Loong-C/FDU-Computer-Vision/releases/download/hw3-task1-weights/cv-hw3-task1-best-weights.tar.gz`
- 漫游视频：`https://github.com/Loong-C/FDU-Computer-Vision/releases/download/hw3-task1-weights/task1-walkthrough.mp4`

Git 中只保留脚本、配置、报告和小型元数据。大数据、训练输出、视频和权重包由 `.gitignore` 排除。
