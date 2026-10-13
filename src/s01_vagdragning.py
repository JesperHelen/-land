# -*- coding: utf-8 -*-
"""Steg 01: Linjernas vägdragning längs gatunätet (OSRM) och förskjutning där flera linjer delar gata.

Vägdragning
  * Stadslinjernas körvägar delas upp i segment mellan på varandra följande hållplatser (alla turmönster en
    typisk vardag). Varje segment ruttas med OSRM (profil 'driving') och sparas i en cache:
    data/processed/vagdragning_segment.gpkg (lager 'segment' och 'linjer').
  * Redan ruttade segment återanvänds vid omkörning; bara saknade segment hämtas.
  * En OSRM-rutt som är orimligt lång (> 2,5 × fågelvägen + 300 m, t.ex. p.g.a. enkelriktning eller fel
    gata vid hållplatsen) avvisas och ersätts med rak linje (kalla = 'osrm_avvisad') för manuell kontroll.
  * Går OSRM inte att nå används rak linje mellan hållplatserna (kalla = 'rak').
Förskjutning (för kartor)
  * Där två eller fler linjer går längs samma gata (inom 15 m, parallell riktning) får varje linje ett eget
    spår vinkelrätt mot gatan. Spårordningen följer linjeordningen J, N, S, V, Ö och är densamma oavsett
    färdriktning, så att linjerna aldrig ritas ovanpå varandra.

Kör (kräver nätåtkomst till OSRM):  python src/s01_vagdragning.py
Egen server:                       OSRM_URL=http://localhost:5000 python src/s01_vagdragning.py
"""
import math
import os
import sys
import time
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import LineString, MultiLineString

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402

OSRM_URL = os.environ.get('OSRM_URL', 'https://router.project-osrm.org').rstrip('/')
CACHE = C.PROCESSED / 'vagdragning_segment.gpkg'
MAX_OMVAG = (2.5, 300.0)          # faktor, tillägg (m) – längre OSRM-rutt avvisas
SAMMA_GATA_M = 15.0               # avstånd inom vilket två linjer räknas gå på samma gata
ORDNING = {l: i for i, l in enumerate(C.STADSLINJER)}


# ====================================================================== segment och turmönster
@lru_cache(maxsize=1)
def monster_per_linje():
    """{linje: [(hållplatsföljd (stop_id), antal turer), ...]} sorterat på antal turer (vanligast först)."""
    g = D.gtfs(); t = D.turer_dag(None, C.STADSLINJER)
    st = g['stop_times'][g['stop_times'].trip_id.isin(t.trip_id)].sort_values(['trip_id', 'seq'])
    m = st.groupby('trip_id').stop_id.apply(tuple)
    lin = t.set_index('trip_id').linje
    ut = {}
    for (ln, mon), n in pd.Series(1, index=pd.MultiIndex.from_arrays([lin.loc[m.index].values, m.values])) \
            .groupby(level=[0, 1]).sum().items():
        ut.setdefault(ln, []).append((mon, int(n)))
    return {ln: sorted(v, key=lambda x: -x[1]) for ln, v in ut.items()}


def segment_linjer():
    """{(från_stop, till_stop): {linjer}} för alla turmönster."""
    ut = {}
    for ln, lista in monster_per_linje().items():
        for mon, _ in lista:
            for a, b in zip(mon[:-1], mon[1:]):
                if a != b:
                    ut.setdefault((a, b), set()).add(ln)
    return ut


@lru_cache(maxsize=1)
def hallplats_xy():
    g = D.gtfs()['stops'].set_index('stop_id')
    x, y = D.till_metrisk(g.lon.values, g.lat.values)
    return {s: (a, b) for s, a, b in zip(g.index, x, y)}, g[['lon', 'lat']]


# ====================================================================== OSRM
def osrm_rutt(lonlat_a, lonlat_b, session):
    url = (f'{OSRM_URL}/route/v1/driving/{lonlat_a[0]:.6f},{lonlat_a[1]:.6f};{lonlat_b[0]:.6f},{lonlat_b[1]:.6f}'
           '?overview=full&geometries=geojson&steps=false')
    r = session.get(url, timeout=20, headers={'User-Agent': 'linjenatsutredning-mariehamn/1.0'})
    r.raise_for_status()
    j = r.json()
    if j.get('code') != 'Ok' or not j.get('routes'):
        raise ValueError(j.get('code'))
    rt = j['routes'][0]
    return np.array(rt['geometry']['coordinates']), float(rt['distance']), float(rt['duration'])


