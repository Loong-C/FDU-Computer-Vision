param(
    [string]$Python = "",
    [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
if (-not $Python) {
    $Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
}
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $RepoRoot "outputs\smoke"
}

$env:SWANLAB_MODE = "offline"
$env:SWANLAB_LOG_DIR = Join-Path $RepoRoot "swanlog"
$SmokeData = Join-Path $RepoRoot "data\smoke"

function Invoke-Python {
    & $Python @args
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE"
    }
}

Invoke-Python scripts\generate_smoke_data.py --output-root $SmokeData
Invoke-Python scripts\train.py `
    --config configs\smoke.yaml `
    --dataset-root (Join-Path $SmokeData "task_ABC_D") `
    --environments B `
    --run-name "act_b_smoke" `
    --output-root $OutputRoot
Invoke-Python scripts\train.py `
    --config configs\smoke.yaml `
    --dataset-root (Join-Path $SmokeData "task_ABC_D") `
    --environments ABC `
    --run-name "act_abc_smoke" `
    --output-root $OutputRoot
Invoke-Python scripts\evaluate_action_error.py `
    --config configs\smoke.yaml `
    --dataset-root (Join-Path $SmokeData "task_D_D") `
    --checkpoint (Join-Path $OutputRoot "act_b_smoke\checkpoints\best.pt") `
    --run-name "act_b_to_d_smoke" `
    --output-root $OutputRoot
Invoke-Python scripts\evaluate_action_error.py `
    --config configs\smoke.yaml `
    --dataset-root (Join-Path $SmokeData "task_D_D") `
    --checkpoint (Join-Path $OutputRoot "act_abc_smoke\checkpoints\best.pt") `
    --run-name "act_abc_to_d_smoke" `
    --output-root $OutputRoot
Invoke-Python scripts\plot_metrics.py `
    --b-run (Join-Path $OutputRoot "act_b_smoke") `
    --abc-run (Join-Path $OutputRoot "act_abc_smoke") `
    --b-eval (Join-Path $OutputRoot "act_b_to_d_smoke") `
    --abc-eval (Join-Path $OutputRoot "act_abc_to_d_smoke") `
    --output-dir (Join-Path $RepoRoot "artifacts\smoke")

Write-Host "Smoke workflow finished."
