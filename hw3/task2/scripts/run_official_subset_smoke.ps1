param(
    [string]$Python = "",
    [string]$DataRoot = "",
    [string]$OutputRoot = "",
    [int]$WindowsPerEnvironment = 1,
    [int]$WindowSize = 4
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
    $OutputRoot = Join-Path $RepoRoot "outputs\official_subset_smoke"
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
    --config configs\smoke.yaml `
    --dataset-root $AbcData `
    --environments B `
    --run-name "official_b_subset_smoke" `
    --output-root $OutputRoot
Invoke-Python scripts\train.py `
    --config configs\smoke.yaml `
    --dataset-root $AbcData `
    --environments ABC `
    --run-name "official_abc_subset_smoke" `
    --output-root $OutputRoot
Invoke-Python scripts\evaluate_action_error.py `
    --config configs\smoke.yaml `
    --dataset-root $DData `
    --checkpoint (Join-Path $OutputRoot "official_b_subset_smoke\checkpoints\best.pt") `
    --run-name "official_b_to_d_subset_smoke" `
    --output-root $OutputRoot
Invoke-Python scripts\evaluate_action_error.py `
    --config configs\smoke.yaml `
    --dataset-root $DData `
    --checkpoint (Join-Path $OutputRoot "official_abc_subset_smoke\checkpoints\best.pt") `
    --run-name "official_abc_to_d_subset_smoke" `
    --output-root $OutputRoot
Invoke-Python scripts\plot_metrics.py `
    --b-run (Join-Path $OutputRoot "official_b_subset_smoke") `
    --abc-run (Join-Path $OutputRoot "official_abc_subset_smoke") `
    --b-eval (Join-Path $OutputRoot "official_b_to_d_subset_smoke") `
    --abc-eval (Join-Path $OutputRoot "official_abc_to_d_subset_smoke") `
    --output-dir (Join-Path $RepoRoot "artifacts\official-subset-smoke")

Write-Host "Official CALVIN subset smoke workflow finished."
