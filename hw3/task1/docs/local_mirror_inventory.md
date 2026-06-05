# Windows 本地镜像清单

生成时间：`2026-06-01`，对应题目一最终整理版本。

## 路径

- WSL 主工作区：`/home/hp/cv_hw3/FDU-Computer-Vision/hw3/task1`
- Windows 镜像：`F:\Personal\Code\Computer Vision\hw3\task1`
- Release 打包缓存：`D:\PackageCache\cv-hw3-task1-release`

## 已镜像到 Windows 的内容

- `outputs/`：正式训练、smoke 测试、导出 Mesh、渲染图和融合视频。
- `logs/`：运行日志、readiness 检查和恢复记录。
- `swanlog/`：本地 SwanLab 记录。
- `data/`：手机图片、COLMAP 输入、Mip-NeRF 360 背景和物体 C 图片。
- `report/`、`docs/`、`notes/`：PDF、图表、预览、实验记录和耗时统计。
- `configs/`、`scripts/`、`patches/`：复现配置和脚本。
- `release/`：权重包、SHA256、manifest、公开链接和发布说明。

## 未重复镜像的内容

以下依赖体积较大或可重新下载，保留在 WSL：

- Magic123 的 Zero123 与 MiDaS 预训练模型。
- Linux 版 Blender 便携运行时。
- 第三方仓库的 `.git`、编译缓存和临时文件。

## 直接交付物

- 最终 PDF：`task1/report/cv_hw3_task1_report.pdf`
- 漫游视频：`task1/outputs/fusion/task1-walkthrough.mp4`
- 权重包：`task1/release/cv-hw3-task1-best-weights.tar.gz`
