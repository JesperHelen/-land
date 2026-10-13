# -*- coding: utf-8 -*-
"""Gemensam kartstil för PM:ets kartor (EPSG:3067): land/vatten, linjer, hållplatser, skalstock, norrpil, bågar."""
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.patheffects as pe  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402

VATTEN = '#dde7ec'
LAND = '#f5f3ee'
KUST = '#b3afa4'
TEXT = '#1f1f1e'
TEXT2 = '#52514e'
HALO = [pe.withStroke(linewidth=2.6, foreground='white')]
BLA = LinearSegmentedColormap.from_list('bla', ['#cde2fb', '#86b6ef', '#3987e5', '#256abf', '#184f95', '#0d366b'])

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8.5, 'axes.titlesize': 11,
                     'axes.titleweight': 'bold', 'savefig.facecolor': 'white'})

# Kartutsnitt (xmin, xmax, ymin, ymax) i EPSG:3067
UTSNITT = {
    'omrade': (101600, 115400, 6672400, 6693600),   # hela befolkningsrutnätet (Mariehamn + Jomala)
    'tatort': (105200, 112400, 6672800, 6687600),   # Mariehamn med Järsö/Nåtö i söder
    'stad': (105600, 111400, 6679200, 6687400),     # Mariehamns stad
    'centrum': (107300, 109500, 6681900, 6684600),  # centrum
}


def ny_karta(utsnitt='tatort', figsize=None, titel=None, ax=None):
    x0, x1, y0, y1 = UTSNITT[utsnitt] if isinstance(utsnitt, str) else utsnitt
    if ax is None:
        h = 9.0
        w = figsize[0] if figsize else min(7.4, h * (x1 - x0) / (y1 - y0) + 0.3)
        fig, ax = plt.subplots(figsize=figsize or (w, h))
    ax.set_facecolor(VATTEN)
    D.land().plot(ax=ax, color=LAND, edgecolor=KUST, linewidth=0.45, zorder=0)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal')
    ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel(''); ax.set_ylabel('')
    for sp in ax.spines.values():
        sp.set_edgecolor('#c9c6bd'); sp.set_linewidth(0.8)
    if titel:
        ax.set_title(titel, loc='left', pad=6)
    return ax.figure, ax


def skalstock(ax, langd_m=None, loc=(0.05, 0.035)):
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    langd_m = langd_m or (2000 if (x1 - x0) > 7000 else 1000 if (x1 - x0) > 3000 else 500)
    bx, by = x0 + loc[0] * (x1 - x0), y0 + loc[1] * (y1 - y0)
    h = 0.007 * (y1 - y0)
    for k in range(2):
        ax.add_patch(Rectangle((bx + k * langd_m / 2, by), langd_m / 2, h, facecolor='#1f1f1e' if k == 0 else 'white',
                               edgecolor='#1f1f1e', lw=0.6, zorder=20))
    for v, etik in [(0, '0'), (langd_m, f'{langd_m / 1000:g} km'.replace('.', ','))]:
        ax.text(bx + v, by + 1.8 * h, etik, ha='center', va='bottom', fontsize=7, color=TEXT, zorder=20,
                path_effects=HALO)


def norrpil(ax, loc=(0.94, 0.93)):
    ax.annotate('N', xy=(loc[0], loc[1] + 0.035), xytext=(loc[0], loc[1] - 0.01), xycoords='axes fraction',
                ha='center', va='center', fontsize=9, fontweight='bold', color=TEXT, zorder=20,
                arrowprops=dict(arrowstyle='-|>', color=TEXT, lw=1.1), path_effects=HALO)


def kalla(ax, text=None):
    if text is None:
        import s01_vagdragning as V
        vag = 'Linjernas vägdragning: OSRM, © OpenStreetMap-bidragsgivare.' if V.kalla_text().startswith('Linjernas') \
            else 'Linjerna ritade som raka streck mellan hållplatser.'
        text = f'Underlag: Ålandstrafiken (GTFS, valideringsdata), befolkningsrutor 2024, kust GSHHG.\n{vag}'
    ax.text(0.995, 0.004, text, transform=ax.transAxes, ha='right', va='bottom', fontsize=5.6, color=TEXT2,
            zorder=20, path_effects=HALO)


def ram(ax, **kw):
    skalstock(ax, **kw); norrpil(ax); kalla(ax)


def spara(fig, namn, dpi=200):
    for a in fig.axes:
        if not a.get_xticks().size:
            a.set_xlabel(''); a.set_ylabel('')
    ut = C.KARTOR / namn
    fig.savefig(ut, dpi=dpi, bbox_inches='tight', pad_inches=0.06)
    plt.close(fig)
    return ut


def teckenforklaring(ax, rader, titel=None, loc='upper left', fontsize=7.5):
    """rader: lista av matplotlib-handles med label."""
    lg = ax.legend(handles=rader, title=titel, loc=loc, fontsize=fontsize, title_fontsize=fontsize + 0.5,
                   frameon=True, framealpha=0.94, edgecolor='#d6d5d0', borderpad=0.7, labelspacing=0.6)
    lg.get_frame().set_linewidth(0.6)
    if titel:
        lg.get_title().set_fontweight('bold')
    lg.set_zorder(30)
    return lg


