#!/usr/bin/env python3
"""Video animado: Cómo abrir Active Directory y crear un usuario.
Formato vertical 1080x1920 @30fps (Reels / Shorts / TikTok).

Uso:
  python3 render.py                 -> renderiza video completo
  python3 render.py --stills 2,8,20 -> exporta PNGs de prueba en esos segundos
"""
import math, random, sys, os, subprocess, wave
import numpy as np
import cairo
import gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.dirname(HERE)

UI = "Adwaita Sans"
HEAD = "Clarity City"
BIG = "Bebas Neue"

# ---------------------------------------------------------------- timeline
T_S1 = 4.5
T_S2 = T_S1 + 8.4
T_S3 = T_S2 + 6.3
T_S4 = T_S3 + 4.3
T_S5 = T_S4 + 8.9
T_S6 = T_S5 + 9.6
T_OUT = T_S6 + 6.0
DUR = T_OUT + 6.5

STEPS = [(T_S1, "Abre la consola"), (T_S2, "Elige la ubicación"), (T_S3, "Crea el objeto"),
         (T_S4, "Datos del usuario"), (T_S5, "La contraseña"), (T_S6, "¡Listo!")]

# ---------------------------------------------------------------- colors
def hx(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)

CYAN, VIOLET, PINK = hx('22D3EE'), hx('8B5CF6'), hx('F472B6')
GREEN, YELLOW, WHITE = hx('34D399'), hx('FBBF24'), (1, 1, 1)
WIN_ACCENT = hx('0067C0')
TXT = hx('1B1B1B')
GRAY = hx('6B6B6B')

def mk(s, col):  # pango markup colored span
    return f'<span foreground="{col}">{s}</span>'
