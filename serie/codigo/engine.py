"""Motor de animación para la serie "Seguridad en Active Directory".
Cada episodio es una especificación declarativa (episodios/epXX.py) que este motor convierte en video.
Formato vertical 1080x1920 @30fps.
"""
import math, random, sys, os, subprocess, wave, importlib
import numpy as np
import cairo
import gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo

W, H, FPS = 1080, 1920, 30
UI, HEAD, BIG, MONO = "Adwaita Sans", "Clarity City", "Bebas Neue", "JetBrains Mono"
SERIES = "SEGURIDAD EN ACTIVE DIRECTORY"
N_EPISODES = 7

def hx(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)

CYAN, VIOLET, PINK = hx('22D3EE'), hx('8B5CF6'), hx('F472B6')
GREEN, YELLOW, WHITE = hx('34D399'), hx('FBBF24'), (1, 1, 1)
RED, ORANGE, BLUE = hx('F87171'), hx('FB923C'), hx('60A5FA')
MUTED, NAVY = hx('CBD5E1'), hx('0A0F2C')
LEVELS = {'BÁSICO': GREEN, 'INTERMEDIO': YELLOW, 'AVANZADO': ORANGE, 'EXPERTO': PINK}

def mk(s, col='#67E8F9'): return f'<span foreground="{col}">{s}</span>'
def cy(s): return mk(s, '#67E8F9')
def ye(s): return mk(s, '#FCD34D')
def gr(s): return mk(s, '#6EE7B7')
def rd(s): return mk(s, '#FCA5A5')
def pk(s): return mk(s, '#F9A8D4')

# ------------------------------------------------------------------ easing
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
def darker(c, k=0.55): return tuple(v * k for v in c)
def mix(a, b, k): return tuple(lerp(x, y, k) for x, y in zip(a, b))

# ------------------------------------------------------------------ text
WEIGHTS = {300: Pango.Weight.LIGHT, 400: Pango.Weight.NORMAL, 500: Pango.Weight.MEDIUM,
           600: Pango.Weight.SEMIBOLD, 700: Pango.Weight.BOLD, 800: Pango.Weight.ULTRABOLD}
_fd = {}
def fdesc(family, size, weight):
    k = (family, size, weight)
    if k not in _fd:
        fd = Pango.FontDescription(); fd.set_family(family); fd.set_weight(WEIGHTS[weight])
        fd.set_absolute_size(size * Pango.SCALE); _fd[k] = fd
    return _fd[k]

def layout(ctx, s, size, family=HEAD, weight=400, width=None, align='l', markup=False, ellipsize=False, spacing=0, wrapchar=False):
    L = PangoCairo.create_layout(ctx)
    L.set_font_description(fdesc(family, size, weight))
    if width:
        L.set_width(int(width * Pango.SCALE))
        if ellipsize: L.set_ellipsize(Pango.EllipsizeMode.END)
        else: L.set_wrap(Pango.WrapMode.CHAR if wrapchar else Pango.WrapMode.WORD_CHAR)
        L.set_alignment({'l': Pango.Alignment.LEFT, 'c': Pango.Alignment.CENTER, 'r': Pango.Alignment.RIGHT}[align])
    if spacing: L.set_spacing(int(spacing * Pango.SCALE))
    if markup: L.set_markup(s, -1)
    else: L.set_text(s, -1)
    return L

def text(ctx, s, x, y, size, color=WHITE, alpha=1.0, family=HEAD, weight=400, align='l', valign='t',
         width=None, markup=False, ellipsize=False, spacing=0, wrapchar=False):
    if alpha <= 0.003: return (0, 0)
    L = layout(ctx, s, size, family, weight, width, align, markup, ellipsize, spacing, wrapchar)
    w, h = L.get_pixel_size()
    dx = ({'l': 0, 'c': -width / 2, 'r': -width} if width else {'l': 0, 'c': -w / 2, 'r': -w})[align]
    dy = {'t': 0, 'm': -h / 2, 'b': -h}[valign]
    ctx.save(); ctx.set_source_rgba(*color[:3], alpha); ctx.move_to(x + dx, y + dy)
    PangoCairo.show_layout(ctx, L); ctx.new_path(); ctx.restore()
    return (w, h)

def tsize(ctx, s, size, family=HEAD, weight=400, markup=False, width=None, spacing=0):
    return layout(ctx, s, size, family, weight, width, markup=markup, spacing=spacing).get_pixel_size()

def fit(ctx, s, size, maxw, family=HEAD, weight=800, markup=False):
    while size > 20 and tsize(ctx, s, size, family, weight, markup)[0] > maxw: size -= 2
    return size

# ------------------------------------------------------------------ shapes
def rrect(ctx, x, y, w, h, r):
    r = max(0, min(r, w / 2, h / 2))
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()
def fill_rr(ctx, x, y, w, h, r, col, a=1.0):
    rrect(ctx, x, y, w, h, r); ctx.set_source_rgba(*col[:3], a); ctx.fill()
def stroke_rr(ctx, x, y, w, h, r, col, a=1.0, lw=1.5, dash=None):
    rrect(ctx, x, y, w, h, r); ctx.set_source_rgba(*col[:3], a); ctx.set_line_width(lw)
    if dash: ctx.set_dash(dash)
    ctx.stroke(); ctx.set_dash([])
def shadow(ctx, x, y, w, h, r, strength=1.0, dy=14):
    for i in range(12):
        e = i * 2.2; rrect(ctx, x - e, y - e + dy, w + 2 * e, h + 2 * e, r + e)
        ctx.set_source_rgba(0, 0, 0, 0.024 * strength); ctx.fill()
def glow_rr(ctx, x, y, w, h, r, col, a=1.0, n=8, step=3):
    for i in range(n, 0, -1):
        e = i * step; rrect(ctx, x - e, y - e, w + 2 * e, h + 2 * e, r + e)
        ctx.set_source_rgba(*col, a * 0.05); ctx.fill()
def circle(ctx, x, y, r, col, a=1.0):
    ctx.new_path(); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgba(*col[:3], a); ctx.fill()
def push(ctx): ctx.push_group()
def pop(ctx, alpha):
    ctx.pop_group_to_source(); ctx.paint_with_alpha(clamp(alpha))
def scale_at(ctx, cx, cy_, s):
    ctx.translate(cx, cy_); ctx.scale(s, s); ctx.translate(-cx, -cy_)
def grad_h(x0, x1, c0, c1):
    g = cairo.LinearGradient(x0, 0, x1, 0); g.add_color_stop_rgb(0, *c0); g.add_color_stop_rgb(1, *c1); return g

def check_path(ctx, cx, cy_, s, col, a=1.0, lw=3, p=1.0):
    pts = [(cx - s * 0.32, cy_ + s * 0.02), (cx - s * 0.08, cy_ + s * 0.26), (cx + s * 0.36, cy_ - s * 0.24)]
    l1 = math.dist(pts[0], pts[1]); l2 = math.dist(pts[1], pts[2]); L = (l1 + l2) * p
    ctx.new_path(); ctx.move_to(*pts[0])
    if L <= l1:
        f = L / l1; ctx.line_to(lerp(pts[0][0], pts[1][0], f), lerp(pts[0][1], pts[1][1], f))
    else:
        ctx.line_to(*pts[1]); f = (L - l1) / l2
        ctx.line_to(lerp(pts[1][0], pts[2][0], f), lerp(pts[1][1], pts[2][1], f))
    ctx.set_source_rgba(*col, a); ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
def x_path(ctx, cx, cy_, s, col, a=1.0, lw=3):
    ctx.new_path(); ctx.move_to(cx - s, cy_ - s); ctx.line_to(cx + s, cy_ + s)
    ctx.move_to(cx + s, cy_ - s); ctx.line_to(cx - s, cy_ + s)
    ctx.set_source_rgba(*col, a); ctx.set_line_width(lw); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()

