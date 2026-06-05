param(
    [string]$Project = "hw3-calvin-act",
    [Parameter(Mandatory = $true, Position = 0)]
    [string[]]$RunPaths
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

foreach ($RunPath in $RunPaths) {
    swanlab sync $RunPath -p $Project
    if ($LASTEXITCODE -ne 0) {
        throw "SwanLab sync failed for $RunPath with exit code $LASTEXITCODE"
    }
}
