# -*- coding: utf-8 -*-
"""UA 7 – kvällstrafik efter efterfrågan: Västra och Östra som anropsstyrd trafik efter kl. 18.

Efter kl. 18 kör två bussar: omlopp 205 (Södra/Norra varannan halvtimme till 21:13) och omlopp 208 (Västra/Östra
18:10–21:07, sex turer). Västras och Östras kvällsturer har mycket få resenärer. UA 7 låter omlopp 205 köra som i
dag och ersätter de sex turerna på Västra och Östra efter kl. 18 med anropsstyrd trafik (förbeställd taxi eller
minibuss mellan hållplatserna, samma biljett).

  * Påstigande per tur och hållplats efter kl. 18 ur höstdatan (data_las.pastigande).
  * Fordonskm och fordonstimmar: turerna som utgår (b4_omlopp, operatörens omlopp); omlopp 208 slutar 18:07.
  * Turtäthet: avgångar per vardag inom 400 m (unika turer) minus de utgående turerna, invånare i Mariehamn.
Utdata: data/processed/b4_ua7_kvall.json, output/kartor/b4_23_kvall.png
"""
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
KVALL = 18 * 60
UTGAR = ('V', 'Ö')


def berakna():
    import data_las as D
    import b4_omlopp as O
    t = O.turer(); op = O.omlopp_operator(t)
    p = D.pastigande()
    kv = op[op.avg >= KVALL]
    bort = kv[kv.linje.isin(UTGAR)]
    pk = p[(p.tid_min >= KVALL)]
    per_linje = pk.groupby('linje').P.sum().round(1).to_dict()
    berorda = pk[pk.linje.isin(UTGAR)]
    hpl = berorda.groupby(['linje', 'omrade']).P.sum().round(2).sort_values(ascending=False)
    # turtäthet inom 400 m
    pt = pd.read_csv(P / 'a2_delpunkter.csv.gz'); pt = pt[pt.mariehamn].reset_index(drop=True)
    import s01_vagdragning as V
    xy, _ = V.hallplats_xy()
    minus = np.zeros(len(pt))
    for m in bort.monster:
        s = np.array([xy[k] for k in m if k in xy])
        d = np.min(np.hypot(pt.x.to_numpy()[:, None] - s[None, :, 0], pt.y.to_numpy()[:, None] - s[None, :, 1]), axis=1)
        minus += d <= C.TACKNING_M
    ny = pt.avg_alla - minus
    under30 = (pt.avg_alla >= 30) & (ny < 30)
    under15 = (pt.avg_alla >= 15) & (ny < 15)
    res = {'turer_efter_18': int(len(kv)), 'turer_utgar': int(len(bort)),
           'utgar': [f"{l} {O.hm(a)}" for l, a in zip(bort.linje, bort.avg)],
           'pastigande_efter_18': round(float(pk.P.sum()), 1), 'pastigande_efter_18_per_linje': per_linje,
           'andel_av_dagen': round(float(pk.P.sum() / p.P.sum()), 3),
           'berorda_resenarer_vardag': round(float(berorda.P.sum()), 1),
           'berorda_per_tur': round(float(berorda.P.sum() / max(len(bort), 1)), 2),
           'berorda_hallplatser': {f'{l} {o}': float(v) for (l, o), v in hpl.head(8).items()},
           'fordonskm_vardag': -round(float(bort.km.sum()), 1),
           'fordonskm_ar': -int(round(float(bort.km.sum()) * 250, -2)),
           'fordonstimmar_vardag': -round(float((bort.ank.max() - kv[kv.linje.isin(UTGAR)].avg.min()) / 60 + 0.0), 1),
           'omlopp_208_slutar': O.hm(op[(op.omlopp == '208') & (op.avg < KVALL)].ank.max()),
           'inv_under_30_avg': int(round(pt.bef[under30].sum())), 'inv_under_15_avg': int(round(pt.bef[under15].sum())),
           'fordon': 5}
    json.dump(res, open(P / 'b4_ua7_kvall.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return res, pk


def figur(pk):
    uts = (105300, 111300, 6681300, 6687400)
    fig, ax = plt.subplots(figsize=(9.4, 9.2))
    K.ny_karta(uts, ax=ax, titel='UA 7 – kvällstrafik efter kl. 18')
    import s01_vagdragning as V
    sg = V.segmentgeometri()
    for ln, kvar in (('N', True), ('S', True), ('V', False), ('Ö', False)):
        st = list(V.monster_per_linje()[ln][0][0])
        xy = np.vstack([sg[(a, b)] for a, b in zip(st[:-1], st[1:]) if (a, b) in sg])
        if kvar:
            ax.plot(xy[:, 0], xy[:, 1], color=C.FARG_LINJE[ln], lw=2.6, zorder=4, solid_capstyle='round',
                    path_effects=[K.pe.Stroke(linewidth=4.4, foreground='white'), K.pe.Normal()])
        else:
            ax.plot(xy[:, 0], xy[:, 1], color=C.FARG_LINJE[ln], lw=1.8, ls=(0, (2, 2)), alpha=0.8, zorder=3)
    zon = pd.read_csv(P / 'a1_zoner_pastigande.csv', index_col=0)
    v = pk.groupby(['omrade']).P.sum()
    an = pk[pk.linje.isin(UTGAR)].groupby('omrade').P.sum()
    vmax = v.max(); rmax = 260
    for z, val in v.sort_values(ascending=False).items():
        if z not in zon.index or val <= 0.05:
            continue
        r = rmax * math.sqrt(val / vmax)
        ax.add_patch(plt.Circle((zon.at[z, 'x'], zon.at[z, 'y']), max(r, 25), facecolor='#495057', edgecolor='white',
                                lw=0.6, alpha=0.75, zorder=6))
    st = [z for z in v.sort_values(ascending=False).index if z in zon.index][:6]
    K.placera_etiketter(ax, [(z.replace('Centrum, Nygatan', 'Centrum'), (zon.at[z, 'x'], zon.at[z, 'y']), 80) for z in st],
                        fontsize=6.6)
    hnd = [Line2D([], [], color=C.FARG_LINJE['N'], lw=2.6, label='Norra (buss, som i dag)'),
           Line2D([], [], color=C.FARG_LINJE['S'], lw=2.6, label='Södra (buss, som i dag)'),
           Line2D([], [], color=C.FARG_LINJE['V'], lw=1.8, ls=(0, (2, 2)), label='Västra – anropsstyrd efter kl. 18'),
           Line2D([], [], color=C.FARG_LINJE['Ö'], lw=1.8, ls=(0, (2, 2)), label='Östra – anropsstyrd efter kl. 18'),
           Line2D([], [], marker='o', ls='', markerfacecolor='#495057', markeredgecolor='white', markersize=9,
                  label='Påstigande efter kl. 18')]
    K.teckenforklaring(ax, hnd, loc='lower right')
    K.ram(ax)
    return K.spara(fig, 'b4_23_kvall.png')


if __name__ == '__main__':
    r, pk = berakna()
    print(r)
    print(figur(pk))
