# HW3 Unified Report

This directory contains the submission report for:

- Student: 陈家龙
- Student ID: `24300980041`

The report was rewritten as one unified technical document. Existing Task 1
and Task 2 drafts are treated only as experiment evidence; they are not merged
or reused as report prose.

## Build

From the `hw3` directory:

```powershell
.\report\build_report.ps1
```

The final PDF is written to:

```text
report/HW3_Report_ChenJialong_24300980041.pdf
```

## Files

- `hw3_report.tex`: report source.
- `build_report_assets.py`: copies verified experiment figures and generates
  the fusion-pipeline, Mesh three-view, and zero-shot comparison figures.
- `build_report.ps1`: reproducible asset and PDF build.
- `UPLOAD_CHECKLIST.md`: files mirrored to the Google Drive submission folder.
- `assets/`: figures used by the report.
- `build/`: XeLaTeX intermediate files.
