# -*- coding: utf-8 -*-
"""A1 – kartor och diagram för granskningen och korrigeringen av OD-matrisen (läser data/processed/a1_*)."""
import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import kartlib as K  # noqa: E402

P = C.PROCESSED
zon = pd.read_csv(P / 'a1_zoner_pastigande.csv', index_col=0)
POS = {z: np.array([r.x, r.y]) for z, r in zon.iterrows()}


def cirklar(ax, varden, vmax, rmax, farg='#3987e5', kant='#184f95', etiketter=0, zorder=8):
    """Proportionella cirklar (area ∝ värde). rmax = radie (m) för vmax."""
    for z in varden.sort_values(ascending=False).index:
        v = varden[z]
        if v <= 0 or z not in POS:
            continue
        r = rmax * math.sqrt(v / vmax)
        ax.add_patch(plt.Circle(POS[z], max(r, 18), facecolor=farg, edgecolor=kant, lw=0.6, alpha=0.78, zorder=zorder))
    if etiketter:
        x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
        synliga = [z for z in varden.sort_values(ascending=False).index
                   if z in POS and x0 < POS[z][0] < x1 and y0 < POS[z][1] < y1][:etiketter]
        K.placera_etiketter(ax, [(z, POS[z], rmax * math.sqrt(varden[z] / vmax)) for z in synliga],
                            undvik=[K.ruta_axes(ax, 0.0, 0.0, 0.42, 0.3)])


def cirkel_forklaring(ax, vmax, rmax, varden, enhet, farg='#3987e5', kant='#184f95', loc=(0.05, 0.13)):
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    bx = x0 + loc[0] * (x1 - x0); by = y0 + loc[1] * (y1 - y0)
    ax.text(bx, by + 2.6 * rmax, f'Påstigande ({enhet})', fontsize=7.2, fontweight='bold', color=K.TEXT, zorder=21,
            path_effects=K.HALO)
    for v in varden:
        r = rmax * math.sqrt(v / vmax)
        ax.add_patch(plt.Circle((bx + rmax, by + r), r, facecolor='none', edgecolor=kant, lw=0.7, zorder=21))
        ax.text(bx + 2 * rmax + 60, by + 2 * r, f'{v:g}'.replace('.', ','), fontsize=6.8, va='center', color=K.TEXT,
                zorder=21, path_effects=K.HALO)


# ---------------------------------------------------------------- figur 1: registreringsdiagnos (diagram)
def fig_registrering():
    d1 = pd.read_csv(P / 'a1_d1_registreringsposition.csv')
    R = pd.read_csv(P / 'a1_d2_benchmark_landsbygd.csv')
    o = pd.read_csv(P / 'a1_d2_startsegment_stad.csv')
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4.3), gridspec_kw={'width_ratios': [1.15, 1]})
    d1 = d1.sort_values(['grupp', 'linje'], ascending=[True, True]).reset_index(drop=True)
    y = np.arange(len(d1))[::-1]
    a.barh(y, d1.andel_forsta_hpl * 100, color='#59A14F', height=0.62, label='Registrerad som turens första hållplats')
    a.barh(y, d1.andel_sista_hpl * 100, left=d1.andel_forsta_hpl * 100, color='#E15759', height=0.62,
           label='Registrerad som turens sista hållplats')
    a.set_yticks(y, [f"{'Stadslinje' if g == 'Stadslinje' else 'Landsbygd'} {l}" for g, l in zip(d1.grupp, d1.linje)])
    a.set_xlim(0, 100); a.set_xlabel('Andel av påstigningarna vid ändhållplatsen (%)')
    a.set_title('Registrering av påstigning vid ändhållplatsen', loc='left', fontsize=10)
    a.legend(loc='upper center', bbox_to_anchor=(0.45, -0.13), ncol=2, fontsize=7, frameon=False)
    for sp in ['top', 'right']:
        a.spines[sp].set_visible(False)
    oo = o[(o.k_hpl == 3) & o.period.isin(['FM', 'EM'])]
    lin = ['Landsbygd\n(kontroll)'] + list(C.STADSLINJER)
    x = np.arange(len(lin)); w = 0.36
    for k, (per, f) in enumerate([('FM', '#4E79A7'), ('EM', '#F28E2B')]):
        vals = [float(R[(R.k_hpl == 3) & (R.period == per)].R.iat[0])] + \
               [float(oo[(oo.linje == l) & (oo.period == per)].kvot_obs.iat[0]) if l in set(oo.linje) else 0 for l in C.STADSLINJER]
        b.bar(x + (k - 0.5) * w, vals, width=w, color=f, label=per)
    b.set_xticks(x, [l if '\n' in l else f'Linje {l}' for l in lin])
    b.set_ylabel('Påstigande startsegment / ändhållplats')
    b.set_title('Påstigande på de 3 första hållplatserna efter\nändhållplatsen, i förhållande till ändhållplatsen', loc='left', fontsize=10)
    b.legend(fontsize=7, frameon=False)
    for sp in ['top', 'right']:
        b.spines[sp].set_visible(False)
    fig.tight_layout()
    return K.spara(fig, 'a1_1_registreringsdiagnos.png')


