param(
    [ValidateSet("ABC", "ABCD", "D")]
    [string]$Split = "ABC",
    [string]$DataRoot = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $DataRoot) {
    $DataRoot = Join-Path $RepoRoot "data\calvin"
}
$TaskName = switch ($Split) {
    "ABC" { "task_ABC_D" }
    "ABCD" { "task_ABCD_D" }
    "D" { "task_D_D" }
}
$Url = "http://calvin.cs.uni-freiburg.de/scene_info_fix/${TaskName}_scene_info.zip"
$ArchiveDir = Join-Path $DataRoot "_scene_info_archives"
$Archive = Join-Path $ArchiveDir "${TaskName}_scene_info.zip"
$ExtractDir = Join-Path $ArchiveDir "${TaskName}_scene_info"

New-Item -ItemType Directory -Force $ArchiveDir | Out-Null
Invoke-WebRequest -Uri $Url -OutFile $Archive
Expand-Archive -LiteralPath $Archive -DestinationPath $ExtractDir -Force

$Metadata = Get-ChildItem -Path $ExtractDir -Recurse -Filter "scene_info.npy" | Select-Object -First 1
if (-not $Metadata) {
    throw "scene_info.npy was not found in $Archive"
}

$Destination = Join-Path (Join-Path $DataRoot $TaskName) "training"
if ($Split -eq "D") {
    $Destination = Join-Path (Join-Path $DataRoot $TaskName) "validation"
}
New-Item -ItemType Directory -Force $Destination | Out-Null
Copy-Item -LiteralPath $Metadata.FullName -Destination (Join-Path $Destination "scene_info.npy") -Force
Write-Host "Installed scene_info.npy into $Destination"
