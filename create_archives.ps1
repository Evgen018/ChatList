# Script to create source code archives for GitHub Release
# Usage: .\create_archives.ps1

param(
    [string]$Version = "1.0.4"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Creating Source Archives for ChatList v$Version ===" -ForegroundColor Cyan
Write-Host ""

# Variables
$name = "ChatList-v$Version"
$tempDir = "temp_archive"
$archiveDir = "$tempDir\$name"
$distDir = "dist"

# Create directories
Write-Host "Creating temporary directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
New-Item -ItemType Directory -Path $distDir -Force -ErrorAction SilentlyContinue | Out-Null

# Files to include
Write-Host "Copying files..." -ForegroundColor Yellow

# Python files
Copy-Item -Path "*.py" -Destination $archiveDir -Force -ErrorAction SilentlyContinue

# Documentation
Copy-Item -Path "*.md" -Destination $archiveDir -Force -ErrorAction SilentlyContinue

# Configuration files
Copy-Item -Path "*.txt" -Destination $archiveDir -Force -ErrorAction SilentlyContinue
Copy-Item -Path "*.ico" -Destination $archiveDir -Force -ErrorAction SilentlyContinue
Copy-Item -Path "*.png" -Destination $archiveDir -Force -ErrorAction SilentlyContinue
Copy-Item -Path "*.iss" -Destination $archiveDir -Force -ErrorAction SilentlyContinue
Copy-Item -Path "*.spec" -Destination $archiveDir -Force -ErrorAction SilentlyContinue

# Special files
Copy-Item -Path "LICENSE" -Destination $archiveDir -Force -ErrorAction SilentlyContinue
Copy-Item -Path ".env.example" -Destination $archiveDir -Force -ErrorAction SilentlyContinue
Copy-Item -Path ".gitignore" -Destination $archiveDir -Force -ErrorAction SilentlyContinue
Copy-Item -Path ".gitattributes" -Destination $archiveDir -Force -ErrorAction SilentlyContinue

# Directories
Copy-Item -Path "docs" -Destination "$archiveDir\docs" -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item -Path ".github" -Destination "$archiveDir\.github" -Recurse -Force -ErrorAction SilentlyContinue

# Count files
$fileCount = (Get-ChildItem -Path $archiveDir -Recurse -File).Count
Write-Host "Copied $fileCount files" -ForegroundColor Green

# Create ZIP archive
Write-Host ""
Write-Host "Creating ZIP archive..." -ForegroundColor Yellow
$zipPath = "$distDir\$name-Source.zip"
Compress-Archive -Path $archiveDir -DestinationPath $zipPath -Force
$zipSize = [math]::Round((Get-Item $zipPath).Length / 1KB, 2)
Write-Host "Created: $zipPath ($zipSize KB)" -ForegroundColor Green

# Create TAR.GZ archive
Write-Host ""
Write-Host "Creating TAR.GZ archive..." -ForegroundColor Yellow
$tarPath = "$distDir\$name-Source.tar.gz"
Push-Location $tempDir
tar -czf "..\$tarPath" $name
Pop-Location
$tarSize = [math]::Round((Get-Item $tarPath).Length / 1KB, 2)
Write-Host "Created: $tarPath ($tarSize KB)" -ForegroundColor Green

# Cleanup
Write-Host ""
Write-Host "Cleaning up..." -ForegroundColor Yellow
Remove-Item -Path $tempDir -Recurse -Force
Write-Host "Temporary files removed" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Archives created successfully!" -ForegroundColor Green
Write-Host ""
Get-ChildItem "$distDir\*Source*" | Select-Object Name, @{Name="Size (KB)";Expression={[math]::Round($_.Length/1KB, 2)}} | Format-Table -AutoSize

Write-Host ""
Write-Host "Ready to upload to GitHub Release!" -ForegroundColor Green
