# -*- coding: utf-8 -*-
"""Skriver varje kartlager i output/gis/linjenatsutredning.gpkg som GeoJSON (EPSG:4326) till output/gis/geojson/,
så att alla kartor kan öppnas och göras om i QGIS (beställaren 2026-10-15). Tabeller utan geometri hoppas över.
Stilar finns i GeoPackage (layer_styles) och som .qml i output/gis/stilar/."""
import sys
from pathlib import Path

import geopandas as gpd
import pyogrio

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402

GPKG = C.ROT / 'output' / 'gis' / 'linjenatsutredning.gpkg'
UT = C.ROT / 'output' / 'gis' / 'geojson'


def main():
    UT.mkdir(parents=True, exist_ok=True)
    for f in UT.glob('*.geojson'):
        f.unlink()
    n = 0
    for namn, typ in pyogrio.list_layers(GPKG):
        if not typ or namn == 'layer_styles':
            continue
        g = gpd.read_file(GPKG, layer=namn)
        for c in g.columns:                                   # GeoJSON saknar mängd-/objekttyper
            if c != 'geometry' and g[c].dtype == object:
                g[c] = g[c].map(lambda v: v if isinstance(v, (str, int, float, bool, type(None))) else str(v))
        g.to_crs(C.CRS_WGS84).to_file(UT / f'{namn}.geojson', driver='GeoJSON'); n += 1
    print(f'{n} lager -> {UT}')


if __name__ == '__main__':
    main()
