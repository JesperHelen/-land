# -*- coding: utf-8 -*-
"""B4.6 – Nordost: omläggning av linje N och Ö mot Lillåkersvägen, Örtvägen, Österkalmare och Solberget.

Områdena ligger 0,6–1,6 km från dagens linjer (a3_behov_ny_linjestrackning.csv). Här prövas vilka kombinationer som
ryms utan fler bussar när N förlängs (partner S) och/eller Ö förlängs (partner V), med reglering hos partnerlinjen
(b4_omlopp.genomgaende_ryms) och, för Ö, med Solberget indragen (förslag 4-lägets Ö-besparing).

Behovet per tur räknas som i b4_sammanslagning: 2 × avstånd till körvägen × 1,3 / 25 km/h + 0,5 min per ny hållplats.
Flera områden på samma avstick: tur och retur till det avlägsnaste området och 0,5 min per hållplats (grov skattning –
körvägarna är raka streck tills OSRM kan användas). De fem alternativen verifieras mot omloppen gemensamt (N och Ö
samtidigt). Utdata: data/processed/b4_nordost.csv/json, output/kartor/b4_nordost.geojson.
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import b4_omlopp as O  # noqa: E402
import b4_forslag as F  # noqa: E402
import s01_vagdragning as V  # noqa: E402

P = C.PROCESSED
OMVAG, KMH = 1.3, 25.0
OMR = ['Örtvägen', 'Lillåkersvägen', 'Österkalmare', 'Solberget', 'Solberget södra']


def avstand(p, linje, geo, sl):
    best = 1e9
    for k, xy in geo.items():
        if linje in sl[k]:
            for q0, q1 in zip(xy[:-1], xy[1:]):
                v = q1 - q0; L2 = float(v @ v)
                tt = 0.0 if L2 == 0 else float(np.clip((p - q0) @ v / L2, 0, 1))
                best = min(best, float(np.hypot(*(q0 + tt * v - p))))
    return best


def behov(namn, dist):
    return round(2 * max(dist[n] for n in namn) * OMVAG / 1000 / KMH * 60 + 0.5 * len(namn), 1)


def main():
    t = O.turer(); b = pd.read_csv(P / 'a3_behov_ny_linjestrackning.csv').set_index('narmaste_hpl')
    geo = V.segmentgeometri(); sl = V.segment_linjer()
    d_n = {o: avstand(np.array([b.at[o, 'x'], b.at[o, 'y']]), 'N', geo, sl) for o in OMR}
    d_o = {o: avstand(np.array([b.at[o, 'x'], b.at[o, 'y']]), 'Ö', geo, sl) for o in OMR}
    plan0 = O.bygg_omlopp(t); r = O.ram(t); ref = O.kopplingar(plan0)
    n_t = list(t[t.linje == 'N'].trip_id); o_t = list(t[t.linje == 'Ö'].trip_id)
    sol = F.solberget_delta(t)
    S_bas = None
    try:
        import b4_ns_sammanslagning as NS
        S_bas = NS.indragning_delta(t, 'S', NS.S_INDRAGNA)
    except Exception:
        pass

    alt = [  # id, text, N-områden, Ö-områden, S-indragning, Solberget indragen
        ('A', 'N till Örtvägen', ['Örtvägen'], [], False, False),
        ('B', 'N till Örtvägen + Lillåkersvägen', ['Örtvägen', 'Lillåkersvägen'], [], False, False),
        ('B+', 'som B, med S-indragning', ['Örtvägen', 'Lillåkersvägen'], [], True, False),
        ('C', 'N till Örtvägen, Lillåkersvägen och Österkalmare', ['Örtvägen', 'Lillåkersvägen', 'Österkalmare'], [], True, False),
        ('D', 'Ö till Solberget + Solberget södra', [], ['Solberget', 'Solberget södra'], False, False),
        ('E', 'Ö till Österkalmare, Solberget indragen', [], ['Österkalmare'], False, True),
        ('F', 'B + D (N och Ö)', ['Örtvägen', 'Lillåkersvägen'], ['Solberget', 'Solberget södra'], True, False),
        ('G', 'A + E (N till Örtvägen, Ö till Österkalmare)', ['Örtvägen'], ['Österkalmare'], False, True),
    ]
    rader = []; res = {}
    for id_, text, nn, oo, sind, solb in alt:
        dd, skift, ok_n, ok_o = {}, {}, None, None
        dn = behov(nn, d_n) if nn else 0.0; do_ = behov(oo, d_o) if oo else 0.0
        for skift_max in (2.0, 4.0):
            dd, skift = {}, {}
            if nn:
                bas = dict(S_bas) if sind and S_bas else None
                v, s_ = O.genomgaende_ryms(t, n_t, dn, r, partner='S', max_skift=skift_max, bas=bas, referens=ref)
                for k in v:
                    dd[k] = dd.get(k, 0.0) + dn
                if bas:
                    for k, x in bas.items():
                        dd[k] = dd.get(k, 0.0) + x
                skift.update(s_); ok_n = len(v)
            if oo:
                bas = dict(sol) if solb else None
                v, s_ = O.genomgaende_ryms(t, o_t, do_, r, partner='V', max_skift=2.0, bas=bas, referens=ref)
                for k in v:
                    dd[k] = dd.get(k, 0.0) + do_
                if bas:
                    for k, x in bas.items():
                        dd[k] = dd.get(k, 0.0) + x
                for k, x in s_.items():
                    skift[k] = skift.get(k, 0.0) + x
                ok_o = len(v)
            plan, nt, ok = O.verifiera(t, dd, r, skift=skift, referens=ref)
            rader.append({'alt': id_, 'text': text, 'n_omraden': ', '.join(nn), 'o_omraden': ', '.join(oo),
                          'inv': float(sum(b.at[o, 'inv'] for o in nn + oo)), 'behov_N_min': dn, 'behov_O_min': do_,
                          'skift_N_max': skift_max if nn else np.nan, 'turer_N': ok_n, 'turer_N_tot': len(n_t) if nn else None,
                          'turer_O': ok_o, 'turer_O_tot': len(o_t) if oo else None, 'fordon': nt['fordon'],
                          'omloppstid_h': nt['omloppstid_h'], 'varv_utan_reglering': nt['varv_utan_reglering'],
                          'gemensamt_ryms': bool(ok), 'robust': bool(O.ar_robust(nt, r))})
            print(rader[-1])
            if skift_max == 2.0 and not nn:
                break
    df = pd.DataFrame(rader); df.to_csv(P / 'b4_nordost.csv', index=False)
    res = {'avstand_N_m': {k: round(v) for k, v in d_n.items()}, 'avstand_O_m': {k: round(v) for k, v in d_o.items()},
           'alternativ': df.to_dict('records')}
    with open(P / 'b4_nordost.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=float)
    pts = pd.DataFrame([{'omrade': o, 'inv': b.at[o, 'inv'], 'avstand_N_m': round(d_n[o]), 'avstand_O_m': round(d_o[o]),
                         'x': b.at[o, 'x'], 'y': b.at[o, 'y']} for o in OMR])
    g = gpd.GeoDataFrame(pts.drop(columns=['x', 'y']), geometry=gpd.points_from_xy(pts.x, pts.y), crs=C.CRS_METRISK)
    g.to_crs(C.CRS_WGS84).to_file(C.KARTOR / 'b4_nordost.geojson', driver='GeoJSON')
    print(df.drop(columns=['text']).to_string())


if __name__ == '__main__':
    main()
