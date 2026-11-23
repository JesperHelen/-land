# -*- coding: utf-8 -*-
"""Bakgrundskarta ur OpenStreetMap (OpenMapTiles-vektorplattor från OpenFreeMap) för inzoomade kartor.

Plattorna (zoom 14) hämtas en gång och sparas i data/processed/osm_plattor/; därefter ritas gator, byggnader,
flygfält, vatten och markanvändning med matplotlib i EPSG:3067. Underlag: © OpenMapTiles © OpenStreetMap-bidragsgivare
(OpenFreeMap).
"""
import math
import sys
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import shape
from shapely.ops import transform

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402

TILEJSON = 'https://tiles.openfreemap.org/planet'
ZOOM = 14
CACHE = C.PROCESSED / 'osm_plattor'
KALLA = 'Bakgrund: © OpenMapTiles © OpenStreetMap-bidragsgivare (OpenFreeMap).'
LAGER = ('water', 'landcover', 'landuse', 'park', 'aeroway', 'building', 'transportation', 'transportation_name')


def _platta_nr(lon, lat, z=ZOOM):
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)
    return x, y


@lru_cache(maxsize=1)
def _url():
    import requests
    return requests.get(TILEJSON, timeout=20).json()['tiles'][0]


def _hamta(x, y, z=ZOOM):
    f = CACHE / f'{z}_{x}_{y}.pbf'
    if not f.exists():
        import requests
        CACHE.mkdir(parents=True, exist_ok=True)
        r = requests.get(_url().format(z=z, x=x, y=y), timeout=30,
                         headers={'User-Agent': 'linjenatsutredning/1.0'})
        r.raise_for_status()
        f.write_bytes(r.content)
    return f.read_bytes()


@lru_cache(maxsize=8)
def osm(uts, zoom=ZOOM):
    """{lager: GeoDataFrame (EPSG:3067)} för utsnittet uts = (x0, x1, y0, y1) i EPSG:3067 (zoom 13 räcker för
    översiktskartor; 14 ger alla gator och byggnader)."""
    import mapbox_vector_tile as mvt
    from pyproj import Transformer
    till_ll = Transformer.from_crs(C.CRS_METRISK, C.CRS_WGS84, always_xy=True)
    fran_ll = Transformer.from_crs(C.CRS_WGS84, C.CRS_METRISK, always_xy=True)
    x0, x1, y0, y1 = uts
    hörn = [till_ll.transform(x, y) for x in (x0, x1) for y in (y0, y1)]     # alla fyra hörnen (meridiankonvergens)
    lo = [h[0] for h in hörn]; la = [h[1] for h in hörn]
    tx0, ty1 = _platta_nr(min(lo), min(la), zoom); tx1, ty0 = _platta_nr(max(lo), max(la), zoom)
    n = 2 ** zoom
    rader = {k: [] for k in LAGER}
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            d = mvt.decode(_hamta(tx, ty, zoom), default_options={'y_coord_down': True})
            for lager in LAGER:
                if lager not in d:
                    continue
                ext = d[lager].get('extent', 4096)

                def till_m(px, py, z=None, tx=tx, ty=ty, ext=ext):
                    px, py = np.asarray(px, float), np.asarray(py, float)
                    lon = (tx + px / ext) / n * 360.0 - 180.0
                    lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * (ty + py / ext) / n))))
                    return fran_ll.transform(lon, lat)
                for ft in d[lager]['features']:
                    try:
                        g = transform(till_m, shape(ft['geometry']))
                    except Exception:
                        continue
                    if not g.is_empty:
                        rader[lager].append({**{k: v for k, v in ft['properties'].items() if isinstance(v, (str, int, float))},
                                             'geometry': g})
    return {k: gpd.GeoDataFrame(v, geometry='geometry', crs=C.CRS_METRISK) if v else None for k, v in rader.items()}


VAG_BREDD = {'motorway': 3.2, 'trunk': 3.0, 'primary': 2.8, 'secondary': 2.4, 'tertiary': 2.0, 'minor': 1.4,
             'service': 0.9, 'track': 0.6, 'path': 0.4}


FARG = {'land': '#f2efe9', 'landcover': '#e3ebd6', 'park': '#dbe8cf', 'landuse': '#ebe7df', 'vatten': '#c9dcef',
        'flygfalt': '#e9e6f0', 'bana': '#c9c6cf', 'hus': '#d9d3c9', 'huskant': '#c9c2b6', 'stig': '#c4bdb0',
        'vagkant': '#bdb6aa', 'vag': 'white', 'namn': '#6f6a60'}
GRA = {'land': '#f1f1ef', 'landcover': '#ebecea', 'park': '#e8eae6', 'landuse': '#ececea', 'vatten': '#dce4ea',
       'flygfalt': '#ebebeb', 'bana': '#dcdcdc', 'hus': '#e4e4e2', 'huskant': '#e4e4e2', 'stig': '#dddddb',
       'vagkant': '#d6d6d3', 'vag': 'white', 'namn': '#8a8a86'}


