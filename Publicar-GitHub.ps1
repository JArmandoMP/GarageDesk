# ============================================================
# Publicar-GitHub.ps1 · Publica GarageDesk 3.1.0.1 en GitHub
# Uso:
#   1) Crear el repo vacío PUBLICADO "GarageDesk" en github.com/new
#   2) Crear token fine-grained (este script NO lo guarda en el repo)
#   3)powershell -NoProfile -ExecutionPolicy Bypass -File .\Publicar-GitHub.ps1 -TokenFile <archivo-temporal>
#
# Hace:
#   - Valida token y repo público
#   - Respalla el .git anterior (con historial viejo) FUERA del repo
#   - Reinicia el historial limpio (sin archivos sensibles)
#   - Push a https://github.com/JArmandoMP/GarageDesk.git (sin token en claro)
#   - Crea Release v3.1.0.1 con instalador + SHA256
#   - Guarda la credencial en el Administrador de Credenciales de Windows
# ============================================================
param(
    [Parameter(Mandatory = $true)][string]$TokenFile
)

$ErrorActionPreference = 'Stop'
$gitExe = 'R:\Programación\OpenCode\Herramientas\Git\bin\git.exe'
$gitCmd = 'R:\Programación\OpenCode\Herramientas\Git\git.cmd'
$root   = 'R:\Programación\OpenCode\Control de Gastos -Vehículos-'
$base   = Split-Path $root -Parent
$owner  = 'JArmandoMP'
$repo   = 'GarageDesk'
$api    = 'https://api.github.com'
$version = '3.1.0.1'
$tag     = "v$version"

if (-not (Test-Path -LiteralPath $TokenFile)) { throw "No existe el archivo de token: $TokenFile" }
$token = ([IO.File]::ReadAllText($TokenFile)).Trim()
if ($token -notmatch '^github_pat_') { throw 'El token no parece fine-grained (debe empezar con github_pat_)' }

$headers = @{
    Authorization = "Bearer $token"
    Accept        = 'application/vnd.github+json'
    'User-Agent'  = 'GarageDesk-Publicador'
    'X-GitHub-Api-Version' = '2022-11-28'
}

Write-Host '1/8 Validando token...' -ForegroundColor Cyan
$user = Invoke-RestMethod -Uri "$api/user" -Headers $headers
if ($user.login -ne $owner) { throw "El token es de '$($user.login)', se esperaba '$owner'" }
Write-Host "   Usuario OK: $($user.login)"

Write-Host '2/8 Verificando repositorio público...' -ForegroundColor Cyan
try {
    $r = Invoke-RestMethod -Uri "$api/repos/$owner/$repo" -Headers $headers
} catch {
    throw "No existe '$owner/$repo'. Créalo vacío y público en https://github.com/new antes de continuar."
}
if ($r.private) {
    Write-Host '   El repo es privado; publicándolo...' -ForegroundColor Yellow
    $null = Invoke-RestMethod -Uri "$api/repos/$owner/$repo" -Method Patch -Headers $headers -Body (@{ private = $false } | ConvertTo-Json -Compress)
    Start-Sleep -Seconds 2
}
Write-Host "   Repo OK: $($r.html_url) (público)"

Write-Host '3/8 Respaldando el historial Git anterior...' -ForegroundColor Cyan
$stamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$histDest = Join-Path $base "Control de Gastos -Vehículos- - Respaldos\Git-Historial-PrePublicacion\$stamp"
New-Item -ItemType Directory -Path $histDest -Force | Out-Null
$oldGit = Join-Path $root '.git'
if (Test-Path -LiteralPath $oldGit) {
    Copy-Item -LiteralPath $oldGit -Destination (Join-Path $histDest '.git') -Recurse -Force
    # Sanitizar también la copia: quitar cualquier token del remote respaldado
    $cfg = Join-Path $histDest '.git\config'
    if (Test-Path -LiteralPath $cfg) {
        (Get-Content -LiteralPath $cfg) -replace 'https://[^/@]+:[^@]+@github\.com', 'https://github.com' |
            Set-Content -LiteralPath $cfg -Encoding ASCII
    }
    Write-Host "   Historial guardado en: $histDest"
}

Write-Host '4/8 Reiniciando historial limpio...' -ForegroundColor Cyan
if (Test-Path -LiteralPath $oldGit) { Remove-Item -LiteralPath $oldGit -Recurse -Force }
& $gitCmd -C $root init -b main
if ($LASTEXITCODE -ne 0) { throw 'git init falló' }
& $gitCmd -C $root config user.name 'JArmandoMP'
& $gitCmd -C $root config user.email 'JArmandoMP@users.noreply.github.com'
& $gitCmd -C $root add -A
& $gitCmd -C $root commit -m "GarageDesk $version - código limpio, parches de estabilidad e instalador"
if ($LASTEXITCODE -ne 0) { throw 'git commit falló' }

