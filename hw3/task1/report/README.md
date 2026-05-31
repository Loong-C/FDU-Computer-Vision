# Task 1 PDF Report

The report is generated from tracked source files and local experiment
outputs. Keep generated charts under `report/assets/`; temporary PDFs and
rendered pages stay under ignored `report/output/` and `tmp/`.

Build and inspect a draft:

```bash
conda activate cv_hw3_threestudio
python report/build_report_assets.py
python report/generate_report.py
python report/render_report.py report/output/pdf/cv_hw3_task1_report_draft.pdf
```

After Object C, fusion, and the cloud-weights upload are complete, update
`report/report_data.json` and publish the final PDF:

```bash
python report/build_report_assets.py
python report/generate_report.py --final --publish
python report/render_report.py report/cv_hw3_task1_report.pdf
```

`--final` validates that the report has no remaining deliverable placeholders.