def hamta(paus_s=1.0):
    """Ruttar alla segment som saknas i cachen. Returnerar GeoDataFrame med segmenten."""
    import requests
    from pyproj import Transformer
    tr = Transformer.from_crs(C.CRS_WGS84, C.CRS_METRISK, always_xy=True)
    xy, ll = hallplats_xy()
    segl = segment_linjer()
    cache = {}
    if CACHE.exists():
        c = gpd.read_file(CACHE, layer='segment')
        cache = {(r.from_stop, r.to_stop): r for r in c.itertuples() if r.kalla == 'osrm'}
    rader, natet_nere, n_hamtade = [], False, 0
    s = requests.Session()
    for (a, b), linjer in sorted(segl.items()):
        rak = float(math.hypot(xy[a][0] - xy[b][0], xy[a][1] - xy[b][1]))
        bas = {'from_stop': a, 'to_stop': b, 'linjer': ','.join(sorted(linjer, key=ORDNING.get)), 'rak_m': round(rak, 1)}
        if (a, b) in cache:
            r = cache[(a, b)]
            rader.append({**bas, 'kalla': 'osrm', 'langd_m': r.langd_m, 'tid_s': r.tid_s, 'geometry': r.geometry})
            continue
        geom, kalla, langd, tid = LineString([xy[a], xy[b]]), 'rak', rak, np.nan
        if not natet_nere:
            try:
                p, langd_o, tid_o = osrm_rutt(ll.loc[a].values, ll.loc[b].values, s)
                n_hamtade += 1
                X, Y = tr.transform(p[:, 0], p[:, 1])
                pts = [xy[a]] + list(zip(X, Y)) + [xy[b]]          # anslut exakt till hållplatserna
                if langd_o <= MAX_OMVAG[0] * rak + MAX_OMVAG[1]:
                    geom, kalla, langd, tid = LineString(pts), 'osrm', langd_o, tid_o
                else:
                    kalla, tid = 'osrm_avvisad', tid_o
                time.sleep(paus_s)
            except Exception as e:                                  # nätet nere: sluta försöka
                natet_nere = True
                print(f'OSRM kunde inte nås ({type(e).__name__}: {e}) – raka linjer används för återstående segment.')
        rader.append({**bas, 'kalla': kalla, 'langd_m': round(langd, 1), 'tid_s': tid, 'geometry': geom})
    seg = gpd.GeoDataFrame(rader, geometry='geometry', crs=C.CRS_METRISK)
    print(f'Segment: {len(seg)} ({(seg.kalla == "osrm").sum()} OSRM, {(seg.kalla == "osrm_avvisad").sum()} avvisade, '
          f'{(seg.kalla == "rak").sum()} raka); nya OSRM-anrop: {n_hamtade}')
    return seg


def spara(seg):
    if CACHE.exists():
        CACHE.unlink()
    seg.to_file(CACHE, layer='segment', driver='GPKG')
    rader = []
    for ln, lista in monster_per_linje().items():
        nycklar = []
        for mon, _ in lista:
            nycklar += [k for k in zip(mon[:-1], mon[1:]) if k[0] != k[1] and k not in nycklar]
        d = seg.set_index(['from_stop', 'to_stop']).loc[nycklar]
        rader.append({'linje': ln, 'turer_vardag': sum(n for _, n in lista), 'langd_m': round(d.langd_m.sum()),
                      'andel_osrm': round(float((d.kalla == 'osrm').mean()), 3),
                      'geometry': MultiLineString(list(d.geometry))})
    gpd.GeoDataFrame(rader, crs=C.CRS_METRISK).to_file(CACHE, layer='linjer', driver='GPKG')


# ====================================================================== läsning för kartor och analys
@lru_cache(maxsize=1)
def segmentgeometri():
    """{(från, till): (N,2)-array} – OSRM-geometri om den finns i cachen, annars rak linje."""
    xy, _ = hallplats_xy()
    ut = {k: np.array([xy[k[0]], xy[k[1]]]) for k in segment_linjer()}
    if CACHE.exists():
        c = gpd.read_file(CACHE, layer='segment')
        for r in c.itertuples():
            if (r.from_stop, r.to_stop) in ut:
                ut[(r.from_stop, r.to_stop)] = np.asarray(r.geometry.coords)
    return ut


def kalla_text():
    if CACHE.exists():
        c = gpd.read_file(CACHE, layer='segment', columns=['kalla'])
        if (c.kalla == 'osrm').mean() > 0.5:
            return 'Linjernas vägdragning: OSRM (OpenStreetMap).'
    return 'Linjer ritade som raka streck mellan hållplatser.'


def linjekedjor():
    """{linje: [kedja, ...]} där en kedja är en lista segmentnycklar i körordning. Första kedjan är det
    vanligaste turmönstret; segment som bara finns i andra mönster bildar egna kortare kedjor."""
    ut = {}
    for ln, lista in monster_per_linje().items():
        sett, kedjor = set(), []
        for mon, _ in lista:
            k = [s for s in zip(mon[:-1], mon[1:]) if s[0] != s[1]]
            aktuell = []
            for s in k:
                if s in sett:
                    if aktuell:
                        kedjor.append(aktuell); aktuell = []
                    continue
                sett.add(s); aktuell.append(s)
            if aktuell:
                kedjor.append(aktuell)
        ut[ln] = kedjor
    return ut


