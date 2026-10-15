# -*- coding: utf-8 -*-
"""B4 – Systemeffekter av de enskilda utredningsalternativen (täckningsgrad före/efter, omlopp, resenärer) och
sammanslagning av linje V och Ö.

Utredningsalternativen redovisas var för sig. Omloppen följer normen att föraren byter linje i centrum Syd ↔ Norr
(S ↔ N) och Öst ↔ Väst (Ö ↔ V), se b4_omlopp.py. Scenarier (driftformerna kommer från b4_ua.omlopp_scenarier):
  idag      Dagens linjenät.
  1a        Möckelö Strand ny via dagens vägar (+4,5 min/tur), alla turer – kräver fler bussar (kostnadsunderlag).
  1a_ryms   1a med dagens tidtabell, bara de turer som ryms i omloppen.
  1a_VO     1a med linje V och Ö sammanslagna till genomgående linje: bussen fortsätter direkt som linje Ö
            (0,5 min) och Ö avgår upp till 2 min efter pulsen – de turer som då ryms.
  1b        Möckelö Strand ny via förlängd Norrgårdsvägen, slinga (+2,5 min/tur), alla turer.
  2         N2 på linje Ö.
  3         Linje N via Bo-Bil i stället för Vikingagränd.
  4         Linje V till flygplatsen, alla turer (kräver fler bussar).
  4_VO      4 med V och Ö sammanslagna (Ö ≤ 2 min efter pulsen).
  4_VO_sol  4 med V och Ö sammanslagna och hållplatsen Solberget indragen på linje Ö.
  4_Y       'Y': bara V-turerna för flygen, V och Ö sammanslagna, Solberget indragen (lika robust som i dag).
För varje scenario: omlopp (fordon, omloppstid, körtid, km, robusthet), täckningsgrad i Mariehamn (400 m,
turtäthetsklasser, svag och otäckt befolkning), resenärseffekter (OD-utläggning) och tillkommande påstigande.
Utdata: data/processed/b4_systemeffekter.json, b4_systemeffekter_omlopp.csv, b4_systemeffekter_tackning.csv.gz,
        output/kartor/b4_9_sammanslagning_vo.png, b4_11_flygplatsen_vo.png, b4_13_systemeffekter.png, b4_14_tackning_fore_efter.png
"""
import json
import sys
from functools import lru_cache
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402
import kartlib as K  # noqa: E402
import b4_omlopp as O  # noqa: E402
import b4_natverk as N  # noqa: E402
import b4_ua as F  # noqa: E402
from a2_tackning import KLASSER, avgangar_inom, hallplatser_med_avgangar, klass, sammanstall  # noqa: E402

P = C.PROCESSED
# id, UA, driftform (nyckel i b4_ua.omlopp_scenarier)
SCENARIER = [('idag', None, None), ('1a', '1a', 'alla'), ('1a_ryms', '1a', 'ryms'), ('1a_VO', '1a', 'VO'),
             ('1b', '1b', 'alla'), ('2', '2', 'alla'), ('3', '3', 'alla'),
             ('4', '4', 'alla'), ('4_VO', '4', 'VO'), ('4_VO_sol', '4', 'VO_sol'), ('4_Y', '4', 'Y_VO_sol')]
BATTRE, SAMRE = '#2f9e44', '#c0392b'


def atgarder():
    xy = F.stopp_xy()
    ut = {f['id']: f for f in F.alternativ()}
    bb = F.bobil_delta(xy)
    ut['3']['delta'], ut['3']['km_tur'] = bb['delta_min'], bb['delta_km']
    ut['sol'] = {'id': 'sol', 'typ': 'indrag', 'linje': 'Ö', 'bort': F.HPL['Solberget'], 'till': [], 'delta': None}
    return ut, xy


def berorda_turer(f, t):
    lt = t[t.linje == f['linje']]
    if f['typ'] == 'ny' and f['segment'][1] is None:
        lt = lt[lt.monster.map(lambda m: f['segment'][0] in m)]
    return list(lt.sort_values('avg').trip_id)


UTESLUTEN = ('1a', '4')        # driftformer som kräver fler bussar – uteslutna, redovisas bara i rapporten
HUVUD = {'1a_VO': '1a', '1b': '1b', '2': '2', '3': '3', '4_VO_sol': '4'}   # huvudalternativ per UA (kartan)


def namn(sid, v):
    n, tot, b = v.get('turer', 0), v.get('turer_tot', 0), v['omlopp']['fordon']
    return {'idag': 'I dag',
            '1a': f"UA 1a Möckelö Strand ny via dagens vägar – alla {tot} turer, dagens tidtabell ({b} bussar, utesluten)",
            '1a_ryms': f"UA 1a – dagens tidtabell, {n} av {tot} turer",
            '1a_VO': f"UA 1a – V och Ö sammanslagna (Ö ≤ 2 min efter pulsen), {n} av {tot} turer (huvudalternativ)",
            '1b': f"UA 1b Möckelö Strand ny via förlängd Norrgårdsvägen – alla {tot} turer (huvudalternativ)",
            '2': 'UA 2 N2 på linje Ö (huvudalternativ)', '3': 'UA 3 Linje N via Bo-Bil (huvudalternativ)',
            '4': f"UA 4 Linje V till flygplatsen – alla {tot} turer, dagens tidtabell ({b} bussar, utesluten)",
            '4_VO': f"UA 4 – V och Ö sammanslagna, {n} av {tot} turer",
            '4_VO_sol': f"UA 4 – V och Ö sammanslagna, Solberget indragen, {n} av {tot} turer (huvudalternativ)",
            '4_Y': f"UA 4Y – bara turerna för flygen ({n} av {tot}), V och Ö sammanslagna, Solberget indragen"}[sid]


def kort(sid, v):
    n, tot, b = v.get('turer', 0), v.get('turer_tot', 0), v['omlopp']['fordon']
    return {'idag': 'I dag', '1a': f"UA 1a alla turer\n({b} bussar – utesluten)",
            '1a_ryms': f"UA 1a dagens tidtabell\n({n} av {tot} turer)",
            '1a_VO': f"UA 1a ★ V och Ö samman-\nslagna ({n} av {tot} turer)",
            '1b': f"UA 1b ★ förlängd Norr-\ngårdsvägen ({n} av {tot})", '2': 'UA 2 ★ N2 linje Ö', '3': 'UA 3 ★ N via Bo-Bil',
            '4': f"UA 4 alla turer\n({b} bussar – utesluten)", '4_VO': f"UA 4 V och Ö samman-\nslagna ({n} av {tot} turer)",
            '4_VO_sol': f"UA 4 ★ dito + Solberget\nindragen ({n} av {tot})", '4_Y': f"UA 4Y flygturerna\n({n} av {tot}), dito"}[sid]


