# -*- coding: utf-8 -*-
"""Steg 0: Extrahera kustlinje/landmask för Åland ur GSHHG (full upplösning).

Källa: GSHHG – Global Self-consistent, Hierarchical, High-resolution Geography (Wessel & Smith), nivå 1 (land)
och 2 (sjöar), full upplösning, distribuerad via PyPI-distributionen ``basemap-data-hires`` (LGPL). Kustlinjen används
som landmask (befolkningen i en 1 km-ruta antas bo på rutans landdel) och som kartbakgrund.

Kör:  python src/s00_kustlinje.py [sökväg/till/basemap_data_hires-*.whl]
Saknas sökväg laddas hjulet ner med ``pip download`` till en temporär mapp.
"""
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import PROCESSED, CRS_WGS84, CRS_METRISK  # noqa: E402

BBOX = (19.30, 59.80, 21.20, 60.50)   # lon_min, lat_min, lon_max, lat_max (Fasta Åland med omnejd)


def hamta_hjul(arg):
    if arg:
        return Path(arg)
    d = Path(tempfile.mkdtemp(prefix='gshhg_'))
    subprocess.run([sys.executable, '-m', 'pip', 'download', '--no-deps', '-q', '-d', str(d),
                    'basemap-data-hires==2.0.0'], check=True)
    return next(d.glob('*.whl'))


def las_polygoner(hjul):
    z = zipfile.ZipFile(hjul)
    meta = z.read('mpl_toolkits/basemap_data/gshhsmeta_f.dat').decode().splitlines()
    data = z.read('mpl_toolkits/basemap_data/gshhs_f.dat')
    lon0, lat0, lon1, lat1 = BBOX
    ut = []
    for rad in meta:
        f = rad.split()
        typ, npts, syd, nord, off, nb = int(f[0]), int(f[2]), float(f[3]), float(f[4]), int(f[5]), int(f[6])
        if typ not in (1, 2) or nord < lat0 or syd > lat1:
            continue
        p = np.frombuffer(data[off:off + nb], dtype='<f4').astype(float).reshape(npts, 2)   # (lon, lat)
        if p[:, 0].max() < lon0 or p[:, 0].min() > lon1 or len(p) < 4:
            continue
        ut.append((typ, Polygon(p).buffer(0)))
    return ut


def main():
    hjul = hamta_hjul(sys.argv[1] if len(sys.argv) > 1 else None)
    polys = las_polygoner(hjul)
    ram = box(*BBOX)
    land = unary_union([g for t, g in polys if t == 1]).intersection(ram)
    sjo = unary_union([g for t, g in polys if t == 2] or [Polygon()]).intersection(ram)
    land = land.difference(sjo)
    gdf = gpd.GeoDataFrame({'typ': ['land']}, geometry=[land], crs=CRS_WGS84).to_crs(CRS_METRISK)
    gdf['geometry'] = gdf.geometry.simplify(5)       # 5 m förenkling – ingen synlig skillnad i kartskala
    ut = PROCESSED / 'kontext_land.gpkg'
    gdf.to_file(ut, driver='GPKG')
    print(f'Land: {len(polys)} polygoner i utsnittet, area {gdf.area.sum() / 1e6:.0f} km² → {ut}')


if __name__ == '__main__':
    main()
