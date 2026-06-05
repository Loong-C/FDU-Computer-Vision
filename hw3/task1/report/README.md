# 题目一报告材料

本目录保存题目一的报告生成脚本、图表和 PDF。

## 草稿构建

```bash
conda activate cv_hw3_threestudio
python report/build_report_assets.py
python report/generate_report.py
python report/render_report.py report/output/pdf/cv_hw3_task1_report_draft.pdf
```

## 最终发布

```bash
python scripts/package_best_weights.py
bash scripts/publish_best_weights_release.sh
python scripts/finalize_task1_metadata.py \
  --cloud-weights-url https://github.com/Loong-C/FDU-Computer-Vision/releases/download/hw3-task1-weights/cv-hw3-task1-best-weights.tar.gz \
  --public-walkthrough-url https://github.com/Loong-C/FDU-Computer-Vision/releases/download/hw3-task1-weights/task1-walkthrough.mp4
python report/build_report_assets.py
python report/generate_report.py --final --publish
python report/render_report.py report/cv_hw3_task1_report.pdf
```

`--final` 会检查正式 Object C、融合视频、融合预览和公开权重链接是否齐全。
