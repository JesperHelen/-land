# -*- coding: utf-8 -*-
"""UA 8 – stomsatsning: Jomalaringen (beställaren 2026-11-26: kreativt förslag till Jomala kyrkby; ett extra fordon
godtas om omloppen optimeras om; landskapsregeringen vill se en stomsatsning och en vision – linjen får vara en
slinga men ska täcka nya områden).

Jomalaringen (R/Q) är en ny ringlinje som binder ihop norra Mariehamn och södra Jomala:
  Centrum – Nabben – Kalmsta (Östras väg) – Österkalmare – Jomala skola – Jomala församlingshem – Vikingahallen
  – Dalkarby – Källarvägen – flygplatsen – Posten – Lönnhagsvägen – Möckelö Strand ny – Sviby bro – Västra macken
  – Centrum (Västras väg baklänges), 27 km, cirka 50 min.
Den nya norra bågen (12 km) går genom områden som i dag saknar stadsbuss: Österkalmare, Jomala skola och kyrkbyn,
och Dalkarby. Flygplatsen (UA 4) och Möckelö Strand ny (UA 1) ingår, så att bussen går runt en gång i timmen med
cirka 10 min reglering (en kortare ring på 35 min gav 25 min stillastående per timme och förkastades).
Byten: Centrum (pulsen :20/:50), Kalmsta (Östra), Källarvägen, Posten och Lönnhagsvägen (Västra), Västra macken
(nära Sjukhuset) och Jomala kyrkby (landsbygdslinjerna 1–6).
  Steg 1  medurs varje timme 06:20–20:20 (ett extra fordon).
  Steg 2  dessutom moturs varje timme 06:50–20:50 (två extra fordon).
Nya hållplatser antas längs bågen i bebyggelsen (cirka var 500:e meter); invånare inom 400 m från bågen, flygplatsen
och Möckelö Strand ny räknas.

Jämförelsevarianter (prövade först, redovisas i tabell):
  A  Linje Norra via Jomala kyrkby (alla 22 turer; Hjortronstigen → kyrkbyn → Maxinge).
  B  Jomalalinje på Norras gator (Centrum – Doktorsvägen – kyrkbyn – Maxinge – Sjukhuset – Centrum), genomgående
     med Järsö, varje timme, och Järsö timtrafik hela dagen.

  * Väglängd: dagens segment (OSRM) och nya delsträckor med OSRM, med körriktning (bearings) vid hållplatserna.
  * Körtid: nya delsträckor med Järsös tidtabellshastighet (landsväg, inkl. uppehåll), övrigt enligt tidtabellen.
  * Omlopp: b4_omlopp.bygg_omlopp (minsta antal fordon, normparen S ↔ N och Ö ↔ V, Järsö ↔ Jomala, ringens två
    riktningar). Byte mellan linjegrupperna straffas med BYTE_GRUPP_STRAFF, så att förarna växlar inom paren som i
    dag; fordonsantalet minimeras först. Avgångstiderna i centrum ligger fast.
  * Restid för dagens resenärer: OD-matrisen på restidsnätet (b4_natverk). Resor till och från de nya områdena
    finns inte i stadstrafikens data och ingår inte.
  * Täckning: invånare (50 m-punkter, a2_delpunkter) inom 400 m från den nya bågen som i dag har längre än 400 m
    till stadsbuss; avgångar per vardag alla linjer.
Utdata: data/processed/b4_ua8_jomala.json, output/kartor/b4_25_jomala_karta.png, b4_26_jomala_omlopp.png
"""
import json
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import kartlib as K  # noqa: E402

