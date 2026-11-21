; ---------------------------------------------------------------
; GarageDesk 3.1.0.1 - Instalador/actualizador para Windows 11
; Instala el PROGRAMA en C:\Program Files (x86)\GarageDesk.
; Los DATOS del usuario NO se tocan: viven en %LOCALAPPDATA%\GarageDesk
; (base de datos, fotos, comprobantes y puntos de restauración).
; El AppId es IDÉNTICO al de la 3.1 instalada: Inno Setup actualiza
; en sitio, sin desinstalar y sin borrar datos personales.
; ---------------------------------------------------------------

#define NombreApp "GarageDesk"
#define VersionApp "3.1.0.1"
#define ExeApp "GarageDesk.exe"

[Setup]
AppId={{9C7F2E1A-5B3D-4E8F-9A2C-77B1D6F04A31}
AppName={#NombreApp}
AppVersion={#VersionApp}
AppVerName={#NombreApp} {#VersionApp}
AppPublisher=GarageDesk Control Vehicular
; Migración solicitada: de Program Files a Program Files (x86)
DefaultDirName={commonpf32}\{#NombreApp}
DefaultGroupName={#NombreApp}
DisableProgramGroupPage=yes
UninstallDisplayName={#NombreApp} {#VersionApp}
UninstallDisplayIcon={app}\{#ExeApp}
SetupIconFile=Icono.ico
WizardStyle=modern
PrivilegesRequired=admin
Compression=lzma2/max
SolidCompression=yes
LZMANumBlockThreads=4
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
OutputDir=release\installer
OutputBaseFilename=GarageDesk_Setup_{#VersionApp}
VersionInfoDescription=GarageDesk - Control Vehicular
VersionInfoProductName=GarageDesk
VersionInfoProductVersion={#VersionApp}
VersionInfoVersion={#VersionApp}
; NO hay [UninstallDelete] de datos: la desinstalación tampoco borra
; la base de datos, fotos ni comprobantes del usuario.

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "release\win\GarageDesk\*"; DestDir: "{app}"; \
    Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#NombreApp}"; Filename: "{app}\{#ExeApp}"
Name: "{group}\Desinstalar {#NombreApp}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#NombreApp}"; Filename: "{app}\{#ExeApp}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#ExeApp}"; Description: "Abrir {#NombreApp}"; \
    Flags: nowait postinstall skipifsilent
