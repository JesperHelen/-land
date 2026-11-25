# -*- coding: utf-8 -*-
"""UA 3 – variant: vänd bara Norras norra slinga (beställaren 2026-11-25).

Norra kör som i dag ut från Centrum via Polishuset till Vedhuggsvägen och hem via Sjukhuset – Yrkesgymnasiet. Den norra
slingan körs baklänges: Vedhuggsvägen – Nabben – Lemlandsvägen – Hindersböle – Bolstavägen – Bo-Bil – Michaelsvägen –
Maxinge (söderut, utan vändning) – Hjortronstigen – Uppgårdsvägen – busslänken – Doktorsvägen – Sjukhuset.
Vikingagränd ersätts av Bo-Bil.
  * Väglängd: OSRM (nya delsträckor, Bo-Bil norrut och Maxinge söderut med bearings), dagens segment baklänges, och
    busslänken Doktorsvägen – Uppgårdsvägen baklänges (stängd för bil i OSRM).
  * Åktid: dagens genomsnittshastighet i Norras varv, +0,5 min uppehåll vid Bo-Bil.
  * Restid: OD-matrisen utlagd på restidsnätet (b4_natverk) med Norras mönster ersatt.
Utdata: data/processed/b4_ua3_slinga.json, output/kartor/b4_24_norra_slinga.png
"""
import json
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import kartlib as K  # noqa: E402

P = C.PROCESSED
VG, BB, MX = '9025302000063201', '9025302000003502', '9025302000031201'
VIA = {(BB, MX): [(108110.0, 6687088.0)]}
BEAR = {MX: '180,45', BB: '0,60'}


def monster():
    import s01_vagdragning as V
    H = pd.read_csv(P / 'a2_hallplatser_avgangar.csv', index_col=0, dtype={'stop_id': str})
    mon = list(V.monster_per_linje()['N'][0][0]); nm = [H.loc[x, 'namn'] for x in mon]
    i0, i1 = nm.index('Vedhuggsvägen'), nm.index('Nabben')
    slinga = [x for x in mon[i0 + 1:i1][::-1] if x != VG]
    slinga.insert(slinga.index(MX), BB)
    return mon, mon[:i0 + 1] + [mon[i1]] + slinga + mon[i1 + 1:], H


def geometri(ny):
    """(N,2)-array per delsträcka längs gatunätet."""
    import requests
    import s01_vagdragning as V
    from pyproj import Transformer
    sg = V.segmentgeometri(); xy = V.alla_xy()[0]
    till_ll = Transformer.from_crs(C.CRS_METRISK, C.CRS_WGS84, always_xy=True)
    fran_ll = Transformer.from_crs(C.CRS_WGS84, C.CRS_METRISK, always_xy=True)
    s = requests.Session(); ut = []
    for a, b in zip(ny[:-1], ny[1:]):
        if (a, b) in sg:
            ut.append(sg[(a, b)]); continue
        if (b, a) in V.BUSSLANK or ((b, a) in sg and a not in BEAR and b not in BEAR):
            ut.append(sg[(b, a)][::-1]); continue
        pts = [xy[a]] + VIA.get((a, b), []) + [xy[b]]
        bear = [BEAR.get(a, '')] + [''] * len(VIA.get((a, b), [])) + [BEAR.get(b, '')]
        u = (f'{V.OSRM_URL}/route/v1/driving/' + ';'.join('%.6f,%.6f' % till_ll.transform(*p) for p in pts))
        r = s.get(u, params={'overview': 'full', 'geometries': 'geojson', 'bearings': ';'.join(bear),
                             'continue_straight': 'true'}, timeout=30).json()
        c = np.array(r['routes'][0]['geometry']['coordinates'])
        X, Y = fran_ll.transform(c[:, 0], c[:, 1]); ut.append(np.column_stack([X, Y])); time.sleep(0.4)
    return ut


