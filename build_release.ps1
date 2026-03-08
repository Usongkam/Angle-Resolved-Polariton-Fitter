param(
    [switch]$OneFile,
    [string]$PythonExe = 'C:\Users\gys\AppData\Local\Python\bin\python.exe'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$pythonExe = $PythonExe

Write-Host 'Installing build dependency: PyInstaller'
& $pythonExe -m pip install pyinstaller

if ($OneFile) {
    Write-Host 'Building onefile release package'
    & $pythonExe -m PyInstaller --noconfirm --clean --onefile --windowed --name AngleResolvedPolaritonFitter --paths apps/V4 --hidden-import PyQt6.sip --hidden-import matplotlib.backends.backend_qtagg --collect-data matplotlib --collect-submodules matplotlib.backends apps/V4/app.py
}
else {
    Write-Host 'Building onedir release package from spec'
    & $pythonExe -m PyInstaller --noconfirm --clean AngleResolvedPolaritonFitter.spec
}

Write-Host 'Build completed. Check dist/ for release artifacts.'

