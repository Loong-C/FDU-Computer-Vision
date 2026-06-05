param(
    [string]$DataRoot = "",
    [string]$CacheRoot = "",
    [string]$OutputRoot = "",
    [ValidateSet("offline", "cloud", "local", "disabled")]
    [string]$SwanLabMode = "offline"
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $DataRoot) {
    $DataRoot = Join-Path $RepoRoot "data\calvin"
}
if (-not $CacheRoot) {
    $CacheRoot = Join-Path $RepoRoot ".cache\hf"
}
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $RepoRoot "outputs"
}

$env:HW3_TASK2_DATA_ROOT = $DataRoot
$env:HW3_TASK2_OUTPUT_ROOT = $OutputRoot
$env:HF_HOME = $CacheRoot
$env:HF_LEROBOT_HOME = Join-Path $CacheRoot "lerobot"
$env:PIP_CACHE_DIR = Join-Path $CacheRoot "pip"
$env:TEMP = Join-Path $CacheRoot "tmp"
$env:TMP = $env:TEMP
$env:SWANLAB_LOG_DIR = Join-Path $RepoRoot "swanlog"
$env:SWANLAB_MODE = $SwanLabMode
$env:SWANLAB_PROJECT = "hw3-calvin-act"

New-Item -ItemType Directory -Force $env:HW3_TASK2_DATA_ROOT | Out-Null
New-Item -ItemType Directory -Force $env:HW3_TASK2_OUTPUT_ROOT | Out-Null
New-Item -ItemType Directory -Force $env:HF_HOME | Out-Null
New-Item -ItemType Directory -Force $env:HF_LEROBOT_HOME | Out-Null
New-Item -ItemType Directory -Force $env:PIP_CACHE_DIR | Out-Null
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
New-Item -ItemType Directory -Force $env:SWANLAB_LOG_DIR | Out-Null

Write-Host "HW3_TASK2_DATA_ROOT=$env:HW3_TASK2_DATA_ROOT"
Write-Host "HW3_TASK2_OUTPUT_ROOT=$env:HW3_TASK2_OUTPUT_ROOT"
Write-Host "HF_HOME=$env:HF_HOME"
Write-Host "TEMP=$env:TEMP"
Write-Host "SWANLAB_MODE=$env:SWANLAB_MODE"