def berakna():
    import b4_natverk as N
    import s01_vagdragning as V
    import data_las as D
    mon, ny, H = monster()
    sg = V.segmentgeometri()
    g0 = [sg[(a, b)] for a, b in zip(mon[:-1], mon[1:])]
    g1 = geometri(ny)
    L0 = [V.langd(g) for g in g0]; L1 = [V.langd(g) for g in g1]
    mon0 = N.monster(); n0p = max([m for m in mon0 if m['linje'] == 'N'], key=lambda m: len(m['turer']))
    v = sum(L0) / n0p['akt'].sum()
    akt = np.array([l / v + (0.5 if b == BB else 0.0) for l, b in zip(L1, ny[1:])])
    om = D.hallplatsomraden()['omrade']
    zoner = list(pd.read_csv(P / 'a1_restider_min.csv', index_col=0).index)
    mon1 = [m if m is not n0p else {**m, 'stopp': tuple(ny), 'zoner': tuple(om.reindex(ny).fillna('Bo-Bil')),
                                      'akt': akt} for m in mon0]
    fak = N.dagsfaktor(); j = N.jamfor(N.Nat(mon0, zoner), N.Nat(mon1, zoner))
    res = {'hallplatsfoljd': [H.loc[x, 'namn'] for x in ny], 'varv_idag_m': round(sum(L0)), 'varv_ny_m': round(sum(L1)),
           'skillnad_m_per_tur': round(sum(L1) - sum(L0)), 'fordonskm_vardag': round((sum(L1) - sum(L0)) * 22 / 1000, 1),
           'kortid_idag_min': round(float(n0p['akt'].sum()), 1), 'kortid_ny_min': round(float(akt.sum()), 1),
           'resenarsminuter_vardag': round((j['FM']['resenarsminuter_h'] + j['EM']['resenarsminuter_h']) / 2 * fak, 0),
           'resor_kortare_vardag': round((j['FM']['resor_kortare_h'] + j['EM']['resor_kortare_h']) / 2 * fak, 0),
           'resor_langre_vardag': round((j['FM']['resor_langre_h'] + j['EM']['resor_langre_h']) / 2 * fak, 0)}
    json.dump(res, open(P / 'b4_ua3_slinga.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return res, mon, ny, g0, g1, H


def figur(mon, ny, g0, g1, H):
    uts = (107150, 109450, 6684700, 6687350)
    fig, axs = plt.subplots(1, 2, figsize=(11.6, 7.2))
    FN = C.FARG_LINJE['N']
    for ax, titel, delar, stopp in ((axs[0], 'I dag – Norra medurs', g0, mon),
                                    (axs[1], 'Variant – norra slingan baklänges via Bo-Bil', g1, ny)):
        K.ny_karta(uts, ax=ax, titel=titel)
        for d in K.sammanfoga(delar, tol=60):
            ax.plot(d[:, 0], d[:, 1], color=FN, lw=3.2, zorder=5, solid_capstyle='round', solid_joinstyle='round',
                    path_effects=[K.pe.Stroke(linewidth=5.4, foreground='white'), K.pe.Normal()])
            L = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(d, axis=0).T))])
            for dist in np.arange(150, L[-1], 330):
                j = min(max(int(np.searchsorted(L, dist)), 1), len(d) - 1)
                a, b = d[j - 1], d[j]
                if np.hypot(*(b - a)) < 1 or not (uts[0] < b[0] < uts[1] and uts[2] < b[1] < uts[3]):
                    continue
                ax.annotate('', xy=tuple(b), xytext=tuple(a), zorder=6,
                            arrowprops=dict(arrowstyle='-|>', color='#2b1838', lw=0, mutation_scale=14))
        h = H.loc[[x for x in stopp if x in H.index]]
        ax.scatter(h.x, h.y, s=18, facecolor='white', edgecolor='#1f1f1e', lw=0.7, zorder=7)
        namn = ['Maxinge', 'Bo-Bil', 'Vikingagränd', 'Bolstavägen', 'Hindersbölevägen', 'Nabben', 'Sjukhuset',
                'Doktorsvägen 1A', 'Vedhuggsvägen']
        g = h[h.namn.isin(namn)].groupby('namn')[['x', 'y']].mean()
        K.placera_etiketter(ax, [(n, (r.x, r.y), 40) for n, r in g.iterrows()], fontsize=6.6,
                            undvik=K.punkt_hinder(ax, h.x, h.y, px=5))
    K.skalstock(axs[0], langd_m=500, loc=(0.06, 0.035))
    hnd = [Line2D([], [], color=FN, lw=3, label='Norra'),
           Line2D([], [], color='#2b1838', lw=0, marker='$→$', markersize=10, label='Körriktning')]
    K.teckenforklaring(axs[1], hnd, loc='lower right')
    fig.tight_layout()
    return K.spara(fig, 'b4_24_norra_slinga.png')


if __name__ == '__main__':
    r, mon, ny, g0, g1, H = berakna()
    print({k: v for k, v in r.items() if k != 'hallplatsfoljd'})
    print(figur(mon, ny, g0, g1, H))