# ------------------------------------------------------------------ linjenät
def linjegeometrier(datum=None):
    """Mittlinje (x, y) per stadslinje för det vanligaste turmönstret – längs gatunätet om vägdragning (OSRM)
    finns i data/processed/vagdragning_segment.gpkg, annars raka streck mellan hållplatserna."""
    import s01_vagdragning as V
    geo = V.segmentgeometri()
    ut = {}
    for ln, kedjor in V.linjekedjor().items():
        k = kedjor[0]
        ut[ln] = np.vstack([geo[s] if i == 0 else geo[s][1:] for i, s in enumerate(k)])
    return {ln: ut[ln] for ln in C.STADSLINJER if ln in ut}


def _m_per_mm(ax):
    ax.figure.canvas.draw_idle()
    bb = ax.get_window_extent()
    h_mm = bb.height / ax.figure.dpi * 25.4
    y0, y1 = ax.get_ylim()
    return (y1 - y0) / max(h_mm, 1e-6)


def rita_linjer(ax, geom=None, alpha=1.0, lw=2.0, etikett=True, zorder=5, forskjut=True):
    """Ritar stadslinjerna längs gatunätet. Där flera linjer delar gata förskjuts de till egna spår
    (spåravstånd anpassat efter kartskalan) så att varje linje syns."""
    import s01_vagdragning as V
    h = []
    if geom is None:
        avst = 0.0
        if forskjut:
            avst = round((lw * 0.3528 + 0.45) * _m_per_mm(ax))   # linjebredd + luft, i meter
        kedjor = V.forskjutna_linjer(avst) if avst > 0 else {
            ln: [np.vstack([V.segmentgeometri()[s] if i == 0 else V.segmentgeometri()[s][1:] for i, s in enumerate(k)])
                 for k in kl] for ln, kl in V.linjekedjor().items()}
    else:
        kedjor = {ln: [xy] for ln, xy in geom.items()}
    for ln in [l for l in C.STADSLINJER if l in kedjor]:
        f = C.FARG_LINJE[ln]
        for i, xy in enumerate(kedjor[ln]):
            line, = ax.plot(xy[:, 0], xy[:, 1], color=f, lw=lw, alpha=alpha, solid_capstyle='round',
                            solid_joinstyle='round', zorder=zorder, label=f'Linje {ln}' if i == 0 else None,
                            path_effects=[pe.Stroke(linewidth=lw + 1.4, foreground='white'), pe.Normal()])
            if i == 0:
                h.append(line)
    return h


# ------------------------------------------------------------------ OD-bågar
def _bage(p0, p2, krok=0.22, n=160):
    d = p2 - p0; L = float(np.hypot(*d))
    p1 = (p0 + p2) / 2 + krok * L * np.array([d[1], -d[0]]) / L       # böjer åt höger i färdriktningen
    t = np.linspace(0, 1, n)[:, None]
    B = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(B, axis=0).T))])
    return B, s


def _langs(B, s, sv):
    return np.column_stack([np.interp(sv, s, B[:, 0]), np.interp(sv, s, B[:, 1])])


def _pil_polygon(B, s, a, b, w, pil_l, pil_b, n=36):
    if b - a <= 0:
        return None
    pil_l = min(pil_l, 0.5 * (b - a)); kropp = b - pil_l
    P = _langs(B, s, np.linspace(a, kropp, n))
    T = np.gradient(P, axis=0); T /= np.maximum(np.hypot(*T.T), 1e-9)[:, None]
    N = np.column_stack([-T[:, 1], T[:, 0]])
    spets = _langs(B, s, [b])[0]
    return np.vstack([P + N * w / 2, P[-1] + N[-1] * pil_b / 2, spets, P[-1] - N[-1] * pil_b / 2,
                      (P - N * w / 2)[::-1]])


def rita_floden(ax, floden, pos, vmax, span=None, radie=None, cmap=BLA, zorder=6):
    """floden: DataFrame(fran, till, resor) ; pos: {zon: np.array([x, y])} ; vmax gemensam skala."""
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    span = span or max(x1 - x0, y1 - y0)
    radie = radie or (lambda z: span * 0.004)
    bredd = lambda v: span * (0.0006 + 0.0095 * v / vmax)
    farg = lambda v: cmap(0.15 + 0.85 * math.sqrt(min(v / vmax, 1.0)))
    for r in floden.sort_values('resor').itertuples(index=False):
        if r.fran not in pos or r.till not in pos or r.fran == r.till:
            continue
        p0, p2 = pos[r.fran], pos[r.till]
        if np.hypot(*(p2 - p0)) < 1:
            continue
        B, s = _bage(p0, p2)
        w = bredd(r.resor)
        poly = _pil_polygon(B, s, radie(r.fran) + span * 0.002, s[-1] - radie(r.till) - span * 0.002, w,
                            max(2.4 * w, span * 0.008), max(2.3 * w, span * 0.006))
        if poly is not None:
            ax.add_patch(Polygon(poly, closed=True, facecolor=farg(r.resor), edgecolor='white', lw=0.4,
                                 alpha=0.93, zorder=zorder))
    return bredd, farg