# ------------------------------------------------------------------ icons (glyphs centered at cx,cy with size s)
def icon(ctx, kind, cx, cy_, s, col=WHITE, a=1.0):
    ctx.save(); ctx.new_path()
    ctx.set_source_rgba(*col, a); lw = max(2.0, s * 0.08); ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if kind == 'user':
        ctx.arc(cx, cy_ - s * 0.17, s * 0.2, 0, 2 * math.pi); ctx.fill()
        ctx.save(); ctx.translate(cx, cy_ + s * 0.4); ctx.scale(s * 0.38, s * 0.34)
        ctx.arc(0, 0, 1, math.pi, 2 * math.pi); ctx.restore(); ctx.close_path(); ctx.fill()
    elif kind == 'users':
        ctx.restore(); icon(ctx, 'user', cx + s * 0.2, cy_ - s * 0.06, s * 0.75, col, a * 0.7)
        icon(ctx, 'user', cx - s * 0.12, cy_ + s * 0.04, s * 0.85, col, a); return
    elif kind == 'attacker':
        ctx.save(); ctx.translate(cx, cy_ + s * 0.42); ctx.scale(s * 0.42, s * 0.36)
        ctx.arc(0, 0, 1, math.pi, 2 * math.pi); ctx.restore(); ctx.close_path(); ctx.fill()
        ctx.move_to(cx - s * 0.3, cy_ + s * 0.02); ctx.curve_to(cx - s * 0.34, cy_ - s * 0.5, cx + s * 0.34, cy_ - s * 0.5, cx + s * 0.3, cy_ + s * 0.02)
        ctx.close_path(); ctx.fill()
        ctx.set_source_rgba(0.06, 0.06, 0.12, a); rrect(ctx, cx - s * 0.2, cy_ - s * 0.2, s * 0.4, s * 0.12, s * 0.05); ctx.fill()
    elif kind == 'pc':
        rrect(ctx, cx - s * 0.4, cy_ - s * 0.32, s * 0.8, s * 0.52, s * 0.06); ctx.stroke()
        ctx.move_to(cx, cy_ + s * 0.2); ctx.line_to(cx, cy_ + s * 0.34); ctx.move_to(cx - s * 0.2, cy_ + s * 0.36); ctx.line_to(cx + s * 0.2, cy_ + s * 0.36); ctx.stroke()
    elif kind in ('server', 'dc'):
        off = s * 0.06 if kind == 'dc' else 0
        for i in range(3):
            y = cy_ - s * 0.36 + i * s * 0.26 + off
            rrect(ctx, cx - s * 0.34, y, s * 0.68, s * 0.2, s * 0.05); ctx.stroke()
            ctx.arc(cx + s * 0.2, y + s * 0.1, s * 0.035, 0, 2 * math.pi); ctx.fill()
        if kind == 'dc':
            ctx.move_to(cx - s * 0.2, cy_ - s * 0.42); ctx.line_to(cx - s * 0.2, cy_ - s * 0.6); ctx.line_to(cx - s * 0.1, cy_ - s * 0.5)
            ctx.line_to(cx, cy_ - s * 0.62); ctx.line_to(cx + s * 0.1, cy_ - s * 0.5); ctx.line_to(cx + s * 0.2, cy_ - s * 0.6)
            ctx.line_to(cx + s * 0.2, cy_ - s * 0.42); ctx.close_path(); ctx.fill()
    elif kind == 'crown':
        ctx.move_to(cx - s * 0.38, cy_ + s * 0.25); ctx.line_to(cx - s * 0.42, cy_ - s * 0.25); ctx.line_to(cx - s * 0.18, cy_ - s * 0.02)
        ctx.line_to(cx, cy_ - s * 0.36); ctx.line_to(cx + s * 0.18, cy_ - s * 0.02); ctx.line_to(cx + s * 0.42, cy_ - s * 0.25)
        ctx.line_to(cx + s * 0.38, cy_ + s * 0.25); ctx.close_path(); ctx.fill()
    elif kind in ('doc', 'gpo', 'cert'):
        x, y, w, h = cx - s * 0.28, cy_ - s * 0.38, s * 0.56, s * 0.76
        ctx.move_to(x, y); ctx.line_to(x + w * 0.7, y); ctx.line_to(x + w, y + w * 0.3); ctx.line_to(x + w, y + h); ctx.line_to(x, y + h); ctx.close_path(); ctx.stroke()
        for i in range(3):
            ctx.move_to(x + w * 0.2, y + h * (0.35 + i * 0.17)); ctx.line_to(x + w * (0.8 if i < 2 else 0.5), y + h * (0.35 + i * 0.17))
        ctx.stroke()
        if kind == 'gpo':
            ctx.arc(x + w, y + h, s * 0.17, 0, 2 * math.pi); ctx.fill()
            ctx.set_source_rgba(0.1, 0.1, 0.2, a); ctx.arc(x + w, y + h, s * 0.07, 0, 2 * math.pi); ctx.fill()
        if kind == 'cert':
            ctx.arc(x + w, y + h * 0.82, s * 0.15, 0, 2 * math.pi); ctx.fill()
            ctx.move_to(x + w - s * 0.08, y + h * 0.9); ctx.line_to(x + w - s * 0.12, y + h + s * 0.12)
            ctx.move_to(x + w + s * 0.08, y + h * 0.9); ctx.line_to(x + w + s * 0.12, y + h + s * 0.12); ctx.stroke()
    elif kind == 'key':
        ctx.arc(cx - s * 0.18, cy_, s * 0.17, 0, 2 * math.pi); ctx.stroke()
        ctx.move_to(cx - s * 0.01, cy_); ctx.line_to(cx + s * 0.4, cy_); ctx.move_to(cx + s * 0.3, cy_); ctx.line_to(cx + s * 0.3, cy_ + s * 0.14)
        ctx.move_to(cx + s * 0.18, cy_); ctx.line_to(cx + s * 0.18, cy_ + s * 0.12); ctx.stroke()
    elif kind == 'lock':
        rrect(ctx, cx - s * 0.3, cy_ - s * 0.05, s * 0.6, s * 0.44, s * 0.07); ctx.fill()
        ctx.arc(cx, cy_ - s * 0.08, s * 0.2, math.pi, 2 * math.pi); ctx.stroke()
    elif kind == 'shield':
        ctx.move_to(cx, cy_ - s * 0.42); ctx.curve_to(cx + s * 0.2, cy_ - s * 0.3, cx + s * 0.36, cy_ - s * 0.32, cx + s * 0.36, cy_ - s * 0.3)
        ctx.curve_to(cx + s * 0.36, cy_ + s * 0.1, cx + s * 0.2, cy_ + s * 0.3, cx, cy_ + s * 0.42)
        ctx.curve_to(cx - s * 0.2, cy_ + s * 0.3, cx - s * 0.36, cy_ + s * 0.1, cx - s * 0.36, cy_ - s * 0.3)
        ctx.curve_to(cx - s * 0.36, cy_ - s * 0.32, cx - s * 0.2, cy_ - s * 0.3, cx, cy_ - s * 0.42); ctx.close_path(); ctx.stroke()
        ctx.restore(); check_path(ctx, cx, cy_, s * 0.45, col, a, lw); return
    elif kind == 'ticket':
        x, y, w, h = cx - s * 0.42, cy_ - s * 0.24, s * 0.84, s * 0.48
        ctx.move_to(x, y); ctx.line_to(x + w, y); ctx.line_to(x + w, y + h * 0.35)
        ctx.arc_negative(x + w, y + h / 2, h * 0.15, -math.pi / 2, math.pi / 2); ctx.line_to(x + w, y + h); ctx.line_to(x, y + h)
        ctx.line_to(x, y + h * 0.65); ctx.arc_negative(x, y + h / 2, h * 0.15, math.pi / 2, -math.pi / 2); ctx.close_path(); ctx.stroke()
        ctx.set_dash([s * 0.05, s * 0.05]); ctx.move_to(cx + s * 0.12, y + s * 0.06); ctx.line_to(cx + s * 0.12, y + h - s * 0.06); ctx.stroke(); ctx.set_dash([])
    elif kind in ('folder', 'ou'):
        ctx.move_to(cx - s * 0.4, cy_ - s * 0.28); ctx.line_to(cx - s * 0.1, cy_ - s * 0.28); ctx.line_to(cx, cy_ - s * 0.18)
        ctx.line_to(cx + s * 0.4, cy_ - s * 0.18); ctx.line_to(cx + s * 0.4, cy_ + s * 0.3); ctx.line_to(cx - s * 0.4, cy_ + s * 0.3); ctx.close_path(); ctx.fill()
    elif kind == 'domain':
        ctx.move_to(cx, cy_ - s * 0.14); ctx.line_to(cx, cy_)
        ctx.move_to(cx - s * 0.28, cy_ + s * 0.14); ctx.line_to(cx - s * 0.28, cy_); ctx.line_to(cx + s * 0.28, cy_); ctx.line_to(cx + s * 0.28, cy_ + s * 0.14); ctx.stroke()
        for (px, py) in [(cx, cy_ - s * 0.26), (cx - s * 0.28, cy_ + s * 0.26), (cx + s * 0.28, cy_ + s * 0.26)]:
            rrect(ctx, px - s * 0.14, py - s * 0.12, s * 0.28, s * 0.24, s * 0.04); ctx.fill()
    elif kind == 'siem':
        for i, hh in enumerate([0.3, 0.55, 0.4, 0.7]):
            rrect(ctx, cx - s * 0.36 + i * s * 0.19, cy_ + s * 0.34 - s * hh, s * 0.13, s * hh, s * 0.03); ctx.fill()
    elif kind == 'eye':
        ctx.move_to(cx - s * 0.42, cy_); ctx.curve_to(cx - s * 0.2, cy_ - s * 0.3, cx + s * 0.2, cy_ - s * 0.3, cx + s * 0.42, cy_)
        ctx.curve_to(cx + s * 0.2, cy_ + s * 0.3, cx - s * 0.2, cy_ + s * 0.3, cx - s * 0.42, cy_); ctx.close_path(); ctx.stroke()
        ctx.arc(cx, cy_, s * 0.12, 0, 2 * math.pi); ctx.fill()
    elif kind == 'clock':
        ctx.arc(cx, cy_, s * 0.36, 0, 2 * math.pi); ctx.stroke()
        ctx.move_to(cx, cy_ - s * 0.22); ctx.line_to(cx, cy_); ctx.line_to(cx + s * 0.16, cy_ + s * 0.1); ctx.stroke()
    elif kind == 'bolt':
        ctx.move_to(cx + s * 0.08, cy_ - s * 0.42); ctx.line_to(cx - s * 0.24, cy_ + s * 0.06); ctx.line_to(cx - s * 0.02, cy_ + s * 0.06)
        ctx.line_to(cx - s * 0.1, cy_ + s * 0.42); ctx.line_to(cx + s * 0.24, cy_ - s * 0.08); ctx.line_to(cx + s * 0.02, cy_ - s * 0.08); ctx.close_path(); ctx.fill()
    elif kind == 'cloud':
        ctx.arc(cx - s * 0.15, cy_ + s * 0.05, s * 0.18, 0, 2 * math.pi); ctx.fill()
        ctx.arc(cx + s * 0.08, cy_ - s * 0.06, s * 0.24, 0, 2 * math.pi); ctx.fill()
        rrect(ctx, cx - s * 0.36, cy_ + s * 0.02, s * 0.72, s * 0.22, s * 0.11); ctx.fill()
    elif kind == 'warn':
        ctx.move_to(cx, cy_ - s * 0.38); ctx.line_to(cx + s * 0.4, cy_ + s * 0.32); ctx.line_to(cx - s * 0.4, cy_ + s * 0.32); ctx.close_path(); ctx.stroke()
        ctx.move_to(cx, cy_ - s * 0.1); ctx.line_to(cx, cy_ + s * 0.1); ctx.stroke(); ctx.arc(cx, cy_ + s * 0.21, s * 0.03, 0, 6.3); ctx.fill()
    elif kind == 'check':
        ctx.restore(); check_path(ctx, cx, cy_, s * 0.8, col, a, lw * 1.3); return
    elif kind == 'x':
        ctx.restore(); x_path(ctx, cx, cy_, s * 0.26, col, a, lw * 1.3); return
    elif kind == 'search':
        ctx.arc(cx - s * 0.06, cy_ - s * 0.06, s * 0.24, 0, 2 * math.pi); ctx.stroke()
        ctx.set_line_width(lw * 1.4); ctx.move_to(cx + s * 0.12, cy_ + s * 0.12); ctx.line_to(cx + s * 0.34, cy_ + s * 0.34); ctx.stroke()
    elif kind == 'terminal':
        rrect(ctx, cx - s * 0.4, cy_ - s * 0.3, s * 0.8, s * 0.6, s * 0.08); ctx.stroke()
        ctx.move_to(cx - s * 0.22, cy_ - s * 0.1); ctx.line_to(cx - s * 0.08, cy_); ctx.line_to(cx - s * 0.22, cy_ + s * 0.1)
        ctx.move_to(cx, cy_ + s * 0.12); ctx.line_to(cx + s * 0.2, cy_ + s * 0.12); ctx.stroke()
    elif kind == 'hash':
        ctx.restore(); text(ctx, "#", cx, cy_, s * 0.7, col, a, MONO, 800, 'c', 'm'); return
    elif kind == 'graph':
        pts = [(cx - s * 0.3, cy_ + s * 0.25), (cx, cy_ - s * 0.3), (cx + s * 0.32, cy_ + s * 0.18), (cx - s * 0.05, cy_ + s * 0.05)]
        for (i, j) in [(0, 1), (1, 2), (0, 3), (3, 2), (1, 3)]:
            ctx.move_to(*pts[i]); ctx.line_to(*pts[j])
        ctx.stroke()
        for p in pts: ctx.arc(p[0], p[1], s * 0.09, 0, 6.3); ctx.fill()
    elif kind == 'scissors':
        ctx.arc(cx - s * 0.2, cy_ + s * 0.22, s * 0.11, 0, 6.3); ctx.stroke()
        ctx.arc(cx + s * 0.2, cy_ + s * 0.22, s * 0.11, 0, 6.3); ctx.stroke()
        ctx.move_to(cx - s * 0.12, cy_ + s * 0.13); ctx.line_to(cx + s * 0.2, cy_ - s * 0.36)
        ctx.move_to(cx + s * 0.12, cy_ + s * 0.13); ctx.line_to(cx - s * 0.2, cy_ - s * 0.36); ctx.stroke()
    elif kind == 'layers':
        for i in range(3):
            y = cy_ - s * 0.22 + i * s * 0.2
            ctx.move_to(cx, y - s * 0.12); ctx.line_to(cx + s * 0.38, y); ctx.line_to(cx, y + s * 0.12); ctx.line_to(cx - s * 0.38, y); ctx.close_path()
            ctx.stroke()
    elif kind == 'bug':
        ctx.save(); ctx.translate(cx, cy_ + s * 0.05); ctx.scale(s * 0.22, s * 0.3); ctx.arc(0, 0, 1, 0, 6.3); ctx.restore(); ctx.fill()
        ctx.arc(cx, cy_ - s * 0.3, s * 0.12, 0, 6.3); ctx.fill()
        for sgn in (-1, 1):
            for k in (-0.12, 0.05, 0.22):
                ctx.move_to(cx + sgn * s * 0.2, cy_ + s * k); ctx.line_to(cx + sgn * s * 0.38, cy_ + s * (k - 0.06))
        ctx.stroke()
    elif kind == 'gear':
        for i in range(8):
            ang = i * math.pi / 4
            ctx.move_to(cx + math.cos(ang) * s * 0.26, cy_ + math.sin(ang) * s * 0.26)
            ctx.line_to(cx + math.cos(ang) * s * 0.4, cy_ + math.sin(ang) * s * 0.4)
        ctx.set_line_width(lw * 1.8); ctx.stroke(); ctx.set_line_width(lw)
        ctx.arc(cx, cy_, s * 0.27, 0, 6.3); ctx.fill()
        ctx.set_source_rgba(0.1, 0.1, 0.2, a); ctx.arc(cx, cy_, s * 0.1, 0, 6.3); ctx.fill()
    elif kind.startswith('txt:'):
        ctx.restore(); text(ctx, kind[4:], cx, cy_, s * 0.5, col, a, HEAD, 800, 'c', 'm'); return
    ctx.restore()

