# Changelog de GarageDesk

Todas las versiones siguen el formato **MAJOR.MINOR.PATCH.BUILD**.

- **MAJOR**: cambio incompatible con la versión anterior.
- **MINOR**: función nueva compatible hacia atrás.
- **PATCH**: corrección de fallos.
- **BUILD**: documentación, orden de carpetas, scripts, empaquetado o seguridad de proceso (sin cambiar el comportamiento de la app).

La fuente de verdad de la versión es la constante `APP_VERSION` en `GarageDesk.py`.
Debe coincidir con `version_info.txt`, `instalador.iss`, el nombre del release y `index`/README.

---

## [3.1.0.1] - 2026-11-20

### Corregido
- El control de integridad y rescate de base de datos miraba la carpeta del ejecutable en lugar de `%LOCALAPPDATA%\GarageDesk`: una BD dañada nunca se recuperaba. Ahora se revisa la ruta real.
- El rescate ignoraba el resultado y podía iniciar igual sobre una BD corrupta; ahora conserva el archivo dañado (incluidos `-wal`/`-shm`) y continúa con una base limpia o restaura el mejor punto automático.
- Los diálogos de rescate antes de crear la ventana usaban `tkinter.messagebox` sin root; ahora usan `MessageBoxW` nativo de Windows.
- Las copias en caliente con WAL (`backups_locales`, nube, `.garagepack`, importación y restauración) copiaban solo el `.db` y podían perder transacciones; ahora usan `sqlite3.Connection.backup()`.
- Posible colisión de nombres de puntos de restauración creados en el mismo segundo; se añadió microsegundos al sello de tiempo.
- `sqlite3.connect` sin `busy_timeout` podía lanzar `database is locked` al abrir dos instancias; ahora usa `timeout=10` y `PRAGMA busy_timeout=5000`.
- La migración automática escaneaba directorios vecinos (incluido `Program Files` y carpetas del usuario) e importaba bases ajenas sin consentimiento; ahora solo revisa `%LOCALAPPDATA%\GarageDesk`.
- `matplotlib` solo capturaba `ImportError`; en Windows una DLL ausente lanza `OSError` e impedía el arranque.
- `confirmar_salida` silenciaba errores y podía dejar el temporizador de autoguardado activo.

### Agregado
- Buscador de actualizaciones vía GitHub Releases (`JArmandoMP/GarageDesk`), con comprobación silenciosa al iniciar y botón manual “Buscar actualizaciones”.
- Descarga del instalador previa confirmación, con verificación opcional de SHA256 publicado en el release, creación de punto de restauración y cierre limpio antes de ejecutar el instalador.
- Metadatos de versión reales en `GarageDesk.exe` (`FileVersion`/`ProductVersion` = `3.1.0.1`).
- Script `Compilar.ps1` reproducible para PyInstaller + Inno Setup.
- Plantilla vacía de base de datos en `db-template/mi_vehiculo.db` (solo estructura, 0 filas) para instalaciones desde cero; no contiene datos personales y es pública de forma segura.

### Cambiado
- Instalación migrada de `C:\Program Files\GarageDesk` a `C:\Program Files (x86)\GarageDesk`.
- El `AppId` de Inno Setup se mantuvo intacto para actualizar en sitio sin desinstalar.
- Repositorio limitado al código de GarageDesk (Python); se descartó el prototipo Electron y los archivos sensibles del proyecto anterior.
- Los datos personales siguen en `%LOCALAPPDATA%\GarageDesk` y jamás se versionan.

---

## [3.1] - 2026-11-07

- Versión original instalada (Python/CustomTkinter, PyInstaller, Inno Setup).
- Base de datos local `mi_vehiculo.db`, fotos, comprobantes, recordatorios, reportes y panel de seguridad/respaldos.