P = C.PROCESSED
HJ, MX, BB = '9025302000064101', '9025302000031201', '9025302000003502'
NORR = ['9025302000054302', '9025302000018502', '9025302000018702', '9025302000037802']   # Vikingahallen … Rönngården
SODER = ['9025302000037801', '9025302000018701', '9025302000018501', '9025302000054301']  # Rönngården … Vikingahallen
ARM = NORR + SODER
KYRKBY = {'Vikingahallen', 'Jomala församlingshem', 'Jomala kyrka', 'Rönngården'}
FARG_K = '#d62828'                    # Jomalalinjen (ny linje)
K_AVG = [h * 60 + 20 for h in range(6, 21)]              # Jomalalinjen varje timme 06:20–20:20
J_EXTRA = [10 * 60 + 50, 11 * 60 + 50, 18 * 60 + 20, 19 * 60 + 20]   # Järsö: luckan mitt på dagen och kvällen
BYTE_GRUPP_STRAFF = 30.0             # min – byte mellan linjegrupper (i stället för b4_omlopp:s 2 min)
GRUPP = {'N': 0, 'S': 0, 'V': 1, 'Ö': 1, 'J': 2, 'K': 2, 'R': 3, 'Q': 3}
FARG_R, FARG_Q = '#d62828', '#9d0208'  # Jomalaringen medurs / moturs
BAGE = ['9025302000067001', '9025302000018902', '9025302000018501', '9025302000054301']  # Österkalmare … Vikingahallen
R_AVG = [h * 60 + 20 for h in range(6, 21)]              # medurs 06:20–20:20 (steg 1)
Q_AVG = [h * 60 + 50 for h in range(6, 21)]              # moturs 06:50–20:50 (steg 2)


# ---------------------------------------------------------------- geometri
def _osrm(a, b, ba='', bb=''):
    import requests
    import s01_vagdragning as V
    from pyproj import Transformer
    till = Transformer.from_crs(C.CRS_METRISK, C.CRS_WGS84, always_xy=True)
    fran = Transformer.from_crs(C.CRS_WGS84, C.CRS_METRISK, always_xy=True)
    u = f'{V.OSRM_URL}/route/v1/driving/' + ';'.join('%.6f,%.6f' % till.transform(*p) for p in (a, b))
    r = requests.get(u, params={'overview': 'full', 'geometries': 'geojson', 'continue_straight': 'true',
                                'bearings': f'{ba};{bb}'}, timeout=30).json()
    c = np.array(r['routes'][0]['geometry']['coordinates']); time.sleep(0.3)
    X, Y = fran.transform(c[:, 0], c[:, 1])
    return np.column_stack([X, Y])


def armgeometri(fran_id):
    """Delsträckor fran_id → kyrkbyn (norrut) → vändning vid Rönngården → Maxinge (söderut)."""
    H = pd.read_csv(P / 'a2_hallplatser_avgangar.csv', index_col=0, dtype={'stop_id': str})
    bear = {fran_id: '0,60', MX: '180,45', **{s: '0,60' for s in NORR}, **{s: '180,60' for s in SODER}}
    sek = [fran_id] + ARM + [MX]
    return [_osrm(tuple(H.loc[a, ['x', 'y']]), tuple(H.loc[b, ['x', 'y']]), bear[a], bear[b])
            for a, b in zip(sek[:-1], sek[1:])], sek


