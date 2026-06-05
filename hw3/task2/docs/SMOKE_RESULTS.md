# Smoke 测试结果

本文件只记录实现检查结果，不作为正式实验结论。

## 环境

| 项目 | 值 |
| --- | --- |
| GPU | NVIDIA GeForce RTX 4060 Ti, 8 GB |
| Python | 3.12.9 |
| PyTorch | 2.11.0+cu128 |
| Torchvision | 0.26.0+cu128 |
| LeRobot | 0.5.1 |
| SwanLab | 0.7.16，offline |

## 已通过检查

- B-only ACT 训练。
- A+B+C ACT 训练。
- SwanLab offline 记录。
- best/latest checkpoint 写入。
- D 环境动作误差评估。
- 训练和评估图表生成。

## 合成数据 smoke

| 模型 | step 2 验证 L1 | D first-action MAE | D chunk MAE |
| --- | ---: | ---: | ---: |
| B-only | 0.907972 | 0.287660 | 0.285675 |
| A+B+C | 0.994025 | 0.337615 | 0.323337 |

合成数据规模很小，只用于证明代码链路能跑通。

## 官方帧子集 smoke

`scripts/run_official_subset_smoke.ps1` 使用官方 CALVIN ZIP 中的极小抽样帧。

| 模型 | step 2 验证 L1 | D first-action MAE | D chunk MAE |
| --- | ---: | ---: | ---: |
| B-only | 0.941828 | 0.083004 | 0.102024 |
| A+B+C | 1.387035 | 0.073969 | 0.085186 |

该结果仍是 smoke 指标，不能代表正式结论。
