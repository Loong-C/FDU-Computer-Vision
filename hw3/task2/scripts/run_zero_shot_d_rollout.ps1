param(
    [string]$DataRoot = ".\data\calvin-subset",
    [string]$OutputRoot = ".\outputs\official_subset_formal",
    [string]$BCheckpoint = ".\outputs\official_subset_formal\act_b_only_partial_formal\checkpoints\best.pt",
    [string]$ABCCheckpoint = ".\outputs\official_subset_formal\act_abc_joint_partial_formal\checkpoints\best.pt",
    [int]$MaxSequences = 10,
    [int]$EpisodeLength = 360,
    [string]$Device = "",
    [switch]$CheckOnly,
    [switch]$UseEgl
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$DatasetRoot = Join-Path $DataRoot "task_D_D"
$CommonArgs = @(
    ".\scripts\evaluate_calvin_rollout.py",
    "--config", ".\configs\calvin_act.yaml",
    "--dataset-root", $DatasetRoot,
    "--output-root", $OutputRoot,
    "--max-sequences", "$MaxSequences",
    "--ep-len", "$EpisodeLength"
)
if ($Device -ne "") {
    $CommonArgs += @("--device", $Device)
}
if ($CheckOnly) {
    $CommonArgs += "--check-only"
}
if ($UseEgl) {
    $CommonArgs += "--use-egl"
}

& $Python @CommonArgs --checkpoint $BCheckpoint --run-name "act_b_only_to_d_rollout"
if ($LASTEXITCODE -ne 0) {
    throw "B-only D rollout failed with exit code $LASTEXITCODE"
}

& $Python @CommonArgs --checkpoint $ABCCheckpoint --run-name "act_abc_joint_to_d_rollout"
if ($LASTEXITCODE -ne 0) {
    throw "A+B+C D rollout failed with exit code $LASTEXITCODE"
}
