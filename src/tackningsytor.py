# -*- coding: utf-8 -*-
"""Täckningsytor som vektorer – exakta 400 m-cirklar runt hållplatserna (i stället för 50 m-raster).

Analysen (invånare per turtäthetsklass) räknas som tidigare på 50 m-delpunkter (a2_tackning). För kartor och GIS
ritas ytorna i stället exakt:
  * Området är befolkningsrutornas landdel (samma område som delpunkterna).
  * 400 m-cirklarna runt alla hållplatser (alla scenarier) delar området i ytor där samma hållplatser ligger
    inom 400 m. Varje yta får antal avgångar per vardag (unika turer, som a2_tackning.avgangar_inom) och
    turtäthetsklass per scenario, och är uppdelad per befolkningsruta.
  * Invånare per yta hämtas från delpunkterna med samma ruta och klass (en delpunkt får samma klass som ytan
    den ligger i, eftersom båda räknas med samma 400 m-regel).
"""
import sys
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402
from a2_tackning import avgangar_inom, klass  # noqa: E402

RADIE = C.TACKNING_M
QUAD_SEGS = 32                    # 128 punkter per cirkel – runda kanter även i stor skala


@lru_cache(maxsize=1)
def rutor_land():
    """Befolkningsrutornas landdel (ruta helt utan land enligt kustlinjen: hela rutan, som delpunkterna)."""
    b = D.befolkning()[['ruta_id', 'geometry']]
    land = D.land().union_all()
    geoms = []
    for g in b.geometry:
        i = g.intersection(land)
        geoms.append(i if not i.is_empty and i.area > 1 else g)
    return gpd.GeoDataFrame({'ruta_id': b.ruta_id.to_numpy()}, geometry=geoms, crs=C.CRS_METRISK)


def ytor(scenarier):
    """scenarier: {namn: DataFrame med x, y, turer (frozenset)}. Returnerar GeoDataFrame med ruta_id och
    avg_<namn>, klass_<namn> per yta."""
    rut = rutor_land()
    omr = shapely.union_all(rut.geometry.to_numpy())
    pos = np.unique(np.round(np.vstack([h[['x', 'y']].to_numpy(float) for h in scenarier.values()]), 1), axis=0)
    cirk = shapely.buffer(shapely.points(pos), RADIE, quad_segs=QUAD_SEGS)
    nar = shapely.intersects(cirk, omr)
    pos, cirk = pos[nar], cirk[nar]
    kanter = shapely.union_all(shapely.boundary(cirk))                     # nodade cirkelkanter
    delar = shapely.get_parts(shapely.polygonize(shapely.get_parts(kanter)))
    tree = cKDTree(pos)
    rp = shapely.get_coordinates(shapely.point_on_surface(delar))
    d, _ = tree.query(rp)
    delar = delar[d < RADIE]                                                # bara ytor inom någon cirkel
    utanfor = shapely.difference(omr, shapely.union_all(cirk))
    g = gpd.GeoDataFrame(geometry=list(delar) + [utanfor], crs=C.CRS_METRISK)
    g = gpd.overlay(g, rut, how='intersection', keep_geom_type=True)
    g = g[g.area > 0.5].reset_index(drop=True)
    rp = shapely.get_coordinates(shapely.point_on_surface(g.geometry.to_numpy()))
    p = pd.DataFrame({'x': rp[:, 0], 'y': rp[:, 1]})
    for namn, h in scenarier.items():
        avg, _ = avgangar_inom(p, h)
        g[f'avg_{namn}'] = avg
        g[f'klass_{namn}'] = [klass(v) for v in avg]
    return g


def per_klass(g, scen, pkt, klasskol):
    """Ytor sammanslagna per ruta och turtäthetsklass för ett scenario, med invånare från delpunkterna
    (pkt med kolumnerna ruta_id, bef och klasskol)."""
    y = g.dissolve(by=['ruta_id', f'klass_{scen}'], as_index=False)[['ruta_id', f'klass_{scen}', 'geometry']]
    y = y.rename(columns={f'klass_{scen}': 'klass_nr'})
    inv = pkt.groupby(['ruta_id', klasskol]).bef.sum().rename('invanare').reset_index().rename(columns={klasskol: 'klass_nr'})
    y = y.merge(inv, on=['ruta_id', 'klass_nr'], how='left').fillna({'invanare': 0.0})
    y['geometry'] = [x if x.geom_type == 'MultiPolygon' else shapely.MultiPolygon(
        [p for p in shapely.get_parts(x) if p.geom_type == 'Polygon']) for x in y.geometry]
    return gpd.GeoDataFrame(y, geometry='geometry', crs=C.CRS_METRISK)


def forandring(g, scen, bas='idag'):
    """Ytor där turtäthetsklassen skiljer sig från bas: 'Bättre' eller 'Sämre' (sammanslagna)."""
    d = g[g[f'klass_{scen}'] != g[f'klass_{bas}']].copy()
    if d.empty:
        return gpd.GeoDataFrame(columns=['forandring', 'geometry'], geometry='geometry', crs=C.CRS_METRISK)
    d['forandring'] = np.where(d[f'klass_{scen}'] > d[f'klass_{bas}'], 'Bättre', 'Sämre')
    return d.dissolve(by='forandring', as_index=False)[['forandring', 'geometry']]


def tathet_alfa(ruta_id, lo=0.30, hi=0.70):
    """Opacitet efter rutans befolkningstäthet (där folk faktiskt bor), som i de tidigare rasterkartorna."""
    b = D.befolkning().set_index('ruta_id').Tot_bef
    t = pd.Series(ruta_id).map(b).fillna(0).to_numpy()
    return lo + hi * np.sqrt(t / b.max())