def rita(ax, uts, vagnamn=True, zorder=0.5, stil='farg', zoom=ZOOM, smala_vagar=True):
    """Ritar OSM-bakgrunden i utsnittet (dämpade färger så att linjerna syns ovanpå). stil='gra' ger en ljusgrå
    bakgrund för översiktskartor (t.ex. OD-flöden)."""
    import matplotlib.patheffects as pe
    F = GRA if stil == 'gra' else FARG
    o = osm(tuple(uts), zoom)
    skala = 1.0 if smala_vagar is True else smala_vagar
    ax.set_facecolor(F['land'])
    for lager, farg, z in [('landcover', F['landcover'], 0.0), ('park', F['park'], 0.05), ('landuse', F['landuse'], 0.02)]:
        g = o.get(lager)
        if g is not None:
            g = g[g.geom_type.isin(['Polygon', 'MultiPolygon'])]
            if lager == 'landuse' and 'class' in g:
                g = g[g['class'].isin(['residential', 'industrial', 'commercial', 'retail'])]
            if len(g):
                g.plot(ax=ax, color=farg, linewidth=0, zorder=zorder + z)
    if o.get('water') is not None:
        o['water'].plot(ax=ax, color=F['vatten'], linewidth=0, zorder=zorder + 0.1)
    a = o.get('aeroway')
    if a is not None:
        poly = a[a.geom_type.isin(['Polygon', 'MultiPolygon'])]
        if 'class' in poly:
            poly[poly['class'] == 'aerodrome'].plot(ax=ax, color=F['flygfalt'], linewidth=0, zorder=zorder + 0.15)
            poly[poly['class'].isin(['runway', 'taxiway', 'apron'])].plot(ax=ax, color=F['bana'], linewidth=0,
                                                                         zorder=zorder + 0.2)
        ln = a[a.geom_type.isin(['LineString', 'MultiLineString'])]
        if len(ln) and 'class' in ln:
            for kl, w in (('runway', 9.0), ('taxiway', 2.5)):
                d = ln[ln['class'] == kl]
                if len(d):
                    d.plot(ax=ax, color=F['bana'], linewidth=w * skala, zorder=zorder + 0.2)
    b = o.get('building')
    if b is not None:
        b.plot(ax=ax, color=F['hus'], edgecolor=F['huskant'], linewidth=0.3, zorder=zorder + 0.3)
    t = o.get('transportation')
    if t is not None and 'class' in t:
        t = t[t.geom_type.isin(['LineString', 'MultiLineString'])]
        for kl in ['path', 'track', 'service', 'minor', 'tertiary', 'secondary', 'primary', 'trunk', 'motorway']:
            d = t[t['class'] == kl]
            if not len(d) or (skala < 1 and kl in ('path', 'track', 'service')):
                continue
            w = VAG_BREDD[kl] * skala
            if kl in ('path', 'track'):
                d.plot(ax=ax, color=F['stig'], linewidth=w, linestyle=(0, (2, 1.5)), zorder=zorder + 0.4)
            else:
                d.plot(ax=ax, color=F['vagkant'], linewidth=w + 1.0 * skala, zorder=zorder + 0.4)
                d.plot(ax=ax, color=F['vag'], linewidth=w, zorder=zorder + 0.45)
    n = o.get('transportation_name')
    if vagnamn and n is not None and 'name' in n:
        x0, x1, y0, y1 = uts
        sett = set()
        n = n[n.geom_type.isin(['LineString', 'MultiLineString'])]
        if 'class' in n:
            n = n[n['class'].isin(['primary', 'secondary', 'tertiary', 'minor'])]
        for r in n.sort_values(by='name').itertuples():
            if not isinstance(r.name, str) or r.name in sett:
                continue
            g = r.geometry if r.geometry.geom_type == 'LineString' else max(r.geometry.geoms, key=lambda q: q.length)
            if g.length < 250:
                continue
            p = g.interpolate(0.5, normalized=True)
            mx, my = 0.08 * (x1 - x0), 0.06 * (y1 - y0)            # inte för nära kanten
            if not (x0 + mx < p.x < x1 - mx and y0 + my < p.y < y1 - my):
                continue
            q = g.interpolate(min(g.project(p) + 20, g.length)); q0 = g.interpolate(max(g.project(p) - 20, 0))
            vinkel = math.degrees(math.atan2(q.y - q0.y, q.x - q0.x))
            vinkel = vinkel - 180 if vinkel > 90 else (vinkel + 180 if vinkel < -90 else vinkel)
            ax.text(p.x, p.y, r.name, rotation=vinkel, rotation_mode='anchor', ha='center', va='center',
                    fontsize=6.2, color=F['namn'], style='italic', zorder=zorder + 0.5, clip_on=True,
                    path_effects=[pe.withStroke(linewidth=2.2, foreground='white')])
            sett.add(r.name)
