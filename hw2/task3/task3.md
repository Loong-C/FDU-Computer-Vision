# 任务 3：从零搭建与损失函数工程：图像分割模型的像素级训练

## 一、任务目标

本任务的目标是从零搭建一个用于语义分割的 U-Net 模型，并在 Oxford-IIIT Pet Dataset 的三分类分割任务上进行像素级训练。与直接调用预训练模型不同，本实验要求不使用任何预训练权重，而是使用 PyTorch 的基础 API 手写完成 U-Net 的完整结构，包括下采样编码器、上采样解码器以及编码器与解码器之间的 Skip Connection 特征拼接逻辑。

同时，本任务还要求围绕语义分割中的损失函数进行对比实验。由于图像分割任务常常存在明显的类别像素数量不均衡，例如背景像素远多于边界像素，因此仅依赖普通的逐像素交叉熵损失可能无法充分优化小区域或边界区域。为此，本实验手动实现了多分类 Dice Loss，并分别使用 Cross-Entropy Loss、Dice Loss、Cross-Entropy Loss + Dice Loss 三种损失配置训练 U-Net，最后使用验证集 mIoU 作为主要指标进行比较。

## 二、实验环境与工程结构

本实验使用 PyTorch 作为深度学习框架，主要依赖包括 torch、torchvision、numpy、Pillow、PyYAML、tqdm、matplotlib 和 scikit-learn。为了便于管理三组实验，项目采用了配置文件驱动的工程结构。不同损失函数对应不同的 yaml 配置文件，训练代码通过读取配置文件决定实验名称、数据路径、模型参数、训练轮数、学习率和损失类型。

项目主要结构如下：

```text
task3/
│  main.py
│  train.py
│  predict.py
│  plot_results.py
│  evaluate.py
│  requirements.txt
│  README.md
│
├─configs
│      unet_ce.yaml
│      unet_dice.yaml
│      unet_ce_dice.yaml
│
├─datasets
│      oxford_pet.py
│
├─losses
│      dice_loss.py
│
├─models
│      unet.py
│
├─utils
│      logger.py
│      metrics.py
│      seed.py
│      visualization.py
│
├─runs
└─results
```

其中，`models/unet.py` 负责 U-Net 网络结构，`datasets/oxford_pet.py` 负责 Oxford-IIIT Pet 分割数据集读取和 mask 预处理，`losses/dice_loss.py` 负责手动实现 Dice Loss 和组合损失，`utils/metrics.py` 负责 Pixel Accuracy、class IoU 和 mIoU 的计算，`train.py` 负责完整训练流程，`plot_results.py` 和 `predict.py` 用于生成实验曲线和预测可视化结果。

## 三、数据集处理

本实验使用 Oxford-IIIT Pet Dataset 的 segmentation trimap 标注。该数据集中的分割 mask 原始像素值通常为 1、2、3，分别对应宠物主体、背景和边界区域。为了适配 PyTorch 中的 `nn.CrossEntropyLoss()`，实验中将原始标签转换为从 0 开始的类别编号，即将原始 mask 减 1，使其变为 0、1、2 三类。

模型输入图像被统一调整为 256 × 256，并转换为 `[3, 256, 256]` 的 float tensor。mask 被同步调整为 256 × 256，并转换为 `[256, 256]` 的 long tensor。图像 resize 使用双线性插值，而 mask resize 必须使用最近邻插值，这是因为分割 mask 中的像素值代表离散类别，如果使用双线性插值，会产生非整数类别值，从而破坏标签。

在正式训练前，对数据加载模块进行了检查。一个 batch 的输出如下：

```text
images shape: torch.Size([8, 3, 256, 256])
masks shape: torch.Size([8, 256, 256])
image dtype: torch.float32
mask dtype: torch.int64
mask min: 0
mask max: 2
```

这说明图像尺寸、mask 尺寸、数据类型和类别范围均符合语义分割训练要求。

## 四、U-Net 网络结构设计

本实验没有使用任何预训练权重，而是使用 PyTorch 基础 API 从零搭建了一个经典 U-Net。网络整体由编码器、解码器和输出层组成。编码器负责逐步下采样并提取高层语义特征，解码器负责逐步上采样恢复空间分辨率，Skip Connection 则用于将编码器中的浅层空间细节特征传递给解码器，从而改善分割边界和局部细节。

