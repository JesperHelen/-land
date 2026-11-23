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
    ax.text(bx, by + 2.6 * rmax, enhet, fontsize=7.0, color=K.TEXT, zorder=21, path_effects=K.HALO)
    for v in varden:
        r = rmax * math.sqrt(v / vmax)
        ax.add_patch(plt.Circle((bx + rmax, by + r), r, facecolor='none', edgecolor=kant, lw=0.7, zorder=21))
        ax.text(bx + 2 * rmax + 60, by + 2 * r, f'{v:g}'.replace('.', ','), fontsize=6.6, va='center', color=K.TEXT,
                zorder=21, path_effects=K.HALO)


# ---------------------------------------------------------------- figur 1: registreringsdiagnos (diagram)
def fig_registrering():
    """Vänster: andel av påstigningarna vid ändhållplatsen som registreras på turens första hållplats – sommardatan
    (stads- och landsbygdslinjer) och den tvättade höstdatan. Höger: startsegmentets kvot mot kontrollgruppen."""
    d1 = pd.read_csv(P / 'a1_d1_registreringsposition.csv')
    R = pd.read_csv(P / 'a1_d2_benchmark_landsbygd.csv')
    o = pd.read_csv(P / 'a1_d2_startsegment_stad.csv')
    kh = pd.read_csv(P / 'a1_kontroll_host.csv')
    fig, (a, b) = plt.subplots(1, 2, figsize=(10.6, 4.6), gridspec_kw={'width_ratios': [1.1, 1]})
    d1 = d1.sort_values(['grupp', 'linje']).reset_index(drop=True)
    rad = [(f"Landsbygd {r.linje}", r.andel_forsta_hpl, '#7a776f') for r in d1[d1.grupp != 'Stadslinje'].itertuples()]
    rad += [(f"Linje {r.linje} – sommar", r.andel_forsta_hpl, '#E15759') for r in d1[d1.grupp == 'Stadslinje'].itertuples()]
    rad += [(f"Linje {r.linje} – höst (tvättad)", r.centrum_forsta_hpl_andel, '#59A14F') for r in kh.itertuples()]
    y = np.arange(len(rad))[::-1]
    a.barh(y, [100 * v for _, v, _ in rad], color=[f for _, _, f in rad], height=0.62)
    for yy, (_, v, _) in zip(y, rad):
        a.text(100 * v + 1.5, yy, f'{100 * v:.0f} %', va='center', fontsize=6.6, color=K.TEXT)
    a.set_yticks(y, [n for n, _, _ in rad], fontsize=7.2)
    a.set_xlim(0, 112); a.set_xlabel('Andel (%)')
    a.set_title('Påstigning vid ändhållplatsen registrerad på rätt tur')
    for sp in ['top', 'right']:
        a.spines[sp].set_visible(False)
    oo = o[(o.k_hpl == 3) & (o.period == 'dygn')]
    lin = [l for l in C.STADSLINJER if l in set(kh.linje)]
    x = np.arange(len(lin) + 1); w = 0.38
    rb = float(R[(R.k_hpl == 3) & (R.period == 'dygn')].R.iat[0])
    b.bar(0, rb, width=w, color='#7a776f', label='Kontrollgrupp (landsbygd)')
    b.bar(x[1:] - w / 2, [float(oo[oo.linje == l].kvot_obs.iat[0]) if l in set(oo.linje) else 0 for l in lin], width=w,
          color='#E15759', label='Sommar')
    b.bar(x[1:] + w / 2, [float(kh[kh.linje == l].kvot_dygn.iat[0]) for l in lin], width=w, color='#59A14F',
          label='Höst (tvättad)')
    b.set_xticks(x, ['Landsbygd\n(kontroll)'] + [f'Linje {l}' for l in lin])
    b.set_ylabel('Kvot (dygn)')
    b.set_title('Påstigande på tre första hållplatserna / ändhållplatsen')
    b.legend(fontsize=7, frameon=False)
    for sp in ['top', 'right']:
        b.spines[sp].set_visible(False)
    fig.tight_layout()
    return K.spara(fig, 'a1_1_registreringsdiagnos.png')