def _sampla(xy, steg):
    d = np.hypot(*np.diff(xy, axis=0).T)
    s = np.concatenate([[0], np.cumsum(d)])
    if s[-1] == 0:
        return xy[:1], np.array([[1.0, 0.0]])
    sv = np.linspace(0, s[-1], max(2, int(s[-1] / steg) + 1))
    P = np.column_stack([np.interp(sv, s, xy[:, 0]), np.interp(sv, s, xy[:, 1])])
    T = np.gradient(P, axis=0); T /= np.maximum(np.hypot(*T.T), 1e-9)[:, None]
    return P, T


@lru_cache(maxsize=8)
def _sparanalys(steg=6.0):
    """Samplar alla linjer och bestämmer för varje punkt spårplacering bland linjer på samma gata."""
    geo = segmentgeometri(); kedjor = linjekedjor()
    prov = []                                     # (linje, kedjenr, P, T)
    for ln, kl in kedjor.items():
        for ki, kedja in enumerate(kl):
            xy = np.vstack([geo[s] if i == 0 else geo[s][1:] for i, s in enumerate(kedja)])
            P, T = _sampla(xy, steg)
            prov.append((ln, ki, P, T))
    allaP = np.vstack([p[2] for p in prov]); allaT = np.vstack([p[3] for p in prov])
    allaL = np.concatenate([[ORDNING[p[0]]] * len(p[2]) for p in prov])
    tree = cKDTree(allaP)
    ut = []
    for ln, ki, P, T in prov:
        mitt = ORDNING[ln]
        slot = np.zeros(len(P)); norm = np.column_stack([-T[:, 1], T[:, 0]]); tecken = np.ones(len(P))
        for i, gr in enumerate(tree.query_ball_point(P, SAMMA_GATA_M)):
            gr = np.asarray(gr)
            if len(gr) == 0:
                continue
            par = np.abs(allaT[gr] @ T[i]) > 0.85                    # parallell gata (oavsett riktning)
            linjer = sorted(set(allaL[gr[par]]) | {mitt})
            if len(linjer) < 2:
                continue
            ref = linjer[0]
            if ref == mitt:
                tref = T[i]
            else:
                kand = gr[par & (allaL[gr] == ref)]
                tref = allaT[kand[np.argmin(np.hypot(*(allaP[kand] - P[i]).T))]]
            slot[i] = linjer.index(mitt) - (len(linjer) - 1) / 2
            norm[i] = [-tref[1], tref[0]]
            tecken[i] = 1.0 if tref @ T[i] > 0 else -1.0
        ut.append((ln, ki, P, T, slot, norm, tecken))
    return ut


def forskjutna_linjer(avstand_m, steg=6.0):
    """{linje: [(N,2)-array, ...]} förskjutna geometrier; avstand_m = spåravstånd i meter."""
    ut = {}
    for ln, ki, P, T, slot, norm, _ in _sparanalys(steg):
        v = slot[:, None] * norm * avstand_m
        k = 9                                                         # mjuk övergång (≈ 50 m)
        if len(v) > k:
            ker = np.ones(k) / k
            v = np.column_stack([np.convolve(np.pad(v[:, j], k // 2, mode='edge'), ker, mode='valid') for j in range(2)])
        ut.setdefault(ln, []).append(P + v)
    return ut


def forskjutna_delar(steg=6.0):
    """GeoDataFrame med linjedelar (oförskjuten mittlinje) och attributet 'forskjutning' (spår, med tecken
    relativt linjens egen riktning) – för förskjutning vid ritning i QGIS (offset i mm)."""
    rader = []
    for ln, ki, P, T, slot, norm, tecken in _sparanalys(steg):
        s = np.round(slot * tecken * 2) / 2
        # filtrera bort enstaka avvikande punkter (flimmer vid korsningar)
        s = pd.Series(s).rolling(5, center=True, min_periods=1).median().to_numpy()
        start = 0
        for i in range(1, len(s) + 1):
            if i == len(s) or s[i] != s[start]:
                if i - start >= 2:
                    rader.append({'linje': ln, 'kedja': ki, 'forskjutning': float(s[start]),
                                  'geometry': LineString(P[start:i + (1 if i < len(s) else 0)])})
                start = i
    return gpd.GeoDataFrame(rader, crs=C.CRS_METRISK)


def main():
    seg = hamta()
    spara(seg)
    print('Sparat:', CACHE)
    av = seg[seg.kalla == 'osrm_avvisad']
    if len(av):
        print('Avvisade OSRM-rutter (kontrollera):')
        print(av[['from_stop', 'to_stop', 'linjer', 'rak_m', 'langd_m']].to_string(index=False))


if __name__ == '__main__':
    main()
