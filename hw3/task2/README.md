# 题目二：LeRobot ACT 在 CALVIN 上的跨环境泛化

本目录完成 HW3 题目二：比较只在 CALVIN 环境 B 训练的 ACT 策略，和在 A+B+C 混合环境训练的 ACT 策略，并在未见过的 D 环境上做零样本评估。

## 核心结论

- 两个模型使用相同 ACT 架构、优化器和训练步数。
- A+B+C 联合训练提高了训练分布复杂度，验证 L1 更高。
- 在 D 环境抽样帧上，A+B+C 的 first-action MAE 降低 `17.0%`，chunk-action MAE 降低 `11.7%`。
- 两个模型都能在 CALVIN D simulator 中闭环运行，但 3 条五任务序列的 SR@1 到 SR@5 均为 `0.0%`。
- simulator 结果说明：离线动作误差改善不等于长时任务成功，语言条件缺失和误差累积仍是主要限制。

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

| 模型 | 验证 L1 | D first-action MAE | D chunk MAE |
| --- | ---: | ---: | ---: |
| B-only | 0.324629 | 0.226251 | 0.259475 |
| A+B+C | 0.386954 | 0.187712 | 0.229145 |

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
- 权重镜像：`https://drive.google.com/drive/folders/1v9oc1uTbZS31SaDJaT7sYV8m5dutMo1y?usp=drive_link`
- SwanLab 项目：`https://swanlab.cn/@Linkukai/hw3-calvin-act`

权重文件：

- `hw3-task2-act-b-only-best.pt`
- `hw3-task2-act-abc-joint-best.pt`

SHA256 记录在 `outputs/official_subset_formal/release/SHA256SUMS.txt`，大权重不提交到 Git。