# ====================================================================== täckning
def hallplatser_scenario(hpl0, atg, turer, xy):
    h = hpl0.copy()
    for a, valda in turer.items():
        f = atg[a]; tn = frozenset(valda)
        if not tn:
            continue
        if f['typ'] == 'ny':
            h.loc[f'NY_{a}'] = {'turer': tn, 'linjer': f['linje'], 'avgangar': len(tn), 'x': f['xy'][0],
                                'y': f['xy'][1], 'namn': f['hpl_namn']}
        else:
            h.at[f['bort'], 'turer'] = h.at[f['bort'], 'turer'] - tn
            for s in f['till']:
                if s in h.index:
                    h.at[s, 'turer'] = h.at[s, 'turer'] | tn
                else:
                    h.loc[s] = {'turer': tn, 'linjer': f['linje'], 'avgangar': len(tn), 'x': xy.at[s, 'x'],
                                'y': xy.at[s, 'y'], 'namn': xy.at[s, 'namn']}
    h = h[h.turer.map(len) > 0].copy()
    h['avgangar'] = h.turer.map(len)
    return h


# ====================================================================== resenärer
def monster_scenario(mon0, atg, turer, t, gen=()):
    """Mönster med UA:ns körtider; andelen turer som trafikerar en åtgärd skalar tillägget."""
    mon = []
    for m in mon0:
        m = dict(m); m['akt'] = m['akt'].copy(); s = list(m['stopp'])
        for a, valda in turer.items():
            f = atg[a]
            if m['linje'] != f['linje'] or not valda:
                continue
            andel = len(valda) / max(len(berorda_turer(f, t)), 1)
            if f['typ'] == 'ny':
                a0, b0 = f['segment']
                for k in range(len(s) - 1):
                    if s[k] == a0 and (b0 is None or s[k + 1] == b0):
                        m['akt'][k] += f['delta'] * andel
                        break
            elif f['typ'] == 'indrag' and f['bort'] in s:         # hållplatsen dras in: direkt mellan grannarna
                k = s.index(f['bort'])
                d = F.direkttider().get((s[k - 1], s[k + 1]))
                tot = m['akt'][k - 1] + m['akt'][k]
                if d is not None and tot > d:
                    m['akt'][k - 1] *= d / tot; m['akt'][k] *= d / tot
            elif f['bort'] in s:
                k = s.index(f['bort'])
                z = list(m['zoner']); z[k] = 'Bo-Bil'; m['zoner'] = tuple(z)
                m['akt'][k - 1] += f['delta'] / 2; m['akt'][k] += f['delta'] / 2
        mon.append(m)
    for x, y in gen:                                   # genomgående: fordonet fortsätter från x till y
        hx = max([m for m in mon if m['linje'] == x], key=lambda m: len(m['turer']))
        hy = max([m for m in mon if m['linje'] == y], key=lambda m: len(m['turer']))
        for a_, b_ in ((hx, hy), (hy, hx)):
            akt = np.concatenate([a_['akt'], b_['akt']]); akt[len(a_['akt'])] += O.GENOMGANG_MIN
            mon.append({'linje': a_['linje'] + b_['linje'], 'stopp': a_['stopp'] + b_['stopp'][1:],
                        'zoner': a_['zoner'] + b_['zoner'][1:], 'akt': akt, 'turer': []})
    return mon


def resenarer(nat0, mon, zoner):
    j = N.jamfor(nat0, N.Nat(mon, zoner)); fak = N.dagsfaktor()
    medel = lambda k: float(np.mean([j[p][k] for p in ('FM', 'EM')]))
    return {'resenarsminuter_vardag': round(medel('resenarsminuter_h') * fak, 1),
            'resor_langre_vardag': round(medel('resor_langre_h') * fak, 1),
            'resor_kortare_vardag': round(medel('resor_kortare_h') * fak, 1)}


