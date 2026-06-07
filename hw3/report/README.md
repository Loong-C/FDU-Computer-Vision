# HW3 统一报告

本目录保存 HW3 最终报告和图表构建脚本。

- 学生：陈家龙
- 学号：`24300980041`
- 报告文件：`HW3_Report_ChenJialong_24300980041.pdf`

## 构建

在 `hw3` 目录运行：

```powershell
.\report\build_report.ps1
```

脚本会先刷新图表，再用 XeLaTeX 生成最终 PDF。

## 文件说明

- `hw3_report.tex`：报告源码。
- `build_report_assets.py`：复制实验图并生成汇总图。
- `build_report.ps1`：一键构建脚本。
- `UPLOAD_CHECKLIST.md`：网盘上传和检查清单。
- `assets/`：报告使用的图表。
- `build/`：XeLaTeX 中间文件，未纳入 Git。

## 公开下载

- 题目二权重 Release：`https://github.com/Loong-C/FDU-Computer-Vision/releases/tag/hw3-task2-formal-partial-v1`
- 题目二权重网盘镜像：`https://drive.google.com/drive/folders/1v9oc1uTbZS31SaDJaT7sYV8m5dutMo1y?usp=drive_link`
