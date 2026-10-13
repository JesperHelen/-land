# -*- coding: utf-8 -*-
"""A2 – kartor: täckning 400 m jämfört med täckning med turtäthet, samt svag faktisk tillgänglighet."""
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402
import kartlib as K  # noqa: E402
from a2_tackning import KLASSER  # noqa: E402

P = C.PROCESSED
pkt = pd.read_csv(P / 'a2_delpunkter.csv.gz')
hpl = pd.read_csv(P / 'a2_hallplatser_avgangar.csv', index_col=0)
KLASSFARG = ['#cfcbc2', '#c6dbf5', '#7fb0ec', '#2a78d6', '#0d366b']     # ingen + sekventiell blå skala
SVAGFARG = {1: '#c0392b', 2: '#f28e2b'}


def raster(ax, varde_till_farg, kol, h=C.DELRUTA_M):
    """Ritar delpunkterna som 50 m-raster. Opacitet efter rutans befolkningstäthet (där folk faktiskt bor)."""
    tat = pkt.groupby('ruta_id').bef.transform('sum')
    alpha = 0.30 + 0.70 * np.sqrt(tat / tat.max())
    x0, y0 = pkt.x.min() - h / 2, pkt.y.min() - h / 2
    ix = ((pkt.x - x0) // h).astype(int); iy = ((pkt.y - y0) // h).astype(int)
    img = np.zeros((iy.max() + 1, ix.max() + 1, 4))
    rgba = np.array([to_rgba(varde_till_farg(v)) for v in pkt[kol]])
    rgba[:, 3] = alpha
    img[iy, ix] = rgba
    ax.imshow(img, origin='lower', extent=(x0, x0 + img.shape[1] * h, y0, y0 + img.shape[0] * h),
              interpolation='nearest', zorder=1)


def rutnat(ax):
    D.befolkning().boundary.plot(ax=ax, color='white', linewidth=0.35, alpha=0.8, zorder=2)


def hallplatser(ax, min_avg=1, skala=1.0):
    h = hpl[hpl.avgangar >= min_avg]
    ax.scatter(h.x, h.y, s=(4 + 0.9 * h.avgangar) * skala, facecolor='white', edgecolor='#1f1f1e', lw=0.5, zorder=6)


def fig_jamforelse():
    fig, axs = plt.subplots(1, 2, figsize=(10.6, 8.6))
    K.ny_karta('omrade', ax=axs[0], titel='Täckning: hållplats inom 400 m')
    raster(axs[0], lambda k: '#3987e5' if k > 0 else KLASSFARG[0], 'klass')
    K.ny_karta('omrade', ax=axs[1], titel='Täckning med turtäthet (avgångar per vardag)')
    raster(axs[1], lambda k: KLASSFARG[k], 'klass')
    for ax in axs:
        rutnat(ax); hallplatser(ax, skala=0.45); K.ram(ax)
    K.teckenforklaring(axs[0], [Patch(facecolor='#3987e5', label='Inom 400 m'),
                                Patch(facecolor=KLASSFARG[0], label='Utanför 400 m')], loc='upper left')
    K.teckenforklaring(axs[1], [Patch(facecolor=KLASSFARG[i], label=n) for i, (_, _, n) in enumerate(KLASSER)],
                       titel='Avgångar inom 400 m', loc='upper left')
    fig.tight_layout()
    return K.spara(fig, 'a2_1_tackning_jamforelse.png')


def fig_mariehamn():
    fig, ax = K.ny_karta('tatort', titel='Turtäthet inom 400 m – Mariehamn', figsize=(7.2, 10.2))
    raster(ax, lambda k: KLASSFARG[k], 'klass')
    rutnat(ax)
    K.rita_linjer(ax, alpha=0.35, lw=1.1, zorder=3)
    hallplatser(ax)
    h = [Patch(facecolor=KLASSFARG[i], label=n) for i, (_, _, n) in enumerate(KLASSER)]
    h += [Line2D([], [], marker='o', ls='', markerfacecolor='white', markeredgecolor='#1f1f1e',
                 markersize=math.sqrt(4 + 0.9 * v), label=f'Hållplats, {v} avg/vardag') for v in (10, 40)]
    lg = K.teckenforklaring(ax, h, titel='Avgångar inom 400 m', loc='lower left')
    lg.set_bbox_to_anchor((1.02, 0.0), transform=ax.transAxes)
    K.ram(ax)
    return K.spara(fig, 'a2_2_turtathet_mariehamn.png')


def fig_svag():
    """Svag faktisk tillgänglighet: ytor inom 400 m från hållplats men ≤ 29 avg/vardag, samt otäckta ytor.
    Antal berörda invånare redovisas per 1 km-ruta (befolkningsdatans upplösning)."""
    fig, ax = K.ny_karta('tatort', titel='Svag faktisk tillgänglighet – buss nära men få avgångar', figsize=(7.2, 10.2))
    farg = {0: '#a8a49a', 1: SVAGFARG[1], 2: SVAGFARG[2], 3: (1, 1, 1, 0), 4: (1, 1, 1, 0)}
    raster(ax, lambda k: farg[k], 'klass')
    rutnat(ax)
    K.rita_linjer(ax, alpha=0.6, lw=1.2, zorder=3)
    s = hpl[hpl.avgangar <= 29]
    ax.scatter(s.x, s.y, s=11, marker='s', facecolor='white', edgecolor='#c0392b', lw=0.8, zorder=6)
    q = pkt.groupby('ruta_id').apply(lambda d: pd.Series({'svag': d.loc[d.klass.isin([1, 2]), 'bef'].sum(),
                                                         'otackt': d.loc[d.klass == 0, 'bef'].sum()}))
    b = D.befolkning().set_index('ruta_id')
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    for rid, r in q.iterrows():
        c = b.loc[rid].geometry.centroid
        if not (x0 < c.x < x1 and y0 < c.y < y1):
            continue
        rad = []
        if r.svag >= 30:
            rad.append((f'{int(round(r.svag, -1))}', '#b03a1a'))
        if r.otackt >= 30:
            rad.append((f'{int(round(r.otackt, -1))}', '#5f5b52'))
        for k, (t, f) in enumerate(rad):
            ax.text(c.x, c.y + 120 - 240 * k, t, ha='center', va='center', fontsize=6.6, fontweight='bold', color=f,
                    zorder=8, path_effects=K.HALO)
    h = [Patch(facecolor=SVAGFARG[1], label='1–14 avgångar/vardag inom 400 m'),
         Patch(facecolor=SVAGFARG[2], label='15–29 avgångar/vardag inom 400 m'),
         Patch(facecolor='#a8a49a', label='Ingen hållplats inom 400 m'),
         Line2D([], [], marker='s', ls='', markerfacecolor='white', markeredgecolor='#c0392b', markersize=5,
                label='Hållplats med ≤ 29 avgångar/vardag'),
         Line2D([], [], ls='', marker='$123$', color='#b03a1a', markersize=11, label='Invånare med svag tillgänglighet'),
         Line2D([], [], ls='', marker='$123$', color='#5f5b52', markersize=11, label='Invånare utan hållplats inom 400 m')]
    lg = K.teckenforklaring(ax, h, titel='Per 1 km-ruta (vit ram)', loc='lower left', fontsize=7)
    lg.set_bbox_to_anchor((1.02, 0.0), transform=ax.transAxes)
    K.ram(ax)
    return K.spara(fig, 'a2_3_svag_tillganglighet.png')


if __name__ == '__main__':
    for f in (fig_jamforelse, fig_mariehamn, fig_svag):
        print(f())
