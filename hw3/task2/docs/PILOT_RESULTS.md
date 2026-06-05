# 官方部分数据实验结果

本文件记录从低成本 pilot 到正式 5000 步实验的结果。

## 20 步 pilot

数据：

| 划分 | 选取帧 |
| --- | ---: |
| ABC 训练 | 288 |
| D 评估 | 96 |

配置：

| 项目 | 值 |
| --- | --- |
| GPU | NVIDIA GeForce RTX 4060 Ti, 8 GB |
| LeRobot | 0.5.1 |
| 策略 | ACT |
| 图像大小 | 128 |
| 动作块长度 | 20 |
| batch size | 4 |
| 学习率 | `1e-5` |
| 步数 | 20 |

结果：

| 模型 | 验证 L1 | D first-action MAE | D chunk MAE |
| --- | ---: | ---: | ---: |
| B-only | 0.635219 | 0.298444 | 0.288037 |
| A+B+C | 0.737689 | 0.159460 | 0.174439 |

pilot 只用于确认方向，不作为最终结论。

## 200 步初步实验

```powershell
.\scripts\run_partial_pilot.ps1 `
  -Steps 200 `
  -OutputRoot "F:\Personal\Code\Computer Vision\hw3\task2\outputs\official_subset_200"
```

| 模型 | 验证 L1 | D first-action MAE | D chunk MAE |
| --- | ---: | ---: | ---: |
| B-only | 0.364523 | 0.281547 | 0.268683 |
| A+B+C | 0.415782 | 0.239925 | 0.257423 |

200 步时 A+B+C 仍降低 D 环境动作误差。

## 正式 5000 步实验

```powershell
.\scripts\run_partial_formal.ps1
```

正式实验下载每个环境 `16` 个连续窗口，每个窗口 `48` 帧，不下载完整 CALVIN 压缩包。

| 划分 | 官方帧数 | 本地数据 |
| --- | ---: | ---: |
| A+B+C 训练 | 2304 | 约 634 MiB |
| D 评估 | 768 | 约 213 MiB |

| 模型 | 验证 L1 | D first-action MAE | D chunk MAE |
| --- | ---: | ---: | ---: |
| B-only | 0.324629 | 0.226251 | 0.259475 |
| A+B+C | 0.386954 | 0.187712 | 0.229145 |

A+B+C 使 first-action MAE 降低 `17.0%`，chunk-action MAE 降低 `11.7%`。

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

rollout 使用官方 D 场景、任务 oracle 和 validation language annotations。当前 ACT 模型没有语言条件输入，因此 simulator 成功率应与离线动作 MAE 分开解读。

## SwanLab

| 运行 | 链接 |
| --- | --- |
| B-only 训练 | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/y34dmlyk6ol06me1f1ig0 |
| A+B+C 训练 | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/t3kfag5dsiipp3wwxy4te |
| B-only 到 D 评估 | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/b1hdsdo4vgrodwkk3syr7 |
| A+B+C 到 D 评估 | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/5ooypxeqhgp4xja928tpk |
| B-only 到 D rollout | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/kcbgr0rmn3jokevjmxlyj |
| A+B+C 到 D rollout | https://swanlab.cn/@Linkukai/hw3-calvin-act/runs/mqrmkx48ojvthl5gm0u2y |

## 权重

| 模型 | 文件 | SHA256 |
| --- | --- | --- |
| B-only | `hw3-task2-act-b-only-best.pt` | `58AFAE052EF2CE029F92C9258E1B5012A9C44FAC5753C1C8330B7D196A976131` |
| A+B+C | `hw3-task2-act-abc-joint-best.pt` | `1B1F182E61026929F0A5FFDC5EE096D15E4771FEBD111D9EFE3D88BC4A9ADCFF` |
