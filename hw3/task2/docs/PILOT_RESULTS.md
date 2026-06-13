# 官方部分数据实验结果

## 实验流程

短步数实验用于检查数据下载、ACT 前向与反向传播、checkpoint、环境 D 评估和 SwanLab 记录链路。
正式结果采用相同配置训练 5000 步，并按独立连续窗口上的最低验证损失选择权重。

```powershell
.\scripts\run_partial_formal.ps1
```

每个环境下载 `16` 个连续窗口，每个窗口 `48` 帧。stride 3 后，每个窗口产生 `16` 个样本；
每个环境固定留出 `2` 个完整窗口作为验证集。

| 数据 | 官方帧数 | 训练样本 | 验证样本 |
| --- | ---: | ---: | ---: |
| B-only | 768 | 224 | 32 |
| A+B+C | 2304 | 672 | 96 |
| D 评估 | 768 | - | 768 |

训练与验证动作监督帧交集为 `0`。具体窗口边界和审计结果保存在每个训练目录的
`split_manifest.json`。

## 正式结果

| 模型 | 最佳序列验证 L1 | 最佳步数 | D first-action MAE | D chunk MAE |
| --- | ---: | ---: | ---: | ---: |
| B-only | 0.505717 | 250 | 0.253965 | 0.268460 |
| A+B+C | 0.561016 | 500 | 0.198150 | 0.222258 |

A+B+C 使 first-action MAE 降低 `22.0%`，chunk-action MAE 降低 `17.2%`。

训练 Action L1 在 5000 步内持续下降，序列验证损失在早期达到最低后升高并波动。
正式离线评估使用各自的最佳 checkpoint。

## D simulator rollout

```powershell
.\scripts\bootstrap.ps1 -WithCalvinRollout
.\scripts\run_zero_shot_d_rollout.ps1 `
  -MaxSequences 3 `
  -EpisodeLength 360 `
  -Device cuda
```

| 模型 | 序列数 | 平均完成子任务 | SR@1 | SR@5 |
| --- | ---: | ---: | ---: | ---: |
| B-only | 3 | 0.0 | 0.0% | 0.0% |
| A+B+C | 3 | 0.0 | 0.0% | 0.0% |

rollout 使用官方 D 场景、任务 oracle 和 validation language annotations。ACT 模型的输入为图像和
机器人状态，未包含语言条件；离线动作误差与闭环长时成功率分别衡量局部动作回归和任务执行能力。

## SwanLab

| 运行 | 链接 |
| --- | --- |
| B-only 训练 | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/5604rx1q61tfydytkh9eo |
| A+B+C 训练 | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/42di3m9zyj2321v11e3xb |
| B-only 到 D 评估 | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/dq0p2cm8j0ypczffatbj6 |
| A+B+C 到 D 评估 | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/6dbyoupmdn0c9loq5p9dv |
| B-only 到 D rollout | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/yeltzn7w84t477i0pyme1 |
| A+B+C 到 D rollout | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/05wghj2bt442shmdzxijj |

## 权重

| 模型 | 文件 | SHA256 |
| --- | --- | --- |
| B-only | [hw3-task2-act-b-only-best.pt](https://github.com/Loong-C/FDU-Computer-Vision/releases/download/hw3-task2-formal-partial-v1/hw3-task2-act-b-only-best.pt) | `49AD38CB15B38FA1AE208CAAC70DA0E41536AA3DADCD6E7408A58647BED06CE5` |
| A+B+C | [hw3-task2-act-abc-joint-best.pt](https://github.com/Loong-C/FDU-Computer-Vision/releases/download/hw3-task2-formal-partial-v1/hw3-task2-act-abc-joint-best.pt) | `7A1EF8617B7F741C0DD8E73B3A6D6C23B6D03381D543F13E95D7150B61832C5B` |

Release 页面：
https://github.com/Loong-C/FDU-Computer-Vision/releases/tag/hw3-task2-formal-partial-v1

Google Drive 镜像：
https://drive.google.com/drive/folders/1v9oc1uTbZS31SaDJaT7sYV8m5dutMo1y?usp=drive_link
