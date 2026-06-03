$ErrorActionPreference = "Stop"

$reportDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $reportDir
$python = Join-Path $repoRoot "task2\.venv\Scripts\python.exe"
$xelatex = "D:\Program Files\texlive\2024\bin\windows\xelatex.exe"
$finalPdf = Join-Path $reportDir "HW3_Report_ChenJialong_24300980041.pdf"

if (-not (Test-Path $python)) {
    throw "Missing Python runtime: $python"
}
if (-not (Test-Path $xelatex)) {
    throw "Missing XeLaTeX runtime: $xelatex"
}

& $python (Join-Path $reportDir "build_report_assets.py")
New-Item -ItemType Directory -Force -Path (Join-Path $reportDir "build") | Out-Null

Push-Location $reportDir
try {
    & $xelatex -interaction=nonstopmode -halt-on-error -output-directory="build" "hw3_report.tex"
    & $xelatex -interaction=nonstopmode -halt-on-error -output-directory="build" "hw3_report.tex"
    Copy-Item -Force -LiteralPath "build\hw3_report.pdf" -Destination $finalPdf
}
finally {
    Pop-Location
}

Write-Output "Built report: $finalPdf"