# ------------------------------------------------------------------ background
_rng = random.Random(7)
PARTS = [(_rng.uniform(0, W), _rng.uniform(0, H), _rng.uniform(1.5, 4.0), _rng.uniform(15, 45),
          _rng.uniform(0, 6.28), _rng.choice([CYAN, VIOLET, PINK, WHITE])) for _ in range(55)]

def draw_bg(ctx, t, accent):
    g = cairo.LinearGradient(0, 0, W * 0.4, H)
    g.add_color_stop_rgb(0, *hx('0A0F2C')); g.add_color_stop_rgb(1, *hx('190F3D'))
    ctx.set_source(g); ctx.paint()
    for (bx, by, r, col, ph) in [(220, 380, 520, VIOLET, 0.0), (900, 900, 560, CYAN, 2.0), (300, 1600, 600, accent, 4.0), (850, 1750, 420, VIOLET, 1.0)]:
        x = bx + 90 * math.sin(t * 0.25 + ph); y = by + 70 * math.cos(t * 0.2 + ph * 1.3)
        rg = cairo.RadialGradient(x, y, 0, x, y, r)
        rg.add_color_stop_rgba(0, *col, 0.2); rg.add_color_stop_rgba(1, *col, 0)
        ctx.set_source(rg); ctx.paint()
    ctx.set_source_rgba(1, 1, 1, 0.04)
    for gx in range(27, W, 54):
        for gy in range(27, H, 54):
            ctx.rectangle(gx - 1.2, gy - 1.2, 2.4, 2.4)
    ctx.fill()
    for (px, py, r, sp, ph, col) in PARTS:
        y = (py - sp * t) % (H + 40) - 20; x = px + 14 * math.sin(t * 0.8 + ph)
        circle(ctx, x, y, r, col, 0.22 + 0.2 * math.sin(t * 2 + ph))

# ------------------------------------------------------------------ chip
def chip(ctx, cx, cy_, label, col, a, sc=1.0, size=24, icn=None, txtcol=WHITE):
    if a <= 0: return
    w, h = tsize(ctx, label, size, HEAD, 700, markup=True)
    pw, ph = w + 40 + (34 if icn else 0), h + 18
    push(ctx); ctx.save(); scale_at(ctx, cx, cy_, sc)
    x, y = cx - pw / 2, cy_ - ph / 2
    shadow(ctx, x, y, pw, ph, ph / 2, 0.8, 6)
    fill_rr(ctx, x, y, pw, ph, ph / 2, col)
    tx = x + 20
    if icn:
        icon(ctx, icn, tx + 13, cy_, 30, txtcol, 1); tx += 34
    text(ctx, label, tx, cy_, size, txtcol, 1, HEAD, 700, valign='m', markup=True)
    ctx.restore(); pop(ctx, a)

# ================================================================== COMPONENTS
# All component times are relative to scene start (ts). Each draw fn gets (ctx, c, lt) with lt = t - scene_start.

def node_draw(ctx, n, lt):
    s = eback(prog(lt, n['t'], n['t'] + .45))
    if s <= 0: return
    a = clamp(prog(lt, n['t'], n['t'] + .2)) * n.get('_fade', 1)
    x, y, r, col = n['x'], n['y'], n.get('r', 56), n.get('col', CYAN)
    push(ctx); ctx.save(); scale_at(ctx, x, y, s)
    glow_rr(ctx, x - r, y - r, 2 * r, 2 * r, r, col, 1, 7, 4)
    g = cairo.LinearGradient(x - r, y - r, x + r, y + r)
    g.add_color_stop_rgb(0, *mix(col, WHITE, 0.15)); g.add_color_stop_rgb(1, *darker(col, 0.55))
    circle(ctx, x, y, r, (0, 0, 0)); ctx.new_path(); ctx.arc(x, y, r, 0, 6.3); ctx.set_source(g); ctx.fill()
    ctx.new_path(); ctx.arc(x, y, r - 1, 0, 6.3); ctx.set_source_rgba(1, 1, 1, 0.3); ctx.set_line_width(2); ctx.stroke()
    icon(ctx, n.get('icon', 'user'), x, y + (r * 0.05 if n.get('icon') == 'dc' else 0), r * 1.15, WHITE, 1)
    ctx.restore()
    lab = n.get('label')
    if lab:
        pos = n.get('lp', 'b'); size = n.get('ls', 26)
        lw_, lh_ = tsize(ctx, lab, size, HEAD, 700, markup=True)
        sub = n.get('sub')
        sw, sh = (tsize(ctx, sub, 21, HEAD, 500, markup=True) if sub else (0, 0))
        bw, bh = max(lw_, sw) + 24, lh_ + (sh + 2 if sub else 0) + 12
        if pos == 'b': bx, by = x - bw / 2, y + r + 10
        elif pos == 't': bx, by = x - bw / 2, y - r - 10 - bh
        elif pos == 'r': bx, by = x + r + 12, y - bh / 2
        else: bx, by = x - r - 12 - bw, y - bh / 2
        fill_rr(ctx, bx, by, bw, bh, 12, NAVY, 0.78)
        text(ctx, lab, bx + bw / 2, by + 6, size, WHITE, 1, HEAD, 700, 'c', markup=True)
        if sub: text(ctx, sub, bx + bw / 2, by + 6 + lh_ + 2, 21, MUTED, 1, HEAD, 500, 'c', markup=True)
    pop(ctx, a)