# ====================================================================== huvudflöde
def berakna():
    t = O.turer(); plan0 = O.bygg_omlopp(t); r = O.ram(t); ref = O.kopplingar(plan0)
    atg, xy = atgarder()
    pkt = pd.read_csv(P / 'a2_delpunkter.csv.gz')
    mh = pkt.mariehamn.to_numpy()
    hpl0 = hallplatser_med_avgangar()
    rate = F.pastigande_per_inv(pkt)
    zoner = list(pd.read_csv(P / 'a1_restider_min.csv', index_col=0).index)
    mon0 = N.monster(); nat0 = N.Nat(mon0, zoner)
    res, planer, kl, scen_f, hpl_scen = {}, [], {}, {}, {}
    for sid, fid, k in SCENARIER:
        if fid is None:
            plan, nt, ok, rob, turer, skift = O.verifiera(t, {}, r, referens=ref) + (True, {}, {})
        else:
            if fid not in scen_f:
                scen_f[fid] = F.omlopp_scenarier(atg[fid], t, r, ref)
            s_ = scen_f[fid][k]
            plan, nt, ok, rob, turer, skift = s_['plan'], s_['nt'], s_['ok'], s_['robust'], {fid: s_['turer']}, s_['skift']
            if s_.get('solberget'):
                turer['sol'] = list(t[t.linje == 'Ö'].trip_id)
        h = hallplatser_scenario(hpl0, atg, turer, xy)
        hpl_scen[sid] = h
        avg, _ = avgangar_inom(pkt, h)
        k_ = np.array([klass(v) for v in avg]); kl[sid] = k_
        p = pkt.assign(k=k_)
        tack_mh = sammanstall(p, 'k', mh); tack_alla = sammanstall(p, 'k')
        nya = {}
        for a, valda in turer.items():
            f = atg[a]
            if f['typ'] == 'ny' and valda:
                d_ = np.hypot(pkt.x - f['xy'][0], pkt.y - f['xy'][1]) <= C.TACKNING_M
                ny_inv = float(pkt.loc[d_ & (kl['idag'] == 0) & (k_ > 0), 'bef'].sum())
                nya[a] = {'avgangar': len(valda), 'ny_tackning_inv': round(ny_inv),
                          'pastigande_vardag': round(ny_inv * rate.get(f['linje'], rate['alla']), 2)}
        gen = [('V', 'Ö')] if k and 'VO' in k else []
        rs = resenarer(nat0, monster_scenario(mon0, atg, turer, t, gen), zoner) if turer else \
            {'resenarsminuter_vardag': 0.0, 'resor_langre_vardag': 0.0, 'resor_kortare_vardag': 0.0}
        v = {'ua': fid, 'driftform': k, 'ryms': bool(ok), 'robust': bool(rob),
             'fler_bussar': bool(nt['fordon'] > r['fordon']), 'omlopp': nt,
             'turer': len(turer.get(fid, [])),
             'turer_tot': (len(F.flygturer(t)) if k.startswith('Y') else len(berorda_turer(atg[fid], t))) if fid else 0,
             'solberget_indragen': 'sol' in turer,
             'skiftade_turer': len(skift), 'tackning_mariehamn': tack_mh, 'tackning_hela_omradet': tack_alla,
             'nya_hallplatser': nya, 'resenarer': rs}
        v['namn'] = namn(sid, v); v['kort'] = kort(sid, v)
        res[sid] = v
        pl = plan.drop(columns=['monster']).copy(); pl['scenario'] = sid
        planer.append(pl)
        print(f"{sid:8s} ryms={ok} robust={rob} varv={nt['varv_utan_reglering']} fordon={nt['fordon']} "
              f"omloppstid={nt['omloppstid_h']} km={nt['km']} turer={v['turer']}/{v['turer_tot']} skift={len(skift)} "
              f"inom400={tack_mh['inom_400m_andel']} ≥30={tack_mh['minst_30_avg_andel']} svag={tack_mh['svag_invanare']} res={rs}")
    # förändring mot i dag
    bas = res['idag']
    k0 = kl['idag']; bef = pkt.bef.to_numpy()
    for sid, v in res.items():
        k1 = kl[sid]; sm = lambda m: int(round(float(bef[mh & m].sum())))
        v['forandring_invanare_mariehamn'] = {
            'ny_tackning': sm((k0 == 0) & (k1 > 0)), 'lyft_till_minst_30': sm((k0 > 0) & (k0 < 3) & (k1 >= 3)),
            'battre_klass': sm(k1 > k0), 'samre_klass': sm(k1 < k0), 'forlorad_tackning': sm((k0 > 0) & (k1 == 0)),
            'samre_klass_kvar_tackning': sm((k1 < k0) & (k1 > 0))}
        a, b = v['tackning_mariehamn'], bas['tackning_mariehamn']
        inv = lambda d, i: d[KLASSER[i][2]]['invanare']
        v['forandring_mariehamn'] = {
            'inom_400m_inv': -(inv(a, 0) - inv(b, 0)),
            'minst_15_inv': sum(inv(a, i) for i in range(2, 5)) - sum(inv(b, i) for i in range(2, 5)),
            'minst_30_inv': sum(inv(a, i) for i in range(3, 5)) - sum(inv(b, i) for i in range(3, 5)),
            'svag_inv': a['svag_invanare'] - b['svag_invanare'],
            'otackt_inv': inv(a, 0) - inv(b, 0)}
        v['forandring_omlopp'] = {k: round(v['omlopp'][k] - bas['omlopp'][k], 2)
                                  for k in ('fordon', 'omloppstid_h', 'korttid_h', 'km')}
    pd.concat(planer).to_csv(P / 'b4_systemeffekter_omlopp.csv', index=False)
    import tackningsytor as T                       # täckningsytor som vektorer (exakta 400 m-cirklar) för kartor/GIS
    f = P / 'b4_systemeffekter_ytor.gpkg'
    f.unlink(missing_ok=True)
    T.ytor(hpl_scen).to_file(f, layer='ytor', driver='GPKG')
    tk = pkt[['x', 'y', 'bef', 'ruta_id', 'mariehamn']].copy()
    for sid, k_ in kl.items():
        tk[f'klass_{sid}'] = k_
    tk.round({'bef': 5}).to_csv(P / 'b4_systemeffekter_tackning.csv.gz', index=False)
    with open(P / 'b4_systemeffekter.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=float)
    return res


# ====================================================================== figurer
def sv(x, d=1):
    return f'{x:.{d}f}'.replace('.', ',').replace('-', '−')


def tidsbudget(fid='1a'):
    """Varv V → Ö → V (60 min) i rusning och i varv med Ö:s skoltur: körtider och byten per alternativ."""
    prof = json.load(open(P / 'b4_omlopp_nyckeltal.json', encoding='utf-8'))['linjer']
    res_f = json.load(open(P / 'b4_ua.json', encoding='utf-8'))
    fs = res_f['ua']
    tv, to = prof['V']['kortid_median'], prof['Ö']['kortid_median']
    pl = pd.read_csv(P / 'b4_omlopp_idag.csv')
    skol = float(pl[(pl.linje == 'Ö') & pl.avg.between(13 * 60, 16 * 60)].kortid.max())   # eftermiddagens skolturer
    sk = O.MAX_SKIFT_PARTNER
    rader = [('I dag – rusning', tv, to, 0.0), (f'I dag – varv med Ö-skoltur ({skol:.0f} min)', tv, skol, 0.0)]
    if fid == '1a':
        d1a, d1b = fs['1a']['delta_min_per_tur'], fs['1b']['delta_min_per_tur']
        return rader + [
            (f'UA 1b +{sv(d1b)} min – rusning', tv + d1b, to, 0.0), (f'UA 1b +{sv(d1b)} min – varv med Ö-skoltur', tv + d1b, skol, 0.0),
            (f'UA 1a +{sv(d1a)} min – dagens tidtabell', tv + d1a, to, 0.0),
            (f'UA 1a +{sv(d1a)} min – V och Ö sammanslagna, Ö ≤ {sv(sk, 0)} min efter pulsen', tv + d1a, to, sk),
            (f'UA 1a +{sv(d1a)} min – sammanslagna, varv med Ö-skoltur', tv + d1a, skol, sk)]
    d4 = fs['4']['delta_min_per_tur']
    sol = np.mean([v for k, v in res_f['solberget_indragen']['besparing_min_per_tur'].items() if k in ('13:10', '14:10', '15:10')])
    return rader + [
        (f'UA 4 +{sv(d4)} min – dagens tidtabell', tv + d4, to, 0.0),
        (f'UA 4 +{sv(d4)} min – V och Ö sammanslagna, Ö ≤ {sv(sk, 0)} min efter pulsen', tv + d4, to, sk),
        (f'UA 4 +{sv(d4)} min – sammanslagna, varv med Ö-skoltur', tv + d4, skol, sk),
        (f'UA 4 +{sv(d4)} min – sammanslagna, Solberget indragen (Ö −{sv(sol)} min), skoltur', tv + d4, skol - sol, sk),
        (f'UA 4 +{sv(d4 + 1)} min (känslighet) – sammanslagna, rusning', tv + d4 + 1, to, sk)]


def fig_vo(res, fid='1a'):
    fs = json.load(open(P / 'b4_ua.json', encoding='utf-8'))['ua']
    rader = tidsbudget(fid)
    fig = plt.figure(figsize=(14.2, 6.4 if fid == '1a' else 7.0))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.45, 1.1], wspace=0.04, left=0.01, right=0.99, top=0.86, bottom=0.17)
    ax = fig.add_subplot(gs[0, 0])
    G = O.GENOMGANG_MIN
    fv, fo = C.FARG_LINJE['V'], C.FARG_LINJE['Ö']
    for i, (rub, tv, to, sk) in enumerate(rader):
        y = len(rader) - 1 - i
        ax.add_patch(Rectangle((0, y - 0.32), tv, 0.64, facecolor=fv, edgecolor='white', lw=0.6, zorder=3))
        ax.text(tv / 2, y, f'V {sv(tv)}', ha='center', va='center', fontsize=7.5, color='white', fontweight='bold', zorder=4)
        o_avg = 30.0 + min(max(tv + G - 30.0, 0.0), sk)          # Ö avgår :50 eller upp till sk min senare
        ok_vo = tv <= o_avg - (G if sk > 0 or tv > 30 - 3 else 0.0) + 1e-9 and tv + G <= o_avg + 1e-9 or tv <= o_avg - G + 1e-9
        konflikt = tv > o_avg - G + 1e-9
        if konflikt:                                               # V hinner inte till Ö:s avgång
            ax.add_patch(Rectangle((o_avg - G, y - 0.42), tv - (o_avg - G), 0.84, facecolor='none', edgecolor=SAMRE,
                                   hatch='xxxx', lw=1.0, zorder=5))
        else:
            v_ = o_avg - tv
            ax.add_patch(Rectangle((tv, y - 0.2), v_, 0.4, facecolor='#1c5cab' if v_ < 3 else '#b9b4a8', zorder=3))
            if v_ >= 1.2:
                ax.text(tv + v_ / 2, y + 0.42, sv(v_), ha='center', va='bottom', fontsize=6.6, color=K.TEXT)
        ax.add_patch(Rectangle((o_avg, y - 0.32), to, 0.64, facecolor=fo, edgecolor='white', lw=0.6, zorder=3, alpha=0.95))
        ax.text(o_avg + to / 2, y, f'Ö {sv(to, 0)}' + (f' (+{sv(o_avg - 30)})' if o_avg > 30 else ''), ha='center',
                va='center', fontsize=7.5, color='white', fontweight='bold', zorder=4)
        rest = 60.0 - (o_avg + to)
        if rest >= G - 1e-9:
            ax.add_patch(Rectangle((o_avg + to, y - 0.2), rest, 0.4, facecolor='#1c5cab' if rest < 3 else '#b9b4a8', zorder=3))
            ax.text(o_avg + to + rest / 2, y + 0.42, sv(rest), ha='center', va='bottom', fontsize=6.6, color=K.TEXT)
        else:
            x0 = o_avg + to
            ax.add_patch(Rectangle((60.0 - G, y - 0.42), x0 - (60.0 - G), 0.84, facecolor='none', edgecolor=SAMRE,
                                   hatch='xxxx', lw=1.0, zorder=5))
        ryms = not konflikt and rest >= G - 1e-9
        ax.text(-1.0, y, rub, ha='right', va='center', fontsize=8, color=K.TEXT)
        ax.text(64.0, y, 'ryms' if ryms else 'ryms inte', ha='left', va='center', fontsize=8,
                color=BATTRE if ryms else SAMRE, fontweight='bold')
    for x_, lbl in [(0, ':20\nV avgår'), (30, ':50 pulsen\nÖ avgår i dag'), (60, ':20\nnästa V')]:
        ax.axvline(x_, color='#52514e', lw=0.9, ls=(0, (3, 2)), zorder=2)
        ax.text(x_, len(rader) - 0.2, lbl, ha='center', va='bottom', fontsize=7, color=K.TEXT2 if hasattr(K, 'TEXT2') else K.TEXT)
    ax.set_xlim(-46, 71); ax.set_ylim(-0.7, len(rader) + 0.7)
    ax.axis('off')
    ax.set_title('Tidsbudget per varv: buss V → Ö → V på 60 min (två bussar ger 30 min turintervall)', loc='left',
                 fontsize=10, fontweight='bold')
    h = [Patch(facecolor=fv, label='Linje V (körtid, min)'), Patch(facecolor=fo, label='Linje Ö'),
         Patch(facecolor='#b9b4a8', label='Byte med reglering ≥ 3 min'), Patch(facecolor='#1c5cab', label='Kort byte (< 3 min)'),
         Patch(facecolor='none', edgecolor=SAMRE, hatch='xxxx', label='Tiden räcker inte')]
    ax.legend(handles=h, loc='upper left', bbox_to_anchor=(0.0, -0.01), ncol=5, fontsize=7.2, frameon=False)
    # resultat
    ax2 = fig.add_subplot(gs[0, 1]); ax2.axis('off')
    o = fs[fid]['omlopp']
    tot = fs[fid]['linjens_turer']
    if fid == '1a':
        b = fs['1b']['omlopp']
        rad = [('UA 1a dagens tidtabell', o['ryms'], tot), ('UA 1a ★ V och Ö sammanslagna', o['VO'], tot),
               ('   … lika robust som i dag', o.get('VO_robust', o['VO']), tot), ('UA 1a alla turer (utesluten)', o['alla'], tot),
               ('UA 1b ★ (+2,5 min)', b['alla'], tot), ('   … lika robust som i dag', b.get('robust', b['alla']), tot),
               ('UA 1b känslighet +3,5 min', b['konservativ_ryms'], tot), ('   … V och Ö sammanslagna', b['konservativ_VO'], tot)]
        rubrik2, ny = 'Möckelö Strand ny utan fler bussar', 'ny hållplats'
    else:
        ny_ = len(json.load(open(P / 'b4_ua.json', encoding='utf-8'))['flygplatsen']['flygturer'])
        d4 = fs['4']['delta_min_per_tur']
        rad = [('UA 4 dagens tidtabell', o['ryms'], tot), ('UA 4 V och Ö sammanslagna', o['VO'], tot),
               ('   … lika robust som i dag', o.get('VO_robust', o['VO']), tot),
               ('UA 4 ★ dito + Solberget indragen', o['VO_sol'], tot), ('   … lika robust som i dag', o['VO_sol_robust'], tot),
               ('UA 4 alla turer (utesluten)', o['alla'], tot), ('UA 4Y flygturerna, dagens tidtabell', o['Y_ryms'], ny_),
               ('UA 4Y V och Ö sammanslagna', o['Y_VO'], ny_), ('UA 4Y dito + Solberget (robust)', o['Y_VO_sol'], ny_)]
        rad += [(f'Känslighet {sv(float(k.split("_")[1]))} min, sammanslagna', o[k], tot)
                for k in o if k.startswith('kansl_')]
        rubrik2, ny = 'Flygplatsen utan fler bussar', 'flygplatsen'
    cell = [[r[0], f"{r[1]['turer_med_andring']} av {r[2]}", str(r[1]['fordon']), str(r[1]['varv_utan_reglering']),
             ', '.join(r[1]['turer_utan_andring'][:3]) + (' …' if len(r[1]['turer_utan_andring']) > 3 else '') or '–']
            for r in rad]
    if fid != '1a':                                    # Y: turer utanför flygturerna räknas inte som "som i dag"
        for c, r in zip(cell, rad):
            if r[0].startswith('UA 4Y'):
                c[4] = '–'
    tb = ax2.table(cellText=cell, colLabels=['Alternativ', f'Turer via\n{ny}', 'Bussar', 'Varv < 3 min\nreglering',
                                             'V-turer som\nkör som i dag'],
                   loc='upper left', cellLoc='left', colLoc='left', colWidths=[0.33, 0.15, 0.09, 0.15, 0.28])
    tb.auto_set_font_size(False); tb.set_fontsize(7.0); tb.scale(1, 1.75)
    for (r_, c_), ce in tb.get_celld().items():
        ce.set_edgecolor('#e0ded7'); ce.set_linewidth(0.5)
        if r_ == 0:
            ce.set_facecolor('#f1efe9'); ce.get_text().set_fontweight('bold'); ce.set_height(ce.get_height() * 1.5)
        elif cell[r_ - 1][2] != str(res['idag']['omlopp']['fordon']):
            ce.get_text().set_color(SAMRE)
    ax2.text(0.0, 0.08, f"I dag: {res['idag']['omlopp']['fordon']} bussar, {res['idag']['omlopp']['varv_utan_reglering']} varv med "
             "< 3 min reglering.\nDe V-turer som inte ryms ligger i varven med Ö:s skolturer (28–29 min).\n"
             + ("Turer utan ändring kör till Möckelö Strand som i dag." if fid == '1a' else
                "Turer utan ändring kör som i dag (utan flygplatsen). Y: 8 turer kring flygen\n11:00 och 17:10 "
                "(ankomsttider antagna). 07:15-flyget nås inte (första V-turen 07:36)."),
             transform=ax2.transAxes, fontsize=7.2,
             color=K.TEXT, va='bottom', linespacing=1.5)
    ax2.set_title(rubrik2, loc='left', fontsize=10, fontweight='bold')
    fig.suptitle(('UA 1a – sammanslagning av linje V och Ö: ryms Möckelö Strand ny via dagens vägar?' if fid == '1a'
                  else 'UA 4 – sammanslagning av linje V och Ö: ryms linje V–Ö via flygplatsen?'), x=0.01, ha='left',
                 fontsize=12.5, fontweight='bold')
    ut = C.KARTOR / ('b4_9_sammanslagning_vo.png' if fid == '1a' else 'b4_11_flygplatsen_vo.png')
    fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


