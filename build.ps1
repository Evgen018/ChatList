# Skript dlya sozdaniya ispolnyaemogo fayla Windows
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Building executable..." -ForegroundColor Green

# Udalyaem starye fayly sborki
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# Sozdayom .exe fayl
pyinstaller --onefile --windowed --name="ChatListApp" --icon=NONE main.py

Write-Host ""
Write-Host "Done! Executable file is in 'dist' folder" -ForegroundColor Green
Write-Host "Run: .\dist\ChatListApp.exe" -ForegroundColor Cyan