def edge_geom(g, e):
    A = g['_n'][e['a']]; B = g['_n'][e['b']]
    ax, ay, bx, by = A['x'], A['y'], B['x'], B['y']
    ra, rb = A.get('r', 56) + 8, B.get('r', 56) + 12
    d = math.dist((ax, ay), (bx, by)) or 1
    ux, uy = (bx - ax) / d, (by - ay) / d
    p0 = (ax + ux * ra, ay + uy * ra); p2 = (bx - ux * rb, by - uy * rb)
    c = e.get('curve', 0)
    mx_, my_ = (p0[0] + p2[0]) / 2 - uy * c, (p0[1] + p2[1]) / 2 + ux * c
    return p0, (mx_, my_), p2

def qpt(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
            (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])

def edge_draw(ctx, g, e, lt):
    f = eio(prog(lt, e['t'], e['t'] + e.get('dur', 0.45)))
    if f <= 0: return
    p0, p1, p2 = edge_geom(g, e)
    col = e.get('col', WHITE)
    cut = e.get('cut')
    ca = 1.0
    if cut is not None and lt >= cut:
        col = mix(col, RED, eout(prog(lt, cut, cut + .3))); ca = lerp(1, 0.25, eout(prog(lt, cut + .2, cut + .6)))
    alpha = e.get('alpha', 0.85) * ca
    N = 40; pts = [qpt(p0, p1, p2, f * i / N) for i in range(N + 1)]
    ctx.new_path(); ctx.move_to(*pts[0])
    for p in pts[1:]: ctx.line_to(*p)
    ctx.set_source_rgba(*col, alpha); ctx.set_line_width(e.get('w', 4))
    if e.get('dashed') or (cut is not None and lt >= cut + .3): ctx.set_dash([14, 10], -lt * 30 if e.get('flow') else 0)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke(); ctx.set_dash([])
    if e.get('arrow', True) and f > 0.05:
        ex, ey = pts[-1]; px, py = pts[-3]
        ang = math.atan2(ey - py, ex - px); s = 16
        ctx.new_path(); ctx.move_to(ex + math.cos(ang) * 4, ey + math.sin(ang) * 4)
        ctx.line_to(ex - math.cos(ang - .45) * s, ey - math.sin(ang - .45) * s)
        ctx.line_to(ex - math.cos(ang + .45) * s, ey - math.sin(ang + .45) * s); ctx.close_path()
        ctx.set_source_rgba(*col, alpha); ctx.fill()
    if e.get('flow') and f >= 1:
        for k in range(3):
            u = ((lt * 0.6 + k / 3) % 1)
            px, py = qpt(p0, p1, p2, u); circle(ctx, px, py, 6, col, alpha * math.sin(math.pi * u))
    lab = e.get('label')
    if lab and f > 0.6:
        la = eout(prog(lt, e['t'] + .3, e['t'] + .6)) * ca
        mx_, my_ = qpt(p0, p1, p2, e.get('lpos', 0.5))
        mx_ += e.get('ldx', 0); my_ += e.get('ldy', 0)
        lw_, lh_ = tsize(ctx, lab, e.get('ls', 22), HEAD, 700, markup=True)
        push(ctx)
        fill_rr(ctx, mx_ - lw_ / 2 - 14, my_ - lh_ / 2 - 6, lw_ + 28, lh_ + 12, (lh_ + 12) / 2, darker(col, 0.35))
        stroke_rr(ctx, mx_ - lw_ / 2 - 14, my_ - lh_ / 2 - 6, lw_ + 28, lh_ + 12, (lh_ + 12) / 2, col, 1, 2)
        text(ctx, lab, mx_, my_, e.get('ls', 22), WHITE, 1, HEAD, 700, 'c', 'm', markup=True)
        pop(ctx, la)
    if cut is not None and lt >= cut:
        s = eback(prog(lt, cut, cut + .35)); mx_, my_ = qpt(p0, p1, p2, 0.5)
        if e.get('label'): mx_ += 0; my_ += 0
        ctx.save(); scale_at(ctx, mx_, my_, s)
        circle(ctx, mx_, my_, 26, RED); x_path(ctx, mx_, my_, 9, WHITE, 1, 4.5); ctx.restore()

def packet_draw(ctx, g, p, lt):
    if not (p['t0'] - .05 <= lt <= p['t1'] + p.get('hold', 0.35)): return
    e = dict(a=p['a'], b=p['b'], curve=p.get('curve', 0))
    p0, p1, p2 = edge_geom(g, e)
    u = eio(prog(lt, p['t0'], p['t1']))
    a = win(lt, p['t0'] - .05, p['t1'] + p.get('hold', 0.35), .15, .3)
    col = p.get('col', YELLOW)
    for k in range(1, 8):
        uu = max(0, u - k * 0.03)
        if uu <= 0 or u >= 1: continue
        px, py = qpt(p0, p1, p2, uu); circle(ctx, px, py, 9 - k, col, a * (0.5 - k * 0.06))
    x, y = qpt(p0, p1, p2, u)
    x += p.get('dx', 0); y += p.get('dy', 0)
    chip(ctx, x, y, p['label'], darker(col, 0.8) if p.get('dark', True) else col, a, 1.0, p.get('size', 24), p.get('icon'))

def graph_draw(ctx, c, lt):
    if '_n' not in c: c['_n'] = {n['id']: n for n in c['nodes']}
    for z in c.get('zones', []):
        za = eout(prog(lt, z['t'], z['t'] + .4))
        if za <= 0: continue
        col = z.get('col', CYAN)
        push(ctx)
        fill_rr(ctx, z['x'], z['y'], z['w'], z['h'], 26, col, 0.08)
        stroke_rr(ctx, z['x'], z['y'], z['w'], z['h'], 26, col, 0.7, 2.5, [12, 8])
        text(ctx, z['label'], z['x'] + 24, z['y'] + 16, z.get('ls', 26), col, 1, HEAD, 800, markup=True)
        if z.get('sub'): text(ctx, z['sub'], z['x'] + z['w'] - 22, z['y'] + 20, 22, MUTED, 1, HEAD, 500, 'r', markup=True)
        pop(ctx, za)
    for e in c.get('edges', []): edge_draw(ctx, c, e, lt)
    for hl in c.get('highlights', []):
        n = c['_n'][hl['node']]
        ha = win(lt, hl['t0'], hl['t1'], .25, .3)
        if ha <= 0: continue
        r = n.get('r', 56); col = hl.get('col', YELLOW)
        pp = ((lt - hl['t0']) % 1.0)
        ctx.new_path(); ctx.arc(n['x'], n['y'], r + 8 + 30 * pp, 0, 6.3)
        ctx.set_source_rgba(*col, ha * 0.8 * (1 - pp)); ctx.set_line_width(5); ctx.stroke()
        ctx.new_path(); ctx.arc(n['x'], n['y'], r + 8, 0, 6.3); ctx.set_source_rgba(*col, ha); ctx.set_line_width(4); ctx.stroke()
    for n in c['nodes']: node_draw(ctx, n, lt)
    for b in c.get('badges', []):
        n = c['_n'][b['node']]
        s = eback(prog(lt, b['t'], b['t'] + .35))
        if s <= 0: continue
        r = n.get('r', 56); bx, by = n['x'] + r * 0.72, n['y'] - r * 0.72
        col = {'x': RED, 'check': GREEN, 'warn': YELLOW, 'key': YELLOW, 'crown': YELLOW}[b['kind']]
        ctx.save(); scale_at(ctx, bx, by, s)
        circle(ctx, bx, by, 24, darker(col, 0.25)); circle(ctx, bx, by, 21, col)
        gl = {'x': 'x', 'check': 'check', 'warn': 'txt:!', 'key': 'key', 'crown': 'crown'}[b['kind']]
        icon(ctx, gl, bx, by, 30 if gl != 'txt:!' else 52, NAVY if col == YELLOW else WHITE, 1)
        ctx.restore()
    for p in c.get('packets', []): packet_draw(ctx, c, p, lt)
    for ch in c.get('chips', []): chip_comp(ctx, ch, lt)

def chip_comp(ctx, c, lt):
    a = win(lt, c['t'], c.get('t1', 999), .2, .3)
    if a <= 0: return
    chip(ctx, c['x'], c['y'], c['text'], c.get('col', VIOLET), a, eback(prog(lt, c['t'], c['t'] + .4)), c.get('size', 26), c.get('icon'),
         c.get('txtcol', WHITE))

