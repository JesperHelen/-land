# -*- coding: utf-8 -*-
"""A3 – kartor: nya hållplatslägen (längs dagens linjer och där ändrad linjesträckning krävs) samt
bedömning av befintliga hållplatser (överflödiga)."""
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import kartlib as K  # noqa: E402
from a2_kartor import raster, rutnat, SVAGFARG  # noqa: E402

P = C.PROCESSED
nya = pd.read_csv(P / 'a3_nya_hallplatser.csv')
behov = pd.read_csv(P / 'a3_behov_ny_linjestrackning.csv')
bed = pd.read_csv(P / 'a3_hallplatsbedomning.csv')
hpl = pd.read_csv(P / 'a2_hallplatser_avgangar.csv', index_col=0)
BLA, ORANGE = '#1c5cab', '#e8590c'


def fig_nya():
    fig, ax = K.ny_karta('tatort', titel='Förslag på nya hållplatslägen', figsize=(7.2, 10.2))
    farg = {0: '#a8a49a', 1: SVAGFARG[1], 2: SVAGFARG[2], 3: (1, 1, 1, 0), 4: (1, 1, 1, 0)}
    raster(ax, lambda k: farg[k], 'klass')
    for im in ax.get_images():
        im.set_alpha(0.55)
    rutnat(ax)
    K.rita_linjer(ax, alpha=0.75, lw=1.4, zorder=3)
    s = hpl[hpl.linjer.str.contains('|'.join(C.STADSLINJER))]
    ax.scatter(s.x, s.y, s=9, facecolor='white', edgecolor='#52514e', lw=0.5, zorder=5)
    for r in nya.itertuples():
        ax.add_patch(plt.Circle((r.x, r.y), C.TACKNING_M, facecolor=BLA, alpha=0.10, edgecolor=BLA, lw=0.8, ls='--', zorder=4))
    ax.scatter(nya.x, nya.y, s=150, marker='*', color=BLA, edgecolor='white', lw=0.7, zorder=8)
    for r in behov.itertuples():
        ax.add_patch(plt.Circle((r.x, r.y), C.TACKNING_M, facecolor=ORANGE, alpha=0.10, edgecolor=ORANGE, lw=0.8, ls='--', zorder=4))
    ax.scatter(behov.x, behov.y, s=70, marker='D', color=ORANGE, edgecolor='white', lw=0.7, zorder=8)
    etik = [(f"N{r.nr}: linje {r.linjer}\n+{r.nytta_inv} inv.", (r.x, r.y), 140) for r in nya.itertuples()]
    etik += [(f"{r.narmaste_hpl}\n≈{int(round(r.inv, -1))} inv.", (r.x, r.y), 110) for r in behov.itertuples()]
    hinder = K.punkt_hinder(ax, list(nya.x) + list(behov.x), list(nya.y) + list(behov.y), px=8)
    K.placera_etiketter(ax, etik, fontsize=6.6, undvik=hinder)
    h = [Line2D([], [], marker='*', ls='', color=BLA, markersize=12, label='Nytt läge längs dagens linje (N1–N5)'),
         Line2D([], [], marker='D', ls='', color=ORANGE, markersize=7, label='Nytt läge som kräver ändrad linjesträckning'),
         Patch(facecolor='none', edgecolor='#52514e', ls='--', label='400 m runt nytt läge'),
         Patch(facecolor=SVAGFARG[2], alpha=0.55, label='Svag tillgänglighet i dag (1–29 avg)'),
         Patch(facecolor='#a8a49a', alpha=0.55, label='Ingen hållplats inom 400 m i dag')]
    h += [Line2D([], [], color=C.FARG_LINJE[l], lw=2, label=f'Linje {l}') for l in C.STADSLINJER]
    lg = K.teckenforklaring(ax, h, loc='lower left', fontsize=7)
    lg.set_bbox_to_anchor((1.02, 0.0), transform=ax.transAxes)
    K.ram(ax)
    return K.spara(fig, 'a3_1_nya_hallplatser.png')


def fig_bedomning():
    stil = {'Behålls': dict(s=14, marker='o', facecolor='white', edgecolor='#7a776f', lw=0.6),
            'Undantas (ändhållplats/vändplats)': dict(s=26, marker='s', facecolor='#1f1f1e', edgecolor='white', lw=0.5),
            'Saknar påstigningsdata': dict(s=26, marker='o', facecolor='none', edgecolor='#1c5cab', lw=1.1),
            'Bör prövas': dict(s=42, marker='o', facecolor='#f28e2b', edgecolor='white', lw=0.6),
            'Kandidat för indragning': dict(s=70, marker='X', facecolor='#c0392b', edgecolor='white', lw=0.6)}
    fig, axs = plt.subplots(1, 2, figsize=(12.4, 8.2), gridspec_kw={'width_ratios': [1.0, 1.05]})
    cx0, cx1, cy0, cy1 = UTS_C = (106950, 109350, 6681650, 6684550)
    for ax, uts, t in [(axs[0], 'stad', 'Översikt'), (axs[1], UTS_C, 'Centrum')]:
        K.ny_karta(uts, ax=ax, titel=t)
        K.rita_linjer(ax, alpha=0.55, lw=1.3, zorder=3)
        for k, st in stil.items():
            d = bed[bed.bedomning == k]
            ax.scatter(d.x, d.y, zorder=6 if k != 'Behålls' else 5, **st)
        d = bed[bed.bedomning.isin(['Kandidat för indragning', 'Bör prövas'])].sort_values('bedomning')
        if uts == 'stad':
            ax.add_patch(plt.Rectangle((cx0, cy0), cx1 - cx0, cy1 - cy0, fill=False, edgecolor='#1f1f1e', lw=0.8,
                                       ls='--', zorder=7))
            d = d[~(d.x.between(cx0, cx1) & d.y.between(cy0, cy1))]
        hinder = K.punkt_hinder(ax, bed.x, bed.y, px=5)
        K.placera_etiketter(ax, [(f"{r.omrade} ({r.pastigande_vardag * C.ANTAL_VARDAGAR:.0f})", (r.x, r.y), 35)
                                 for r in d.itertuples()], fontsize=6.4, undvik=hinder)
        K.ram(ax)
    h = [Line2D([], [], ls='', label=k, markersize=8 if k != 'Behålls' else 5, marker=v['marker'],
                markerfacecolor=v['facecolor'], markeredgecolor=v['edgecolor']) for k, v in stil.items()]
    h += [Line2D([], [], ls='', label='(n) = påstigande under 92 vardagar')]
    lg = K.teckenforklaring(axs[1], h, loc='lower left', fontsize=7)
    lg.set_bbox_to_anchor((1.02, 0.0), transform=axs[1].transAxes)
    fig.suptitle('Bedömning av befintliga hållplatser (stadslinjer)', x=0.01, ha='left', fontsize=12, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    return K.spara(fig, 'a3_2_hallplatsbedomning.png')


if __name__ == '__main__':
    for f in (fig_nya, fig_bedomning):
        print(f())
