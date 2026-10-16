# -*- coding: utf-8 -*-
"""B4.5 – Genomgående linje N/S (och S/Ö utan puls): rymmer sammanslagningen nordostområdena?

Fråga (beställaren 2026-10-14): kan linje N förlängas mot Örtvägen, Lillåkersvägen och Österkalmare utan fler bussar
om N och S slås ihop till en genomgående linje (bussen fortsätter N → S efter 0,5 min), med Bo-Bil i stället för
Vikingagränd (UA 3) och/eller några indragna hållplatser på linje S som tidsutrymme? Kravet är detsamma som för
V/Ö: varvet N + S inom timmen med minst MARGINAL_VARV = 5 min i centrum, dagens omlopp i övrigt oförändrat.

Delar
  1. Tidsutrymme per par (analytiskt): pulsen kvar / partnern startar senare, marginal 5 min (krav) och 3,5 min
     (0,5 genomgång + 3 reglering en gång per varv – tidigare screening, 'utan puls': N/S 7,5, S/Ö 10,5 min).
  2. Största förlängning per N-tur (omloppsverifierat, steg 0,1 min) i fyra fall: bara sammanslagning;
     + Bo-Bil (UA 3, −0,4 min); + indragna hållplatser på S (antagande 0,25 min per hållplats, 5 kandidater ur A3);
     + båda.
  3. Antal N-turer som ryms för varje nordostområde (behovet ur b4_sammanslagning_omraden.csv).
Utdata: data/processed/b4_ns.json, b4_ns_turer.csv, b4_ns_omraden.geojson (EPSG:4326, för QGIS),
        output/kartor/b4_16_ns.png
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import b4_omlopp as O  # noqa: E402
import b4_ua as F  # noqa: E402
import kartlib as K  # noqa: E402
import data_las as D  # noqa: E402

P = C.PROCESSED
OMRADEN = ['Örtvägen', 'Lillåkersvägen', 'Österkalmare']
S_KANDIDATER = ['Gröna Udden', 'Torggatan', 'Neptunigatan', 'Skillnadsgatan', 'Hamngatan']   # A3, linje S
TID_PER_INDRAGEN_HPL = 0.25        # min per tur och indragen hållplats (antagande: inbromsning, uppehåll, acceleration)
D_MAX, D_STEG = 12.0, 0.1


def utrymme_par(prof, a, b, marginal, puls):
    """Förlängning (min/tur) av linje a som genomgående med b. puls: b avgår i pulsen (≤ 30 − 0,5 − t_a),
    annars startar b när a har kommit tillbaka (60 − marginal − t_a − t_b)."""
    ta, tb = prof[a]['kortid_median'], prof[b]['kortid_median']
    varv = 60.0 - marginal - ta - tb
    return round(min(varv, 30.0 - O.GENOMGANG_MIN - ta) if puls else varv, 1)


def screening(prof):
    ut = []
    for a, b in (('N', 'S'), ('S', 'N'), ('S', 'Ö'), ('Ö', 'S'), ('V', 'Ö'), ('Ö', 'V')):
        ut.append({'par': f'{a}→{b}', 't_a': prof[a]['kortid_median'], 't_b': prof[b]['kortid_median'],
                   'puls_5': utrymme_par(prof, a, b, 5.0, True), 'utan_puls_5': utrymme_par(prof, a, b, 5.0, False),
                   'puls_3_5': utrymme_par(prof, a, b, 3.5, True), 'utan_puls_3_5': utrymme_par(prof, a, b, 3.5, False)})
    return pd.DataFrame(ut)


def stopp_id_for(namn):
    s = D.gtfs()['stops']
    return set(s[s.stop_name == namn].stop_id)


def s_indragning(t, namn=S_KANDIDATER, per_hpl=TID_PER_INDRAGEN_HPL):
    """{S-tur: −min} för indragna kandidater som turen passerar."""
    g = D.gtfs()['stop_times']; ids = set().union(*[stopp_id_for(n) for n in namn]); ut = {}
    for r in t[t.linje == 'S'].itertuples():
        n = g[(g.trip_id == r.trip_id) & g.stop_id.isin(ids)].stop_id.nunique()
        if n:
            ut[r.trip_id] = -round(n * per_hpl, 2)
    return ut


def maxd(t, k, plan0, bas, sol):
    """Största tillägg på N-turen k (steg D_STEG) som ryms som genomgående N/S, eller 0 om inte ens 0 ryms."""
    def ok(d):
        v, _ = O.genomgaende_ryms(t, [k], d, plan0, partner='S', linje='N', bas=bas, sol=sol)
        return bool(v)
    lo, hi = 0, int(D_MAX / D_STEG)
    if not ok(0.0):
        return np.nan
    while lo < hi:                       # största d som ryms (ryms-egenskapen är monoton i d)
        mid = (lo + hi + 1) // 2
        lo, hi = (mid, hi) if ok(mid * D_STEG) else (lo, mid - 1)
    return round(lo * D_STEG, 1)


def main():
    t = O.turer(); plan = O.bygg_omlopp(t); ref = O.kopplingar(plan); plan0 = O.bygg_omlopp(t, referens=ref)
    prof = json.load(open(P / 'b4_omlopp_nyckeltal.json', encoding='utf-8'))['linjer']
    scr = screening(prof)
    xy = F.stopp_xy(); bb = F.bobil_delta(xy)
    bobil = bb['delta_min']                                          # −0,4 min per N-tur
    ntur = t[t.linje == 'N'].sort_values('avg')
    bas_bb = {k: bobil for k in ntur.trip_id}
    sol_s = s_indragning(t)
    idag_varv = O.varv_vo(plan0, 'N', 'S')
    fall = {'sammanslagning': ({}, {}), 'bobil': (bas_bb, {}), 'indragning_S': ({}, sol_s), 'bobil_och_indragning_S': (bas_bb, sol_s)}
    rader = []
    for k in ntur.trip_id:
        r = {'trip_id': k, 'avg': O.hm(float(ntur.set_index('trip_id').avg[k])),
             'tid_centrum_idag': float(idag_varv.set_index('trip_id').centrum_min[k])}
        for namn, (bas, sol) in fall.items():
            r[namn] = maxd(t, k, plan0, bas, sol)
        rader.append(r)
    tur = pd.DataFrame(rader)
    tur.to_csv(P / 'b4_ns_turer.csv', index=False)

    omr = pd.read_csv(P / 'b4_sammanslagning_omraden.csv').set_index('omrade').loc[OMRADEN].reset_index()
    ut_omr = []
    for r in omr.itertuples():
        rad = {'omrade': r.omrade, 'inv': r.inv, 'x': r.x, 'y': r.y, 'behov_min_per_tur': r.behov_min_per_tur,
               'turer_totalt': len(tur)}
        for namn in fall:
            rad[f'turer_{namn}'] = int((tur[namn] >= r.behov_min_per_tur - 1e-9).sum())
        ut_omr.append(rad)
    omr_df = pd.DataFrame(ut_omr)

    res = {'parametrar': {'marginal_varv_min': O.MARGINAL_VARV, 'bobil_delta_min': bobil,
                          'tid_per_indragen_hpl_min': TID_PER_INDRAGEN_HPL, 's_kandidater': S_KANDIDATER,
                          'sparad_tid_S_per_tur_min': sorted(set(-v for v in sol_s.values()))},
           'screening': scr.to_dict('records'),
           'max_forlangning_N': {n: {'min': float(tur[n].min()), 'median': float(tur[n].median()),
                                     'max': float(tur[n].max()), 'turer_utan_utrymme': int(tur[n].isna().sum())}
                                 for n in fall},
           'omraden': omr_df.drop(columns=['x', 'y']).to_dict('records')}
    with open(P / 'b4_ns.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=float)
    g = gpd.GeoDataFrame(omr_df.drop(columns=['x', 'y']), geometry=gpd.points_from_xy(omr_df.x, omr_df.y), crs=C.CRS_METRISK)
    g.to_crs(C.CRS_WGS84).to_file(P / 'b4_ns_omraden.geojson', driver='GeoJSON')
    print(scr.to_string()); print(tur.to_string()); print(omr_df.drop(columns=['x', 'y']).to_string())
    print(figur(tur, omr_df, scr))


def figur(tur, omr, scr):
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw={'width_ratios': [1.15, 1]})
    namn = {'sammanslagning': 'N/S genomgående', 'bobil': '+ Bo-Bil (UA 3)', 'indragning_S': '+ indragna hpl på S',
            'bobil_och_indragning_S': '+ Bo-Bil och indragna hpl på S'}
    farg = ['#b9b4a8', '#1c5cab', '#159a9c', '#2f9e44']
    x = np.arange(len(tur))
    for i, (k, n) in enumerate(namn.items()):
        ax.bar(x + (i - 1.5) * 0.2, tur[k].fillna(0), width=0.2, color=farg[i], label=n)
    for r in omr.itertuples():
        ax.axhline(r.behov_min_per_tur, color='#c0392b', lw=0.9, ls='--')
        ax.text(len(tur) - 0.4, r.behov_min_per_tur + 0.1, f'{r.omrade} {r.behov_min_per_tur:g}'.replace('.', ','),
                ha='right', fontsize=7.5, color='#c0392b')
    ax.set_xticks(x); ax.set_xticklabels(tur.avg, rotation=90, fontsize=7)
    ax.set_ylabel('största förlängning av N-turen, min', fontsize=8)
    ax.set_title('Största förlängning per N-tur (varv N + S ≥ 5 min i centrum)', loc='left', fontsize=10, fontweight='bold')
    ax.legend(fontsize=7.5, frameon=False, loc='upper left'); ax.grid(axis='y', color='#e6e4de', lw=0.6)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    w = 0.2; y = np.arange(len(omr))
    for i, (k, n) in enumerate(namn.items()):
        ax2.barh(y + (i - 1.5) * w, omr[f'turer_{k}'], height=w, color=farg[i])
    ax2.set_yticks(y); ax2.set_yticklabels([f"{r.omrade}\n({int(round(r.inv, -1))} inv., +{str(r.behov_min_per_tur).replace('.', ',')} min)"
                                           for r in omr.itertuples()], fontsize=8)
    ax2.invert_yaxis(); ax2.set_xlim(0, len(tur)); ax2.axvline(len(tur), color='#52514e', lw=0.6)
    ax2.set_xlabel(f'antal av {len(tur)} N-turer per vardag som ryms', fontsize=8)
    ax2.set_title('Turer som ryms per nordostområde', loc='left', fontsize=10, fontweight='bold')
    for s in ('top', 'right'):
        ax2.spines[s].set_visible(False)
    fig.suptitle('Genomgående linje N/S – rymmer den nordostområdena?', x=0.01, ha='left', fontsize=12.5, fontweight='bold')
    ut = C.KARTOR / 'b4_16_ns.png'
    fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


if __name__ == '__main__':
    main()
