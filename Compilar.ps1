# ============================================================
# Compilar.ps1 · Construye GarageDesk 3.1.0.1 y su instalador
# Requiere:
#   Python completo con Tkinter: E:\Programación\Utilerias\Python-Full
#   Inno Setup 6:                E:\Programación\Utilerias\InnoSetup6
# El instalador se copia además a:
#   E:\Programación\OpenCode\Control de Gastos -Vehículos- - Compilación\Instaladores\
# ============================================================

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$py   = 'E:\Programación\Utilerias\Python-Full\python.exe'
$iscc = 'E:\Programación\Utilerias\InnoSetup6\ISCC.exe'

if (-not (Test-Path -LiteralPath $py))   { throw "No existe Python: $py" }
if (-not (Test-Path -LiteralPath $iscc)) { throw "No existe Inno Setup: $iscc" }

# Versión desde la fuente (fuente de verdad)
$match = Select-String -LiteralPath (Join-Path $root 'GarageDesk.py') -Pattern '^APP_VERSION\s*=\s*"([0-9.]+)"'
if (-not $match) { throw 'No se pudo leer APP_VERSION de GarageDesk.py' }
$version = $match.Matches[0].Groups[1].Value
Write-Host "Compilando GarageDesk v$version" -ForegroundColor Cyan

$dist = Join-Path $root 'release\win'
$work = Join-Path $root 'release\build'
$inst = Join-Path $root 'release\installer'
foreach ($d in @($dist, $work, $inst)) {
    if (Test-Path -LiteralPath $d) { Remove-Item -LiteralPath $d -Recurse -Force }
}
New-Item -ItemType Directory -Path $inst -Force | Out-Null

Write-Host '1/3 PyInstaller...' -ForegroundColor Yellow
Push-Location $root
try {
    & $py -m PyInstaller --noconfirm --clean --distpath $dist --workpath $work GarageDesk.spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller falló ($LASTEXITCODE)" }
} finally { Pop-Location }

Write-Host '2/3 Inno Setup...' -ForegroundColor Yellow
& $iscc (Join-Path $root 'instalador.iss')
if ($LASTEXITCODE -ne 0) { throw "Inno Setup falló ($LASTEXITCODE)" }

$setup = Get-ChildItem -LiteralPath $inst -Filter '*.exe' -File |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $setup) { throw 'No se generó el instalador .exe' }

$hash = (Get-FileHash -LiteralPath $setup.FullName -Algorithm SHA256).Hash
Write-Host '3/3 Copiando a Compilación...' -ForegroundColor Yellow
$base = Split-Path $root -Parent
$destinoDir = Join-Path $base 'Control de Gastos -Vehículos- - Compilación\Instaladores'
New-Item -ItemType Directory -Path $destinoDir -Force | Out-Null
$destino = Join-Path $destinoDir $setup.Name
Copy-Item -LiteralPath $setup.FullName -Destination $destino -Force
$hashFile = Join-Path $destinoDir ($setup.Name + '.sha256.txt')
Set-Content -LiteralPath $hashFile -Value $hash -Encoding ASCII

Write-Host ''
Write-Host 'Compilación terminada:' -ForegroundColor Green
Write-Host "  Instalador: $destino"
Write-Host "  SHA256:     $hash"
Write-Host ("  Tamaño:     {0:N1} MB" -f ((Get-Item -LiteralPath $destino).Length / 1MB))
