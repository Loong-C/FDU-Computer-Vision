# 数据目录

`data/` 只保存本机数据，不提交到 Git。

## 推荐结构

```text
data/
  raw/
    object_a_images/          物体 A 手机多视角照片
    object_c_image/           物体 C 单张输入图
    mipnerf360/counter/       背景场景原始数据
  processed/
    object_a_2dgs_ready/      COLMAP 与 2DGS 处理后的物体 A 数据
    background_counter/       背景场景链接或处理结果
    object_c_image/c_rgba.png 去背景后的物体 C 输入
```

## 常用命令

物体 A：

```bash
bash scripts/prepare_colmap_object_a.sh --force
```

物体 C：

```bash
python scripts/prepare_object_c_image.py --swanlab-mode local
bash scripts/download_magic123_models.sh
bash scripts/prepare_magic123_object_c.sh
```

背景：

```bash
bash scripts/download_background_counter.sh
```

下载和中间结果会被缓存，重复运行时会尽量复用已有文件。
