$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    Write-Error "Project virtualenv not found. Create it and install requirements first: python -m venv .venv; .\.venv\Scripts\python -m pip install -r requirements.txt"
    exit 1
}

$tesseract = $null
if ($env:TESSERACT_CMD -and (Test-Path -LiteralPath $env:TESSERACT_CMD)) {
    $tesseract = $env:TESSERACT_CMD
}

if (-not $tesseract -and $env:LOCALAPPDATA) {
    $userInstall = Join-Path $env:LOCALAPPDATA "Programs\Tesseract-OCR\tesseract.exe"
    if (Test-Path -LiteralPath $userInstall) {
        $tesseract = $userInstall
    }
}

if (-not $tesseract -and $env:ProgramFiles) {
    $systemInstall = Join-Path $env:ProgramFiles "Tesseract-OCR\tesseract.exe"
    if (Test-Path -LiteralPath $systemInstall) {
        $tesseract = $systemInstall
    }
}

if (-not $tesseract) {
    $pathCommand = Get-Command "tesseract.exe" -ErrorAction SilentlyContinue
    if ($pathCommand) {
        $tesseract = $pathCommand.Source
    }
}

if (-not $tesseract) {
    Write-Error "Tesseract was not found. Install it or set TESSERACT_CMD to the full path of tesseract.exe."
    exit 1
}

$env:TESSERACT_CMD = $tesseract
Set-Location $projectRoot
Write-Host "Using Tesseract: $tesseract"
Write-Host "Starting Kliros Manager at http://127.0.0.1:5000"
& $python app.py
exit $LASTEXITCODE