# ---------------------------------------------------------------- beräkning
def berakna():
    import b4_natverk as N
    import b4_omlopp as O
    import b4_ua as F
    import data_las as D
    import s01_vagdragning as V
    sg = V.segmentgeometri(); L = V.langd
    t = O.turer()
    jt = t[t.linje == 'J']
    v_land = float(jt.km.sum() / jt.kortid.sum())                  # km/min, Järsös tidtabellshastighet
    zoner = list(pd.read_csv(P / 'a1_restider_min.csv', index_col=0).index)
    mon0 = N.monster(); nat0 = N.Nat(mon0, zoner); fak = N.dagsfaktor()
    om = D.hallplatsomraden()['omrade']
    n0 = max([m for m in mon0 if m['linje'] == 'N'], key=lambda m: len(m['turer']))
    s0 = list(n0['stopp']); i = s0.index(HJ); assert s0[i + 1] == MX
    arm, sek = armgeometri(HJ)
    arm_km = [L(g) / 1000 for g in arm]; arm_min = [k / v_land for k in arm_km]

    def effekt(mon1):
        j = N.jamfor(nat0, N.Nat(mon1, zoner))
        v = lambda k: round(float((j['FM'][k] + j['EM'][k]) / 2 * fak), 0)
        return {'resenarsminuter_vardag': v('resenarsminuter_h'), 'resor_langre_vardag': v('resor_langre_h'),
                'resor_kortare_vardag': v('resor_kortare_h')}

    def monster(base, stopp, akt):
        return {**base, 'stopp': tuple(stopp), 'zoner': tuple(om.reindex(stopp).fillna('?')), 'akt': np.array(akt)}

    # --- A: Norra via kyrkbyn (dagens riktning)
    stA = s0[:i + 1] + ARM + s0[i + 1:]
    aktA = list(n0['akt'][:i]) + arm_min + list(n0['akt'][i + 1:])
    monA = [m if m is not n0 else monster(n0, stA, aktA) for m in mon0]
    dA_min = float(sum(aktA) - sum(n0['akt']))
    dA_km = sum(arm_km) - L(sg[(HJ, MX)]) / 1000
    # A ovanpå UA 3 (redovisas)
    m3 = F.ua3_monster(mon0); n3 = next(m for m, m_ in zip(m3, mon0) if m is not m_)
    s3 = list(n3['stopp']); i3 = s3.index(BB)
    arm3, _ = armgeometri(BB)
    a3 = [L(g) / 1000 / v_land for g in arm3]
    monA3 = [m if m is not n3 else monster(n3, s3[:i3 + 1] + ARM + s3[i3 + 1:], list(n3['akt'][:i3]) + a3
                                           + list(n3['akt'][i3 + 1:])) for m in m3]
    # --- B: Jomalalinjen K
    u3 = json.load(open(P / 'b4_ua3_slinga.json', encoding='utf-8')); k3 = u3['stopp_ny'].index(MX)
    stK = s0[:i + 1] + ARM + u3['stopp_ny'][k3:]
    aktK = list(n0['akt'][:i]) + arm_min + u3['akt_ny'][k3:]
    geoK = [sg[(a, b)] for a, b in zip(s0[:i], s0[1:i + 1])] + arm + [np.array(g) for g in u3['geometri_ny'][k3:]]
    kK = sum(L(g) for g in geoK) / 1000; tK = float(sum(aktK))
    monB = mon0 + [{'linje': 'K', 'stopp': tuple(stK), 'zoner': tuple(om.reindex(stK).fillna('?')),
                    'akt': np.array(aktK), 'turer': []}]
    geoA = [sg[(a, b)] for a, b in zip(s0[:i], s0[1:i + 1])] + arm + \
        [sg[(a, b)] for a, b in zip(s0[i + 1:-1], s0[i + 2:])]

    # --- omlopp
    pl0 = O.omlopp_operator(t); nt0 = O.nyckeltal(pl0)
    O.ANNAT_BYTE_STRAFF = BYTE_GRUPP_STRAFF
    blandat = lambda pl: int(sum(1 for r in pl.itertuples() if r.nasta >= 0 and r.vand_efter <= 60
                                 and GRUPP[r.linje] != GRUPP[pl.linje.iloc[r.nasta]]))
    tA = t.copy(); n = tA.linje == 'N'
    tA.loc[n, 'kortid'] += dA_min; tA.loc[n, 'ank'] += dA_min; tA.loc[n, 'km'] += dA_km
    tA['delta'] = np.where(n, dA_min, 0.0)
    plA = O.bygg_omlopp(tA); ntA = O.nyckeltal(plA)
    jkm, jtid = float(jt.km.median()), float(jt.kortid.median())
    ny = pd.DataFrame([{'trip_id': f'K{a}', 'avg': a, 'linje': 'K', 'kortid': tK, 'km': kK} for a in K_AVG]
                      + [{'trip_id': f'JX{a}', 'avg': a, 'linje': 'J', 'kortid': jtid, 'km': jkm} for a in J_EXTRA])
    ny['ank'] = ny.avg + ny.kortid
    tB = pd.concat([t, ny], ignore_index=True).sort_values(['avg', 'linje']).reset_index(drop=True)
    par_b = O.NORMPAR + (('J', 'K'), ('K', 'J'))
    plB = O.bygg_omlopp(tB, par=par_b); ntB = O.nyckeltal(plB)
    tB0 = pd.concat([t, ny[ny.linje == 'K']], ignore_index=True).sort_values(['avg', 'linje']).reset_index(drop=True)
    ntB0 = O.nyckeltal(O.bygg_omlopp(tB0, par=par_b))
    genom = int(sum(1 for r in plB.itertuples() if r.nasta >= 0 and
                    {r.linje, plB.linje.iloc[r.nasta]} == {'J', 'K'} and r.vand_efter <= 15))

    # --- turtäthet i kyrkbyn
    H = pd.read_csv(P / 'a2_hallplatser_avgangar.csv', index_col=0, dtype={'stop_id': str})
    pkt = pd.read_csv(P / 'a2_delpunkter.csv.gz')
    hx = H.loc[ARM, ['x', 'y']].to_numpy()
    d = np.min(np.hypot(pkt.x.to_numpy()[:, None] - hx[:, 0], pkt.y.to_numpy()[:, None] - hx[:, 1]), axis=1)
    nara = pkt[d <= C.TACKNING_M]
    import tackningsytor as T
    kl = lambda a: np.array([T.klass(x) for x in a])
    def tack(extra):
        k0, k1 = kl(nara.avg_alla), kl(nara.avg_alla + extra)
        return {'invanare_400m': round(float(nara.bef.sum())), 'avgangar_idag': int(nara.avg_alla.median()),
                'avgangar_ny': int(nara.avg_alla.median() + extra),
                'invanare_battre_klass': round(float(nara.bef[k1 > k0].sum())),
                'invanare_minst_30_ny': round(float(nara.bef[(nara.avg_alla + extra) >= 30].sum())),
                'invanare_minst_30_idag': round(float(nara.bef[nara.avg_alla >= 30].sum()))}

    t_centrum_kyrka = float(sum(n0['akt'][:i]) + sum(arm_min[:3]))
    res = {
        'v_land_kmh': round(v_land * 60, 1),
        'landsbygd_idag': {'avgangar_per_riktning': 14, 'torget_jomala_kyrka_min': 13},
        'stadsbuss_centrum_jomala_kyrka_min': round(t_centrum_kyrka, 1),
        'idag': {'fordon': nt0['fordon'], 'km': nt0['km'], 'omloppstid_h': nt0['omloppstid_h'],
                 'byten_mellan_grupper': blandat(pl0)},
        'A': {'turer': int(n.sum()), 'varv_min_idag': round(float(sum(n0['akt'])), 1), 'varv_min': round(float(sum(aktA)), 1),
              'delta_min_per_tur': round(dA_min, 1), 'delta_km_per_tur': round(dA_km, 2),
              'fordon': ntA['fordon'], 'fler_fordon': ntA['fordon'] - nt0['fordon'],
              'fordonskm_vardag': round(ntA['km'] - nt0['km'], 1), 'omloppstid_h': ntA['omloppstid_h'],
              'vandningar_under_rek': ntA['vandningar_under_rek'], 'byten_enligt_norm': ntA['byten_enligt_norm'],
              'samma_linje': ntA['samma_linje'], 'byten_mellan_grupper': blandat(plA), **effekt(monA), 'tackning': tack(int(n.sum())),
              'centrum_maxinge_min': [round(float(sum(n0['akt'][:i + 1])), 1),
                                      round(float(sum(aktA[:i + 1 + len(ARM)])), 1)],
              'ovanpa_ua3': effekt(monA3)},
        'B': {'turer_K': len(K_AVG), 'turer_J_extra': len(J_EXTRA), 'kortid_K_min': round(tK, 1), 'km_K': round(kK, 2),
              'fordon': ntB['fordon'], 'fler_fordon': ntB['fordon'] - nt0['fordon'],
              'fordonskm_vardag': round(ntB['km'] - nt0['km'], 1), 'omloppstid_h': ntB['omloppstid_h'],
              'utan_jarso_extra': {'fordon': ntB0['fordon'], 'fordonskm_vardag': round(ntB0['km'] - nt0['km'], 1)},
              'genomgaende_jarso_jomala': genom, 'byten_mellan_grupper': blandat(plB),
              'bussar_jarso_jomala': int(plB.groupby('buss').linje.agg(lambda x: set(x) <= {'J', 'K'}).sum()),
              'vandningar_under_rek': ntB['vandningar_under_rek'],
              **effekt(monB), 'tackning': tack(len(K_AVG))},
    }
    for x in ('A', 'B'):
        res[x]['fordonskm_ar'] = int(round(res[x]['fordonskm_vardag'] * 250 + 5 * 52 * (
            res['A']['delta_km_per_tur'] if x == 'A' else res['B']['km_K']), -2))

    # --- Jomalaringen: Centrum – Kalmsta – norra bågen – Källarvägen – flygplatsen – Posten – Möckelö Strand ny –
    #     Sviby bro – Västra macken – Centrum (medurs)
    lm = V.monster_per_linje(); fg = V.uageometri(); xyv = V.alla_xy()[0]
    oo = list(lm['Ö'][0][0])
    nv = max([m for m in mon0 if m['linje'] == 'V'], key=lambda m: len(m['turer'])); vs = list(nv['stopp'])
    no = max([m for m in mon0 if m['linje'] == 'Ö'], key=lambda m: len(m['turer']))
    kal, kv, po, nog = oo[2], '9025302000025902', '9025302000035802', '9025302000067701'
    assert vs[10] == po and vs[11] == kv and nog in (vs[6], vs[8])
    bear = {s_: '180,60' for s_ in BAGE[2:]}; bear[kv] = '180,60'
    bseq = [kal] + BAGE + [kv]
    bage = [_osrm(tuple(H.loc[a, ['x', 'y']]), tuple(H.loc[b, ['x', 'y']]), bear.get(a, ''), bear.get(b, ''))
            for a, b in zip(bseq[:-1], bseq[1:])]
    rev = lambda a, b: sg[(a, b)][::-1]
    ua4 = json.load(open(P / 'b4_ua.json', encoding='utf-8'))['ua']['4']['delta_min_per_tur']
    t_flyg = ua4 + float(nv['akt'][10])                      # Posten – flygplatsen – Källarvägen (UA 4)
    delar = ([(oo[k], oo[k + 1], sg[(oo[k], oo[k + 1])], float(no['akt'][k])) for k in range(2)]
             + [(a, b, g_, L(g_) / 1000 / v_land) for (a, b), g_ in zip(zip(bseq[:-1], bseq[1:]), bage)]
             + [(kv, 'FLYGPLATSEN', fg[('FLYGPLATSEN', kv)]['xy'][::-1], t_flyg / 2),
                ('FLYGPLATSEN', po, fg[(po, 'FLYGPLATSEN')]['xy'][::-1], t_flyg / 2),
                (po, vs[9], rev(vs[9], vs[10]), float(nv['akt'][9])),
                (vs[9], vs[8], rev(vs[8], vs[9]), float(nv['akt'][8])),
                (vs[8], 'NY_MOCKELO', fg[(nog, 'NY_MOCKELO')]['xy'], 2.0 + 0.5),
                ('NY_MOCKELO', vs[6], fg[('NY_MOCKELO', nog)]['xy'], 2.0),
                (vs[6], vs[5], rev(vs[5], vs[6]), float(nv['akt'][5])),
                (vs[5], vs[4], rev(vs[4], vs[5]), float(nv['akt'][4])),
                (vs[4], vs[18], rev(vs[3], vs[4]), float(nv['akt'][3]))]
             + [(vs[k], vs[k + 1], sg[(vs[k], vs[k + 1])], float(nv['akt'][k])) for k in range(18, len(vs) - 1)])
    geoR = [d_[2] for d_ in delar]
    stR = [delar[0][0]] + [d_[1] for d_ in delar]
    aktR = [d_[3] for d_ in delar]
    kmR = sum(L(g) for g in geoR) / 1000; km_bage = sum(L(g) for g in bage) / 1000
    tR = float(sum(aktR))
    pR = {'linje': 'R', 'stopp': tuple(stR), 'zoner': tuple(om.reindex(stR).fillna('?')), 'akt': np.array(aktR),
          'turer': []}
    pQ = {**pR, 'linje': 'Q', 'stopp': tuple(stR[::-1]), 'zoner': tuple(om.reindex(stR[::-1]).fillna('?')),
          'akt': np.array(aktR[::-1])}
    par_r = O.NORMPAR + (('R', 'Q'), ('Q', 'R'))
    def ringturer(cw, ccw):
        d_ = pd.DataFrame([{'trip_id': f'R{a}', 'avg': a, 'linje': 'R'} for a in cw]
                          + [{'trip_id': f'Q{a}', 'avg': a, 'linje': 'Q'} for a in ccw])
        d_['kortid'] = tR; d_['km'] = kmR; d_['ank'] = d_.avg + tR
        return pd.concat([t, d_], ignore_index=True).sort_values(['avg', 'linje']).reset_index(drop=True)
    plR1 = O.bygg_omlopp(ringturer(R_AVG, []), par=par_r); nR1 = O.nyckeltal(plR1)
    plR2 = O.bygg_omlopp(ringturer(R_AVG, Q_AVG), par=par_r); nR2 = O.nyckeltal(plR2)
    # nya områden: inom 400 m från bågen, i dag längre än 400 m till stadsbuss
    from scipy.spatial import cKDTree
    stad = H[H.linjer.astype(str).str.contains('|'.join(C.STADSLINJER))]
    d_stad, _ = cKDTree(stad[['x', 'y']].to_numpy()).query(pkt[['x', 'y']].to_numpy())
    bxy = np.vstack(bage + [np.array([V.FLYGPLATSEN_XY, xyv['NY_MOCKELO'][:2]])])
    d_bage, _ = cKDTree(bxy).query(pkt[['x', 'y']].to_numpy())
    nya = pkt[(d_bage <= C.TACKNING_M) & (d_stad > C.TACKNING_M)]
    langs = pkt[d_bage <= C.TACKNING_M]
    def ringtack(extra):
        return {'invanare_far_stadsbuss': round(float(nya.bef.sum())),
                'invanare_langs_bagen': round(float(langs.bef.sum())),
                'invanare_battre_klass': round(float(langs.bef[kl(langs.avg_alla + extra) > kl(langs.avg_alla)].sum())),
                'invanare_minst_30_ny': round(float(langs.bef[(langs.avg_alla + extra) >= 30].sum())),
                'invanare_minst_30_idag': round(float(langs.bef[langs.avg_alla >= 30].sum()))}
    ar = lambda dag, n_lor: int(round(dag * 250 + 5 * n_lor * 52 * kmR, -2))
    res['R'] = {'km_ring': round(kmR, 1), 'km_bage': round(km_bage, 1), 'kortid_min': round(tR, 1),
                'hallplatser': [H.loc[x, 'namn'] if x in H.index else x for x in stR],
                'reglering_per_varv_min': round(60 - tR, 1), 'andel_kortid': round(tR / 60 * 100, 0),
                'steg1': {'turer': len(R_AVG), 'fordon': nR1['fordon'], 'fler_fordon': nR1['fordon'] - nt0['fordon'],
                          'fordonskm_vardag': round(nR1['km'] - nt0['km'], 1), 'omloppstid_h': nR1['omloppstid_h'],
                          'byten_mellan_grupper': blandat(plR1), **effekt(mon0 + [pR]),
                          'tackning': ringtack(len(R_AVG))},
                'steg2': {'turer': len(R_AVG) + len(Q_AVG), 'fordon': nR2['fordon'],
                          'fler_fordon': nR2['fordon'] - nt0['fordon'],
                          'fordonskm_vardag': round(nR2['km'] - nt0['km'], 1), 'omloppstid_h': nR2['omloppstid_h'],
                          'byten_mellan_grupper': blandat(plR2), **effekt(mon0 + [pR, pQ]),
                          'tackning': ringtack(len(R_AVG) + len(Q_AVG))}}
    res['R']['steg1']['fordonskm_ar'] = ar(res['R']['steg1']['fordonskm_vardag'], 1)
    res['R']['steg2']['fordonskm_ar'] = ar(res['R']['steg2']['fordonskm_vardag'], 2)
    res['R']['andel_av_idag_ar'] = {k: round(res['R'][k]['fordonskm_ar'] / 342000 * 100, 0) for k in ('steg1', 'steg2')}
    json.dump(res, open(P / 'b4_ua8_jomala.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
    return res, geoR, bage, nya, pl0, plR1, plR2


# ---------------------------------------------------------------- figurer
def _rita_linje(ax, delar, farg, uts, steg=420, lw=3.0):
    for d in K.sammanfoga(delar, tol=60):
        ax.plot(d[:, 0], d[:, 1], color=farg, lw=lw, solid_capstyle='round', solid_joinstyle='round', zorder=5,
                path_effects=[K.pe.Stroke(linewidth=lw + 2.2, foreground='white'), K.pe.Normal()])
        Lc = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(d, axis=0).T))])
        for dist in np.arange(steg / 2, Lc[-1], steg):
            j = min(max(int(np.searchsorted(Lc, dist)), 1), len(d) - 1)
            a, b = d[j - 1], d[j]
            if np.hypot(*(b - a)) > 0.5 and uts[0] + 60 < b[0] < uts[1] - 60 and uts[2] + 60 < b[1] < uts[3] - 60:
                ax.annotate('', xy=tuple(b), xytext=tuple(a), zorder=6,
                            arrowprops=dict(arrowstyle='-|>', color='#2b1838', lw=0, mutation_scale=11))