网络的基本卷积模块为 DoubleConv，即连续两次执行 `Conv2d -> BatchNorm2d -> ReLU`。下采样模块由 `MaxPool2d` 和 DoubleConv 组成。上采样模块使用 `ConvTranspose2d` 将特征图放大，然后与对应编码器层的特征图在 channel 维度上进行拼接，最后再通过 DoubleConv 融合特征。最终通过 1 × 1 卷积将特征通道映射为三分类 logits。

模型前向传播的核心逻辑如下：

```python
x1 = self.in_conv(x)
x2 = self.down1(x1)
x3 = self.down2(x2)
x4 = self.down3(x3)
x5 = self.down4(x4)

x = self.up1(x5, x4)
x = self.up2(x, x3)
x = self.up3(x, x2)
x = self.up4(x, x1)

logits = self.out_conv(x)
```

其中，`up1` 到 `up4` 中都包含 Skip Connection 的特征拼接逻辑：

```python
x = torch.cat([skip, x], dim=1)
```

这正是 U-Net 区别于普通编码器-解码器结构的重要部分。编码器深层特征具有较强的语义表达能力，但空间细节较弱；浅层特征保留了更多边缘、轮廓和位置信息。通过 Skip Connection，解码器可以同时利用语义信息和局部细节，从而更适合像素级分割任务。

在模型测试中，输入 `[2, 3, 256, 256]` 的随机 tensor 后，输出为 `[2, 3, 256, 256]`，说明模型能够保持输入输出空间分辨率一致，并为每个像素输出三类 logits。

## 五、Dice Loss 的手动实现

语义分割任务中，不同类别的像素数量往往不均衡。在 Oxford-IIIT Pet 的 trimap 分割中，背景和宠物主体通常占据大面积，而边界区域较细、像素数量较少。Cross-Entropy Loss 是逐像素分类损失，虽然训练稳定，但对类别不平衡问题并不总是敏感。因此，本实验手动实现了多分类 Dice Loss。

Dice 系数本质上衡量预测区域与真实区域的重叠程度。对于某一类别，Dice 系数可表示为：

$$
Dice = \frac{2|P \cap G|}{|P| + |G|}
$$

其中，$P$ 表示模型预测区域，$G$ 表示真实标注区域。Dice Loss 则定义为：

$$
DiceLoss = 1 - Dice
$$

在多分类场景中，模型输出 logits 的形状为 `[B, C, H, W]`，其中 C 为类别数。实现时先对 logits 在类别维度上执行 softmax，得到每个像素属于各类别的概率；再将标签 `[B, H, W]` 转换为 one-hot 形式，并调整为 `[B, C, H, W]`。然后分别计算各类别的 Dice 系数，最后对类别取平均，得到最终 Dice Loss。

核心实现逻辑如下：

```python
probs = torch.softmax(logits, dim=1)

targets_one_hot = F.one_hot(
    targets,
    num_classes=self.num_classes,
)

targets_one_hot = targets_one_hot.permute(0, 3, 1, 2).float()

intersection = torch.sum(probs * targets_one_hot, dim=(0, 2, 3))
cardinality = torch.sum(probs + targets_one_hot, dim=(0, 2, 3))

dice_score = (2.0 * intersection + smooth) / (cardinality + smooth)
dice_loss = 1.0 - dice_score.mean()
```

此外，本实验还实现了组合损失：

```python
loss = CrossEntropyLoss + DiceLoss
```

该组合损失一方面保留交叉熵损失稳定的逐像素监督，另一方面利用 Dice Loss 强化区域重叠优化，因此理论上更适合存在像素不均衡的分割任务。

## 六、训练设置

三组实验使用相同的数据划分、模型结构和训练超参数，只改变损失函数配置，从而保证比较结果尽可能公平。实验统一使用随机初始化的 U-Net，不加载任何预训练权重。

主要训练设置如下：

```text
Dataset: Oxford-IIIT Pet Dataset
Task: 三分类语义分割
Input size: 256 × 256
Number of classes: 3
Model: U-Net
Base channels: 64
Batch size: 8
Optimizer: AdamW
Learning rate: 0.0001
Weight decay: 0.0001
Epochs: 50
Validation ratio: 0.2
Random seed: 42
```

三种损失函数配置分别为：

