# -*- coding: utf-8 -*-
"""Inläsning av påstigandedata (Radata), hållplatsregister, GTFS och befolkning – gemensamt för alla steg."""
import sys
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402


# ------------------------------------------------------------------ påstigandedata
@lru_cache(maxsize=1)
def radata():
    """Radata med textnycklar (16-siffriga ID får inte tolkas som tal) och hjälpkolumner."""
    r = pd.read_excel(C.RADATA_XLSX, sheet_name='Radata', dtype={'Stop ID': str, 'Trip ID': str})
    r['P'] = r['Product Count'].fillna(0.0)
    r['linje'] = r['Route Short Name'].astype(str)
    r['datum'] = pd.to_datetime(r['Departure Date'])
    r['vardag'] = r['datum'].dt.weekday < 5
    r['tid_min'] = r['Scheduled Departure Time'].map(_tid_min)
    return r


def _tid_min(t):
    """'10 hours 55 mins' -> 655."""
    t = str(t)
    h = int(t.split(' hour')[0]) if 'hour' in t else 0
    m = int(t.split('hours ')[-1].split('hour ')[-1].split(' min')[0]) if 'min' in t else 0
    return h * 60 + m


@lru_cache(maxsize=1)
def produktfilter():
    """Biljettyper som ingick i den ursprungliga analysen (Filter-fliken, kolumn B)."""
    f = pd.read_excel(C.RADATA_XLSX, sheet_name='Filter', header=None)
    return set(f.iloc[1:, 1].dropna().astype(str)) - {'Tid'}


def period(tid_min):
    if C.FM[0] * 60 <= tid_min < C.FM[1] * 60:
        return 'FM'
    if C.EM[0] * 60 <= tid_min < C.EM[1] * 60:
        return 'EM'
    return None


# ------------------------------------------------------------------ hållplatser / hållplatsområden
@lru_cache(maxsize=1)
def hallplatsomraden():
    """Hållplatsläge (JPP-gid, = GTFS stop_id) -> hållplatsområde (namn, centroid)."""
    x = pd.ExcelFile(C.RADATA_XLSX)
    h = x.parse('Hallpaltser', dtype=str)[['IsJourneyPatternPointGid', 'IsIncludedInStopAreaGid', 'Name']]
    o = x.parse('Hallplatsomraden', dtype={'IsIncludedInStopAreaGid': str})
    o = o.rename(columns={'Name': 'omrade', 'CentroidNorthingCoordinate': 'lat', 'CentroidEastingCoordinate': 'lon'})
    m = h.merge(o[['IsIncludedInStopAreaGid', 'omrade', 'lat', 'lon']], on='IsIncludedInStopAreaGid', how='left')
    m = m.rename(columns={'IsJourneyPatternPointGid': 'stop_id', 'IsIncludedInStopAreaGid': 'area_id'})
    m['omrade'] = m['omrade'].fillna(m['Name'])
    return m.drop_duplicates('stop_id').set_index('stop_id')


# ------------------------------------------------------------------ GTFS
@lru_cache(maxsize=1)
def gtfs():
    g = {}
    for k in ['stops', 'routes', 'trips', 'stop_times', 'calendar', 'calendar_dates']:
        g[k] = pd.read_csv(C.GTFS_DIR / f'{k}.txt', dtype=str, keep_default_na=False)
    st = g['stop_times']
    st['seq'] = st['stop_sequence'].astype(int)
    st['t_dep'] = st['departure_time'].map(_gtfs_min)
    st['t_arr'] = st['arrival_time'].map(_gtfs_min)
    g['stops']['lat'] = g['stops']['stop_lat'].astype(float)
    g['stops']['lon'] = g['stops']['stop_lon'].astype(float)
    return g


def _gtfs_min(t):
    try:
        h, m, s = (int(v) for v in t.split(':'))
        return h * 60 + m + s / 60
    except Exception:
        return np.nan


def aktiva_services(datum):
    g = gtfs()
    vd = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'][datum.weekday()]
    ds = datum.strftime('%Y%m%d')
    cal = g['calendar']
    akt = set(cal.loc[(cal[vd] == '1') & (cal.start_date <= ds) & (cal.end_date >= ds), 'service_id'])
    cd = g['calendar_dates']; sub = cd[cd.date == ds]
    akt |= set(sub.loc[sub.exception_type == '1', 'service_id'])
    akt -= set(sub.loc[sub.exception_type == '2', 'service_id'])
    return akt


def typvardag():
    """Representativ vardag i GTFS: den vardag under höstterminen med flest stadslinjeturer (tie -> tidigast)."""
    g = gtfs()
    trips = g['trips'].merge(g['routes'][['route_id', 'route_short_name']], on='route_id')
    stad = trips[trips.route_short_name.isin(C.STADSLINJER)]
    bast, n_bast = None, -1
    for d in pd.date_range('2026-09-01', '2026-11-30'):
        if d.weekday() >= 5:
            continue
        n = stad.service_id.isin(aktiva_services(d)).sum()
        if n > n_bast:
            bast, n_bast = d, n
    return bast.date()


def turer_dag(datum=None, linjer=None):
    """Trips som trafikerar datumet (valfritt filtrerat på route_short_name), med linjenamn."""
    g = gtfs()
    datum = datum or typvardag()
    t = g['trips'].merge(g['routes'][['route_id', 'route_short_name', 'route_type', 'agency_id']], on='route_id')
    t = t[t.service_id.isin(aktiva_services(pd.Timestamp(datum)))]
    if linjer is not None:
        t = t[t.route_short_name.isin(linjer)]
    return t.rename(columns={'route_short_name': 'linje'})


def avgangar_per_hallplats(datum=None, linjer=None, fonster=None):
    """Antal avgångar per GTFS-hållplatsläge under dagen (eller inom fönster (h0, h1)). Sista hpl räknas ej."""
    g = gtfs()
    t = turer_dag(datum, linjer)
    st = g['stop_times'][g['stop_times'].trip_id.isin(t.trip_id)].copy()
    st['maxseq'] = st.groupby('trip_id').seq.transform('max')
    st = st[st.seq < st.maxseq]                       # avstigning vid slutstation är ingen avgång
    if fonster:
        st = st[(st.t_dep >= fonster[0] * 60) & (st.t_dep < fonster[1] * 60)]
    return st.merge(t[['trip_id', 'linje']], on='trip_id')


# ------------------------------------------------------------------ befolkning och land
@lru_cache(maxsize=1)
def befolkning():
    b = gpd.read_file(C.BEFOLKNING_SHP).to_crs(C.CRS_METRISK)
    b['ruta_id'] = np.arange(len(b))
    return b


@lru_cache(maxsize=1)
def land():
    return gpd.read_file(C.PROCESSED / 'kontext_land.gpkg').to_crs(C.CRS_METRISK)


def till_metrisk(lon, lat):
    """WGS84 -> EPSG:3067 (x, y) som numpy-arrayer."""
    from pyproj import Transformer
    tr = Transformer.from_crs(C.CRS_WGS84, C.CRS_METRISK, always_xy=True)
    return tr.transform(np.asarray(lon, float), np.asarray(lat, float))