def karta(geoR, bage, nya):
    H = pd.read_csv(P / 'a2_hallplatser_avgangar.csv', index_col=0, dtype={'stop_id': str})
    uts = (104700, 111900, 6682900, 6690000)
    fig, ax = plt.subplots(figsize=(10.6, 10.6))
    K.ny_karta(uts, ax=ax, titel='UA 8 – Jomalaringen')
    ax.scatter(nya.x, nya.y, s=3, color=FARG_R, alpha=0.18, lw=0, zorder=1.5)
    K.rita_linjer(ax, alpha=0.45, lw=1.5, zorder=3, etikett=False)
    _rita_linje(ax, geoR, FARG_R, uts, steg=650, lw=3.4)
    for d in K.sammanfoga(geoR, tol=60):                     # moturs (steg 2): pilar åt andra hållet, förskjutna
        r = d[::-1]
        Lc = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(r, axis=0).T))])
        for dist in np.arange(325, Lc[-1], 650):
            j = min(max(int(np.searchsorted(Lc, dist)), 1), len(r) - 1)
            a, b = r[j - 1], r[j]
            if np.hypot(*(b - a)) > 0.5 and uts[0] + 60 < b[0] < uts[1] - 60 and uts[2] + 60 < b[1] < uts[3] - 60:
                ax.annotate('', xy=tuple(b), xytext=tuple(a), zorder=6,
                            arrowprops=dict(arrowstyle='-|>', color='#8a8780', lw=0, mutation_scale=10))
    namn = ['Centrum, Nygatan', 'Nabben', 'Kalmsta', 'Österkalmare', 'Jomala skola', 'Vikingahallen', 'Jomala kyrka',
            'Källarvägen', 'Posten', 'Sviby bro', 'Västra macken', 'Maxinge', 'Lönnhagsvägen']
    g = H[H.namn.isin(namn) & H.x.between(*uts[:2]) & H.y.between(*uts[2:])].groupby('namn')[['x', 'y']].mean()
    ax.scatter(g.x, g.y, s=20, facecolor='white', edgecolor='#1f1f1e', lw=0.8, zorder=7)
    import s01_vagdragning as V
    xyv = V.alla_xy()[0]
    extra = {'Flygplatsen': V.FLYGPLATSEN_XY, 'Möckelö Strand ny': xyv['NY_MOCKELO'][:2]}
    ax.scatter([p_[0] for p_ in extra.values()], [p_[1] for p_ in extra.values()], s=150, marker='*', color='#1c5cab',
               edgecolor='white', lw=0.8, zorder=8)
    K.placera_etiketter(ax, [(n.replace('Centrum, Nygatan', 'Centrum'), (r.x, r.y), 40) for n, r in g.iterrows()]
                        + [(n, p_, 60) for n, p_ in extra.items()],
                        fontsize=6.9, undvik=K.punkt_hinder(ax, g.x, g.y, px=6))
    K.skalstock(ax, langd_m=1000, loc=(0.05, 0.03))
    hnd = [Line2D([], [], color=FARG_R, lw=3.4, label='Jomalaringen'),
           Line2D([], [], color='#2b1838', lw=0, marker='$→$', markersize=9, label='Medurs (steg 1)'),
           Line2D([], [], color='#8a8780', lw=0, marker='$→$', markersize=9, label='Moturs (steg 2)'),
           Line2D([], [], color='#8a8780', lw=1.5, alpha=0.6, label='Stadslinjer i dag'),
           Line2D([], [], marker='*', ls='', color='#1c5cab', markeredgecolor='white', markersize=11,
                  label='Flygplatsen och Möckelö Strand ny'),
           Patch(facecolor=FARG_R, alpha=0.25, label='Nya områden med stadsbuss')]
    K.teckenforklaring(ax, hnd, loc='lower right')
    return K.spara(fig, 'b4_25_jomala_karta.png')


