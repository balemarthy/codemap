param(
  [Parameter(Mandatory=$true)]
  [string]$Folder
)

Write-Host ""
Write-Host "==================================================="
Write-Host " CodeMap (Windows Runner)"
Write-Host "==================================================="
Write-Host ""

# Go to the script's directory (repo root)
Set-Location -Path $PSScriptRoot

# Install deps (safe to run multiple times)
python -m pip install -r .\requirements.txt | Out-Null

Write-Host "Indexing folder:"
Write-Host "  $Folder"
Write-Host ""

# Build / refresh index
python .\codemap-indexer\analyze_folder_callsites_v2.py "$Folder"

Write-Host ""
Write-Host "Starting CodeMap Navigator..."
Write-Host ""

# Start navigator (folder-based)
python .\codemap-cli\nav_console_v3.py "$Folder"
