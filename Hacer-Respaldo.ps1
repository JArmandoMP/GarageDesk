# ============================================================
# Hacer-Respaldo.ps1 · Copia de seguridad versionada de GarageDesk
# Lee APP_VERSION de GarageDesk.py (fuente de verdad) y crea:
#   E:\Programación\OpenCode\Control de Gastos -Vehículos- - Respaldos\Versiones\AAAA-MM\
#     1) Carpeta "vX.Y.Z.W (fecha hora)" con el proyecto (sin generados)
#     2) ZIP del mismo respaldo
# Los datos personales NO se copian aquí: están en ... - Respaldos\Datos\
# ============================================================

$ErrorActionPreference = 'Stop'
$src  = $PSScriptRoot
$base = Split-Path $src -Parent

$backupRoot   = Join-Path $base 'Control de Gastos -Vehículos- - Respaldos'
$versionsRoot = Join-Path $backupRoot 'Versiones'
$monthFolder  = Join-Path $versionsRoot (Get-Date -Format 'yyyy-MM')
if (-not (Test-Path -LiteralPath $monthFolder)) {
    New-Item -ItemType Directory -Path $monthFolder -Force | Out-Null
}

# Fuente de verdad de la versión: GarageDesk.py -> APP_VERSION
$version = '0.0.0.0'
$pyPath = Join-Path $src 'GarageDesk.py'
if (Test-Path -LiteralPath $pyPath) {
    $match = Select-String -LiteralPath $pyPath -Pattern '^APP_VERSION\s*=\s*"([0-9.]+)"'
    if ($match) {
        $v = $match.Matches[0].Groups[1].Value
        $parts = $v.Split('.')
        while ($parts.Count -lt 4) { $parts += '0' }
        $version = ($parts[0..3] -join '.')
    }
}

$stamp = Get-Date -Format 'yyyy-MM-dd_HHmm'
$folderName = "v$version ($stamp)"
$destFolder = Join-Path $monthFolder $folderName
$zipPath = Join-Path $monthFolder "GarageDesk-v$version ($stamp).zip"

if (Test-Path -LiteralPath $destFolder) {
    $stamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
    $folderName = "v$version ($stamp)"
    $destFolder = Join-Path $monthFolder $folderName
    $zipPath = Join-Path $monthFolder "GarageDesk-v$version ($stamp).zip"
}

# Excluir artefactos regenerables, datos personales y sesiones locales
$excludes = @('node_modules', 'release', 'dist', 'build', '__pycache__',
              'comprobantes', 'fotos_vehiculos', 'backups_locales',
              'ses_*.json', '*.db', '*.garagepack', '*.log', '*.zip')
$null = robocopy $src $destFolder /E /COPY:DAT /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XD $excludes /XF $excludes
if ($LASTEXITCODE -ge 8) { throw "robocopy falló con código $LASTEXITCODE" }

Compress-Archive -Path $destFolder -DestinationPath $zipPath -Force

Write-Host ''
Write-Host 'Respaldo creado correctamente:' -ForegroundColor Green
Write-Host "  Versión: $version"
Write-Host "  Mes:     $monthFolder"
Write-Host "  Carpeta: $destFolder"
Write-Host "  ZIP:     $zipPath"
Write-Host ''