IDS = ['1a', '1a_ryms', '1a_VO', '1b', '2', '3', '4', '4_VO', '4_VO_sol', '4_Y']


def fig_systemeffekter(res):
    mat = [('ny_tackning', 'Får hållplats inom 400 m', BATTRE, 1),
           ('lyft_till_minst_30', 'Får minst 30 avgångar/vardag (hade 1–29)', '#1c5cab', 1),
           ('forlorad_tackning', 'Förlorar hållplats inom 400 m', SAMRE, -1),
           ('samre_klass_kvar_tackning', 'Färre avgångar, har kvar hållplats', '#f28e2b', -1)]
    fig = plt.figure(figsize=(15.6, 12.6))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 0.95], hspace=0.28, left=0.11, right=0.99, top=0.94, bottom=0.02)
    ax = fig.add_subplot(gs[0])
    y = np.arange(len(IDS)); hgt = 0.19
    for j, (k, lbl, f, tecken) in enumerate(mat):
        v = [tecken * res[i]['forandring_invanare_mariehamn'][k] for i in IDS]
        ax.barh(y + (j - 1.5) * hgt, v, height=hgt, color=f, label=lbl)
        for yy, vv in zip(y, v):
            if vv:
                ax.text(vv + (3 if vv > 0 else -3), yy + (j - 1.5) * hgt, f'{vv:+d}'.replace('-', '−'), va='center',
                        ha='left' if vv > 0 else 'right', fontsize=6.6, color=K.TEXT)
    ax.axvline(0, color='#52514e', lw=0.8)
    ax.set_yticks(y); ax.set_yticklabels([res[i]['kort'] for i in IDS], fontsize=7.6); ax.invert_yaxis()
    ax.set_xlabel('invånare i Mariehamn med bättre (+) respektive sämre (−) tillgänglighet än i dag', fontsize=8)
    ax.set_xlim(-80, 230); ax.tick_params(labelsize=7.5); ax.grid(axis='x', color='#e6e4de', lw=0.6); ax.set_axisbelow(True)
    for s_ in ['top', 'right']:
        ax.spines[s_].set_visible(False)
    ax.legend(loc='lower right', ncol=2, fontsize=7.3, frameon=True, facecolor='white', edgecolor='#e0ded7')
    ax.set_title('Vem får bättre och sämre tillgänglighet? (varje UA för sig, ★ = huvudalternativ)', loc='left', fontsize=10,
                 fontweight='bold')
    rad = [('Hållplats inom 400 m', lambda t: t['inom_400m_andel']),
           ('Minst 15 avgångar/vardag', lambda t: t['minst_15_avg_andel']),
           ('Minst 30 avgångar/vardag', lambda t: t['minst_30_avg_andel']),
           ('Svag (1–29 avg./vardag)', lambda t: t['svag_andel']),
           ('Ingen hållplats inom 400 m', lambda t: 1 - t['inom_400m_andel'])]
    ax2 = fig.add_subplot(gs[1]); ax2.axis('off')
    kol = ['idag'] + IDS
    cell = [[n] + [sv(100 * fn(res[s_]['tackning_mariehamn']), 1) + ' %' for s_ in kol] for n, fn in rad]
    cell += [['Turer via den nya sträckan', '–', *[f"{res[s_]['turer']} av {res[s_]['turer_tot']}" for s_ in IDS]],
             ['Bussar', *[str(res[s_]['omlopp']['fordon']) for s_ in kol]],
             ['Omloppstid (h/vardag)', *[sv(res[s_]['omlopp']['omloppstid_h']) for s_ in kol]],
             ['Fordonskm per vardag', *[sv(res[s_]['omlopp']['km'], 0) for s_ in kol]],
             ['Varv med < 3 min reglering', *[str(res[s_]['omlopp']['varv_utan_reglering']) for s_ in kol]],
             ['Restid befintliga resenärer\n(resenärsminuter/vardag)', '–',
              *[sv(res[s_]['resenarer']['resenarsminuter_vardag'], 0) for s_ in kol[1:]]]]
    rub = ['Mariehamn (14 821 inv.)', 'I dag', 'UA 1a\nalla turer\n(utesluten)', 'UA 1a\ndagens\ntidtabell',
           'UA 1a ★\nV + Ö\nsamman-\nslagna', 'UA 1b ★', 'UA 2 ★\nN2', 'UA 3 ★\nBo-Bil', 'UA 4\nalla turer\n(utesluten)',
           'UA 4\nV + Ö\nsamman-\nslagna', 'UA 4 ★\ndito +\nSolberget\nindragen', 'UA 4Y\nflyg-\nturerna']
    tb = ax2.table(cellText=cell, colLabels=rub, loc='upper left', cellLoc='right', colLoc='center',
                   colWidths=[0.175] + [0.075] * len(kol))
    tb.auto_set_font_size(False); tb.set_fontsize(7.4); tb.scale(1, 1.55)
    rad_bussar = 1 + len(rad) + 1
    for (r_, c_), ce in tb.get_celld().items():
        ce.set_edgecolor('#e0ded7'); ce.set_linewidth(0.5)
        if c_ == 0:
            ce._loc = 'left'; ce.get_text().set_ha('left')
        if r_ == 0:
            ce.set_facecolor('#f1efe9'); ce.get_text().set_fontweight('bold'); ce.set_height(ce.get_height() * 3.0)
            ce.get_text().set_fontsize(6.8)
        if r_ == len(cell):
            ce.set_height(ce.get_height() * 1.6)
        if r_ == rad_bussar and c_ > 0 and cell[r_ - 1][c_] != cell[r_ - 1][1]:
            ce.get_text().set_color(SAMRE); ce.get_text().set_fontweight('bold')
    ax2.set_title('Nyckeltal – i dag och med varje UA för sig (★ = huvudalternativ; UA 1a och 4 i flera driftformer)', loc='left',
                  fontsize=10, fontweight='bold')
    fig.suptitle('Systemeffekter av utredningsalternativen – täckningsgrad och turtäthet i Mariehamn', x=0.01, ha='left',
                 fontsize=12, fontweight='bold')
    ut = C.KARTOR / 'b4_13_systemeffekter.png'
    fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