def cards_draw(ctx, c, lt):
    y = c.get('y', 480); hh = c.get('h', 150); gap = c.get('gap', 20); x0, w = c.get('x', 60), c.get('w', 960)
    tsz, dsz = c.get('ts', 34), c.get('ds', 26)
    for i, it in enumerate(c['items']):
        p = prog(lt, it['t'], it['t'] + .45)
        if p <= 0: y += hh + gap; continue
        a = eout(p); dx = 70 * (1 - eout(p))
        col = it.get('col', CYAN)
        push(ctx); ctx.save(); ctx.translate(dx, 0)
        hl = it.get('hl')
        if hl and lt >= hl:
            glow_rr(ctx, x0, y, w, hh, 28, col, eout(prog(lt, hl, hl + .3)), 7, 4)
        fill_rr(ctx, x0, y, w, hh, 28, WHITE, 0.08 if not (hl and lt >= hl) else 0.13)
        stroke_rr(ctx, x0, y, w, hh, 28, col, 0.55, 2)
        ir = min(46, hh * 0.32)
        icx = x0 + 30 + ir
        g = cairo.LinearGradient(icx - ir, y + hh / 2 - ir, icx + ir, y + hh / 2 + ir)
        g.add_color_stop_rgb(0, *col); g.add_color_stop_rgb(1, *darker(col, 0.5))
        ctx.new_path(); ctx.arc(icx, y + hh / 2, ir, 0, 6.3); ctx.set_source(g); ctx.fill()
        icon(ctx, it.get('icon', 'check'), icx, y + hh / 2, ir * 1.25, WHITE, 1)
        tx = icx + ir + 26; tw = w - (tx - x0) - (70 if 'state' in it else 26)
        th = tsize(ctx, it['title'], tsz, HEAD, 800, markup=True, width=tw)[1]
        dh = tsize(ctx, it.get('desc', ''), dsz, HEAD, 500, markup=True, width=tw)[1] if it.get('desc') else 0
        ty = y + (hh - th - (dh + 6 if dh else 0)) / 2
        text(ctx, it['title'], tx, ty, tsz, WHITE, 1, HEAD, 800, width=tw, markup=True)
        if dh: text(ctx, it['desc'], tx, ty + th + 6, dsz, MUTED, 1, HEAD, 500, width=tw, markup=True)
        if 'state' in it:
            st, stt = it['state']
            s = eback(prog(lt, stt, stt + .35))
            if s > 0:
                bx, by = x0 + w - 44, y + hh / 2
                scol = {'check': GREEN, 'x': RED, 'warn': YELLOW}[st]
                ctx.save(); scale_at(ctx, bx, by, s); circle(ctx, bx, by, 24, scol)
                icon(ctx, {'check': 'check', 'x': 'x', 'warn': 'txt:!'}[st], bx, by, 34 if st != 'warn' else 54, NAVY if st == 'warn' else WHITE, 1)
                ctx.restore()
        ctx.restore(); pop(ctx, a)
        y += hh + gap

def term_draw(ctx, c, lt):
    x, y, w, h = c.get('x', 60), c.get('y', 480), c.get('w', 960), c.get('h', 900)
    p = prog(lt, c.get('t', 0), c.get('t', 0) + .45)
    if p <= 0: return
    push(ctx); ctx.save(); scale_at(ctx, x + w / 2, y + h / 2, lerp(.9, 1, eback(p)))
    shadow(ctx, x, y, w, h, 20, 1.6)
    fill_rr(ctx, x, y, w, h, 20, hx('0C1222'))
    stroke_rr(ctx, x, y, w, h, 20, hx('334155'), 1, 1.5)
    ctx.save(); rrect(ctx, x, y, w, 58, 20); ctx.clip(); ctx.rectangle(x, y, w, 58); ctx.set_source_rgb(*hx('1E293B')); ctx.fill(); ctx.restore()
    for i, col in enumerate([hx('F87171'), hx('FBBF24'), hx('34D399')]): circle(ctx, x + 32 + i * 30, y + 29, 9, col)
    fill_rr(ctx, x + 140, y + 10, 330, 48, 12, hx('0C1222'))
    icon(ctx, 'terminal', x + 172, y + 34, 30, hx('60A5FA'))
    text(ctx, c.get('title', 'Windows PowerShell'), x + 198, y + 34, 22, WHITE, 1, UI, 600, valign='m')
    ctx.save(); ctx.rectangle(x, y + 60, w, h - 66); ctx.clip()
    size = c.get('size', 25); lh = size * 1.45
    tw = w - 60
    blocks = []
    for (t0, kind, s) in c['lines']:
        if lt < t0: break
        if kind == 'cmd':
            n = len(s); cps = c.get('cps', 34)
            k = min(n, int((lt - t0) * cps) + 1)
            shown = s[:k]; typing = k < n
            mark = f'<span foreground="#FCD34D">PS C:\\&gt;</span> ' + esc(shown)
            blocks.append((mark, WHITE, typing, None))
        else:
            col = {'out': hx('E2E8F0'), 'warn': hx('FCD34D'), 'bad': hx('FCA5A5'), 'good': hx('6EE7B7'),
                   'note': hx('64748B'), 'head': hx('93C5FD')}[kind]
            blocks.append((esc(s), col, False, kind))
    heights = [tsize(ctx, b[0], size, MONO, 500, markup=True, width=tw)[1] + 6 for b in blocks]
    total = sum(heights) + 24
    oy = max(0, total - (h - 90))
    cy_ = y + 82 - oy
    for (b, hh) in zip(blocks, heights):
        mark, col, typing, kind = b
        if kind in ('warn', 'bad'):
            fill_rr(ctx, x + 18, cy_ - 4, w - 36, hh + 2, 8, col, 0.12)
        text(ctx, mark, x + 30, cy_, size, col, 1, MONO, 600 if kind == 'head' else 500, width=tw, markup=True)
        if typing or (b is blocks[-1] and mark.startswith('<span') and (lt * 2) % 1 < .5):
            L = layout(ctx, mark, size, MONO, 500, tw, markup=True)
            ln = L.get_line_count() - 1
            line = L.get_line_readonly(ln); ink, logical = line.get_pixel_extents()
            ctx.rectangle(x + 30 + logical.width + 4, cy_ + ln * (hh - 6) / max(1, L.get_line_count()) + 4, 13, size)
            ctx.set_source_rgba(*WHITE, .85); ctx.fill()
        cy_ += hh
    ctx.restore()
    ctx.restore(); pop(ctx, eout(p))

def esc(s): return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def events_draw(ctx, c, lt):
    x, y, w = c.get('x', 60), c.get('y', 480), c.get('w', 960)
    rh = c.get('rh', 112); h = 120 + rh * len(c['rows']) + 10
    p = prog(lt, c.get('t', 0), c.get('t', 0) + .45)
    if p <= 0: return
    push(ctx); ctx.save(); scale_at(ctx, x + w / 2, y + h / 2, lerp(.9, 1, eback(p)))
    shadow(ctx, x, y, w, h, 18, 1.5)
    fill_rr(ctx, x, y, w, h, 18, hx('F3F3F3'))
    icon(ctx, 'eye', x + 40, y + 30, 34, hx('0067C0'))
    text(ctx, c.get('title', 'Visor de eventos  ›  Seguridad'), x + 70, y + 30, 23, hx('1B1B1B'), 1, UI, 400, valign='m')
    ctx.rectangle(x, y + 60, w, 52); ctx.set_source_rgb(*hx('E8E8E8')); ctx.fill()
    text(ctx, "Id. evento", x + 30, y + 86, 22, hx('5F5F5F'), 1, UI, 600, valign='m')
    text(ctx, "Descripción", x + 230, y + 86, 22, hx('5F5F5F'), 1, UI, 600, valign='m')
    ry = y + 116
    for i, row in enumerate(c['rows']):
        t0, eid, desc, lvl = row[:4]
        ra = eout(prog(lt, t0, t0 + .35))
        if ra > 0:
            hl = [hh for hh in c.get('highlights', []) if hh[0] == i]
            push(ctx)
            fill_rr(ctx, x + 10, ry + 4, w - 20, rh - 8, 10, WHITE)
            if hl:
                ha = win(lt, hl[0][1], hl[0][2], .25, .3)
                if ha > 0:
                    hcol = hl[0][3] if len(hl[0]) > 3 else RED
                    pp = 0.6 + 0.4 * math.sin(lt * 7)
                    fill_rr(ctx, x + 10, ry + 4, w - 20, rh - 8, 10, hcol, 0.18 * ha)
                    stroke_rr(ctx, x + 10, ry + 4, w - 20, rh - 8, 10, hcol, ha * pp, 4)
            lc = {'info': hx('0067C0'), 'warn': hx('D97706'), 'crit': hx('DC2626'), 'ok': hx('059669')}[lvl]
            circle(ctx, x + 44, ry + rh / 2, 17, lc)
            icon(ctx, {'info': 'txt:i', 'warn': 'txt:!', 'crit': 'txt:!', 'ok': 'check'}[lvl], x + 44, ry + rh / 2, 40 if lvl != 'ok' else 26, WHITE, 1)
            text(ctx, eid, x + 76, ry + rh / 2, 34, hx('111827'), 1, MONO, 800, valign='m')
            text(ctx, desc, x + 230, ry + rh / 2, 26, hx('1F2937'), 1, UI, 500, valign='m', width=w - 260, markup=True)
            pop(ctx, ra)
        ry += rh
    ctx.restore(); pop(ctx, eout(p))

