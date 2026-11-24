# -*- coding: utf-8 -*-
"""UA 6 – linje Norra i båda riktningarna.

Linje Norra är i dag en enkelriktad slinga (Centrum – Maxinge – Hindersböle – Nabben – Sjukhuset – Centrum), 22 turer
per vardag. Den som åker ut från centrum på morgonen åker direkt, men hemresan går hela varvet runt. UA 6 kör Norra
även i motsatt riktning med samma turtäthet (22 turer moturs), med ett extra fordon.

  * Restid: den korrigerade OD-matrisen utlagd på restidsnätet (b4_natverk), med Norras mönster även baklänges
    (samma åktider per delsträcka). Nätmodellen räknar inte väntetid, så vinsten av den dubblade turtätheten ingår inte.
  * Turtäthet: invånare i Mariehamn inom 400 m från Norras hållplatser får 22 avgångar fler per vardag.
  * Fordon och fordonskm: varvet tar 26 min; med 4 min reglering i centrum ryms 30-minuterstrafik moturs i ett
    fordon (eget omlopp). Fordonskm = Norras varvlängd längs gatunätet (OSRM) × 22 turer.
  * Vid Maxinge finns bara hållplats på västra sidan (södergående). Moturs kommer bussen från Vikingagränd, kör norrut
    till rondellen norr om Maxinge och stannar vid Maxinge på väg söderut, spegelvänt mot i dag.
  * Omlopp: förarna växlar i dag Södra ↔ Norra. Med Norra i båda riktningarna blir det dubbelt så många Norra-turer
    som Södra-turer. A (ett extra fordon): Norra/Södra-gruppen körs av tre bussar i rotationen Norra medurs →
    Södra → Norra moturs, så att föraren byter linje vid varje vändning; Västra/Östra och Järsö som i dag.
    B (dagens fem fordon): varannan Norra-tur körs moturs, så att varje riktning går en gång i timmen.
  * Väntetid (känslighet): halva turintervallet vid första påstigningen (Järsö 60 min, övriga 30 min; i B Norra
    60 min per riktning).
Utdata: data/processed/b4_ua6_norra.json, output/kartor/b4_21_norra_bada_riktningar.png, b4_22_norra_omlopp.png
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from shapely.geometry import LineString

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import kartlib as K  # noqa: E402

P = C.PROCESSED
TURER = 22
REGLERING = 4.0


def berakna():
    import b4_natverk as N
    import s01_vagdragning as V
    zoner = list(pd.read_csv(P / 'a1_restider_min.csv', index_col=0).index)
    mon0 = N.monster(); nat0 = N.Nat(mon0, zoner)
    nm = max([m for m in mon0 if m['linje'] == 'N'], key=lambda m: len(m['turer']))
    rev = {'linje': 'N', 'stopp': nm['stopp'][::-1], 'zoner': nm['zoner'][::-1], 'akt': nm['akt'][::-1].copy(), 'turer': []}
    nat1 = N.Nat(mon0 + [rev], zoner); fak = N.dagsfaktor()
    j = N.jamfor(nat0, nat1)
    c0, c1 = nat0.restider(), nat1.restider()
    exempel = []
    for per in ('FM', 'EM'):
        T = N.od_matris(per).reindex(index=zoner, columns=zoner).fillna(0)
        for a in zoner:
            for b in zoner:
                d = c0.at[a, b] - c1.at[a, b]
                if T.at[a, b] > 0.02 and d > 0.5:
                    exempel.append({'period': per, 'fran': a, 'till': b, 'resor_h': round(float(T.at[a, b]), 2),
                                    'idag_min': round(float(c0.at[a, b]), 1), 'ua6_min': round(float(c1.at[a, b]), 1),
                                    'vinst_resenarsmin_h': round(float(T.at[a, b] * d), 2)})
    exempel = sorted(exempel, key=lambda e: -e['vinst_resenarsmin_h'])
    sg = V.segmentgeometri(); st = list(V.monster_per_linje()['N'][0][0])
    km = sum(V.langd(sg[(a, b)]) for a, b in zip(st[:-1], st[1:])) / 1000
    p = pd.read_csv(P / 'a2_delpunkter.csv.gz'); p = p[p.mariehamn]
    H = pd.read_csv(P / 'a2_hallplatser_avgangar.csv', index_col=0, dtype={'stop_id': str})
    xy = H.loc[[s for s in st if s in H.index], ['x', 'y']].to_numpy()
    dd = np.min(np.hypot(p.x.to_numpy()[:, None] - xy[None, :, 0], p.y.to_numpy()[:, None] - xy[None, :, 1]), axis=1)
    nara = dd <= C.TACKNING_M
    ny = p.avg_alla + np.where(nara, TURER, 0)
    lyft30 = nara & (p.avg_alla < 30) & (ny >= 30)
    res = {'turer_moturs': TURER, 'kortid_varv_min': round(float(nm['akt'].sum()), 1), 'reglering_min': REGLERING,
           'fordon_extra': int(np.ceil((nm['akt'].sum() + REGLERING) / 30.0)), 'km_varv': round(km, 2),
           'fordonskm_vardag': round(km * TURER, 1),
           'restid': {per: {k: round(v, 2) for k, v in j[per].items()} for per in j},
           'resenarsminuter_vardag': round((j['FM']['resenarsminuter_h'] + j['EM']['resenarsminuter_h']) / 2 * fak, 0),
           'resor_kortare_vardag': round((j['FM']['resor_kortare_h'] + j['EM']['resor_kortare_h']) / 2 * fak, 0),
           'inv_inom_400m_norra': int(round(p.bef[nara].sum())),
           'inv_lyft_till_minst_30': int(round(p.bef[lyft30].sum())),
           'inv_lyft_till_minst_60': int(round(p.bef[nara & (p.avg_alla < 60) & (ny >= 60)].sum())),
           'andel_minst_30_fore': round(float(p.bef[p.avg_alla >= 30].sum() / p.bef.sum()), 3),
           'andel_minst_30_efter': round(float(p.bef[ny >= 30].sum() / p.bef.sum()), 3),
           'exempel': exempel[:15]}
    json.dump(res, open(P / 'b4_ua6_norra.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return res, p[lyft30]


def figur(res, lyft):
    import s01_vagdragning as V
    sg = V.segmentgeometri(); st = list(V.monster_per_linje()['N'][0][0])
    xy = np.vstack([sg[(a, b)] if i == 0 else sg[(a, b)][1:] for i, (a, b) in enumerate(zip(st[:-1], st[1:]))])
    uts = (106900, 109500, 6683100, 6687250)
    FN = C.FARG_LINJE['N']
    fig, axs = plt.subplots(1, 2, figsize=(11.4, 9.6))
    for ax, titel, bada in ((axs[0], 'I dag – en riktning', False), (axs[1], 'UA 6 – båda riktningarna', True)):
        K.ny_karta(uts, ax=ax, titel=titel)
        if bada:
            ax.scatter(lyft.x, lyft.y, s=5, color='#2f9e44', alpha=0.45, lw=0, zorder=2)
        ax.plot(xy[:, 0], xy[:, 1], color=FN, lw=3.4, zorder=5, solid_capstyle='round', solid_joinstyle='round',
                path_effects=[K.pe.Stroke(linewidth=5.6, foreground='white'), K.pe.Normal()])
        L = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])
        for dist in np.arange(260, L[-1], 520):                   # körriktning: enkel- eller dubbelpil
            j_ = min(max(int(np.searchsorted(L, dist)), 1), len(xy) - 1)
            a_, b_ = xy[j_ - 1], xy[j_]
            if np.hypot(*(b_ - a_)) < 1:
                continue
            m_ = (a_ + b_) / 2; t_ = (b_ - a_) / np.hypot(*(b_ - a_)) * 35
            ax.annotate('', xy=tuple(m_ + t_), xytext=tuple(m_ - t_), zorder=7,
                        arrowprops=dict(arrowstyle='<|-|>' if bada else '-|>', color='#2b1838', lw=1.2,
                                        mutation_scale=11))
        H = pd.read_csv(P / 'a2_hallplatser_avgangar.csv', index_col=0, dtype={'stop_id': str})
        h = H.loc[[s for s in st if s in H.index]]
        ax.scatter(h.x, h.y, s=16, facecolor='white', edgecolor='#1f1f1e', lw=0.7, zorder=6)
        namn = ['Centrum, Nygatan', 'Maxinge', 'Hindersbölevägen', 'Nabben', 'Sjukhuset', 'Doktorsvägen 1A', 'Norragatan']
        g = h[h.namn.isin(namn)].groupby('namn')[['x', 'y']].mean()
        K.placera_etiketter(ax, [(n.replace('Centrum, Nygatan', 'Centrum'), (r.x, r.y), 40) for n, r in g.iterrows()],
                            fontsize=6.6)
    K.skalstock(axs[0], loc=(0.06, 0.035))
    hnd = [Line2D([], [], color=FN, lw=3, label='Norra'),
           Line2D([], [], color='#2b1838', lw=0, marker='$↔$', markersize=12, label='Körriktning (dubbelpil = båda)'),
           Patch(facecolor='#2f9e44', alpha=0.6, label='Får minst 30 avgångar per vardag')]
    lg = K.teckenforklaring(axs[1], hnd, loc='lower right')
    fig.tight_layout()
    return K.spara(fig, 'b4_21_norra_bada_riktningar.png')


ROTATION = (('N', 'S'), ('S', 'M'), ('M', 'N'))          # Norra medurs → Södra → Norra moturs → …
INTERVALL = {'J': 60.0}


def omlopp():
    """Omlopp i dag (operatörens), A (+1 fordon, rotation N → S → M) och B (fem fordon, varannan Norra-tur moturs)."""
    import b4_omlopp as O
    t = O.turer(); op = O.omlopp_operator(t)
    m = t[t.linje == 'N'].copy(); m['linje'] = 'M'; m['trip_id'] = m.trip_id.astype(str) + '_M'
    nsm = pd.concat([t[t.linje.isin(['N', 'S'])], m], ignore_index=True).sort_values(['avg', 'linje']).reset_index(drop=True)
    gammal = O.ANNAT_BYTE_STRAFF; O.ANNAT_BYTE_STRAFF = 20.0     # rotationen före andra byten
    a_ns = O.bygg_omlopp(nsm, par=ROTATION)
    O.ANNAT_BYTE_STRAFF = gammal
    ovr = op[~op.linje.isin(['N', 'S'])].copy()
    ovr['buss'] = ovr.buss.rank(method='dense').astype(int) + a_ns.buss.max()
    a_ns['omlopp'] = a_ns.buss.map(lambda b: f'NS{b}')
    pa = pd.concat([a_ns, ovr], ignore_index=True)
    pb = op.copy(); idx = pb[pb.linje == 'N'].sort_values('avg').index[1::2]; pb.loc[idx, 'linje'] = 'M'   # dagens omlopp
    def nt(o):
        span = o.groupby('buss').apply(lambda d: d.ank.max() - d.avg.min(), include_groups=False)
        ln = o.linje.to_numpy(); nx = o.nasta.to_numpy() if 'nasta' in o else None
        return {'fordon': int(o.buss.nunique()), 'omloppstid_h': round(float(span.sum() / 60), 1),
                'km': round(float(o.km.sum()), 1), 'turer': int(len(o))}
    rot = {}
    for b, d in a_ns.groupby('buss'):
        rot[int(b)] = ''.join(d.sort_values('avg').linje.map({'N': 'N', 'S': 'S', 'M': 'm'}))
    return {'idag': op, 'A': pa, 'B': pb}, {'idag': nt(op), 'A': nt(pa), 'B': nt(pb), 'rotation_A': rot}


def restid_vantan():
    """Resenärsminuter per vardag med väntetid (halva turintervallet) för A och B jämfört med i dag."""
    import b4_natverk as N
    zoner = list(pd.read_csv(P / 'a1_restider_min.csv', index_col=0).index)
    mon0 = N.monster(); fak = N.dagsfaktor()
    nm = max([m for m in mon0 if m['linje'] == 'N'], key=lambda m: len(m['turer']))
    rev = {'linje': 'N', 'stopp': nm['stopp'][::-1], 'zoner': nm['zoner'][::-1], 'akt': nm['akt'][::-1].copy(),
           'turer': [], 'moturs': True}
    def v(mon, h_norra):
        return [{**m, 'vantan': (h_norra if m['linje'] == 'N' else INTERVALL.get(m['linje'], 30.0)) / 2} for m in mon]
    n0 = N.Nat(v(mon0, 30.0), zoner)
    dag = lambda j: float(round((j['FM']['resenarsminuter_h'] + j['EM']['resenarsminuter_h']) / 2 * fak, 0))
    return {'A': dag(N.jamfor(n0, N.Nat(v(mon0 + [rev], 30.0), zoner))),
            'B': dag(N.jamfor(n0, N.Nat(v(mon0 + [rev], 60.0), zoner)))}


def fig_omlopp(planer, nyck):
    import b4_omlopp as O
    C.FARG_LINJE.setdefault('M', '#3c2350'); C.NAMN_LINJE.setdefault('M', 'Norra moturs')
    fig, axs = plt.subplots(3, 1, figsize=(12.4, 0.75 + 1.75 * 3), squeeze=False)
    titlar = {'idag': f"I dag – {nyck['idag']['fordon']} bussar",
              'A': f"★ UA 6 A – Norra i båda riktningarna var 30:e minut: {nyck['A']['fordon']} bussar",
              'B': f"UA 6 B – varannan Norra-tur moturs (varje riktning en gång i timmen): {nyck['B']['fordon']} bussar"}
    for ax, k in zip(axs[:, 0], ('idag', 'A', 'B')):
        pl = planer[k].copy()
        if k != 'idag' and 'omlopp' in pl:
            pl = pl.drop(columns=['omlopp'])
        O.rita_omlopp(ax, pl, titel=titlar[k])
    fig.suptitle('UA 6 – omlopp', x=0.01, ha='left')
    extra = [Patch(facecolor=C.FARG_LINJE['M'], label='Norra moturs (mörk)')]
    O.omlopp_forklaring(fig, extra=extra, y=-0.01)
    fig.tight_layout(rect=(0, 0.035, 1, 0.975), h_pad=0.9)
    ut = C.KARTOR / 'b4_22_norra_omlopp.png'
    K.fullnamn_fig(fig); fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


if __name__ == '__main__':
    r, lyft = berakna()
    planer, nyck = omlopp(); rv = restid_vantan()
    r['omlopp'] = nyck; r['resenarsminuter_vardag_med_vantan'] = rv
    json.dump(r, open(P / 'b4_ua6_norra.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
    print(nyck, rv)
    print(fig_omlopp(planer, nyck))
    print({k: v for k, v in r.items() if k != 'exempel'})
    for e in r['exempel'][:8]:
        print(e)
    print(figur(r, lyft))