def flodes_forklaring(ax, vmax, bredd, farg, enhet='resor/h', loc=(0.03, 0.035), varden=None):
    """Teckenförklaring för bågbredd (ritad i dataenheter)."""
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    span = max(x1 - x0, y1 - y0)
    snygga = [m * 10 ** e for e in range(-3, 4) for m in (1, 2, 2.5, 5)]
    topp = max([t for t in snygga if t <= vmax] or [vmax])
    varden = varden or [topp, topp / 2, topp / 10]
    W, H = 0.36, 0.035 + 0.036 * len(varden)
    ax.add_patch(FancyBboxPatch(loc, W, H, boxstyle='round,pad=0,rounding_size=0.01', transform=ax.transAxes,
                                facecolor='white', edgecolor='#d6d5d0', lw=0.6, alpha=0.94, zorder=25))
    ax.text(loc[0] + 0.02, loc[1] + H - 0.02, f'Resor ({enhet})', transform=ax.transAxes, fontsize=7.5,
            fontweight='bold', color=TEXT, va='center', zorder=26)
    for k, v in enumerate(varden):
        fy = loc[1] + H - 0.052 - k * 0.036
        a = np.array([x0 + (loc[0] + 0.02) * (x1 - x0), y0 + fy * (y1 - y0)])
        b = np.array([x0 + (loc[0] + 0.17) * (x1 - x0), y0 + fy * (y1 - y0)])
        w = bredd(v); B = np.vstack([a, b]); s = np.array([0.0, np.hypot(*(b - a))])
        ax.add_patch(Polygon(_pil_polygon(B, s, 0, s[-1], w, max(2.4 * w, span * 0.008), max(2.3 * w, span * 0.006), n=2),
                             closed=True, facecolor=farg(v), edgecolor='white', lw=0.4, zorder=26))
        ax.text(loc[0] + 0.195, fy, f'{v:g}'.replace('.', ','), transform=ax.transAxes, fontsize=7.5, color=TEXT,
                va='center', zorder=26)


# ------------------------------------------------------------------ etiketter utan överlapp
def placera_etiketter(ax, punkter, fontsize=6.8, farg=None, fet=False, undvik=None):
    """punkter: [(text, (x, y), radie_m)] i prioritetsordning. Placerar varje etikett på första lediga plats
    runt punkten (höger, vänster, ovan, under, diagonaler); hoppar över etiketter som inte får plats."""
    fig = ax.figure; fig.canvas.draw(); rend = fig.canvas.get_renderer()
    axbb = ax.get_window_extent(rend)
    upptagna = [tuple(b) for b in (undvik or [])]
    krock = lambda a, b: not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])
    for text, xy, r in punkter:
        cx, cy = ax.transData.transform(xy); rx = ax.transData.transform((xy[0] + r, xy[1]))[0] - cx + 3
        kandidater = [(m * dx, m * dy, ha, va) for m in (1.0, 2.6) for dx, dy, ha, va in
                      [(1, 0, 'left', 'center'), (-1, 0, 'right', 'center'), (0, 1, 'center', 'bottom'),
                       (0, -1, 'center', 'top'), (0.7, 0.7, 'left', 'bottom'), (-0.7, 0.7, 'right', 'bottom'),
                       (0.7, -0.7, 'left', 'top'), (-0.7, -0.7, 'right', 'top')]]
        for dx, dy, ha, va in kandidater:
            pos = ax.transData.inverted().transform((cx + dx * rx, cy + dy * rx))
            t = ax.text(pos[0], pos[1], text, fontsize=fontsize, ha=ha, va=va, color=farg or TEXT, zorder=25,
                        fontweight='bold' if fet else 'normal', path_effects=HALO, clip_on=True)
            bb = t.get_window_extent(rend); b = (bb.x0 - 1, bb.y0 - 1, bb.x1 + 1, bb.y1 + 1)
            if axbb.x0 <= b[0] and b[2] <= axbb.x1 and axbb.y0 <= b[1] and b[3] <= axbb.y1 and \
                    not any(krock(b, u) for u in upptagna):
                upptagna.append(b)
                break
            t.remove()
    return upptagna


def ruta_axes(ax, x0, y0, x1, y1):
    """Bounding box (pixlar) för ett område angivet i axes-koordinater – att undvika vid etikettplacering."""
    (a, b), (c, d) = ax.transAxes.transform([(x0, y0), (x1, y1)])
    return (a, b, c, d)


def punkt_hinder(ax, xs, ys, px=7):
    """Pixelboxar runt punkter – används som hinder vid etikettplacering."""
    ax.figure.canvas.draw()
    ut = []
    for x, y in zip(xs, ys):
        cx, cy = ax.transData.transform((x, y))
        ut.append((cx - px, cy - px, cx + px, cy + px))
    return ut
