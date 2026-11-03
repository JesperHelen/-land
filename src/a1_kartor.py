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
    a.set_xlim(0, 112); a.set_xlabel('Andel registrerad som turens första hållplats (%)')
    a.set_title('Påstigning vid ändhållplatsen: registrerad på rätt tur?', loc='left', fontsize=10)
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
    b.set_ylabel('Påstigande startsegment / ändhållplats (dygn)')
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
    fore = zon['O_FM_medO'] + zon['O_EM_medO']                 # sommardatan som den är (inkl. linje Ö), utan korrigering
    efter = zon['O_FM_host'] + zon['O_EM_host']
    vmax = max(fore.max(), efter.max())
    fig, axs = plt.subplots(1, 2, figsize=(10.4, 10.2))
    for ax, v, t in [(axs[0], fore, 'Sommardata (som levererad)'), (axs[1], efter, 'Höstdata (tvättad)')]:
        K.ny_karta('tatort', ax=ax, titel=t)
        K.rita_linjer(ax, alpha=0.45, lw=1.3, zorder=3)
        cirklar(ax, v, vmax, 520, etiketter=8)
        cirkel_forklaring(ax, vmax, 520, [10, 4, 1], 'resor/h, FM + EM', loc=(0.06, 0.09))
        K.ram(ax)
    axs[0].text(0.02, 0.975, f'Maj–sep 2026: {fore.sum():.1f} resor/h (FM + EM)'.replace('.', ','),
                transform=axs[0].transAxes, fontsize=7.5, va='top', color=K.TEXT, path_effects=K.HALO)
    axs[1].text(0.02, 0.975, f'Höst 2026: {efter.sum():.1f} resor/h (FM + EM); linje J ur sommardatan'.replace('.', ','),
                transform=axs[1].transAxes, fontsize=7.5, va='top', color='#1c5cab', path_effects=K.HALO)
    fig.tight_layout()
    return K.spara(fig, 'a1_3_pastigande_fore_efter.png')


# ---------------------------------------------------------------- figur 4–5: OD-flöden före/efter (karta)
def urval(L, andel=0.85, maxn=260):
    L = L[L.fran != L.till].sort_values('resor_h', ascending=False)
    cs = L.resor_h.cumsum() / L.resor_h.sum()
    return L.head(min(int(np.searchsorted(cs.to_numpy(), andel)) + 1, maxn)).rename(columns={'resor_h': 'resor'})


def fig_od(per):
    """OD-matrisen som används i kapitel 4 (höstdata, linje J ur sommardatan, utan korrigering): de största
    flödena som bågar med pilar i färdriktningen."""
    kor = pd.read_csv(P / f'a1_od_{per}_korrigerad.csv')
    B = urval(kor)
    vmax = B.resor.max()
    namn = {'FM': 'förmiddag 06–09', 'EM': 'eftermiddag 15–18'}[per]
    fig, ax = plt.subplots(1, 1, figsize=(8.4, 10.4))
    K.ny_karta('tatort', ax=ax, titel=f'OD-matris, {namn} (höst 2026)')
    tot = kor.resor_h.sum()
    odsum = kor.groupby('fran').resor_h.sum().add(kor.groupby('till').resor_h.sum(), fill_value=0)
    span = 14800
    rad = lambda z: span * (0.0025 + 0.012 * math.sqrt(odsum.get(z, 0) / odsum.max()))
    bredd, farg = K.rita_floden(ax, B, POS, vmax, span=span, radie=rad)
    for z, v in odsum.items():
        if z in POS:
            ax.add_patch(plt.Circle(POS[z], rad(z), facecolor='white', edgecolor='#52514e', lw=0.6, zorder=7))
    K.placera_etiketter(ax, [(z, POS[z], rad(z)) for z in odsum.sort_values(ascending=False).index[:12] if z in POS],
                        fontsize=6.6)
    via = (kor.loc[(kor.fran == C.CENTRUM) | (kor.till == C.CENTRUM), 'resor_h'].sum()) / tot
    ax.text(0.03, 0.235, f'{tot:.1f} resor/h · {via:.0%} av resorna till/från {C.CENTRUM}\n'.replace('.', ',', 1)
            + 'Pilarna visar färdriktningen (från ursprung\ntill destination); bågarna böjer åt höger.',
            transform=ax.transAxes, fontsize=7.3, va='bottom', color=K.TEXT, zorder=30, linespacing=1.4,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#d6d5d0', lw=0.6, alpha=0.94))
    K.flodes_forklaring(ax, vmax, bredd, farg, loc=(0.03, 0.06))
    K.skalstock(ax, loc=(0.62, 0.035)); K.norrpil(ax); K.kalla(ax)
    fig.tight_layout()
    return K.spara(fig, f'a1_{4 if per == "FM" else 5}_od_{per}_fore_efter.png')


if __name__ == '__main__':
    for f in (fig_registrering, fig_omfordelning, fig_pastigande, lambda: fig_od('FM'), lambda: fig_od('EM')):
        print(f())
