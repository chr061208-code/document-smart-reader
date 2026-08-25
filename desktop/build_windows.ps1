$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$CorePath = Join-Path $ProjectRoot "plugins\document-smart-reader\skills\document-smart-reader\scripts"
$EntryPoint = Join-Path $PSScriptRoot "document_smart_reader.py"

Push-Location $ProjectRoot
try {
    python -m PyInstaller --noconfirm --clean --onefile --windowed `
        --name DocumentSmartReader `
        --version-file (Join-Path $PSScriptRoot "version_info.txt") `
        --paths $CorePath `
        --exclude-module pandas `
        --exclude-module numpy `
        --exclude-module matplotlib `
        --exclude-module openpyxl `
        $EntryPoint
} finally {
    Pop-Location
}

Write-Host "Built: $ProjectRoot\dist\DocumentSmartReader.exe"