Write-Host '5/8 Haciendo push con el token nuevo (remote limpio al terminar)...' -ForegroundColor Cyan
# Se autentica explícitamente para no usar credenciales viejas cacheadas.
# El token aparece en .git/config solo durante el push y se quita de inmediato.
& $gitCmd -C $root config remote.origin.url "https://x-access-token:$token@github.com/$owner/$repo.git"
& $gitCmd -C $root config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'
try {
    # --force: el remoto tenía el historial viejo del prototipo con archivos sensibles.
    # Se sobrescribe deliberadamente con el historial limpio y auditado.
    & $gitCmd -C $root push -u --force origin main
    if ($LASTEXITCODE -ne 0) { throw 'git push falló' }
} finally {
    & $gitCmd -C $root config remote.origin.url "https://github.com/$owner/$repo.git"
}
Write-Host '   Remote limpio: https://github.com/'"$owner/$repo.git"

Write-Host '6/8 Guardando credencial en Windows (fuera del repo)...' -ForegroundColor Cyan
$credTmp = Join-Path $env:TEMP ('gdcred_' + [guid]::NewGuid().ToString('N') + '.txt')
try {
    [IO.File]::WriteAllText($credTmp, "protocol=https`nhost=github.com`nusername=$owner`npassword=$token`n`n")
    $null = cmd /c "type ""$credTmp"" | ""$gitExe"" credential approve"
    if ($LASTEXITCODE -ne 0) { Write-Host '   No se pudo guardar la credencial (no es crítico).' -ForegroundColor Yellow }
} finally {
    Remove-Item -LiteralPath $credTmp -Force -ErrorAction SilentlyContinue
}

Write-Host '7/8 Creando Release...' -ForegroundColor Cyan
$releaseBody = @(
    "## GarageDesk $version"
    ""
    "Instalador/actualizador para Windows 11. Actualiza encima sin desinstalar y sin borrar tus datos."
    "Los datos viven en %LOCALAPPDATA%\GarageDesk."
    ""
    "### Corregido"
    "- Rescate de base de datos corrupta en la ruta real de datos, preservando el archivo danyado."
    "- Copias en caliente con WAL usando sqlite3.Connection.backup() (sin perdida de transacciones)."
    "- Nombres unicos de respaldo, busy_timeout y fin del escaneo de BDs vecinas."
    "- matplotlib maneja errores de DLL en Windows; dialogos previos usan MessageBox nativo."
    ""
    "### Agregado"
    "- Buscador de actualizaciones desde GitHub Releases con verificacion de SHA256."
    "- Metadatos reales de version en GarageDesk.exe y script Compilar.ps1."
    ""
    "Cambio completo: https://github.com/$owner/$repo/blob/main/CHANGELOG.md"
) -join "`n"
try {
    $existing = Invoke-RestMethod -Uri "$api/repos/$owner/$repo/releases/tags/$tag" -Headers $headers -ErrorAction Stop
    $release = $existing
    Write-Host '   El release ya existía; se reutiliza.'
} catch {
    $body = @{
        tag_name         = $tag
        name             = "GarageDesk $version"
        body             = $releaseBody
        draft            = $false
        prerelease       = $false
        generate_release_notes = $false
    } | ConvertTo-Json -Depth 5 -Compress
    $postHeaders = $headers.Clone()
    $postHeaders['Content-Type'] = 'application/json'
    $release = Invoke-RestMethod -Uri "$api/repos/$owner/$repo/releases" -Method Post -Headers $postHeaders -Body $body
}
Write-Host "   Release: $($release.html_url)"

Write-Host '8/8 Subiendo instalador y SHA256...' -ForegroundColor Cyan
$installers = Join-Path $base 'Control de Gastos -Vehículos- - Compilación\Instaladores'
$setup = Get-ChildItem -LiteralPath $installers -Filter "GarageDesk_Setup_$version*.exe" -File |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $setup) { throw "No se encontró el instalador en $installers" }
$hashFile = Join-Path $installers ($setup.Name + '.sha256.txt')
$hash = (Get-FileHash -LiteralPath $setup.FullName -Algorithm SHA256).Hash

$assets = @($setup.FullName, $hashFile)
foreach ($asset in $assets) {
    $name = [IO.Path]::GetFileName($asset)
    $uri = "https://uploads.github.com/repos/$owner/$repo/releases/$($release.id)/assets?name=$([uri]::EscapeDataString($name))"
    $upHeaders = $headers.Clone()
    $upHeaders['Content-Type'] = 'application/octet-stream'
    $null = Invoke-RestMethod -Uri $uri -Method Post -Headers $upHeaders -InFile $asset
    Write-Host "   Subido: $name"
}

Write-Host ''
Write-Host 'PUBLICACIÓN COMPLETADA' -ForegroundColor Green
Write-Host "  Repo:     https://github.com/$owner/$repo"
Write-Host "  Release:  $($release.html_url)"
Write-Host "  SHA256:   $hash"
Write-Host "  Histórico anterior resguardado en: $histDest"
