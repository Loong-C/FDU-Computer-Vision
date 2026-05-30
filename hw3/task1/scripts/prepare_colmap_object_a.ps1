$ErrorActionPreference = "Stop"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR

$DATA_PATH = Join-Path $PROJECT_ROOT "data\processed\object_a_colmap"
$IMAGE_PATH = Join-Path $DATA_PATH "input"
$DATABASE_PATH = Join-Path $DATA_PATH "database.db"
$SPARSE_PATH = Join-Path $DATA_PATH "sparse"

Write-Host "Project root: $PROJECT_ROOT"
Write-Host "Image path: $IMAGE_PATH"
Write-Host "Database path: $DATABASE_PATH"
Write-Host "Sparse output path: $SPARSE_PATH"

if (!(Test-Path $IMAGE_PATH)) {
    throw "Image folder does not exist: $IMAGE_PATH"
}

$image_count = (Get-ChildItem $IMAGE_PATH -File | Where-Object {
    $_.Extension -match "\.(jpg|jpeg|png|JPG|JPEG|PNG)$"
}).Count

if ($image_count -eq 0) {
    throw "No images found in: $IMAGE_PATH"
}

Write-Host "Found $image_count images."

if (Test-Path $DATABASE_PATH) {
    Remove-Item $DATABASE_PATH
}

if (Test-Path $SPARSE_PATH) {
    Remove-Item $SPARSE_PATH -Recurse -Force
}

New-Item -ItemType Directory -Path $SPARSE_PATH | Out-Null

Write-Host "Running COLMAP feature extraction..."
colmap feature_extractor `
    --database_path "$DATABASE_PATH" `
    --image_path "$IMAGE_PATH" `
    --ImageReader.single_camera 1

if ($LASTEXITCODE -ne 0) {
    throw "COLMAP feature_extractor failed."
}

Write-Host "Running COLMAP exhaustive matching..."
colmap exhaustive_matcher `
    --database_path "$DATABASE_PATH"

if ($LASTEXITCODE -ne 0) {
    throw "COLMAP exhaustive_matcher failed."
}

Write-Host "Running COLMAP mapper..."
colmap mapper `
    --database_path "$DATABASE_PATH" `
    --image_path "$IMAGE_PATH" `
    --output_path "$SPARSE_PATH"

if ($LASTEXITCODE -ne 0) {
    throw "COLMAP mapper failed."
}

Write-Host "COLMAP reconstruction completed."
Write-Host "Please check whether cameras.bin, images.bin, and points3D.bin exist under sparse\0."