def rita_ua(ax, fid):
    """UA:ts nya/ändrade körvägar och hållplatser (b4_ua.gpkg) ovanpå kartan."""
    import geopandas as gpd
    g = gpd.read_file(P / 'b4_ua.gpkg', layer='ua')
    g = g[g.ua == fid]
    for r in g[g.geom_type.isin(['LineString', 'MultiLineString'])].itertuples():
        f = C.FARG_LINJE.get(r.linje, '#1f1f1e')
        stil = dict(color='#3d3d3a', lw=2.4, ls=(0, (1, 1.4))) if r.objekt == 'körväg utgår' else \
            dict(color=f, lw=2.4, ls=(0, (3, 2)) if 'planerad' in r.objekt else '-')
        for d in getattr(r.geometry, 'geoms', [r.geometry]):
            x, y = d.xy
            ax.plot(x, y, zorder=6, solid_capstyle='round',
                    path_effects=[K.pe.Stroke(linewidth=4.2, foreground='white'), K.pe.Normal()], **stil)
    for r in g[g.geom_type == 'Point'].itertuples():
        utgar = 'utgår' in r.objekt or 'dras in' in r.objekt
        ax.scatter([r.geometry.x], [r.geometry.y], s=90 if utgar else 190, marker='X' if utgar else '*',
                   color=SAMRE if utgar else '#1c5cab', edgecolor='white', lw=0.8, zorder=8)