def compare_draw(ctx, c, lt):
    y = c.get('y', 480); cw = 465; ih = c.get('ih', 96)
    for k, (lab, col, items, icn) in enumerate([(c['left'][0], c['left'][1], c['left'][2], c['left'][3] if len(c['left']) > 3 else 'x'),
                                                (c['right'][0], c['right'][1], c['right'][2], c['right'][3] if len(c['right']) > 3 else 'check')]):
        x = 60 + k * (cw + 30)
        ha = eback(prog(lt, c.get('t', 0) + k * .15, c.get('t', 0) + k * .15 + .4))
        if ha > 0:
            push(ctx); ctx.save(); scale_at(ctx, x + cw / 2, y + 36, ha)
            fill_rr(ctx, x, y, cw, 72, 36, col)
            icon(ctx, icn, x + 46, y + 36, 40, NAVY, 1)
            text(ctx, lab, x + cw / 2 + 16, y + 36, 32, NAVY, 1, HEAD, 800, 'c', 'm')
            ctx.restore(); pop(ctx, clamp(ha))
        yy = y + 96
        for (t0, s) in items:
            p = prog(lt, t0, t0 + .4)
            th = tsize(ctx, s, 27, HEAD, 600, markup=True, width=cw - 90)[1]
            hh = max(ih, th + 36)
            if p > 0:
                push(ctx); ctx.save(); ctx.translate(0, 30 * (1 - eout(p)))
                fill_rr(ctx, x, yy, cw, hh, 22, col, 0.1); stroke_rr(ctx, x, yy, cw, hh, 22, col, 0.5, 2)
                circle(ctx, x + 38, yy + hh / 2, 18, col)
                icon(ctx, icn, x + 38, yy + hh / 2, 26, NAVY, 1)
                text(ctx, s, x + 70, yy + hh / 2, 27, WHITE, 1, HEAD, 600, valign='m', width=cw - 90, markup=True)
                ctx.restore(); pop(ctx, eout(p))
            yy += hh + 16

def big_draw(ctx, c, lt):
    t0 = c.get('t', 0); y = c.get('y', 820); col = c.get('col', CYAN)
    s = eback(prog(lt, t0, t0 + .5))
    if s > 0 and c.get('icon'):
        r = c.get('r', 110)
        ctx.save(); scale_at(ctx, 540, y - r - 60, s)
        glow_rr(ctx, 540 - r, y - 2 * r - 60, 2 * r, 2 * r, r, col, 1, 10, 5)
        g = cairo.LinearGradient(540 - r, y - 2 * r - 60, 540 + r, y - 60)
        g.add_color_stop_rgb(0, *mix(col, WHITE, .2)); g.add_color_stop_rgb(1, *darker(col, .5))
        ctx.new_path(); ctx.arc(540, y - r - 60, r, 0, 6.3); ctx.set_source(g); ctx.fill()
        icon(ctx, c['icon'], 540, y - r - 60, r * 1.15, WHITE)
        ctx.restore()
    ta = eout(prog(lt, t0 + .25, t0 + .7))
    size = c.get('size', 64)
    text(ctx, c['text'], 540, y + 30 * (1 - ta), size, WHITE, ta, HEAD, 800, 'c', width=940, markup=True, spacing=6)
    if c.get('sub'):
        th = tsize(ctx, c['text'], size, HEAD, 800, markup=True, width=940, spacing=6)[1]
        sa = eout(prog(lt, t0 + .7, t0 + 1.1))
        text(ctx, c['sub'], 540, y + th + 30, c.get('ss', 32), MUTED, sa, HEAD, 500, 'c', width=900, markup=True)

def dm_draw(ctx, c, lt):
    y = c.get('y', 1090)
    for k, (lab, col, s, icn) in enumerate([("DETECTA", CYAN, c['detect'], 'eye'), ("MITIGA", GREEN, c['mitigate'], 'shield')]):
        t0 = c['t'] + k * c.get('gap_t', 0.8)
        p = prog(lt, t0, t0 + .45)
        if p <= 0: continue
        yy = y + k * (c.get('h', 140) + 18); hh = c.get('h', 140)
        push(ctx); ctx.save(); ctx.translate(60 * (1 - eout(p)), 0)
        fill_rr(ctx, 60, yy, 960, hh, 26, col, 0.1); stroke_rr(ctx, 60, yy, 960, hh, 26, col, 0.6, 2)
        fill_rr(ctx, 84, yy + 22, 196, 44, 22, col)
        icon(ctx, icn, 112, yy + 44, 30, NAVY)
        text(ctx, lab, 196, yy + 44, 24, NAVY, 1, HEAD, 800, 'c', 'm')
        text(ctx, s, 300, yy + hh / 2, 28, WHITE, 1, HEAD, 600, valign='m', width=690, markup=True)
        ctx.restore(); pop(ctx, eout(p))

def text_comp(ctx, c, lt):
    a = win(lt, c['t'], c.get('t1', 999), .3, .3)
    text(ctx, c['text'], c.get('x', 540), c['y'] + 20 * (1 - eout(prog(lt, c['t'], c['t'] + .3))), c.get('size', 30),
         c.get('col', MUTED), a, HEAD, c.get('weight', 600), c.get('align', 'c'), width=c.get('w', 940), markup=True)

DRAW = {'graph': graph_draw, 'cards': cards_draw, 'term': term_draw, 'events': events_draw,
        'compare': compare_draw, 'big': big_draw, 'dm': dm_draw, 'chip': chip_comp, 'text': text_comp}

