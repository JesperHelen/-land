# -*- coding: utf-8 -*-
"""A2 – Täckningsgrad med turtäthet.

Kompletterar täckningsanalysen (andel av befolkningen inom 400 m fågelväg från hållplats) med antal avgångar.
Metod
  * Befolkningen i varje 1×1 km-ruta fördelas jämnt över rutans landdel i delpunkter om 50×50 m
    (landmask: GSHHG). Detta är den finaste fördelning som underlaget medger.
  * För varje delpunkt räknas antal unika turer (avgångar) en typisk vardag från alla busshållplatser inom
    400 m – stadslinjer och landsbygdslinjer (färjor ingår ej). En tur som passerar flera närliggande
    hållplatser räknas en gång. Avstigning vid slutstation räknas inte som avgång.
  * Klasser (avgångar/vardag): 0 = ingen hållplats inom 400 m; 1–14 mycket låg (sämre än timtrafik);
    15–29 låg (≈ en linje); 30–59 medel; ≥ 60 god.
Utdata: data/processed/a2_*.csv/.gpkg/.json
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402

KLASSER = [(0, 0, 'Ingen hållplats inom 400 m'), (1, 14, 'Mycket låg (1–14 avg/vardag)'),
           (15, 29, 'Låg (15–29)'), (30, 59, 'Medel (30–59)'), (60, 10 ** 6, 'God (≥ 60)')]
SVAG_MAX = 29            # svag faktisk tillgänglighet: hållplats nära men sämre än halvtimmestrafik (≤ 29 avg/vardag)
MARIEHAMN = (105200, 112400, 6672800, 6687600)   # Mariehamn med Järsö/Nåtö (samma som kartutsnittet 'tatort')


def klass(n):
    for i, (lo, hi, _) in enumerate(KLASSER):
        if lo <= n <= hi:
            return i
    return len(KLASSER) - 1


def delpunkter():
    """Delpunkter (50 m) på land inom varje befolkningsruta, med befolkning per punkt."""
    b = D.befolkning()
    land = D.land().union_all(); shapely.prepare(land)
    h = C.DELRUTA_M; rader = []
    for r in b.itertuples():
        x0, y0, x1, y1 = r.geometry.bounds
        xs = np.arange(x0 + h / 2, x1, h); ys = np.arange(y0 + h / 2, y1, h)
        X, Y = np.meshgrid(xs, ys); X, Y = X.ravel(), Y.ravel()
        pa = shapely.contains_xy(land, X, Y)
        if pa.sum() == 0:
            pa[:] = True                       # ruta helt utan land enligt kustlinjen: jämn fördelning
        X, Y = X[pa], Y[pa]
        rader.append(pd.DataFrame({'ruta_id': r.ruta_id, 'x': X, 'y': Y, 'bef': r.Tot_bef / len(X)}))
    return pd.concat(rader, ignore_index=True)


def hallplatser_med_avgangar(fonster=None, linjer=None):
    d = D.typvardag(); t = D.turer_dag(d)
    busslinjer = sorted(t.loc[t.route_type == '3', 'linje'].unique()) if linjer is None else linjer
    a = D.avgangar_per_hallplats(d, busslinjer, fonster)
    g = D.gtfs()['stops'].set_index('stop_id')
    s = a.groupby('stop_id').agg(turer=('trip_id', lambda v: frozenset(v)), linjer=('linje', lambda v: ','.join(sorted(set(v)))))
    s['avgangar'] = s.turer.map(len)
    s['x'], s['y'] = D.till_metrisk(g.loc[s.index, 'lon'].values, g.loc[s.index, 'lat'].values)
    s['namn'] = g.loc[s.index, 'stop_name'].values
    return s


def avgangar_inom(pkt, hpl, r=C.TACKNING_M):
    """Antal unika turer från hållplatser inom r meter från varje punkt."""
    tree = cKDTree(hpl[['x', 'y']].to_numpy())
    grannar = tree.query_ball_point(pkt[['x', 'y']].to_numpy(), r)
    turer = hpl.turer.to_numpy(); cache = {}; ut = np.zeros(len(pkt), int); narmast = np.zeros(len(pkt))
    d, _ = tree.query(pkt[['x', 'y']].to_numpy())
    for i, g in enumerate(grannar):
        k = tuple(sorted(g))
        if k not in cache:
            cache[k] = len(frozenset().union(*[turer[j] for j in k])) if k else 0
        ut[i] = cache[k]
    return ut, d


def sammanstall(pkt, kol, mask=None):
    p = pkt if mask is None else pkt[mask]
    tot = p.bef.sum(); ut = {'befolkning': round(float(tot))}
    for i, (_, _, namn) in enumerate(KLASSER):
        v = p.loc[p[kol] == i, 'bef'].sum()
        ut[namn] = {'invanare': round(float(v)), 'andel': round(float(v / tot), 4)}
    ut['inom_400m_andel'] = round(float(p.loc[p[kol] > 0, 'bef'].sum() / tot), 4)
    ut['minst_15_avg_andel'] = round(float(p.loc[p[kol] >= 2, 'bef'].sum() / tot), 4)
    ut['minst_30_avg_andel'] = round(float(p.loc[p[kol] >= 3, 'bef'].sum() / tot), 4)
    ut['svag_andel'] = round(float(p.loc[p[kol].isin([1, 2]), 'bef'].sum() / tot), 4)
    ut['svag_invanare'] = round(float(p.loc[p[kol].isin([1, 2]), 'bef'].sum()))
    return ut


def main():
    P = C.PROCESSED
    pkt = delpunkter()
    alla = hallplatser_med_avgangar()
    stad = hallplatser_med_avgangar(linjer=C.STADSLINJER)
    fm = hallplatser_med_avgangar(fonster=C.FM)
    pkt['avg_alla'], pkt['dist_hpl'] = avgangar_inom(pkt, alla)
    pkt['avg_stad'], _ = avgangar_inom(pkt, stad)
    pkt['avg_fm'], _ = avgangar_inom(pkt, fm)
    pkt['klass'] = pkt.avg_alla.map(klass)
    pkt['klass_stad'] = pkt.avg_stad.map(klass)
    pkt['svag'] = (pkt.avg_alla >= 1) & (pkt.avg_alla <= SVAG_MAX)
    mh = pkt.x.between(MARIEHAMN[0], MARIEHAMN[1]) & pkt.y.between(MARIEHAMN[2], MARIEHAMN[3])
    pkt['mariehamn'] = mh
    pkt.round({'x': 1, 'y': 1, 'bef': 5, 'dist_hpl': 1}).to_csv(P / 'a2_delpunkter.csv.gz', index=False)

    res = {'typvardag': str(D.typvardag()),
           'hela_omradet_alla_bussar': sammanstall(pkt, 'klass'),
           'mariehamn_alla_bussar': sammanstall(pkt, 'klass', mh),
           'mariehamn_endast_stadslinjer': sammanstall(pkt, 'klass_stad', mh),
           'mariehamn_fm_minst_3_avg_andel': round(float(pkt.loc[mh & (pkt.avg_fm >= 3), 'bef'].sum() / pkt.loc[mh, 'bef'].sum()), 4),
           'hallplatslagen_med_avgang': int(len(alla)), 'hallplatslagen_stadslinjer': int(len(stad))}
    # per 1 km-ruta (för GIS och kartor)
    b = D.befolkning()[['ruta_id', 'Tot_bef', 'geometry']].copy()
    g = pkt.groupby('ruta_id')
    agg = pd.DataFrame({
        'andel_inom_400m': g.apply(lambda d: d.loc[d.avg_alla > 0, 'bef'].sum() / max(d.bef.sum(), 1e-9)),
        'andel_minst_15_avg': g.apply(lambda d: d.loc[d.avg_alla >= 15, 'bef'].sum() / max(d.bef.sum(), 1e-9)),
        'inv_svag': g.apply(lambda d: d.loc[d.svag, 'bef'].sum()),
        'inv_otackt': g.apply(lambda d: d.loc[d.avg_alla == 0, 'bef'].sum()),
        'avg_befviktat': g.apply(lambda d: (d.avg_alla * d.bef).sum() / max(d.bef.sum(), 1e-9))})
    b = b.merge(agg, left_on='ruta_id', right_index=True, how='left')
    b.to_file(P / 'a2_tackning_rutor.gpkg', driver='GPKG')
    alla.drop(columns='turer').to_csv(P / 'a2_hallplatser_avgangar.csv')
    with open(P / 'a2_sammanfattning.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