FARG_VO = '#8c3b74'
KLASSFARG = ['#cfcbc2', '#c6dbf5', '#7fb0ec', '#2a78d6', '#0d366b']


@lru_cache(maxsize=1)
def ytor_alla():
    import geopandas as gpd
    return gpd.read_file(P / 'b4_systemeffekter_ytor.gpkg', layer='ytor')


def rita_klasser(ax, sid, skala=1.0):
    """Turtäthetsklass inom 400 m för ett scenario – exakta 400 m-cirklar (tackningsytor.py)."""
    import tackningsytor as T
    y = ytor_alla().dissolve(by=['ruta_id', f'klass_{sid}'], as_index=False)
    rgba = np.array([to_rgba(KLASSFARG[int(k)]) for k in y[f'klass_{sid}']])
    rgba[:, 3] = T.tathet_alfa(y.ruta_id, 0.35, 0.65) * skala
    y.plot(ax=ax, color=rgba, linewidth=0, zorder=1)


def rita_forandring(ax, sid, fyll=0.75, kant=0.0, zorder=2):
    """Ytor där klassen är bättre (grön) respektive sämre (röd) än i dag."""
    import tackningsytor as T
    f = T.forandring(ytor_alla(), sid)
    for r in f.itertuples():
        c = BATTRE if r.forandring == 'Bättre' else SAMRE
        gpd_ = f[f.forandring == r.forandring]
        gpd_.plot(ax=ax, facecolor=to_rgba(c, fyll), edgecolor=c if kant else 'none', linewidth=kant, zorder=zorder)