# ---------------------------------------------------------------- figur 2: omfördelning i centrum (karta)
def fig_omfordelning():
    f = pd.read_csv(P / 'a1_centrum_omfordelning.csv')
    tot = f.groupby('till_omrade').resor_h.sum()
    fig, ax = K.ny_karta('centrum', titel='Omfördelning av felregistrerade centrumpåstigningar', figsize=(7, 8.2))
    K.rita_linjer(ax, alpha=0.55, lw=1.6, zorder=3)
    c = POS[C.CENTRUM]
    vmax = tot.max()
    for z, v in tot.sort_values().items():
        ax.annotate('', xy=POS[z], xytext=c, arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=0.8 + 4.5 * v / vmax,
                    mutation_scale=9 + 8 * v / vmax, shrinkA=14, shrinkB=10), zorder=9)
    ax.add_patch(plt.Circle(c, 55, facecolor='white', edgecolor='#c0392b', lw=1.6, zorder=11))
    h = [Line2D([], [], color='#c0392b', lw=2.5, label='Flyttade påstigningar (FM + EM)')]
    h += [Line2D([], [], color=C.FARG_LINJE[l], lw=2, label=f'Linje {l}') for l in C.STADSLINJER]
    lg = K.teckenforklaring(ax, h, loc='lower right')
    lg.set_bbox_to_anchor((0.99, 0.03), transform=ax.transAxes)
    upp = K.placera_etiketter(ax, [(f'{C.CENTRUM}\n−{tot.sum():.2f} resor/h (FM + EM)'.replace('.', ','), c, 60)],
                              fontsize=7.4, farg='#c0392b', fet=True, undvik=[K.ruta_axes(ax, 0.55, 0.02, 1, 0.3)])
    K.placera_etiketter(ax, [(f'{z}\n+{v:.2f} resor/h'.replace('.', ','), POS[z], 30)
                             for z, v in tot.sort_values(ascending=False).items() if v >= 0.02], undvik=upp)
    K.ram(ax)
    return K.spara(fig, 'a1_2_omfordelning_centrum.png')


# ---------------------------------------------------------------- figur 3: påstigande före/efter (karta)
def fig_pastigande():
    fore = zon['O_FM_orig'] + zon['O_EM_orig']
    efter = zon['O_FM_korr'] + zon['O_EM_korr']
    vmax = max(fore.max(), efter.max())
    fig, axs = plt.subplots(1, 2, figsize=(10.4, 10.2))
    for ax, v, t in [(axs[0], fore, 'Ursprungligt underlag'), (axs[1], efter, 'Korrigerat underlag')]:
        K.ny_karta('tatort', ax=ax, titel=t)
        K.rita_linjer(ax, alpha=0.45, lw=1.3, zorder=3)
        cirklar(ax, v, vmax, 520, etiketter=8)
        cirkel_forklaring(ax, vmax, 520, [5, 2, 0.5], 'resor/h, FM + EM', loc=(0.06, 0.09))
        K.ram(ax)
    axs[0].text(0.02, 0.975, 'Linje Ö ingår ej (filterfel)', transform=axs[0].transAxes, fontsize=7.5, va='top',
                color='#c0392b', path_effects=K.HALO)
    axs[1].text(0.02, 0.975, 'Linje Ö ingår, centrumöverskott omfördelat', transform=axs[1].transAxes, fontsize=7.5,
                va='top', color='#1c5cab', path_effects=K.HALO)
    fig.tight_layout()
    return K.spara(fig, 'a1_3_pastigande_fore_efter.png')


# ---------------------------------------------------------------- figur 4–5: OD-flöden före/efter (karta)
def urval(L, andel=0.85, maxn=260):
    L = L[L.fran != L.till].sort_values('resor_h', ascending=False)
    cs = L.resor_h.cumsum() / L.resor_h.sum()
    return L.head(min(int(np.searchsorted(cs.to_numpy(), andel)) + 1, maxn)).rename(columns={'resor_h': 'resor'})


def fig_od(per):
    lev = pd.read_csv(P / f'a1_od_{per}_levererad.csv')
    kor = pd.read_csv(P / f'a1_od_{per}_korrigerad.csv')
    A, B = urval(lev), urval(kor)
    vmax = max(A.resor.max(), B.resor.max())
    namn = {'FM': 'förmiddag 06–09', 'EM': 'eftermiddag 15–18'}[per]
    fig, axs = plt.subplots(1, 2, figsize=(10.4, 10.2))
    for ax, L, full, t in [(axs[0], A, lev, 'Levererad OD-matris'), (axs[1], B, kor, 'Korrigerad OD-matris')]:
        K.ny_karta('tatort', ax=ax, titel=f'{t}, {namn}')
        tot = full.resor_h.sum()
        odsum = full.groupby('fran').resor_h.sum().add(full.groupby('till').resor_h.sum(), fill_value=0)
        span = 14800
        rad = lambda z: span * (0.0025 + 0.012 * math.sqrt(odsum.get(z, 0) / odsum.max()))
        bredd, farg = K.rita_floden(ax, L, POS, vmax, span=span, radie=rad)
        for z, v in odsum.items():
            if z in POS:
                ax.add_patch(plt.Circle(POS[z], rad(z), facecolor='white', edgecolor='#52514e', lw=0.6, zorder=7))
        via = (full.loc[(full.fran == C.CENTRUM) | (full.till == C.CENTRUM), 'resor_h'].sum()) / tot
        ax.text(0.02, 0.975, f'{tot:.1f} resor/h · {via:.0%} av resorna till/från {C.CENTRUM}'.replace('.', ',', 1),
                transform=ax.transAxes, fontsize=7.3, va='top', color=K.TEXT, path_effects=K.HALO, zorder=30)
        K.flodes_forklaring(ax, vmax, bredd, farg, loc=(0.03, 0.06))
        K.skalstock(ax, loc=(0.62, 0.035)); K.norrpil(ax); K.kalla(ax)
    fig.tight_layout()
    return K.spara(fig, f'a1_{4 if per == "FM" else 5}_od_{per}_fore_efter.png')


if __name__ == '__main__':
    for f in (fig_registrering, fig_omfordelning, fig_pastigande, lambda: fig_od('FM'), lambda: fig_od('EM')):
        print(f())
