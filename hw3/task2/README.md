# HW3 Task 2: LeRobot ACT on CALVIN

This repository implements the second computer vision homework task: compare a
CALVIN environment-B-only ACT policy against an A+B+C jointly trained ACT policy,
then evaluate both policies zero-shot on the unseen D environment.

The model is the upstream LeRobot `ACTPolicy` from the pinned `v0.5.1` release.
The local code adds a lazy adapter for the official CALVIN `.npz` frame format,
SwanLab experiment tracking, resumable checkpoints, zero-shot action-error
evaluation, CALVIN simulator rollout evaluation, plotting, and a small
end-to-end smoke workflow.

## Design Notes

- Large data stays inside ignored machine-local directories under `task2/`.
- Defaults point to `data\calvin`, `data\calvin-subset`, and `.cache\hf`.
- The official 517 GB `task_ABC_D.zip` archive is not downloaded automatically.
- `scripts/download_calvin_subset.py` fetches official frame windows with HTTP
  Range requests instead of downloading full archives.
- Formal experiments can use an evenly sampled subset by editing
  `configs/calvin_act.yaml`.
- B-only samples are selected from the official `training/scene_info.npy`
  metadata, not approximated by task labels.
- Zero-shot D evaluation is reported at two levels: sampled D-frame action MAE
  and CALVIN simulator rollout success in the unseen D scene.

The official CALVIN metadata defines these inclusive training-frame ranges:

| Environment | Frame range |
| --- | ---: |
| B | `0..598909` |
| C | `598910..1191338` |
| A | `1191339..1795044` |

## Repository Layout

```text
configs/                 formal and smoke experiment configs
docs/                    experiment and report checklists
scripts/                 bootstrap, train, evaluate, and plotting entry points
src/hw3_calvin_act/      raw CALVIN adapter, ACT construction, and tracking
tests/                   fast dataset and configuration tests
```

Ignored machine-local directories include `data/`, `external/`, `.cache/`,
`.venv/`, `outputs/`, `swanlog/`, and `artifacts/`.

## Windows Setup

Use PowerShell from this repository root:

```powershell
.\scripts\bootstrap.ps1
.\.venv\Scripts\Activate.ps1
.\scripts\set_env.ps1
python .\scripts\check_environment.py
```

`bootstrap.ps1` creates `.venv` under `task2/`, uses `.cache\hf` for package
and Hugging Face caches, and clones these upstream references under ignored
`external/` directories:

- `https://github.com/huggingface/lerobot.git` at `v0.5.1`
- `https://github.com/mees/calvin.git`

The CALVIN `calvin_env` submodule is initialized automatically. Install the
optional PyBullet/Hydra simulator dependencies only when running rollout:

```powershell
.\scripts\bootstrap.ps1 -WithCalvinRollout
```

The default bootstrap reuses system PyTorch packages to avoid a large duplicate
download. Pass `-FreshTorchEnvironment` for a clean environment if needed.
For formal experiments, prefer the fresh environment and keep the LeRobot
`v0.5.1` constraints `torch>=2.7,<2.11` and `torchvision>=0.22,<0.26`.
The local smoke test also passed with the machine's existing
`torch 2.11.0+cu128` and `torchvision 0.26.0+cu128`, but those versions are
outside the upstream support range.

## SwanLab

Offline logging works without credentials and is the default:

```powershell
$env:SWANLAB_MODE = "offline"
```

For cloud dashboards:

```powershell
swanlab login
$env:SWANLAB_MODE = "cloud"
```

Every training run also writes a plain `metrics.csv` file so results remain
inspectable and plottable without a SwanLab account.

Sync an existing offline run on Windows with UTF-8 console handling:

```powershell
.\scripts\sync_swanlab.ps1 -RunPaths @(
  ".\swanlog\run-YYYYMMDD_HHMMSS-xxxxxxxxxxxxxxxxxxxxx"
)
```

## Smoke Test

The smoke workflow generates a tiny CALVIN-shaped dataset locally and runs both
training conditions, both D evaluations, and report plots:

```powershell
.\scripts\run_smoke.ps1
```

Generated plots appear under `artifacts/smoke/`.

Run the same tiny workflow on HTTP-Range-downloaded official CALVIN frames:

