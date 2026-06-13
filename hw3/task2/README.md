# 题目二：LeRobot ACT 在 CALVIN 上的跨环境泛化

本目录完成 HW3 题目二：比较只在 CALVIN 环境 B 训练的 ACT 策略，和在 A+B+C 混合环境训练的 ACT 策略，并在未见过的 D 环境上做零样本评估。

## 核心结论

- 两个模型使用相同 ACT 架构、优化器和训练步数。
- 训练和验证按环境内连续窗口划分，动作监督帧交集为 `0`。
- A+B+C 联合训练的最佳序列验证 L1 略高，训练分布包含更多视觉变化。
- 在 D 环境抽样帧上，A+B+C 的 first-action MAE 降低 `22.0%`，chunk-action MAE 降低 `17.2%`。
- 两个模型都能在 CALVIN D simulator 中闭环运行，但 3 条五任务序列的 SR@1 到 SR@5 均为 `0.0%`。
- 离线动作误差与长时任务成功反映不同层面的泛化，语言条件缺失和误差累积仍是主要限制。

## 目录

```text
configs/             正式和 smoke 配置
docs/                实验计划、结果记录和提交清单
scripts/             环境、下载、训练、评估、画图和发布脚本
src/hw3_calvin_act/  CALVIN 数据适配、ACT 构建和 SwanLab 记录
tests/               快速单元测试
```

本地数据、缓存、输出、权重和 SwanLab 日志由 `.gitignore` 排除。

## 环境

在 PowerShell 中运行：

```powershell
.\scripts\bootstrap.ps1
.\.venv\Scripts\Activate.ps1
.\scripts\set_env.ps1
python .\scripts\check_environment.py
```

如需运行 CALVIN simulator rollout：

```powershell
.\scripts\bootstrap.ps1 -WithCalvinRollout
```

`bootstrap.ps1` 会创建本地 `.venv`，并在 `external/` 中拉取 LeRobot `v0.5.1` 和 CALVIN 代码。

## 数据

完整 CALVIN 数据很大：

| 数据 | 大小 | 用途 |
| --- | ---: | --- |
| `task_ABC_D` | 517 GB | A/B/C 训练 |
| `task_D_D` | 166 GB | D 环境评估 |

本实验使用 HTTP Range 下载官方 ZIP 中的均匀抽样帧，不下载完整压缩包：

```powershell
.\scripts\set_env.ps1 -DataRoot .\data\calvin-subset
python .\scripts\download_calvin_subset.py `
  --archive ALL `
  --output-root .\data\calvin-subset `
  --cache-root .\.cache\hf\calvin-remote-index `
  --windows-per-env 16 `
  --window-size 48 `
  --workers 2
```

正式实验使用 `2304` 帧 A+B+C 训练数据和 `768` 帧 D 评估数据。
每个训练环境包含 `16` 个连续 48 帧窗口。划分时每个环境固定留出 `2` 个完整窗口，
得到 B-only 的 `224/32` 个训练/验证样本，以及 A+B+C 的 `672/96` 个训练/验证样本。
每次训练都会在 `split_manifest.json` 中记录窗口边界并审计动作帧交集。

## 训练与评估

正式部分数据实验：

```powershell
.\scripts\run_partial_formal.ps1
```

D 环境 simulator rollout：

```powershell
.\scripts\run_zero_shot_d_rollout.ps1 `
  -MaxSequences 3 `
  -EpisodeLength 360 `
  -Device cuda
```

快速 smoke 测试：

```powershell
.\scripts\run_smoke.ps1
.\scripts\run_official_subset_smoke.ps1
```

## 正式结果

| 模型 | 最佳序列验证 L1 | D first-action MAE | D chunk MAE |
| --- | ---: | ---: | ---: |
| B-only | 0.505717 | 0.253965 | 0.268460 |
| A+B+C | 0.561016 | 0.198150 | 0.222258 |

| 模型 | D rollout 序列数 | 平均完成子任务 | SR@1 | SR@5 |
| --- | ---: | ---: | ---: | ---: |
| B-only | 3 | 0.0 | 0.0% | 0.0% |
| A+B+C | 3 | 0.0 | 0.0% | 0.0% |

详细记录见：

- `docs/PILOT_RESULTS.md`
- `docs/FINAL_REPORT.md`
- `docs/images/formal_training_curves.svg`
- `docs/images/formal_zero_shot_d_action_error.svg`

## 公开链接

- 代码：`https://github.com/Loong-C/FDU-Computer-Vision/tree/main/hw3/task2`
- 权重 Release：`https://github.com/Loong-C/FDU-Computer-Vision/releases/tag/hw3-task2-formal-partial-v1`
- B-only 权重：`https://github.com/Loong-C/FDU-Computer-Vision/releases/download/hw3-task2-formal-partial-v1/hw3-task2-act-b-only-best.pt`
- A+B+C 权重：`https://github.com/Loong-C/FDU-Computer-Vision/releases/download/hw3-task2-formal-partial-v1/hw3-task2-act-abc-joint-best.pt`
- 权重网盘镜像：`https://drive.google.com/drive/folders/1v9oc1uTbZS31SaDJaT7sYV8m5dutMo1y?usp=drive_link`
- SwanLab 项目：`https://swanlab.cn/@Linkukai/hw3-calvin-act`
- B-only 训练：`https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/5604rx1q61tfydytkh9eo`
- A+B+C 训练：`https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/42di3m9zyj2321v11e3xb`

权重文件：

- `hw3-task2-act-b-only-best.pt`
- `hw3-task2-act-abc-joint-best.pt`

SHA256 记录在 `outputs/official_subset_formal/release/SHA256SUMS.txt`，大权重不提交到 Git。
当前摘要分别为 `49ad38cb15b38fa1ae208caac70da0e41536aa3dadcd6e7408a58647bed06ce5`
和 `7a1ef8617b7f741c0dd8e73b3a6d6c23b6d03381d543f13e95d7150b61832c5b`。
旧独立仓库的迁移核对见 `docs/LEGACY_REPOSITORY_MIGRATION.md`。
