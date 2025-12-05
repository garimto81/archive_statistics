# Create deployment package
# This script creates a ZIP file for deployment

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputFile = "$projectRoot\..\archive-stats-deploy-$timestamp.zip"

Write-Host "Creating deployment package..."
Write-Host "Source: $projectRoot"
Write-Host "Output: $outputFile"

# Create temp directory
$tempDir = "$env:TEMP\archive-stats-package"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

# Copy files (excluding unnecessary)
$excludeDirs = @(
    "venv",
    ".venv",
    "node_modules",
    "__pycache__",
    ".git",
    ".pytest_cache",
    "dist",
    "build",
    ".idea",
    ".vscode",
    "data"
)

$excludeFiles = @(
    "*.pyc",
    "*.pyo",
    "*.db",
    "*.sqlite",
    "*.log",
    ".env",
    ".env.local"
)

# Use robocopy for efficient copy with exclusions
$excludeDirArgs = $excludeDirs | ForEach-Object { "/XD", $_ }
$excludeFileArgs = $excludeFiles | ForEach-Object { "/XF", $_ }

$robocopyArgs = @(
    $projectRoot,
    "$tempDir\Archive_Statistics",
    "/E",
    "/NP",
    "/NFL",
    "/NDL"
) + $excludeDirArgs + $excludeFileArgs

& robocopy @robocopyArgs | Out-Null

# Create data directory placeholder
New-Item -ItemType Directory -Force -Path "$tempDir\Archive_Statistics\data" | Out-Null
"# Database files will be created here" | Out-File "$tempDir\Archive_Statistics\data\.gitkeep"

# Create ZIP
Write-Host "Compressing files..."
if (Test-Path $outputFile) {
    Remove-Item $outputFile
}
Compress-Archive -Path "$tempDir\Archive_Statistics" -DestinationPath $outputFile -CompressionLevel Optimal

# Cleanup
Remove-Item -Recurse -Force $tempDir

$size = (Get-Item $outputFile).Length / 1MB
Write-Host ""
Write-Host "========================================"
Write-Host " Package created successfully!"
Write-Host "========================================"
Write-Host " File: $outputFile"
Write-Host " Size: $([math]::Round($size, 2)) MB"
Write-Host ""
Write-Host " To deploy, copy this file to the target server and run:"
Write-Host "   Expand-Archive archive-stats-deploy-*.zip -DestinationPath C:\"
Write-Host "   cd C:\Archive_Statistics"
Write-Host "   .\deploy\install.ps1"
Write-Host ""