```powershell
.\scripts\run_official_subset_smoke.ps1
```

## Official CALVIN Data

The official CALVIN repository documents:

| Split | Archive size | Use in this repository |
| --- | ---: | --- |
| `task_ABC_D` | 517 GB | B-only and A+B+C training |
| `task_D_D` | 166 GB | unseen-D evaluation |
| `calvin_debug_dataset` | 1.3 GB | optional inspection only |

Place extracted official data under the ignored local data directory:

```text
data\calvin\
  task_ABC_D\
    training\
      episode_0000000.npz
      scene_info.npy
      ...
  task_D_D\
    validation\
      episode_0000000.npz
      ...
```

For a practical partial-data experiment, download evenly distributed official
frame windows without fetching the full 517 GB and 166 GB ZIP archives:

```powershell
.\scripts\set_env.ps1 -DataRoot .\data\calvin-subset
python .\scripts\download_calvin_subset.py `
  --archive ALL `
  --output-root .\data\calvin-subset `
  --cache-root .\.cache\hf\calvin-remote-index `
  --windows-per-env 4 `
  --window-size 24 `
  --workers 2
```

The first run caches the remote ZIP central directories: about 229 MB for ABC
and 73 MB for D. It then downloads only the selected consecutive frame windows,
validates CRC checksums, and preserves the official directory layout. Increase
the number or size of windows gradually when disk space and training time allow.

Run a 20-step pilot with the formal ACT architecture after the smoke workflow:

```powershell
.\scripts\run_partial_pilot.ps1
```

The verified pilot numbers are documented in `docs/PILOT_RESULTS.md`.
An extended 200-step preliminary run and the final resource-aware 5000-step
experiment are documented there as well.

Run the resumable partial-data formal experiment with a larger but still
bounded HTTP-Range subset:

```powershell
.\scripts\run_partial_formal.ps1
```

The default formal wrapper requests `16` windows of `48` frames per
environment, trains both policies for `5000` steps with the same config, resumes
from each `latest.pt` checkpoint when present, evaluates unseen D action error,
and refreshes the report plots. Pass `-SkipDownload` when resuming without
changing the cached subset.

The verified formal experiment used `2304` ABC training frames and `768` D
evaluation frames. The final unseen-D action errors are:

| Run | D first-action MAE | D chunk-action MAE |
| --- | ---: | ---: |
| B-only | 0.226251 | 0.259475 |
| A+B+C | 0.187712 | 0.229145 |

ABC joint training reduces first-action MAE by `17.0%` and chunk-action MAE by
`11.7%` relative to B-only on the sampled unseen-D frames.

The same two trained policies were also deployed in the CALVIN D simulator with
the official 360-step per-subtask horizon and three generated five-task
evaluation sequences:

```powershell
.\scripts\run_zero_shot_d_rollout.ps1 `
  -MaxSequences 3 `
  -EpisodeLength 360 `
  -Device cuda
```

| Run | D rollout sequences | Avg solved subtasks | SR@1 | SR@5 |
| --- | ---: | ---: | ---: | ---: |
| B-only | 3 | 0.0 | 0.0% | 0.0% |
| A+B+C | 3 | 0.0 | 0.0% | 0.0% |

SwanLab rollout runs: B-only
https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/kcbgr0rmn3jokevjmxlyj and
A+B+C https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/mqrmkx48ojvthl5gm0u2y.

The simulator result is harsher than action MAE because this ACT policy is not
language-conditioned: it receives RGB/state observations and predicts actions,
while the official CALVIN long-horizon benchmark asks the policy to execute a
language-specified subtask sequence. The result still satisfies the deployment
check: both trained checkpoints run end-to-end in the unseen D environment, and
their zero-shot rollout success is explicitly recorded.

Install the small official scene metadata file after extracting data:

```powershell
.\scripts\download_scene_info.ps1 -Split ABC -DataRoot .\data\calvin
```

The formal config defaults to a bounded subset:

```yaml
data:
  max_train_samples: 50000
  stride: 3
