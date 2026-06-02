param(
    [string]$DataRoot = "",
    [string]$CacheRoot = "",
    [switch]$FreshTorchEnvironment
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Invoke-Checked {
    param([string]$Command, [string[]]$Arguments)
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Command failed with exit code $LASTEXITCODE"
    }
}

& "$PSScriptRoot\set_env.ps1" -DataRoot $DataRoot -CacheRoot $CacheRoot

if (-not (Test-Path "external\lerobot")) {
    New-Item -ItemType Directory -Force "external" | Out-Null
    git clone --depth 1 --branch v0.5.1 https://github.com/huggingface/lerobot.git "external\lerobot"
}
if (-not (Test-Path "external\calvin")) {
    New-Item -ItemType Directory -Force "external" | Out-Null
    git clone --depth 1 https://github.com/mees/calvin.git "external\calvin"
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    if ($FreshTorchEnvironment) {
        python -m venv .venv
    } else {
        python -m venv --system-site-packages .venv
    }
}

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
Invoke-Checked -Command $Python -Arguments @("-m", "pip", "install", "--upgrade", "pip")
Invoke-Checked -Command $Python -Arguments @("-m", "pip", "install", "-e", ".", "--no-deps")
$RuntimePackages = @(
    "draccus==0.10.0",
    "einops>=0.8,<0.9",
    "huggingface-hub>=1.0,<2.0",
    "accelerate>=1.10,<2.0",
    "diffusers>=0.27.2,<0.36",
    "datasets>=4.0,<5.0",
    "av>=15,<16",
    "jsonlines>=4,<5",
    "opencv-python-headless>=4.9,<4.14",
    "wandb>=0.24,<0.25",
    "scikit-learn>=1.7,<2.0",
    "deepdiff>=7,<9",
    "gymnasium>=1.1,<2",
    "pynput>=1.7.8,<1.9",
    "pyserial>=3.5,<4",
    "rerun-sdk>=0.24,<0.27",
    "cmake>=3.29,<4.2",
    "packaging>=24.2,<26",
    "imageio[ffmpeg]>=2.34,<3"
)
Invoke-Checked -Command $Python -Arguments (@("-m", "pip", "install") + $RuntimePackages)
Invoke-Checked -Command $Python -Arguments @("-m", "pip", "install", "-e", "external\lerobot", "--no-deps")

Write-Host "Bootstrap complete. Activate with: .\.venv\Scripts\Activate.ps1"
Write-Host "For cloud SwanLab logging, run: swanlab login"
