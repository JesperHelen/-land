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
Vägdragning ruttad i QGIS:         python src/s01_vagdragning.py --fran-gis   (se output/gis/rutta_med_osrm.py)
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
# Utredningsalternativens nya delsträckor (kapitel 4). Ruttas också med OSRM när det går, för kartor/GIS och för att
# kontrollera körtiderna. NY_MOCKELO = nytt hållplatsläge i Möckelö Strand (indikativt läge från A3).
# Norrgårdsvägen (9025302000067701) ↔ NY_MOCKELO går på befintlig väg (beställarens skiss 2026-10-14, 2 min):
# UA 1a kör den fram och tillbaka, UA 1b kör den tillbaka från den nya hållplatsen (slinga).
# FLYGPLATSEN = hållplats vid flygterminalen (UA 4): Posten → flygplatsen → Källarvägen (beställarens skiss).
UA_SEGMENT = [('9025302000067701', 'NY_MOCKELO', 'UA 1a'), ('NY_MOCKELO', '9025302000067701', 'UA 1a, 1b'),
                   ('9025302000031201', '9025302000003502', 'UA 3'), ('9025302000003502', '9025302000063301', 'UA 3'),
                   ('9025302000035802', 'FLYGPLATSEN', 'UA 4'), ('FLYGPLATSEN', '9025302000025902', 'UA 4')]
# UA 1b: Norrgårdsvägen förlängd från Möckelö Strand till den nya hållplatsen (planerad väg, 1 min). Vägen finns
# inte i dag och ruttas därför inte; den ritas schematiskt (rak linje).
PLANERAD_VAG = ('9025302000066401', 'NY_MOCKELO')
# Befintlig väg Norrgårdsvägen → nytt hållplatsläge, digitaliserad ur beställarens skiss (EPSG:3067, ≈ 10 m noggrannhet).
# Används tills OSRM-rutten hämtats (kalla = 'skiss').
SKISS_NORRGARDSVAGEN_NY_MOCKELO = [
    (105734, 6684367), (105742, 6684258), (105760, 6684159), (105797, 6684060), (105849, 6683964), (105904, 6683891),
    (105956, 6683837), (106003, 6683782), (106038, 6683723), (106058, 6683672), (106061, 6683632), (106046, 6683596),
    (105999, 6683556), (105914, 6683511), (105812, 6683477), (105715, 6683459)]
# UA 4: hållplats vid flygterminalen och körvägen Posten → terminalen (slinga runt terminalen) → tillbaka till
# Norra Svibyvägen, digitaliserad ur beställarens skiss (2026-10-14). Skalan (≈ 1,19 m/px) är bestämd så att
# terminalen hamnar ≈ 390 m öster om banans mittlinje (banändarna 60,1144/19,8914 och 60,1300/19,9049).
# Osäkerhet i läget ≈ ± 25 %. Ersätts av OSRM-rutten när den hämtats.
FLYGPLATSEN_XY = (106462.0, 6686544.0)
SKISS_POSTEN_FLYGPLATSEN = [
    (106913, 6686152), (106908, 6686168), (106888, 6686190), (106858, 6686223), (106828, 6686259), (106798, 6686297),
    (106772, 6686336), (106745, 6686384), (106715, 6686426), (106685, 6686461), (106656, 6686483), (106620, 6686503),
    (106584, 6686518), (106548, 6686530), (106525, 6686535), (106510, 6686544), (106495, 6686568), (106483, 6686587),
    (106469, 6686585), (106460, 6686568)]
SKISS_FLYGPLATSEN_KALLARVAGEN = [
    (106454, 6686518), (106452, 6686496), (106472, 6686493), (106491, 6686514), (106508, 6686530), (106525, 6686535),
    (106548, 6686530), (106584, 6686518), (106620, 6686503), (106656, 6686483), (106685, 6686461), (106715, 6686426),
    (106745, 6686384), (106772, 6686336), (106798, 6686297), (106828, 6686259), (106858, 6686223), (106888, 6686190),
    (106908, 6686168), (106941, 6686205), (106953, 6686247)]


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


def pseudohallplatser():
    """Nya hållplatslägen utan stop_id: {id: (x, y, lon, lat)}."""
    f = C.PROCESSED / 'a3_behov_ny_linjestrackning.csv'
    if not f.exists():
        return {}
    b = pd.read_csv(f); m = b[b.narmaste_hpl == 'Möckelö Strand']
    ut = {'NY_MOCKELO': tuple(float(m[k].iloc[0]) for k in ('x', 'y', 'lon', 'lat'))} if len(m) else {}
    from pyproj import Transformer
    lon, lat = Transformer.from_crs(C.CRS_METRISK, C.CRS_WGS84, always_xy=True).transform(*FLYGPLATSEN_XY)
    ut['FLYGPLATSEN'] = (*FLYGPLATSEN_XY, float(lon), float(lat))
    return ut


