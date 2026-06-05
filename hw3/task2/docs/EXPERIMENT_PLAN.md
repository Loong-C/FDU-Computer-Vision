# 实验计划

## 对比设置

| 实验 | 训练环境 | 测试环境 |
| --- | --- | --- |
| `act_b_only` | B | D |
| `act_abc_joint` | A+B+C | D |

两组实验使用同一个 `configs/calvin_act.yaml`。除训练环境外，网络结构、优化器、步数和评估脚本完全一致。

## 资源约束流程

1. 运行 `scripts/run_smoke.ps1` 检查完整链路。
2. 用 `scripts/download_calvin_subset.py` 下载官方 CALVIN 抽样帧。
3. 先用短训练确认显存和速度。
4. 正式实验保持 `image_size: 128`、`batch_size: 4`、`max_steps: 5000`。
5. 权重和大数据只放在本地或网盘，不提交到 Git。

## 指标

- `train/l1_loss`：ACT 动作重建 L1。
- `train/kld_loss`：VAE 正则项。
- `validation/loss`：训练场景内验证损失。
- `zero_shot/first_action_mae`：D 环境第一步动作误差。
- `zero_shot/chunk_action_mae`：D 环境动作块误差。
- `rollout/SR@k`：D simulator 五任务序列成功率。

## 解释重点

- A+B+C 是否降低 D 环境动作误差。
- 多视觉环境是否让训练更难但泛化更好。
- chunk 误差是否比 first-action 更容易受分布偏移影响。
- simulator 成功率与离线 MAE 是否一致，以及差异来自哪里。
