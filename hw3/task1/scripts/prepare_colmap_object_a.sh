$ErrorActionPreference = "Stop"

$COLMAP = "D:\Program Files\COLMAP\bin\colmap.exe"

if (!(Test-Path $COLMAP)) {
    Write-Host "COLMAP executable not found at: $COLMAP"
    Write-Host "Please update the COLMAP path in this script."
    exit 1
}

$DATA_PATH = "data/processed/object_a_colmap"
$IMAGE_PATH = "$DATA_PATH/input"
$DATABASE_PATH = "$DATA_PATH/database.db"
$SPARSE_PATH = "$DATA_PATH/sparse"

if (!(Test-Path $SPARSE_PATH)) {
    New-Item -ItemType Directory -Path $SPARSE_PATH | Out-Null
}

Write-Host "Running COLMAP feature extraction..."
& $COLMAP feature_extractor `
    --database_path $DATABASE_PATH `
    --image_path $IMAGE_PATH `
    --ImageReader.single_camera 1 `
    --SiftExtraction.use_gpu 1

Write-Host "Running COLMAP exhaustive matching..."
& $COLMAP exhaustive_matcher `
    --database_path $DATABASE_PATH `
    --SiftMatching.use_gpu 1

Write-Host "Running COLMAP mapper..."
& $COLMAP mapper `
    --database_path $DATABASE_PATH `
    --image_path $IMAGE_PATH `
    --output_path $SPARSE_PATH

Write-Host "COLMAP reconstruction completed."