```text
1. Cross-Entropy Loss
2. Dice Loss
3. Cross-Entropy Loss + Dice Loss
```

训练过程中，每个 epoch 记录 train loss、validation loss、validation pixel accuracy、validation mIoU 和每类 IoU。每组实验根据验证集 mIoU 保存最优模型 `best_model.pth`，并保存最后一轮模型 `last_model.pth`。同时，每个实验目录保存 `config.json`、`history.json` 和 `summary.json`，便于后续复现实验和生成报告。

## 七、评价指标

本实验的主要评价指标为 mIoU，即 mean Intersection over Union。对于每一类，IoU 定义为预测区域和真实区域的交集除以并集：

$$
IoU = \frac{TP}{TP + FP + FN}
$$

其中，TP 表示该类别被正确预测的像素数，FP 表示其他类别被错误预测为该类别的像素数，FN 表示该类别被错误预测为其他类别的像素数。mIoU 则是所有有效类别 IoU 的平均值。

除了 mIoU，本实验还记录 Pixel Accuracy。Pixel Accuracy 表示所有像素中预测正确的比例。它直观易懂，但在类别不均衡情况下可能偏乐观。例如背景像素较多时，即使模型主要预测背景，也可能取得较高像素准确率。因此，本实验以 mIoU 作为核心比较指标。

## 八、实验结果

三组损失函数配置的实验结果如下：

| Loss Config | Best Val mIoU | Best Epoch | Final Val mIoU | Final Pixel Acc |
|---|---:|---:|---:|---:|
| CE | 0.763213 | 48 | 0.738991 | 0.900209 |
| Dice | 0.767711 | 47 | 0.760501 | 0.909191 |
| CE + Dice | 0.770272 | 39 | 0.762963 | 0.912962 |

从 Best Val mIoU 看，组合损失 CE + Dice 取得了最高结果，达到 0.770272；单独 Dice Loss 的结果为 0.767711；单独 Cross-Entropy Loss 的结果为 0.763213。三组结果差距不算特别大，但整体趋势比较清晰：加入 Dice Loss 后，验证集 mIoU 有一定提升；将 Cross-Entropy Loss 与 Dice Loss 组合后，取得了三组实验中的最佳 mIoU。

从最佳 epoch 来看，CE + Dice 在第 39 个 epoch 达到最佳结果，而 CE 和 Dice 分别在第 48 和第 47 个 epoch 达到最佳结果。这说明组合损失不仅最终 mIoU 更高，而且在本次实验中较早达到了最佳验证表现。一个合理解释是，Cross-Entropy Loss 提供了稳定的像素级分类梯度，Dice Loss 则推动模型优化整体区域重叠，两者互补后使模型更快学习到较好的分割表示。

从 Final Pixel Accuracy 看，CE + Dice 也最高，为 0.912962；Dice Loss 为 0.909191；CE 为 0.900209。这与 mIoU 的趋势一致，说明组合损失不仅提升了区域重叠指标，也提升了整体像素分类正确率。

## 九、类别 IoU 分析

以 CE + Dice 最后一轮的类别 IoU 为例，三类结果如下：

```text
Class IoU:
0.840958
0.911047
0.536885
```

可以看出，模型对大面积区域的分割效果较好，尤其是背景类和宠物主体类的 IoU 较高；而边界类 IoU 明显较低。这一现象符合任务特点。Oxford-IIIT Pet 的 trimap 标签中，边界区域通常是一圈较窄的像素带，面积远小于宠物主体和背景。同时，边界形状细碎、不规则，受图像 resize、标注精度和模型上采样误差影响较大，因此比主体和背景更难学习。

从可视化结果也能看到类似现象。模型通常能够大致识别宠物主体和背景区域，但在边界、腿部、阴影附近或形状细长区域容易出现误分割。特别是在宠物轮廓和背景相似、阴影干扰较强的图像中，预测 mask 可能出现边界过宽、局部断裂或细节不准确的问题。

## 十、预测可视化分析

下图展示了模型在验证集样本上的一次预测结果。左侧为原图，中间为真实 mask，右侧为模型预测 mask。三种颜色分别表示宠物主体、背景和边界区域。

```markdown
![Prediction Example](results/predictions/prediction_5.png)
```

