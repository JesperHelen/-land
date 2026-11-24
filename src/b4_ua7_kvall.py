# -*- coding: utf-8 -*-
"""UA 7 – kvällstrafik efter efterfrågan: Norra i båda riktningarna efter kl. 18 i stället för Västra.

Efter kl. 18 kör två bussar: omlopp 205 (Södra/Norra varannan halvtimme till 21:13) och omlopp 208 (Östra/Västra
18:10–21:07). Norra har flest kvällsresenärer (många stiger på vid Maxinge), Västra få. UA 7 låter omlopp 208 köra
Norra moturs i stället för Västra efter kl. 18 (18:40, 19:40, 20:40), så att Norra går åt båda hållen varje timme på
kvällen (medurs :20, moturs :40). Västras få kvällsresenärer hänvisas till anropsstyrd trafik.

Varianter som prövats (b4_natverk med väntetid = halva turintervallet, kvällens resor = påstigandet efter kl. 18 per
hållplatsområde med destination enligt EM-matrisens fördelning):
  * huvud: alla tre Västra-turer → Norra moturs;
  * varannan Västra-tur → Norra moturs (Västra och Norra moturs varannan timme);
  * varannan Östra-tur, Södra varannan timme, Västra och Östra varannan timme;
  * jämförelse: Västra och Östra anropsstyrda efter kl. 18 (sparar omlopp 208 på kvällen).
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
VARIANTER = [('huvud', 'Alla tre Västra-turer blir Norra moturs', {'N': 60, 'S': 60, 'Ö': 60, 'NM': 60}),
             ('varannan_vastra', 'Varannan Västra-tur blir Norra moturs', {'N': 60, 'S': 60, 'V': 120, 'Ö': 60, 'NM': 120}),
             ('varannan_ostra', 'Varannan Östra-tur blir Norra moturs', {'N': 60, 'S': 60, 'V': 60, 'Ö': 120, 'NM': 120}),
             ('vastra_ostra', 'Västra och Östra varannan timme, Norra moturs varje timme',
              {'N': 60, 'S': 60, 'V': 120, 'Ö': 120, 'NM': 60}),
             ('sodra', 'Södra varannan timme, Norra moturs varannan timme', {'N': 60, 'S': 120, 'V': 60, 'Ö': 60, 'NM': 120})]


def restid():
    """Resenärsminuter per kväll (18–21) för varianterna, jämfört med i dag (alla linjer varje timme)."""
    import data_las as D
    import b4_natverk as N
    zoner = list(pd.read_csv(P / 'a1_restider_min.csv', index_col=0).index)
    mon0 = [m for m in N.monster() if m['linje'] != 'J']
    nm = max([m for m in mon0 if m['linje'] == 'N'], key=lambda m: len(m['turer']))
    rev = {'linje': 'NM', 'stopp': nm['stopp'][::-1], 'zoner': nm['zoner'][::-1], 'akt': nm['akt'][::-1].copy(), 'turer': []}
    T = N.od_matris('EM').reindex(index=zoner, columns=zoner).fillna(0.0)
    p = D.pastigande(); pk = p[p.tid_min >= KVALL].groupby('omrade').P.sum() / 3
    Tk = T.div(T.sum(axis=1).replace(0, np.nan), axis=0).fillna(0).mul(pk.reindex(zoner).fillna(0), axis=0).to_numpy()

    def nat(h):
        return N.Nat([{**m, 'vantan': h[m['linje']] / 2} for m in mon0 + [rev] if h.get(m['linje'])], zoner)
    c0 = nat({'N': 60, 'S': 60, 'V': 60, 'Ö': 60}).restider().to_numpy()
    ut = {}
    for k, namn, h in VARIANTER:
        c1 = nat(h).restider().reindex(index=zoner, columns=zoner).to_numpy()
        with np.errstate(invalid='ignore'):
            d = c1 - c0
        ok = np.isfinite(d)
        ut[k] = {'namn': namn, 'resenarsminuter_kvall': round(float((Tk[ok] * d[ok]).sum() * 3), 0),
                 'resor_kortare_kvall': round(float(Tk[ok & (d < -0.5)].sum() * 3), 1),
                 'resor_langre_kvall': round(float(Tk[ok & (d > 0.5)].sum() * 3), 1),
                 'resor_utan_buss_kvall': round(float(Tk[~np.isfinite(c1) & np.isfinite(c0)].sum() * 3), 1)}
    return ut, round(float(Tk.sum() * 3), 1)


def berakna():
    import data_las as D
    import b4_omlopp as O
    import s01_vagdragning as V
    t = O.turer(); op = O.omlopp_operator(t)
    p = D.pastigande(); pk = p[p.tid_min >= KVALL]
    kv = op[op.avg >= KVALL]
    v_kv = kv[kv.linje == 'V']; o_kv = kv[kv.linje == 'Ö']
    km_n = float(t[t.linje == 'N'].km.median())
    # turtäthet inom 400 m: Norras hållplatser +3 avgångar, Västras −3
    pt = pd.read_csv(P / 'a2_delpunkter.csv.gz'); pt = pt[pt.mariehamn].reset_index(drop=True)
    xy, _ = V.hallplats_xy()
    def nara(stopp):
        s = np.array([xy[k] for k in stopp if k in xy])
        return np.min(np.hypot(pt.x.to_numpy()[:, None] - s[None, :, 0], pt.y.to_numpy()[:, None] - s[None, :, 1]),
                      axis=1) <= C.TACKNING_M
    n_st = list(V.monster_per_linje()['N'][0][0])
    delta = np.zeros(len(pt))
    for m in v_kv.monster:
        delta -= nara(m)
    delta += len(v_kv) * nara(n_st)
    ny = pt.avg_alla + delta
    rt, n_resor = restid()
    # jämförelse: Västra och Östra anropsstyrda
    anrop = kv[kv.linje.isin(('V', 'Ö'))]
    res = {'turer_efter_18': int(len(kv)), 'pastigande_efter_18': round(float(pk.P.sum()), 1),
           'pastigande_efter_18_per_linje': pk.groupby('linje').P.sum().round(1).to_dict(),
           'pastigande_maxinge_norra': round(float(pk[(pk.linje == 'N') & (pk.omrade == 'Maxinge')].P.sum()), 1),
           'andel_av_dagen': round(float(pk.P.sum() / p.P.sum()), 3), 'resor_kvall_modell': n_resor,
           'vastra_turer': [O.hm(a) for a in v_kv.avg], 'ostra_turer': [O.hm(a) for a in o_kv.avg],
           'vastra_resenarer_kvall': round(float(pk[pk.linje == 'V'].P.sum()), 1),
           'fordonskm_vardag': round(len(v_kv) * km_n - float(v_kv.km.sum()), 1),
           'fordonskm_ar': int(round((len(v_kv) * km_n - float(v_kv.km.sum())) * 250, -2)), 'fordon': 5,
           'inv_battre_klass30': int(round(pt.bef[(pt.avg_alla < 30) & (ny >= 30)].sum())),
           'inv_samre_klass30': int(round(pt.bef[(pt.avg_alla >= 30) & (ny < 30)].sum())),
           'restid': rt,
           'anropsstyrt': {'turer': int(len(anrop)), 'resenarer_vardag': round(float(pk[pk.linje.isin(('V', 'Ö'))].P.sum()), 1),
                           'fordonskm_vardag': -round(float(anrop.km.sum()), 1), 'fordonstimmar_vardag': -3.0}}
    json.dump(res, open(P / 'b4_ua7_kvall.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return res, pk


def figur(pk):
    import s01_vagdragning as V
    uts = (105300, 111300, 6681300, 6687400)
    fig, ax = plt.subplots(figsize=(9.4, 9.2))
    K.ny_karta(uts, ax=ax, titel='UA 7 – kvällstrafik efter kl. 18')
    sg = V.segmentgeometri()
    for ln in ('V', 'Ö', 'S', 'N'):
        st = list(V.monster_per_linje()[ln][0][0])
        xy = np.vstack([sg[(a, b)] for a, b in zip(st[:-1], st[1:]) if (a, b) in sg])
        if ln == 'V':
            ax.plot(xy[:, 0], xy[:, 1], color=C.FARG_LINJE[ln], lw=1.8, ls=(0, (2, 2)), alpha=0.8, zorder=3)
            continue
        ax.plot(xy[:, 0], xy[:, 1], color=C.FARG_LINJE[ln], lw=2.8 if ln == 'N' else 2.2, zorder=4 if ln == 'N' else 3.5,
                solid_capstyle='round', path_effects=[K.pe.Stroke(linewidth=4.6, foreground='white'), K.pe.Normal()])
        if ln == 'N':
            L = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])
            for dist in np.arange(300, L[-1], 650):
                j = min(max(int(np.searchsorted(L, dist)), 1), len(xy) - 1)
                a, b = xy[j - 1], xy[j]
                if np.hypot(*(b - a)) < 1:
                    continue
                m = (a + b) / 2; u = (b - a) / np.hypot(*(b - a)) * 45
                ax.annotate('', xy=tuple(m + u), xytext=tuple(m - u), zorder=7,
                            arrowprops=dict(arrowstyle='<|-|>', color='#2b1838', lw=1.1, mutation_scale=10))
    zon = pd.read_csv(P / 'a1_zoner_pastigande.csv', index_col=0)
    v = pk.groupby('omrade').P.sum(); vmax = v.max(); rmax = 260
    for z, val in v.sort_values(ascending=False).items():
        if z in zon.index and val > 0.05:
            ax.add_patch(plt.Circle((zon.at[z, 'x'], zon.at[z, 'y']), max(rmax * math.sqrt(val / vmax), 25),
                                    facecolor='#495057', edgecolor='white', lw=0.6, alpha=0.7, zorder=6))
    st = [z for z in v.sort_values(ascending=False).index if z in zon.index][:6]
    K.placera_etiketter(ax, [(z.replace('Centrum, Nygatan', 'Centrum'), (zon.at[z, 'x'], zon.at[z, 'y']), 80) for z in st],
                        fontsize=6.6)
    hnd = [Line2D([], [], color=C.FARG_LINJE['N'], lw=2.8, label='Norra – båda riktningarna varje timme'),
           Line2D([], [], color=C.FARG_LINJE['S'], lw=2.2, label='Södra – som i dag'),
           Line2D([], [], color=C.FARG_LINJE['Ö'], lw=2.2, label='Östra – som i dag'),
           Line2D([], [], color=C.FARG_LINJE['V'], lw=1.8, ls=(0, (2, 2)), label='Västra – anropsstyrd efter kl. 18'),
           Line2D([], [], marker='o', ls='', markerfacecolor='#495057', markeredgecolor='white', markersize=9,
                  label='Påstigande efter kl. 18')]
    K.teckenforklaring(ax, hnd, loc='lower right')
    K.ram(ax)
    return K.spara(fig, 'b4_23_kvall.png')


if __name__ == '__main__':
    r, pk = berakna()
    print(json.dumps(r, ensure_ascii=False, indent=1))
    print(figur(pk))
