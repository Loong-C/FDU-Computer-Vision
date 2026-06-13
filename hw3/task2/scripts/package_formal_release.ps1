param(
    [string]$OutputRoot = ".\outputs\official_subset_formal"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$ReleaseDir = Join-Path $OutputRoot "release"
New-Item -ItemType Directory -Force $ReleaseDir | Out-Null

$Assets = @(
    @{
        Source = Join-Path $OutputRoot "act_b_only_partial_formal\checkpoints\best.pt"
        Name = "hw3-task2-act-b-only-best.pt"
    },
    @{
        Source = Join-Path $OutputRoot "act_abc_joint_partial_formal\checkpoints\best.pt"
        Name = "hw3-task2-act-abc-joint-best.pt"
    }
)

$Lines = foreach ($Asset in $Assets) {
    if (-not (Test-Path -LiteralPath $Asset.Source)) {
        throw "Missing checkpoint: $($Asset.Source)"
    }
    $Destination = Join-Path $ReleaseDir $Asset.Name
    Copy-Item -LiteralPath $Asset.Source -Destination $Destination -Force
    $Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Destination).Hash.ToLowerInvariant()
    "$Hash  $($Asset.Name)"
}

$SumsPath = Join-Path $ReleaseDir "SHA256SUMS.txt"
[System.IO.File]::WriteAllText(
    (Resolve-Path $ReleaseDir).Path + "\SHA256SUMS.txt",
    ($Lines -join [Environment]::NewLine) + [Environment]::NewLine,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "Packaged formal release assets:"
$Lines | ForEach-Object { Write-Host $_ }
