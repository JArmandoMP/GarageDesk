import customtkinter as ctk
import sqlite3
import calendar
import contextlib
import tempfile
import webbrowser
import os
import sys
import shutil
import uuid
import html
import subprocess
import re
import unicodedata
import zipfile
import threading
from datetime import datetime, date
from pathlib import Path
from tkinter import messagebox, filedialog, Menu
from PIL import Image, ImageDraw, ImageFont
import ctypes
import hashlib
import json
import urllib.error
import urllib.request

# Gráficas (opcional). En Windows, una DLL faltante lanza OSError, no
# ImportError: capturamos ambas para que la app siempre pueda arrancar.
try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.ticker import FuncFormatter
    HAY_MATPLOTLIB = True
except (ImportError, OSError):
    HAY_MATPLOTLIB = False

# ============================================================
# VERSIONADO (fuente de verdad: MAJOR.MINOR.PATCH.BUILD)
#   3.1.0.0 = versión instalada original (3.1)
#   3.1.0.1 = primer parche: estabilidad, respaldos y updates
# ============================================================
APP_VERSION = "3.1.0.1"
UPDATE_OWNER = "JArmandoMP"
UPDATE_REPO = "GarageDesk"
UPDATE_API = f"https://api.github.com/repos/{UPDATE_OWNER}/{UPDATE_REPO}/releases/latest"
UPDATE_TIMEOUT = 10
UPDATE_USER_AGENT = f"GarageDesk/{APP_VERSION}"

# ------------------ PALETAS DE COLOR PROFESIONALES ------------------
TEMAS = {
    "Cyber Titanium": {
        "mode": "Dark",
        "app_bg": "#0F1015",
        "sidebar_bg": "#16181F",
        "sidebar_text": "#F8FAFC",
        "sidebar_icon": "#FF5E1E",
        "btn_active": "#262938",
        "panel_bg": "#1E202B",
        "card_bg": "#13141C",
        "text_title": "#FFFFFF",
        "text_sub": "#9499AA",
        "accent": "#FF5E1E",
        "accent_hover": "#E04B10",
        "accent_text": "#FFFFFF",
        "entry_bg": "#13141C",
        "entry_border": "#313545",
        "plot_bg": "#1E202B",
        "plot_text": "#F8FAFC",
        "plot_grid": "#313545",
        "plot_bar": "#FF5E1E",
        "plot_bar2": "#3B82F6",
        "plot_bar3": "#10B981",
    },
    "Obsidian Cyan": {
        "mode": "Dark",
        "app_bg": "#070A0E",
        "sidebar_bg": "#0C1118",
        "sidebar_text": "#F0FDF4",
        "sidebar_icon": "#00D2FF",
        "btn_active": "#182433",
        "panel_bg": "#141C26",
        "card_bg": "#0B1017",
        "text_title": "#F0FDF4",
        "text_sub": "#7DD3FC",
        "accent": "#00D2FF",
        "accent_hover": "#009AC4",
        "accent_text": "#070A0E",
        "entry_bg": "#0B1017",
        "entry_border": "#213042",
        "plot_bg": "#141C26",
        "plot_text": "#F0FDF4",
        "plot_grid": "#213042",
        "plot_bar": "#00D2FF",
        "plot_bar2": "#10B981",
        "plot_bar3": "#F59E0B",
    },
    "British Racing": {
        "mode": "Dark",
        "app_bg": "#09100D",
        "sidebar_bg": "#0E1914",
        "sidebar_text": "#F2FBF7",
        "sidebar_icon": "#34D399",
        "btn_active": "#182C23",
        "panel_bg": "#15241E",
        "card_bg": "#0A130F",
        "text_title": "#F2FBF7",
        "text_sub": "#A7F3D0",
        "accent": "#10B981",
        "accent_hover": "#059669",
        "accent_text": "#FFFFFF",
        "entry_bg": "#0A130F",
        "entry_border": "#233D32",
        "plot_bg": "#15241E",
        "plot_text": "#F2FBF7",
        "plot_grid": "#233D32",
        "plot_bar": "#34D399",
        "plot_bar2": "#F59E0B",
        "plot_bar3": "#06B6D4",
    },
    "Neon Violet": {
        "mode": "Dark",
        "app_bg": "#0C0A1D",
        "sidebar_bg": "#130F2D",
        "sidebar_text": "#FAF5FF",
        "sidebar_icon": "#C084FC",
        "btn_active": "#261C52",
        "panel_bg": "#1D1742",
        "card_bg": "#110D29",
        "text_title": "#FAF5FF",
        "text_sub": "#DDD6FE",
        "accent": "#8B5CF6",
        "accent_hover": "#7C3AED",
        "accent_text": "#FFFFFF",
        "entry_bg": "#110D29",
        "entry_border": "#372A70",
        "plot_bg": "#1D1742",
        "plot_text": "#FAF5FF",
        "plot_grid": "#372A70",
        "plot_bar": "#A78BFA",
        "plot_bar2": "#38BDF8",
        "plot_bar3": "#F43F5E",
    },
    "Ceramic Light": {
        "mode": "Light",
        "app_bg": "#F3F4F6",
        "sidebar_bg": "#E5E7EB",
        "sidebar_text": "#111827",
        "sidebar_icon": "#1D4ED8",
        "btn_active": "#D1D5DB",
        "panel_bg": "#FFFFFF",
        "card_bg": "#F9FAFB",
        "text_title": "#111827",
        "text_sub": "#4B5563",
        "accent": "#1D4ED8",
        "accent_hover": "#1E40AF",
        "accent_text": "#FFFFFF",
        "entry_bg": "#FFFFFF",
        "entry_border": "#D1D5DB",
        "plot_bg": "#FFFFFF",
        "plot_text": "#111827",
        "plot_grid": "#E5E7EB",
        "plot_bar": "#2563EB",
        "plot_bar2": "#0D9488",
        "plot_bar3": "#7C3AED",
    }
}

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def _familia_iconos():
    """Fuente de glifos de Windows: preferir Segoe Fluent Icons (Win11),
    si no existe usar Segoe MDL2 Assets (Win10)."""
    windir = os.getenv("WINDIR", r"C:\Windows")
    if os.path.exists(os.path.join(windir, "Fonts", "SegoeFluent-Icons.ttf")):
        return "Segoe Fluent Icons"
    return "Segoe MDL2 Assets"


FAMILIA_ICONOS = _familia_iconos()

# ---- TAMAÑOS ESTANDARIZADOS POR ROL (los glifos MDL2 dibujan ~75% del
# tamaño de punto del texto Segoe; se compensa subiendo la medida) ----
FONT_LOGO_ICON = (FAMILIA_ICONOS, 30)     # logo del sidebar
FONT_SIDEBAR_ICON = (FAMILIA_ICONOS, 19)  # navegación lateral
FONT_ACTION_ICON = (FAMILIA_ICONOS, 18)   # botones cuadrados de acción
FONT_CLIP_ICON = (FAMILIA_ICONOS, 18)     # botón de adjunto (singlón)
FONT_CAL_ICON = (FAMILIA_ICONOS, 17)      # botones de calendario
ICON_TAM_CHEVRON = 15                     # flechas del calendario emergente
ICON_TAM_AVISO = 22                       # ícono de aviso en diálogos
ICON_TAM_EMPTY = 34                       # ícono grande de estado vacío
ICON_TAM_PNG = 15                         # glifo-PNG en botones ícono+texto

# Glifos de Segoe MDL2 Assets / Fluent Icons (vectoriales, monocromáticos,
# se alinean con el texto - tabla oficial de Microsoft Learn)
ICON_CAR = "\uE804"      # Car
ICON_ADD = "\uE710"      # Add
ICON_CHART = "\uE9D2"    # AreaChart
ICON_CAL = "\uE787"      # Calendar
ICON_PRINT = "\uE749"    # Print
ICON_EDIT = "\uE70F"     # Edit
ICON_DEL = "\uE74D"      # Delete
ICON_ATTACH = "\uE723"   # Attach
ICON_PREV = "\uE76B"     # ChevronLeft
ICON_NEXT = "\uE76C"     # ChevronRight
ICON_DASH = "\uE80F"     # Home
ICON_CLEAR = "\uE894"    # Clear (limpiar/borrar filtros)
ICON_VEH = "\uE804"      # Car
ICON_BELL = "\uEA8F"     # Ringer
ICON_CHECK = "\uE73E"    # CheckMark
ICON_WARN = "\uE7BA"     # Warning
ICON_PHOTO = "\uE722"    # Camera
ICON_ZOOM = "\uE721"     # Search
ICON_GEAR = "\uE713"     # Setting
ICON_SHIELD = "\uEA18"   # Shield
ICON_HEALTH = "\uE95E"   # Health
ICON_PACKAGE = "\uE7B8"  # Package
ICON_DOWNLOAD = "\uE896" # Download

# Imágenes de glifo (para botones que mezclan ícono + texto: customtkinter
# recorta el texto si la etiqueta usa la fuente de glifos; con imagen PNG
# renderizada por PIL el glifo queda perfectamente alineado y el texto
# conserva su fuente normal). Caché por (glifo, tamaño, color).
_CACHE_ICONOS = {}


def icono_imagen(glifo, tamano=14, color="#FFFFFF"):
    """Devuelve un CTkImage con el glifo de íconos de Windows centrado."""
    from pathlib import Path as _P
    clave = (glifo, tamano, color)
    if clave in _CACHE_ICONOS:
        return _CACHE_ICONOS[clave]
    mult = 2  # renderizar a 2x para que se vea nítido en pantallas HiDPI
    px = tamano * mult
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    dc = ImageDraw.Draw(img)
    archivo = ("SegoeFluent-Icons.ttf" if FAMILIA_ICONOS == "Segoe Fluent Icons"
               else "segmdl2.ttf")
    try:
        fuente_ttf = ImageFont.truetype(
            str(_P(os.getenv("WINDIR", r"C:\Windows")) / "Fonts" / archivo), int(px * 0.86))
    except OSError:
        fuente_ttf = ImageFont.load_default()
    caja = dc.textbbox((0, 0), glifo, font=fuente_ttf)
    dc.text(((px - caja[2] - caja[0]) / 2, (px - caja[3] - caja[1]) / 2),
            glifo, font=fuente_ttf, fill=color)
    imagen = ctk.CTkImage(light_image=img, dark_image=img, size=(tamano, tamano))
    _CACHE_ICONOS[clave] = imagen
    return imagen


def _directorio_base():
    try:
        if getattr(sys, "frozen", False):
            return os.path.dirname(os.path.abspath(sys.executable))
        if sys.argv and sys.argv[0]:
            return os.path.dirname(os.path.abspath(sys.argv[0]))
    except Exception:
        pass
    return os.path.abspath(os.getcwd())


BASE_DIR = _directorio_base()

# DATOS del usuario: como .exe instalado, "Program Files" es de SOLO lectura,
# así que la BD, comprobantes, fotos y respaldos viven en %LOCALAPPDATA%\GarageDesk
# (igual que todo programa de Windows 11: los datos sobreviven a reinstalaciones
# y a desinstalar el programa). En desarrollo, todo vive junto al script.
EN_EXE = bool(getattr(sys, "frozen", False))
CARPETA_DATOS = (
    os.path.join(os.getenv("LOCALAPPDATA")
                 or os.path.join(os.path.expanduser("~"), "AppData", "Local"),
                 "GarageDesk")
    if EN_EXE else BASE_DIR
)

CARPETA_COMPROBANTES = os.path.join(CARPETA_DATOS, "comprobantes")
CARPETA_FOTOS = os.path.join(CARPETA_DATOS, "fotos_vehiculos")
CARPETA_BACKUPS = os.path.join(CARPETA_DATOS, "backups_locales")
os.makedirs(CARPETA_COMPROBANTES, exist_ok=True)
os.makedirs(CARPETA_FOTOS, exist_ok=True)
os.makedirs(CARPETA_BACKUPS, exist_ok=True)

ANIO_MIN, ANIO_MAX = 1990, 2050
LISTA_ANIOS = [str(y) for y in range(ANIO_MAX, ANIO_MIN - 1, -1)]


# ------------------ DIÁLOGOS NATIVOS Y ACTUALIZACIONES ------------------
def MessageBoxNativo(titulo, mensaje, botones=0, icono=0x40):
    """MessageBoxW de Windows: usable ANTES de crear el root de Tkinter."""
    try:
        return int(ctypes.windll.user32.MessageBoxW(
            None, str(mensaje), str(titulo), botones | icono))
    except Exception:
        return 2


def normalizar_version(texto):
    """3.1 -> (3,1,0,0); 3.1.0.1 -> (3,1,0,1)."""
    nums = [int(p) for p in re.findall(r"\d+", str(texto or ""))[:4]]
    while len(nums) < 4:
        nums.append(0)
    return tuple(nums)


def hay_version_nueva(actual, disponible):
    return normalizar_version(disponible) > normalizar_version(actual)