C_CY, C_YE, C_PK, C_GR = '#67E8F9', '#FCD34D', '#F9A8D4', '#6EE7B7'

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, t0, t1): return clamp((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t0)
def eio(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eout(x): return 1 - (1 - x) ** 3
def eback(x, s=1.70158):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2
def lerp(a, b, x): return a + (b - a) * x
def win(t, t0, t1, fi=.3, fo=.3):
    if t < t0 or t > t1: return 0.0
    return eout(prog(t, t0, t0 + fi)) * (1 - eio(prog(t, t1 - fo, t1)))

# ---------------------------------------------------------------- drawing helpers
WEIGHTS = {300: Pango.Weight.LIGHT, 400: Pango.Weight.NORMAL, 500: Pango.Weight.MEDIUM,
           600: Pango.Weight.SEMIBOLD, 700: Pango.Weight.BOLD, 800: Pango.Weight.ULTRABOLD}
_fd = {}
def fdesc(family, size, weight):
    k = (family, size, weight)
    if k not in _fd:
        fd = Pango.FontDescription()
        fd.set_family(family)
        fd.set_weight(WEIGHTS[weight])
        fd.set_absolute_size(size * Pango.SCALE)
        _fd[k] = fd
    return _fd[k]

def layout(ctx, s, size, family=UI, weight=400, width=None, align='l', markup=False, ellipsize=False, spacing=0):
    L = PangoCairo.create_layout(ctx)
    L.set_font_description(fdesc(family, size, weight))
    if width:
        L.set_width(int(width * Pango.SCALE))
        if ellipsize:
            L.set_ellipsize(Pango.EllipsizeMode.END)
        else:
            L.set_wrap(Pango.WrapMode.WORD_CHAR)
        L.set_alignment({'l': Pango.Alignment.LEFT, 'c': Pango.Alignment.CENTER, 'r': Pango.Alignment.RIGHT}[align])
    if spacing:
        L.set_spacing(int(spacing * Pango.SCALE))
    if markup:
        L.set_markup(s, -1)
    else:
        L.set_text(s, -1)
    return L

def text(ctx, s, x, y, size, color=WHITE, alpha=1.0, family=UI, weight=400, align='l', valign='t',
         width=None, markup=False, ellipsize=False, spacing=0):
    if alpha <= 0.003: return (0, 0)
    L = layout(ctx, s, size, family, weight, width, align, markup, ellipsize, spacing)
    w, h = L.get_pixel_size()
    if width:
        dx = {'l': 0, 'c': -width / 2, 'r': -width}[align]
    else:
        dx = {'l': 0, 'c': -w / 2, 'r': -w}[align]
    dy = {'t': 0, 'm': -h / 2, 'b': -h}[valign]
    ctx.save()
    ctx.set_source_rgba(*color[:3], alpha)
    ctx.move_to(x + dx, y + dy)
    PangoCairo.show_layout(ctx, L)
    ctx.new_path()
    ctx.restore()
    return (w, h)

def tsize(ctx, s, size, family=UI, weight=400, markup=False):
    return layout(ctx, s, size, family, weight, markup=markup).get_pixel_size()

def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()

def fill_rr(ctx, x, y, w, h, r, col, a=1.0):
    rrect(ctx, x, y, w, h, r)
    ctx.set_source_rgba(*col[:3], a)
    ctx.fill()

def stroke_rr(ctx, x, y, w, h, r, col, a=1.0, lw=1.5):
    rrect(ctx, x, y, w, h, r)
    ctx.set_source_rgba(*col[:3], a)
    ctx.set_line_width(lw)
    ctx.stroke()

def shadow(ctx, x, y, w, h, r, strength=1.0, dy=14):
    for i in range(14):
        e = i * 2.2
        rrect(ctx, x - e, y - e + dy, w + 2 * e, h + 2 * e, r + e)
        ctx.set_source_rgba(0, 0, 0, 0.022 * strength)
        ctx.fill()

def glow_rr(ctx, x, y, w, h, r, col, a=1.0, n=8, step=3):
    for i in range(n, 0, -1):
        e = i * step
        rrect(ctx, x - e, y - e, w + 2 * e, h + 2 * e, r + e)
        ctx.set_source_rgba(*col, a * 0.05)
        ctx.fill()

def push(ctx): ctx.push_group()
def pop(ctx, alpha):
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(clamp(alpha))

def scale_at(ctx, cx, cy, s):
    ctx.translate(cx, cy); ctx.scale(s, s); ctx.translate(-cx, -cy)

# ---------------------------------------------------------------- icons
def ic_user(ctx, cx, cy, s, col=hx('3B82F6'), a=1.0):
    ctx.set_source_rgba(*col, a)
    ctx.arc(cx, cy - s * 0.17, s * 0.21, 0, 2 * math.pi); ctx.fill()
    ctx.save(); ctx.translate(cx, cy + s * 0.42); ctx.scale(s * 0.40, s * 0.36)
    ctx.arc(0, 0, 1, math.pi, 2 * math.pi); ctx.restore(); ctx.close_path(); ctx.fill()

def ic_group(ctx, cx, cy, s, a=1.0):
    ic_user(ctx, cx + s * 0.18, cy - s * 0.05, s * 0.8, hx('60A5FA'), a)
    ic_user(ctx, cx - s * 0.12, cy + s * 0.05, s * 0.85, hx('2563EB'), a)

def ic_folder(ctx, cx, cy, s, a=1.0, badge=None):
    x, y = cx - s / 2, cy - s * 0.38
    fill_rr(ctx, x, y, s * 0.45, s * 0.2, s * 0.06, hx('E8A825'), a)
    fill_rr(ctx, x, y + s * 0.1, s, s * 0.66, s * 0.08, hx('F8C84A'), a)
    if badge:
        fill_rr(ctx, cx + s * 0.05, cy + s * 0.02, s * 0.42, s * 0.34, s * 0.05, badge, a)
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.rectangle(cx + s * 0.12, cy + s * 0.1, s * 0.28, s * 0.05); ctx.fill()
        ctx.rectangle(cx + s * 0.12, cy + s * 0.2, s * 0.2, s * 0.05); ctx.fill()

def ic_domain(ctx, cx, cy, s, a=1.0):
    ctx.set_source_rgba(*hx('64748B'), a); ctx.set_line_width(max(1.5, s * 0.06))
    ctx.move_to(cx, cy - s * 0.2); ctx.line_to(cx, cy)
    ctx.move_to(cx - s * 0.3, cy + s * 0.18); ctx.line_to(cx - s * 0.3, cy); ctx.line_to(cx + s * 0.3, cy); ctx.line_to(cx + s * 0.3, cy + s * 0.18)
    ctx.stroke()
    for (px, py, c) in [(cx, cy - s * 0.3, '2563EB'), (cx - s * 0.3, cy + s * 0.28, '0EA5E9'), (cx + s * 0.3, cy + s * 0.28, '0EA5E9')]:
        fill_rr(ctx, px - s * 0.17, py - s * 0.14, s * 0.34, s * 0.28, s * 0.05, hx(c), a)

def ic_aduc(ctx, cx, cy, s, a=1.0):
    fill_rr(ctx, cx - s * 0.42, cy - s * 0.42, s * 0.84, s * 0.84, s * 0.14, hx('1E40AF'), a)
    ic_user(ctx, cx, cy + s * 0.02, s * 0.7, (1, 1, 1), a)

def ic_run(ctx, cx, cy, s, a=1.0):
    x, y = cx - s / 2, cy - s * 0.4
    fill_rr(ctx, x, y, s, s * 0.8, s * 0.08, hx('E5E7EB'), a)
    stroke_rr(ctx, x, y, s, s * 0.8, s * 0.08, hx('9CA3AF'), a, 1.5)
    fill_rr(ctx, x, y, s, s * 0.18, s * 0.06, WIN_ACCENT, a)
    ctx.set_source_rgba(*WIN_ACCENT, a); ctx.set_line_width(s * 0.08)
    ctx.move_to(cx - s * 0.2, cy + s * 0.25); ctx.line_to(cx + s * 0.18, cy - s * 0.05); ctx.stroke()
    ctx.move_to(cx + s * 0.22, cy - s * 0.1); ctx.line_to(cx + s * 0.22, cy + s * 0.08); ctx.line_to(cx + s * 0.04, cy - s * 0.1); ctx.close_path(); ctx.fill()

def win_logo(ctx, cx, cy, s, col, a=1.0):
    g = s * 0.08; q = (s - g) / 2
    for dx in (0, 1):
        for dy in (0, 1):
            ctx.rectangle(cx - s / 2 + dx * (q + g), cy - s / 2 + dy * (q + g), q, q)
    ctx.set_source_rgba(*col, a); ctx.fill()

def chevron(ctx, cx, cy, s, angle, col, a=1.0, lw=2.2):
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(angle)
    ctx.move_to(-s * 0.25, -s * 0.5); ctx.line_to(s * 0.25, 0); ctx.line_to(-s * 0.25, s * 0.5)
    ctx.set_source_rgba(*col, a); ctx.set_line_width(lw); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke(); ctx.restore()

def check_mark(ctx, cx, cy, s, col, a=1.0, lw=3, p=1.0):
    pts = [(cx - s * 0.32, cy + s * 0.02), (cx - s * 0.08, cy + s * 0.26), (cx + s * 0.36, cy - s * 0.24)]
    l1 = math.dist(pts[0], pts[1]); l2 = math.dist(pts[1], pts[2]); L = (l1 + l2) * p
    ctx.move_to(*pts[0])
    if L <= l1:
        f = L / l1; ctx.line_to(lerp(pts[0][0], pts[1][0], f), lerp(pts[0][1], pts[1][1], f))
    else:
        ctx.line_to(*pts[1]); f = (L - l1) / l2
        ctx.line_to(lerp(pts[1][0], pts[2][0], f), lerp(pts[1][1], pts[2][1], f))
    ctx.set_source_rgba(*col, a); ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()

def close_x(ctx, cx, cy, s, col, a=1.0):
    ctx.set_source_rgba(*col, a); ctx.set_line_width(1.8)
    ctx.move_to(cx - s, cy - s); ctx.line_to(cx + s, cy + s)
    ctx.move_to(cx + s, cy - s); ctx.line_to(cx - s, cy + s); ctx.stroke()

# ---------------------------------------------------------------- windows widgets
def win_frame(ctx, x, y, w, h, title, icon=None, a=1.0):
    shadow(ctx, x, y, w, h, 14, 1.4)
    fill_rr(ctx, x, y, w, h, 14, hx('F3F3F3'))
    stroke_rr(ctx, x, y, w, h, 14, hx('BDBDBD'), 1, 1.2)
    tx = x + 22
    if icon:
        icon(ctx, x + 36, y + 28, 30); tx = x + 64
    text(ctx, title, tx, y + 28, 24, TXT, 1, UI, 400, valign='m', width=w - 200, ellipsize=True)
    close_x(ctx, x + w - 34, y + 28, 8, TXT)

def button(ctx, x, y, w, h, label, primary=False, pressed=False, disabled=False, hover=False):
    if primary:
        col = hx('005A9E') if pressed else (hx('1975C5') if hover else WIN_ACCENT)
        fill_rr(ctx, x, y, w, h, 8, col)
        text(ctx, label, x + w / 2, y + h / 2, 24, WHITE, 1, UI, 600, 'c', 'm')
    else:
        col = hx('E0E0E0') if pressed else (hx('F6F6F6') if hover else hx('FDFDFD'))
        fill_rr(ctx, x, y, w, h, 8, col)
        stroke_rr(ctx, x, y, w, h, 8, hx('CFCFCF'), 1, 1.2)
        text(ctx, label, x + w / 2, y + h / 2, 24, hx('A0A0A0') if disabled else TXT, 1, UI, 400, 'c', 'm')

def input_box(ctx, x, y, w, h, s, focused=False, caret=False, disabled=False, size=25, dots=False):
    fill_rr(ctx, x, y, w, h, 6, hx('F7F7F7') if disabled else WHITE)
    stroke_rr(ctx, x, y, w, h, 6, hx('C4C4C4'), 1, 1.2)
    if focused:
        ctx.save(); rrect(ctx, x, y, w, h, 6); ctx.clip()
        ctx.rectangle(x, y + h - 3, w, 3); ctx.set_source_rgb(*WIN_ACCENT); ctx.fill(); ctx.restore()
    tw = 0
    if s:
        if dots:
            for i in range(len(s)):
                ctx.arc(x + 20 + i * 22, y + h / 2, 6, 0, 2 * math.pi)
            ctx.set_source_rgb(*TXT); ctx.fill()
            tw = 22 * len(s) - 6
        else:
            tw, _ = text(ctx, s, x + 14, y + h / 2, size, hx('808080') if disabled else TXT, 1, UI, 400, valign='m')
    if focused and caret:
        cx = x + (14 if not dots else 14) + tw + (4 if s else 0)
        ctx.rectangle(cx, y + 10, 2, h - 20); ctx.set_source_rgb(*TXT); ctx.fill()

def checkbox(ctx, x, y, checked, s=30):
    if checked:
        fill_rr(ctx, x, y, s, s, 6, WIN_ACCENT)
        check_mark(ctx, x + s / 2, y + s / 2, s * 0.8, WHITE, 1, 3)
    else:
        fill_rr(ctx, x, y, s, s, 6, WHITE)
        stroke_rr(ctx, x, y, s, s, 6, hx('8A8A8A'), 1, 1.6)

def chip(ctx, cx, cy, label, col, a, sc=1.0, size=24, icon=None):
    if a <= 0: return
    w, h = tsize(ctx, label, size, HEAD, 700)
    pw, ph = w + 40 + (34 if icon else 0), h + 18
    push(ctx); ctx.save(); scale_at(ctx, cx, cy, sc)
    x, y = cx - pw / 2, cy - ph / 2
    shadow(ctx, x, y, pw, ph, ph / 2, 0.8, 6)
    fill_rr(ctx, x, y, pw, ph, ph / 2, col)
    tx = x + 20
    if icon == 'check':
        check_mark(ctx, tx + 12, cy, 26, WHITE, 1, 3.5); tx += 34
    text(ctx, label, tx, cy, size, WHITE, 1, HEAD, 700, valign='m')
    ctx.restore(); pop(ctx, a)

# ---------------------------------------------------------------- background
_rng = random.Random(7)
PARTS = [(_rng.uniform(0, W), _rng.uniform(0, H), _rng.uniform(1.5, 4.0), _rng.uniform(15, 45),
          _rng.uniform(0, 6.28), _rng.choice([CYAN, VIOLET, PINK, WHITE])) for _ in range(55)]
BLOBS = [(220, 380, 520, VIOLET, 0.0), (900, 900, 560, CYAN, 2.0), (300, 1600, 600, PINK, 4.0), (850, 1750, 420, VIOLET, 1.0)]

def draw_bg(ctx, t):
    g = cairo.LinearGradient(0, 0, W * 0.4, H)
    g.add_color_stop_rgb(0, *hx('0A0F2C')); g.add_color_stop_rgb(1, *hx('190F3D'))
    ctx.set_source(g); ctx.paint()
    for (bx, by, r, col, ph) in BLOBS:
        x = bx + 90 * math.sin(t * 0.25 + ph); y = by + 70 * math.cos(t * 0.2 + ph * 1.3)
        rg = cairo.RadialGradient(x, y, 0, x, y, r)
        rg.add_color_stop_rgba(0, *col, 0.22); rg.add_color_stop_rgba(1, *col, 0)
        ctx.set_source(rg); ctx.paint()
    ctx.set_source_rgba(1, 1, 1, 0.045)
    for gx in range(27, W, 54):
        for gy in range(27, H, 54):
            ctx.rectangle(gx - 1.2, gy - 1.2, 2.4, 2.4)
    ctx.fill()
    for (px, py, r, sp, ph, col) in PARTS:
        y = (py - sp * t) % (H + 40) - 20
        x = px + 14 * math.sin(t * 0.8 + ph)
        a = 0.25 + 0.25 * math.sin(t * 2 + ph)
        ctx.set_source_rgba(*col, a); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.fill()

# ---------------------------------------------------------------- typing / focus / clicks
TYPES = {
    'run': ('dsa.msc', T_S1 + 2.9, T_S1 + 4.1),
    'nombre': ('Ana', T_S4 + 1.1, T_S4 + 1.6),
    'apellidos': ('García', T_S4 + 2.3, T_S4 + 3.1),
    'logon': ('agarcia', T_S4 + 4.3, T_S4 + 5.3),
    'pwd': ('•' * 10, T_S5 + 1.0, T_S5 + 2.2),
    'pwd2': ('•' * 10, T_S5 + 2.8, T_S5 + 4.0),
}
def char_times(k):
    s, t0, t1 = TYPES[k]; dt = (t1 - t0) / len(s)
    return [t0 + i * dt for i in range(len(s))]
def typed(k, t):
    s, t0, t1 = TYPES[k]
    if t < t0: return ''
    dt = (t1 - t0) / len(s)
    return s[:min(len(s), int((t - t0) / dt) + 1)]
def typing_now(k, t):
    s, t0, t1 = TYPES[k]; return t0 - 0.05 <= t <= t1 + 0.15

FOCUS = [(T_S4 + 0.8, 'nombre'), (T_S4 + 2.1, 'apellidos'), (T_S4 + 4.0, 'logon'), (T_S4 + 8.7, None),
         (T_S5 + 0.8, 'pwd'), (T_S5 + 2.6, 'pwd2'), (T_S5 + 7.4, None)]
def focused(t):
    f = None
    for (ft, k) in FOCUS:
        if t >= ft: f = k
    return f
def caret_on(t, k):
    return typing_now(k, t) or (t * 1.8) % 1 < 0.55

# ---------------------------------------------------------------- layout constants
# Run dialog
RX, RY, RW, RH = 90, 820, 900, 440
BTN_ACEPTAR = (480, 1150, 150, 52)
# ADUC window
AX, AY, AW, AH = 50, 480, 980, 900
CY0 = AY + 150
LPW = 440
TY, TRH = 645, 46
TREE_TOP = [(0, "Usuarios y equipos de Active Directory", 'aduc'), (1, "Consultas guardadas", 'folder'),
            (1, "empresa.local", 'domain')]
TREE_CH = [("Builtin", 'folder'), ("Computers", 'folder'), ("Domain Controllers", 'ou'),
           ("ForeignSecurityPrincipals", 'folder'), ("Managed Service Accounts", 'folder'),
           ("Users", 'folder'), ("Ventas", 'ou')]
EXPANDER = (50 + 12 + 30 + 6, TY + 2 * TRH + TRH // 2)
VENTAS_ROW_Y = TY + 9 * TRH
VENTAS_PT = (240, VENTAS_ROW_Y + TRH // 2 + 1)
# context menu
MENU_ITEMS = ["Delegar control...", "Mover...", "Buscar...", None, "Nuevo", "Todas las tareas", None,
              "Cortar", "Eliminar", "Cambiar nombre", None, "Propiedades"]
SUB_ITEMS = ["Equipo", "Contacto", "Grupo", "InetOrgPerson", "Unidad organizativa", "Impresora", "Usuario",
             "Carpeta compartida"]
IH, SEPH, MPAD, MW, SMW = 46, 13, 8, 360, 380
MH = 2 * MPAD + sum(IH if it else SEPH for it in MENU_ITEMS)
MX, MY = VENTAS_PT[0], VENTAS_PT[1] - MH
def item_rows(items, x, y):
    rows = []; cy = y + MPAD
    for it in items:
        hh = IH if it else SEPH
        rows.append((it, cy, hh)); cy += hh
    return rows
MENU_ROWS = item_rows(MENU_ITEMS, MX, MY)
NUEVO_Y0 = [r for r in MENU_ROWS if r[0] == "Nuevo"][0][1]
SX, SY = MX + MW - 4, NUEVO_Y0 - MPAD
SMH = 2 * MPAD + len(SUB_ITEMS) * IH
SUB_ROWS = item_rows(SUB_ITEMS, SX, SY)
USUARIO_Y0 = [r for r in SUB_ROWS if r[0] == "Usuario"][0][1]
P_NUEVO = (MX + 130, NUEVO_Y0 + IH / 2)
P_SUBIN = (SX + 70, NUEVO_Y0 + IH / 2)
P_USUARIO = (SX + 100, USUARIO_Y0 + IH / 2)
# new user dialog
DX, DY, DW, DH = 70, 500, 940, 860
F_NOMBRE = (330, 680, 300, 48)
F_INIC = (800, 680, 120, 48)
F_APELL = (330, 750, 590, 48)
F_FULL = (330, 820, 590, 48)
F_LOGON = (100, 950, 470, 48)
F_DOM = (590, 950, 330, 48)
F_PRE1 = (100, 1075, 330, 48)
F_PRE2 = (450, 1075, 470, 48)
F_PWD = (400, 690, 520, 48)
F_PWD2 = (400, 760, 520, 48)
CHK_Y = [870, 960, 1030, 1100]
BTN_BACK = (330, 1280, 180, 52)
BTN_NEXT = (525, 1280, 230, 52)
BTN_CANCEL = (770, 1280, 210, 52)
def center(r, dx=0): return (r[0] + r[2] / 2 + dx, r[1] + r[3] / 2)

# ---------------------------------------------------------------- cursor
MOVES = [
    (T_S1 + 4.1, T_S1 + 4.1, (900, 1560)),
    (T_S1 + 4.3, T_S1 + 5.1, center(BTN_ACEPTAR, 10)),
    (T_S2 + 0.9, T_S2 + 1.7, EXPANDER),
    (T_S2 + 2.9, T_S2 + 3.8, VENTAS_PT),
    (T_S3 + 1.2, T_S3 + 1.8, P_NUEVO),
    (T_S3 + 2.2, T_S3 + 2.6, P_SUBIN),
    (T_S3 + 2.8, T_S3 + 3.5, P_USUARIO),
    (T_S4 + 0.1, T_S4 + 0.6, (F_NOMBRE[0] + 90, F_NOMBRE[1] + 26)),
    (T_S4 + 1.7, T_S4 + 2.0, (F_APELL[0] + 170, F_APELL[1] + 26)),
    (T_S4 + 3.3, T_S4 + 3.9, (F_LOGON[0] + 200, F_LOGON[1] + 26)),
    (T_S4 + 7.6, T_S4 + 8.4, center(BTN_NEXT)),
    (T_S5 + 0.3, T_S5 + 0.7, (F_PWD[0] + 230, F_PWD[1] + 26)),
    (T_S5 + 2.3, T_S5 + 2.5, (F_PWD2[0] + 230, F_PWD2[1] + 26)),
    (T_S5 + 4.4, T_S5 + 5.0, (116, CHK_Y[0] + 16)),
    (T_S5 + 6.5, T_S5 + 7.2, center(BTN_NEXT)),
    (T_S5 + 8.3, T_S5 + 8.6, center(BTN_NEXT, 45)),
    (T_S5 + 8.8, T_S5 + 9.1, center(BTN_NEXT)),
    (T_S6 + 0.3, T_S6 + 0.9, (930, 1330)),
]
CLICKS = [(T_S1 + 5.4, 'L'), (T_S2 + 2.0, 'L'), (T_S2 + 4.1, 'L'), (T_S3 + 0.6, 'R'), (T_S3 + 3.9, 'L'),
          (T_S4 + 0.8, 'L'), (T_S4 + 2.1, 'L'), (T_S4 + 4.0, 'L'), (T_S4 + 8.7, 'L'),
          (T_S5 + 0.8, 'L'), (T_S5 + 2.6, 'L'), (T_S5 + 7.4, 'L'), (T_S5 + 9.4, 'L')]
CUR_T0, CUR_T1 = T_S1 + 4.1, T_S6 + 1.0

def cursor_pos(t):
    pos = MOVES[0][2]
    for (s, e, p) in MOVES:
        if t >= e: pos = p
        elif t > s:
            k = eio(prog(t, s, e)); return (lerp(pos[0], p[0], k), lerp(pos[1], p[1], k))
        else: break
    return pos

def pressed(rect, t):
    for (ct, kind) in CLICKS:
        if ct <= t <= ct + 0.18:
            x, y = cursor_pos(ct)
            if rect[0] <= x <= rect[0] + rect[2] and rect[1] <= y <= rect[1] + rect[3]: return True
    return False

def hovering(rect, t):
    if not (CUR_T0 <= t <= CUR_T1): return False
    x, y = cursor_pos(t)
    return rect[0] <= x <= rect[0] + rect[2] and rect[1] <= y <= rect[1] + rect[3]

def draw_cursor(ctx, t):
    a = win(t, CUR_T0, CUR_T1, .25, .4)
    if a <= 0: return
    x, y = cursor_pos(t)
    for (ct, kind) in CLICKS:
        p = prog(t, ct, ct + 0.5)
        if 0 < p < 1:
            cx, cy = cursor_pos(ct); col = CYAN if kind == 'L' else PINK
            ctx.set_source_rgba(*col, 0.7 * (1 - p)); ctx.set_line_width(5)
            ctx.arc(cx, cy, 12 + 50 * eout(p), 0, 2 * math.pi); ctx.stroke()
            ctx.set_source_rgba(*col, 0.25 * (1 - p)); ctx.arc(cx, cy, 12 + 40 * eout(p), 0, 2 * math.pi); ctx.fill()
        if kind == 'R':
            ca = win(t, ct - 0.05, ct + 1.1, .15, .3)
            if ca > 0:
                cx, cy = cursor_pos(ct)
                chip(ctx, cx - 30, cy + 70, "Clic derecho", PINK, ca, eback(prog(t, ct - .05, ct + .3)), 24)
    s = 1.0
    for (ct, kind) in CLICKS:
        if ct - 0.05 <= t <= ct + 0.2: s = 0.85
    pts = [(0, 0), (0, 17), (4, 13.2), (7, 20), (9.4, 19), (6.6, 12.4), (12, 12.4)]
    k = 2.4 * s
    push(ctx)
    ctx.save(); ctx.translate(x + 3, y + 5)
    ctx.move_to(*[v * k for v in pts[0]])
    for p in pts[1:]: ctx.line_to(p[0] * k, p[1] * k)
    ctx.close_path(); ctx.set_source_rgba(0, 0, 0, 0.3); ctx.fill(); ctx.restore()
    ctx.save(); ctx.translate(x, y)
    ctx.move_to(*[v * k for v in pts[0]])
    for p in pts[1:]: ctx.line_to(p[0] * k, p[1] * k)
    ctx.close_path(); ctx.set_source_rgb(1, 1, 1); ctx.fill_preserve()
    ctx.set_source_rgb(0, 0, 0); ctx.set_line_width(2); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    ctx.restore()
    pop(ctx, a)

# ---------------------------------------------------------------- header + caption
def step_index(t):
    i = 0
    for k, (st, _) in enumerate(STEPS):
        if t >= st: i = k
    return i

def draw_header(ctx, t):
    a = win(t, T_S1, T_OUT + 0.3, .5, .5)
    if a <= 0: return
    push(ctx)
    segw = (960 - 5 * 12) / 6
    for i, (st, _) in enumerate(STEPS):
        x = 60 + i * (segw + 12)
        fill_rr(ctx, x, 205, segw, 10, 5, WHITE, 0.14)
        f = eout(prog(t, st, st + 0.7))
        if f > 0:
            g = cairo.LinearGradient(x, 0, x + segw, 0)
            g.add_color_stop_rgb(0, *CYAN); g.add_color_stop_rgb(1, *VIOLET)
            rrect(ctx, x, 205, max(10, segw * f), 10, 5); ctx.set_source(g); ctx.fill()
    i = step_index(t); st = STEPS[i][0]
    for (k, alpha, dy) in ([(i - 1, 1 - eio(prog(t, st, st + .35)), -40 * eio(prog(t, st, st + .35)))] if i > 0 else []) + \
            [(i, eout(prog(t, st + .15, st + .6)), 40 * (1 - eout(prog(t, st + .15, st + .6))))]:
        if alpha <= 0: continue
        push(ctx)
        label = f"PASO {k + 1} DE 6"
        w, h = tsize(ctx, label, 26, HEAD, 800)
        fill_rr(ctx, 60, 238 + dy, w + 44, 50, 25, VIOLET, 0.35)
        stroke_rr(ctx, 60, 238 + dy, w + 44, 50, 25, CYAN, 0.8, 2)
        text(ctx, label, 82, 263 + dy, 26, hx('CFFAFE'), 1, HEAD, 800, valign='m')
        tw, th = text(ctx, STEPS[k][1], 58, 305 + dy, 76, WHITE, 1, HEAD, 800)
        uw = tw * eout(prog(t, STEPS[k][0] + .3, STEPS[k][0] + .9))
        if uw > 4:
            g = cairo.LinearGradient(60, 0, 60 + tw, 0)
            g.add_color_stop_rgb(0, *CYAN); g.add_color_stop_rgb(1, *PINK)
            rrect(ctx, 60, 305 + th + 4 + dy, uw, 8, 4); ctx.set_source(g); ctx.fill()
        pop(ctx, alpha)
    pop(ctx, a)

CAPTIONS = [
    (T_S1 + 0.3, T_S1 + 5.4, f"Pulsa {mk('Win + R', C_CY)} y escribe {mk('dsa.msc', C_YE)}"),
    (T_S1 + 5.4, T_S2, f"Pulsa {mk('Aceptar', C_YE)} y se abre\n{mk('Usuarios y equipos de AD', C_CY)}"),
    (T_S2, T_S2 + 4.1, f"Despliega tu dominio\n{mk('empresa.local', C_CY)}"),
    (T_S2 + 4.1, T_S3, f"Selecciona la {mk('Unidad Organizativa', C_YE)}\ndonde vivirá el usuario"),
    (T_S3, T_S4, f"Clic derecho → {mk('Nuevo', C_CY)} → {mk('Usuario', C_YE)}"),
    (T_S4, T_S4 + 4.0, f"Escribe el {mk('nombre', C_CY)} y los {mk('apellidos', C_CY)}"),
    (T_S4 + 4.0, T_S5, f"Define su {mk('nombre de inicio de sesión', C_YE)}"),
    (T_S5, T_S5 + 4.3, f"Asigna una {mk('contraseña segura', C_CY)}"),
    (T_S5 + 4.3, T_S5 + 7.4, f"Que la cambie en su\n{mk('primer inicio de sesión', C_YE)}"),
    (T_S5 + 7.4, T_S6, f"Revisa el resumen y pulsa {mk('Finalizar', C_GR)}"),
    (T_S6, T_OUT, f"{mk('Ana García', C_GR)} ya forma parte\ndel dominio"),
]

def draw_caption(ctx, t):
    a = win(t, T_S1, T_OUT + 0.3, .5, .5)
    if a <= 0: return
    push(ctx)
    x, y, w, h = 60, 1450, 960, 180
    fill_rr(ctx, x, y, w, h, 36, WHITE, 0.08)
    stroke_rr(ctx, x, y, w, h, 36, WHITE, 0.14, 1.5)
    g = cairo.LinearGradient(0, y, 0, y + h)
    g.add_color_stop_rgb(0, *CYAN); g.add_color_stop_rgb(1, *VIOLET)
    rrect(ctx, x + 18, y + 30, 8, h - 60, 4); ctx.set_source(g); ctx.fill()
    for (t0, t1, s) in CAPTIONS:
        ca = win(t, t0, t1, .35, .25)
        if ca <= 0: continue
        dy = 24 * (1 - eout(prog(t, t0, t0 + .35)))
        text(ctx, s, x + w / 2 + 10, y + h / 2 + dy, 44, WHITE, ca, HEAD, 700, 'c', 'm', width=860, markup=True, spacing=4)
    pop(ctx, a)

# ---------------------------------------------------------------- intro
INTRO_NODES = [((540, 560), 0.3, None), ((400, 710), 0.55, (540, 560)), ((680, 710), 0.65, (540, 560)),
               ((330, 850), 0.85, (400, 710)), ((470, 850), 0.95, (400, 710)), ((610, 850), 1.05, (680, 710)),
               ((750, 850), 1.15, (680, 710))]

def draw_intro(ctx, t):
    if t > 4.6: return
    out = eio(prog(t, 3.9, 4.5))
    push(ctx); ctx.save(); scale_at(ctx, 540, 900, 1 + 0.08 * out)
    for (p, t0, parent) in INTRO_NODES:
        if parent:
            f = eout(prog(t, t0 - 0.2, t0 + 0.1))
            if f > 0:
                ctx.set_source_rgba(1, 1, 1, 0.35); ctx.set_line_width(4)
                ctx.move_to(*parent); ctx.line_to(lerp(parent[0], p[0], f), lerp(parent[1], p[1], f)); ctx.stroke()
    cols = [VIOLET, CYAN, CYAN, PINK, PINK, PINK, GREEN]
    for i, (p, t0, parent) in enumerate(INTRO_NODES):
        s = eback(prog(t, t0, t0 + 0.4))
        if s <= 0: continue
        r = (64 if i == 0 else 50) * s
        glow_rr(ctx, p[0] - r, p[1] - r, 2 * r, 2 * r, r, cols[i], 1, 6, 4)
        g = cairo.LinearGradient(p[0] - r, p[1] - r, p[0] + r, p[1] + r)
        g.add_color_stop_rgb(0, *cols[i]); g.add_color_stop_rgb(1, *VIOLET)
        ctx.arc(p[0], p[1], r, 0, 2 * math.pi); ctx.set_source(g); ctx.fill()
        if i == 0: ic_domain(ctx, p[0], p[1] + 4, r * 1.1, 1)
        else: ic_user(ctx, p[0], p[1] + 2, r * 1.15, WHITE, 1)
    if t > 1.6:  # pulse on new user node
        p = INTRO_NODES[-1][0]; pp = ((t - 1.6) % 1.2) / 1.2
        ctx.set_source_rgba(*GREEN, 0.6 * (1 - pp)); ctx.set_line_width(4)
        ctx.arc(p[0], p[1], 50 + 40 * pp, 0, 2 * math.pi); ctx.stroke()
    # title letters
    title = "ACTIVE DIRECTORY"
    L = layout(ctx, title, 190, BIG, 400)
    tw, th = L.get_pixel_size()
    x0 = 540 - tw / 2; y0 = 930
    xs = 0
    for i, ch in enumerate(title):
        Lc = layout(ctx, ch, 190, BIG, 400)
        cw, _ = Lc.get_pixel_size()
        p = eback(prog(t, 0.6 + i * 0.04, 1.1 + i * 0.04))
        if p > 0:
            ctx.save(); ctx.translate(x0 + xs, y0 + 80 * (1 - p))
            PangoCairo.layout_path(ctx, Lc)
            g = cairo.LinearGradient(-xs, 0, tw - xs, th)
            g.add_color_stop_rgb(0, *CYAN); g.add_color_stop_rgb(0.5, *hx('A78BFA')); g.add_color_stop_rgb(1, *PINK)
            ctx.set_source(g); ctx.fill(); ctx.restore()
        xs += cw
    a2 = eout(prog(t, 1.4, 1.9))
    text(ctx, "Crea un usuario paso a paso", 540, 1150 + 30 * (1 - a2), 60, WHITE, a2, HEAD, 800, 'c')
    a3 = eback(prog(t, 2.0, 2.5))
    if a3 > 0:
        lab = "Windows Server  ·  ADUC"
        w, h = tsize(ctx, lab, 32, HEAD, 700)
        push(ctx); ctx.save(); scale_at(ctx, 540, 1280, a3)
        fill_rr(ctx, 540 - w / 2 - 30, 1250, w + 60, 62, 31, WHITE, 0.1)
        stroke_rr(ctx, 540 - w / 2 - 30, 1250, w + 60, 62, 31, CYAN, 0.7, 2)
        text(ctx, lab, 540, 1281, 32, hx('CFFAFE'), 1, HEAD, 700, 'c', 'm')
        ctx.restore(); pop(ctx, clamp(a3))
    ctx.restore(); pop(ctx, 1 - out)

# ---------------------------------------------------------------- step 1: run dialog
def keycap(ctx, cx, cy, w, h, press, content):
    x, y = cx - w / 2, cy - h / 2
    fill_rr(ctx, x, y + 16, w, h, 24, hx('64748B'))
    off = 12 * press
    if press > 0:
        glow_rr(ctx, x, y + off, w, h, 24, CYAN, press, 10, 4)
    g = cairo.LinearGradient(0, y, 0, y + h)
    g.add_color_stop_rgb(0, *hx('FFFFFF')); g.add_color_stop_rgb(1, *hx('D5DCE6'))
    rrect(ctx, x, y + off, w, h, 24); ctx.set_source(g); ctx.fill()
    content(cx, cy + off)

def draw_s1(ctx, t):
    b = T_S1
    if not (b <= t <= T_S2 + 0.3): return
    # keys
    ka = 1 - eio(prog(t, b + 5.5, b + 5.9))
    if ka > 0:
        push(ctx)
        for (cx, w, t0, pr, kind) in [(310, 290, b + .5, (b + 1.4, b + 2.1), 'win'), (540, 0, b + .65, None, 'plus'),
                                       (770, 190, b + .8, (b + 1.6, b + 2.0), 'r')]:
            s = eback(prog(t, t0, t0 + .45))
            if s <= 0: continue
            ctx.save(); scale_at(ctx, cx, 650, s)
            if kind == 'plus':
                text(ctx, "+", cx, 650, 110, WHITE, 1, HEAD, 800, 'c', 'm')
            else:
                p = 0.0
                if pr:
                    p = eout(prog(t, pr[0], pr[0] + .1)) * (1 - eout(prog(t, pr[1], pr[1] + .12)))
                if kind == 'win':
                    def c(x, y):
                        win_logo(ctx, x - 62, y, 52, hx('1E293B'))
                        text(ctx, "Win", x + 34, y, 62, hx('1E293B'), 1, HEAD, 800, 'c', 'm')
                else:
                    def c(x, y): text(ctx, "R", x, y, 80, hx('1E293B'), 1, HEAD, 800, 'c', 'm')
                keycap(ctx, cx, 640, w, 160, p, c)
            ctx.restore()
        pop(ctx, ka)
    # tip card
    ta = win(t, b + 5.8, T_S2 - 0.1, .4, .35)
    if ta > 0:
        push(ctx); ctx.save(); dy = 30 * (1 - eout(prog(t, b + 5.8, b + 6.3)))
        ctx.translate(0, dy)
        fill_rr(ctx, 60, 545, 960, 210, 30, YELLOW, 0.12)
        stroke_rr(ctx, 60, 545, 960, 210, 30, YELLOW, 0.6, 2)
        fill_rr(ctx, 90, 575, 100, 46, 23, YELLOW)
        text(ctx, "TIP", 140, 598, 26, hx('1E1B4B'), 1, HEAD, 800, 'c', 'm')
        text(ctx, f"También desde el <b>Administrador del servidor</b> → Herramientas → {mk('Usuarios y equipos de Active Directory', C_YE)}",
             90, 640, 30, WHITE, 1, HEAD, 500, width=900, markup=True)
        ctx.restore(); pop(ctx, ta)
    # run dialog
    ra = eout(prog(t, b + 2.1, b + 2.45)) * (1 - eio(prog(t, T_S2 - 0.3, T_S2 + 0.15)))
    if ra > 0:
        s = lerp(0.85, 1, eback(prog(t, b + 2.1, b + 2.55))) * lerp(1, 0.7, eio(prog(t, T_S2 - 0.3, T_S2 + 0.15)))
        push(ctx); ctx.save(); scale_at(ctx, 540, RY + RH / 2, s)
        win_frame(ctx, RX, RY, RW, RH, "Ejecutar", ic_run)
        ic_run(ctx, RX + 70, RY + 120, 56)
        text(ctx, "Escribe el nombre del programa, carpeta, documento o recurso de Internet y Windows lo abrirá.",
             RX + 125, RY + 85, 25, TXT, 1, UI, 400, width=RW - 170)
        text(ctx, "Abrir:", RX + 40, RY + 226, 26, TXT, 1, UI, 400, valign='m')
        foc = b + 2.1 <= t < b + 5.4
        input_box(ctx, RX + 130, RY + 200, RW - 175, 54, typed('run', t), foc, foc and caret_on(t, 'run'), size=28)
        button(ctx, *BTN_ACEPTAR, "Aceptar", primary=True, pressed=pressed(BTN_ACEPTAR, t), hover=hovering(BTN_ACEPTAR, t))
        button(ctx, 645, 1150, 150, 52, "Cancelar")
        button(ctx, 810, 1150, 150, 52, "Examinar...")
        ctx.restore(); pop(ctx, ra)

# ---------------------------------------------------------------- ADUC window
def tree_icon(ctx, kind, cx, cy, a=1.0):
    {'aduc': lambda: ic_aduc(ctx, cx, cy, 28, a), 'folder': lambda: ic_folder(ctx, cx, cy, 28, a),
     'domain': lambda: ic_domain(ctx, cx, cy, 30, a),
     'ou': lambda: ic_folder(ctx, cx, cy, 28, a, hx('2563EB'))}[kind]()

def list_icon(ctx, kind, cx, cy, a=1.0):
    if kind == 'user': ic_user(ctx, cx, cy, 30, hx('3B82F6'), a)
    elif kind == 'group': ic_group(ctx, cx, cy, 28, a)
    else: tree_icon(ctx, kind, cx, cy, a)

def draw_aduc(ctx, t):
    if not (T_S2 - 0.1 <= t <= T_OUT + 0.5): return
    pin = prog(t, T_S2 - 0.1, T_S2 + 0.5)
    pout = eio(prog(t, T_OUT - 0.1, T_OUT + 0.4))
    a = eout(pin) * (1 - pout)
    s = lerp(0.6, 1, eback(pin)) * lerp(1, 0.85, pout)
    push(ctx); ctx.save(); scale_at(ctx, 540, AY + AH / 2, s)
    win_frame(ctx, AX, AY, AW, AH, "Usuarios y equipos de Active Directory", ic_aduc)
    # menu bar
    mx = AX + 22
    for m in ["Archivo", "Acción", "Ver", "Ayuda"]:
        w, _ = text(ctx, m, mx, AY + 76, 23, TXT, 1, UI, 400, valign='m'); mx += w + 34
    # toolbar
    ctx.set_source_rgb(*hx('DADADA')); ctx.rectangle(AX + 1, AY + 98, AW - 2, 1); ctx.fill()
    tx = AX + 22
    for i in range(9):
        if i in (2, 5):
            ctx.set_source_rgb(*hx('CFCFCF')); ctx.rectangle(tx, AY + 110, 1.5, 28); ctx.fill(); tx += 16; continue
        if i == 0: chevron(ctx, tx + 14, AY + 124, 16, math.pi, hx('3B82F6'), 1, 3)
        elif i == 1: chevron(ctx, tx + 14, AY + 124, 16, 0, hx('9CA3AF'), 1, 3)
        elif i == 6: ic_user(ctx, tx + 14, AY + 124, 28, hx('3B82F6'))
        elif i == 7: ic_group(ctx, tx + 14, AY + 124, 26)
        elif i == 8: ic_folder(ctx, tx + 14, AY + 124, 26, 1, hx('2563EB'))
        else: ic_folder(ctx, tx + 14, AY + 124, 26)
        tx += 46
    # panes
    ctx.rectangle(AX + 1, CY0, LPW, AH - 150 - 36); ctx.set_source_rgb(1, 1, 1); ctx.fill()
    ctx.rectangle(AX + LPW + 3, CY0, AW - LPW - 4, AH - 150 - 36); ctx.fill()
    ctx.set_source_rgb(*hx('DADADA')); ctx.rectangle(AX + 1, CY0 - 1, AW - 2, 1); ctx.fill()
    # tree
    ctx.save(); ctx.rectangle(AX + 1, CY0, LPW, AH - 150 - 36); ctx.clip()
    E0 = T_S2 + 2.1
    exp = eio(prog(t, T_S2 + 2.0, T_S2 + 2.25))
    sel_ventas = t >= T_S2 + 4.1
    rows = [(lvl, lab, ic, 1.0, 0) for (lvl, lab, ic) in TREE_TOP]
    for i, (lab, ic) in enumerate(TREE_CH):
        ca = eout(prog(t, E0 + i * 0.07, E0 + i * 0.07 + 0.25))
        rows.append((2, lab, ic, ca, -20 * (1 - ca)))
    for r, (lvl, lab, ic, ra, dx) in enumerate(rows):
        if ra <= 0: continue
        ry = TY + r * TRH
        if r == 9 and sel_ventas:
            fill_rr(ctx, AX + 6, ry + 2, LPW - 10, TRH - 4, 6, hx('D6E9FA'))
            fill_rr(ctx, AX + 6, ry + 12, 4, TRH - 24, 2, WIN_ACCENT)
        elif hovering((AX + 6, ry + 2, LPW - 10, TRH - 4), t) and t < T_S4:
            fill_rr(ctx, AX + 6, ry + 2, LPW - 10, TRH - 4, 6, hx('EEF2F6'))
        x0 = AX + 12 + lvl * 30 + dx
        if r in (0, 2):
            ang = math.pi / 2 if r == 0 else math.pi / 2 * exp
            chevron(ctx, x0 + 6, ry + TRH / 2, 12, ang, hx('5F5F5F'), ra, 2)
        elif r == 1:
            chevron(ctx, x0 + 6, ry + TRH / 2, 12, 0, hx('5F5F5F'), ra, 2)
        tree_icon(ctx, ic, x0 + 34, ry + TRH / 2, ra)
        text(ctx, lab, x0 + 56, ry + TRH / 2, 24, TXT, ra, UI, 600 if (r == 9 and sel_ventas) else 400,
             valign='m', width=LPW - (x0 + 56 - AX) - 10, ellipsize=True)
    ctx.restore()
    ctx.set_source_rgb(*hx('DADADA')); ctx.rectangle(AX + LPW + 1, CY0, 2, AH - 150 - 36); ctx.fill()
    # right list
    RX0 = AX + LPW + 3
    ctx.save(); ctx.rectangle(RX0, CY0, AW - LPW - 4, AH - 150 - 36); ctx.clip()
    text(ctx, "Nombre", RX0 + 18, CY0 + 22, 22, GRAY, 1, UI, 600, valign='m')
    text(ctx, "Tipo", RX0 + 290, CY0 + 22, 22, GRAY, 1, UI, 600, valign='m')
    ctx.set_source_rgb(*hx('E2E2E2')); ctx.rectangle(RX0, CY0 + 44, AW, 1); ctx.rectangle(RX0 + 275, CY0 + 8, 1, 28); ctx.fill()
    LY = CY0 + 52
    if not sel_ventas:
        items = [("Consultas guardadas", 'folder', "", 1, 0), ("empresa.local", 'domain', "Dominio", 1, 0)]
        n_obj = 2
    else:
        ins = prog(t, T_S6 + 0.4, T_S6 + 0.9)
        ia = eout(ins)
        base = [("Luis Pérez", 'user', "Usuario"), ("María López", 'user', "Usuario"), ("Ventas-Equipo", 'group', "Grupo de seguridad")]
        items = []
        if ins > 0:
            items.append(("Ana García", 'user', "Usuario", ia, 0))
        for i, (n, k, ty) in enumerate(base):
            la = eout(prog(t, T_S2 + 4.2 + i * 0.08, T_S2 + 4.5 + i * 0.08))
            items.append((n, k, ty, la, -TRH * (1 - eio(ins)) if ins > 0 else 0))
        n_obj = 4 if ins > 0 else 3
    for i, (n, k, ty, la, dy) in enumerate(items):
        ry = LY + i * TRH + dy
        if n == "Ana García":
            ry = LY
            gp = 0.5 + 0.5 * math.sin((t - T_S6) * 5)
            fill_rr(ctx, RX0 + 6, ry + 2, AW - LPW - 16, TRH - 4, 6, hx('D1FAE5'), la)
            stroke_rr(ctx, RX0 + 6, ry + 2, AW - LPW - 16, TRH - 4, 6, hx('10B981'), la * (0.5 + 0.5 * gp), 2.5)
        list_icon(ctx, k, RX0 + 34, ry + TRH / 2, la)
        text(ctx, n, RX0 + 58, ry + TRH / 2, 24, TXT, la, UI, 600 if n == "Ana García" else 400, valign='m', width=210, ellipsize=True)
        text(ctx, ty, RX0 + 290, ry + TRH / 2, 24, GRAY, la, UI, 400, valign='m', width=AW - LPW - 300, ellipsize=True)
    ctx.restore()
    # status bar
    ctx.set_source_rgb(*hx('DADADA')); ctx.rectangle(AX + 1, AY + AH - 36, AW - 2, 1); ctx.fill()
    text(ctx, f"{n_obj} objetos", AX + 22, AY + AH - 18, 20, GRAY, 1, UI, 400, valign='m')
    # highlight ring around Ventas
    ha = win(t, T_S2 + 4.1, T_S3 + 0.5, .3, .3)
    if ha > 0:
        pp = 0.5 + 0.5 * math.sin((t - T_S2) * 6)
        glow_rr(ctx, AX + 4, VENTAS_ROW_Y, LPW - 6, TRH, 8, CYAN, ha * (0.6 + 0.4 * pp), 6, 3)
        stroke_rr(ctx, AX + 4, VENTAS_ROW_Y, LPW - 6, TRH, 8, CYAN, ha, 3)
    # expander highlight before click
    ea = win(t, T_S2 + 0.8, T_S2 + 2.2, .3, .2)
    if ea > 0:
        ctx.set_source_rgba(*CYAN, ea); ctx.set_line_width(3)
        ctx.arc(EXPANDER[0], EXPANDER[1], 20 + 3 * math.sin(t * 8), 0, 2 * math.pi); ctx.stroke()
    # dim when dialog open
    da = 0.55 * win(t, T_S4, T_S6 + 0.4, .3, .35)
    if da > 0:
        rrect(ctx, AX, AY, AW, AH, 14); ctx.set_source_rgba(*hx('0A0F2C'), da); ctx.fill()
    ctx.restore(); pop(ctx, a)

# ---------------------------------------------------------------- context menu
def draw_menu(ctx, t):
    t0, t1 = T_S3 + 0.7, T_S3 + 4.05
    a = win(t, t0, t1, .15, .15)
    if a <= 0: return
    sub_open = t >= T_S3 + 2.0
    push(ctx); ctx.save()
    sc = lerp(0.92, 1, eout(prog(t, t0, t0 + .2)))
    scale_at(ctx, MX, MY + MH, sc)
    shadow(ctx, MX, MY, MW, MH, 12, 1.2, 8)
    fill_rr(ctx, MX, MY, MW, MH, 12, hx('F9F9F9')); stroke_rr(ctx, MX, MY, MW, MH, 12, hx('D0D0D0'), 1, 1.2)
    for (it, y0, hh) in MENU_ROWS:
        if it is None:
            ctx.set_source_rgb(*hx('E0E0E0')); ctx.rectangle(MX + 12, y0 + hh / 2, MW - 24, 1); ctx.fill(); continue
        hov = hovering((MX, y0, MW, hh), t) or (it == "Nuevo" and sub_open)
        if hov: fill_rr(ctx, MX + 6, y0 + 3, MW - 12, hh - 6, 6, hx('E6E6E6') if it != "Nuevo" else hx('DCEBFA'))
        text(ctx, it, MX + 24, y0 + hh / 2, 24, TXT, 1, UI, 600 if (it == "Nuevo" and sub_open) else 400, valign='m')
        if it in ("Nuevo", "Todas las tareas"):
            chevron(ctx, MX + MW - 26, y0 + hh / 2, 12, 0, TXT, 1, 2)
    ctx.restore()
    if sub_open:
        sa = eout(prog(t, T_S3 + 2.0, T_S3 + 2.2))
        ctx.save(); ctx.translate(-14 * (1 - sa), 0)
        push(ctx)
        shadow(ctx, SX, SY, SMW, SMH, 12, 1.2, 8)
        fill_rr(ctx, SX, SY, SMW, SMH, 12, hx('F9F9F9')); stroke_rr(ctx, SX, SY, SMW, SMH, 12, hx('D0D0D0'), 1, 1.2)
        for (it, y0, hh) in SUB_ROWS:
            hov = hovering((SX, y0, SMW, hh), t) or (it == "Usuario" and t >= T_S3 + 3.5)
            if hov:
                fill_rr(ctx, SX + 6, y0 + 3, SMW - 12, hh - 6, 6, hx('DCEBFA') if it == "Usuario" else hx('E6E6E6'))
            text(ctx, it, SX + 24, y0 + hh / 2, 24, TXT, 1, UI, 600 if (it == "Usuario" and hov) else 400, valign='m')
        pop(ctx, sa); ctx.restore()
    pop(ctx, a)

# ---------------------------------------------------------------- new user dialog
def label(ctx, s, x, field, size=25):
    text(ctx, s, x, field[1] + field[3] / 2, size, TXT, 1, UI, 400, valign='m')

def page1(ctx, t):
    f = focused(t)
    nom, ape, log = typed('nombre', t), typed('apellidos', t), typed('logon', t)
    label(ctx, "Nombre:", 100, F_NOMBRE)
    input_box(ctx, *F_NOMBRE, nom, f == 'nombre', f == 'nombre' and caret_on(t, 'nombre'))
    label(ctx, "Iniciales:", 660, F_INIC)
    input_box(ctx, *F_INIC, "")
    label(ctx, "Apellidos:", 100, F_APELL)
    input_box(ctx, *F_APELL, ape, f == 'apellidos', f == 'apellidos' and caret_on(t, 'apellidos'))
    label(ctx, "Nombre completo:", 100, F_FULL)
    full = (nom + " " + ape).strip()
    fa = win(t, T_S4 + 3.1, T_S4 + 5.8, .3, .4)
    if fa > 0:
        glow_rr(ctx, *F_FULL, 6, YELLOW, fa, 6, 3)
    input_box(ctx, *F_FULL, full)
    if fa > 0:
        chip(ctx, F_FULL[0] + F_FULL[2] - 140, F_FULL[1] + 24, "¡Se completa solo!", hx('D97706'), fa,
             eback(prog(t, T_S4 + 3.1, T_S4 + 3.5)), 22)
    text(ctx, "Nombre de inicio de sesión de usuario:", 100, 905, 25, TXT, 1, UI, 400, valign='m')
    la = win(t, T_S4 + 5.3, T_S4 + 8.6, .3, .4)
    if la > 0:
        glow_rr(ctx, F_LOGON[0], F_LOGON[1], F_DOM[0] + F_DOM[2] - F_LOGON[0], 48, 6, GREEN, la, 6, 3)
    input_box(ctx, *F_LOGON, log, f == 'logon', f == 'logon' and caret_on(t, 'logon'))
    input_box(ctx, *F_DOM, "@empresa.local")
    chevron(ctx, F_DOM[0] + F_DOM[2] - 26, F_DOM[1] + 24, 12, math.pi / 2, TXT, 1, 2)
    text(ctx, "Nombre de inicio de sesión (anterior a Windows 2000):", 100, 1030, 25, TXT, 1, UI, 400, valign='m')
    input_box(ctx, *F_PRE1, "EMPRESA\\", disabled=True)
    input_box(ctx, *F_PRE2, log)
    if la > 0:
        chip(ctx, 735, 1180, "Así iniciará sesión: agarcia@empresa.local", hx('059669'), la,
             eback(prog(t, T_S4 + 5.3, T_S4 + 5.7)), 22, 'check')

def page2(ctx, t):
    f = focused(t)
    label(ctx, "Contraseña:", 100, F_PWD)
    input_box(ctx, *F_PWD, typed('pwd', t), f == 'pwd', f == 'pwd' and caret_on(t, 'pwd'), dots=True)
    label(ctx, "Confirmar contraseña:", 100, F_PWD2)
    input_box(ctx, *F_PWD2, typed('pwd2', t), f == 'pwd2', f == 'pwd2' and caret_on(t, 'pwd2'), dots=True)
    # strength meter
    sp = eio(prog(t, T_S5 + 1.0, T_S5 + 4.2))
    if sp > 0:
        fill_rr(ctx, F_PWD[0], 822, F_PWD[2], 10, 5, hx('E5E7EB'))
        col = (lerp(0.94, 0.06, sp), lerp(0.27, 0.73, sp), lerp(0.27, 0.5, sp))
        fill_rr(ctx, F_PWD[0], 822, max(10, F_PWD[2] * sp), 10, 5, col)
        lab = "Débil" if sp < .35 else ("Media" if sp < .7 else "Fuerte")
        text(ctx, f"Seguridad: {lab}", 100, 827, 21, col, 1, UI, 600, valign='m')
    cks = ["El usuario debe cambiar la contraseña en el siguiente inicio de sesión",
           "El usuario no puede cambiar la contraseña", "La contraseña nunca expira", "La cuenta está deshabilitada"]
    ca = win(t, T_S5 + 4.3, T_S5 + 7.3, .3, .4)
    if ca > 0:
        pp = 0.6 + 0.4 * math.sin((t - T_S5) * 6)
        glow_rr(ctx, 86, CHK_Y[0] - 14, 850, 92, 12, CYAN, ca * pp, 6, 3)
        stroke_rr(ctx, 86, CHK_Y[0] - 14, 850, 92, 12, CYAN, ca, 3)
    for i, s in enumerate(cks):
        checkbox(ctx, 100, CHK_Y[i], i == 0)
        text(ctx, s, 148, CHK_Y[i] - 2, 24, TXT, 1, UI, 400, width=770)
    if ca > 0:
        chip(ctx, 790, CHK_Y[0] - 14, "Recomendado", hx('0891B2'), ca, eback(prog(t, T_S5 + 4.3, T_S5 + 4.7)), 22, 'check')

def page3(ctx, t):
    text(ctx, "Al hacer clic en Finalizar, se creará el siguiente objeto:", 100, 690, 25, TXT, 1, UI, 400, width=820)
    fill_rr(ctx, 100, 760, 820, 400, 8, WHITE); stroke_rr(ctx, 100, 760, 820, 400, 8, hx('C4C4C4'), 1, 1.2)
    lines = ["Nombre completo: <b>Ana García</b>", "",
             "Nombre de inicio de sesión de usuario: <b>agarcia@empresa.local</b>", "",
             "El usuario debe cambiar la contraseña en el siguiente inicio de sesión."]
    text(ctx, "\n".join(lines), 125, 785, 25, TXT, 1, UI, 400, width=770, markup=True, spacing=4)

def draw_dialog(ctx, t):
    t0, t1 = T_S4, T_S6 + 0.4
    if not (t0 <= t <= t1): return
    pin = prog(t, t0, t0 + .45)
    pout = eio(prog(t, T_S6, T_S6 + 0.4))
    a = eout(pin) * (1 - pout)
    s = lerp(0.85, 1, eback(pin)) * lerp(1, 0.9, pout)
    push(ctx); ctx.save(); scale_at(ctx, 540, DY + DH / 2, s)
    win_frame(ctx, DX, DY, DW, DH, "Nuevo objeto: Usuario", lambda c, x, y, sz: ic_user(c, x, y, sz, hx('3B82F6')))
    ic_user(ctx, 128, 600, 56, hx('3B82F6'))
    text(ctx, "Crear en:", 180, 600, 25, GRAY, 1, UI, 400, valign='m')
    text(ctx, "empresa.local/Ventas", 300, 600, 25, TXT, 1, UI, 600, valign='m')
    ctx.set_source_rgb(*hx('D6D6D6')); ctx.rectangle(DX + 24, 650, DW - 48, 1); ctx.fill()
    # pages with slide
    p12 = eio(prog(t, T_S5, T_S5 + .5)); p23 = eio(prog(t, T_S5 + 7.6, T_S5 + 8.1))
    off = -DW * (p12 + p23)
    ctx.save(); ctx.rectangle(DX + 1, 655, DW - 2, 605); ctx.clip()
    for i, fn in enumerate([page1, page2, page3]):
        o = off + i * DW
        if abs(o) < DW:
            ctx.save(); ctx.translate(o, 0); fn(ctx, t); ctx.restore()
    ctx.restore()
    ctx.set_source_rgb(*hx('D6D6D6')); ctx.rectangle(DX + 24, 1262, DW - 48, 1); ctx.fill()
    page = 0 if t < T_S5 + .25 else (1 if t < T_S5 + 7.85 else 2)
    button(ctx, *BTN_BACK, "< Atrás", disabled=(page == 0))
    button(ctx, *BTN_NEXT, "Finalizar" if page == 2 else "Siguiente >", primary=True,
           pressed=pressed(BTN_NEXT, t), hover=hovering(BTN_NEXT, t))
    button(ctx, *BTN_CANCEL, "Cancelar")
    ctx.restore(); pop(ctx, a)

# ---------------------------------------------------------------- success
_cr = random.Random(3)
CONFETTI = [(_cr.uniform(-1, 1) * 900, _cr.uniform(-1500, -500), _cr.uniform(0, 6.28), _cr.uniform(-9, 9),
             _cr.choice([CYAN, PINK, YELLOW, GREEN, VIOLET, WHITE]), _cr.uniform(10, 22), _cr.uniform(0, 0.25)) for _ in range(110)]

def draw_success(ctx, t):
    b = T_S6 + 1.0
    if not (b - 0.1 <= t <= b + 4.0): return
    cx, cy = 540, 900
    a = 1 - eio(prog(t, b + 3.0, b + 3.5))
    s = eback(prog(t, b, b + 0.5), 2.2)
    # rings
    for k in range(2):
        p = prog(t, b + k * 0.15, b + 0.9 + k * 0.15)
        if 0 < p < 1:
            ctx.set_source_rgba(*GREEN, 0.7 * (1 - p)); ctx.set_line_width(8 * (1 - p) + 1)
            ctx.arc(cx, cy, 120 + 220 * eout(p), 0, 2 * math.pi); ctx.stroke()
    if s > 0 and a > 0:
        push(ctx); ctx.save(); scale_at(ctx, cx, cy, s)
        glow_rr(ctx, cx - 130, cy - 130, 260, 260, 130, GREEN, 1, 10, 5)
        g = cairo.LinearGradient(cx - 130, cy - 130, cx + 130, cy + 130)
        g.add_color_stop_rgb(0, *hx('6EE7B7')); g.add_color_stop_rgb(1, *hx('059669'))
        ctx.arc(cx, cy, 130, 0, 2 * math.pi); ctx.set_source(g); ctx.fill()
        check_mark(ctx, cx, cy + 6, 170, WHITE, 1, 22, eout(prog(t, b + 0.2, b + 0.6)))
        ctx.restore()
        ps = eback(prog(t, b + 0.35, b + 0.8))
        if ps > 0:
            ctx.save(); scale_at(ctx, cx, cy + 210, ps)
            lab = "¡Usuario creado!"
            w, h = tsize(ctx, lab, 56, HEAD, 800)
            shadow(ctx, cx - w / 2 - 40, cy + 170, w + 80, 84, 42, 1.2, 8)
            fill_rr(ctx, cx - w / 2 - 40, cy + 170, w + 80, 84, 42, WHITE)
            text(ctx, lab, cx, cy + 212, 56, hx('065F46'), 1, HEAD, 800, 'c', 'm')
            ctx.restore()
        pop(ctx, a)
    # confetti
    dt = t - b
    for (vx, vy, rot, vr, col, sz, delay) in CONFETTI:
        d = dt - delay
        if d <= 0 or d > 3.2: continue
        x = cx + vx * d * (1 - 0.25 * d)
        y = cy + vy * d + 0.5 * 1500 * d * d
        if y > H + 40: continue
        ca = clamp(1 - (d - 2.2))
        ctx.save(); ctx.translate(x, y); ctx.rotate(rot + vr * d)
        ctx.scale(1, abs(math.cos(d * 6 + rot)) + 0.2)
        ctx.rectangle(-sz / 2, -sz / 4, sz, sz / 2); ctx.set_source_rgba(*col, ca); ctx.fill(); ctx.restore()

# ---------------------------------------------------------------- outro
RECAP = [("Win + R  →  dsa.msc", "Abre Usuarios y equipos de AD"),
         ("Elige la OU", "Dentro de tu dominio"),
         ("Clic derecho → Nuevo → Usuario", "Se abre el asistente"),
         ("Datos + contraseña → Finalizar", "¡Listo para iniciar sesión!")]

def draw_outro(ctx, t):
    b = T_OUT
    if t < b: return
    a = 1 - eio(prog(t, DUR - 0.6, DUR))
    push(ctx)
    ta = eout(prog(t, b + .2, b + .7))
    tw, th = text(ctx, "Resumen rápido", 60, 250 + 40 * (1 - ta), 82, WHITE, ta, HEAD, 800)
    uw = tw * eout(prog(t, b + .5, b + 1.1))
    if uw > 4:
        g = cairo.LinearGradient(60, 0, 60 + tw, 0)
        g.add_color_stop_rgb(0, *CYAN); g.add_color_stop_rgb(1, *PINK)
        rrect(ctx, 60, 250 + th + 6, uw, 9, 4.5); ctx.set_source(g); ctx.fill()
    cols = [CYAN, YELLOW, PINK, GREEN]
    for i, (h1, h2) in enumerate(RECAP):
        p = prog(t, b + 0.7 + i * 0.35, b + 1.2 + i * 0.35)
        if p <= 0: continue
        ca = eout(p); dx = 80 * (1 - eout(p))
        y = 470 + i * 200
        push(ctx); ctx.save(); ctx.translate(dx, 0)
        fill_rr(ctx, 60, y, 960, 170, 32, WHITE, 0.08)
        stroke_rr(ctx, 60, y, 960, 170, 32, cols[i], 0.5, 2)
        g = cairo.LinearGradient(100, y + 40, 190, y + 130)
        g.add_color_stop_rgb(0, *cols[i]); g.add_color_stop_rgb(1, *VIOLET)
        ctx.arc(150, y + 85, 48, 0, 2 * math.pi); ctx.set_source(g); ctx.fill()
        text(ctx, str(i + 1), 150, y + 85, 52, WHITE, 1, HEAD, 800, 'c', 'm')
        text(ctx, h1, 230, y + 40, 40, WHITE, 1, HEAD, 800, width=770, ellipsize=True)
        text(ctx, h2, 230, y + 98, 30, hx('CBD5E1'), 1, HEAD, 500)
        ctx.restore(); pop(ctx, ca)
    cp = eback(prog(t, b + 2.6, b + 3.1))
    if cp > 0:
        pulse = 1 + 0.03 * math.sin((t - b) * 5)
        lab = "Guárdalo para tenerlo a mano"
        w, h = tsize(ctx, lab, 40, HEAD, 800)
        push(ctx); ctx.save(); scale_at(ctx, 540, 1335, cp * pulse)
        g = cairo.LinearGradient(540 - w / 2 - 90, 0, 540 + w / 2 + 50, 0)
        g.add_color_stop_rgb(0, *CYAN); g.add_color_stop_rgb(1, *VIOLET)
        glow_rr(ctx, 540 - w / 2 - 80, 1290, w + 140, 90, 45, VIOLET, 1, 8, 4)
        rrect(ctx, 540 - w / 2 - 80, 1290, w + 140, 90, 45); ctx.set_source(g); ctx.fill()
        bx, by = 540 - w / 2 - 40, 1335  # bookmark icon
        ctx.move_to(bx - 14, by - 22); ctx.line_to(bx + 14, by - 22); ctx.line_to(bx + 14, by + 22)
        ctx.line_to(bx, by + 10); ctx.line_to(bx - 14, by + 22); ctx.close_path()
        ctx.set_source_rgb(1, 1, 1); ctx.fill()
        text(ctx, lab, 540 + 30, 1335, 40, WHITE, 1, HEAD, 800, 'c', 'm')
        ctx.restore(); pop(ctx, clamp(cp))
    fa = eout(prog(t, b + 3.3, b + 3.8))
    text(ctx, "Sígueme para más tutoriales de IT", 540, 1450, 36, hx('CBD5E1'), fa, HEAD, 600, 'c')
    pop(ctx, a)

# ---------------------------------------------------------------- frame
def render_frame(t):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    draw_bg(ctx, t)
    draw_intro(ctx, t)
    draw_header(ctx, t)
    draw_s1(ctx, t)
    draw_aduc(ctx, t)
    draw_menu(ctx, t)
    draw_dialog(ctx, t)
    draw_success(ctx, t)
    draw_outro(ctx, t)
    draw_caption(ctx, t)
    draw_cursor(ctx, t)
    # global fade in
    fi = 1 - prog(t, 0, 0.4)
    if fi > 0:
        ctx.set_source_rgba(0, 0, 0, fi); ctx.paint()
    surf.flush()
    return surf

def frame_bytes(i):
    return bytes(render_frame(i / FPS).get_data())

# ---------------------------------------------------------------- audio
SR = 44100
def midi(n): return 440 * 2 ** ((n - 69) / 12)

def build_audio(path):
    n = int(DUR * SR) + SR
    L = np.zeros(n); R = np.zeros(n)
    rng = np.random.default_rng(1)

    def add(sig, t, gain=1.0, pan=0.0):
        i = int(t * SR)
        if i >= n: return
        sig = sig[:n - i]
        L[i:i + len(sig)] += sig * gain * (1 - max(0, pan))
        R[i:i + len(sig)] += sig * gain * (1 + min(0, pan))

    def tt(d): return np.arange(int(d * SR)) / SR

    # --- music: 96 bpm, chords Cmaj7 Am7 Fmaj7 G6
    beat = 60 / 96; bar = beat * 4
    chords = [[48, 60, 64, 67, 71], [45, 57, 60, 64, 67], [41, 57, 60, 64, 69], [43, 55, 59, 62, 64]]
    music_end = DUR
    nbars = int(music_end / bar) + 1
    for bi in range(nbars):
        t0 = bi * bar
        ch = chords[bi % 4]
        d = bar + 0.6
        x = tt(d)
        env = np.minimum(1, x / 0.35) * np.minimum(1, (d - x) / 0.6)
        for k, m in enumerate(ch):
            f = midi(m)
            v = 0.05 if k == 0 else 0.028
            sig = (np.sin(2 * np.pi * f * x) + 0.25 * np.sin(4 * np.pi * f * x)) * env * (1 + 0.1 * np.sin(2 * np.pi * 4 * x))
            add(sig, t0, v, pan=(-0.3 if k % 2 else 0.3))
        # pluck arpeggio
        arp = [ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[4] + 12, ch[3] + 12, ch[2] + 12, ch[4] + 12, ch[1] + 24]
        for k, m in enumerate(arp):
            if bi == 0: break
            x = tt(0.5); f = midi(m)
            sig = (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(6 * np.pi * f * x) * np.exp(-x * 20)) * np.exp(-x * 7)
            add(sig, t0 + k * beat / 2, 0.035, pan=0.4 * math.sin(k))
        if bi >= 1:
            for k in range(4):
                tb = t0 + k * beat
                if k in (0, 2):  # kick
                    x = tt(0.3); f = 45 + 80 * np.exp(-x * 30)
                    add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 14), tb, 0.22)
                else:  # soft clap
                    x = tt(0.2); nz = rng.standard_normal(len(x)); nz = np.diff(nz, prepend=0)
                    add(nz * np.exp(-x * 30), tb, 0.025)
                x = tt(0.06); nz = np.diff(rng.standard_normal(len(x)), prepend=0)
                add(nz * np.exp(-x * 90), tb + beat / 2, 0.018, pan=0.3)
    # music fade in/out
    env = np.ones(n); tl = np.arange(n) / SR
    env *= np.clip(tl / 1.5, 0, 1); env *= np.clip((DUR - tl) / 1.5, 0, 1)
    L *= env; R *= env

    # --- sfx
    def click():
        x = tt(0.05); return np.sin(2 * np.pi * 1900 * x) * np.exp(-x * 160) + 0.4 * rng.standard_normal(len(x)) * np.exp(-x * 400)
    def rclick():
        x = tt(0.06); return np.sin(2 * np.pi * 1200 * x) * np.exp(-x * 120) + 0.4 * rng.standard_normal(len(x)) * np.exp(-x * 400)
    def tick(fr=1300):
        x = tt(0.05); return np.sin(2 * np.pi * fr * x) * np.exp(-x * 120)
    def typ():
        x = tt(0.03); f = rng.uniform(2500, 3800)
        return 0.6 * np.diff(rng.standard_normal(len(x)), prepend=0) * np.exp(-x * 300) + 0.5 * np.sin(2 * np.pi * f * x) * np.exp(-x * 350)
    def thock():
        x = tt(0.15); return np.sin(2 * np.pi * 170 * x) * np.exp(-x * 35) + 0.3 * rng.standard_normal(len(x)) * np.exp(-x * 120)
    def pop_s(f0=380, f1=1000):
        x = tt(0.12); f = f0 + (f1 - f0) * np.clip(x / 0.09, 0, 1)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * np.clip(x / 0.12, 0, 1))
    def whoosh(d=0.5):
        x = tt(d); nz = rng.standard_normal(len(x))
        k = np.ones(24) / 24; nz = np.convolve(nz, k, mode='same')
        env = np.sin(np.pi * x / d) ** 2
        return nz * env * 3
    def chime():
        out = np.zeros(int(1.8 * SR))
        for k, m in enumerate([84, 88, 91, 96]):
            x = tt(1.8 - k * 0.09); f = midi(m)
            s = (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(4 * np.pi * f * x)) * np.exp(-x * 3)
            i = int(k * 0.09 * SR); out[i:i + len(s)] += s
        return out

    for (ct, kind) in CLICKS:
        add(click() if kind == 'L' else rclick(), ct, 0.35)
    for k in TYPES:
        for ct in char_times(k):
            add(typ(), ct, 0.22, pan=rng.uniform(-.2, .2))
    add(thock(), T_S1 + 1.4, 0.5); add(thock(), T_S1 + 1.6, 0.5)
    for (_, t0, _) in INTRO_NODES:
        add(pop_s(500, 1100), t0, 0.12)
    add(whoosh(0.7), 0.4, 0.25)
    for t0 in [T_S1 + .5, T_S1 + .65, T_S1 + .8]: add(pop_s(), t0, 0.18)
    add(pop_s(300, 800), T_S1 + 2.1, 0.22)
    add(pop_s(500, 900), T_S1 + 5.8, 0.15)
    add(whoosh(0.5), T_S2 - 0.25, 0.3)
    for i in range(len(TREE_CH)): add(tick(1100 + i * 90), T_S2 + 2.1 + i * 0.07, 0.12)
    for i in range(3): add(tick(1500), T_S2 + 4.2 + i * 0.08, 0.1)
    add(pop_s(300, 700), T_S3 + 0.7, 0.18); add(pop_s(400, 800), T_S3 + 2.0, 0.12)
    add(pop_s(250, 750), T_S4, 0.22)
    add(pop_s(600, 1200), T_S4 + 3.1, 0.12); add(pop_s(600, 1200), T_S4 + 5.3, 0.12)
    add(whoosh(0.45), T_S5, 0.22); add(whoosh(0.45), T_S5 + 7.6, 0.22)
    add(pop_s(600, 1200), T_S5 + 4.3, 0.12)
    add(whoosh(0.4), T_S6, 0.15)
    add(pop_s(500, 1000), T_S6 + 0.5, 0.15)
    add(chime(), T_S6 + 1.0, 0.3)
    add(whoosh(0.6), T_OUT - 0.2, 0.25)
    for i in range(4): add(pop_s(500, 1000), T_OUT + 0.7 + i * 0.35, 0.14)
    add(pop_s(300, 900), T_OUT + 2.6, 0.2)

    st = np.stack([L, R], 1)[:int(DUR * SR)]
    st = np.tanh(st * 1.2) * 0.9
    pcm = (st * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

# ---------------------------------------------------------------- main
def main():
    if '--stills' in sys.argv:
        secs = [float(s) for s in sys.argv[sys.argv.index('--stills') + 1].split(',')]
        d = os.path.join(HERE, 'stills'); os.makedirs(d, exist_ok=True)
        for s in secs:
            render_frame(s).write_to_png(os.path.join(d, f"t{s:05.1f}.png"))
        print("ok", d); return
    from multiprocessing import Pool
    audio = os.path.join(HERE, 'audio.wav')
    build_audio(audio)
    out = os.path.join(OUT_DIR, 'crear_usuario_active_directory.mp4')
    nframes = int(DUR * FPS)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-i', audio, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(max(1, os.cpu_count() - 2)) as pool:
        for i, fb in enumerate(pool.imap(frame_bytes, range(nframes), chunksize=4)):
            ff.stdin.write(fb)
            if i % 150 == 0: print(f"frame {i}/{nframes}", flush=True)
    ff.stdin.close(); ff.wait()
    print("listo:", out)

if __name__ == '__main__':
    main()
