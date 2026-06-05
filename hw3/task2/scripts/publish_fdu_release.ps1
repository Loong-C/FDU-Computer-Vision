param(
    [string]$Repository = "Loong-C/FDU-Computer-Vision",
    [string]$Tag = "hw3-task2-formal-partial-v1",
    [string]$Target = "hw3",
    [string]$ReleaseDir = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $ReleaseDir) {
    $ReleaseDir = Join-Path $RepoRoot "outputs\official_subset_formal\release"
}

$Expected = @{
    "hw3-task2-act-b-only-best.pt" = "58afae052ef2ce029f92c9258e1b5012a9c44fac5753c1c8330b7d196a976131"
    "hw3-task2-act-abc-joint-best.pt" = "1b1f182e61026929f0a5ffdc5ee096d15e4771febd111d9efe3d88bc4a9adcff"
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

foreach ($Name in $Expected.Keys) {
    $Path = Join-Path $ReleaseDir $Name
    $Actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
    if ($Actual -ne $Expected[$Name]) {
        throw "SHA256 mismatch for $Name. Expected $($Expected[$Name]), got $Actual"
    }
}

$Sums = Get-Content -LiteralPath (Join-Path $ReleaseDir "SHA256SUMS.txt") -Raw
foreach ($Name in $Expected.Keys) {
    if ($Sums -notmatch [regex]::Escape($Expected[$Name]) -or $Sums -notmatch [regex]::Escape($Name)) {
        throw "SHA256SUMS.txt does not contain the expected entry for $Name"
    }
}

$Assets = $RequiredFiles | ForEach-Object { Join-Path $ReleaseDir $_ }
$Notes = @"
HW3 Task2 formal partial ACT checkpoints.

- Source: https://github.com/$Repository/tree/$Target/hw3/task2
- Data protocol: HTTP-Range CALVIN subset, 16 windows of 48 frames per environment.
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

gh release view $Tag --repo $Repository *> $null
if ($LASTEXITCODE -ne 0) {
    gh release create $Tag --repo $Repository --target $Target --title "HW3 Task2 formal partial ACT checkpoints" --notes $Notes
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create GitHub Release $Tag in $Repository"
    }
}

$UploadArgs = @("release", "upload", $Tag) + $Assets + @("--repo", $Repository, "--clobber")
& gh @UploadArgs
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upload release assets to $Repository@$Tag"
}

Write-Host "Published release:"
Write-Host "https://github.com/$Repository/releases/tag/$Tag"
