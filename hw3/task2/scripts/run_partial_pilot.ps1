param(
    [string]$Python = "",
    [string]$DataRoot = "",
    [string]$OutputRoot = "",
    [int]$WindowsPerEnvironment = 4,
    [int]$WindowSize = 24,
    [int]$Steps = 20
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
if (-not $DataRoot) {
    $DataRoot = Join-Path $RepoRoot "data\calvin-subset"
}
if (-not $Python) {
    $Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
}
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $RepoRoot "outputs\official_subset_pilot"
}

& "$PSScriptRoot\set_env.ps1" -DataRoot $DataRoot -OutputRoot $OutputRoot
$IndexRoot = Join-Path $env:HF_HOME "calvin-remote-index"
$AbcData = Join-Path $DataRoot "task_ABC_D"
$DData = Join-Path $DataRoot "task_D_D"

function Invoke-Python {
    & $Python @args
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE"
    }
}

Invoke-Python scripts\download_calvin_subset.py `
    --archive ALL `
    --output-root $DataRoot `
    --cache-root $IndexRoot `
    --windows-per-env $WindowsPerEnvironment `
    --window-size $WindowSize `
    --workers 2
Invoke-Python scripts\train.py `
    --config configs\calvin_act.yaml `
    --dataset-root $AbcData `
    --environments B `
    --run-name "act_b_only_pilot" `
    --output-root $OutputRoot `
    --max-steps $Steps
Invoke-Python scripts\train.py `
    --config configs\calvin_act.yaml `
    --dataset-root $AbcData `
    --environments ABC `
    --run-name "act_abc_joint_pilot" `
    --output-root $OutputRoot `
    --max-steps $Steps
Invoke-Python scripts\evaluate_action_error.py `
    --config configs\calvin_act.yaml `
    --dataset-root $DData `
    --checkpoint (Join-Path $OutputRoot "act_b_only_pilot\checkpoints\best.pt") `
    --run-name "act_b_only_to_d_pilot" `
    --output-root $OutputRoot
Invoke-Python scripts\evaluate_action_error.py `
    --config configs\calvin_act.yaml `
    --dataset-root $DData `
    --checkpoint (Join-Path $OutputRoot "act_abc_joint_pilot\checkpoints\best.pt") `
    --run-name "act_abc_joint_to_d_pilot" `
    --output-root $OutputRoot
Invoke-Python scripts\plot_metrics.py `
    --b-run (Join-Path $OutputRoot "act_b_only_pilot") `
    --abc-run (Join-Path $OutputRoot "act_abc_joint_pilot") `
    --b-eval (Join-Path $OutputRoot "act_b_only_to_d_pilot") `
    --abc-eval (Join-Path $OutputRoot "act_abc_joint_to_d_pilot") `
    --output-dir (Join-Path $RepoRoot "artifacts\official-subset-pilot")

Write-Host "Official CALVIN partial-data pilot finished."
