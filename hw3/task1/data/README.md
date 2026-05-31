# Data Layout

Large datasets are intentionally excluded from Git. Keep the following layout:

```text
data/
  raw/
    object_a_images/              phone-captured multi-view photos
    object_c_image/               one foreground-only phone photo
    mipnerf360/                   downloaded open-source scenes
  processed/
    object_a_2dgs_ready/          undistorted COLMAP dataset for Object A
    background_counter/           selected Mip-NeRF 360 background scene
```

For Object A, place the captured photos in `data/raw/object_a_images/`, then run:

```bash
bash scripts/prepare_colmap_object_a.sh --force
```

The script copies the input images to `data/processed/object_a_2dgs_ready/input/`
and invokes the official 2DGS `convert.py` pipeline to run COLMAP and undistort
the images into the ideal pinhole camera format expected by 2DGS.

For Object C, add a photo of a different real object to
`data/raw/object_c_image/`. The current input contains a baked RGB checkerboard,
so prepare an RGBA image before running Magic123:

```bash
python scripts/prepare_object_c_image.py --swanlab-mode local
```

For the background, download the official Mip-NeRF 360 `360_v2.zip` archive,
extract only `counter`, and create the processed-data link:

```bash
bash scripts/download_background_counter.sh
```

The script uses `curl --continue-at -`, so interrupted downloads resume.
