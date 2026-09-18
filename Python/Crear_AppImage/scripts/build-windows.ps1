# Compila e instala appimage-builder en Windows (venv + wheel + smoke tests).
#
# Nota: los AppImage son solo para Linux; en Windows se instala el paquete
# (CLI + GUI Qt) para desarrollo y uso local.
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1
#
# Variables de entorno:
#   VENV_DIR   Directorio del venv (defecto: <repo>\.venv)
#   WITH_DEV   "0" omite extras dev/gui/build (defecto: "1")
#   BUILD_DIST "0" omite sdist/wheel (defecto: "1")

$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$VenvDir = if ($env:VENV_DIR) { $env:VENV_DIR } else { Join-Path $Root '.venv' }
$WithDev = if ($env:WITH_DEV) { $env:WITH_DEV } else { '1' }
$BuildDist = if ($env:BUILD_DIST) { $env:BUILD_DIST } else { '1' }

function Write-Log($msg) { Write-Host "[build-windows] $msg" }

function Find-Python {
    foreach ($cmd in @('py -3', 'python')) {
        $parts = $cmd.Split(' ')
        try {
            $out = & $parts[0] $parts[1..($parts.Count - 1)] --version 2>&1
            if ($LASTEXITCODE -eq 0 -and $out -match 'Python 3\.(1[1-9]|[2-9][0-9])') {
                return $parts
            }
        } catch { }
    }
    throw 'No se encontró Python >= 3.11 (instala Python o el launcher py)'
}

$Python = Find-Python
Write-Log "Python detectado: $($Python -join ' ')"

$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'
if (-not (Test-Path $VenvPython)) {
    Write-Log "Creando venv en $VenvDir"
    & $Python -m venv $VenvDir
}
& $VenvPython -m pip install --upgrade pip

if ($WithDev -eq '1') {
    Write-Log 'Instalando paquete + extras (dev,gui,build)'
    & $VenvPython -m pip install -e "$Root[dev,gui,build]"
} else {
    Write-Log 'Instalando solo el paquete'
    & $VenvPython -m pip install $Root
}

if ($BuildDist -eq '1') {
    Write-Log 'Generando sdist/wheel'
    & $VenvPython -m pip install --quiet build
    if (Test-Path (Join-Path $Root 'dist')) { Remove-Item -Recurse -Force (Join-Path $Root 'dist') }
    New-Item -ItemType Directory -Force -Path (Join-Path $Root 'dist') | Out-Null
    & $VenvPython -m build $Root --outdir (Join-Path $Root 'dist')
}

Write-Log 'Smoke tests'
$Cli = Join-Path $VenvDir 'Scripts\appimage-builder.exe'
& $Cli --version
& $Cli template list | Out-Null
$env:QT_QPA_PLATFORM = 'offscreen'
& $VenvPython -c "from appimage_builder.gui.wizard.wizard import AppImageWizard; print('GUI OK')"

Write-Log "OK: venv=$VenvDir"
Write-Log "Nota: 'appimage-builder build/doctor' está orientado a Linux (AppImage)."
