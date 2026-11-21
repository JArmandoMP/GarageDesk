# GarageDesk

Control vehicular personal: mantenimiento, servicios, costos, recordatorios, fotos, comprobantes y reportes.

- **Versión actual:** `3.1.0.1` (fuente de verdad: `APP_VERSION` en `GarageDesk.py`)
- **Tecnología:** Python 3.15 + CustomTkinter + SQLite (PyInstaller one-folder)
- **Instalación:** `C:\Program Files (x86)\GarageDesk`
- **Datos del usuario:** `%LOCALAPPDATA%\GarageDesk`

## Privacidad

GarageDesk **no envía datos a ningún servidor**. La única salida a Internet es la comprobación optativa de actualizaciones a GitHub Releases (`api.github.com`), y solo descarga el instalador después de tu confirmación.

**Nunca se suben a GitHub** la base de datos real, fotos, comprobantes, respaldos ni ningún dato personal. `.gitignore` excluye explícitamente `*.db`, `*-wal`, `*-shm`, `.garagepack`, `comprobantes/`, `fotos_vehiculos/`, `backups_locales/` y `ses_*.json`.

La única base de datos incluida en el repo es [`db-template/mi_vehiculo.db`](db-template/mi_vehiculo.db): una **plantilla vacía sin datos** para instalar GarageDesk desde cero. Está exenta de la regla anterior mediante una excepción en `.gitignore` y es públicamente segura de compartir.

## Actualizar sin desinstalar

1. Abre GarageDesk. Si hay versión nueva, avisará al iniciar; también puedes pulsar **Buscar actualizaciones** en el lateral.
2. Confirma la descarga. Se valida el SHA256 publicado en el Release.
3. Confirma la ejecución del instalador. Windows pedirá permiso de administrador (UAC).
4. El instalador usa el mismo `AppId`, por lo que **actualiza en sitio** y no borra tus datos.

Si lo prefieres, descarga manualmente el instalador desde **Releases** y ejecútalo sobre la instalación existente.

## Datos y respaldos

Todo se guarda en `%LOCALAPPDATA%\GarageDesk`:

- `mi_vehiculo.db` — base de datos SQLite (WAL activo).
- `comprobantes\` — archivos adjuntos de servicios.
- `fotos_vehiculos\` — fotos de vehículos.
- `backups_locales\` — puntos de restauración automáticos (se conservan los 15 más recientes).

GarageDesk crea un punto de restauración antes de importar paquetes o aplicar una actualización. La pestaña **Seguridad y Respaldo** permite exportar/importar un `.garagepack` (ZIP con DB + adjuntos) y elegir una carpeta de sincronización.

## Compilar desde el código

Requiere las herramientas portables de `R:\Programación\OpenCode\Herramientas`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\Compilar.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\Hacer-Respaldo.ps1"
```

`Compilar.ps1` genera:

- `release\win\GarageDesk\GarageDesk.exe`
- `release\installer\GarageDesk_Setup_<versión>.exe`
- Una copia en `R:\Programación\OpenCode\Control de Gastos -Vehículos- - Compilación\Instaladores\` con su `.sha256.txt`.

## Reglas de versión

`MAJOR.MINOR.PATCH.BUILD`

| Grado | Cuándo |
|---|---|
| MAJOR | Cambio incompatible con la versión anterior |
| MINOR | Función nueva compatible |
| PATCH | Corrección de fallos |
| BUILD | Documentación, orden, scripts, empaquetado o seguridad de proceso |

Detalle histórico en [CHANGELOG.md](CHANGELOG.md).

## Licencia

Todos los derechos reservados. Ver [LICENSE](LICENSE).
