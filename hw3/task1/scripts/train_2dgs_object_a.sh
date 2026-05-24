#!/usr/bin/env bash
set -e

# Train 2DGS for Object A.
# This script should be run inside external/2d-gaussian-splatting.

DATA_PATH="../../data/processed/object_a_colmap"
OUTPUT_PATH="../../outputs/object_a_2dgs"

python train.py \
  -s "${DATA_PATH}" \
  -m "${OUTPUT_PATH}"