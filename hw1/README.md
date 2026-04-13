# HW1：从零开始构建三层神经网络分类器

本仓库实现复旦大学计算机视觉Homework1，任务是手工实现三层 MLP，并在 Fashion-MNIST 上完成任务
## 仓库链接与模型权重

- GitHub Repo: <https://github.com/Loong-C/FDU-Computer-Vision.git>
- 模型权重下载: <https://drive.google.com/file/d/12k378k0q2_tA5KuZpSIs9tKtFYN-TZNC/view?usp=drive_link>

## 实验结果概览

- 最优验证集准确率: `0.8518`
- 测试集准确率: `0.8422`
- 最优超参数:
  - `hidden_dim=1024`
  - `activation=relu`
  - `lr=0.01`
  - `weight_decay=1e-4`
  - `lr_decay=0.95`
  - `batch_size=512`
- 最终训练轮数: `500`

测试阶段的结果会保存到以下文件：

- `results/test_metrics.txt`
- `results/confusion_matrix.png`

## 环境依赖

- Python `3.10+`
- `numpy`
- `matplotlib`

## 数据集说明

代码默认读取 `data/` 目录下的 Fashion-MNIST 原始 `gz` 文件：

- `train-images-idx3-ubyte.gz`
- `train-labels-idx1-ubyte.gz`
- `t10k-images-idx3-ubyte.gz`
- `t10k-labels-idx1-ubyte.gz`

如果本地不存在，`src/dataloader.py` 会尝试自动下载。

## 项目结构

```text
hw1/
|-- data/                     # Fashion-MNIST 数据
|-- checkpoints/             # 训练得到的模型权重
|-- results/                 # 曲线、混淆矩阵、错例分析等输出
|-- report/                  # 实验报告 LaTeX、PDF 与插图
|-- src/
|   |-- dataloader.py        # 数据加载与预处理
|   |-- layers.py            # 线性层与激活函数
|   |-- loss.py              # Softmax + CrossEntropy
|   |-- model.py             # 三层 MLP
|   |-- optimizer.py         # SGD + Weight Decay + LR Decay
|   |-- utils.py             # 曲线图、权重图、错例分析
|-- search_param.py          # 网格搜索
|-- train.py                 # 单独训练脚本
|-- test.py                  # 测试集评估脚本
|-- main.py                  # 完整 pipeline
|-- HW1_计算机视觉.pdf        # 作业要求
```

## 运行方式

### 1. 直接测试已有最佳模型

如果已经有 `checkpoints/best_model.pkl`，直接运行：

```bash
python test.py
```

输出内容：

- 测试集准确率
- 混淆矩阵
- `results/confusion_matrix.png`
- `results/test_metrics.txt`

### 2. 仅做超参数搜索

```bash
python search_param.py
```

搜索结果会写入：

- `checkpoints/grid_search_results.txt`

### 3. 按默认配置训练模型

```bash
python train.py
```

默认配置：

- `hidden_dim=1024`
- `activation=relu`
- `lr=0.01`
- `weight_decay=1e-4`
- `lr_decay=0.95`
- `epochs=500`
- `batch_size=512`

输出内容：

- `checkpoints/best_model.pkl`
- `results/training_curves.png`

### 4. 完整流程

```bash
python main.py
```

`main.py` 会依次执行：

1. 网格搜索
2. 使用最优配置重新训练
3. 在测试集上评估并输出准确率与混淆矩阵
4. 绘制训练/验证曲线
5. 绘制第一层权重可视化
6. 生成错例分析图

## 当前结果文件

- 训练与验证曲线：`results/curves.png`
- 第一层权重可视化：`results/weights.png`
- 错例分析：`results/errors.png`
- 混淆矩阵：`results/confusion_matrix.png`
- 测试指标文本：`results/test_metrics.txt`
- 网格搜索结果：`results/grid_search_results.txt`

## 实验报告

报告源码与生成文件位于 `report/`：

- LaTeX 源码：`report/report.tex`
- 编译后的 PDF：`report/report.pdf`
