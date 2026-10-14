# -*- coding: utf-8 -*-
"""B4.5 – Sammanslagning av linjer, genomgående N/S (+ Bo-Bil) och varianter utan puls.

Frågan: hur långt kan linje N förlängas (Örtvägen, Lillåkersvägen, Österkalmare) utan fler bussar om N och S
körs som genomgående linje (bussen fortsätter N → S efter GENOMGANG_MIN, regleringen tas vid S → N), och vad
tillför indragna hållplatser på S (Gröna Udden, Torggatan, Neptunigatan, Skillnadsgatan, Hamngatan) och
Bo-Bil i stället för Vikingagränd (linje N, +0,1 min/tur)?

Metod (samma som b4_omlopp.genomgaende_ryms): N-turerna prövas en i taget i tidsordning med tillägget d min på
ankomsten; S-turen som följer i omloppet får avgå högst `skift` min efter dagens avgång (pulsen i centrum). En tur
räknas som löst om omloppen byggs om utan fler fordon (≤ 5) och utan att omloppstiden ökar mer än toleransen.
  * Puls bevarad: skift = 0  (bara bytet N → S kortas till 0,5 min)
  * Skift ≤ 2 min: partnerlinjen avgår högst 2 min efter pulsen (beställarens nivå i B4.4b)
  * Utan puls: skift upp till 4 / 7 min (partnerns avgångstid släpps)
  * S/Ö (och N/V) som alternativt linjepar: normparet i omloppsbyggaren byts till S ↔ Ö, N ↔ V.
Robust = inte fler varv utan ≥ 3 min reglering än i dag.
Utdata: data/processed/b4_ns_*.csv/json, output/kartor/b4_ns_sammanslagning.geojson (+ b4_ns_*.png)
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402
import b4_omlopp as O  # noqa: E402
import b4_forslag as F  # noqa: E402

P = C.PROCESSED
SKIFT = [0.0, 2.0, 4.0, 7.0]
BEHOV = {'Bo-Bil': None, 'Örtvägen': 4.4, 'Dalkullavägen (V)': None, 'Lillåkersvägen': 6.5, 'Österkalmare': 10.3}
S_INDRAGNA = ['Gröna Udden', 'Torggatan', 'Neptunigatan', 'Skillnadsgatan', 'Hamngatan']
BESPARING_PER_HPL = F.UPPEHALL   # min – antagen tidsbesparing per indragen hållplats (lika med uppehållet för en ny)
PAR_NS = O.NORMPAR
PAR_SO = (('S', 'Ö'), ('Ö', 'S'), ('N', 'V'), ('V', 'N'))


def indragning_delta(t, linje, namn):
    """Kortare körtid per tur om hållplatserna `namn` dras in: {trip_id: −min} (som b4_forslag.solberget_delta)."""
    g = D.gtfs(); st = g['stop_times']; stops = g['stops']
    ids = set(stops[stops.stop_name.isin(namn)].stop_id)
    dt = F.direkttider(); ut = {}
    for r in t[t.linje == linje].itertuples():
        s_ = st[st.trip_id == r.trip_id].sort_values('seq')
        sid, ta = list(s_.stop_id), list(s_.t_arr)
        tot = 0.0; i = 1
        # sammanhängande indragna hållplatser dras in som block
        while i < len(sid) - 1:
            if sid[i] in ids:
                j = i
                while j + 1 < len(sid) - 1 and sid[j + 1] in ids:
                    j += 1
                a, b = sid[i - 1], sid[j + 1]
                direkt = dt.get((a, b))
                if direkt is None:                       # ingen direktsträcka i tidtabellen (interpolerade tider):
                    tot += BESPARING_PER_HPL * (j - i + 1)   # antagen besparing per indragen hållplats
                else:
                    tot += (ta[j + 1] - ta[i - 1]) - direkt
                i = j + 1
            else:
                i += 1
        if tot > 0:
            ut[r.trip_id] = -round(tot, 2)
    return ut


def prova(t, kand, d, par, partner, skift, bas=None, robust=False):
    plan0 = O.bygg_omlopp(t, par=par)
    r = O.ram(t) if par is PAR_NS else {**{k: v for k, v in O.nyckeltal(plan0).items()
                                           if k in ('fordon', 'omloppstid_h', 'varv_utan_reglering')}}
    ref = O.kopplingar(plan0)
    valda, s_ = O.genomgaende_ryms(t, kand, d, r, partner=partner, max_skift=skift, robust=robust, bas=bas,
                                   par=par, referens=ref)
    return valda, s_


def main():
    t = O.turer()
    n_trips = list(t[t.linje == 'N'].trip_id); s_trips = list(t[t.linje == 'S'].trip_id)
    bb = json.load(open(P / 'b4_forslag.json', encoding='utf-8'))['antaganden']['bobil']['delta_min']
    ntot = len(n_trips)
    S_bas = indragning_delta(t, 'S', S_INDRAGNA)
    sparar = sorted(v for v in S_bas.values())
    print('S-indragning: turer med besparing', len(S_bas), 'median min', np.median(list(S_bas.values())) if S_bas else 0)
    rader = []

    def kor(variant, par, forlangd, partner, kand, d, skift, bas=None, text=''):
        for rob in (False, True):
            v, s_ = prova(t, kand, d, par, partner, skift, bas=bas, robust=rob)
            rader.append({'variant': variant, 'linje': forlangd, 'partner': partner, 'tillagg_min': d, 'skift_max_min': skift,
                          'robust': rob, 'turer_totalt': len(kand), 'turer_ryms': len(v), 'skiftade_turer': len(s_),
                          'bas': text})
        print(variant, forlangd, d, skift, [r['turer_ryms'] for r in rader[-2:]])

    # 1. N/S, N förlängs: tillägg d och skift s, utan och med indragna hållplatser på S
    for d in (0.1, 3.5, 4.4, 5.5, 6.5, 7.5, 10.3):
        for s in SKIFT:
            kor('N/S', PAR_NS, 'N', 'S', n_trips, d, s)
            kor('N/S + S indragna', PAR_NS, 'N', 'S', n_trips, d, s, bas=S_bas, text='S: 5 hållplatser indragna')
    # 2. S/Ö-par: S förlängs (för jämförelse, utan puls S/Ö 10,5 min)
    for d in (3.5, 6.5, 10.5):
        for s in SKIFT:
            kor('S/Ö (par S↔Ö, N↔V)', PAR_SO, 'S', 'Ö', s_trips, d, s)
    # 3. N/S mot områdena (behovet per tur) – en rad per område
    omr = pd.read_csv(P / 'b4_sammanslagning_omraden.csv')
    res_omr = []
    ut = pd.DataFrame(rader)
    for o in omr[omr.linje == 'N'].itertuples():
        d = o.behov_min_per_tur
        # närmaste prövade nivå ≥ behovet beräknas direkt
        for s in SKIFT:
            for sv, kw in (('N/S', None), ('N/S + S indragna', S_bas)):
                v, s_ = prova(t, n_trips, d, PAR_NS, 'S', s, bas=kw)
                vr, _ = prova(t, n_trips, d, PAR_NS, 'S', s, bas=kw, robust=True)
                res_omr.append({'omrade': o.omrade, 'inv': o.inv, 'behov_min_per_tur': d, 'variant': sv, 'skift_max_min': s,
                                'turer_ryms': len(v), 'turer_ryms_robust': len(vr), 'turer_totalt': ntot})
    ro = pd.DataFrame(res_omr)
    # Bo-Bil: +0,1 min/tur, kombinerat med N/S
    bobil = []
    for s in SKIFT:
        v, _ = prova(t, n_trips, bb, PAR_NS, 'S', s); vr, _ = prova(t, n_trips, bb, PAR_NS, 'S', s, robust=True)
        bobil.append({'skift_max_min': s, 'turer_ryms': len(v), 'turer_ryms_robust': len(vr), 'turer_totalt': ntot})
    ut.to_csv(P / 'b4_ns_grid.csv', index=False)
    ro.to_csv(P / 'b4_ns_omraden.csv', index=False)
    res = {'bobil_delta_min': bb, 's_indragna': S_INDRAGNA, 's_indragna_turer_med_besparing': len(S_bas),
           's_indragna_besparing_min_median': float(np.median(list(S_bas.values()))) if S_bas else 0.0,
           'bobil_ns': bobil, 'omraden': ro.to_dict('records'), 'grid': ut.to_dict('records')}
    with open(P / 'b4_ns_sammanslagning.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=float)
    print(ro.to_string()); print(pd.DataFrame(bobil).to_string())

    # GIS: områdespunkter med resultat (GeoJSON, WGS84) – för QGIS
    best = ro.copy()
    best['ok'] = best.turer_ryms >= ntot
    gj = []
    for o in omr[omr.linje == 'N'].itertuples():
        d = best[best.omrade == o.omrade]
        def forst(variant, kol):
            m = d[(d.variant == variant) & (d[kol] >= ntot)]
            return float(m.skift_max_min.min()) if len(m) else np.nan
        gj.append({'omrade': o.omrade, 'inv': o.inv, 'behov_min_per_tur': o.behov_min_per_tur,
                   'skift_krav_NS_min': forst('N/S', 'turer_ryms'), 'skift_krav_NS_robust_min': forst('N/S', 'turer_ryms_robust'),
                   'skift_krav_NS_Sindragna_min': forst('N/S + S indragna', 'turer_ryms'),
                   'turer_ryms_puls_bevarad': int(d[(d.variant == 'N/S') & (d.skift_max_min == 0)].turer_ryms.iat[0]),
                   'turer_totalt': ntot, 'x': o.x, 'y': o.y})
    g = pd.DataFrame(gj)
    gdf = gpd.GeoDataFrame(g.drop(columns=['x', 'y']), geometry=gpd.points_from_xy(g.x, g.y), crs=C.CRS_METRISK)
    gdf.to_crs(C.CRS_WGS84).to_file(C.KARTOR / 'b4_ns_sammanslagning.geojson', driver='GeoJSON')
    print(gdf.drop(columns='geometry').to_string())


if __name__ == '__main__':
    main()
