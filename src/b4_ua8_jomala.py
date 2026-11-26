# -*- coding: utf-8 -*-
"""UA 8 – stadsbuss till Jomala kyrkby (beställaren 2026-11-26: kreativt förslag, ett extra fordon godtas om
omloppen optimeras om).

Jomala kyrkby ligger cirka 2,7 km norr om Maxinge längs Godbyvägen. I dag trafikeras orten bara av
landsbygdslinjerna 2–4 (14 avgångar per vardag och riktning, oregelbundna tider; Torget – Jomala kyrka cirka 13 min).
Hållplatser i kyrkbyn (norrut / söderut): Vikingahallen, Jomala församlingshem, Jomala kyrka och Rönngården; bussen
vänder norr om Rönngården.

  A  Linje Norra via Jomala kyrkby. Alla 22 turer: efter Hjortronstigen kör Norra Nya Godbyvägen norrut till
     kyrkbyn, vänder vid Rönngården och kommer söderut till Maxinge (hållplatsen på västra sidan nås i rätt
     riktning). Därefter som i dag (Vikingagränd – Bolstavägen – Hindersböle – Nabben – Sjukhuset – Centrum).
     Varianten ovanpå UA 3 (norra slingan baklänges) prövas också; den ger längre restid och redovisas bara.
  B  Ny Jomalalinje (K), genomgående med Järsö. Centrum – Polishuset – Doktorsvägen – Hjortronstigen – Jomala
     kyrkby – Maxinge – Sjukhuset – Yrkesgymnasiet – Centrum, varje timme 06:20–20:20. Bussarna kör Järsö och
     Jomala om vartannat, så att resenärer från Järsö kan sitta kvar genom centrum mot Jomala. Med extrabussens
     lediga tid blir Järsö också timtrafik mitt på dagen och på kvällen (fyra extra turer). Norra som i dag.

  * Väglängd: dagens segment (OSRM) och nya delsträckor med OSRM, med körriktning (bearings) vid hållplatserna.
  * Körtid: nya delsträckor med Järsös tidtabellshastighet (landsväg, inkl. uppehåll), övrigt enligt tidtabellen.
  * Omlopp: b4_omlopp.bygg_omlopp (minsta antal fordon, normparen S ↔ N och Ö ↔ V, i B även Järsö ↔ Jomala).
    Byte mellan linjegrupperna (Norra/Södra, Västra/Östra, Järsö/Jomala) straffas med BYTE_GRUPP_STRAFF, så att
    förarna växlar inom paren som i dag; fordonsantalet minimeras först. Avgångstiderna i centrum ligger fast;
    A förlänger Norras turer, B lägger till turer.
  * Restid för dagens resenärer: OD-matrisen på restidsnätet (b4_natverk). Resor till och från kyrkbyn finns inte
    i stadstrafikens data och ingår inte.
  * Turtäthet: invånare (50 m-punkter, a2_delpunkter) inom 400 m från kyrkbyns hållplatser, avgångar alla linjer.
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
GRUPP = {'N': 0, 'S': 0, 'V': 1, 'Ö': 1, 'J': 2, 'K': 2}


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
    json.dump(res, open(P / 'b4_ua8_jomala.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
    return res, geoA, geoK, pl0, plA, plB, tA


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


def karta(geoA, geoK):
    H = pd.read_csv(P / 'a2_hallplatser_avgangar.csv', index_col=0, dtype={'stop_id': str})
    import s01_vagdragning as V
    uts = (106900, 110100, 6682700, 6690500)
    fig, axs = plt.subplots(1, 2, figsize=(11.6, 12.2))
    ovr = V.segmentgeometri()
    for ax, titel, geo, farg in ((axs[0], 'A – Norra via Jomala kyrkby', geoA, C.FARG_LINJE['N']),
                                 (axs[1], 'B – Jomalalinjen, genomgående med Järsö', geoK, FARG_K)):
        K.ny_karta(uts, ax=ax, titel=titel)
        K.rita_linjer(ax, alpha=0.35, lw=1.4, zorder=3, etikett=False)
        _rita_linje(ax, geo, farg, uts)
        stopp = [s for s in H.index if H.loc[s, 'namn'] in KYRKBY]
        h = H.loc[stopp]
        ax.scatter(h.x, h.y, s=22, facecolor='white', edgecolor='#1f1f1e', lw=0.8, zorder=7)
        namn = ['Vikingahallen', 'Jomala kyrka', 'Rönngården', 'Maxinge', 'Sjukhuset', 'Centrum, Nygatan',
                'Bo-Bil', 'Doktorsvägen 1A', 'Polishuset']
        g = H[H.namn.isin(namn) & H.x.between(*uts[:2]) & H.y.between(*uts[2:])].groupby('namn')[['x', 'y']].mean()
        ax.scatter(g.x, g.y, s=18, facecolor='white', edgecolor='#1f1f1e', lw=0.7, zorder=7)
        K.placera_etiketter(ax, [(n.replace('Centrum, Nygatan', 'Centrum'), (r.x, r.y), 40) for n, r in g.iterrows()],
                            fontsize=6.8, undvik=K.punkt_hinder(ax, list(h.x) + list(g.x), list(h.y) + list(g.y), px=6))
    K.skalstock(axs[0], langd_m=1000, loc=(0.06, 0.03))
    hnd = [Line2D([], [], color=C.FARG_LINJE['N'], lw=3, label='Norra via Jomala kyrkby (A)'),
           Line2D([], [], color=FARG_K, lw=3, label='Jomalalinjen (B)'),
           Line2D([], [], color='#8a8780', lw=1.4, alpha=0.6, label='Övriga stadslinjer i dag'),
           Line2D([], [], color='#2b1838', lw=0, marker='$→$', markersize=9, label='Körriktning')]
    K.teckenforklaring(axs[1], hnd, loc='lower right')
    fig.tight_layout()
    return K.spara(fig, 'b4_25_jomala_karta.png')


def omloppsfigur(pl0, plA, plB, tA):
    import b4_omlopp as O
    C.FARG_LINJE.setdefault('K', FARG_K)
    O.BOKSTAV.setdefault('K', 'K')
    fig, axs = plt.subplots(3, 1, figsize=(11.4, 9.6), gridspec_kw={'height_ratios': [5, 6, 6]})
    O.rita_omlopp(axs[0], pl0, titel='I dag – 5 bussar', t0=6 * 60 + 10)
    O.rita_omlopp(axs[1], plA.assign(omlopp=np.nan), titel=f'A – Norra via Jomala kyrkby: {plA.buss.nunique()} bussar',
                  andrade=set(tA[tA.linje == 'N'].trip_id), t0=6 * 60 + 10)
    O.rita_omlopp(axs[2], plB.assign(omlopp=np.nan), titel=f'B – Jomalalinjen (K) och Järsö: {plB.buss.nunique()} bussar', t0=6 * 60 + 10)
    O.omlopp_forklaring(fig, extra=[Patch(facecolor=FARG_K, label='Jomalalinjen (K)')])
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    ut = C.KARTOR / 'b4_26_jomala_omlopp.png'
    K.fullnamn_fig(fig); fig.savefig(ut, dpi=200, bbox_inches='tight'); plt.close(fig)
    return ut


if __name__ == '__main__':
    r, geoA, geoK, pl0, plA, plB, tA = berakna()
    print(json.dumps(r, ensure_ascii=False, indent=1, default=float))
    print(karta(geoA, geoK)); print(omloppsfigur(pl0, plA, plB, tA))
