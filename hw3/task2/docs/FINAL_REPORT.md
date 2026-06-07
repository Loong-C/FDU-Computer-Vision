# 题目二最终报告草稿

本文件记录题目二的正式实验内容。最终提交版已整合到 `report/HW3_Report_ChenJialong_24300980041.pdf`。

## 基本信息

| 项目 | 内容 |
| --- | --- |
| 姓名 | 陈家龙 |
| 学号 | `24300980041` |
| 组队情况 | 单人完成 |
| 分工 | 独立完成 |

## 公开链接

- 代码：`https://github.com/Loong-C/FDU-Computer-Vision/tree/main/hw3/task2`
- 权重 Release：`https://github.com/Loong-C/FDU-Computer-Vision/releases/tag/hw3-task2-formal-partial-v1`
- 权重网盘镜像：`https://drive.google.com/drive/folders/1v9oc1uTbZS31SaDJaT7sYV8m5dutMo1y?usp=drive_link`
- SwanLab：`https://swanlab.cn/@Linkukai/hw3-calvin-act`

## 任务

训练两个 LeRobot ACT 策略：

| 模型 | 训练环境 | 测试环境 |
| --- | --- | --- |
| B-only | B | D |
| A+B+C | A+B+C | D |

两者使用相同架构、优化器、batch size、学习率和训练步数。差异只来自训练环境分布。

## 数据

完整 CALVIN 数据过大，因此正式实验只下载官方 ZIP 中的均匀抽样帧：

| 用途 | 帧数 |
| --- | ---: |
| A+B+C 训练源数据 | 2304 |
| B-only 训练源数据 | 768 |
| D 零样本评估 | 768 |

处理后样本数：

- B-only：230 个训练样本，26 个验证样本。
- A+B+C：691 个训练样本，77 个验证样本。

## 方法

ACT 从当前图像和机器人状态预测未来一段动作。本实验使用 LeRobot `v0.5.1` 的 `ACTPolicy`。

| 项目 | 值 |
| --- | --- |
| 视觉骨干 | ResNet-18 |
| 图像大小 | 128 |
| Transformer 维度 | 256 |
| 编码器/解码器层数 | 3 / 1 |
| 动作块长度 | 20 |
| batch size | 4 |
| 优化器 | AdamW |
| 学习率 | `1e-5` |
| weight decay | `1e-4` |
| 训练步数 | 5000 |
| GPU | NVIDIA GeForce RTX 4060 Ti, 8 GB |

## 结果

| 模型 | 验证 L1 | D first-action MAE | D chunk MAE |
| --- | ---: | ---: | ---: |
| B-only | 0.324629 | 0.226251 | 0.259475 |
| A+B+C | 0.386954 | 0.187712 | 0.229145 |

A+B+C 相比 B-only：

- first-action MAE 降低 `17.0%`。
- chunk-action MAE 降低 `11.7%`。

CALVIN D simulator rollout：

| 模型 | 序列数 | 平均完成子任务 | SR@1 | SR@5 |
| --- | ---: | ---: | ---: | ---: |
| B-only | 3 | 0.0 | 0.0% | 0.0% |
| A+B+C | 3 | 0.0 | 0.0% | 0.0% |

## 分析

A+B+C 的验证损失更高，因为模型要同时拟合三个视觉场景。但它在 D 环境的动作误差更低，说明多环境训练增强了局部动作预测的视觉泛化。

rollout 成功率仍为 0，原因是该 ACT 输入没有语言指令，只根据图像和状态预测动作块。CALVIN 长时任务要求执行语言指定的子任务序列，闭环误差会持续累积。因此，离线 MAE 改善说明局部动作更接近专家动作，但还不足以转化为完整任务成功。

## 复现

```powershell
.\scripts\bootstrap.ps1
.\scripts\run_partial_formal.ps1
.\scripts\bootstrap.ps1 -WithCalvinRollout
.\scripts\run_zero_shot_d_rollout.ps1 -MaxSequences 3 -EpisodeLength 360 -Device cuda
```

## 权重

| 模型 | 文件 | SHA256 |
| --- | --- | --- |
| B-only | [hw3-task2-act-b-only-best.pt](https://github.com/Loong-C/FDU-Computer-Vision/releases/download/hw3-task2-formal-partial-v1/hw3-task2-act-b-only-best.pt) | `58AFAE052EF2CE029F92C9258E1B5012A9C44FAC5753C1C8330B7D196A976131` |
| A+B+C | [hw3-task2-act-abc-joint-best.pt](https://github.com/Loong-C/FDU-Computer-Vision/releases/download/hw3-task2-formal-partial-v1/hw3-task2-act-abc-joint-best.pt) | `1B1F182E61026929F0A5FFDC5EE096D15E4771FEBD111D9EFE3D88BC4A9ADCFF` |