# ================================================================== EPISODE RUNTIME
class Episode:
    def __init__(self, spec):
        self.s = spec
        self.T_INTRO = spec.get('intro_dur', 4.3)
        t = self.T_INTRO
        self.starts = []
        for sc in spec['scenes']:
            self.starts.append(t); t += sc['dur']
        self.T_OUT = t
        self.DUR = t + spec.get('outro_dur', 7.0)
        self.accent = LEVELS[spec['level']]

    def scene_at(self, t):
        for i, st in enumerate(self.starts):
            if st <= t < st + self.s['scenes'][i]['dur']: return i
        return None

    # ---------------- header
    def draw_header(self, ctx, t):
        a = win(t, self.T_INTRO, self.T_OUT + 0.3, .5, .5)
        if a <= 0: return
        scs = self.s['scenes']; n = len(scs)
        push(ctx)
        segw = (960 - (n - 1) * 10) / n
        for i, st in enumerate(self.starts):
            x = 60 + i * (segw + 10)
            fill_rr(ctx, x, 205, segw, 10, 5, WHITE, 0.14)
            f = eout(prog(t, st, st + 0.7))
            if f > 0:
                rrect(ctx, x, 205, max(10, segw * f), 10, 5); ctx.set_source(grad_h(x, x + segw, CYAN, VIOLET)); ctx.fill()
        # level badge
        lv = self.s['level']; lw_, _ = tsize(ctx, lv, 24, HEAD, 800)
        fill_rr(ctx, 1020 - lw_ - 44, 238, lw_ + 44, 50, 25, self.accent)
        text(ctx, lv, 1020 - lw_ / 2 - 22, 263, 24, NAVY, 1, HEAD, 800, 'c', 'm')
        i = self.scene_at(min(t, self.T_OUT - 0.001)) or 0
        st = self.starts[i]
        entries = []
        if i > 0: entries.append((i - 1, 1 - eio(prog(t, st, st + .35)), -40 * eio(prog(t, st, st + .35))))
        entries.append((i, eout(prog(t, st + .15, st + .6)), 40 * (1 - eout(prog(t, st + .15, st + .6)))))
        for (k, alpha, dy) in entries:
            if alpha <= 0: continue
            push(ctx)
            label = f"EP. {self.s['ep']}  ·  {k + 1}/{n}"
            w, h = tsize(ctx, label, 24, HEAD, 800)
            fill_rr(ctx, 60, 238 + dy, w + 44, 50, 25, VIOLET, 0.35)
            stroke_rr(ctx, 60, 238 + dy, w + 44, 50, 25, CYAN, 0.8, 2)
            text(ctx, label, 82, 263 + dy, 24, hx('CFFAFE'), 1, HEAD, 800, valign='m')
            title = scs[k]['title']
            size = fit(ctx, title, 72, 960)
            tw, th = text(ctx, title, 58, 305 + dy + (72 - size) * 0.6, size, WHITE, 1, HEAD, 800)
            uw = tw * eout(prog(t, self.starts[k] + .3, self.starts[k] + .9))
            if uw > 4:
                rrect(ctx, 60, 305 + 92 + dy, uw, 8, 4); ctx.set_source(grad_h(60, 60 + tw, CYAN, PINK)); ctx.fill()
            pop(ctx, alpha)
        pop(ctx, a)

    # ---------------- captions
    def draw_caption(self, ctx, t):
        a = win(t, self.T_INTRO, self.T_OUT + 0.3, .5, .5)
        if a <= 0: return
        push(ctx)
        x, y, w, h = 60, 1450, 960, 190
        fill_rr(ctx, x, y, w, h, 36, WHITE, 0.08); stroke_rr(ctx, x, y, w, h, 36, WHITE, 0.14, 1.5)
        g = cairo.LinearGradient(0, y, 0, y + h); g.add_color_stop_rgb(0, *CYAN); g.add_color_stop_rgb(1, *VIOLET)
        rrect(ctx, x + 18, y + 30, 8, h - 60, 4); ctx.set_source(g); ctx.fill()
        for i, sc in enumerate(self.s['scenes']):
            st = self.starts[i]; caps = sc.get('captions', [])
            for j, (rt, s) in enumerate(caps):
                t0 = st + rt; t1 = st + caps[j + 1][0] if j + 1 < len(caps) else st + sc['dur']
                ca = win(t, t0, t1, .35, .25)
                if ca <= 0: continue
                size = 42
                while size > 28 and tsize(ctx, s, size, HEAD, 700, markup=True, width=860, spacing=4)[1] > 150: size -= 2
                dy = 24 * (1 - eout(prog(t, t0, t0 + .35)))
                text(ctx, s, x + w / 2 + 10, y + h / 2 + dy, size, WHITE, ca, HEAD, 700, 'c', 'm', width=860, markup=True, spacing=4)
        pop(ctx, a)

    # ---------------- intro
    def draw_intro(self, ctx, t):
        D = self.T_INTRO
        if t > D + 0.1: return
        sp = self.s
        out = eio(prog(t, D - 0.55, D))
        push(ctx); ctx.save(); scale_at(ctx, 540, 900, 1 + 0.08 * out)
        a0 = eout(prog(t, 0.2, 0.6))
        lab = f"SERIE  ·  {SERIES}"
        w, _ = tsize(ctx, lab, 24, HEAD, 800)
        push(ctx)
        fill_rr(ctx, 540 - w / 2 - 28, 300, w + 56, 52, 26, WHITE, 0.08); stroke_rr(ctx, 540 - w / 2 - 28, 300, w + 56, 52, 26, CYAN, 0.6, 2)
        text(ctx, lab, 540, 326, 24, hx('CFFAFE'), 1, HEAD, 800, 'c', 'm')
        pop(ctx, a0)
        # emblem
        s = eback(prog(t, 0.3, 0.8)); cx, cy0, r = 540, 560, 115
        if s > 0:
            ctx.save(); scale_at(ctx, cx, cy0, s)
            for k in range(3):
                ang = t * (0.9 + k * 0.35) + k * 2.1; rr = r + 40 + k * 22
                ctx.new_path(); ctx.arc(cx, cy0, rr, 0, 6.3); ctx.set_source_rgba(1, 1, 1, 0.08); ctx.set_line_width(2); ctx.stroke()
                circle(ctx, cx + math.cos(ang) * rr, cy0 + math.sin(ang) * rr, 9, [CYAN, PINK, self.accent][k])
            glow_rr(ctx, cx - r, cy0 - r, 2 * r, 2 * r, r, self.accent, 1, 10, 5)
            g = cairo.LinearGradient(cx - r, cy0 - r, cx + r, cy0 + r)
            g.add_color_stop_rgb(0, *CYAN); g.add_color_stop_rgb(1, *VIOLET)
            ctx.new_path(); ctx.arc(cx, cy0, r, 0, 6.3); ctx.set_source(g); ctx.fill()
            icon(ctx, sp.get('icon', 'domain'), cx, cy0, r * 1.2, WHITE)
            ctx.restore()
        ea = eout(prog(t, 0.6, 1.0))
        text(ctx, f"EPISODIO {sp['ep']}  ·  {sp['level']}", 540, 760 + 20 * (1 - ea), 34, self.accent, ea, HEAD, 800, 'c')
        y = 820
        for li, line in enumerate(sp['title']):
            size = fit(ctx, line, 160, 980, BIG, 400)
            L = layout(ctx, line, size, BIG, 400); tw, th = L.get_pixel_size()
            p = eback(prog(t, 0.8 + li * 0.15, 1.3 + li * 0.15))
            if p > 0:
                ctx.save(); ctx.translate(540 - tw / 2, y + 60 * (1 - p))
                PangoCairo.layout_path(ctx, L)
                g = cairo.LinearGradient(0, 0, tw, th)
                g.add_color_stop_rgb(0, *CYAN); g.add_color_stop_rgb(0.5, *hx('A78BFA')); g.add_color_stop_rgb(1, *PINK)
                ctx.set_source(g); ctx.fill(); ctx.restore()
            y += th * 0.86
        sa = eout(prog(t, 1.5, 2.0))
        text(ctx, sp['subtitle'], 540, y + 30 + 30 * (1 - sa), 46, WHITE, sa, HEAD, 700, 'c', width=940)
        ctx.restore(); pop(ctx, 1 - out)

    # ---------------- outro
    def draw_outro(self, ctx, t):
        b = self.T_OUT
        if t < b: return
        a = 1 - eio(prog(t, self.DUR - 0.6, self.DUR))
        push(ctx)
        ta = eout(prog(t, b + .2, b + .7))
        tw, th = text(ctx, "Resumen", 60, 250 + 40 * (1 - ta), 82, WHITE, ta, HEAD, 800)
        uw = tw * eout(prog(t, b + .5, b + 1.1))
        if uw > 4:
            rrect(ctx, 60, 250 + th + 6, uw, 9, 4.5); ctx.set_source(grad_h(60, 60 + tw, CYAN, PINK)); ctx.fill()
        cols = [CYAN, YELLOW, PINK, GREEN]
        for i, (h1, h2) in enumerate(self.s['recap']):
            p = prog(t, b + 0.6 + i * 0.3, b + 1.1 + i * 0.3)
            if p <= 0: continue
            y = 450 + i * 180
            push(ctx); ctx.save(); ctx.translate(80 * (1 - eout(p)), 0)
            fill_rr(ctx, 60, y, 960, 158, 30, WHITE, 0.08); stroke_rr(ctx, 60, y, 960, 158, 30, cols[i], 0.5, 2)
            g = cairo.LinearGradient(100, y + 35, 190, y + 125); g.add_color_stop_rgb(0, *cols[i]); g.add_color_stop_rgb(1, *VIOLET)
            ctx.new_path(); ctx.arc(146, y + 79, 44, 0, 6.3); ctx.set_source(g); ctx.fill()
            text(ctx, str(i + 1), 146, y + 79, 48, WHITE, 1, HEAD, 800, 'c', 'm')
            text(ctx, h1, 220, y + 34, fit(ctx, h1, 38, 770), WHITE, 1, HEAD, 800, markup=True)
            text(ctx, h2, 220, y + 92, 28, MUTED, 1, HEAD, 500, width=770, ellipsize=True, markup=True)
            ctx.restore(); pop(ctx, eout(p))
        cp = eback(prog(t, b + 2.2, b + 2.7))
        if cp > 0:
            nxt = self.s['next']
            push(ctx); ctx.save(); scale_at(ctx, 540, 1250, cp)
            y0 = 1180
            glow_rr(ctx, 60, y0, 960, 150, 34, VIOLET, 1, 8, 4)
            rrect(ctx, 60, y0, 960, 150, 34); ctx.set_source(grad_h(60, 1020, darker(CYAN, .7), VIOLET)); ctx.fill()
            text(ctx, nxt[0], 110, y0 + 28, 26, hx('E0F2FE'), 1, HEAD, 800)
            text(ctx, nxt[1], 110, y0 + 66, fit(ctx, nxt[1], 44, 780), WHITE, 1, HEAD, 800)
            chevron_x = 960
            ctx.new_path(); ctx.move_to(chevron_x - 12, y0 + 52); ctx.line_to(chevron_x + 14, y0 + 75); ctx.line_to(chevron_x - 12, y0 + 98)
            ctx.set_source_rgb(1, 1, 1); ctx.set_line_width(6); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
            ctx.restore(); pop(ctx, clamp(cp))
        fa = eout(prog(t, b + 3.0, b + 3.5))
        text(ctx, "Guárdalo y sígueme para la serie completa", 540, 1400, 34, MUTED, fa, HEAD, 600, 'c')
        pop(ctx, a)

    # ---------------- scenes
    def draw_scenes(self, ctx, t):
        for i, sc in enumerate(self.s['scenes']):
            st = self.starts[i]; et = st + sc['dur']
            if not (st <= t < et + 0.01): continue
            lt = t - st
            fo = 1 - eio(prog(t, et - 0.35, et))
            push(ctx)
            for c in sc['items']: DRAW[c['type']](ctx, c, lt)
            pop(ctx, fo)

    def render(self, t):
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(surf)
        draw_bg(ctx, t, self.accent)
        self.draw_intro(ctx, t)
        self.draw_header(ctx, t)
        self.draw_scenes(ctx, t)
        self.draw_outro(ctx, t)
        self.draw_caption(ctx, t)
        # footer brand
        fa = win(t, self.T_INTRO, self.T_OUT + .3, .5, .5)
        text(ctx, f"Seguridad en Active Directory  ·  Ep. {self.s['ep']}/{N_EPISODES:02d}", 540, 1668, 22, MUTED, 0.45 * fa, HEAD, 600, 'c')
        fi = 1 - prog(t, 0, 0.4)
        if fi > 0: ctx.set_source_rgba(0, 0, 0, fi); ctx.paint()
        surf.flush()
        return surf

    # ---------------- audio
    def sound_events(self):
        ev = []  # (time, kind, param)
        ev.append((0.3, 'whoosh', 0.7)); ev.append((0.35, 'pop', 0)); ev.append((0.85, 'pop', 1))
        for i, sc in enumerate(self.s['scenes']):
            st = self.starts[i]
            ev.append((st - 0.2, 'whoosh', 0.45))
            for c in sc['items']:
                ty = c['type']
                if ty == 'graph':
                    for n in c['nodes']: ev.append((st + n['t'], 'pop', 0))
                    for e in c.get('edges', []):
                        ev.append((st + e['t'], 'tick', 0))
                        if e.get('cut') is not None: ev.append((st + e['cut'], 'cut', 0))
                    for p in c.get('packets', []): ev.append((st + p['t0'], 'swish', 0))
                    for b in c.get('badges', []): ev.append((st + b['t'], 'bad' if b['kind'] == 'x' else 'ding', 0))
                    for h in c.get('highlights', []): ev.append((st + h['t0'], 'ping', 0))
                    for ch in c.get('chips', []): ev.append((st + ch['t'], 'pop', 1))
                elif ty == 'cards':
                    for it in c['items']:
                        ev.append((st + it['t'], 'pop', 0))
                        if 'state' in it: ev.append((st + it['state'][1], 'ding' if it['state'][0] == 'check' else 'bad', 0))
                        if it.get('hl'): ev.append((st + it['hl'], 'ping', 0))
                elif ty == 'term':
                    ev.append((st + c.get('t', 0), 'pop', 0))
                    for (t0, kind, s) in c['lines']:
                        if kind == 'cmd':
                            cps = c.get('cps', 34)
                            for k in range(len(s)):
                                if k % 2 == 0: ev.append((st + t0 + k / cps, 'type', 0))
                            ev.append((st + t0 + len(s) / cps + 0.05, 'enter', 0))
                        elif kind in ('warn', 'bad'): ev.append((st + t0, 'bad', 0))
                        else: ev.append((st + t0, 'tick', 0))
                elif ty == 'events':
                    ev.append((st + c.get('t', 0), 'pop', 0))
                    for r in c['rows']: ev.append((st + r[0], 'tick', 0))
                    for h in c.get('highlights', []): ev.append((st + h[1], 'ping', 0))
                elif ty == 'compare':
                    ev.append((st + c.get('t', 0), 'pop', 0))
                    for (t0, s) in c['left'][2]: ev.append((st + t0, 'tick', 0))
                    for (t0, s) in c['right'][2]: ev.append((st + t0, 'ding', 0))
                elif ty == 'big':
                    ev.append((st + c.get('t', 0), 'impact', 0))
                elif ty == 'dm':
                    ev.append((st + c['t'], 'pop', 0)); ev.append((st + c['t'] + c.get('gap_t', .8), 'pop', 0))
                elif ty == 'chip':
                    ev.append((st + c['t'], 'pop', 1))
        ev.append((self.T_OUT - 0.2, 'whoosh', 0.6))
        for i in range(4): ev.append((self.T_OUT + 0.6 + i * 0.3, 'pop', 0))
        ev.append((self.T_OUT + 2.2, 'chime', 0))
        return ev

    def build_audio(self, path):
        SR = 44100; DUR = self.DUR
        n = int(DUR * SR) + SR
        L = np.zeros(n); R = np.zeros(n)
        rng = np.random.default_rng(int(self.s['ep']))
        def midi(m): return 440 * 2 ** ((m - 69) / 12)
        def tt(d): return np.arange(int(d * SR)) / SR
        def add(sig, t, gain=1.0, pan=0.0):
            i = int(max(0, t) * SR)
            if i >= n: return
            sig = sig[:n - i]
            L[i:i + len(sig)] += sig * gain * (1 - max(0, pan)); R[i:i + len(sig)] += sig * gain * (1 + min(0, pan))
        tr = self.s.get('transpose', 0)
        beat = 60 / self.s.get('bpm', 96); bar = beat * 4
        prog_ = self.s.get('chords', [[48, 60, 64, 67, 71], [45, 57, 60, 64, 67], [41, 57, 60, 64, 69], [43, 55, 59, 62, 64]])
        for bi in range(int(DUR / bar) + 1):
            t0 = bi * bar; ch = [m + tr for m in prog_[bi % len(prog_)]]
            d = bar + 0.6; x = tt(d)
            env = np.minimum(1, x / 0.35) * np.minimum(1, (d - x) / 0.6)
            for k, m in enumerate(ch):
                f = midi(m)
                sig = (np.sin(2 * np.pi * f * x) + 0.25 * np.sin(4 * np.pi * f * x)) * env * (1 + 0.1 * np.sin(2 * np.pi * 4 * x))
                add(sig, t0, 0.045 if k == 0 else 0.024, pan=(-0.3 if k % 2 else 0.3))
            if bi >= 1:
                arp = [ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[4] + 12, ch[3] + 12, ch[2] + 12, ch[4] + 12, ch[1] + 24]
                for k, m in enumerate(arp):
                    x = tt(0.5); f = midi(m)
                    sig = (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(6 * np.pi * f * x) * np.exp(-x * 20)) * np.exp(-x * 7)
                    add(sig, t0 + k * beat / 2, 0.03, pan=0.4 * math.sin(k))
                for k in range(4):
                    tb = t0 + k * beat
                    if k in (0, 2):
                        x = tt(0.3); f = 45 + 80 * np.exp(-x * 30)
                        add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 14), tb, 0.2)
                    else:
                        x = tt(0.2); nz = np.diff(rng.standard_normal(len(x)), prepend=0); add(nz * np.exp(-x * 30), tb, 0.022)
                    x = tt(0.06); nz = np.diff(rng.standard_normal(len(x)), prepend=0); add(nz * np.exp(-x * 90), tb + beat / 2, 0.016, pan=0.3)
        tl = np.arange(n) / SR
        env = np.clip(tl / 1.5, 0, 1) * np.clip((DUR - tl) / 1.5, 0, 1)
        L *= env; R *= env
        def pop_s(f0=380, f1=1000):
            x = tt(0.12); f = f0 + (f1 - f0) * np.clip(x / 0.09, 0, 1)
            return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * np.clip(x / 0.12, 0, 1))
        def noise_lp(d, k=24):
            nz = rng.standard_normal(int(d * SR)); return np.convolve(nz, np.ones(k) / k, mode='same')
        def whoosh(d):
            x = tt(d); return noise_lp(d)[:len(x)] * np.sin(np.pi * x / d) ** 2 * 3
        def tone(f, d, dec):
            x = tt(d); return (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(4 * np.pi * f * x)) * np.exp(-x * dec)
        for (t, kind, prm) in self.sound_events():
            if kind == 'whoosh': add(whoosh(prm), t, 0.22)
            elif kind == 'swish': add(whoosh(0.35), t, 0.13)
            elif kind == 'pop': add(pop_s(500, 1000) if prm else pop_s(), t, 0.13 if prm else 0.15)
            elif kind == 'tick': add(tone(rng.uniform(1100, 1500), 0.06, 110), t, 0.09)
            elif kind == 'type':
                x = tt(0.03); add(0.6 * np.diff(rng.standard_normal(len(x)), prepend=0) * np.exp(-x * 300)
                                  + 0.5 * np.sin(2 * np.pi * rng.uniform(2500, 3800) * x) * np.exp(-x * 350), t, 0.17, rng.uniform(-.2, .2))
            elif kind == 'enter':
                x = tt(0.15); add(np.sin(2 * np.pi * 170 * x) * np.exp(-x * 35) + 0.3 * rng.standard_normal(len(x)) * np.exp(-x * 120), t, 0.3)
            elif kind == 'ding': add(tone(1568, 0.6, 7) + 0.6 * tone(2093, 0.6, 8), t, 0.1)
            elif kind == 'bad':
                x = tt(0.25); add((np.sign(np.sin(2 * np.pi * 180 * x)) * 0.3 + np.sin(2 * np.pi * 130 * x)) * np.exp(-x * 12), t, 0.1)
            elif kind == 'ping': add(tone(1320, 0.8, 5), t, 0.1)
            elif kind == 'cut':
                x = tt(0.12); add(np.diff(rng.standard_normal(len(x)), prepend=0) * np.exp(-x * 40) + tone(900, 0.12, 30)[:len(x)], t, 0.18)
            elif kind == 'impact':
                x = tt(0.9); f = 40 + 60 * np.exp(-x * 8)
                add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 4) + 0.3 * noise_lp(0.9, 60)[:len(x)] * np.exp(-x * 6), t, 0.3)
            elif kind == 'chime':
                for k, m in enumerate([84, 88, 91, 96]): add(tone(midi(m), 1.6, 3), t + k * 0.09, 0.08)
        st = np.stack([L, R], 1)[:int(DUR * SR)]
        st = np.tanh(st * 1.2) * 0.9
        with wave.open(path, 'wb') as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())