def alla_xy():
    """Hållplatser (GTFS) och nya hållplatslägen: ({id: (x, y)}, DataFrame lon/lat)."""
    xy, ll = hallplats_xy()
    xy = dict(xy); ll = ll.copy()
    for k, (x, y, lon, lat) in pseudohallplatser().items():
        xy[k] = (x, y); ll.loc[k] = [lon, lat]
    return xy, ll
# Via-punkter ("gömda stopp") där OSRM:s snabbaste väg inte är bussens väg. En punkt gäller segmentet
# from_stop → to_stop och motsvarande segment i motsatt riktning (hållplatserna på andra sidan gatan); utan
# from_stop/to_stop gäller den närmaste segmentet. Fler punkter kan läggas till i QGIS i lagret 00_viapunkter
# (output/gis/rutta_med_osrm.py läser lagret). OSRM anropas då med continue_straight (ingen vändning vid punkten).
VIA_PUNKTER = [
    {'from_stop': '9025302000029202', 'to_stop': '9025302000067702', 'x': 106101.0, 'y': 6684603.0,
     'kommentar': 'Linje V Lönnhagsvägen – Norrgårdsvägen kör vägen söder om huvudvägen och vänder inte vid '
                  'hållplatsen (beställaren 2026-10-14)'}]
TVILLING_M = 100.0     # motsatt riktning: ändpunkterna inom detta avstånd från segmentets ändpunkter i omvänd ordning


def _punkt_linje(p, a, b):
    """(avstånd, läge 0–1) från punkten p till sträckan a–b."""
    vx, vy = b[0] - a[0], b[1] - a[1]
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L2))
    return math.hypot(a[0] + t * vx - p[0], a[1] + t * vy - p[1]), t


def via_per_segment(segment, punkter, tvilling_m=TVILLING_M):
    """segment: {(a, b): ((xa, ya), (xb, yb))}; punkter: [{'from_stop', 'to_stop', 'x', 'y'}]. Returnerar
    {(a, b): [(x, y), ...]} i körordning a → b. (Samma kod finns i output/gis/rutta_med_osrm.py.)"""
    ut = {}
    for p in punkter:
        q = (float(p['x']), float(p['y']))
        k0 = (str(p.get('from_stop') or ''), str(p.get('to_stop') or ''))
        if k0 not in segment:
            k0 = min(segment, key=lambda k: _punkt_linje(q, *segment[k])[0])
        (xa, ya), (xb, yb) = segment[k0]
        for k, (pa, pb) in segment.items():
            if k == k0 or (math.hypot(pa[0] - xb, pa[1] - yb) <= tvilling_m and math.hypot(pb[0] - xa, pb[1] - ya) <= tvilling_m):
                ut.setdefault(k, []).append(q)
    for k, lista in ut.items():
        lista.sort(key=lambda q: _punkt_linje(q, *segment[k])[1])
    return ut


def via_text(punkter):
    return ';'.join(f'{x:.0f},{y:.0f}' for x, y in punkter)


def skiss(a, b):
    """Skissad geometri för ett UA-segment ((N,2)-array) eller None."""
    xy, _ = alla_xy()
    if a not in xy or b not in xy:
        return None
    if (a, b) == ('9025302000067701', 'NY_MOCKELO'):
        return np.array([xy[a]] + SKISS_NORRGARDSVAGEN_NY_MOCKELO + [xy[b]], float)
    if (a, b) == ('NY_MOCKELO', '9025302000067701'):
        return skiss(b, a)[::-1].copy()
    if (a, b) == ('9025302000035802', 'FLYGPLATSEN'):
        return np.array([xy[a]] + SKISS_POSTEN_FLYGPLATSEN + [xy[b]], float)
    if (a, b) == ('FLYGPLATSEN', '9025302000025902'):
        return np.array([xy[a]] + SKISS_FLYGPLATSEN_KALLARVAGEN + [xy[b]], float)
    return None


def planerad_vag():
    """UA 1b:s planerade väg (förlängd Norrgårdsvägen) som (2,2)-array."""
    xy, _ = alla_xy()
    a, b = PLANERAD_VAG
    return np.array([xy[a], xy[b]], float)


def langd(p):
    return float(np.hypot(*np.diff(np.asarray(p, float), axis=0).T).sum())


