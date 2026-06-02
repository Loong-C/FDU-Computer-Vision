# Final Report and Submission Checklist

## Report

- [ ] Group members, student IDs, and responsibility split on the first page.
- [x] Task background and CALVIN dataset description.
- [x] ACT architecture and action-chunking explanation.
- [x] B-only and A+B+C experiment settings table.
- [x] SwanLab loss curves and validation curves.
- [x] Zero-shot D action-error table or simulator success-rate table.
- [x] Analysis of visual distribution shift and ACT robustness.
- [x] Public GitHub URL.
- [x] Permanent model-weight download URL and access code if needed.

## Repository

- [x] Replace all `TODO` links in `README.md`.
- [x] Run `python -m pytest`.
- [x] Run `scripts/run_smoke.ps1`.
- [x] Keep data, caches, checkpoints, and SwanLab logs out of Git.
- [x] Commit the exact final config used for each reported experiment.

## Weights

- [x] Upload `best.pt` for B-only.
- [x] Upload `best.pt` for A+B+C joint training.
- [x] Verify the public release page, anonymous GitHub API asset metadata, and
      anonymous `SHA256SUMS.txt` download.
- [ ] Before submission, manually open one large checkpoint URL in a private
      browser window. This workstation's GitHub large-file HEAD requests timed
      out after upload.
