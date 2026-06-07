# 旧独立仓库迁移核对

旧仓库：
`https://github.com/Loong-C/computer-vision-hw3-task2-calvin-act`

统一仓库：
`https://github.com/Loong-C/FDU-Computer-Vision/tree/main/hw3/task2`

## 已迁移内容

- Task2 源码、配置、测试、训练与评估脚本均位于统一仓库。
- 后续新增的 CALVIN D rollout 和 Release 发布脚本也只维护在统一仓库。
- 两个正式 `best.pt` 和 `SHA256SUMS.txt` 已发布到：
  `https://github.com/Loong-C/FDU-Computer-Vision/releases/tag/hw3-task2-formal-partial-v1`
- Google Drive 文件夹继续作为权重镜像：
  `https://drive.google.com/drive/folders/1v9oc1uTbZS31SaDJaT7sYV8m5dutMo1y?usp=drive_link`
- SwanLab 项目和所有正式运行链接继续有效。

## 校验

| 文件 | 大小 | SHA256 |
| --- | ---: | --- |
| `hw3-task2-act-b-only-best.pt` | 196370804 bytes | `58afae052ef2ce029f92c9258e1b5012a9c44fac5753c1c8330b7d196a976131` |
| `hw3-task2-act-abc-joint-best.pt` | 196370804 bytes | `1b1f182e61026929f0a5ffdc5ee096d15e4771febd111d9efe3d88bc4a9adcff` |

匿名 GitHub API、校验文件下载和两个大文件的 HTTP `200 OK` /
`Content-Length` 已于 2026-06-07 验证。

## 旧仓库独有路径说明

旧仓库树中只剩三个未原样保留的生成文件：

- `docs/HW3_Task2_Report_Draft.pdf`：已由统一最终报告
  `hw3/report/HW3_Report_ChenJialong_24300980041.pdf` 取代。
- `docs/images/formal_training_curves.png`：统一仓库保留可缩放 SVG 版本。
- `docs/images/formal_zero_shot_d_action_error.png`：统一仓库保留可缩放 SVG 版本。

这些文件均不是独有训练资产、源码或模型权重。删除旧仓库不会丢失不可再生资源。
