param(
    [string]$Repository = "Loong-C/FDU-Computer-Vision",
    [string]$Tag = "hw3-task2-formal-partial-v1",
    [string]$Target = "main",
    [string]$ReleaseDir = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $ReleaseDir) {
    $ReleaseDir = Join-Path $RepoRoot "outputs\official_subset_formal\release"
}

$RequiredFiles = @(
    "hw3-task2-act-b-only-best.pt",
    "hw3-task2-act-abc-joint-best.pt",
    "SHA256SUMS.txt"
)

foreach ($Name in $RequiredFiles) {
    $Path = Join-Path $ReleaseDir $Name
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing release asset: $Path"
    }
}

$Expected = @{}
$SumsPath = Join-Path $ReleaseDir "SHA256SUMS.txt"
foreach ($Line in Get-Content -LiteralPath $SumsPath) {
    if ($Line -match '^([0-9a-fA-F]{64})\s+(.+)$') {
        $Expected[$Matches[2]] = $Matches[1].ToLowerInvariant()
    }
}

foreach ($Name in $RequiredFiles | Where-Object { $_ -ne "SHA256SUMS.txt" }) {
    if (-not $Expected.ContainsKey($Name)) {
        throw "SHA256SUMS.txt does not contain an entry for $Name"
    }
    $Path = Join-Path $ReleaseDir $Name
    $Actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
    if ($Actual -ne $Expected[$Name]) {
        throw "SHA256 mismatch for $Name. Expected $($Expected[$Name]), got $Actual"
    }
}

$Assets = $RequiredFiles | ForEach-Object { Join-Path $ReleaseDir $_ }
$Notes = @"
HW3 Task2 formal partial ACT checkpoints.

- Source: https://github.com/$Repository/tree/$Target/hw3/task2
- Google Drive mirror: https://drive.google.com/drive/folders/1v9oc1uTbZS31SaDJaT7sYV8m5dutMo1y?usp=drive_link
- Data protocol: HTTP-Range CALVIN subset, 16 windows of 48 frames per environment.
- Validation protocol: environment-stratified continuous-window holdout with zero train/validation action-frame overlap.
- B-only SHA256: $($Expected["hw3-task2-act-b-only-best.pt"])
- A+B+C SHA256: $($Expected["hw3-task2-act-abc-joint-best.pt"])
"@

if ($DryRun) {
    Write-Host "Dry run OK. Local release assets and hashes are valid."
    Write-Host "Would publish tag '$Tag' to '$Repository' targeting '$Target'."
    foreach ($Asset in $Assets) {
        Write-Host "Would upload: $Asset"
    }
    return
}

gh auth status
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run: gh auth login -h github.com"
}

$PreviousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& gh release view $Tag --repo $Repository *> $null
$ReleaseExists = $LASTEXITCODE -eq 0
$ErrorActionPreference = $PreviousErrorActionPreference
if (-not $ReleaseExists) {
    gh release create $Tag --repo $Repository --target $Target --title "HW3 Task2 formal partial ACT checkpoints" --notes $Notes
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create GitHub Release $Tag in $Repository"
    }
} else {
    gh release edit $Tag --repo $Repository --target $Target --title "HW3 Task2 formal partial ACT checkpoints" --notes $Notes
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to update GitHub Release $Tag in $Repository"
    }
}

$UploadArgs = @("release", "upload", $Tag) + $Assets + @("--repo", $Repository, "--clobber")
& gh @UploadArgs
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upload release assets to $Repository@$Tag"
}

Write-Host "Published release:"
Write-Host "https://github.com/$Repository/releases/tag/$Tag"
