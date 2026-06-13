param(
    [string]$Python = "",
    [string]$DataRoot = "",
    [string]$OutputRoot = "",
    [int]$WindowsPerEnvironment = 16,
    [int]$WindowSize = 48,
    [int]$Steps = 5000,
    [ValidateSet("offline", "cloud", "disabled")]
    [string]$SwanLabMode = "offline",
    [switch]$SkipDownload
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
    $OutputRoot = Join-Path $RepoRoot "outputs\official_subset_formal"
}

& "$PSScriptRoot\set_env.ps1" -DataRoot $DataRoot -OutputRoot $OutputRoot
$env:SWANLAB_MODE = $SwanLabMode
$IndexRoot = Join-Path $env:HF_HOME "calvin-remote-index"
$AbcData = Join-Path $DataRoot "task_ABC_D"
$DData = Join-Path $DataRoot "task_D_D"

function Invoke-Python {
    & $Python @args
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE"
    }
}

function Invoke-ResumableTrain {
    param(
        [string]$Environments,
        [string]$RunName
    )

    $RunDir = Join-Path $OutputRoot $RunName
    $SplitManifest = Join-Path $RunDir "split_manifest.json"
    $TrainArgs = @(
        "scripts\train.py",
        "--config", "configs\calvin_act.yaml",
        "--dataset-root", $AbcData,
        "--environments", $Environments,
        "--run-name", $RunName,
        "--output-root", $OutputRoot,
        "--max-steps", $Steps
    )
    $LatestCheckpoint = Join-Path $OutputRoot "$RunName\checkpoints\latest.pt"
    if ((Test-Path $LatestCheckpoint) -and (Test-Path $SplitManifest)) {
        Write-Host "Resuming $RunName from $LatestCheckpoint"
        $TrainArgs += @("--resume", $LatestCheckpoint)
    } elseif (Test-Path $RunDir) {
        $ArchiveName = "$RunName-frame-split-archived-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        $ArchivePath = Join-Path $OutputRoot $ArchiveName
        Write-Host "Archiving incompatible prior run to $ArchivePath"
        Move-Item -LiteralPath $RunDir -Destination $ArchivePath
    }
    Invoke-Python @TrainArgs
}

if (-not $SkipDownload) {
    Invoke-Python scripts\download_calvin_subset.py `
        --archive ALL `
        --output-root $DataRoot `
        --cache-root $IndexRoot `
        --windows-per-env $WindowsPerEnvironment `
        --window-size $WindowSize `
        --workers 2
}

Invoke-ResumableTrain -Environments "B" -RunName "act_b_only_partial_formal"
Invoke-ResumableTrain -Environments "ABC" -RunName "act_abc_joint_partial_formal"
Invoke-Python scripts\evaluate_action_error.py `
    --config configs\calvin_act.yaml `
    --dataset-root $DData `
    --checkpoint (Join-Path $OutputRoot "act_b_only_partial_formal\checkpoints\best.pt") `
    --run-name "act_b_only_to_d_partial_formal" `
    --output-root $OutputRoot
Invoke-Python scripts\evaluate_action_error.py `
    --config configs\calvin_act.yaml `
    --dataset-root $DData `
    --checkpoint (Join-Path $OutputRoot "act_abc_joint_partial_formal\checkpoints\best.pt") `
    --run-name "act_abc_joint_to_d_partial_formal" `
    --output-root $OutputRoot
Invoke-Python scripts\plot_metrics.py `
    --b-run (Join-Path $OutputRoot "act_b_only_partial_formal") `
    --abc-run (Join-Path $OutputRoot "act_abc_joint_partial_formal") `
    --b-eval (Join-Path $OutputRoot "act_b_only_to_d_partial_formal") `
    --abc-eval (Join-Path $OutputRoot "act_abc_joint_to_d_partial_formal") `
    --output-dir (Join-Path $RepoRoot "artifacts\official-subset-formal")

Write-Host "Official CALVIN partial-data formal experiment finished."