def omloppsfigur(pl0, plR1, plR2):
    import b4_omlopp as O
    C.FARG_LINJE.setdefault('R', FARG_R); C.FARG_LINJE.setdefault('Q', FARG_Q)
    O.BOKSTAV.setdefault('Q', 'R')
    fig, axs = plt.subplots(3, 1, figsize=(11.4, 9.8), gridspec_kw={'height_ratios': [5, 6, 7]})
    O.rita_omlopp(axs[0], pl0, titel='I dag – 5 bussar', t0=6 * 60 + 10)
    O.rita_omlopp(axs[1], plR1.assign(omlopp=np.nan), titel=f'Steg 1 – Jomalaringen medurs varje timme: '
                  f'{plR1.buss.nunique()} bussar', t0=6 * 60 + 10)
    O.rita_omlopp(axs[2], plR2.assign(omlopp=np.nan), titel=f'Steg 2 – Jomalaringen åt båda hållen varje timme: '
                  f'{plR2.buss.nunique()} bussar', t0=6 * 60 + 10)
    O.omlopp_forklaring(fig, extra=[Patch(facecolor=FARG_R, label='Jomalaringen medurs (R)'),
                                    Patch(facecolor=FARG_Q, label='Jomalaringen moturs (R)')])
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    ut = C.KARTOR / 'b4_26_jomala_omlopp.png'
    K.fullnamn_fig(fig); fig.savefig(ut, dpi=200, bbox_inches='tight'); plt.close(fig)
    return ut


if __name__ == '__main__':
    r, geoR, bage, nya, pl0, plR1, plR2 = berakna()
    print(json.dumps({k: v for k, v in r.items()}, ensure_ascii=False, indent=1, default=float))
    print(karta(geoR, bage, nya)); print(omloppsfigur(pl0, plR1, plR2))
