# -*- coding: utf-8 -*-
"""UA 8 – Jomalapendeln: stadsbuss mellan Mariehamn och Jomala kyrkby (beställaren 2026-11-26).

Problemet: invånarna i Jomala kyrkby kan inte på ett användbart sätt åka kollektivt till Mariehamn och tillbaka.
Landsbygdslinjerna 2–4 går 14 gånger per vardag och riktning på oregelbundna tider. Vesterkalmare och Österkalmare
saknar kollektivtrafik nästan helt. Ett extra fordon godtas, om omloppen optimeras om. Slingan ska ta under 27 min,
så att en buss kan köra varje halvtimme.

  A  Jomalapendeln: Centrum, Nygatan – Nya Godbyvägen (utan uppehåll) – Dalkarbyvägen – Vikingahallen – Jomala
     församlingshem – Jomala kyrka (vänder) – Jomala församlingshem – Vikingahallen – Dalkarbyvägen – Maxinge
     (hållplatsen på västra sidan, söderut) – Centrum. Varje halvtimme 06:20–20:50 med ett fordon.
  B  Som A, men varannan tur kör hem via Jomala skola – Vesterkalmare (ny hållplats) – Nabben – Centrum.
     Kyrkbyn får två turer i timmen (ojämnt intervall) och Vesterkalmare en.

  * Väglängd och körtid: OSRM per delsträcka mellan hållplatserna, med körriktning (bearings). Busstid = OSRM-tid
    × 1,05 + 0,3 min per uppehåll (kalibrerat mot Norra och Järsö: OSRM 26,9 respektive 45,3 min mot tidtabellens
    26 respektive cirka 48 min).
  * Omlopp: b4_omlopp.bygg_omlopp (minsta antal fordon; byte mellan linjegrupper straffas så att förarna växlar inom
    paren som i dag). Avgångstiderna i centrum ligger fast.
  * Restid för dagens resenärer: OD-matrisen på restidsnätet (b4_natverk). Resor till och från kyrkbyn och
    Kalmare finns inte i stadstrafikens data och ingår inte.
  * Täckning: invånare (50 m-punkter, a2_delpunkter) inom 400 m från de nya hållplatserna; avgångar alla linjer.
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
CEN, MX, NAB = '9025302000066201', '9025302000031201', '9025302000032401'
DKN, DKS = '9025302000006401', '9025302000006402'          # Dalkarbyvägen norrut / söderut
VHN, VHS = '9025302000054302', '9025302000054301'          # Vikingahallen
FHN, FHS = '9025302000018502', '9025302000018501'          # Jomala församlingshem
JKN, JKS = '9025302000018702', '9025302000018701'          # Jomala kyrka
JS = '9025302000018902'                                     # Jomala skola
VK = 'VESTERKALMARE'; VK_XY = (110068.0, 6686171.0)        # ny hållplats (byns mitt enligt OSM)
BEAR = {DKN: '0,60', VHN: '0,60', FHN: '0,60', JKN: '0,60', JKS: '180,60', FHS: '180,60', VHS: '180,60', DKS: '180,60', MX: '180,45'}
DIREKT = [CEN, DKN, VHN, FHN, JKN, JKS, FHS, VHS, DKS, MX, CEN]
KALMARE = [CEN, DKN, VHN, FHN, FHS, JS, VK, NAB, CEN]
OSRM_FAKTOR, UPPEHALL = 1.05, 0.3
AVG_A = [h * 60 + m for h in range(6, 21) for m in (20, 50)]           # varje halvtimme 06:20–20:50
FARG_P, FARG_K = '#d62828', '#9d0208'
BYTE_GRUPP_STRAFF = 30.0
GRUPP = {'N': 0, 'S': 0, 'V': 1, 'Ö': 1, 'J': 2, 'P': 3, 'K': 3}


def _xy(s, H):
    return VK_XY if s == VK else tuple(H.loc[s, ['x', 'y']])


def _osrm(a, b, ba='', bb=''):
    import requests
    import s01_vagdragning as V
    from pyproj import Transformer
    till = Transformer.from_crs(C.CRS_METRISK, C.CRS_WGS84, always_xy=True)
    fran = Transformer.from_crs(C.CRS_WGS84, C.CRS_METRISK, always_xy=True)
    u = f'{V.OSRM_URL}/route/v1/driving/' + ';'.join('%.6f,%.6f' % till.transform(*p) for p in (a, b))
    r = requests.get(u, params={'overview': 'full', 'geometries': 'geojson', 'continue_straight': 'true',
                                'bearings': f'{ba};{bb}'}, timeout=30).json()
    rt = r['routes'][0]; c = np.array(rt['geometry']['coordinates']); time.sleep(0.3)
    X, Y = fran.transform(c[:, 0], c[:, 1])
    return np.column_stack([X, Y]), rt['distance'] / 1000, rt['duration'] / 60


def rutt(seq, H):
    """Delsträckor: (geometri, km, busstid min)."""
    ut = []
    for a, b in zip(seq[:-1], seq[1:]):
        g, km, t = _osrm(_xy(a, H), _xy(b, H), BEAR.get(a, ''), BEAR.get(b, ''))
        ut.append((g, km, t * OSRM_FAKTOR + UPPEHALL))
    return ut


def berakna():
    import b4_natverk as N
    import b4_omlopp as O
    import data_las as D
    import tackningsytor as T
    from scipy.spatial import cKDTree
    H = pd.read_csv(P / 'a2_hallplatser_avgangar.csv', index_col=0, dtype={'stop_id': str})
    t = O.turer()
    zoner = list(pd.read_csv(P / 'a1_restider_min.csv', index_col=0).index)
    mon0 = N.monster(); nat0 = N.Nat(mon0, zoner); fak = N.dagsfaktor()
    om = D.hallplatsomraden()['omrade']
    rA, rB = rutt(DIREKT, H), rutt(KALMARE, H)
    kmA, tA = sum(x[1] for x in rA), sum(x[2] for x in rA)
    kmB, tB = sum(x[1] for x in rB), sum(x[2] for x in rB)

    def monster(seq, r, lin):
        return {'linje': lin, 'stopp': tuple(seq), 'zoner': tuple(om.reindex(seq).fillna('?')),
                'akt': np.array([x[2] for x in r]), 'turer': []}

    def effekt(extra):
        j = N.jamfor(nat0, N.Nat(mon0 + extra, zoner))
        v = lambda k: round(float((j['FM'][k] + j['EM'][k]) / 2 * fak), 0)
        return {'resenarsminuter_vardag': v('resenarsminuter_h'), 'resor_kortare_vardag': v('resor_kortare_h'),
                'resor_langre_vardag': v('resor_langre_h')}

    # --- omlopp
    O.ANNAT_BYTE_STRAFF = BYTE_GRUPP_STRAFF
    pl0 = O.omlopp_operator(t); nt0 = O.nyckeltal(pl0)

    def omlopp(nya):
        d_ = pd.DataFrame(nya); d_['ank'] = d_.avg + d_.kortid
        tt = pd.concat([t, d_], ignore_index=True).sort_values(['avg', 'linje']).reset_index(drop=True)
        pl = O.bygg_omlopp(tt, par=O.NORMPAR)
        return pl, O.nyckeltal(pl)
    plA, ntA = omlopp([{'trip_id': f'P{a}', 'avg': a, 'linje': 'P', 'kortid': tA, 'km': kmA} for a in AVG_A])
    # B: varannan tur via Vesterkalmare. Kalmareturen avgår :20 och den direkta :52 (kalmareturen tar mer än 30 min)
    avg_b = [(h * 60 + 20, 'K') for h in range(6, 21)] + [(h * 60 + 52, 'P') for h in range(6, 21)]
    plB, ntB = omlopp([{'trip_id': f'{l}{a}', 'avg': a, 'linje': l, 'kortid': tB if l == 'K' else tA,
                        'km': kmB if l == 'K' else kmA} for a, l in avg_b])

    # --- täckning
    pkt = pd.read_csv(P / 'a2_delpunkter.csv.gz')
    stad = H[H.linjer.astype(str).str.contains('|'.join(C.STADSLINJER))]
    d_stad, _ = cKDTree(stad[['x', 'y']].to_numpy()).query(pkt[['x', 'y']].to_numpy())
    kl = lambda a: np.array([T.klass(x) for x in a])

    def tack(stopp, n_turer):
        xy = np.array([_xy(s, H) for s in stopp])
        d, _ = cKDTree(xy).query(pkt[['x', 'y']].to_numpy())
        m = d <= C.TACKNING_M
        nara = pkt[m]; ny = pkt[m & (d_stad > C.TACKNING_M)]
        return {'invanare_400m': round(float(nara.bef.sum())), 'invanare_utan_stadsbuss_idag': round(float(ny.bef.sum())),
                'avgangar_idag': int(nara.avg_alla.median()), 'avgangar_ny': int(nara.avg_alla.median() + n_turer),
                'invanare_battre_klass': round(float(nara.bef[kl(nara.avg_alla + n_turer) > kl(nara.avg_alla)].sum())),
                'invanare_minst_30_ny': round(float(nara.bef[(nara.avg_alla + n_turer) >= 30].sum())),
                'invanare_minst_30_idag': round(float(nara.bef[nara.avg_alla >= 30].sum()))}
    blandat = lambda pl: int(sum(1 for r in pl.itertuples() if r.nasta >= 0 and r.vand_efter <= 60
                                 and GRUPP[r.linje] != GRUPP[pl.linje.iloc[r.nasta]]))
    i_fh = DIREKT.index(JKN)
    res = {
        'problem': {'landsbygd_avgangar_per_riktning': 14, 'torget_jomala_kyrka_min': 13},
        'idag': {'fordon': nt0['fordon'], 'km': nt0['km']},
        'A': {'tur_km': round(kmA, 1), 'tur_min': round(tA, 1), 'reglering_per_halvtimme': round(30 - tA, 1),
              'centrum_kyrkbyn_min': round(sum(x[2] for x in rA[:i_fh]), 1),
              'kyrkbyn_centrum_min': round(sum(x[2] for x in rA[i_fh + 1:]), 1),
              'maxinge_centrum_min': round(rA[-1][2], 1),
              'turer': len(AVG_A), 'fordon': ntA['fordon'], 'fler_fordon': ntA['fordon'] - nt0['fordon'],
              'fordonskm_vardag': round(ntA['km'] - nt0['km'], 1), 'byten_mellan_grupper': blandat(plA),
              **effekt([monster(DIREKT, rA, 'P')]),
              'tackning_kyrkbyn': tack([DKN, VHN, FHN, JKN], len(AVG_A))},
        'B': {'tur_kalmare_km': round(kmB, 1), 'tur_kalmare_min': round(tB, 1),
              'reglering_per_timme': round(60 - tA - tB, 1),
              'turer_direkt': 15, 'turer_kalmare': 15, 'fordon': ntB['fordon'], 'fler_fordon': ntB['fordon'] - nt0['fordon'],
              'fordonskm_vardag': round(ntB['km'] - nt0['km'], 1), 'byten_mellan_grupper': blandat(plB),
              **effekt([monster(DIREKT, rA, 'P'), monster(KALMARE, rB, 'K')]),
              'tackning_kyrkbyn': tack([DKN, VHN, FHN, JKN], 30), 'tackning_vesterkalmare': tack([VK], 15)},
    }
    for x, km_tur in (('A', kmA), ('B', (kmA + kmB) / 2)):
        res[x]['fordonskm_ar'] = int(round(res[x]['fordonskm_vardag'] * 250 + 10 * 52 * km_tur, -2))
        res[x]['andel_av_idag_ar'] = round(res[x]['fordonskm_ar'] / 342000 * 100, 0)
    json.dump(res, open(P / 'b4_ua8_jomala.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
    return res, rA, rB, pl0, plA, plB


# ---------------------------------------------------------------- figurer
def _pilar(ax, d, uts, steg, ms=11):
    Lc = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(d, axis=0).T))])
    for dist in np.arange(steg / 2, Lc[-1], steg):
        j = min(max(int(np.searchsorted(Lc, dist)), 1), len(d) - 1)
        a, b = d[j - 1], d[j]
        if np.hypot(*(b - a)) > 0.5 and uts[0] + 60 < b[0] < uts[1] - 60 and uts[2] + 60 < b[1] < uts[3] - 60:
            ax.annotate('', xy=tuple(b), xytext=tuple(a), zorder=6,
                        arrowprops=dict(arrowstyle='-|>', color='#2b1838', lw=0, mutation_scale=ms))


def karta(rA, rB):
    H = pd.read_csv(P / 'a2_hallplatser_avgangar.csv', index_col=0, dtype={'stop_id': str})
    uts = (106700, 111300, 6683000, 6690200)
    fig, ax = plt.subplots(figsize=(8.6, 11.6))
    K.ny_karta(uts, ax=ax, titel='UA 8 – Jomalapendeln')
    K.rita_linjer(ax, alpha=0.45, lw=1.5, zorder=3, etikett=False)
    i0 = KALMARE.index(FHS)
    for d in K.sammanfoga([x[0] for x in rB[i0:]], tol=60):                # varannan tur hem via Vesterkalmare (B)
        ax.plot(d[:, 0], d[:, 1], color=FARG_K, lw=2.4, ls=(0, (2.5, 1.6)), zorder=4.6)
        _pilar(ax, d, uts, 700, ms=9)
    for d in K.sammanfoga([x[0] for x in rA], tol=60):
        ax.plot(d[:, 0], d[:, 1], color=FARG_P, lw=3.4, solid_capstyle='round', solid_joinstyle='round', zorder=5,
                path_effects=[K.pe.Stroke(linewidth=5.6, foreground='white'), K.pe.Normal()])
        _pilar(ax, d, uts, 700)
    stopp = {'Centrum': CEN, 'Maxinge': MX, 'Dalkarbyvägen': DKS, 'Vikingahallen': VHS, 'Jomala kyrka': JKS,
             'Jomala skola': JS, 'Nabben': NAB}
    pts = {n: tuple(H.loc[s, ['x', 'y']]) for n, s in stopp.items()}
    ax.scatter([p[0] for p in pts.values()], [p[1] for p in pts.values()], s=22, facecolor='white',
               edgecolor='#1f1f1e', lw=0.8, zorder=7)
    ax.scatter([VK_XY[0]], [VK_XY[1]], s=170, marker='*', color='#1c5cab', edgecolor='white', lw=0.8, zorder=8)
    K.placera_etiketter(ax, [(n, p, 40) for n, p in pts.items()] + [('Vesterkalmare (ny hållplats)', VK_XY, 60)],
                        fontsize=7.0, undvik=K.punkt_hinder(ax, [p[0] for p in pts.values()],
                                                            [p[1] for p in pts.values()], px=6))
    K.skalstock(ax, langd_m=1000, loc=(0.05, 0.03))
    hnd = [Line2D([], [], color=FARG_P, lw=3.4, label='Jomalapendeln, varje halvtimme (A)'),
           Line2D([], [], color=FARG_K, lw=2.4, ls=(0, (2.5, 1.6)), label='Varannan tur hem via Vesterkalmare (B)'),
           Line2D([], [], color='#2b1838', lw=0, marker='$→$', markersize=9, label='Körriktning'),
           Line2D([], [], color='#8a8780', lw=1.5, alpha=0.6, label='Stadslinjer i dag')]
    K.teckenforklaring(ax, hnd, loc='lower right')
    return K.spara(fig, 'b4_25_jomala_karta.png')


def omloppsfigur(pl0, plA, plB):
    import b4_omlopp as O
    C.FARG_LINJE.setdefault('P', FARG_P); C.FARG_LINJE.setdefault('K', FARG_K)
    O.BOKSTAV.setdefault('K', 'P')
    fig, axs = plt.subplots(3, 1, figsize=(11.4, 9.6), gridspec_kw={'height_ratios': [5, 6, 6]})
    O.rita_omlopp(axs[0], pl0, titel='I dag – 5 bussar', t0=6 * 60 + 10)
    O.rita_omlopp(axs[1], plA.assign(omlopp=np.nan),
                  titel=f'A – Jomalapendeln varje halvtimme: {plA.buss.nunique()} bussar', t0=6 * 60 + 10)
    O.rita_omlopp(axs[2], plB.assign(omlopp=np.nan),
                  titel=f'B – varannan tur via Vesterkalmare: {plB.buss.nunique()} bussar', t0=6 * 60 + 10)
    O.omlopp_forklaring(fig, extra=[Patch(facecolor=FARG_P, label='Jomalapendeln (P)'),
                                    Patch(facecolor=FARG_K, label='Jomalapendeln via Vesterkalmare (P)')])
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    ut = C.KARTOR / 'b4_26_jomala_omlopp.png'
    K.fullnamn_fig(fig); fig.savefig(ut, dpi=200, bbox_inches='tight'); plt.close(fig)
    return ut


if __name__ == '__main__':
    r, rA, rB, pl0, plA, plB = berakna()
    print(json.dumps(r, ensure_ascii=False, indent=1, default=float))
    print(karta(rA, rB)); print(omloppsfigur(pl0, plA, plB))