# ====================================================================== OSRM
def osrm_rutt(lonlat_a, lonlat_b, session, via=()):
    pkt = ';'.join(f'{p[0]:.6f},{p[1]:.6f}' for p in [lonlat_a, *via, lonlat_b])
    url = (f'{OSRM_URL}/route/v1/driving/{pkt}?overview=full&geometries=geojson&steps=false'
           + ('&continue_straight=true' if len(via) else ''))
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
    xy, ll = alla_xy()
    segl = {k: set(v) for k, v in segment_linjer().items()}
    for a, b, namn in UA_SEGMENT:                      # UA:ns nya delsträckor
        if a in xy and b in xy:
            segl.setdefault((a, b), set()).add(namn)
    via = via_per_segment({k: (xy[k[0]], xy[k[1]]) for k in segl}, VIA_PUNKTER)
    tr_inv = Transformer.from_crs(C.CRS_METRISK, C.CRS_WGS84, always_xy=True)
    cache = {}
    if CACHE.exists():
        c = gpd.read_file(CACHE, layer='segment')
        if 'via' not in c:
            c['via'] = ''
        cache = {(r.from_stop, r.to_stop): r for r in c.itertuples() if r.kalla == 'osrm'}
    rader, natet_nere, n_hamtade = [], False, 0
    s = requests.Session()
    for (a, b), linjer in sorted(segl.items()):
        rak = float(math.hypot(xy[a][0] - xy[b][0], xy[a][1] - xy[b][1]))
        v_ = via.get((a, b), [])
        bas = {'from_stop': a, 'to_stop': b, 'linjer': ','.join(sorted(linjer, key=lambda l: ORDNING.get(l, 99))),
               'rak_m': round(rak, 1), 'via': via_text(v_)}
        if (a, b) in cache and (cache[(a, b)].via or '') == bas['via']:      # ruttad med samma via-punkter
            r = cache[(a, b)]
            rader.append({**bas, 'kalla': 'osrm', 'langd_m': r.langd_m, 'tid_s': r.tid_s, 'geometry': r.geometry})
            continue
        sk = skiss(a, b)
        geom, kalla, langd_, tid = ((LineString(sk), 'skiss', langd(sk), np.nan) if sk is not None
                                    else (LineString([xy[a], xy[b]]), 'rak', rak, np.nan))
        if not natet_nere:
            try:
                p, langd_o, tid_o = osrm_rutt(ll.loc[a].values, ll.loc[b].values, s,
                                              via=[tr_inv.transform(x_, y_) for x_, y_ in v_])
                n_hamtade += 1
                X, Y = tr.transform(p[:, 0], p[:, 1])
                pts = [xy[a]] + list(zip(X, Y)) + [xy[b]]          # anslut exakt till hållplatserna
                if langd_o <= MAX_OMVAG[0] * rak + MAX_OMVAG[1]:
                    geom, kalla, langd_, tid = LineString(pts), 'osrm', langd_o, tid_o
                else:
                    kalla, tid = 'osrm_avvisad', tid_o
                time.sleep(paus_s)
            except Exception as e:                                  # nätet nere: sluta försöka
                natet_nere = True
                print(f'OSRM kunde inte nås ({type(e).__name__}: {e}) – raka linjer används för återstående segment.')
        rader.append({**bas, 'kalla': kalla, 'langd_m': round(langd_, 1), 'tid_s': tid, 'geometry': geom})
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


def uageometri():
    """Utredningsalternativens nya delsträckor: {(från, till): {'xy', 'kalla', 'langd_m', 'tid_s'}} – OSRM om den finns i
    cachen, annars beställarens skiss (kalla = 'skiss') eller rak linje (kalla = 'rak')."""
    xy, _ = alla_xy()
    ut = {}
    for a, b, _ in UA_SEGMENT:
        if a in xy and b in xy:
            sk = skiss(a, b)
            p = sk if sk is not None else np.array([xy[a], xy[b]])
            ut[(a, b)] = {'xy': p, 'kalla': 'skiss' if sk is not None else 'rak', 'langd_m': langd(p), 'tid_s': np.nan}
    if CACHE.exists():
        c = gpd.read_file(CACHE, layer='segment')
        for r in c.itertuples():
            if (r.from_stop, r.to_stop) in ut and r.kalla == 'osrm':
                ut[(r.from_stop, r.to_stop)] = {'xy': np.asarray(r.geometry.coords), 'kalla': 'osrm',
                                                'langd_m': float(r.langd_m), 'tid_s': float(r.tid_s)}
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


def fran_gis(gpkg=None):
    """Läser vägdragning som ruttats i QGIS (output/gis/rutta_med_osrm.py) från GIS-filens lager 00_segment."""
    gpkg = gpkg or C.ROT / 'output' / 'gis' / 'linjenatsutredning.gpkg'
    g = gpd.read_file(gpkg, layer='00_segment').to_crs(C.CRS_METRISK)
    g['rak_m'] = [round(float(math.hypot(x.coords[-1][0] - x.coords[0][0], x.coords[-1][1] - x.coords[0][1])), 1)
                  for x in g.geometry]
    seg = g[['from_stop', 'to_stop', 'linjer', 'rak_m', 'kalla', 'langd_m', 'tid_s', 'geometry']].copy()
    print(f'Från {gpkg}: {len(seg)} segment ({(seg.kalla == "osrm").sum()} OSRM).')
    return seg


def main():
    seg = fran_gis() if '--fran-gis' in sys.argv else hamta()
    spara(seg)
    print('Sparat:', CACHE)
    av = seg[seg.kalla == 'osrm_avvisad']
    if len(av):
        print('Avvisade OSRM-rutter (kontrollera):')
        print(av[['from_stop', 'to_stop', 'linjer', 'rak_m', 'langd_m']].to_string(index=False))


if __name__ == '__main__':
    main()
