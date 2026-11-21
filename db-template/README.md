# Plantilla de base de datos vacía

`mi_vehiculo.db` contiene **únicamente la estructura** (tablas, índices y disparadores) de la base de datos de GarageDesk, sin ningún registro.

Está pensada para quien quiera partir de cero: cópiala a `%LOCALAPPDATA%\GarageDesk\mi_vehiculo.db` antes de iniciar la aplicación por primera vez. Si el archivo ya existe, **no lo reemplaces** (perderías tus datos).

Verificación: todas las tablas (`configuracion`, `recordatorios`, `registros`, `vehiculos`) tienen 0 filas y `PRAGMA integrity_check` devuelve `ok`.

Esta plantilla es pública y no contiene información personal. Tu base de datos real nunca se sube a GitHub.