# ---------------------------------------------------------------- figur 2: omfördelning i centrum (karta)
def fig_omfordelning():
    f = pd.read_csv(P / 'a1_centrum_omfordelning.csv')
    tot = f.groupby('till_omrade').resor_h.sum()
    fig, ax = K.ny_karta('centrum', titel='Omfördelning av centrumpåstigningar', figsize=(7, 8.2))
    K.rita_linjer(ax, alpha=0.55, lw=1.6, zorder=3)
    c = POS[C.CENTRUM]
    vmax = tot.max()
    for z, v in tot.sort_values().items():
        ax.annotate('', xy=POS[z], xytext=c, arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=0.8 + 4.5 * v / vmax,
                    mutation_scale=9 + 8 * v / vmax, shrinkA=14, shrinkB=10), zorder=9)
    ax.add_patch(plt.Circle(c, 55, facecolor='white', edgecolor='#c0392b', lw=1.6, zorder=11))
    h = [Line2D([], [], color='#c0392b', lw=2.5, label='Flyttade påstigningar')]
    h += [Line2D([], [], color=C.FARG_LINJE[l], lw=2, label=f'Linje {l}') for l in C.STADSLINJER]
    lg = K.teckenforklaring(ax, h, loc='lower right')
    lg.set_bbox_to_anchor((0.99, 0.03), transform=ax.transAxes)
    upp = K.placera_etiketter(ax, [('Centrum', c, 60)], fontsize=7.0, farg='#c0392b',
                              undvik=[K.ruta_axes(ax, 0.6, 0.02, 1, 0.3)])
    K.placera_etiketter(ax, [(z, POS[z], 30) for z, v in tot.sort_values(ascending=False).items() if v >= 0.02],
                        fontsize=6.6, undvik=upp)
    K.ram(ax)
    return K.spara(fig, 'a1_2_omfordelning_centrum.png')


# ---------------------------------------------------------------- figur 3: påstigande före/efter (karta)
def fig_pastigande():
    fore = zon['O_FM_medO'] + zon['O_EM_medO']                 # sommardatan som den är (inkl. linje Ö), utan korrigering
    efter = zon['O_FM_host'] + zon['O_EM_host']
    vmax = max(fore.max(), efter.max())
    fig, axs = plt.subplots(1, 2, figsize=(10.4, 10.2))
    for ax, v, t in [(axs[0], fore, 'Sommardata (som levererad)'), (axs[1], efter, 'Höstdata (tvättad)')]:
        K.ny_karta('tatort', ax=ax, titel=t)
        K.rita_linjer(ax, alpha=0.45, lw=1.3, zorder=3)
        cirklar(ax, v, vmax, 520, etiketter=8)
    cirkel_forklaring(axs[0], vmax, 520, [10, 4, 1], 'Påstigande per timme', loc=(0.06, 0.07))
    K.ram(axs[0])
    fig.tight_layout()
    return K.spara(fig, 'a1_3_pastigande_fore_efter.png')


# ---------------------------------------------------------------- figur 4–5: OD-flöden före/efter (karta)
def urval(L, andel=0.85, maxn=260):
    L = L[L.fran != L.till].sort_values('resor_h', ascending=False)
    cs = L.resor_h.cumsum() / L.resor_h.sum()
    return L.head(min(int(np.searchsorted(cs.to_numpy(), andel)) + 1, maxn)).rename(columns={'resor_h': 'resor'})


OD_BLA = '#2f6fb7'
OD_UTS = (105200, 112400, 6672800, 6687400)


def fig_od():
    """OD-matrisen som används i kapitel 4 (höstdata, linje J ur sommardatan): förmiddag och eftermiddag sida vid
    sida. De största flödena (75 % av resorna) som blå bågar med pilspets vid målet; bredden = resor per timme."""
    od = {per: pd.read_csv(P / f'a1_od_{per}_korrigerad.csv') for per in ('FM', 'EM')}
    vmax = max(urval(d, 0.75).resor.max() for d in od.values())
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 9.6))
    span = OD_UTS[3] - OD_UTS[2]
    for ax, per, titel in [(axs[0], 'FM', 'Förmiddag (FM 06–09)'), (axs[1], 'EM', 'Eftermiddag (EM 15–18)')]:
        K.ny_karta(OD_UTS, ax=ax, titel=titel)
        kor = od[per]
        B = urval(kor, 0.75)
        odsum = kor.groupby('fran').resor_h.sum().add(kor.groupby('till').resor_h.sum(), fill_value=0)
        rad = lambda z: span * 0.0032
        bredd, farg = K.rita_floden(ax, B, POS, vmax, span=span, radie=rad, mittpil=False, fast_farg=OD_BLA,
                                    alpha=0.78)
        zoner = sorted(set(B.fran) | set(B.till))
        ax.scatter([POS[z][0] for z in zoner if z in POS], [POS[z][1] for z in zoner if z in POS], s=7, c='white',
                   edgecolors='#5f5e5a', linewidths=0.5, zorder=8)
        storsta = [z for z in odsum.sort_values(ascending=False).index if z in POS][:7]
        K.placera_etiketter(ax, [(z.replace('Centrum, Nygatan', 'Centrum'), POS[z], rad(z)) for z in storsta],
                            fontsize=6.4, undvik=[K.ruta_axes(ax, 0.0, 0.0, 0.42, 0.16)])
    K.flodes_forklaring(axs[0], vmax, bredd, farg, loc=(0.03, 0.025), titel='Resor per timme', storlek=0.82)
    fig.tight_layout(w_pad=0.8)
    return K.spara(fig, 'a1_4_od_fm_em.png')


if __name__ == '__main__':
    for f in (fig_registrering, fig_omfordelning, fig_pastigande, fig_od):
        print(f())