# ================================================================== main
EP = None
def _frame(i): return bytes(EP.render(i / FPS).get_data())

def main():
    global EP
    name = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(here, 'episodios'))
    spec = importlib.import_module(name).SPEC
    EP = Episode(spec)
    outdir = os.path.join(here, 'out'); os.makedirs(outdir, exist_ok=True)
    if '--stills' in sys.argv:
        arg = sys.argv[sys.argv.index('--stills') + 1]
        if arg == 'auto':
            secs = [2.6] + [st + sc['dur'] * 0.82 for st, sc in zip(EP.starts, spec['scenes'])] + [EP.DUR - 1.5]
        else:
            secs = [float(s) for s in arg.split(',')]
        d = os.path.join(outdir, 'stills', name); os.makedirs(d, exist_ok=True)
        for s in secs: EP.render(s).write_to_png(os.path.join(d, f"t{s:05.1f}.png"))
        print(d); return
    import multiprocessing as mp
    audio = os.path.join(outdir, f'{name}.wav'); EP.build_audio(audio)
    out = os.path.join(outdir, f"{name}.mp4")
    nframes = int(EP.DUR * FPS)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-i', audio, '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with mp.get_context('fork').Pool(max(1, os.cpu_count() - 2)) as pool:
        for fb in pool.imap(_frame, range(nframes), chunksize=4): ff.stdin.write(fb)
    ff.stdin.close(); ff.wait(); os.remove(audio)
    print(f"{out}  ({EP.DUR:.1f}s)")

if __name__ == '__main__':
    main()