从该样本可以观察到，模型基本能够将宠物主体从背景中分离出来，并且可以生成较完整的主体区域。然而，预测结果中也存在一些问题。首先，宠物头部和身体之间的细节区域出现了局部误分类，说明模型对复杂轮廓和细小结构的处理仍然不够稳定。其次，边界区域相较真实标注存在一定扩张和偏移，这与边界类像素数量少、形状复杂有关。最后，图像中存在较明显的阴影，模型容易将某些阴影或外形相近区域误判为宠物相关区域，这说明模型在复杂背景下仍有改进空间。

总体而言，可视化结果与数值指标是一致的。模型对主体和背景的分割已经较稳定，但边界类别仍是主要瓶颈。由于本实验要求从随机初始化开始训练，且没有使用预训练编码器，当前结果说明手写 U-Net 已经能够在轻量级分割数据集上有效收敛。

## 十一、损失函数对比分析

Cross-Entropy Loss 是语义分割中最常见的基础损失函数。它把每个像素看作一个独立的分类样本，并对每个像素计算分类误差。它的优点是优化稳定、实现简单、梯度明确；缺点是在像素类别分布不均衡时，模型可能更倾向于优化大面积类别，例如背景和主体，而对边界这类少数像素类别关注不足。本实验中，CE 的 Best Val mIoU 为 0.763213，是三组中最低的，但仍然达到了可用水平，说明 U-Net 本身已经具备较强的分割能力。

Dice Loss 更关注预测区域与真实区域之间的重叠比例，因此对类别区域的整体形状更敏感。相比交叉熵，它不只是逐像素地惩罚分类错误，而是从区域层面衡量预测与标签的一致性。本实验中，Dice Loss 的 Best Val mIoU 为 0.767711，高于 CE，说明在该三分类分割任务中，区域重叠优化确实带来了收益。不过，Dice Loss 的训练可能会比 CE 更不稳定，尤其是在训练初期，当预测概率还比较随机时，Dice 的梯度可能不如交叉熵直接。

CE + Dice 组合损失取得了最高 Best Val mIoU，达到 0.770272。它的优势在于同时结合了两种损失的特点：CE 负责稳定的像素级分类学习，Dice 负责优化整体区域重叠，并在一定程度上缓解类别不平衡问题。从实验结果看，组合损失不仅 mIoU 最高，而且最佳 epoch 更早，说明它在本任务中具有更好的综合表现。

## 十二、实验总结

本实验完成了从零搭建 U-Net 并进行语义分割训练的完整流程。网络结构上，实验没有使用任何预训练权重，而是手写实现了 DoubleConv、Down、Up 和 OutConv 等模块，构建了完整的编码器、解码器和 Skip Connection。数据处理上，实验使用 Oxford-IIIT Pet Dataset 的三分类 segmentation mask，将原始标签映射为 0、1、2 三类，并保证图像和 mask 采用正确的插值方式进行 resize。损失函数上，实验手动实现了多分类 Dice Loss，并与 Cross-Entropy Loss 进行对比和组合。

三组实验结果表明，单独使用 Cross-Entropy Loss 可以获得较好的基础分割效果，Best Val mIoU 为 0.763213；单独使用 Dice Loss 后，Best Val mIoU 提升到 0.767711；使用 CE + Dice 组合损失后，Best Val mIoU 进一步提升到 0.770272，是三组实验中的最佳结果。因此，本实验验证了 Dice Loss 在像素不均衡分割任务中的有效性，也说明组合损失能够更好地兼顾像素级分类准确性和区域重叠质量。

不过，实验仍存在一些可以改进的方向。首先，边界类别的 IoU 明显低于主体和背景，说明模型对细粒度轮廓的学习仍不充分。后续可以尝试类别加权损失、边界感知损失或更强的数据增强方法。其次，本实验使用的是标准 U-Net，后续可以尝试 Attention U-Net、UNet++ 或轻量化残差结构来提升细节表达能力。最后，由于本任务限制不能使用预训练权重，模型需要较长训练时间才能达到较好效果；如果在实际应用中允许使用预训练编码器，分割性能和收敛速度可能进一步提升。

总体来看，本实验较完整地实现了从数据集处理、模型搭建、损失函数工程、训练验证、指标评估到结果可视化的语义分割流程，满足任务中关于从零搭建 U-Net、使用轻量级三分类分割数据集训练、手动实现 Dice Loss 并比较三种损失配置 mIoU 表现的要求。