def vo_kedjor(fid='4'):
    """Den genomgående linjen V–Ö i huvudalternativet: [(N,2)-arrayer] för V (med UA:ts omväg) och Ö."""
    import s01_vagdragning as V
    sg = V.segmentgeometri(); fg = V.uageometri(); hxy = V.alla_xy()[0]; mon = V.monster_per_linje()
    dt = F.direkttider()
    seg = lambda a, b: sg.get((a, b), np.array([hxy[a], hxy[b]]))
    kedja = lambda stopp: [seg(a, b) for a, b in zip(stopp[:-1], stopp[1:])]
    vm, om = list(mon['V'][0][0]), list(mon['Ö'][0][0])
    if fid == '4':
        po, ka = F.HPL['Posten'], F.HPL['Källarvägen']
        ip = vm.index(po)
        v_ = kedja(vm[:ip + 1]) + [fg[(po, 'FLYGPLATSEN')]['xy'], fg[('FLYGPLATSEN', ka)]['xy']] + kedja(vm[ip + 1:])
        om = [x for x in om if x != F.HPL['Solberget']]          # Solberget indragen
    else:
        v_ = kedja(vm)
    return v_ + kedja(om)


def fig_ua4_karta(res):
    """UA 4 – huvudalternativet: linje V–Ö (V och Ö sammanslagna) via flygplatsen, Solberget indragen."""
    import geopandas as gpd
    fs = json.load(open(P / 'b4_ua.json', encoding='utf-8'))
    f = fs['ua']['4']; o = f['omlopp']; fp = fs['flygplatsen']; so = fs['solberget_indragen']
    v = res['4_VO_sol']; fi = v['forandring_invanare_mariehamn']
    uts = (104900, 111700, 6682000, 6689300)
    fig, ax = plt.subplots(figsize=(10.2, 10.6))
    K.ny_karta(uts, ax=ax, titel='UA 4 – Linje V–Ö via flygplatsen (huvudalternativ: V och Ö sammanslagna, Solberget indragen)')
    rita_forandring(ax, '4_VO_sol', fyll=0.6, kant=1.0)
    D.befolkning().boundary.plot(ax=ax, color='#b9b4a8', linewidth=0.35, alpha=0.8, zorder=1.5)
    K.rita_linjer(ax, lw=1.3, alpha=0.35, zorder=3, etikett=False)
    for xy_ in vo_kedjor('4'):
        ax.plot(xy_[:, 0], xy_[:, 1], color=FARG_VO, lw=3.0, zorder=5, solid_capstyle='round',
                path_effects=[K.pe.Stroke(linewidth=4.8, foreground='white'), K.pe.Normal()])
    g = gpd.read_file(P / 'b4_ua.gpkg', layer='ua'); g = g[g.ua == '4']
    fl = g[g.objekt == 'ny hållplats'].geometry.iloc[0]; sl = g[g.objekt == 'hållplats dras in'].geometry.iloc[0]
    xy = F.stopp_xy(); c = xy.loc['9025302000066202', ['x', 'y']].to_numpy(float)
    ax.scatter([fl.x], [fl.y], s=260, marker='*', color='#1c5cab', edgecolor='white', lw=0.8, zorder=8)
    ax.scatter([sl.x], [sl.y], s=110, marker='X', color=SAMRE, edgecolor='white', lw=0.8, zorder=8)
    ax.scatter([c[0]], [c[1]], s=110, marker='s', color='#1f1f1e', edgecolor='white', lw=0.8, zorder=8)
    hinder = K.punkt_hinder(ax, [fl.x, sl.x, c[0]], [fl.y, sl.y, c[1]], px=12)
    K.placera_etiketter(ax, [('Flygplatsen (ny hållplats)', (fl.x, fl.y), 90), ('Solberget (dras in)', (sl.x, sl.y), 90),
                             ('Centrum, Nygatan – bussen fortsätter\nV → Ö efter 0,5 min (genomgående)', tuple(c), 120)],
                        fontsize=7, fet=True, undvik=hinder)
    ny = len(fp['flygturer'])
    txt = [r'$\bf{Huvudalternativ}$' + '   V och Ö körs som en genomgående linje via flygplatsen;',
           f"Ö avgår högst 2 min efter pulsen och Solberget dras in (Ö 1,6–2,5 min kortare)",
           f"Omväg +{sv(f['delta_min_per_tur'])} min/tur (+{sv(f['km_per_tur'], 2)} km). "
           f"{o['VO_sol']['turer_med_andring']} av {f['linjens_turer']} turer via flygplatsen, 5 bussar "
           f"({o['VO_sol_robust']['turer_med_andring']} lika robust som i dag)",
           r'$\bf{UA\ 4Y}$' + f"   bara de {ny} turerna för flygen ({', '.join(fp['flygturer'])}):",
           f"ryms med samma linje, lika robust som i dag",
           r'$\bf{Uteslutet}$' + f"   bara förlängning av V (dagens tidtabell): alla turer kräver {o['alla']['fordon']} bussar",
           r'$\bf{Effekt}$' + f"   +{fi['ny_tackning']} inv. vid flygplatsen får hållplats inom 400 m;",
           f"{so['tackning']['forlorad_tackning_inv']} inv. vid Solberget förlorar sin (≈ {sv(so['pastigande_vardag'])} påstigande/vardag)"]
    ax.text(0.015, 0.985, '\n'.join(txt), transform=ax.transAxes, ha='left', va='top', fontsize=7.2,
            color=K.TEXT, zorder=30, linespacing=1.5,
            bbox=dict(boxstyle='round,pad=0.55', facecolor='white', edgecolor='#d6d5d0', lw=0.6, alpha=0.95))
    hnd = [Line2D([], [], color=FARG_VO, lw=3, label='Linje V–Ö (V och Ö sammanslagna, genomgående i centrum)'),
           Line2D([], [], color='#9a978f', lw=1.5, label='Övriga stadslinjer'),
           Line2D([], [], marker='*', ls='', color='#1c5cab', markersize=12, label='Ny hållplats vid flygterminalen'),
           Line2D([], [], marker='X', ls='', color=SAMRE, markersize=8, label='Hållplats som dras in (Solberget)'),
           Line2D([], [], marker='s', ls='', color='#1f1f1e', markersize=8, label='Byte V ↔ Ö i centrum'),
           Patch(facecolor=to_rgba(BATTRE, 0.75), label='Bättre turtäthetsklass än i dag'),
           Patch(facecolor=to_rgba(SAMRE, 0.75), label='Sämre turtäthetsklass än i dag')]
    lg = K.teckenforklaring(ax, hnd, loc='lower left', fontsize=7)
    lg.set_bbox_to_anchor((1.02, 0.0), transform=ax.transAxes)
    K.ram(ax)
    return K.spara(fig, 'b4_10_ua4_karta.png')