def consultar_ultima_version():
    """Devuelve datos del último release; None si no hay red o no hay release."""
    req = urllib.request.Request(
        UPDATE_API,
        headers={"User-Agent": UPDATE_USER_AGENT,
                 "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=UPDATE_TIMEOUT) as resp:
        datos = json.loads(resp.read().decode("utf-8"))
    tag = (datos.get("tag_name") or "").strip()
    if not tag:
        return None
    activos = [a for a in datos.get("assets", [])
               if str(a.get("name", "")).lower().endswith(".exe")]
    return {
        "version": tag.lstrip("vV"),
        "tag": tag,
        "pagina": datos.get("html_url", ""),
        "notas": datos.get("body") or "",
        "asset": activos[0] if activos else None,
    }


def hash_de_archivo(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest().upper()


LUGARES_SUGERIDOS = [
    "Agencia / Concesionario",
    "Servicio mecánico",
    "Refaccionaria",
    "Mercado Libre",
    "Amazon",
    "AutoZone",
    "Tienda de accesorios",
]

MESES_COMPLETOS = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                   "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

MESES_CORTOS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

COLORES_CATEGORIA = {
    "Mantenimiento": "#3B82F6",
    "Reparación": "#EF4444",
    "Trámites": "#10B981",
    "Verificaciones": "#8B5CF6",
    "Mejoras": "#F59E0B",
}

TIPOS_RECORDATORIO = [
    "Cambio de aceite",
    "Filtros",
    "Frenos",
    "Llantas",
    "Verificación",
    "Seguro",
    "Tenencia",
    "Servicio general",
    "Otro",
]

ESTADOS_ALERTA = {
    "vencido": (("#FEE2E2", "#7F1D1D"), ("#991B1B", "#FCA5A5"), "VENCIDO"),
    "por_vencer": (("#FEF3C7", "#78350F"), ("#92400E", "#FDE047"), "POR VENCER"),
    "ok": (("#D1FAE5", "#064E3B"), ("#065F46", "#6EE7B7"), "AL DÍA"),
}
ORDEN_ESTADO = {"ok": 0, "por_vencer": 1, "vencido": 2}

DIAS_AVISO = 30
KM_AVISO = 1000

# ------------------ SISTEMA DE CORRECCIÓN ORTOGRÁFICA ------------------
DICCIONARIO_MECANICO = [
    "aceite", "filtro", "filtros", "freno", "frenos", "balata", "balatas", "disco", "discos",
    "suspensión", "amortiguador", "amortiguadores", "bujía", "bujías", "afinación", "alineación",
    "balanceo", "batería", "acumulador", "llanta", "llantas", "neumático", "neumáticos", "rotación",
    "transmisión", "caja", "velocidades", "clutch", "embrague", "bomba", "agua", "gasolina",
    "combustible", "radiador", "anticongelante", "refrigerante", "termostato", "manguera", "mangueras",
    "banda", "distribución", "accesorios", "alternador", "marcha", "motor", "cabeza", "empaque",
    "junta", "escape", "catalizador", "sensor", "oxígeno", "revisión", "mantenimiento", "preventivo",
    "correctivo", "reparación", "servicio", "general", "mayor", "menor", "garantía", "factura", "nota",
    "taller", "agencia", "refaccionaria", "original", "cambio", "reemplazo", "instalación", "mano",
    "obra", "hojalatería", "pintura", "pulido", "encerado", "verificación", "tenencia", "seguro",
    "póliza", "refrendo", "tarjeta", "circulación", "placas", "luces", "faros", "focos", "led",
    "computadora", "diagnóstico", "escaneo", "falla", "eléctrico", "sensor", "válvula", "inyección",
    "inyectores", "líquido", "dirección", "hidráulica", "rotula", "terminal", "bielas", "pistón"
]


def quitar_tildes(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')


def distancia_levenshtein(s1, s2):
    if len(s1) < len(s2):
        return distancia_levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    anterior = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        actual = [i + 1]
        for j, c2 in enumerate(s2):
            inserciones = anterior[j + 1] + 1
            eliminaciones = actual[j] + 1
            sustituciones = anterior[j] + (c1 != c2)
            actual.append(min(inserciones, eliminaciones, sustituciones))
        anterior = actual
    return anterior[-1]


def sugerir_palabra(palabra):
    p_limpia = palabra.lower().strip()
    if not p_limpia or len(p_limpia) < 3:
        return []
    p_sin_tilde = quitar_tildes(p_limpia)

    for d in DICCIONARIO_MECANICO:
        if p_limpia == d or p_sin_tilde == quitar_tildes(d):
            return []

    candidatos = []
    for cand in DICCIONARIO_MECANICO:
        cand_sin_tilde = quitar_tildes(cand)
        dist = distancia_levenshtein(p_sin_tilde, cand_sin_tilde)
        if dist <= 2:
            candidatos.append((dist, cand))

    candidatos.sort(key=lambda x: x[0])
    return [c[1] for c in candidatos[:3]]


def activar_corrector_en_vivo(ctk_textbox, delay=350):
    tb = ctk_textbox._textbox
    try:
        tb.tag_configure("error_ortografia", underline=True, underlinefg="#EF4444")
    except Exception:
        tb.tag_configure("error_ortografia", underline=True)

    after_id = [None]
    TECLAS_IGNORADAS = {
        "Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next",
        "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
        "Caps_Lock", "Num_Lock", "F1", "F2", "F3", "F4", "F5", "F6", "F7",
        "F8", "F9", "F10", "F11", "F12",
    }

    def verificar():
        after_id[0] = None
        tb.tag_remove("error_ortografia", "1.0", "end")
        texto = tb.get("1.0", "end-1c")
        for match in re.finditer(r'\b[a-zA-ZáéíóúÁÉÍÓúñÑ]{3,}\b', texto):
            palabra = match.group()
            if sugerir_palabra(palabra):
                tb.tag_add("error_ortografia", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

    def programar(event=None):
        if getattr(event, "keysym", "") in TECLAS_IGNORADAS:
            return
        if after_id[0] is not None:
            try:
                tb.after_cancel(after_id[0])
            except Exception:
                pass
        after_id[0] = tb.after(delay, verificar)

    def mostrar_menu_contextual(event):
        idx = tb.index(f"@{event.x},{event.y}")
        try:
            linea, col = map(int, str(idx).split("."))
        except ValueError:
            return
        texto_linea = tb.get(f"{linea}.0", f"{linea}.end")

        palabra_sel = None
        ini_col, fin_col = 0, 0
        for match in re.finditer(r'\b[a-zA-ZáéíóúÁÉÍÓúñÑ]+\b', texto_linea):
            if match.start() <= col <= match.end():
                palabra_sel = match.group()
                ini_col = match.start()
                fin_col = match.end()
                break

        menu = Menu(tb, tearoff=0)
        if palabra_sel:
            sugs = sugerir_palabra(palabra_sel)
            if sugs:
                menu.add_command(label=f"Sugerencias para '{palabra_sel}':", state="disabled")
                for s in sugs:
                    def reemplazar(nueva=s, ic=ini_col, fc=fin_col, l=linea):
                        tb.delete(f"{l}.{ic}", f"{l}.{fc}")
                        tb.insert(f"{l}.{ic}", nueva)
                        verificar()
                    menu.add_command(label=f"✔ {s}", command=reemplazar)
                menu.add_separator()

        menu.add_command(label="Cortar", command=lambda: tb.event_generate("<<Cut>>"))
        menu.add_command(label="Copiar", command=lambda: tb.event_generate("<<Copy>>"))
        menu.add_command(label="Pegar", command=lambda: tb.event_generate("<<Paste>>"))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                menu.grab_release()
            except Exception:
                pass

    tb.bind("<KeyRelease>", programar)
    for seq in ("<Button-3>", "<Button-2>"):
        try:
            tb.bind(seq, mostrar_menu_contextual)
        except Exception:
            pass
    verificar()


# ------------------ MANEJO DE ARCHIVOS Y FECHAS ------------------
def abrir_archivo_sistema(ruta):
    try:
        if sys.platform.startswith("win"):
            os.startfile(ruta)
        elif sys.platform.startswith("darwin"):
            subprocess.run(["open", ruta], check=False)
        else:
            subprocess.run(["xdg-open", ruta], check=False)
    except Exception:
        webbrowser.open(f"file:///{ruta.replace(chr(92), '/')}")


FORMAS_FECHA = ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y")


def normalizar_a_iso(fecha_str):
    if not fecha_str:
        return ""
    txt = str(fecha_str).strip()
    if not txt:
        return ""
    for fmt in FORMAS_FECHA:
        try:
            return datetime.strptime(txt, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def formatear_fecha(valor):
    iso = normalizar_a_iso(valor)
    if not iso:
        return str(valor) if valor else ""
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return str(valor)


def sumar_meses(fecha_txt, meses):
    fecha_iso = normalizar_a_iso(fecha_txt)
    if not fecha_iso:
        return None
    try:
        f = datetime.strptime(fecha_iso, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
    total = f.month - 1 + int(meses)
    anio = f.year + total // 12
    mes = total % 12 + 1
    dia = min(f.day, calendar.monthrange(anio, mes)[1])
    return date(anio, mes, dia)


# ------------------ FORMATO NUMÉRICO EN ENTRADAS ------------------
def _reformatear_entry(widget, formateado):
    w = getattr(widget, "_entry", widget)
    texto_viejo = w.get()
    if formateado == texto_viejo:
        return
    try:
        pos = w.index("insert")
    except Exception:
        pos = len(texto_viejo)
    al_final = pos >= len(texto_viejo)
    previos = sum(1 for c in texto_viejo[:pos] if c.isdigit())

    w.delete(0, "end")
    w.insert(0, formateado)

    if al_final:
        w.icursor("end")
        return
    n, cursor_nuevo = 0, 0
    for i, c in enumerate(w.get()):
        if n >= previos:
            break
        if c.isdigit():
            n += 1
        cursor_nuevo = i + 1
    w.icursor(cursor_nuevo)


def _teclas_que_suelta(event):
    return getattr(event, "keysym", "") not in {
        "Left", "Right", "Up", "Down", "Home", "End", "Tab", "Shift_L", "Shift_R",
        "Control_L", "Control_R", "Alt_L", "Alt_R", "Escape",
    }


def parsear_numero(texto):
    t = str(texto).replace(" ", "").replace("\u00a0", "").replace("$", "").strip()
    if not t or not re.search(r"\d", t):
        return None
    tiene_p, tiene_c = "." in t, "," in t

    if tiene_p and tiene_c:
        sep_dec = "," if t.rfind(",") > t.rfind(".") else "."
        t = t.replace("," if sep_dec == "." else ".", "").replace(sep_dec, ".")
    elif tiene_c:
        if re.fullmatch(r"\d{1,3}(,\d{3})+", t):
            t = t.replace(",", "")
        elif t.count(",") == 1 and re.search(r",\d{1,2}$", t):
            t = t.replace(",", ".")
        else:
            t = t.replace(",", "")
    elif tiene_p:
        grupos = t.split(".")
        ultimo = grupos[-1]
        if len(grupos) >= 3:
            if len(ultimo) in (1, 2):
                t = "".join(grupos[:-1]) + "." + ultimo
            else:
                t = "".join(grupos)
        elif len(ultimo) == 3 and grupos[0] and grupos[0] not in ("0", "00"):
            t = t.replace(".", "")
    if not re.fullmatch(r"\d*\.?\d*", t) or not re.search(r"\d", t):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def parsear_entero(texto):
    valor = parsear_numero(texto)
    return None if valor is None else int(round(valor))


def asegurar_foco_al_clic(widget):
    destino = getattr(widget, "_entry", None)
    if destino is None:
        return
    def al_clic(event):
        try:
            destino.focus_set()
        except Exception:
            pass
    for sub in {id(widget), id(getattr(widget, "_canvas", widget))}:
        try:
            obj = widget if sub == id(widget) else widget._canvas
            obj.bind("<Button-1>", al_clic, add="+")
        except Exception:
            pass


def aplicar_formato_entero(entry_widget, event=None):
    if event is not None and not _teclas_que_suelta(event):
        return
    texto = str(entry_widget.get()).replace(" ", "").strip()
    if not texto or not re.search(r"\d", texto):
        return
    puro = re.sub(r"[^\d]", "", texto)
    if not puro:
        return
    if not re.search(r"[.,]", texto):
        _reformatear_entry(entry_widget, f"{int(puro):,}")
        return
    if re.search(r"[.,]\d{3}", texto) or texto[-1] in (".", ","):
        _reformatear_entry(entry_widget, f"{int(puro):,}")


def aplicar_formato_decimal(entry_widget, event=None):
    if event is not None and not _teclas_que_suelta(event):
        return
    texto = str(entry_widget.get()).replace(" ", "").replace("$", "").strip()
    if not texto or not re.search(r"\d", texto):
        return
    tiene_p, tiene_c = "." in texto, "," in texto
    entero, dec = "", ""

    if tiene_p and tiene_c:
        sep_dec = "," if texto.rfind(",") > texto.rfind(".") else "."
        miles = "." if sep_dec == "." else ","
        entero, dec = texto.rsplit(sep_dec, 1)
        entero = entero.replace(miles, "")
    elif tiene_c:
        if re.fullmatch(r"\d{1,3}(,\d{3})+", texto):
            entero = texto.replace(",", "")
        elif texto.count(",") == 1 and re.search(r",\d{1,2}$", texto):
            entero, dec = texto.rsplit(",", 1)
        else:
            entero = texto.replace(",", "")
    elif tiene_p:
        grupos = texto.split(".")
        ultimo = grupos[-1]
        if len(grupos) >= 3:
            if len(ultimo) in (1, 2):
                entero = "".join(grupos[:-1]).replace(".", ""); dec = ultimo
            else:
                entero = texto.replace(".", "")
        elif len(ultimo) == 3 and grupos[0] and grupos[0] not in ("0", "00"):
            entero = texto.replace(".", "")
        else:
            entero, dec = grupos[0], ultimo
    else:
        entero = texto

    entero = re.sub(r"[^\d]", "", entero)
    dec = re.sub(r"[^\d]", "", dec)[:2]
    if not entero and not dec:
        return
    base = f"{int(entero):,}" if entero else ("0" if dec else "")
    abre_decimal = dec == "" and texto[-1] in (".", ",")
    if dec:
        formateado = f"{base}.{dec}"
    elif abre_decimal:
        formateado = base + texto[-1]
    else:
        formateado = base
    _reformatear_entry(entry_widget, formateado)


# ------------------ SELECTOR DE CALENDARIO ------------------
class CalendarPicker(ctk.CTkToplevel):
    def __init__(self, parent, target_entry, tema=None):
        super().__init__(parent)
        self.target = target_entry
        self.tema = tema or TEMAS["Cyber Titanium"]

        val = target_entry.get().strip()
        val_iso = normalizar_a_iso(val) if val else ""
        try:
            f = datetime.strptime(val_iso, "%Y-%m-%d")
        except (ValueError, TypeError):
            f = datetime.today()

        self.y = max(ANIO_MIN, min(ANIO_MAX, f.year))
        self.m, self.sel_d = f.month, f.day

        self.title("Seleccionar Fecha")
        self.geometry("315x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkButton(
            nav, text=ICON_PREV, font=(FAMILIA_ICONOS, ICON_TAM_CHEVRON), width=28, height=28,
            fg_color=self.tema["accent"], hover_color=self.tema["accent_hover"],
            text_color=self.tema["accent_text"],
            command=lambda: self.nav_mes(-1)
        ).pack(side="left")

        centro_frame = ctk.CTkFrame(nav, fg_color="transparent")
        centro_frame.pack(side="left", expand=True)

        self.lbl_mes = ctk.CTkLabel(centro_frame, text="", font=ctk.CTkFont(size=13, weight="bold"), anchor="center")
        self.lbl_mes.pack(side="left", padx=(0, 6))

        self.combo_anio = ctk.CTkComboBox(
            centro_frame, values=LISTA_ANIOS, width=78, height=26,
            button_color=self.tema["accent"], button_hover_color=self.tema["accent_hover"],
            command=self.cambiar_anio_combo
        )
        self.combo_anio.set(str(self.y))
        self.combo_anio.pack(side="left")

        ctk.CTkButton(
            nav, text=ICON_NEXT, font=(FAMILIA_ICONOS, ICON_TAM_CHEVRON), width=28, height=28,
            fg_color=self.tema["accent"], hover_color=self.tema["accent_hover"],
            text_color=self.tema["accent_text"],
            command=lambda: self.nav_mes(1)
        ).pack(side="right")

        self.grid_frame = ctk.CTkFrame(self, corner_radius=6, fg_color=self.tema["panel_bg"])
        self.grid_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        for col_idx in range(7):
            self.grid_frame.grid_columnconfigure(col_idx, weight=1)

        self.render_cal()

    def cambiar_anio_combo(self, anio_str):
        try:
            self.y = max(ANIO_MIN, min(ANIO_MAX, int(anio_str)))
            self.render_cal()
        except (ValueError, TypeError):
            pass

    def nav_mes(self, paso):
        self.m += paso
        if self.m < 1:
            self.m = 12
            self.y -= 1
        elif self.m > 12:
            self.m = 1
            self.y += 1
        self.y = max(ANIO_MIN, min(ANIO_MAX, self.y))
        self.combo_anio.set(str(self.y))
        self.render_cal()

    def set_dia(self, d):
        self.target.delete(0, "end")
        self.target.insert(0, f"{d:02d}/{self.m:02d}/{self.y:04d}")
        self.destroy()

    def render_cal(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        self.lbl_mes.configure(text=f"{MESES_COMPLETOS[self.m]}")

        for c, nom in enumerate(["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]):
            ctk.CTkLabel(self.grid_frame, text=nom, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=("gray50", "gray70")).grid(row=0, column=c, padx=1, pady=2, sticky="nsew")

        cal = calendar.monthcalendar(self.y, self.m)
        hoy = datetime.today()

        for r_idx in range(len(cal) + 1):
            self.grid_frame.grid_rowconfigure(r_idx, weight=1)

        for r, sem in enumerate(cal, 1):
            for c, dia in enumerate(sem):
                if dia:
                    es_hoy = (dia == hoy.day and self.m == hoy.month and self.y == hoy.year)
                    es_sel = (dia == self.sel_d)

                    if es_sel:
                        fg = self.tema["accent"]
                        txt_col = self.tema["accent_text"]
                    elif es_hoy:
                        fg = self.tema["btn_active"]
                        txt_col = self.tema["sidebar_icon"]
                    else:
                        fg = self.tema["card_bg"]
                        txt_col = self.tema["sidebar_text"]

                    btn = ctk.CTkButton(
                        self.grid_frame, text=str(dia), width=32, height=26,
                        fg_color=fg, text_color=txt_col, font=ctk.CTkFont(size=11, weight="bold"),
                        hover_color=self.tema["accent_hover"],
                        command=lambda d=dia: self.set_dia(d)
                    )
                    btn.grid(row=r, column=c, padx=1, pady=1, sticky="nsew")


# ------------------ BASE DE DATOS LOCAL + RECUPERACIÓN AUTOMÁTICA ------------------
class DBManager:
    DEMO_TAG = "Registro de demostración"

    def __init__(self, db_name="mi_vehiculo.db"):
        self.db_name = os.path.join(CARPETA_DATOS, db_name)
        # quick_check antes de tocar nada: el arranque ya habrá restaurado
        # una copia si estaba dañada. Si aún falla, avisamos al usuario.
        with contextlib.closing(self._conectar()) as con:
            estado = con.execute("PRAGMA quick_check;").fetchone()
        if not estado or estado[0] != "ok":
            raise sqlite3.DatabaseError(f"Integridad de base de datos: {estado}")
        self._crear_esquema()
        self.resumen_migracion = self.migrar_datos_externos()

    def _conectar(self):
        con = sqlite3.connect(self.db_name, timeout=10)
        con.execute("PRAGMA busy_timeout = 5000;")
        con.execute("PRAGMA foreign_keys = ON;")
        return con

    def _crear_esquema(self):
        with contextlib.closing(self._conectar()) as con, con:
            con.execute("PRAGMA journal_mode = WAL;")

            con.execute("""
                CREATE TABLE IF NOT EXISTS configuracion (
                    clave TEXT PRIMARY KEY,
                    valor TEXT
                )
            """)

            con.execute("""
                CREATE TABLE IF NOT EXISTS vehiculos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    anio INTEGER,
                    placas TEXT,
                    notas TEXT,
                    foto_path TEXT,
                    fecha_compra TEXT,
                    km_inicial INTEGER,
                    precio_compra REAL
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS registros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    vehiculo TEXT,
                    vehiculo_id INTEGER,
                    modelo INTEGER,
                    tipo TEXT NOT NULL,
                    kilometraje INTEGER,
                    costo REAL,
                    descripcion TEXT,
                    taller_lugar TEXT,
                    notas TEXT,
                    comprobante_path TEXT,
                    FOREIGN KEY(vehiculo_id) REFERENCES vehiculos(id) ON DELETE SET NULL
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS recordatorios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehiculo_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    intervalo_km INTEGER,
                    intervalo_meses INTEGER,
                    ultima_fecha TEXT,
                    ultimo_km INTEGER,
                    notas TEXT,
                    FOREIGN KEY(vehiculo_id) REFERENCES vehiculos(id) ON DELETE CASCADE
                )
            """)

            columnas_veh = [col[1] for col in con.execute("PRAGMA table_info(vehiculos)").fetchall()]
            for col_sql in (
                "ALTER TABLE vehiculos ADD COLUMN foto_path TEXT",
                "ALTER TABLE vehiculos ADD COLUMN fecha_compra TEXT",
                "ALTER TABLE vehiculos ADD COLUMN km_inicial INTEGER",
                "ALTER TABLE vehiculos ADD COLUMN precio_compra REAL",
            ):
                nombre_col = col_sql.split("ADD COLUMN ")[1].split()[0]
                if nombre_col not in columnas_veh:
                    con.execute(col_sql)

            columnas_reg = [col[1] for col in con.execute("PRAGMA table_info(registros)").fetchall()]
            for col_sql in (
                "ALTER TABLE registros ADD COLUMN vehiculo_id INTEGER",
                "ALTER TABLE registros ADD COLUMN modelo INTEGER",
                "ALTER TABLE registros ADD COLUMN comprobante_path TEXT",
            ):
                nombre_col = col_sql.split("ADD COLUMN ")[1].split()[0]
                if nombre_col not in columnas_reg:
                    con.execute(col_sql)

            con.execute("CREATE INDEX IF NOT EXISTS idx_reg_vehiculo ON registros(vehiculo_id)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_reg_fecha ON registros(fecha)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_rec_vehiculo ON recordatorios(vehiculo_id)")

    def query(self, sql, params=()):
        with contextlib.closing(self._conectar()) as con:
            cur = con.execute(sql, params)
            return cur.fetchall()

    def execute(self, sql, params=()):
        with contextlib.closing(self._conectar()) as con, con:
            con.execute(sql, params)

    def execute_insert(self, sql, params=()):
        with contextlib.closing(self._conectar()) as con, con:
            cur = con.execute(sql, params)
            return cur.lastrowid

    def obtener_config(self, clave, default=None):
        filas = self.query("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
        return filas[0][0] if filas else default

    def guardar_config(self, clave, valor):
        self.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)", (clave, str(valor)))

    def obtener_o_crear_vehiculo(self, nombre, anio=None):
        nombre = (nombre or "").strip() or "General"
        filas = self.query("SELECT id FROM vehiculos WHERE nombre = ? COLLATE NOCASE", (nombre,))
        if filas:
            vid = filas[0][0]
            if anio:
                self.execute("UPDATE vehiculos SET anio = ? WHERE id = ? AND anio IS NULL", (anio, vid))
            return vid
        return self.execute_insert("INSERT INTO vehiculos (nombre, anio) VALUES (?, ?)", (nombre, anio))

    def nombre_vehiculo(self, vehiculo_id):
        if vehiculo_id is None:
            return "General"
        filas = self.query("SELECT nombre FROM vehiculos WHERE id = ?", (vehiculo_id,))
        return filas[0][0] if filas else "General"

    def migrar_datos_externos(self):
        resumen = {"vehiculos": 0, "registros": 0, "recordatorios": 0, "fuentes": [], "respaldo": ""}

        if self.obtener_config("migracion_datos_completada"):
            return resumen

        propios = sum(int(self.query(f"SELECT COUNT(*) FROM {t}")[0][0] or 0)
                      for t in ("vehiculos", "registros", "recordatorios"))

        if propios == 0:
            resumen["respaldo"] = self._crear_respaldo()
            for ruta, con, tabs, cols in self._fuentes_externas():
                try:
                    nv, nr, nm = self._importar_fuente(ruta, con, tabs, cols)
                finally:
                    try:
                        con.close()
                    except Exception:
                        pass
                if nv + nr + nm > 0:
                    resumen["vehiculos"] += nv
                    resumen["registros"] += nr
                    resumen["recordatorios"] += nm
                    resumen["fuentes"].append(os.path.basename(os.path.dirname(ruta)) or ruta)
                    break

        self.guardar_config("migracion_datos_completada", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return resumen

    def _crear_respaldo(self):
        try:
            nombre = f"mi_vehiculo_previo_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.db"
            destino = os.path.join(CARPETA_DATOS, nombre)
            if os.path.exists(self.db_name):
                with contextlib.closing(sqlite3.connect(self.db_name)) as src, \
                     contextlib.closing(sqlite3.connect(destino)) as dst:
                    src.backup(dst)
            return nombre
        except Exception:
            return ""

    def _rutas_bd_candidatas(self):
        excluidas = {"venv", "__pycache__", "node_modules", "site-packages",
                     "build", ".git", ".vscode", ".idea", "$recycle.bin", "backups_locales"}
        # Nunca escanear directorios vecinos: en Program Files sería lento
        # y podía importar bases ajenas sin consentimiento del usuario.
        bases = [CARPETA_DATOS]
        rutas = []
        vistas = set()

        for base in bases:
            if not base or not os.path.isdir(base):
                continue
            for dirpath, dirs, files in os.walk(base, topdown=True):
                rel = os.path.relpath(dirpath, base)
                profundidad = 0 if rel == "." else rel.count(os.sep) + 1
                if profundidad >= 2:
                    dirs[:] = []
                dirs[:] = [d for d in dirs if d.lower() not in excluidas and not d.startswith(".")]
                for f in files:
                    low = f.lower()
                    if (low.endswith((".db", ".sqlite", ".sqlite3"))
                            and not low.endswith(("-wal", "-shm"))
                            and not low.startswith("mi_vehiculo_previo")):
                        p = os.path.abspath(os.path.join(dirpath, f))
                        if p == os.path.abspath(self.db_name) or p in vistas:
                            continue
                        try:
                            if os.path.getsize(p) > 8 * 1024 * 1024:
                                continue
                        except OSError:
                            continue
                        vistas.add(p)
                        rutas.append(p)

        rutas.sort(key=lambda p: (os.path.getmtime(p) if os.path.exists(p) else 0), reverse=True)
        return rutas

    def _fuentes_externas(self):
        ruta_actual = os.path.abspath(self.db_name).lower()

        for ruta in self._rutas_bd_candidatas():
            if os.path.abspath(ruta).lower() == ruta_actual:
                continue
            con = None
            try:
                con = sqlite3.connect(Path(ruta).as_uri() + "?mode=ro", uri=True)
                tabs = {f[0] for f in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}

                if "vehiculos" not in tabs or ("registros" not in tabs and "recordatorios" not in tabs):
                    continue
                cols = {}
                for t in ("vehiculos", "registros", "recordatorios"):
                    if t in tabs:
                        cols[t] = [c[1] for c in con.execute(f"PRAGMA table_info({t})").fetchall()]
                if "nombre" not in cols.get("vehiculos", []):
                    continue

                hay_datos = any(
                    con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] > 0
                    for t in ("vehiculos", "registros", "recordatorios") if t in tabs
                )
                if not hay_datos:
                    continue

                if "registros" in tabs and "notas" in cols.get("registros", []):
                    demo = con.execute(
                        "SELECT COUNT(*) FROM registros WHERE TRIM(COALESCE(notas, '')) = ?",
                        (self.DEMO_TAG,)
                    ).fetchone()[0]
                    if demo:
                        continue

                yield ruta, con, tabs, cols
            except Exception:
                if con is not None:
                    try:
                        con.close()
                    except Exception:
                        pass

    def _importar_fuente(self, ruta, con, tabs, cols):
        carpeta = os.path.dirname(ruta)
        mapa_veh, nv = self._importar_vehiculos_fuente(con, cols["vehiculos"], carpeta)
        nr = self._importar_registros_fuente(con, cols.get("registros", []), carpeta, mapa_veh) if "registros" in tabs else 0
        nm = self._importar_recordatorios_fuente(con, cols.get("recordatorios", []), mapa_veh) if "recordatorios" in tabs else 0
        return nv, nr, nm

    def _importar_vehiculos_fuente(self, con, cols_v, carpeta_fuente):
        mapa = {}
        nv = 0
        for fila in con.execute("SELECT * FROM vehiculos"):
            d = dict(zip(cols_v, fila))
            nombre = str(d.get("nombre") or d.get("alias") or "").strip()
            if not nombre:
                continue

            existentes = self.query("SELECT id FROM vehiculos WHERE nombre = ? COLLATE NOCASE", (nombre,))
            if existentes:
                vid = existentes[0][0]
                dest_actual = dict(zip(
                    ("anio", "placas", "notas", "foto_path", "fecha_compra", "km_inicial", "precio_compra"),
                    self.query(
                        "SELECT anio, placas, notas, foto_path, fecha_compra, km_inicial, precio_compra "
                        "FROM vehiculos WHERE id = ?", (vid,)
                    )[0]
                ))
                nuevos = {c: d[c] for c in dest_actual if dest_actual[c] is None and d.get(c) is not None}
                if nuevos:
                    sets = ", ".join(f"{c} = ?" for c in nuevos)
                    self.execute(f"UPDATE vehiculos SET {sets} WHERE id = ?", tuple(nuevos.values()) + (vid,))
            else:
                vid = self.execute_insert(
                    "INSERT INTO vehiculos (nombre, anio, placas, notas, foto_path, fecha_compra, km_inicial, precio_compra) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (nombre, d.get("anio"), d.get("placas"), d.get("notas"), d.get("foto_path"),
                     d.get("fecha_compra"), d.get("km_inicial"), d.get("precio_compra"))
                )
                nv += 1

            foto = d.get("foto_path")
            if foto:
                self._copiar_adjunto(carpeta_fuente, "fotos_vehiculos", foto, CARPETA_FOTOS)

            if d.get("id") is not None:
                mapa[d["id"]] = vid
        return mapa, nv

    def _importar_registros_fuente(self, con, cols_r, carpeta_fuente, mapa_veh):
        nr = 0
        for fila in con.execute("SELECT * FROM registros"):
            d = dict(zip(cols_r, fila))

            fecha_iso = normalizar_a_iso(d.get("fecha"))
            if not fecha_iso:
                continue

            tipo = str(d.get("tipo") or "Sin categoría").strip() or "Sin categoría"
            try:
                costo = float(d.get("costo") or 0)
            except (TypeError, ValueError):
                costo = 0.0
            try:
                km = int(d.get("kilometraje")) if d.get("kilometraje") is not None else 0
            except (TypeError, ValueError):
                km = 0
            desc = str(d.get("descripcion") or "")
            taller = str(d.get("taller_lugar") or "")
            notas = str(d.get("notas") or "")

            modelo = None
            if d.get("modelo") is not None:
                try:
                    modelo = int(d["modelo"])
                except (TypeError, ValueError):
                    modelo = None

            vid = None
            if d.get("vehiculo_id") is not None and d["vehiculo_id"] in mapa_veh:
                vid = mapa_veh[d["vehiculo_id"]]
            nombre_txt = str(d.get("vehiculo") or "").strip()
            if vid is None and nombre_txt:
                vid = self.obtener_o_crear_vehiculo(nombre_txt)
            veh_nombre = self.nombre_vehiculo(vid) if vid else "General"

            ya_existe = self.query(
                "SELECT 1 FROM registros WHERE fecha = ? AND COALESCE(tipo,'') = ? "
                "AND COALESCE(kilometraje,0) = ? AND COALESCE(costo,0) = ? "
                "AND COALESCE(descripcion,'') = ? AND COALESCE(taller_lugar,'') = ? LIMIT 1",
                (fecha_iso, tipo, km, costo, desc, taller)
            )
            if ya_existe:
                continue

            comp = d.get("comprobante_path") if "comprobante_path" in cols_r else None
            if comp:
                self._copiar_adjunto(carpeta_fuente, "comprobantes", comp, CARPETA_COMPROBANTES)

            self.execute_insert(
                "INSERT INTO registros (fecha, vehiculo, vehiculo_id, modelo, tipo, kilometraje, costo, "
                "descripcion, taller_lugar, notas, comprobante_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (fecha_iso, veh_nombre, vid, modelo, tipo, km, costo, desc, taller, notas, comp)
            )
            nr += 1
        return nr

    def _importar_recordatorios_fuente(self, con, cols_rec, mapa_veh):
        nm = 0
        for fila in con.execute("SELECT * FROM recordatorios"):
            d = dict(zip(cols_rec, fila))
            vid = mapa_veh.get(d.get("vehiculo_id")) if d.get("vehiculo_id") is not None else None
            if vid is None:
                continue
            tipo = str(d.get("tipo") or "").strip()
            if not tipo:
                continue
            ya_existe = self.query(
                "SELECT 1 FROM recordatorios WHERE vehiculo_id = ? AND tipo = ? "
                "AND COALESCE(intervalo_km,-1) = COALESCE(?,-1) "
                "AND COALESCE(intervalo_meses,-1) = COALESCE(?,-1) LIMIT 1",
                (vid, tipo, d.get("intervalo_km"), d.get("intervalo_meses"))
            )
            if ya_existe:
                continue
            self.execute_insert(
                "INSERT INTO recordatorios (vehiculo_id, tipo, intervalo_km, intervalo_meses, "
                "ultima_fecha, ultimo_km, notas) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (vid, tipo, d.get("intervalo_km"), d.get("intervalo_meses"),
                 normalizar_a_iso(d.get("ultima_fecha")) or None,
                 d.get("ultimo_km"), d.get("notas"))
            )
            nm += 1
        return nm

    def _copiar_adjunto(self, carpeta_fuente, subcarpeta, nombre_archivo, carpeta_destino):
        if not nombre_archivo:
            return False
        destino = os.path.join(carpeta_destino, os.path.basename(nombre_archivo))
        if os.path.exists(destino):
            return True
        origen = os.path.join(carpeta_fuente, subcarpeta, os.path.basename(nombre_archivo))
        try:
            if os.path.exists(origen):
                shutil.copy2(origen, destino)
                return True
        except OSError:
            pass
        return False


# ------------------ SISTEMA DE SEGURIDAD, RESPALDO Y TOLERANCIA A FALLOS ------------------
class SecurityManager:
    def __init__(self, db_manager, app_instance=None):
        self.db = db_manager
        self.app = app_instance
        self._timer = None
        self._detener_timer = threading.Event()
        self.iniciar_autoguardado()

    @classmethod
    def verificar_integridad_archivo(cls, db_path):
        if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
            return True, "Base de datos nueva o inicial."
        try:
            with contextlib.closing(sqlite3.connect(db_path, timeout=10)) as con:
                cursor = con.execute("PRAGMA integrity_check;")
                res = cursor.fetchall()
                if res and res[0][0] == "ok":
                    return True, "Integridad correcta (OK)."
                return False, f"Problemas detectados: {res}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def _renombrar_db_danada(db_path):
        """Renombra .db, -wal y -shm juntos: un WAL viejo no debe
        reaplicarse a la base recién creada o restaurada."""
        sello = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        for sufijo in ("", "-wal", "-shm"):
            ruta = db_path + sufijo
            if os.path.exists(ruta):
                try:
                    shutil.move(ruta, ruta + f".corrupto_{sello}")
                except OSError:
                    pass

    @classmethod
    def rescatar_arranque_fallido(cls, parent_root, db_path):
        es_valida, error = cls.verificar_integridad_archivo(db_path)
        if es_valida:
            return True

        candidatos = []
        if os.path.exists(CARPETA_BACKUPS):
            for f in os.listdir(CARPETA_BACKUPS):
                if f.endswith(".db"):
                    p = os.path.join(CARPETA_BACKUPS, f)
                    candidatos.append((os.path.getmtime(p), p))
        candidatos.sort(reverse=True)

        msj = (
            "GarageDesk detectó que la base de datos se cerró de forma incorrecta o sufrió daños.\n\n"
            f"Diagnóstico técnico: {error}\n\n"
        )

        if not candidatos:
            MessageBoxNativo(
                "Error crítico",
                msj + "No se encontraron copias automáticas locales. Se conservará el archivo dañado renombrado y se creará una base en blanco.",
                0, 0x10)
            cls._renombrar_db_danada(db_path)
            return True

        mejor_copia = candidatos[0][1]
        fecha_copia = datetime.fromtimestamp(candidatos[0][0]).strftime("%d/%m/%Y %H:%M:%S")
        msj += (
            f"Se encontró una copia limpia automática del:\n📅 {fecha_copia}\n\n"
            "¿Deseas restaurarla ahora para iniciar el programa con normalidad?"
        )

        # 4 = SÍ/NO, 0x31 = advertencia + botón por defecto = NO
        if MessageBoxNativo("Recuperación de Sistema", msj, 4, 0x31) == 6:
            try:
                cls._renombrar_db_danada(db_path)
                with contextlib.closing(sqlite3.connect(mejor_copia)) as src, \
                     contextlib.closing(sqlite3.connect(db_path)) as dst:
                    src.backup(dst)
                return True
            except Exception as ex:
                MessageBoxNativo("Error al restaurar",
                                 f"No se pudo completar la restauración: {ex}", 0, 0x10)
        else:
            MessageBoxNativo("Recuperación de Sistema",
                             "No se restauró la copia. Se conservará el archivo dañado renombrado y se creará una base en blanco.",
                             0, 0x30)
        cls._renombrar_db_danada(db_path)
        return True

    def crear_punto_restauracion(self, silencioso=False):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        nombre = f"respaldo_{timestamp}.db"
        destino = os.path.join(CARPETA_BACKUPS, nombre)

        try:
            with contextlib.closing(sqlite3.connect(self.db.db_name, timeout=10)) as src, \
                 contextlib.closing(sqlite3.connect(destino)) as dst:
                src.backup(dst)

            ruta_nube = self.db.obtener_config("ruta_carpeta_nube", "")
            if ruta_nube and os.path.isdir(ruta_nube):
                threading.Thread(
                    target=self._empaquetar_a_nube,
                    args=(ruta_nube, timestamp),
                    daemon=True
                ).start()

            self._limpiar_backups_antiguos()

            if not silencioso and self.app:
                messagebox.showinfo("Punto Creado", f"Punto de restauración generado correctamente:\n{nombre}", parent=self.app)
            return True, destino
        except Exception as e:
            if not silencioso and self.app:
                messagebox.showerror("Error de respaldo", f"No se pudo crear la copia: {e}", parent=self.app)
            return False, str(e)

    def eliminar_punto_restauracion(self, nombre_archivo):
        try:
            ruta = os.path.join(CARPETA_BACKUPS, nombre_archivo)
            if os.path.exists(ruta):
                os.remove(ruta)
                return True, "Archivo eliminado correctamente."
            return False, "El archivo de respaldo no existe."
        except OSError as e:
            return False, str(e)

    def _limpiar_backups_antiguos(self, max_copias=15):
        try:
            archivos = [
                os.path.join(CARPETA_BACKUPS, f) for f in os.listdir(CARPETA_BACKUPS)
                if f.endswith(".db")
            ]
            if len(archivos) > max_copias:
                archivos.sort(key=os.path.getmtime)
                for eliminar in archivos[:-max_copias]:
                    os.remove(eliminar)
        except OSError:
            pass

    def _copia_db_para_zip(self, zf):
        """Copia coherente (backup API) de una BD con WAL activo."""
        tmp = os.path.join(tempfile.gettempdir(), f"gd_zip_{uuid.uuid4().hex}.db")
        try:
            with contextlib.closing(sqlite3.connect(self.db.db_name, timeout=10)) as src, \
                 contextlib.closing(sqlite3.connect(tmp)) as dst:
                src.backup(dst)
            zf.write(tmp, "mi_vehiculo.db")
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass

    def _agregar_carpetas_al_zip(self, zf):
        for carpeta, nombre_en_zip in ((CARPETA_COMPROBANTES, "comprobantes"),
                                       (CARPETA_FOTOS, "fotos_vehiculos")):
            if os.path.isdir(carpeta):
                for f in os.listdir(carpeta):
                    ruta = os.path.join(carpeta, f)
                    if os.path.isfile(ruta):
                        zf.write(ruta, os.path.join(nombre_en_zip, f))

    def _empaquetar_a_nube(self, destino_nube, timestamp):
        zip_path = os.path.join(destino_nube, f"GarageDesk_Sync_{timestamp}.zip")
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                if os.path.exists(self.db.db_name):
                    self._copia_db_para_zip(zf)
                self._agregar_carpetas_al_zip(zf)
        except Exception:
            pass

    def exportar_paquete_completo(self, ruta_archivo):
        try:
            with zipfile.ZipFile(ruta_archivo, "w", zipfile.ZIP_DEFLATED) as zf:
                if os.path.exists(self.db.db_name):
                    self._copia_db_para_zip(zf)
                self._agregar_carpetas_al_zip(zf)
            return True, "Paquete exportado exitosamente."
        except Exception as e:
            return False, str(e)

    def importar_paquete_completo(self, ruta_archivo):
        try:
            self.crear_punto_restauracion(silencioso=True)

            with tempfile.TemporaryDirectory() as tmp_dir:
                with zipfile.ZipFile(ruta_archivo, "r") as zf:
                    zf.extractall(tmp_dir)

                db_tmp = os.path.join(tmp_dir, "mi_vehiculo.db")
                if not os.path.exists(db_tmp):
                    return False, "El archivo no contiene una base de datos válida de GarageDesk."

                with contextlib.closing(sqlite3.connect(db_tmp)) as src, \
                     contextlib.closing(sqlite3.connect(self.db.db_name, timeout=10)) as dst:
                    src.backup(dst)

                comp_tmp = os.path.join(tmp_dir, "comprobantes")
                if os.path.exists(comp_tmp):
                    for f in os.listdir(comp_tmp):
                        shutil.copy2(os.path.join(comp_tmp, f), os.path.join(CARPETA_COMPROBANTES, f))

                fotos_tmp = os.path.join(tmp_dir, "fotos_vehiculos")
                if os.path.exists(fotos_tmp):
                    for f in os.listdir(fotos_tmp):
                        shutil.copy2(os.path.join(fotos_tmp, f), os.path.join(CARPETA_FOTOS, f))

            return True, "Paquete restaurado completamente con éxito."
        except Exception as e:
            return False, str(e)

    def iniciar_autoguardado(self):
        frecuencia = self.db.obtener_config("frecuencia_respaldo", "Cada 30 min")
        intervalos = {
            "Cada 15 min": 15 * 60,
            "Cada 30 min": 30 * 60,
            "Solo al cerrar": 0
        }
        segundos = intervalos.get(frecuencia, 1800)

        if self._timer:
            self._timer.cancel()

        if segundos > 0:
            def ciclo():
                if not self._detener_timer.is_set():
                    self.crear_punto_restauracion(silencioso=True)
                    self._timer = threading.Timer(segundos, ciclo)
                    self._timer.daemon = True
                    self._timer.start()

            self._timer = threading.Timer(segundos, ciclo)
            self._timer.daemon = True
            self._timer.start()

    def detener(self):
        self._detener_timer.set()
        if self._timer:
            self._timer.cancel()


# ------------------ APLICACIÓN PRINCIPAL ------------------
class ModernApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.security = SecurityManager(self.db, self)
        self.resumen_migracion = self.db.resumen_migracion

        tema_guardado = self.db.obtener_config("tema_actual", "Cyber Titanium")
        self.nombre_tema_actual = tema_guardado if tema_guardado in TEMAS else "Cyber Titanium"
        self.tema_actual = TEMAS[self.nombre_tema_actual]

        self.title(f"GarageDesk • Control Vehicular v{APP_VERSION}")

        # Ícono de ventana y barra de tareas: usa el .ico junto al programa.
        _dirs_ico = [BASE_DIR]
        if EN_EXE:
            # PyInstaller 6 guarda los datos junto al exe, en "_internal".
            _dirs_ico.append(os.path.join(BASE_DIR, "_internal"))
        for _dir in _dirs_ico:
            for _nombre in ("Icono.ico", "GarageDesk.ico", "icono.ico"):
                _ruta_ico = os.path.join(_dir, _nombre)
                if os.path.exists(_ruta_ico):
                    try:
                        self.iconbitmap(_ruta_ico)
                    except Exception:
                        pass
                    break
            else:
                continue
            break

        ancho_app, alto_app = 1120, 780
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        pos_x = max(0, int((sw - ancho_app) / 2))
        pos_y = max(0, int((sh - alto_app) / 2))
        self.geometry(f"{ancho_app}x{alto_app}+{pos_x}+{pos_y}")
        self.minsize(980, 640)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.badges = {
            "Mantenimiento": (("#DBEAFE", "#1E3A8A"), ("#1E40AF", "#93C5FD")),
            "Reparación": (("#FEE2E2", "#7F1D1D"), ("#991B1B", "#FCA5A5")),
            "Trámites": (("#D1FAE5", "#064E3B"), ("#065F46", "#6EE7B7")),
            "Verificaciones": (("#EDE9FE", "#4C1D95"), ("#6D28D9", "#C4B5FD")),
            "Mejoras": (("#FEF3C7", "#78350F"), ("#92400E", "#FDE047"))
        }

        self.ruta_comprobante_temporal = None
        self.vista_actual = "captura"

        self.setup_sidebar()
        self.setup_views()
        self.aplicar_tema_completo(self.nombre_tema_actual)

        self.protocol("WM_DELETE_WINDOW", self.confirmar_salida)

        if self.resumen_migracion["fuentes"]:
            self.after(500, self.mostrar_resumen_migracion)
        self.after(1100, self.chequear_alertas_inicio)
        # Consulta silenciosa: solo interrumpe si realmente hay versión nueva.
        self.after(2500, lambda: self.buscar_actualizaciones(silencioso=True))

    # ------------------ ACTUALIZACIONES VÍA GITHUB RELEASES ------------------
    def buscar_actualizaciones(self, silencioso=False):
        def worker():
            try:
                info = consultar_ultima_version()
            except Exception:
                info = None
            self.after(0, lambda: self._responder_actualizacion(info, silencioso))

        threading.Thread(target=worker, daemon=True).start()

    def _responder_actualizacion(self, info, silencioso):
        if not info:
            if not silencioso:
                messagebox.showinfo(
                    "Actualizaciones",
                    "No se pudo consultar GitHub Releases.\nRevisa tu conexión e inténtalo de nuevo.",
                    parent=self)
            return
        if not hay_version_nueva(APP_VERSION, info["version"]):
            if not silencioso:
                messagebox.showinfo(
                    "Actualizaciones",
                    f"Ya tienes la versión más reciente ({APP_VERSION}).", parent=self)
            return
        notas = (info.get("notas") or "").strip()
        if len(notas) > 900:
            notas = notas[:900] + "\n..."
        texto = (f"Hay una versión nueva de GarageDesk.\n\n"
                 f"Instalada: {APP_VERSION}\nDisponible: {info['version']}\n\n"
                 f"{notas}\n\n¿Descargar e instalar ahora?")
        if MessageBoxNativo("GarageDesk · Actualización disponible", texto, 4, 0x40) == 6:
            self.descargar_actualizacion(info)

    def descargar_actualizacion(self, info):
        asset = info.get("asset")
        if not asset:
            MessageBoxNativo(
                "Actualización",
                "El release no contiene un instalador .exe. Se abrirá la página de descarga.",
                0, 0x40)
            if info.get("pagina"):
                webbrowser.open(info["pagina"])
            return
        nombre = asset.get("name") or "GarageDesk_Setup.exe"
        destino = os.path.join(tempfile.gettempdir(), nombre)
        try:
            req = urllib.request.Request(
                asset["browser_download_url"], headers={"User-Agent": UPDATE_USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as respuesta, \
                 open(destino, "wb") as salida:
                shutil.copyfileobj(respuesta, salida)
        except Exception as e:
            MessageBoxNativo("Error de descarga",
                             f"No se pudo descargar el instalador:\n{e}", 0, 0x10)
            return

        esperado = re.search(r"(?i)sha256\s*[:\-]?\s*([0-9a-f]{64})",
                             info.get("notas") or "")
        if esperado:
            real = hash_de_archivo(destino)
            if real != esperado.group(1).upper():
                MessageBoxNativo("Actualización",
                                 "El SHA256 del instalador no coincide. No se ejecutará.",
                                 0, 0x10)
                return

        mensaje = ("El instalador se descargó correctamente.\n\n"
                   f"Archivo: {destino}\n\n"
                   "Se ejecutará ahora y Windows puede pedir permiso de administrador (UAC).\n"
                   "Tus datos personales NO se eliminan.\n\n¿Continuar?")
        if MessageBoxNativo("Instalar actualización", mensaje, 4, 0x40) != 6:
            return
        try:
            self.security.crear_punto_restauracion(silencioso=True)
            self.security.detener()
        except Exception:
            pass
        try:
            os.startfile(destino)
        except Exception:
            MessageBoxNativo(
                "Actualización",
                f"No se pudo iniciar el instalador. Ejecútalo manualmente:\n{destino}",
                0, 0x40)
            return
        self.after(500, self.destroy)

    def mostrar_resumen_migracion(self):
        r = self.resumen_migracion
        if not r["fuentes"]:
            return
        fuentes = ", ".join(r["fuentes"])
        texto = (
            "Se recuperaron los datos de una instalación anterior.\n\n"
            f"Fuente encontrada: {fuentes}\n"
            f"• {r['vehiculos']} vehículo(s)\n"
            f"• {r['registros']} registro(s) de servicio\n"
            f"• {r['recordatorios']} recordatorio(s)\n"
        )
        if r["respaldo"]:
            texto += f"\nSe creó un respaldo previo: {r['respaldo']}\n"
        texto += "\nTodo quedó guardado en la base de datos de esta carpeta."
        messagebox.showinfo("Recuperación de datos", texto, parent=self)

    def confirmar_salida(self):
        m = ctk.CTkToplevel(self)
        m.title("Confirmar salida")
        m.geometry("400x200")
        m.resizable(False, False)
        m.grab_set()
        m.transient(self)

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        px = max(0, int((sw - 400) / 2))
        py = max(0, int((sh - 200) / 2))
        m.geometry(f"400x200+{px}+{py}")

        p = ctk.CTkFrame(m, corner_radius=12, fg_color=self.tema_actual["panel_bg"])
        p.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(
            p, text=f"{ICON_WARN}  Guardar y Salir",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=self.tema_actual["accent"]
        ).pack(pady=(16, 6))

        ctk.CTkLabel(
            p, text="¿Deseas guardar los cambios y la configuración\ndel sistema antes de salir del programa?",
            font=ctk.CTkFont(size=12),
            text_color=self.tema_actual["sidebar_text"],
            justify="center"
        ).pack(pady=(0, 22))

        btn_box = ctk.CTkFrame(p, fg_color="transparent")
        btn_box.pack(fill="x", padx=25)

        def aceptar():
            try:
                self.db.guardar_config("tema_actual", self.nombre_tema_actual)
                if self.db.obtener_config("frecuencia_respaldo") == "Solo al cerrar":
                    self.security.crear_punto_restauracion(silencioso=True)
            except Exception as exc:
                MessageBoxNativo("GarageDesk",
                                 f"No se pudo guardar la configuración:\n{exc}", 0, 0x30)
            finally:
                try:
                    self.security.detener()
                except Exception:
                    pass
            m.destroy()
            self.destroy()

        def cancelar():
            m.destroy()

        ctk.CTkButton(
            btn_box, text="Aceptar", width=120, height=36, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"], command=aceptar
        ).pack(side="left", expand=True, padx=6)

        ctk.CTkButton(
            btn_box, text="Cancelar", width=120, height=36, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#64748B", "#475569"), hover_color=("#475569", "#334155"),
            text_color="#FFFFFF", command=cancelar
        ).pack(side="left", expand=True, padx=6)

    def vincular_tab(self, controles):
        color_borde_foco = self.tema_actual["accent"]
        color_borde_normal = self.tema_actual["entry_border"]

        for idx, widget in enumerate(controles):
            def on_focus_in(event, w=widget):
                try:
                    w.configure(border_color=color_borde_foco, border_width=2)
                except Exception:
                    pass
                if getattr(w, "_placeholder_text_active", False):
                    try:
                        w._deactivate_placeholder()
                    except Exception:
                        pass

            def on_focus_out(event, w=widget):
                try:
                    w.configure(border_color=color_borde_normal, border_width=1)
                except Exception:
                    pass

            widget.bind("<FocusIn>", on_focus_in)
            widget.bind("<FocusOut>", on_focus_out)
            asegurar_foco_al_clic(widget)

            sub = getattr(widget, "_entry", getattr(widget, "_textbox", None))
            if sub:
                sub.bind("<FocusIn>", on_focus_in)
                sub.bind("<FocusOut>", on_focus_out)

            def hacer_salto(i_destino):
                destino = controles[i_destino]
                destino.focus_set()
                sub_dest = getattr(destino, "_entry", None)
                if sub_dest:
                    sub_dest.select_range(0, "end")
                    sub_dest.icursor("end")
                return "break"

            widget.bind("<Tab>", lambda e, i=idx: hacer_salto((i + 1) % len(controles)))
            widget.bind("<Shift-Tab>", lambda e, i=idx: hacer_salto((i - 1) % len(controles)))
            widget.bind("<ISO_Left_Tab>", lambda e, i=idx: hacer_salto((i - 1) % len(controles)))

            if sub:
                sub.bind("<Tab>", lambda e, i=idx: hacer_salto((i + 1) % len(controles)))
                sub.bind("<Shift-Tab>", lambda e, i=idx: hacer_salto((i - 1) % len(controles)))
                sub.bind("<ISO_Left_Tab>", lambda e, i=idx: hacer_salto((i - 1) % len(controles)))

    # ------------------ SIDEBAR ------------------
    def setup_sidebar(self):
        self.sb = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=self.tema_actual["sidebar_bg"])
        self.sb.grid(row=0, column=0, sticky="nsew")

        logo_box = ctk.CTkFrame(self.sb, fg_color="transparent")
        logo_box.pack(padx=20, pady=(22, 25), anchor="w")

        ctk.CTkLabel(logo_box, text=ICON_CAR, font=FONT_LOGO_ICON).pack(side="left", padx=(0, 10))
        self.lbl_app_name = ctk.CTkLabel(logo_box, text="GarageDesk", font=ctk.CTkFont(size=20, weight="bold"),
                                         text_color=self.tema_actual["sidebar_text"])
        self.lbl_app_name.pack(side="left")

        def crear_nav_btn(parent, icon, text, cmd):
            btn_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=8, height=48, cursor="hand2")
            btn_frame.pack(fill="x", padx=12, pady=5)
            btn_frame.pack_propagate(False)

            lbl_ico = ctk.CTkLabel(btn_frame, text=icon, font=FONT_SIDEBAR_ICON,
                                   text_color=self.tema_actual["sidebar_icon"], width=34)
            lbl_ico.pack(side="left", padx=(10, 8))

            lbl_txt = ctk.CTkLabel(btn_frame, text=text, font=ctk.CTkFont(size=13, weight="bold"),
                                   text_color=self.tema_actual["sidebar_text"], anchor="w")
            lbl_txt.pack(side="left", fill="x", expand=True)

            for w in [btn_frame, lbl_ico, lbl_txt]:
                w.bind("<Button-1>", lambda e: cmd())

            btn_frame._lbl_txt = lbl_txt
            btn_frame._lbl_ico = lbl_ico
            return btn_frame

        self.btn_nav_dash = crear_nav_btn(self.sb, ICON_DASH, "Dashboard", lambda: self.mostrar_vista("dashboard"))
        self.btn_nav_cap = crear_nav_btn(self.sb, ICON_ADD, "Nuevo Registro", lambda: self.mostrar_vista("captura"))
        self.btn_nav_his = crear_nav_btn(self.sb, ICON_CHART, "Historial y Resumen", lambda: self.mostrar_vista("historial"))
        self.btn_nav_veh = crear_nav_btn(self.sb, ICON_VEH, "Vehículos", lambda: self.mostrar_vista("vehiculos"))
        self.btn_nav_alert = crear_nav_btn(self.sb, ICON_BELL, "Alertas", lambda: self.mostrar_vista("alertas"))
        self.nav_btns = [self.btn_nav_dash, self.btn_nav_cap, self.btn_nav_his, self.btn_nav_veh, self.btn_nav_alert]

        self.lbl_ver = ctk.CTkLabel(self.sb, text=f"Versión {APP_VERSION}", font=ctk.CTkFont(size=10),
                                    text_color=("gray40", "gray70"))
        self.lbl_ver.pack(side="bottom", padx=20, pady=(0, 6), anchor="w")

        self.btn_actualizar = ctk.CTkButton(
            self.sb, text="Buscar actualizaciones",
            image=icono_imagen(ICON_DOWNLOAD, 13, "#8892A0"),
            compound="left", font=ctk.CTkFont(size=10), height=24,
            fg_color="transparent", text_color=("gray50", "gray60"),
            hover_color=self.tema_actual["btn_active"], anchor="w",
            command=lambda: self.buscar_actualizaciones(silencioso=False)
        )
        self.btn_actualizar.pack(side="bottom", padx=15, pady=(0, 2), fill="x")

        # Filigrana sutil en Sidebar
        self.btn_seguridad_filigrana = ctk.CTkButton(
            self.sb, text="Seguridad y Respaldo", image=icono_imagen(ICON_GEAR, 13, "#8892A0"),
            compound="left",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=("gray50", "gray60"),
            hover_color=self.tema_actual["btn_active"],
            anchor="w", height=32,
            command=self.abrir_panel_seguridad
        )
        self.btn_seguridad_filigrana.pack(side="bottom", padx=15, pady=(0, 6), fill="x")

        self.opt_tema = ctk.CTkOptionMenu(
            self.sb, values=list(TEMAS.keys()), command=self.aplicar_tema_completo, height=28,
            fg_color=self.tema_actual["accent"], button_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"]
        )
        self.opt_tema.set(self.nombre_tema_actual)
        self.opt_tema.pack(side="bottom", padx=15, pady=(0, 10), fill="x")

        self.lbl_tema_tit = ctk.CTkLabel(self.sb, text="Estilo visual:", font=ctk.CTkFont(size=11, weight="bold"),
                                         text_color=("gray50", "gray70"))
        self.lbl_tema_tit.pack(side="bottom", padx=20, pady=(0, 4), anchor="w")

    def aplicar_tema_completo(self, nuevo_tema_nombre):
        self.nombre_tema_actual = nuevo_tema_nombre
        self.tema_actual = TEMAS[nuevo_tema_nombre]
        t = self.tema_actual

        self.db.guardar_config("tema_actual", nuevo_tema_nombre)

        ctk.set_appearance_mode(t["mode"])
        self.configure(fg_color=t["app_bg"])
        self.sb.configure(fg_color=t["sidebar_bg"])
        self.lbl_app_name.configure(text_color=t["sidebar_text"])

        self.opt_tema.configure(fg_color=t["accent"], button_color=t["accent_hover"], text_color=t["accent_text"])
        self.btn_seguridad_filigrana.configure(hover_color=t["btn_active"])

        for b in self.nav_btns:
            b._lbl_ico.configure(text_color=t["sidebar_icon"])
            b._lbl_txt.configure(text_color=t["sidebar_text"])

        if hasattr(self, "panel_cap"):
            self.panel_cap.configure(fg_color=t["panel_bg"])
            self.btn_cal_cap.configure(fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["accent_text"])
            self.btn_veh_cap.configure(fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["accent_text"])
            self.btn_subir_comp.configure(fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["accent_text"])
            self.btn_guardar_cap.configure(fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["accent_text"])

        if hasattr(self, "cards_kpi_dash"):
            for card in self.cards_kpi_dash:
                card.configure(fg_color=t["panel_bg"])
        if hasattr(self, "cards_kpi_his"):
            for card in self.cards_kpi_his:
                card.configure(fg_color=t["panel_bg"])
        if hasattr(self, "filtros_frame"):
            self.filtros_frame.configure(fg_color=t["panel_bg"])
            self.btn_cal_desde.configure(fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["accent_text"])
            self.btn_cal_hasta.configure(fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["accent_text"])

        if hasattr(self, "btn_nuevo_veh"):
            self.btn_nuevo_veh.configure(fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["accent_text"])
        if hasattr(self, "btn_nuevo_rec"):
            self.btn_nuevo_rec.configure(fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["accent_text"])
        if hasattr(self, "cards_kpi_alert"):
            for card in self.cards_kpi_alert:
                card.configure(fg_color=t["panel_bg"])

        self.mostrar_vista(self.vista_actual)

    def setup_views(self):
        self.v_dash = ctk.CTkFrame(self, fg_color="transparent")
        self.setup_dashboard()

        self.v_cap = ctk.CTkFrame(self, fg_color="transparent")
        self.setup_captura()

        self.v_his = ctk.CTkFrame(self, fg_color="transparent")
        self.setup_historial()

        self.v_veh = ctk.CTkFrame(self, fg_color="transparent")
        self.setup_vehiculos()

        self.v_alert = ctk.CTkFrame(self, fg_color="transparent")
        self.setup_alertas()

    def mostrar_vista(self, v):
        self.vista_actual = v
        color_activo = self.tema_actual["btn_active"]

        vistas = {
            "dashboard": (self.v_dash, self.btn_nav_dash),
            "captura": (self.v_cap, self.btn_nav_cap),
            "historial": (self.v_his, self.btn_nav_his),
            "vehiculos": (self.v_veh, self.btn_nav_veh),
            "alertas": (self.v_alert, self.btn_nav_alert),
        }

        for frame, boton in vistas.values():
            frame.grid_forget()
            boton.configure(fg_color="transparent")

        frame, boton = vistas.get(v, vistas["captura"])
        frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        boton.configure(fg_color=color_activo)

        if v == "captura":
            self.in_fecha.focus_set()
        elif v == "dashboard":
            self.actualizar_dashboard()
        elif v == "historial":
            self.actualizar_historial()
        elif v == "vehiculos":
            self.actualizar_vehiculos()
        else:
            self.actualizar_alertas()

    # ------------------ PANEL MODAL: CENTRO DE SEGURIDAD Y RESPALDO ------------------
    def abrir_panel_seguridad(self):
        m = ctk.CTkToplevel(self)
        m.title("Centro de Seguridad y Respaldo")
        m.geometry("580x690")
        m.resizable(False, False)
        m.grab_set()
        m.transient(self)

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        px = max(0, int((sw - 580) / 2))
        py = max(0, int((sh - 690) / 2))
        m.geometry(f"580x690+{px}+{py}")

        p = ctk.CTkScrollableFrame(m, corner_radius=10, fg_color=self.tema_actual["panel_bg"])
        p.pack(fill="both", expand=True, padx=14, pady=14)

        t = self.tema_actual

        def titulo_sec(txt, centrado=False):
            anc = "center" if centrado else "w"
            ctk.CTkLabel(p, text=txt, font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=t["accent"], anchor=anc).pack(fill="x", pady=(14, 4))

        # 1. Respaldo Manual Centrado con Ícono Destacado
        titulo_sec("Punto de Restauración Inmediato", centrado=True)
        ctk.CTkLabel(p, text="Crea una instantánea completa de tu base de datos en este momento.",
                     font=ctk.CTkFont(size=11), text_color=("gray40", "gray60"), anchor="center").pack(fill="x", pady=(0, 8))

        btn_snap_box = ctk.CTkFrame(p, fg_color="transparent")
        btn_snap_box.pack(fill="x", pady=(4, 14))

        def disparar_crear_punto():
            self.security.crear_punto_restauracion(silencioso=False)
            refrescar_lista_puntos()

        btn_snap = ctk.CTkButton(
            btn_snap_box,
            text="Crear Punto de Restauración Ahora", image=icono_imagen(ICON_SHIELD, 16),
            compound="left",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=44, width=360, corner_radius=8,
            fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["accent_text"],
            command=disparar_crear_punto
        )
        btn_snap.pack(anchor="center")

        # 2. Sincronización Nube (Carpeta Espejo)
        titulo_sec("Sincronización en la Nube (Google Drive / OneDrive / Dropbox)")
        ctk.CTkLabel(p, text="Los respaldos comprimidos se copiarán a esta carpeta para respaldar fuera de la PC.",
                     font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")).pack(anchor="w")

        box_nube = ctk.CTkFrame(p, fg_color="transparent")
        box_nube.pack(fill="x", pady=(6, 10))

        ruta_nube_actual = self.db.obtener_config("ruta_carpeta_nube", "")
        lbl_nube_path = ctk.CTkLabel(box_nube, text=ruta_nube_actual or "Sin carpeta vinculada",
                                     font=ctk.CTkFont(size=11), text_color=("#64748B", "#94A3B8"), anchor="w")
        lbl_nube_path.pack(side="left", fill="x", expand=True, padx=(0, 8))

        def vincular_nube():
            dir_sel = filedialog.askdirectory(title="Selecciona la carpeta local de tu Nube", parent=m)
            if dir_sel:
                self.db.guardar_config("ruta_carpeta_nube", dir_sel)
                lbl_nube_path.configure(text=dir_sel)
                messagebox.showinfo("Nube Configurada", "Carpeta sincronizada vinculada correctamente.", parent=m)

        ctk.CTkButton(box_nube, text="Examinar...", width=95, height=32, command=vincular_nube).pack(side="right")

        # 3. Frecuencia de Autoguardado
        titulo_sec("Automatización y Autoguardado")
        box_frec = ctk.CTkFrame(p, fg_color="transparent")
        box_frec.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(box_frec, text="Frecuencia del respaldo en segundo plano:").pack(side="left", padx=(0, 10))
        opt_frec = ctk.CTkOptionMenu(
            box_frec, values=["Cada 15 min", "Cada 30 min", "Solo al cerrar"],
            command=lambda val: (self.db.guardar_config("frecuencia_respaldo", val), self.security.iniciar_autoguardado())
        )
        opt_frec.set(self.db.obtener_config("frecuencia_respaldo", "Cada 30 min"))
        opt_frec.pack(side="left")

        # 4. Salud de la Base de Datos (Texto y Botón Centrados con Ícono Amplio)
        titulo_sec("Diagnóstico de Integridad", centrado=True)
        def diagnosticar():
            ok, msj = self.security.verificar_integridad_archivo(self.db.db_name)
            if ok:
                messagebox.showinfo("Diagnóstico Exitoso", f"La base de datos está saludable y sin errores estructurales.\n\n{msj}", parent=m)
            else:
                messagebox.showwarning("Atención", f"Se detectaron anomalías estructurales:\n{msj}", parent=m)

        box_diag = ctk.CTkFrame(p, fg_color="transparent")
        box_diag.pack(fill="x", pady=(4, 10))
        ctk.CTkButton(box_diag, text="Verificar Salud de la Base de Datos", image=icono_imagen(ICON_HEALTH, ICON_TAM_PNG),
                      compound="left", height=38, width=310,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      fg_color=("#334155", "#475569"), hover_color=("#1E293B", "#334155"),
                      command=diagnosticar).pack(anchor="center")

        # 5. Portabilidad (.garagepack) (Texto y Botones Centrados con Íconos Claros)
        titulo_sec("Portabilidad Total de Datos (Comprobantes + Fotos + Base)", centrado=True)
        box_port = ctk.CTkFrame(p, fg_color="transparent")
        box_port.pack(fill="x", pady=(4, 10))

        box_port_btns = ctk.CTkFrame(box_port, fg_color="transparent")
        box_port_btns.pack(anchor="center")

        def exportar():
            dest = filedialog.asksaveasfilename(
                title="Guardar Paquete Portátil", defaultextension=".garagepack",
                filetypes=[("Paquete GarageDesk", "*.garagepack")], parent=m
            )
            if dest:
                ok, res = self.security.exportar_paquete_completo(dest)
                if ok: messagebox.showinfo("Exportación Lista", res, parent=m)
                else: messagebox.showerror("Error", res, parent=m)

        def importar():
            orig = filedialog.askopenfilename(
                title="Importar Paquete Portátil", filetypes=[("Paquete GarageDesk", "*.garagepack")], parent=m
            )
            if orig:
                msj_imp = (
                    "Se reemplazarán los datos actuales del programa con los contenidos en el paquete seleccionado.\n\n"
                    "• Se generará un respaldo de seguridad previo de tus datos actuales antes de sobrescribir.\n\n"
                    "¿Deseas continuar con la importación?"
                )
                if self.dialogo_confirmar_accion(
                    m,
                    "Importar Paquete de Datos",
                    msj_imp,
                    "Importar y Sobrescribir",
                    ("#0284C7", "#0369A1")
                ):
                    ok, res = self.security.importar_paquete_completo(orig)
                    if ok:
                        messagebox.showinfo("Importación Completa", res, parent=m)
                        self.refrescar_vehiculos_ui()
                        self.actualizar_historial()
                        m.destroy()
                    else:
                        messagebox.showerror("Error", res, parent=m)

        ctk.CTkButton(box_port_btns, text="Exportar Paquete", image=icono_imagen(ICON_PACKAGE, ICON_TAM_PNG),
                      compound="left", width=160, height=36,
                      font=ctk.CTkFont(size=12, weight="bold"), command=exportar).pack(side="left", padx=6)
        ctk.CTkButton(box_port_btns, text="Importar Paquete", image=icono_imagen(ICON_DOWNLOAD, ICON_TAM_PNG),
                      compound="left", width=160, height=36,
                      font=ctk.CTkFont(size=12, weight="bold"), command=importar).pack(side="left", padx=6)

        # 6. Historial de Puntos Locales con Borrado y Confirmación
        titulo_sec("Puntos de Restauración Disponibles")
        scroll_hist_resp = ctk.CTkScrollableFrame(p, height=150, fg_color=t["card_bg"])
        scroll_hist_resp.pack(fill="x", pady=(4, 10))

        def restaurar_archivo(arch):
            msj_rest = (
                "¿Deseas restaurar la base de datos a este punto previo?\n\n"
                f"• Archivo: {arch}\n\n"
                "Tus datos actuales serán resguardados en un nuevo punto de restauración antes de aplicar el cambio."
            )
            if self.dialogo_confirmar_accion(
                m,
                "Restaurar Punto de Restauración",
                msj_rest,
                "Sí, Restaurar",
                ("#D97706", "#B45309")
            ):
                try:
                    self.security.crear_punto_restauracion(silencioso=True)
                    with contextlib.closing(sqlite3.connect(os.path.join(CARPETA_BACKUPS, arch))) as src, \
                         contextlib.closing(sqlite3.connect(self.db.db_name, timeout=10)) as dst:
                        src.backup(dst)
                    messagebox.showinfo("Restauración Completada", "Datos restaurados correctamente.", parent=m)
                    self.refrescar_vehiculos_ui()
                    self.actualizar_historial()
                    m.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo restaurar: {e}", parent=m)

        def borrar_archivo(arch):
            msj_borrar = (
                "¿Deseas eliminar permanentemente este punto de restauración?\n\n"
                f"• Archivo: {arch}\n\n"
                "Esta acción liberará espacio en disco pero no podrá revertirse."
            )
            if self.dialogo_confirmar_accion(
                m,
                "Eliminar Punto de Restauración",
                msj_borrar,
                "Sí, Eliminar",
                ("#DC2626", "#B91C1C")
            ):
                ok, msj = self.security.eliminar_punto_restauracion(arch)
                if ok:
                    refrescar_lista_puntos()
                else:
                    messagebox.showerror("Error al borrar", msj, parent=m)

        def refrescar_lista_puntos():
            for w in scroll_hist_resp.winfo_children():
                w.destroy()

            backups = [f for f in os.listdir(CARPETA_BACKUPS) if f.endswith(".db")]
            backups.sort(reverse=True)

            if not backups:
                ctk.CTkLabel(scroll_hist_resp, text="No hay puntos de restauración guardados aún.",
                             font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")).pack(pady=15)
                return

            for b in backups[:15]:
                row = ctk.CTkFrame(scroll_hist_resp, fg_color="transparent")
                row.pack(fill="x", pady=3, padx=2)

                ctk.CTkLabel(row, text=b, font=ctk.CTkFont(size=11), anchor="w").pack(side="left", fill="x", expand=True, padx=4)

                btn_box_punto = ctk.CTkFrame(row, fg_color="transparent")
                btn_box_punto.pack(side="right")

                ctk.CTkButton(
                    btn_box_punto, text="Restaurar", width=74, height=26, font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color=("#D97706", "#B45309"), hover_color=("#B45309", "#92400E"), text_color="#FFFFFF",
                    command=lambda arch=b: restaurar_archivo(arch)
                ).pack(side="left", padx=3)

                ctk.CTkButton(
                    btn_box_punto, text=ICON_DEL, width=32, height=26, font=FONT_ACTION_ICON,
                    fg_color=("#FEE2E2", "#7F1D1D"), hover_color=("#FECACA", "#991B1B"), text_color=("#DC2626", "#FCA5A5"),
                    command=lambda arch=b: borrar_archivo(arch)
                ).pack(side="left", padx=2)

        refrescar_lista_puntos()

    def dialogo_confirmar_accion(self, parent_window, titulo, mensaje, texto_confirmar="Aceptar", color_confirmar=None):
        confirmado = [False]

        diag = ctk.CTkToplevel(parent_window)
        diag.title(titulo)
        diag.geometry("480x250")
        diag.resizable(False, False)
        diag.grab_set()
        diag.transient(parent_window)

        sw = diag.winfo_screenwidth()
        sh = diag.winfo_screenheight()
        px = max(0, int((sw - 480) / 2))
        py = max(0, int((sh - 250) / 2))
        diag.geometry(f"480x250+{px}+{py}")

        panel = ctk.CTkFrame(diag, corner_radius=12, fg_color=self.tema_actual["panel_bg"])
        panel.pack(fill="both", expand=True, padx=14, pady=14)

        header_box = ctk.CTkFrame(panel, fg_color="transparent")
        header_box.pack(fill="x", padx=16, pady=(14, 8))

        inner_header = ctk.CTkFrame(header_box, fg_color="transparent")
        inner_header.pack(anchor="center")

        col_conf = color_confirmar or self.tema_actual["accent"]

        ctk.CTkLabel(
            inner_header, text=ICON_WARN,
            font=(FAMILIA_ICONOS, ICON_TAM_AVISO),
            text_color=col_conf[0] if isinstance(col_conf, tuple) else col_conf
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            inner_header, text=titulo,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=self.tema_actual["text_title"]
        ).pack(side="left")

        card_msg = ctk.CTkFrame(panel, corner_radius=8, fg_color=self.tema_actual["card_bg"])
        card_msg.pack(fill="both", expand=True, padx=16, pady=(4, 14))

        lbl_msj = ctk.CTkLabel(
            card_msg, text=mensaje,
            font=ctk.CTkFont(size=12),
            text_color=self.tema_actual["sidebar_text"],
            justify="left", anchor="w", wraplength=410
        )
        lbl_msj.pack(fill="both", expand=True, padx=14, pady=10)

        btn_box = ctk.CTkFrame(panel, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(0, 8))

        def al_aceptar():
            confirmado[0] = True
            diag.destroy()

        def al_cancelar():
            confirmado[0] = False
            diag.destroy()

        ctk.CTkButton(
            btn_box, text="Cancelar", width=110, height=36, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#64748B", "#475569"), hover_color=("#475569", "#334155"),
            text_color="#FFFFFF", command=al_cancelar
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_box, text=texto_confirmar, width=150, height=36, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=col_conf, text_color="#FFFFFF", command=al_aceptar
        ).pack(side="right")

        parent_window.wait_window(diag)
        return confirmado[0]

    # ------------------ PANTALLA: DASHBOARD ------------------
    def setup_dashboard(self):
        self.v_dash.grid_columnconfigure(0, weight=1)
        self.v_dash.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(self.v_dash, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.lbl_dash_tit = ctk.CTkLabel(top, text="Dashboard de Gastos", font=ctk.CTkFont(size=20, weight="bold"),
                                         text_color=("#0F172A", "#F8FAFC"))
        self.lbl_dash_tit.pack(side="left")

        ctk.CTkButton(
            top, text="Actualizar", width=110, height=34, corner_radius=6,
            fg_color=("#334155", "#475569"), hover_color=("#1E293B", "#334155"), text_color="#FFFFFF",
            command=self.actualizar_dashboard
        ).pack(side="right")

        kpi = ctk.CTkFrame(self.v_dash, fg_color="transparent")
        kpi.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        kpi.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.cards_kpi_dash = []

        def kpi_card(col, titulo, color):
            f = ctk.CTkFrame(kpi, corner_radius=8, fg_color=self.tema_actual["panel_bg"])
            f.grid(row=0, column=col, sticky="ew", padx=5)
            self.cards_kpi_dash.append(f)
            ctk.CTkLabel(f, text=titulo, font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")).pack(anchor="w", padx=12, pady=(8, 0))
            lbl = ctk.CTkLabel(f, text="-", font=ctk.CTkFont(size=17, weight="bold"), text_color=color)
            lbl.pack(anchor="w", padx=12, pady=(0, 8))
            return lbl

        self.dash_total = kpi_card(0, "Gasto total", ("#0F172A", "#F8FAFC"))
        self.dash_mes = kpi_card(1, "Gasto este mes", ("#2563EB", "#60A5FA"))
        self.dash_prom = kpi_card(2, "Promedio mensual", ("#0D9488", "#2DD4BF"))
        self.dash_n = kpi_card(3, "Registros", ("#7C3AED", "#A78BFA"))

        self.dash_grid = ctk.CTkScrollableFrame(self.v_dash, corner_radius=8, fg_color="transparent")
        self.dash_grid.grid(row=2, column=0, sticky="nsew")
        self.dash_grid.grid_columnconfigure((0, 1), weight=1, uniform="graf")
        self.dash_figures = []

    def actualizar_dashboard(self):
        if not hasattr(self, "dash_grid"):
            return

        total = float(self.db.query("SELECT COALESCE(SUM(costo), 0) FROM registros")[0][0] or 0)
        n = int(self.db.query("SELECT COUNT(*) FROM registros")[0][0] or 0)
        mes_actual = date.today().strftime("%Y-%m")

        filas_mes = self.db.query("SELECT fecha, costo FROM registros")
        gasto_mes = sum(float(c or 0) for f, c in filas_mes
                        if (normalizar_a_iso(f) or "").startswith(mes_actual))

        meses_unicos = {(normalizar_a_iso(f) or "")[:7] for f, _ in filas_mes
                        if normalizar_a_iso(f)}
        meses_datos = len(meses_unicos)

        self.dash_total.configure(text=f"${total:,.2f}")
        self.dash_mes.configure(text=f"${gasto_mes:,.2f}")
        self.dash_prom.configure(text=f"${(total / meses_datos) if meses_datos else 0:,.2f}")
        self.dash_n.configure(text=f"{n} registro(s)")

        if HAY_MATPLOTLIB:
            for fig in self.dash_figures:
                plt.close(fig)
        self.dash_figures.clear()

        for w in self.dash_grid.winfo_children():
            w.destroy()

        if not HAY_MATPLOTLIB:
            ctk.CTkLabel(
                self.dash_grid,
                text="Para ver las gráficas instala matplotlib:\n\npip install matplotlib",
                text_color=("gray40", "gray60"), justify="center"
            ).grid(row=0, column=0, columnspan=2, pady=60)
            return

        if n == 0:
            ctk.CTkLabel(
                self.dash_grid,
                text="Aún no hay datos para graficar.\nGuarda tu primer registro y vuelve aquí.",
                text_color=("gray40", "gray60"), justify="center"
            ).grid(row=0, column=0, columnspan=2, pady=60)
            return

        self._grafica_meses(0, 0)
        self._grafica_categorias(0, 1)
        self._grafica_vehiculos(1, 0)
        self._grafica_lugares(1, 1)

    def _colores_tema(self):
        t = self.tema_actual
        return {
            "fondo": t["plot_bg"],
            "texto": t["plot_text"],
            "grid": t["plot_grid"],
            "bar": t["plot_bar"],
            "bar2": t["plot_bar2"],
            "bar3": t["plot_bar3"],
        }

    def _nueva_figura(self):
        col = self._colores_tema()
        fig = Figure(figsize=(4.0, 2.4), dpi=100)
        self.dash_figures.append(fig)
        fig.patch.set_facecolor(col["fondo"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(col["fondo"])
        ax.tick_params(colors=col["texto"], labelsize=8)
        for lado in ax.spines.values():
            lado.set_color(col["grid"])
        ax.grid(axis="y", color=col["grid"], alpha=0.35, linewidth=0.6)
        ax.set_axisbelow(True)
        formato_miles = FuncFormatter(lambda v, _: f"{v:,.0f}")
        ax.yaxis.set_major_formatter(formato_miles)
        ax.xaxis.set_major_formatter(formato_miles)
        fig.subplots_adjust(left=0.16, right=0.97, top=0.84, bottom=0.24)
        return fig, ax

    def _mostrar_figura(self, fig, fila, col):
        canvas = FigureCanvasTkAgg(fig, master=self.dash_grid)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.grid(row=fila, column=col, padx=6, pady=6, sticky="nsew")

    def _grafica_meses(self, fila, col):
        hoy = date.today()
        anio, mes = hoy.year, hoy.month
        meses = []
        for _ in range(12):
            meses.append(f"{anio:04d}-{mes:02d}")
            mes -= 1
            if mes == 0:
                mes = 12
                anio -= 1
        meses.reverse()

        todas = self.db.query("SELECT fecha, costo FROM registros")
        mapa = {}
        for f, c in todas:
            m_iso = (normalizar_a_iso(f) or "")[:7]
            if m_iso:
                mapa[m_iso] = mapa.get(m_iso, 0.0) + float(c or 0)

        valores = [mapa.get(m, 0.0) for m in meses]
        etiquetas = [f"{MESES_CORTOS[int(m[5:7]) - 1]} {m[2:4]}" for m in meses]

        colores = self._colores_tema()
        fig, ax = self._nueva_figura()
        ax.bar(range(len(meses)), valores, color=colores["bar"], width=0.68, edgecolor="none")
        ax.set_xticks(range(len(meses)))
        ax.set_xticklabels(etiquetas, rotation=45, ha="right", fontsize=7)
        ax.set_title("Gasto por mes (últimos 12)", color=colores["texto"], fontsize=10, fontweight="bold", pad=8)
        self._mostrar_figura(fig, fila, col)

    def _grafica_categorias(self, fila, col):
        filas = self.db.query("SELECT tipo, COALESCE(SUM(costo), 0) AS g FROM registros GROUP BY tipo ORDER BY g DESC")
        datos = [(t or "Sin categoría", float(g or 0)) for t, g in filas if (g or 0) > 0]
        colores = self._colores_tema()

        if not datos:
            fig, ax = self._nueva_figura()
            ax.axis("off")
            ax.set_title("Gasto por categoría", color=colores["texto"], fontsize=10, fontweight="bold", pad=8)
            ax.text(0.5, 0.45, "Sin costos registrados", ha="center", va="center",
                    color=colores["texto"], fontsize=9, transform=ax.transAxes)
            self._mostrar_figura(fig, fila, col)
            return

        etiquetas = [t for t, _ in datos]
        valores = [v for _, v in datos]
        colores_torta = [COLORES_CATEGORIA.get(t, "#64748B") for t in etiquetas]

        fig, ax = self._nueva_figura()
        ax.grid(False)
        for lado in ax.spines.values():
            lado.set_visible(False)
        ax.pie(
            valores, colors=colores_torta, startangle=90, counterclock=False,
            autopct=lambda p: f"{p:.0f}%", pctdistance=0.75,
            textprops={"color": "#FFFFFF", "fontsize": 7, "fontweight": "bold"},
            wedgeprops={"linewidth": 1.5, "edgecolor": colores["fondo"], "width": 0.45}
        )
        ax.legend(etiquetas, loc="center left", bbox_to_anchor=(0.92, 0.5), fontsize=7, frameon=False, labelcolor=colores["texto"])
        fig.subplots_adjust(left=0.02, right=0.62, top=0.86, bottom=0.04)
        ax.set_title("Gasto por categoría", color=colores["texto"], fontsize=10, fontweight="bold", pad=8)
        self._mostrar_figura(fig, fila, col)

    def _grafica_vehiculos(self, fila, col):
        filas = self.db.query("""
            SELECT COALESCE(v.nombre, NULLIF(TRIM(r.vehiculo), ''), 'General') AS nombre,
                   COALESCE(SUM(r.costo), 0) AS g
            FROM registros r
            LEFT JOIN vehiculos v ON v.id = r.vehiculo_id
            GROUP BY nombre
            ORDER BY g DESC
            LIMIT 6
        """)
        datos = [(n or "General", float(g or 0)) for n, g in filas][::-1]
        colores = self._colores_tema()

        fig, ax = self._nueva_figura()
        if not datos:
            ax.axis("off")
            self._mostrar_figura(fig, fila, col)
            return

        etiquetas = [n for n, _ in datos]
        valores = [v for _, v in datos]
        barras = ax.barh(range(len(datos)), valores, color=colores["bar2"], height=0.6, edgecolor="none")
        ax.set_yticks(range(len(datos)))
        ax.set_yticklabels(etiquetas, fontsize=8)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", color=colores["grid"], alpha=0.35, linewidth=0.6)
        ax.bar_label(barras, labels=[f"${v:,.0f}" for v in valores], padding=3, fontsize=7, color=colores["texto"])
        ax.set_title("Gasto por vehículo", color=colores["texto"], fontsize=10, fontweight="bold", pad=8)
        fig.subplots_adjust(left=0.32, right=0.86, top=0.84, bottom=0.14)
        self._mostrar_figura(fig, fila, col)

    def _grafica_lugares(self, fila, col):
        filas = self.db.query("""
            SELECT COALESCE(NULLIF(TRIM(taller_lugar), ''), 'Sin lugar') AS lugar,
                   COALESCE(SUM(costo), 0) AS g
            FROM registros
            GROUP BY lugar
            ORDER BY g DESC
            LIMIT 6
        """)
        datos = [(l, float(g or 0)) for l, g in filas][::-1]
        colores = self._colores_tema()

        fig, ax = self._nueva_figura()
        if not datos:
            ax.axis("off")
            ax.set_title("Top lugares / procedencia", color=colores["texto"], fontsize=10, fontweight="bold", pad=8)
            ax.text(0.5, 0.45, "Sin lugares registrados", ha="center", va="center",
                    color=colores["texto"], fontsize=9, transform=ax.transAxes)
            self._mostrar_figura(fig, fila, col)
            return

        etiquetas = [l for l, _ in datos]
        valores = [v for _, v in datos]
        barras = ax.barh(range(len(datos)), valores, color=colores["bar3"], height=0.6, edgecolor="none")
        ax.set_yticks(range(len(datos)))
        ax.set_yticklabels(etiquetas, fontsize=8)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", color=colores["grid"], alpha=0.35, linewidth=0.6)
        ax.bar_label(barras, labels=[f"${v:,.0f}" for v in valores], padding=3, fontsize=7, color=colores["texto"])
        ax.set_title("Top lugares / procedencia", color=colores["texto"], fontsize=10, fontweight="bold", pad=8)
        fig.subplots_adjust(left=0.42, right=0.84, top=0.84, bottom=0.14)
        self._mostrar_figura(fig, fila, col)

    # ------------------ PANTALLA: CAPTURA ------------------
    def setup_captura(self):
        self.panel_cap = ctk.CTkScrollableFrame(self.v_cap, corner_radius=10, fg_color=self.tema_actual["panel_bg"])
        self.panel_cap.pack(fill="both", expand=True)

        ctk.CTkLabel(self.panel_cap, text="Detalles del Registro", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=("#0F172A", "#F8FAFC")).pack(anchor="w", padx=25, pady=(15, 10))

        form = ctk.CTkFrame(self.panel_cap, fg_color="transparent")
        form.pack(fill="x", expand=True, padx=25, pady=5)

        for i in range(6):
            form.grid_columnconfigure(i, weight=1, uniform="col")

        ctk.CTkLabel(form, text="Fecha:", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#1E293B", "#F1F5F9")).grid(row=0, column=0, columnspan=3, sticky="w", padx=(0, 15), pady=(5, 2))
        f_box = ctk.CTkFrame(form, fg_color="transparent")
        f_box.grid(row=1, column=0, columnspan=3, sticky="ew", padx=(0, 15), pady=(0, 10))
        f_box.grid_columnconfigure(0, weight=1)

        self.in_fecha = ctk.CTkEntry(f_box, height=38, corner_radius=6, placeholder_text="DD/MM/AAAA")
        self.in_fecha.insert(0, datetime.today().strftime('%d/%m/%Y'))
        self.in_fecha.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.btn_cal_cap = ctk.CTkButton(
            f_box, text=ICON_CAL, font=FONT_CAL_ICON, width=46, height=38, corner_radius=6,
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"],
            command=lambda: CalendarPicker(self, self.in_fecha, self.tema_actual)
        )
        self.btn_cal_cap.grid(row=0, column=1)

        ctk.CTkLabel(form, text="Vehículo:", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#1E293B", "#F1F5F9")).grid(row=0, column=3, columnspan=3, sticky="w", padx=(15, 0), pady=(5, 2))
        veh_box = ctk.CTkFrame(form, fg_color="transparent")
        veh_box.grid(row=1, column=3, columnspan=3, sticky="ew", padx=(15, 0), pady=(0, 10))
        veh_box.grid_columnconfigure(0, weight=1)

        self.in_vehiculo = ctk.CTkComboBox(
            veh_box, height=38, corner_radius=6,
            values=self.lista_vehiculos_nombres() or ["General"]
        )
        self.in_vehiculo.set("")
        self.in_vehiculo.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.btn_veh_cap = ctk.CTkButton(
            veh_box, text=ICON_ADD, font=FONT_CAL_ICON, width=46, height=38, corner_radius=6,
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"],
            command=self.nuevo_vehiculo_desde_captura
        )
        self.btn_veh_cap.grid(row=0, column=1)

        ctk.CTkLabel(form, text="Categoría:", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#1E293B", "#F1F5F9")).grid(row=2, column=0, columnspan=2, sticky="w", padx=(0, 10), pady=(5, 2))
        self.in_tipo = ctk.CTkComboBox(form, height=38, corner_radius=6, values=list(self.badges.keys()))
        self.in_tipo.set(list(self.badges.keys())[0])
        self.in_tipo.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(0, 10), pady=(0, 10))

        ctk.CTkLabel(form, text="Kilometraje Actual:", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#1E293B", "#F1F5F9")).grid(row=2, column=2, columnspan=2, sticky="w", padx=10, pady=(5, 2))
        self.in_km = ctk.CTkEntry(form, height=38, corner_radius=6, placeholder_text="Ej. 85,000")
        self.in_km.grid(row=3, column=2, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        self.in_km.bind("<KeyRelease>", lambda e: aplicar_formato_entero(self.in_km, e))

        ctk.CTkLabel(form, text="Costo Total ($):", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#1E293B", "#F1F5F9")).grid(row=2, column=4, columnspan=2, sticky="w", padx=(10, 0), pady=(5, 2))
        self.in_costo = ctk.CTkEntry(form, height=38, corner_radius=6, placeholder_text="Ej. 1,450.00")
        self.in_costo.grid(row=3, column=4, columnspan=2, sticky="ew", padx=(10, 0), pady=(0, 10))
        self.in_costo.bind("<KeyRelease>", lambda e: aplicar_formato_decimal(self.in_costo, e))

        ctk.CTkLabel(form, text="Lugar / Procedencia:", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#1E293B", "#F1F5F9")).grid(row=4, column=0, columnspan=3, sticky="w", pady=(5, 2))
        ctk.CTkLabel(form, text="Servicio/Taller • Compra", font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")).grid(row=4, column=3, columnspan=3, sticky="e", pady=(5, 2))

        self.in_taller = ctk.CTkComboBox(form, height=38, corner_radius=6, values=LUGARES_SUGERIDOS)
        self.in_taller.set("")
        self.in_taller.grid(row=5, column=0, columnspan=6, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(form, text="Trabajo Realizado:", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#1E293B", "#F1F5F9")).grid(row=6, column=0, columnspan=3, sticky="w", padx=(0, 15), pady=(5, 2))
        self.in_desc = ctk.CTkTextbox(form, height=85, corner_radius=6)
        self.in_desc._textbox.tag_configure("justificado", justify="left")
        self.in_desc.grid(row=7, column=0, columnspan=3, sticky="ew", padx=(0, 15), pady=(0, 10))
        activar_corrector_en_vivo(self.in_desc)

        ctk.CTkLabel(form, text="Notas / Garantía:", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#1E293B", "#F1F5F9")).grid(row=6, column=3, columnspan=3, sticky="w", padx=(15, 0), pady=(5, 2))
        self.in_notas = ctk.CTkTextbox(form, height=85, corner_radius=6)
        self.in_notas._textbox.tag_configure("justificado", justify="left")
        self.in_notas.grid(row=7, column=3, columnspan=3, sticky="ew", padx=(15, 0), pady=(0, 10))
        activar_corrector_en_vivo(self.in_notas)

        ctk.CTkLabel(form, text="Nota de Pago o Comprobante (Opcional):", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#1E293B", "#F1F5F9")).grid(row=8, column=0, columnspan=6, sticky="w", pady=(5, 2))
        comp_box = ctk.CTkFrame(form, fg_color="transparent")
        comp_box.grid(row=9, column=0, columnspan=6, sticky="ew", pady=(0, 15))
        comp_box.grid_columnconfigure(1, weight=1)

        self.btn_subir_comp = ctk.CTkButton(
            comp_box, text="Adjuntar Comprobante", image=icono_imagen(ICON_ATTACH, ICON_TAM_PNG),
            compound="left", height=42, width=235, corner_radius=6,
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"],
            font=ctk.CTkFont(size=13, weight="bold"), command=self.seleccionar_comprobante
        )
        self.btn_subir_comp.grid(row=0, column=0, padx=(0, 12))

        self.lbl_comp_nombre = ctk.CTkLabel(comp_box, text="Ningún comprobante seleccionado",
                                            text_color=("gray50", "gray60"), anchor="w")
        self.lbl_comp_nombre.grid(row=0, column=1, sticky="ew")

        self.btn_quitar_comp = ctk.CTkButton(
            comp_box, text=ICON_DEL, font=FONT_ACTION_ICON, width=42, height=42, corner_radius=6,
            fg_color=("#FEE2E2", "#7F1D1D"), hover_color=("#FCA5A5", "#991B1B"),
            text_color=("#B91C1C", "#FCA5A5"), command=self.limpiar_comprobante
        )
        self.btn_quitar_comp.grid(row=0, column=2, padx=(5, 0))
        self.btn_quitar_comp.grid_remove()

        self.btn_guardar_cap = ctk.CTkButton(
            self.panel_cap, text="Guardar Registro", height=42, width=200, font=ctk.CTkFont(weight="bold"),
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"],
            command=self.guardar_registro
        )
        self.btn_guardar_cap.pack(anchor="e", padx=25, pady=(5, 25))

        self.vincular_tab([
            self.in_fecha, self.in_vehiculo,
            self.in_tipo, self.in_km, self.in_costo,
            self.in_taller, self.in_desc, self.in_notas,
            self.btn_guardar_cap
        ])

    def seleccionar_comprobante(self):
        tipos = [
            ("Archivos de Comprobante", "*.jpg;*.jpeg;*.png;*.webp;*.pdf"),
            ("Imágenes (*.jpg, *.png, *.webp)", "*.jpg;*.jpeg;*.png;*.webp"),
            ("Documentos PDF (*.pdf)", "*.pdf")
        ]
        archivo = filedialog.askopenfilename(title="Seleccionar Nota o Comprobante", filetypes=tipos, parent=self)
        if archivo:
            self.ruta_comprobante_temporal = archivo
            nombre = os.path.basename(archivo)
            self.lbl_comp_nombre.configure(text=f"{ICON_ATTACH}  {nombre}", text_color=self.tema_actual["sidebar_icon"])
            self.btn_quitar_comp.grid()

    def limpiar_comprobante(self):
        self.ruta_comprobante_temporal = None
        self.lbl_comp_nombre.configure(text="Ningún comprobante seleccionado", text_color=("gray50", "gray60"))
        self.btn_quitar_comp.grid_remove()

    def _nombre_comprobante_unico(self, ruta_origen):
        ext = os.path.splitext(ruta_origen)[1].lower()
        return f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"

    def guardar_registro(self):
        fecha_txt = self.in_fecha.get().strip()
        fecha_iso = normalizar_a_iso(fecha_txt)
        if not fecha_iso:
            messagebox.showerror("Fecha inválida", "Usa una fecha válida (ej. 04/11/2026).")
            return

        desc = self.in_desc.get("1.0", "end-1c").strip()
        if not desc:
            messagebox.showwarning("Faltan datos", "Por favor ingresa una descripción del trabajo.")
            return

        raw_km = self.in_km.get().strip()
        km = parsear_entero(raw_km) if raw_km else 0
        if km is None:
            messagebox.showerror("Dato inválido",
                                 "El kilometraje debe ser un número entero.\n\n"
                                 "Formatos válidos: 112800 · 112,800 · 112.800")
            return
        if km < 0:
            messagebox.showerror("Dato inválido", "El kilometraje no puede ser negativo.")
            return

        raw_costo = self.in_costo.get().strip()
        costo = parsear_numero(raw_costo) if raw_costo else 0.0
        if costo is None:
            messagebox.showerror("Dato inválido",
                                 "El costo debe ser un valor numérico.\n\n"
                                 "Formatos válidos: 1450.00 · 1,450.50 · 299,50 · 1.250.50")
            return
        costo = round(costo, 2)
        if costo < 0:
            messagebox.showerror("Dato inválido", "El costo no puede ser negativo.")
            return

        tipo = self.in_tipo.get().strip() or "Sin categoría"
        vehiculo_id = self.db.obtener_o_crear_vehiculo(self.in_vehiculo.get())
        vehiculo_nombre = self.nombre_vehiculo(vehiculo_id)

        filas_v = self.db.query("SELECT anio FROM vehiculos WHERE id = ?", (vehiculo_id,))
        modelo = filas_v[0][0] if filas_v and filas_v[0][0] else None

        ruta_guardada = None
        if self.ruta_comprobante_temporal and os.path.exists(self.ruta_comprobante_temporal):
            nuevo_nombre = self._nombre_comprobante_unico(self.ruta_comprobante_temporal)
            ruta_destino = os.path.join(CARPETA_COMPROBANTES, nuevo_nombre)
            try:
                shutil.copy2(self.ruta_comprobante_temporal, ruta_destino)
                ruta_guardada = nuevo_nombre
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo copiar el comprobante: {e}")
                return

        self.db.execute(
            "INSERT INTO registros (fecha, vehiculo, vehiculo_id, modelo, tipo, kilometraje, costo, "
            "descripcion, taller_lugar, notas, comprobante_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (fecha_iso, vehiculo_nombre, vehiculo_id, modelo, tipo, km, costo, desc,
             self.in_taller.get().strip(), self.in_notas.get("1.0", "end-1c").strip(), ruta_guardada)
        )

        for c in [self.in_km, self.in_costo]:
            c.delete(0, "end")
        self.in_taller.set("")
        self.in_vehiculo.set("")
        self.in_desc.delete("1.0", "end")
        self.in_notas.delete("1.0", "end")
        self.limpiar_comprobante()

        self.refrescar_vehiculos_ui()
        self.mostrar_vista("historial")

    # ------------------ PANTALLA: HISTORIAL ------------------
    def setup_historial(self):
        self.v_his.grid_columnconfigure(0, weight=1)
        self.v_his.grid_rowconfigure(2, weight=1)

        kpi_box = ctk.CTkFrame(self.v_his, fg_color="transparent")
        kpi_box.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        kpi_box.grid_columnconfigure((0, 1, 2), weight=1)
        self.cards_kpi_his = []

        def make_kpi(col, tit):
            f = ctk.CTkFrame(kpi_box, corner_radius=8, fg_color=self.tema_actual["panel_bg"])
            f.grid(row=0, column=col, sticky="ew", padx=6)
            self.cards_kpi_his.append(f)
            ctk.CTkLabel(f, text=tit, font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")).pack(anchor="w", padx=12, pady=(8, 0))
            lbl = ctk.CTkLabel(f, text="-", font=ctk.CTkFont(size=18, weight="bold"), text_color=("#0F172A", "#F8FAFC"))
            lbl.pack(anchor="w", padx=12, pady=(0, 8))
            return lbl

        self.kpi_gasto = make_kpi(0, "Gasto Total")
        self.kpi_serv = make_kpi(1, "Eventos Registrados")
        self.kpi_km = make_kpi(2, "Último Odómetro")

        self.filtros_frame = ctk.CTkFrame(self.v_his, corner_radius=8, fg_color=self.tema_actual["panel_bg"])
        self.filtros_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        bar = ctk.CTkFrame(self.filtros_frame, fg_color="transparent")
        bar.pack(fill="x", padx=6, pady=(8, 4))
        bar.grid_columnconfigure(0, weight=1)

        self.f_busq = ctk.CTkEntry(bar, placeholder_text="Buscar palabra clave, taller o auto...", height=38, corner_radius=6)
        self.f_busq.grid(row=0, column=0, sticky="ew", padx=(6, 4))
        self.f_busq.bind("<Return>", lambda _: self.actualizar_historial())

        self.f_tipo = ctk.CTkComboBox(bar, values=["Todos"] + list(self.badges.keys()), height=38, width=150, corner_radius=6, command=lambda _: self.actualizar_historial())
        self.f_tipo.set("Todos")
        self.f_tipo.grid(row=0, column=1, padx=4)

        self.f_veh = ctk.CTkComboBox(bar, values=["Todos"] + self.lista_vehiculos_nombres(), height=38, width=160, corner_radius=6, command=lambda _: self.actualizar_historial())
        self.f_veh.set("Todos")
        self.f_veh.grid(row=0, column=2, padx=4)

        ctk.CTkButton(
            bar, text="Filtrar", width=85, height=38, corner_radius=6,
            fg_color=("#334155", "#475569"), hover_color=("#1E293B", "#334155"), text_color="#FFFFFF",
            command=self.actualizar_historial
        ).grid(row=0, column=3, padx=(4, 6))

        bar2 = ctk.CTkFrame(self.filtros_frame, fg_color="transparent")
        bar2.pack(fill="x", padx=6, pady=(0, 8))

        estilo_fecha = {"height": 36, "width": 130, "corner_radius": 6}

        ctk.CTkLabel(bar2, text="Desde:", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#1E293B", "#F1F5F9")).pack(side="left", padx=(10, 4))
        self.f_desde = ctk.CTkEntry(bar2, placeholder_text="DD/MM/AAAA", **estilo_fecha)
        self.f_desde.pack(side="left", padx=(0, 4))
        self.f_desde.bind("<Return>", lambda _: self.actualizar_historial())

        self.btn_cal_desde = ctk.CTkButton(
            bar2, text=ICON_CAL, font=FONT_CAL_ICON, width=38, height=36, corner_radius=6,
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"],
            command=lambda: CalendarPicker(self, self.f_desde, self.tema_actual)
        )
        self.btn_cal_desde.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(bar2, text="Hasta:", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#1E293B", "#F1F5F9")).pack(side="left", padx=(0, 4))
        self.f_hasta = ctk.CTkEntry(bar2, placeholder_text="DD/MM/AAAA", **estilo_fecha)
        self.f_hasta.pack(side="left", padx=(0, 4))
        self.f_hasta.bind("<Return>", lambda _: self.actualizar_historial())

        self.btn_cal_hasta = ctk.CTkButton(
            bar2, text=ICON_CAL, font=FONT_CAL_ICON, width=38, height=36, corner_radius=6,
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"],
            command=lambda: CalendarPicker(self, self.f_hasta, self.tema_actual)
        )
        self.btn_cal_hasta.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            bar2, text="Limpiar", image=icono_imagen(ICON_CLEAR, ICON_TAM_PNG), compound="left",
            width=110, height=36, corner_radius=6,
            fg_color=("#64748B", "#475569"), hover_color=("#475569", "#334155"), text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"), command=self.limpiar_fechas
        ).pack(side="left", padx=(0, 6))

        self.btn_imprimir = ctk.CTkButton(
            bar2, text="Imprimir Reporte", image=icono_imagen(ICON_PRINT, ICON_TAM_PNG), compound="left",
            width=160, height=36, corner_radius=6,
            fg_color=("#0D9488", "#0F766E"), hover_color=("#0F766E", "#115E59"), text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"), command=self.imprimir_reporte
        )
        self.btn_imprimir.pack(side="right", padx=(0, 6))

        self.scroll_hist = ctk.CTkScrollableFrame(self.v_his, corner_radius=8, fg_color="transparent")
        self.scroll_hist.grid(row=2, column=0, sticky="nsew")

    def _filtros_sql(self):
        t_sel = self.f_tipo.get()
        v_sel = self.f_veh.get()
        q_sel = self.f_busq.get().strip()
        desde_raw = self.f_desde.get().strip()
        hasta_raw = self.f_hasta.get().strip()
        desde = hasta = ""

        if desde_raw:
            desde = normalizar_a_iso(desde_raw)
            if not desde:
                messagebox.showerror("Fecha inválida", "El campo «Desde» debe tener una fecha válida.")
                return None
        if hasta_raw:
            hasta = normalizar_a_iso(hasta_raw)
            if not hasta:
                messagebox.showerror("Fecha inválida", "El campo «Hasta» debe tener una fecha válida.")
                return None

        if desde and hasta and desde > hasta:
            messagebox.showwarning("Rango inválido", "La fecha «Desde» no puede ser posterior a la fecha «Hasta».")
            return None

        where = " WHERE 1=1"
        params = []
        criterio = []

        if t_sel != "Todos":
            where += " AND tipo = ?"
            params.append(t_sel)
            criterio.append(f"Categoría: {t_sel}")
        if v_sel != "Todos":
            where += " AND (vehiculo = ? OR vehiculo_id = (SELECT id FROM vehiculos WHERE nombre = ?))"
            params.extend([v_sel, v_sel])
            criterio.append(f"Vehículo: {v_sel}")
        if desde:
            where += " AND fecha >= ?"
            params.append(desde)
            criterio.append(f"Desde: {formatear_fecha(desde)}")
        if hasta:
            where += " AND fecha <= ?"
            params.append(hasta)
            criterio.append(f"Hasta: {formatear_fecha(hasta)}")
        if q_sel:
            where += " AND (descripcion LIKE ? OR taller_lugar LIKE ? OR vehiculo LIKE ? OR notas LIKE ?)"
            params.extend([f"%{q_sel}%"] * 4)
            criterio.append(f'Búsqueda: "{q_sel}"')

        return where, params, " | ".join(criterio) if criterio else "Todos"

    def limpiar_fechas(self):
        self.f_desde.delete(0, "end")
        self.f_hasta.delete(0, "end")
        self.f_busq.delete(0, "end")
        self.f_tipo.set("Todos")
        self.f_veh.set("Todos")
        self.actualizar_historial()

    _COLS_HIST = "id, fecha, vehiculo, vehiculo_id, modelo, tipo, kilometraje, costo, descripcion, taller_lugar, notas, comprobante_path"

    def actualizar_historial(self):
        filtro = self._filtros_sql()
        if filtro is None:
            return
        where, params, _ = filtro

        res = self.db.query(
            "SELECT COUNT(*), COALESCE(SUM(costo), 0), COALESCE(MAX(kilometraje), 0) FROM registros" + where,
            params
        )[0]
        self.kpi_gasto.configure(text=f"${res[1]:,.2f}")
        self.kpi_serv.configure(text=f"{res[0]} servicios")
        self.kpi_km.configure(text=f"{res[2]:,} km")

        for w in self.scroll_hist.winfo_children():
            w.destroy()

        regs = self.db.query(
            f"SELECT {self._COLS_HIST} FROM registros" + where + " ORDER BY fecha DESC, id DESC",
            params
        )
        if not regs:
            ctk.CTkLabel(self.scroll_hist, text="No hay registros que coincidan con la búsqueda.",
                         text_color=("gray40", "gray60")).pack(pady=30)
            return

        for r in regs:
            self.crear_tarjeta(r)

    def abrir_comprobante(self, nombre_archivo):
        if not nombre_archivo:
            return
        ruta = os.path.join(CARPETA_COMPROBANTES, nombre_archivo)
        if os.path.exists(ruta):
            abrir_archivo_sistema(ruta)
        else:
            messagebox.showwarning("Archivo no encontrado", f"No se encontró el comprobante en:\n{ruta}")

    def crear_tarjeta(self, r):
        rid, f, veh, vid_reg, mod, tip, km, cos, desc, tal, nots, comp = r

        c = ctk.CTkFrame(self.scroll_hist, corner_radius=8, fg_color=self.tema_actual["panel_bg"])
        c.pack(fill="x", padx=4, pady=4)
        c.grid_columnconfigure(1, weight=1)

        col0 = ctk.CTkFrame(c, fg_color="transparent")
        col0.grid(row=0, column=0, padx=12, pady=10, sticky="nw")
        ctk.CTkLabel(col0, text=formatear_fecha(f), font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=("#0F172A", "#F8FAFC")).pack(anchor="w")

        badge_info = self.badges.get(tip, (("#E2E8F0", "#374151"), ("#374151", "#D1D5DB")))
        ctk.CTkLabel(col0, text=f" {tip} ", fg_color=badge_info[0], text_color=badge_info[1], corner_radius=4,
                     font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", pady=(4, 0))

        col1 = ctk.CTkFrame(c, fg_color="transparent")
        col1.grid(row=0, column=1, padx=8, pady=10, sticky="nsew")

        info_veh = f"{veh} {mod}".strip() if mod else (veh or "General")
        subtitulo = f"{info_veh} • {km:,} km" if km else info_veh
        ctk.CTkLabel(col1, text=subtitulo, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=("#475569", "#94A3B8")).pack(anchor="w")

        lbl_desc = ctk.CTkLabel(col1, text=desc, font=ctk.CTkFont(size=13), wraplength=480, justify="left",
                                text_color=("#0F172A", "#F8FAFC"))
        lbl_desc.pack(anchor="w", pady=2)

        info = []
        if tal: info.append(f"📍 {tal}")
        if nots: info.append(f"📝 {nots}")
        if comp: info.append(f"{ICON_ATTACH} Comprobante adjunto")
        if info:
            ctk.CTkLabel(col1, text="   |   ".join(info), font=ctk.CTkFont(size=11),
                         text_color=("#64748B", "#94A3B8"), wraplength=480, justify="left").pack(anchor="w")

        col2 = ctk.CTkFrame(c, fg_color="transparent")
        col2.grid(row=0, column=2, padx=12, pady=10, sticky="ne")
        ctk.CTkLabel(col2, text=f"${cos:,.2f}" if cos else "$0.00", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=("#059669", "#34D399")).pack(anchor="e")

        acts = ctk.CTkFrame(col2, fg_color="transparent")
        acts.pack(anchor="e", pady=(6, 0))

        if comp:
            ctk.CTkButton(
                acts, text=ICON_ATTACH, font=FONT_CLIP_ICON, width=38, height=34, corner_radius=6,
                fg_color=("#DBEAFE", "#1E40AF"), hover_color=("#BFDBFE", "#2563EB"),
                text_color=("#1D4ED8", "#FFFFFF"),
                command=lambda a=comp: self.abrir_comprobante(a)
            ).pack(side="left", padx=3)

        ctk.CTkButton(
            acts, text=ICON_EDIT, font=FONT_ACTION_ICON, width=38, height=34, corner_radius=6,
            fg_color=("#FEF3C7", "#854D0E"), hover_color=("#FDE68A", "#A16207"),
            text_color=("#B45309", "#FEF08A"),
            command=lambda: self.abrir_editor(rid)
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            acts, text=ICON_DEL, font=FONT_ACTION_ICON, width=38, height=34, corner_radius=6,
            fg_color=("#FEE2E2", "#7F1D1D"), hover_color=("#FECACA", "#991B1B"),
            text_color=("#DC2626", "#FCA5A5"),
            command=lambda: self.borrar_registro(rid, comp)
        ).pack(side="left", padx=3)

    def borrar_registro(self, rid, comp_path=None):
        if messagebox.askyesno("Eliminar", f"¿Deseas eliminar el registro #{rid}?"):
            self.db.execute("DELETE FROM registros WHERE id = ?", (rid,))
            if comp_path:
                ruta = os.path.join(CARPETA_COMPROBANTES, comp_path)
                if os.path.exists(ruta):
                    try:
                        os.remove(ruta)
                    except OSError:
                        pass
            self.actualizar_historial()

    # ------------------ EDICIÓN MODAL ------------------
    def abrir_editor(self, rid):
        filas = self.db.query(f"SELECT {self._COLS_HIST} FROM registros WHERE id = ?", (rid,))
        if not filas:
            self.actualizar_historial()
            return
        rid, f, veh, vid_original, mod, tip, km, cos, desc, tal, nots, comp_original = filas[0]

        modal = ctk.CTkToplevel(self)
        modal.title(f"Modificar #{rid}")
        modal.geometry("540x700")
        modal.grab_set()
        modal.transient(self)

        p = ctk.CTkScrollableFrame(modal, corner_radius=8, fg_color=self.tema_actual["panel_bg"])
        p.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(p, text=f"Editar Registro #{rid}", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=("#0F172A", "#F8FAFC")).pack(anchor="w", padx=10, pady=(5, 10))

        ctk.CTkLabel(p, text="Fecha:", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#1E293B", "#F1F5F9")).pack(anchor="w", padx=10)
        fb = ctk.CTkFrame(p, fg_color="transparent")
        fb.pack(anchor="w", padx=10, pady=(2, 6))
        ef = ctk.CTkEntry(fb, width=390, height=36, corner_radius=6, placeholder_text="DD/MM/AAAA")
        ef.insert(0, formatear_fecha(f))
        ef.pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            fb, text=ICON_CAL, font=FONT_CAL_ICON, width=44, height=36, corner_radius=6,
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"],
            command=lambda: CalendarPicker(modal, ef, self.tema_actual)
        ).pack(side="left")

        def item_edit(txt, val):
            ctk.CTkLabel(p, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=("#1E293B", "#F1F5F9")).pack(anchor="w", padx=10)
            e = ctk.CTkEntry(p, width=436, height=36, corner_radius=6)
            e.insert(0, str(val if val is not None else ""))
            e.pack(anchor="w", padx=10, pady=(2, 6))
            return e

        ctk.CTkLabel(p, text="Vehículo:", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#1E293B", "#F1F5F9")).pack(anchor="w", padx=10)
        ev = ctk.CTkComboBox(p, width=436, height=36, corner_radius=6, values=self.lista_vehiculos_nombres() or ["General"])
        ev.set(veh or "General")
        ev.pack(anchor="w", padx=10, pady=(2, 6))

        ctk.CTkLabel(p, text="Categoría:", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#1E293B", "#F1F5F9")).pack(anchor="w", padx=10)
        etip = ctk.CTkComboBox(p, width=436, height=36, corner_radius=6, values=list(self.badges.keys()))
        etip.set(tip)
        etip.pack(anchor="w", padx=10, pady=(2, 6))

        ek = item_edit("Kilometraje:", f"{km:,}" if km else "")
        ek.bind("<KeyRelease>", lambda e: aplicar_formato_entero(ek, e))

        ec = item_edit("Costo ($):", f"{cos:,.2f}" if cos else "")
        ec.bind("<KeyRelease>", lambda e: aplicar_formato_decimal(ec, e))

        ctk.CTkLabel(p, text="Lugar / Procedencia:", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#1E293B", "#F1F5F9")).pack(anchor="w", padx=10)
        et = ctk.CTkComboBox(p, width=436, height=36, corner_radius=6, values=LUGARES_SUGERIDOS)
        et.set(tal or "")
        et.pack(anchor="w", padx=10, pady=(2, 6))

        ctk.CTkLabel(p, text="Trabajo Realizado:", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#1E293B", "#F1F5F9")).pack(anchor="w", padx=10)
        edesc = ctk.CTkTextbox(p, width=436, height=65, corner_radius=6)
        edesc._textbox.tag_configure("justificado", justify="left")
        edesc.insert("1.0", desc)
        edesc.pack(anchor="w", padx=10, pady=(2, 6))
        activar_corrector_en_vivo(edesc)

        ctk.CTkLabel(p, text="Notas / Garantía:", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#1E293B", "#F1F5F9")).pack(anchor="w", padx=10)
        enots = ctk.CTkTextbox(p, width=436, height=45, corner_radius=6)
        enots._textbox.tag_configure("justificado", justify="left")
        enots.insert("1.0", nots or "")
        enots.pack(anchor="w", padx=10, pady=(2, 12))
        activar_corrector_en_vivo(enots)

        comp_pending = [None]
        ctk.CTkLabel(p, text="Comprobante Adjunto:", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#1E293B", "#F1F5F9")).pack(anchor="w", padx=10)
        box_c = ctk.CTkFrame(p, fg_color="transparent")
        box_c.pack(fill="x", padx=10, pady=(2, 12))

        lbl_c_status = ctk.CTkLabel(box_c, text=f"{ICON_ATTACH}  {comp_original}" if comp_original else "Sin comprobante",
                                    text_color=("gray40", "gray60"), anchor="w")
        lbl_c_status.pack(side="left", expand=True, fill="x")

        def cambiar_comp():
            tipos = [("Comprobantes", "*.jpg;*.jpeg;*.png;*.webp;*.pdf")]
            nuevo = filedialog.askopenfilename(title="Seleccionar Nuevo Comprobante", filetypes=tipos, parent=modal)
            if nuevo:
                comp_pending[0] = {"origen": nuevo, "nombre": self._nombre_comprobante_unico(nuevo)}
                lbl_c_status.configure(text=f"{ICON_ATTACH}  {comp_pending[0]['nombre']}",
                                       text_color=self.tema_actual["sidebar_icon"])

        def quitar_comp():
            comp_pending[0] = {"origen": None, "nombre": None}
            lbl_c_status.configure(text="Sin comprobante", text_color=("gray40", "gray60"))

        ctk.CTkButton(
            box_c, text="Cambiar", width=80, height=30,
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"],
            command=cambiar_comp
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            box_c, text="Quitar", width=70, height=30,
            fg_color=("#FEE2E2", "#7F1D1D"), hover_color=("#FECACA", "#991B1B"),
            text_color=("#DC2626", "#FCA5A5"),
            command=quitar_comp
        ).pack(side="left")

        box_btn = ctk.CTkFrame(p, fg_color="transparent")
        box_btn.pack(fill="x", padx=10, pady=(0, 10))

        def guardar():
            nd = edesc.get("1.0", "end-1c").strip()
            if not nd:
                messagebox.showwarning("Faltan datos", "La descripción no puede estar vacía.", parent=modal)
                return
            raw_km_edit = ek.get().strip()
            nk = parsear_entero(raw_km_edit) if raw_km_edit else 0
            if nk is None:
                messagebox.showerror("Error", "Kilometraje inválido.\nFormatos válidos: 112800 · 112,800 · 112.800", parent=modal)
                return
            if nk < 0:
                messagebox.showerror("Error", "El kilometraje no puede ser negativo.", parent=modal)
                return
            raw_costo_edit = ec.get().strip()
            nc = 0.0
            if raw_costo_edit:
                valor_costo_edit = parsear_numero(raw_costo_edit)
                nc = None if valor_costo_edit is None else round(valor_costo_edit, 2)
            if nc is None:
                messagebox.showerror("Error", "Costo inválido.\nFormatos válidos: 1450.00 · 1,450.50 · 299,50 · 1.000", parent=modal)
                return
            if nc < 0:
                messagebox.showerror("Error", "El costo no puede ser negativo.", parent=modal)
                return

            fecha_iso = normalizar_a_iso(ef.get().strip())
            if not fecha_iso:
                messagebox.showerror("Fecha inválida", "Usa una fecha válida.", parent=modal)
                return

            if comp_pending[0] is not None:
                comp_final = comp_pending[0]["nombre"]
                if comp_final:
                    try:
                        shutil.copy2(comp_pending[0]["origen"],
                                     os.path.join(CARPETA_COMPROBANTES, comp_final))
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo copiar el comprobante: {e}", parent=modal)
                        return
            else:
                comp_final = comp_original

            nuevo_nombre = ev.get().strip()
            if vid_original:
                vid = vid_original
                if nuevo_nombre and nuevo_nombre != (veh or ""):
                    vid = self.db.obtener_o_crear_vehiculo(nuevo_nombre)
            elif nuevo_nombre:
                vid = self.db.obtener_o_crear_vehiculo(nuevo_nombre)
            else:
                vid = None
            veh_nombre = self.nombre_vehiculo(vid) if vid else "General"

            filas_v = self.db.query("SELECT anio FROM vehiculos WHERE id = ?", (vid,)) if vid else []
            nmod = filas_v[0][0] if filas_v and filas_v[0][0] else None

            try:
                self.db.execute(
                    "UPDATE registros SET fecha=?, vehiculo=?, vehiculo_id=?, modelo=?, tipo=?, "
                    "kilometraje=?, costo=?, descripcion=?, taller_lugar=?, notas=?, comprobante_path=? WHERE id=?",
                    (fecha_iso, veh_nombre, vid, nmod, etip.get(), nk, nc, nd, et.get().strip(),
                     enots.get("1.0", "end-1c").strip(), comp_final, rid)
                )
            except Exception as e:
                if comp_final and comp_final != comp_original:
                    try:
                        os.remove(os.path.join(CARPETA_COMPROBANTES, comp_final))
                    except OSError:
                        pass
                messagebox.showerror("Error", f"No se pudo actualizar el registro: {e}", parent=modal)
                return

            if comp_original and comp_final != comp_original:
                ruta_antigua = os.path.join(CARPETA_COMPROBANTES, comp_original)
                if os.path.exists(ruta_antigua):
                    try:
                        os.remove(ruta_antigua)
                    except OSError:
                        pass

            modal.destroy()
            self.refrescar_vehiculos_ui()
            self.actualizar_historial()

        bsave = ctk.CTkButton(
            box_btn, text="Guardar Cambios", width=140, height=36, font=ctk.CTkFont(weight="bold"),
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"],
            command=guardar
        )
        bcancel = ctk.CTkButton(
            box_btn, text="Cancelar", fg_color=("#64748B", "#475569"), hover_color=("#475569", "#334155"),
            text_color="#FFFFFF", width=90, height=36, command=modal.destroy
        )
        bsave.pack(side="right", padx=(8, 0))
        bcancel.pack(side="right")

        self.vincular_tab([ef, ev, etip, ek, ec, et, edesc, enots, bsave, bcancel])
        ef.focus_set()

    # ------------------ VEHÍCULOS ------------------
    def lista_vehiculos_nombres(self):
        filas = self.db.query("SELECT nombre FROM vehiculos ORDER BY nombre COLLATE NOCASE")
        return [f[0] for f in filas]

    def nuevo_vehiculo_desde_captura(self):
        def seleccionar(nombre):
            self.in_vehiculo.set(nombre)
        self.modal_vehiculo(al_guardar=seleccionar)

    def nombre_vehiculo(self, vehiculo_id):
        return self.db.nombre_vehiculo(vehiculo_id)

    def refrescar_vehiculos_ui(self):
        nombres = self.lista_vehiculos_nombres() or ["General"]
        self.in_vehiculo.configure(values=nombres)
        self.f_veh.configure(values=["Todos"] + nombres)
        self.actualizar_vehiculos()
        self.actualizar_alertas()
        self.actualizar_badge_alertas()

    def setup_vehiculos(self):
        self.v_veh.grid_columnconfigure(0, weight=1)
        self.v_veh.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(self.v_veh, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(top, text="Mis Vehículos", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=("#0F172A", "#F8FAFC")).pack(side="left")

        self.btn_nuevo_veh = ctk.CTkButton(
            top, text="Nuevo Vehículo", image=icono_imagen(ICON_ADD, ICON_TAM_PNG), compound="left",
            width=190, height=38, corner_radius=6,
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"],
            font=ctk.CTkFont(size=12, weight="bold"), command=lambda: self.modal_vehiculo()
        )
        self.btn_nuevo_veh.pack(side="right")

        self.lbl_veh_resumen = ctk.CTkLabel(self.v_veh, text="", font=ctk.CTkFont(size=12), text_color=("gray40", "gray60"))
        self.lbl_veh_resumen.grid(row=1, column=0, sticky="w", pady=(0, 8))

        self.scroll_veh = ctk.CTkScrollableFrame(self.v_veh, corner_radius=8, fg_color="transparent")
        self.scroll_veh.grid(row=2, column=0, sticky="nsew")

    def actualizar_vehiculos(self):
        for w in self.scroll_veh.winfo_children():
            w.destroy()

        vehs = self.db.query("""
            SELECT v.id, v.nombre, v.anio, v.placas, v.notas, v.foto_path, v.fecha_compra, v.km_inicial, v.precio_compra,
                   COUNT(r.id), COALESCE(SUM(r.costo), 0), COALESCE(MAX(r.kilometraje), 0)
            FROM vehiculos v
            LEFT JOIN registros r ON r.vehiculo_id = v.id
            GROUP BY v.id
            ORDER BY v.nombre COLLATE NOCASE
        """)

        self.lbl_veh_resumen.configure(text=f"{len(vehs)} vehículo(s) registrado(s)")

        if not vehs:
            ctk.CTkLabel(
                self.scroll_veh,
                text="Aún no hay vehículos.\nUsa “Nuevo Vehículo” o guarda un registro para crear uno.",
                text_color=("gray40", "gray60"), justify="center"
            ).pack(pady=30)
            return

        for v in vehs:
            self.crear_tarjeta_vehiculo(v)

    def abrir_visor_foto(self, ruta_foto, titulo_auto):
        if not ruta_foto:
            return
        ruta = os.path.join(CARPETA_FOTOS, ruta_foto)
        if not os.path.exists(ruta):
            messagebox.showwarning("Foto no encontrada", "El archivo de imagen no existe.")
            return

        visor = ctk.CTkToplevel(self)
        visor.title(f"Fotografía • {titulo_auto}")
        visor.geometry("640x520")
        visor.grab_set()
        visor.transient(self)

        try:
            pil_img = Image.open(ruta)
            pil_img.thumbnail((600, 440))
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)

            lbl = ctk.CTkLabel(visor, image=ctk_img, text="")
            lbl.pack(expand=True, padx=20, pady=20)
        except Exception as e:
            ctk.CTkLabel(visor, text=f"No se pudo cargar la imagen:\n{e}").pack(expand=True)

        ctk.CTkButton(
            visor, text="Cerrar", width=100, height=32, command=visor.destroy,
            fg_color=("#334155", "#475569")
        ).pack(pady=(0, 15))

    def crear_tarjeta_vehiculo(self, v):
        vid, nombre, anio, placas, notas, foto, f_compra, km_ini, p_compra, n_reg, gasto, km_max = v

        c = ctk.CTkFrame(self.scroll_veh, corner_radius=8, fg_color=self.tema_actual["panel_bg"])
        c.pack(fill="x", padx=4, pady=4)
        c.grid_columnconfigure(1, weight=1)

        col0 = ctk.CTkFrame(c, fg_color="transparent", width=80)
        col0.grid(row=0, column=0, padx=12, pady=12, sticky="nw")

        titulo = f"{nombre} {anio}".strip() if anio else nombre

        foto_cargada = False
        if foto:
            ruta_img = os.path.join(CARPETA_FOTOS, foto)
            if os.path.exists(ruta_img):
                try:
                    pil_mini = Image.open(ruta_img)
                    pil_mini.thumbnail((64, 64))
                    mini_ctk = ctk.CTkImage(light_image=pil_mini, dark_image=pil_mini, size=pil_mini.size)

                    lbl_foto = ctk.CTkLabel(col0, image=mini_ctk, text="", cursor="hand2")
                    lbl_foto.pack(anchor="center")
                    lbl_foto.bind("<Button-1>", lambda e, f=foto, t=titulo: self.abrir_visor_foto(f, t))

                    btn_zoom = ctk.CTkButton(
                        col0, text="Ver", image=icono_imagen(ICON_ZOOM, 11), compound="left",
                        width=64, height=20, font=ctk.CTkFont(size=10),
                        fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
                        text_color=self.tema_actual["accent_text"],
                        command=lambda f=foto, t=titulo: self.abrir_visor_foto(f, t)
                    )
                    btn_zoom.pack(pady=(4, 0))
                    foto_cargada = True
                except Exception:
                    pass

        if not foto_cargada:
            ctk.CTkLabel(col0, text=ICON_CAR, font=(FAMILIA_ICONOS, ICON_TAM_EMPTY)).pack(anchor="center", pady=5)

        col1 = ctk.CTkFrame(c, fg_color="transparent")
        col1.grid(row=0, column=1, sticky="nsew", padx=8, pady=12)

        ctk.CTkLabel(col1, text=titulo, font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=("#0F172A", "#F8FAFC")).pack(anchor="w")

        detalles_top = []
        if placas: detalles_top.append(f"Placas: {placas}")
        if f_compra: detalles_top.append(f"Compra: {formatear_fecha(f_compra)}")
        if p_compra: detalles_top.append(f"Precio compra: ${p_compra:,.2f}")
        if km_ini is not None: detalles_top.append(f"Km inicial: {km_ini:,} km")
        if detalles_top:
            ctk.CTkLabel(col1, text="  •  ".join(detalles_top), font=ctk.CTkFont(size=11),
                         text_color=("#64748B", "#94A3B8")).pack(anchor="w")

        stats = f"{n_reg} servicio(s)  •  ${gasto:,.2f} invertidos"
        odometro_final = max(km_max or 0, km_ini or 0)
        if odometro_final:
            stats += f"  •  Odómetro: {odometro_final:,} km"
        ctk.CTkLabel(col1, text=stats, font=ctk.CTkFont(size=12),
                     text_color=("#475569", "#94A3B8")).pack(anchor="w", pady=(3, 0))

        if notas:
            ctk.CTkLabel(col1, text=notas, font=ctk.CTkFont(size=11), text_color=("#64748B", "#94A3B8"),
                         wraplength=440, justify="left").pack(anchor="w", pady=(3, 0))

        col2 = ctk.CTkFrame(c, fg_color="transparent")
        col2.grid(row=0, column=2, padx=12, pady=12, sticky="ne")

        ctk.CTkButton(
            col2, text=ICON_CHART, font=FONT_ACTION_ICON, width=38, height=34, corner_radius=6,
            fg_color=("#DBEAFE", "#1E40AF"), hover_color=("#BFDBFE", "#2563EB"),
            text_color=("#1D4ED8", "#FFFFFF"),
            command=lambda n=nombre: self.ver_historial_vehiculo(n)
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            col2, text=ICON_EDIT, font=FONT_ACTION_ICON, width=38, height=34, corner_radius=6,
            fg_color=("#FEF3C7", "#854D0E"), hover_color=("#FDE68A", "#A16207"),
            text_color=("#B45309", "#FEF08A"),
            command=lambda vv=v: self.modal_vehiculo(vv)
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            col2, text=ICON_DEL, font=FONT_ACTION_ICON, width=38, height=34, corner_radius=6,
            fg_color=("#FEE2E2", "#7F1D1D"), hover_color=("#FECACA", "#991B1B"),
            text_color=("#DC2626", "#FCA5A5"),
            command=lambda vv=v: self.eliminar_vehiculo(vv)
        ).pack(side="left", padx=3)

    def ver_historial_vehiculo(self, nombre):
        self.f_veh.set(nombre)
        self.f_tipo.set("Todos")
        self.mostrar_vista("historial")

    def modal_vehiculo(self, vehiculo=None, al_guardar=None):
        vid = vehiculo[0] if vehiculo else None
        nombre_act = vehiculo[1] if vehiculo else ""
        anio_act = vehiculo[2] if vehiculo else None
        placas_act = vehiculo[3] if vehiculo else ""
        notas_act = vehiculo[4] if vehiculo else ""
        foto_act = vehiculo[5] if vehiculo and len(vehiculo) > 5 else None
        f_compra_act = vehiculo[6] if vehiculo and len(vehiculo) > 6 else ""
        km_ini_act = vehiculo[7] if vehiculo and len(vehiculo) > 7 else None
        p_compra_act = vehiculo[8] if vehiculo and len(vehiculo) > 8 else None

        m = ctk.CTkToplevel(self)
        m.title("Editar Vehículo" if vid else "Nuevo Vehículo")
        m.geometry("490x670")
        m.grab_set()
        m.transient(self)
        m.after(10, m.focus_force)

        p = ctk.CTkScrollableFrame(m, corner_radius=8, fg_color=self.tema_actual["panel_bg"])
        p.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(p, text="Editar Vehículo" if vid else "Nuevo Vehículo", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=("#0F172A", "#F8FAFC")).pack(anchor="w", pady=(0, 8))

        def etiqueta(txt):
            ctk.CTkLabel(p, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=("#1E293B", "#F1F5F9")).pack(anchor="w", pady=(6, 2))

        etiqueta("Marca / Submarca:")
        enom = ctk.CTkEntry(p, height=36, corner_radius=6, placeholder_text="Ej. Toyota Corolla, Mazda 3...")
        enom.insert(0, nombre_act)
        enom.pack(fill="x")

        etiqueta("Año:")
        eanio = ctk.CTkComboBox(p, height=36, corner_radius=6, values=LISTA_ANIOS)
        val_defecto = str(anio_act) if (anio_act and str(anio_act) in LISTA_ANIOS) else LISTA_ANIOS[0]
        eanio.set(val_defecto)
        eanio.pack(fill="x")

        etiqueta("Placas:")
        eplacas = ctk.CTkEntry(p, height=36, corner_radius=6, placeholder_text="Ej. ABC-123-A")
        eplacas.insert(0, placas_act or "")
        eplacas.pack(fill="x")

        etiqueta("Fecha de compra:")
        fc_box = ctk.CTkFrame(p, fg_color="transparent")
        fc_box.pack(fill="x", pady=(0, 4))
        ef_compra = ctk.CTkEntry(fc_box, height=36, corner_radius=6, placeholder_text="Ej. DD/MM/AAAA")
        ef_compra.insert(0, formatear_fecha(f_compra_act) if f_compra_act else "")
        ef_compra.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(
            fc_box, text=ICON_CAL, font=FONT_CAL_ICON, width=44, height=36, corner_radius=6,
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"],
            command=lambda: CalendarPicker(m, ef_compra, self.tema_actual)
        ).pack(side="left")

        etiqueta("Precio de compra ($):")
        ep_compra = ctk.CTkEntry(p, height=36, corner_radius=6, placeholder_text="Ej. 185,000.00")
        if p_compra_act is not None:
            ep_compra.insert(0, f"{p_compra_act:,.2f}")
        ep_compra.bind("<KeyRelease>", lambda e: aplicar_formato_decimal(ep_compra, e))
        ep_compra.pack(fill="x")

        etiqueta("Kilometraje inicial al adquirir:")
        ekm_ini = ctk.CTkEntry(p, height=36, corner_radius=6, placeholder_text="Ej. 45,000")
        if km_ini_act is not None:
            ekm_ini.insert(0, f"{km_ini_act:,}")
        ekm_ini.bind("<KeyRelease>", lambda e: aplicar_formato_entero(ekm_ini, e))
        ekm_ini.pack(fill="x")

        etiqueta("Foto del vehículo:")
        foto_box = ctk.CTkFrame(p, fg_color="transparent")
        foto_box.pack(fill="x", pady=(2, 6))

        foto_pending = [None]
        foto_quitada = [False]

        def texto_foto():
            if foto_pending[0]:
                return f"{ICON_PHOTO} {foto_pending[0]['nombre']}"
            if foto_quitada[0]:
                return "Sin foto"
            return f"{ICON_PHOTO} {foto_act}" if foto_act else "Sin foto"

        lbl_foto_status = ctk.CTkLabel(foto_box, text=texto_foto(), text_color=("gray40", "gray60"))
        lbl_foto_status.pack(side="left", fill="x", expand=True, anchor="w")

        def seleccionar_foto():
            archivo = filedialog.askopenfilename(
                title="Seleccionar foto del vehículo",
                filetypes=[("Imágenes", "*.jpg;*.jpeg;*.png;*.webp")],
                parent=m
            )
            if archivo:
                ext = os.path.splitext(archivo)[1].lower()
                nomb = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}{ext}"
                foto_pending[0] = {"origen": archivo, "nombre": nomb}
                foto_quitada[0] = False
                lbl_foto_status.configure(text=texto_foto(), text_color=self.tema_actual["sidebar_icon"])

        def quitar_foto():
            foto_pending[0] = None
            foto_quitada[0] = True
            lbl_foto_status.configure(text=texto_foto(), text_color=("gray40", "gray60"))

        ctk.CTkButton(foto_box, text="Subir", width=70, height=30,
                      fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
                      text_color=self.tema_actual["accent_text"], command=seleccionar_foto).pack(side="left", padx=4)
        ctk.CTkButton(foto_box, text="Quitar", width=70, height=30,
                      fg_color=("#FEE2E2", "#7F1D1D"), hover_color=("#FECACA", "#991B1B"),
                      text_color=("#DC2626", "#FCA5A5"), command=quitar_foto).pack(side="left")

        etiqueta("Notas:")
        enotas = ctk.CTkTextbox(p, height=65, corner_radius=6)
        enotas._textbox.tag_configure("justificado", justify="left")
        enotas.insert("1.0", notas_act or "")
        enotas.pack(fill="x")
        activar_corrector_en_vivo(enotas)

        def guardar():
            nom = enom.get().strip()
            if not nom:
                messagebox.showwarning("Faltan datos", "El campo Marca / Submarca es obligatorio.", parent=m)
                return
            anio_txt = eanio.get().strip()
            try:
                anio_val = int(anio_txt) if anio_txt else None
            except ValueError:
                messagebox.showerror("Dato inválido", "El año debe ser numérico.", parent=m)
                return

            f_compra_txt = ef_compra.get().strip() or None
            f_compra_iso = normalizar_a_iso(f_compra_txt) if f_compra_txt else None
            if f_compra_txt and not f_compra_iso:
                messagebox.showerror("Fecha inválida", "Usa una fecha válida para la compra.", parent=m)
                return

            raw_p_compra = ep_compra.get().strip()
            p_compra_val = parsear_numero(raw_p_compra) if raw_p_compra else None
            if raw_p_compra and p_compra_val is None:
                messagebox.showerror("Dato inválido",
                                     "El precio de compra debe ser un número válido.\n\n"
                                     "Formatos válidos: 170000.00 · 170,000.00 · 170.000,00", parent=m)
                return
            if p_compra_val is not None:
                p_compra_val = round(p_compra_val, 2)
            if p_compra_val is not None and p_compra_val < 0:
                messagebox.showerror("Dato inválido", "El precio de compra no puede ser negativo.", parent=m)
                return

            raw_km_ini = ekm_ini.get().strip()
            km_ini_val = parsear_entero(raw_km_ini) if raw_km_ini else None
            if raw_km_ini and km_ini_val is None:
                messagebox.showerror("Dato inválido",
                                     "El kilometraje inicial debe ser un número entero.\n\n"
                                     "Formatos válidos: 112000 · 112,000 · 112.000", parent=m)
                return
            if km_ini_val is not None and km_ini_val < 0:
                messagebox.showerror("Dato inválido", "El kilometraje inicial no puede ser negativo.", parent=m)
                return

            if foto_pending[0]:
                foto_final = foto_pending[0]["nombre"]
                try:
                    shutil.copy2(foto_pending[0]["origen"], os.path.join(CARPETA_FOTOS, foto_final))
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo copiar la foto: {e}", parent=m)
                    return
            elif foto_quitada[0]:
                foto_final = None
            else:
                foto_final = foto_act

            try:
                if vid:
                    self.db.execute(
                        "UPDATE vehiculos SET nombre=?, anio=?, placas=?, notas=?, foto_path=?, "
                        "fecha_compra=?, km_inicial=?, precio_compra=? WHERE id=?",
                        (nom, anio_val, eplacas.get().strip(), enotas.get("1.0", "end-1c").strip(),
                         foto_final, f_compra_iso, km_ini_val, p_compra_val, vid)
                    )
                else:
                    self.db.execute_insert(
                        "INSERT INTO vehiculos (nombre, anio, placas, notas, foto_path, fecha_compra, km_inicial, precio_compra) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (nom, anio_val, eplacas.get().strip(), enotas.get("1.0", "end-1c").strip(),
                         foto_final, f_compra_iso, km_ini_val, p_compra_val)
                    )
            except sqlite3.IntegrityError:
                if foto_pending[0] and os.path.exists(os.path.join(CARPETA_FOTOS, foto_final or "")):
                    try:
                        os.remove(os.path.join(CARPETA_FOTOS, foto_final))
                    except OSError:
                        pass
                messagebox.showerror("Duplicado", "Ya existe un vehículo con esa Marca / Submarca.", parent=m)
                return

            if vid and nom != nombre_act:
                self.db.execute("UPDATE registros SET vehiculo = ? WHERE vehiculo_id = ?", (nom, vid))
            if vid and foto_act and (foto_act != foto_final or foto_final is None):
                ruta_ant = os.path.join(CARPETA_FOTOS, foto_act)
                if os.path.exists(ruta_ant):
                    try:
                        os.remove(ruta_ant)
                    except OSError:
                        pass

            m.destroy()
            self.refrescar_vehiculos_ui()
            if al_guardar:
                al_guardar(nom)

        box = ctk.CTkFrame(p, fg_color="transparent")
        box.pack(fill="x", pady=(14, 0))
        ctk.CTkButton(
            box, text="Guardar", width=120, height=36, font=ctk.CTkFont(weight="bold"),
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"],
            command=guardar
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            box, text="Cancelar", width=90, height=36,
            fg_color=("#64748B", "#475569"), hover_color=("#475569", "#334155"), text_color="#FFFFFF",
            command=m.destroy
        ).pack(side="right")

        self.vincular_tab([enom, eanio, eplacas, ef_compra, ep_compra, ekm_ini, enotas])
        enom.focus_set()

    def eliminar_vehiculo(self, v):
        vid, nombre = v[0], v[1]
        n = self.db.query("SELECT COUNT(*) FROM registros WHERE vehiculo_id = ?", (vid,))[0][0]
        if n:
            messagebox.showwarning(
                "No se puede eliminar",
                f"“{nombre}” tiene {n} registro(s) asociados.\nElimina o reasigna esos registros primero."
            )
            return
        if messagebox.askyesno("Eliminar vehículo", f"¿Eliminar “{nombre}” y sus recordatorios?"):
            self.db.execute("DELETE FROM vehiculos WHERE id = ?", (vid,))
            self.db.execute("DELETE FROM recordatorios WHERE vehiculo_id = ?", (vid,))
            self.refrescar_vehiculos_ui()

    # ------------------ ALERTAS DE MANTENIMIENTO ------------------
    def setup_alertas(self):
        self.v_alert.grid_columnconfigure(0, weight=1)
        self.v_alert.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(self.v_alert, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(top, text="Alertas de Mantenimiento", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=("#0F172A", "#F8FAFC")).pack(side="left")

        self.btn_nuevo_rec = ctk.CTkButton(
            top, text="Nuevo Recordatorio", image=icono_imagen(ICON_ADD, ICON_TAM_PNG), compound="left",
            width=220, height=38, corner_radius=6,
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"],
            font=ctk.CTkFont(size=12, weight="bold"), command=lambda: self.modal_recordatorio()
        )
        self.btn_nuevo_rec.pack(side="right")

        kpi = ctk.CTkFrame(self.v_alert, fg_color="transparent")
        kpi.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        kpi.grid_columnconfigure((0, 1, 2), weight=1)
        self.cards_kpi_alert = []

        def kpi_card(col, titulo, color):
            f = ctk.CTkFrame(kpi, corner_radius=8, fg_color=self.tema_actual["panel_bg"])
            f.grid(row=0, column=col, sticky="ew", padx=6)
            self.cards_kpi_alert.append(f)
            ctk.CTkLabel(f, text=titulo, font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")).pack(anchor="w", padx=12, pady=(8, 0))
            lbl = ctk.CTkLabel(f, text="-", font=ctk.CTkFont(size=18, weight="bold"), text_color=color)
            lbl.pack(anchor="w", padx=12, pady=(0, 8))
            return lbl

        self.kpi_venc = kpi_card(0, "Vencidos", ("#DC2626", "#FCA5A5"))
        self.kpi_prox = kpi_card(1, "Por vencer", ("#B45309", "#FDE047"))
        self.kpi_ok = kpi_card(2, "Al día", ("#059669", "#34D399"))

        self.scroll_alert = ctk.CTkScrollableFrame(self.v_alert, corner_radius=8, fg_color="transparent")
        self.scroll_alert.grid(row=2, column=0, sticky="nsew")

    def km_actual_vehiculo(self, vehiculo_id):
        filas = self.db.query("SELECT COALESCE(MAX(kilometraje), 0) FROM registros WHERE vehiculo_id = ?", (vehiculo_id,))
        km_reg = int(filas[0][0] or 0)
        km_ini_q = self.db.query("SELECT COALESCE(km_inicial, 0) FROM vehiculos WHERE id = ?", (vehiculo_id,))
        km_ini = int(km_ini_q[0][0] or 0) if km_ini_q else 0
        return max(km_reg, km_ini)

    def evaluar_recordatorio(self, rec):
        _, vid, _, ival_km, ival_mes, ufecha, ukm, _ = rec[:8]
        km_actual = self.km_actual_vehiculo(vid)
        estado = "ok"
        lineas = []
        dias = None
        km_faltan = None

        def marcar(nuevo):
            nonlocal estado
            if ORDEN_ESTADO[nuevo] > ORDEN_ESTADO[estado]:
                estado = nuevo

        if ival_mes and ufecha:
            vence = sumar_meses(ufecha, ival_mes)
            if vence:
                dias = (vence - date.today()).days
                if dias < 0:
                    marcar("vencido")
                    lineas.append(f"📅 Vence {formatear_fecha(vence)} · hace {abs(dias)} días")
                else:
                    if dias <= DIAS_AVISO:
                        marcar("por_vencer")
                    lineas.append(f"📅 Vence {formatear_fecha(vence)} · faltan {dias} días")
            else:
                lineas.append("📅 Fecha de último servicio inválida")

        if ival_km and ukm is not None:
            proximo = int(ukm) + int(ival_km)
            km_faltan = proximo - km_actual
            if km_faltan <= 0:
                marcar("vencido")
                lineas.append(f"🛞 Programado a {proximo:,} km · excedido por {abs(km_faltan):,} km")
            else:
                if km_faltan <= KM_AVISO:
                    marcar("por_vencer")
                lineas.append(f"🛞 Programado a {proximo:,} km · faltan {km_faltan:,} km")

        if not lineas:
            lineas.append("Sin intervalo definido")

        orden = (
            ORDEN_ESTADO[estado],
            dias if dias is not None else 9999,
            km_faltan if km_faltan is not None else 999999,
        )
        return {"estado": estado, "lineas": lineas, "dias": dias, "km_faltan": km_faltan, "orden": orden}

    def _recordatorios(self):
        return self.db.query("""
            SELECT r.id, r.vehiculo_id, r.tipo, r.intervalo_km, r.intervalo_meses,
                   r.ultima_fecha, r.ultimo_km, r.notas, v.nombre
            FROM recordatorios r
            JOIN vehiculos v ON v.id = r.vehiculo_id
        """)

    def actualizar_alertas(self):
        for w in self.scroll_alert.winfo_children():
            w.destroy()

        recs = self._recordatorios()

        evaluados = []
        conteo = {"vencido": 0, "por_vencer": 0, "ok": 0}
        for rec in recs:
            datos = self.evaluar_recordatorio(rec)
            conteo[datos["estado"]] += 1
            evaluados.append((datos["orden"], rec, datos))

        evaluados.sort(key=lambda x: x[0])
        self.kpi_venc.configure(text=str(conteo["vencido"]))
        self.kpi_prox.configure(text=str(conteo["por_vencer"]))
        self.kpi_ok.configure(text=str(conteo["ok"]))

        if not evaluados:
            ctk.CTkLabel(
                self.scroll_alert,
                text="No hay recordatorios configurados.\nCrea uno para vigilar aceite, verificación, seguro, tenencia, etc.",
                text_color=("gray40", "gray60"), justify="center"
            ).pack(pady=30)
            return

        for _, rec, datos in evaluados:
            self.crear_tarjeta_alerta(rec, datos)

    def crear_tarjeta_alerta(self, rec, datos):
        rid, _, tipo, _, _, ufecha, ukm, notas, nombre_veh = rec
        bg, fg, etiqueta = ESTADOS_ALERTA[datos["estado"]]

        c = ctk.CTkFrame(self.scroll_alert, corner_radius=8, fg_color=self.tema_actual["panel_bg"])
        c.pack(fill="x", padx=4, pady=4)
        c.grid_columnconfigure(1, weight=1)

        col0 = ctk.CTkFrame(c, fg_color="transparent")
        col0.grid(row=0, column=0, padx=14, pady=12, sticky="nw")
        ctk.CTkLabel(col0, text=f" {etiqueta} ", fg_color=bg, text_color=fg, corner_radius=4,
                     font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w")

        col1 = ctk.CTkFrame(c, fg_color="transparent")
        col1.grid(row=0, column=1, sticky="nsew", padx=8, pady=12)
        ctk.CTkLabel(col1, text=f"{ICON_BELL} {tipo}", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=("#0F172A", "#F8FAFC")).pack(anchor="w")
        ctk.CTkLabel(col1, text=f"{ICON_CAR} {nombre_veh}", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=("#475569", "#94A3B8")).pack(anchor="w")

        for linea in datos["lineas"]:
            ctk.CTkLabel(col1, text=linea, font=ctk.CTkFont(size=12), text_color=("#334155", "#CBD5E1")).pack(anchor="w", pady=(2, 0))

        ultimo = []
        if ufecha: ultimo.append(f"Último: {formatear_fecha(ufecha)}")
        if ukm is not None: ultimo.append(f"{ukm:,} km")
        if ultimo:
            ctk.CTkLabel(col1, text=" · ".join(ultimo), font=ctk.CTkFont(size=10),
                         text_color=("#64748B", "#94A3B8")).pack(anchor="w", pady=(4, 0))

        if notas:
            ctk.CTkLabel(col1, text=f"📝 {notas}", font=ctk.CTkFont(size=11), text_color=("#64748B", "#94A3B8"),
                         wraplength=420, justify="left").pack(anchor="w", pady=(2, 0))

        col2 = ctk.CTkFrame(c, fg_color="transparent")
        col2.grid(row=0, column=2, padx=12, pady=12, sticky="ne")

        ctk.CTkButton(
            col2, text=ICON_CHECK, font=FONT_ACTION_ICON, width=38, height=34, corner_radius=6,
            fg_color=("#D1FAE5", "#064E3B"), hover_color=("#A7F3D0", "#065F46"),
            text_color=("#047857", "#6EE7B7"),
            command=lambda i=rid: self.completar_recordatorio(i)
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            col2, text=ICON_EDIT, font=FONT_ACTION_ICON, width=38, height=34, corner_radius=6,
            fg_color=("#FEF3C7", "#854D0E"), hover_color=("#FDE68A", "#A16207"),
            text_color=("#B45309", "#FEF08A"),
            command=lambda rr=rec: self.modal_recordatorio(rr)
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            col2, text=ICON_DEL, font=FONT_ACTION_ICON, width=38, height=34, corner_radius=6,
            fg_color=("#FEE2E2", "#7F1D1D"), hover_color=("#FECACA", "#991B1B"),
            text_color=("#DC2626", "#FCA5A5"),
            command=lambda i=rid: self.eliminar_recordatorio(i)
        ).pack(side="left", padx=3)

    def modal_recordatorio(self, rec=None):
        vehiculos = self.db.query("SELECT id, nombre FROM vehiculos ORDER BY nombre COLLATE NOCASE")
        if not vehiculos:
            messagebox.showwarning("Sin vehículos", "Primero registra un vehículo en la sección “Vehículos”.")
            return

        rid = rec[0] if rec else None
        vid_act = rec[1] if rec else vehiculos[0][0]
        tipo_act = rec[2] if rec else TIPOS_RECORDATORIO[0]
        ival_km_act = rec[3] if rec else None
        ival_mes_act = rec[4] if rec else None
        fecha_act = rec[5] if rec else date.today().strftime("%Y-%m-%d")
        km_act = rec[6] if rec else self.km_actual_vehiculo(vid_act)
        notas_act = rec[7] if rec else ""

        m = ctk.CTkToplevel(self)
        m.title("Editar Recordatorio" if rid else "Nuevo Recordatorio")
        m.geometry("470x660")
        m.grab_set()
        m.transient(self)
        m.after(10, m.focus_force)

        p = ctk.CTkScrollableFrame(m, corner_radius=8, fg_color=self.tema_actual["panel_bg"])
        p.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(p, text="Editar Recordatorio" if rid else "Nuevo Recordatorio", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=("#0F172A", "#F8FAFC")).pack(anchor="w", padx=10, pady=(5, 8))

        def etiqueta(txt):
            ctk.CTkLabel(p, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=("#1E293B", "#F1F5F9")).pack(anchor="w", padx=10, pady=(6, 2))

        etiqueta("Vehículo:")
        ev = ctk.CTkComboBox(p, width=400, height=36, corner_radius=6, values=[v[1] for v in vehiculos])
        ev.set(next((v[1] for v in vehiculos if v[0] == vid_act), vehiculos[0][1]))
        ev.pack(anchor="w", padx=10)

        etiqueta("Tipo de mantenimiento:")
        etipo = ctk.CTkComboBox(p, width=400, height=36, corner_radius=6, values=TIPOS_RECORDATORIO)
        etipo.set(tipo_act)
        etipo.pack(anchor="w", padx=10)

        etiqueta("Cada cuántos meses (opcional):")
        emes = ctk.CTkEntry(p, width=400, height=36, corner_radius=6, placeholder_text="Ej. 6")
        if ival_mes_act: emes.insert(0, str(ival_mes_act))
        emes.pack(anchor="w", padx=10)

        etiqueta("Cada cuántos km (opcional):")
        ekm = ctk.CTkEntry(p, width=400, height=36, corner_radius=6, placeholder_text="Ej. 5,000")
        if ival_km_act: ekm.insert(0, f"{ival_km_act:,}")
        ekm.bind("<KeyRelease>", lambda e: aplicar_formato_entero(ekm, e))
        ekm.pack(anchor="w", padx=10)

        etiqueta("Última fecha de servicio:")
        fb = ctk.CTkFrame(p, fg_color="transparent")
        fb.pack(anchor="w", padx=10, pady=(2, 0))
        ef = ctk.CTkEntry(fb, width=352, height=36, corner_radius=6, placeholder_text="DD/MM/AAAA")
        ef.insert(0, formatear_fecha(fecha_act) if fecha_act else "")
        ef.pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            fb, text=ICON_CAL, font=FONT_CAL_ICON, width=42, height=36, corner_radius=6,
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"],
            command=lambda: CalendarPicker(m, ef, self.tema_actual)
        ).pack(side="left")

        etiqueta("Último odómetro (km):")
        eod = ctk.CTkEntry(p, width=400, height=36, corner_radius=6, placeholder_text="Ej. 85,000")
        if km_act is not None: eod.insert(0, f"{km_act:,}")
        eod.bind("<KeyRelease>", lambda e: aplicar_formato_entero(eod, e))
        eod.pack(anchor="w", padx=10)

        etiqueta("Notas:")
        enotas = ctk.CTkTextbox(p, width=400, height=60, corner_radius=6)
        enotas._textbox.tag_configure("justificado", justify="left")
        enotas.insert("1.0", notas_act or "")
        enotas.pack(anchor="w", padx=10, pady=(2, 10))
        activar_corrector_en_vivo(enotas)

        def guardar():
            nombre_veh = ev.get()
            vid = next((v[0] for v in vehiculos if v[1] == nombre_veh), None)
            if vid is None:
                messagebox.showerror("Error", "Selecciona un vehículo válido.", parent=m)
                return

            meses_txt = emes.get().strip()
            km_txt = ekm.get().strip()
            try:
                meses = int(meses_txt) if meses_txt else None
                km_int = parsear_entero(km_txt) if km_txt else None
            except ValueError:
                messagebox.showerror("Dato inválido", "Los intervalos deben ser números enteros.", parent=m)
                return
            if meses_txt and meses is None:
                messagebox.showerror("Dato inválido", "Los meses deben ser un número entero válido.", parent=m)
                return
            if km_txt and km_int is None:
                messagebox.showerror("Dato inválido", "Los km del intervalo deben ser un número entero válido.", parent=m)
                return

            if not meses and not km_int:
                messagebox.showwarning("Faltan datos", "Define al menos un intervalo (meses o km).", parent=m)
                return
            if meses is not None and meses <= 0:
                messagebox.showerror("Dato inválido", "Los meses deben ser mayores a 0.", parent=m)
                return
            if km_int is not None and km_int <= 0:
                messagebox.showerror("Dato inválido", "Los km deben ser mayores a 0.", parent=m)
                return

            raw_odometro = eod.get().strip()
            odometro = parsear_entero(raw_odometro) if raw_odometro else None
            if raw_odometro and odometro is None:
                messagebox.showerror("Dato inválido", "El odómetro debe ser numérico.", parent=m)
                return
            if odometro is not None and odometro < 0:
                messagebox.showerror("Dato inválido", "El odómetro no puede ser negativo.", parent=m)
                return

            fecha_val_raw = ef.get().strip() or None
            fecha_iso = normalizar_a_iso(fecha_val_raw) if fecha_val_raw else None
            if fecha_val_raw and not fecha_iso:
                messagebox.showerror("Fecha inválida", "Usa una fecha válida.", parent=m)
                return

            datos = (vid, etipo.get(), km_int, meses, fecha_iso, odometro, enotas.get("1.0", "end-1c").strip())
            if rid:
                self.db.execute(
                    "UPDATE recordatorios SET vehiculo_id=?, tipo=?, intervalo_km=?, intervalo_meses=?, "
                    "ultima_fecha=?, ultimo_km=?, notas=? WHERE id=?",
                    datos + (rid,)
                )
            else:
                self.db.execute_insert(
                    "INSERT INTO recordatorios (vehiculo_id, tipo, intervalo_km, intervalo_meses, "
                    "ultima_fecha, ultimo_km, notas) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    datos
                )

            m.destroy()
            self.actualizar_alertas()
            self.actualizar_badge_alertas()

        box = ctk.CTkFrame(p, fg_color="transparent")
        box.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkButton(
            box, text="Guardar", width=130, height=36, font=ctk.CTkFont(weight="bold"),
            fg_color=self.tema_actual["accent"], hover_color=self.tema_actual["accent_hover"],
            text_color=self.tema_actual["accent_text"],
            command=guardar
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            box, text="Cancelar", width=90, height=36,
            fg_color=("#64748B", "#475569"), hover_color=("#475569", "#334155"), text_color="#FFFFFF",
            command=m.destroy
        ).pack(side="right")

        self.vincular_tab([ev, etipo, emes, ekm, ef, eod, enotas])
        ev.focus_set()

    def completar_recordatorio(self, rid):
        filas = self.db.query("SELECT vehiculo_id, tipo FROM recordatorios WHERE id = ?", (rid,))
        if not filas:
            return
        vid, tipo = filas[0]
        km = self.km_actual_vehiculo(vid)
        if messagebox.askyesno(
            "Marcar como realizado",
            f"¿Registrar “{tipo}” como realizado hoy?\nSe guardará el odómetro actual: {km:,} km."
        ):
            self.db.execute(
                "UPDATE recordatorios SET ultima_fecha = ?, ultimo_km = ? WHERE id = ?",
                (date.today().strftime("%Y-%m-%d"), km, rid)
            )
            self.actualizar_alertas()
            self.actualizar_badge_alertas()

    def eliminar_recordatorio(self, rid):
        if messagebox.askyesno("Eliminar", f"¿Eliminar el recordatorio #{rid}?"):
            self.db.execute("DELETE FROM recordatorios WHERE id = ?", (rid,))
            self.actualizar_alertas()
            self.actualizar_badge_alertas()

    def actualizar_badge_alertas(self):
        etiqueta = getattr(self.btn_nav_alert, "_lbl_txt", None)
        if etiqueta is None:
            return
        try:
            vencidos = sum(1 for r in self._recordatorios_raw()
                           if self.evaluar_recordatorio(r)["estado"] == "vencido")
        except Exception:
            vencidos = 0

        if vencidos:
            etiqueta.configure(text=f"Alertas  {ICON_WARN} {vencidos}", text_color=("#DC2626", "#FCA5A5"))
        else:
            etiqueta.configure(text="Alertas", text_color=self.tema_actual["sidebar_text"])

    def _recordatorios_raw(self):
        return self.db.query("""
            SELECT id, vehiculo_id, tipo, intervalo_km, intervalo_meses,
                   ultima_fecha, ultimo_km, notas,
                   COALESCE((SELECT nombre FROM vehiculos WHERE id = r.vehiculo_id), '')
            FROM recordatorios r
        """)

    def chequear_alertas_inicio(self):
        self.actualizar_badge_alertas()
        vencidos = 0
        for rec in self._recordatorios_raw():
            if self.evaluar_recordatorio(rec)["estado"] == "vencido":
                vencidos += 1

        if vencidos and messagebox.askyesno(
            "Mantenimiento vencido",
            f"Tienes {vencidos} recordatorio(s) vencido(s).\n\n¿Deseas revisarlos ahora?"
        ):
            self.mostrar_vista("alertas")

    # ------------------ REPORTE DE IMPRESIÓN ------------------
    def imprimir_reporte(self):
        filtro = self._filtros_sql()
        if filtro is None:
            return
        where, params, criterio = filtro

        regs = self.db.query(
            f"SELECT {self._COLS_HIST} FROM registros" + where + " ORDER BY fecha DESC, id DESC",
            params
        )
        total_costo = sum(float(r[7] or 0) for r in regs)
        max_km = max((int(r[6]) for r in regs if r[6]), default=0)

        filas = ""
        for i, r in enumerate(regs, 1):
            n_txt = f"<br><small style='color:#666;'>Notas: {html.escape(r[10])}</small>" if r[10] else ""
            auto_str = f"{r[2]} {r[4]}".strip() if r[4] else r[2]

            comp_link = "-"
            if r[11]:
                ruta_abs = os.path.join(CARPETA_COMPROBANTES, r[11])
                if os.path.exists(ruta_abs):
                    comp_link = f"<a href='{Path(ruta_abs).as_uri()}' target='_blank'>📎 Ver Nota</a>"

            filas += f"""
            <tr>
                <td style="text-align:center;">{i}</td>
                <td style="white-space:nowrap;">{html.escape(formatear_fecha(r[1]))}</td>
                <td><strong>{html.escape(str(auto_str))}</strong></td>
                <td>{html.escape(str(r[5]))}</td>
                <td style="text-align:right;">{f"{r[6]:,} km" if r[6] else "-"}</td>
                <td style="text-align:justify;">{html.escape(str(r[8]))}{n_txt}</td>
                <td>{html.escape(str(r[9] or "-"))}</td>
                <td style="text-align:center;">{comp_link}</td>
                <td style="text-align:right; font-weight:bold;">${r[7] or 0:,.2f}</td>
            </tr>
            """

        criterio_html = html.escape(criterio)

        html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Reporte Vehicular</title>
<style>
    @page {{ size: letter landscape; margin: 12mm 15mm; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; margin: 0; padding: 20px; color: #111; font-size: 10pt; }}
    .no-print {{ background: #2563eb; color: #fff; padding: 10px 16px; border-radius: 6px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
    .btn {{ background: #fff; color: #1e40af; border: none; padding: 6px 14px; font-weight: bold; border-radius: 4px; cursor: pointer; }}
    .header {{ border-bottom: 2px solid #0f172a; padding-bottom: 8px; margin-bottom: 12px; display: flex; justify-content: space-between; }}
    .cards {{ display: flex; gap: 15px; margin-bottom: 12px; }}
    .card {{ flex: 1; border: 1px solid #e2e8f0; background: #f8fafc; padding: 8px 12px; border-radius: 4px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 9pt; }}
    th {{ background: #0f172a; color: #fff; padding: 6px 8px; text-align: left; }}
    td {{ padding: 6px 8px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }}
    tr:nth-child(even) {{ background: #f8fafc; }}
    tr {{ page-break-inside: avoid; }}
    @media print {{ .no-print {{ display: none !important; }} body {{ padding: 0; }} }}
</style>
</head>
<body>
<div class="no-print">
    <span>Vista Previa del Reporte</span>
    <button class="btn" onclick="window.print()">Mandar a Imprimir</button>
</div>
<div class="header">
    <div><h2 style="margin:0;">Reporte Solicitado</h2><span>Criterio: {criterio_html}</span></div>
    <div style="text-align:right; font-size:8.5pt; color:#64748b;">Emitido: {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>
</div>
<div class="cards">
    <div class="card">Total Invertido: <strong style="color:#047857;">${total_costo:,.2f}</strong></div>
    <div class="card">Servicios: <strong>{len(regs)}</strong></div>
    <div class="card">Odómetro más alto: <strong>{max_km:,} km</strong></div>
</div>
<table>
    <thead><tr><th>#</th><th>Fecha</th><th>Vehículo / Modelo</th><th>Categoría</th><th style="text-align:right;">Km</th><th>Descripción</th><th>Lugar</th><th style="text-align:center;">Comprobante</th><th style="text-align:right;">Costo</th></tr></thead>
    <tbody>{filas if filas else '<tr><td colspan="9" style="text-align:center; padding:15px;">Sin datos.</td></tr>'}</tbody>
</table>
</body>
</html>"""

        tmp = os.path.join(tempfile.gettempdir(), f"reporte_vehicular_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        with open(tmp, "w", encoding="utf-8") as f_out:
            f_out.write(html_doc)
        abrir_archivo_sistema(tmp)


if __name__ == "__main__":
    # La base real vive en %LOCALAPPDATA%\GarageDesk cuando corre el .exe,
    # NO junto al ejecutable en Program Files.
    db_ruta = os.path.join(CARPETA_DATOS, "mi_vehiculo.db")
    if os.path.exists(db_ruta):
        valida, error = SecurityManager.verificar_integridad_archivo(db_ruta)
        if not valida:
            if not SecurityManager.rescatar_arranque_fallido(None, db_ruta):
                MessageBoxNativo(
                    "GarageDesk",
                    "No se pudo recuperar la base de datos. La aplicación se cerrará.",
                    0, 0x10)
                sys.exit(1)

    try:
        app = ModernApp()
    except sqlite3.DatabaseError as exc:
        MessageBoxNativo("GarageDesk", f"No se pudo abrir la base de datos:\n{exc}", 0, 0x10)
        sys.exit(1)
    except Exception as exc:
        MessageBoxNativo("GarageDesk", f"Error al iniciar GarageDesk:\n{exc}", 0, 0x10)
        sys.exit(1)
    app.mainloop()
