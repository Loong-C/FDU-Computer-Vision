param(
    [string]$Python = "",
    [string]$DataRoot = "",
    [string]$OutputRoot = "",
    [string]$Config = "configs\calvin_act.yaml"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
if (-not $DataRoot) {
    $DataRoot = Join-Path $RepoRoot "data\calvin"
}
if (-not $Python) {
    $Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
}
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $RepoRoot "outputs\calvin"
}

& "$PSScriptRoot\set_env.ps1" -DataRoot $DataRoot -OutputRoot $OutputRoot
$AbcData = Join-Path $DataRoot "task_ABC_D"
$DData = Join-Path $DataRoot "task_D_D"

function Invoke-Python {
    & $Python @args
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE"
    }
}

Invoke-Python scripts\train.py `
    --config $Config `
    --dataset-root $AbcData `
    --environments B `
    --run-name "act_b_only" `
    --output-root $OutputRoot
Invoke-Python scripts\train.py `
    --config $Config `
    --dataset-root $AbcData `
    --environments ABC `
    --run-name "act_abc_joint" `
    --output-root $OutputRoot
Invoke-Python scripts\evaluate_action_error.py `
    --config $Config `
    --dataset-root $DData `
    --checkpoint (Join-Path $OutputRoot "act_b_only\checkpoints\best.pt") `
    --run-name "act_b_only_to_d" `
    --output-root $OutputRoot
Invoke-Python scripts\evaluate_action_error.py `
    --config $Config `
    --dataset-root $DData `
    --checkpoint (Join-Path $OutputRoot "act_abc_joint\checkpoints\best.pt") `
    --run-name "act_abc_joint_to_d" `
    --output-root $OutputRoot
Invoke-Python scripts\plot_metrics.py `
    --b-run (Join-Path $OutputRoot "act_b_only") `
    --abc-run (Join-Path $OutputRoot "act_abc_joint") `
    --b-eval (Join-Path $OutputRoot "act_b_only_to_d") `
    --abc-eval (Join-Path $OutputRoot "act_abc_joint_to_d") `
    --output-dir (Join-Path $RepoRoot "artifacts\calvin")

Write-Host "CALVIN experiments finished."