def fig_tackning_fore_efter(res):
    """Turtäthet inom 400 m före och efter, inzoomat per UA (rader) – förbättrade/försämrade celler markerade."""
    farg = KLASSFARG
    rader = [('1b', 'UA 1a och 1b Möckelö Strand ny', (104650, 107050, 6682750, 6685150),
              'UA 1a med V och Ö sammanslagna ger samma klass (17 avgångar);\nUA 1a med dagens tidtabell 9 avgångar (klass 1–14).'),
             ('2', 'UA 2 N2 på linje Ö', (109250, 111650, 6682050, 6684450), ''),
             ('3', 'UA 3 linje N via Bo-Bil', (106950, 109350, 6685150, 6687550), ''),
             ('4_VO_sol', 'UA 4 flygplatsen', (105500, 107900, 6685100, 6687500),
              'Huvudalternativet: V och Ö sammanslagna, Solberget\nindragen (20 avgångar vid flygplatsen, UA 4Y 8).'),
             ('4_VO_sol', 'UA 4 Solberget indragen', (109000, 111400, 6683600, 6686000),
              'Solberget dras in i huvudalternativet och i UA 4Y.')]
    fig, axs = plt.subplots(len(rader), 2, figsize=(11.6, 5.4 * len(rader)))
    for (sid, rub, uts, fot), (a0, a1) in zip(rader, axs):
        for ax, s_, t_ in [(a0, 'idag', f'{rub} – i dag'), (a1, sid, f'{rub} – med huvudalternativet')]:
            K.ny_karta(uts, ax=ax, titel=t_)
            rita_klasser(ax, s_)
            if s_ != 'idag':
                rita_forandring(ax, s_, fyll=0.25, kant=1.4, zorder=3)
            D.befolkning().boundary.plot(ax=ax, color='white', linewidth=0.35, alpha=0.8, zorder=2)
            ax.set_xlim(uts[0], uts[1]); ax.set_ylim(uts[2], uts[3]); ax.set_xlabel(''); ax.set_ylabel('')
            K.rita_linjer(ax, lw=1.6, alpha=0.9, zorder=4, etikett=False)
            if s_ != 'idag':
                rita_ua(ax, sid.split('_')[0])
            if s_ != 'idag':
                v = res[s_]; fi = v['forandring_invanare_mariehamn']; t0, t1 = res['idag']['tackning_mariehamn'], v['tackning_mariehamn']
                txt = [f"Bättre: {fi['battre_klass']} inv. (varav ny hållplats inom 400 m: {fi['ny_tackning']})",
                       f"Sämre: {fi['samre_klass']} inv. (varav utan hållplats: {fi['forlorad_tackning']})",
                       f"Mariehamn inom 400 m: {sv(100 * t0['inom_400m_andel'])} → {sv(100 * t1['inom_400m_andel'])} %",
                       f"Minst 30 avg./vardag: {sv(100 * t0['minst_30_avg_andel'])} → {sv(100 * t1['minst_30_avg_andel'])} %"]
                if fot:
                    txt.append(fot)
                ax.text(0.02, 0.98, '\n'.join(txt), transform=ax.transAxes, ha='left', va='top', fontsize=6.8,
                        color=K.TEXT, zorder=30, linespacing=1.5, wrap=True,
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#d6d5d0', lw=0.6, alpha=0.95))
            K.ram(ax)
    hnd = [Patch(facecolor=f, label=n) for f, (_, _, n) in zip(farg, KLASSER)]
    hnd += [Patch(facecolor='none', edgecolor=BATTRE, lw=1.2, label='Bättre klass än i dag'),
            Patch(facecolor='none', edgecolor=SAMRE, lw=1.2, label='Sämre klass än i dag'),
            Line2D([], [], marker='*', ls='', color='#1c5cab', markersize=11, label='Ny hållplats'),
            Line2D([], [], marker='X', ls='', color=SAMRE, markersize=8, label='Hållplats utgår för linjen'),
            Line2D([], [], color='#7a776f', lw=2, label='Ny körväg (linjens färg)'),
            Line2D([], [], color='#7a776f', lw=2, ls=(0, (3, 2)), label='Planerad väg'),
            Line2D([], [], color='#3d3d3a', lw=2, ls=(0, (1, 1.4)), label='Körväg som utgår')]
    hnd += [Line2D([], [], color=C.FARG_LINJE[l], lw=2, label=f'Linje {l}') for l in C.STADSLINJER]
    fig.legend(handles=hnd, loc='lower center', ncol=6, fontsize=7.2, frameon=False, bbox_to_anchor=(0.5, -0.012))
    fig.suptitle('Turtäthet inom 400 m (avgångar per vardag) – före och efter, huvudalternativet per UA', x=0.01, ha='left',
                 fontsize=12, fontweight='bold')
    fig.tight_layout(rect=(0, 0.035, 1, 0.985))
    ut = C.KARTOR / 'b4_14_tackning_fore_efter.png'
    fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


def main():
    for f in ['b4_10_systemeffekter.png', 'b4_11_tackning_fore_efter.png', 'b4_13_flygplatsen_vo.png',   # utgångna
              'b4_10_flygplatsen_karta.png']:
        (C.KARTOR / f).unlink(missing_ok=True)
    res = berakna()
    for f in (fig_vo, lambda r: fig_vo(r, '4'), fig_ua4_karta, fig_systemeffekter, fig_tackning_fore_efter):
        print(f(res))


if __name__ == '__main__':
    main()
