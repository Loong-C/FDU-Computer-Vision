#!/usr/bin/env bash
set -e

# Train 2DGS for the background scene.
# This script should be run inside external/2d-gaussian-splatting.

DATA_PATH="../../data/processed/background_colmap"
OUTPUT_PATH="../../outputs/background_2dgs"

python train.py \
  -s "${DATA_PATH}" \
  -m "${OUTPUT_PATH}"