```

This keeps the experiment practical on an 8 GB GPU while preserving the exact
environment split. Increase the sample count only after a successful smoke run.

## Train and Evaluate

Run the complete B-only versus A+B+C comparison:

```powershell
.\scripts\run_experiments.ps1 -DataRoot .\data\calvin
```

Equivalent explicit commands:

```powershell
python .\scripts\train.py `
  --config .\configs\calvin_act.yaml `
  --dataset-root .\data\calvin\task_ABC_D `
  --environments B `
  --run-name act_b_only

python .\scripts\train.py `
  --config .\configs\calvin_act.yaml `
  --dataset-root .\data\calvin\task_ABC_D `
  --environments ABC `
  --run-name act_abc_joint

python .\scripts\evaluate_action_error.py `
  --config .\configs\calvin_act.yaml `
  --dataset-root .\data\calvin\task_D_D `
  --checkpoint .\outputs\act_b_only\checkpoints\best.pt `
  --run-name act_b_only_to_d

python .\scripts\evaluate_calvin_rollout.py `
  --config .\configs\calvin_act.yaml `
  --dataset-root .\data\calvin\task_D_D `
  --checkpoint .\outputs\act_b_only\checkpoints\best.pt `
  --run-name act_b_only_to_d_rollout `
  --max-sequences 10 `
  --ep-len 360
```

Resume a stopped run:

```powershell
python .\scripts\train.py `
  --config .\configs\calvin_act.yaml `
  --dataset-root .\data\calvin\task_ABC_D `
  --environments B `
  --run-name act_b_only `
  --resume .\outputs\act_b_only\checkpoints\latest.pt
```

## WSL

CALVIN simulator rollout now works from the Windows `.venv` in PyBullet DIRECT
mode. Use WSL only as a fallback if a future simulator or rendering dependency
requires Linux, and operate on the same checkout through the mounted drive
instead of making a second clone:

```bash
cd "/mnt/f/Personal/Code/Computer Vision/hw3/task2"
git status
```

This keeps Windows and WSL synchronized because both environments operate on the
same files. Keep WSL-side caches under the mounted repository's
`task2/.cache/hf` directory as well.

## Report Checklist

The final report should include:

- ACT action-chunking mechanism and expected robustness under visual shift.
- Dataset ranges, subset size, batch size, learning rate, optimizer, number of
  steps, loss function, and GPU.
- SwanLab-exported Action L1 Loss and held-out validation curves.
- D-environment zero-shot first-action and chunk-action MAE.
- D-environment simulator rollout success rate and its language-conditioning
  limitation.
- A discussion of why joint A+B+C training helps or hurts relative to B-only.
- Public GitHub URL and cloud-storage URL for final weights.

See `docs/REPORT_CHECKLIST.md` for the full submission checklist.
Generate the technical report draft locally at
`docs/HW3_Task2_Report_Draft.pdf`; edit the member placeholders before
submission and rebuild it with:

```powershell
python .\scripts\build_report.py
```

## Submission Links

- Public GitHub repository:
  `https://github.com/Loong-C/FDU-Computer-Vision/tree/hw3/hw3/task2`
- Model weights release (temporary legacy host):
  `https://github.com/Loong-C/computer-vision-hw3-task2-calvin-act/releases/tag/formal-partial-v1`
- B-only best checkpoint:
  `https://github.com/Loong-C/computer-vision-hw3-task2-calvin-act/releases/download/formal-partial-v1/hw3-task2-act-b-only-best.pt`
- A+B+C best checkpoint:
  `https://github.com/Loong-C/computer-vision-hw3-task2-calvin-act/releases/download/formal-partial-v1/hw3-task2-act-abc-joint-best.pt`
- SwanLab project dashboard: `https://swanlab.cn/@Linkukai/hw3-calvin-act`

The source tree is consolidated in `FDU-Computer-Vision`. The verified weight
files remain on the legacy release temporarily so the download links stay
usable until the same assets are uploaded to an FDU repository release.
After `gh auth login -h github.com` is available on a machine with GitHub API
write access, publish the same verified assets with:

```powershell
.\scripts\publish_fdu_release.ps1
```

## Upstream References

- LeRobot: https://github.com/huggingface/lerobot
- LeRobot ACT source:
  https://github.com/huggingface/lerobot/tree/v0.5.1/src/lerobot/policies/act
- CALVIN: https://github.com/mees/calvin
- ACT paper: https://arxiv.org/abs/2304.13705
