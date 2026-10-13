# -*- coding: utf-8 -*-
"""A3 – Förslag på nya hållplatslägen samt markering av överflödiga hållplatser.

Nya hållplatser
  * Kandidatlägen var 50:e meter längs stadslinjernas nuvarande körvägar (gatunätet enligt OSRM, se
    s01_vagdragning.py; rak linje mellan hållplatser om vägdragning saknas), på land och minst 250 m från
    befintliga hållplatser på samma linje.
  * Nytta för ett läge = invånare som får hållplats inom 400 m (i dag ingen) + invånare som lyfts från svag
    tillgänglighet (1–29 avg/vardag) till minst 30 avg/vardag när linjens turer stannar i läget.
  * Lägen väljs girigt (störst nytta först, nyttan räknas om efter varje val så att samma invånare inte räknas
    två gånger), med minst 300 m mellan nya lägen, så länge nyttan är minst 40 invånare.
  * Otäckt befolkning som ligger mer än 400 m från stadslinjernas körvägar kan inte nås med nya hållplatser
    och redovisas som behov av ändrad linjesträckning (indata till kapitel 4).
  * För områden utom räckhåll redovisas ett indikativt hållplatsläge (befolkningsviktad tyngdpunkt).
Överflödiga hållplatser (stadslinjernas hållplatsområden) – prövas en i taget, lägst påstigande först:
  * Lågt påstigande (nödvändigt villkor): < 0,1 påstigande per vardag på stadslinjerna (92 vardagar).
  * Tät placering: avståndet mellan kvarvarande grannhållplatser på linjen blir högst 600 m efter indragning.
  * Liten unik täckning: < 25 invånare saknar annan busshållplats inom 400 m efter indragning.
  * Alla tre = kandidat för indragning; lågt påstigande + ett av de andra = bör prövas.
  * Undantag: centrum, vändplatser, hållplatser i startsegmentet (påstigandet underskattat, se kap. 1) och
    skol-/säsongshållplatser (mätperioden är sommar) blir högst 'bör prövas'.
Utdata: data/processed/a3_*.csv/.gpkg/.json
"""
import json
import math
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
from a1_od_granskning import vardagsurval  # noqa: E402
from a2_tackning import hallplatser_med_avgangar  # noqa: E402
import s01_vagdragning as V  # noqa: E402

VAG = V.segmentgeometri()   # körvägar längs gatunätet (OSRM) eller raka streck om vägdragning saknas

STEG_M = 50
MIN_AVST_BEFINTLIG = 250
MIN_AVST_NYA = 300
MIN_NYTTA = 30
MAX_NYA = 12
LAG_PAST = 0.1
MAX_LUCKA_M = 600
SASONG = ('skola', 'gymnasi', 'lyceum', 'idrott', 'yrkes', 'restaurangskolan', 'sportfält', 'hallen')
UNIK_MAX = 25


def stadsmonster():
    """Unika hållplatsföljder (stop_id) för stadslinjerna en typisk vardag, med turer per mönster."""
    g = D.gtfs(); t = D.turer_dag(None, C.STADSLINJER)
    st = g['stop_times'][g['stop_times'].trip_id.isin(t.trip_id)].sort_values(['trip_id', 'seq'])
    m = st.groupby('trip_id').stop_id.apply(tuple)
    lin = t.set_index('trip_id').linje
    ut = []
    for monster, turer in m.groupby(m).groups.items():
        ut.append({'monster': monster, 'turer': frozenset(turer), 'linje': lin.loc[list(turer)[0]]})
    return ut


def kandidater(monster, hpl_xy, land):
    """Kandidatpunkter längs segmenten; samma segment (stopp-par) i flera mönster slås ihop."""
    seg = {}
    for m in monster:
        for a, b in zip(m['monster'][:-1], m['monster'][1:]):
            k = (a, b)
            if k not in seg:
                seg[k] = {'turer': set(), 'linjer': set()}
            seg[k]['turer'] |= m['turer']; seg[k]['linjer'].add(m['linje'])
    rader = []
    for (a, b), v in seg.items():
        if a not in hpl_xy or b not in hpl_xy:
            continue
        xy = VAG.get((a, b), np.array([hpl_xy[a], hpl_xy[b]]))      # gatunätet (OSRM) om det finns
        d = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]); L = float(d[-1])
        for s in np.arange(STEG_M, L - STEG_M / 2, STEG_M):
            p = (np.interp(s, d, xy[:, 0]), np.interp(s, d, xy[:, 1]))
            rader.append({'x': p[0], 'y': p[1], 'turer': frozenset(v['turer']), 'linjer': ','.join(sorted(v['linjer'])),
                          'seg': f'{a}-{b}'})
    k = pd.DataFrame(rader)
    k = k[shapely.contains_xy(land, k.x.to_numpy(), k.y.to_numpy())].reset_index(drop=True)
    return k


def main():
    P = C.PROCESSED
    pkt = pd.read_csv(P / 'a2_delpunkter.csv.gz')
    land = D.land().union_all(); shapely.prepare(land)
    alla = hallplatser_med_avgangar()                 # alla bussars hållplatslägen med turmängder
    g = D.gtfs()['stops'].set_index('stop_id')
    sx, sy = D.till_metrisk(g.lon.values, g.lat.values)
    hpl_xy = {sid: (x, y) for sid, x, y in zip(g.index, sx, sy)}
    monster = stadsmonster()

    # ---------------- turmängd per delpunkt (nuläge, alla bussar)
    tree_h = cKDTree(alla[['x', 'y']].to_numpy())
    turer_h = alla.turer.to_numpy()
    grann = tree_h.query_ball_point(pkt[['x', 'y']].to_numpy(), C.TACKNING_M)
    cache = {}
    turmangd = []
    for gr in grann:
        key = tuple(sorted(gr))
        if key not in cache:
            cache[key] = frozenset().union(*[turer_h[j] for j in key]) if key else frozenset()
        turmangd.append(cache[key])
    pkt['turer'] = turmangd
    bef = pkt.bef.to_numpy()

    # ---------------- kandidater och girigt urval
    kand = kandidater(monster, hpl_xy, land)
    # avstånd till befintlig hållplats som trafikeras av kandidatens turer
    stad_stopp = {}
    for m in monster:
        for sid in m['monster']:
            stad_stopp.setdefault(sid, set()).update(m['turer'])
    sids = list(stad_stopp); tree_s = cKDTree(np.array([hpl_xy[s] for s in sids]))
    ok = []
    for r in kand.itertuples():
        idx = tree_s.query_ball_point([r.x, r.y], MIN_AVST_BEFINTLIG)
        ok.append(not any(stad_stopp[sids[j]] & r.turer for j in idx))
    kand = kand[np.array(ok)].reset_index(drop=True)
    tree_p = cKDTree(pkt[['x', 'y']].to_numpy())
    kand['pkt'] = tree_p.query_ball_point(kand[['x', 'y']].to_numpy(), C.TACKNING_M)
    nuvarande = list(pkt.turer)

    def nytta(r):
        ny = lyft = 0.0
        for j in r.pkt:
            fore = len(nuvarande[j]); efter = len(nuvarande[j] | r.turer)
            if fore == 0 and efter > 0:
                ny += bef[j]
            elif 1 <= fore <= 29 and efter >= 30:
                lyft += bef[j]
        return ny, lyft

    valda = []
    for _ in range(MAX_NYA):
        bast, bast_v = None, (0, 0)
        for i, r in kand.iterrows():
            if any(math.hypot(r.x - v['x'], r.y - v['y']) < MIN_AVST_NYA for v in valda):
                continue
            v = nytta(r)
            if sum(v) > sum(bast_v):
                bast, bast_v = i, v
        if bast is None or sum(bast_v) < MIN_NYTTA:
            break
        r = kand.loc[bast]
        for j in r.pkt:
            nuvarande[j] = nuvarande[j] | r.turer
        valda.append({'nr': len(valda) + 1, 'x': r.x, 'y': r.y, 'linjer': r.linjer, 'avgangar_vardag': len(r.turer),
                      'ny_tackning_inv': round(bast_v[0]), 'lyft_fran_svag_inv': round(bast_v[1]),
                      'nytta_inv': round(sum(bast_v)), 'segment': r.seg})
    nya = pd.DataFrame(valda)
    from pyproj import Transformer
    tr = Transformer.from_crs(C.CRS_METRISK, C.CRS_WGS84, always_xy=True)  # noqa: E501
    if len(nya):
        nya['lon'], nya['lat'] = tr.transform(nya.x.values, nya.y.values)
        # närmaste befintliga hållplats för beskrivning
        _, j = cKDTree(alla[['x', 'y']].to_numpy()).query(nya[['x', 'y']].to_numpy())
        nya['narmaste_befintliga'] = alla.namn.to_numpy()[j]
        nya['avst_narmaste_m'] = np.hypot(nya.x - alla.x.to_numpy()[j], nya.y - alla.y.to_numpy()[j]).round()

    # ---------------- otäckt befolkning utom räckhåll för stadslinjernas körvägar
    efter_n = np.array([len(t) for t in nuvarande])
    pkt['efter_avg'] = efter_n
    korvag = shapely.MultiLineString([VAG.get((a, b), np.array([hpl_xy[a], hpl_xy[b]])) for m in monster
                                      for a, b in zip(m['monster'][:-1], m['monster'][1:])
                                      if a in hpl_xy and b in hpl_xy and a != b])
    o = pkt[(efter_n == 0) & pkt.mariehamn].copy()
    o['d_korvag'] = shapely.distance(korvag, shapely.points(o.x.to_numpy(), o.y.to_numpy()))
    utom = o[o.d_korvag > C.TACKNING_M]
    behov = utom.groupby('ruta_id').agg(inv=('bef', 'sum'), x=('x', 'mean'), y=('y', 'mean'), d_korvag=('d_korvag', 'median'))
    behov = behov[behov.inv >= 75].sort_values('inv', ascending=False).round(0)
    _, j = cKDTree(alla[['x', 'y']].to_numpy()).query(behov[['x', 'y']].to_numpy())
    behov['narmaste_hpl'] = alla.namn.to_numpy()[j]

    # ---------------- överflödiga hållplatser (sekventiell prövning)
    om = D.hallplatsomraden()
    s = vardagsurval(C.STADSLINJER)
    past = s.groupby('omrade').P.sum() / C.ANTAL_VARDAGAR
    har_data = set(s.omrade)
    omr_av = {sid: om['omrade'].get(sid, g.loc[sid, 'stop_name']) for sid in hpl_xy}
    try:
        startseg = set(z for v in json.load(open(P / 'a1_sammanfattning.json'))['startsegment_bas'].values() for z in v)
    except Exception:
        startseg = set()
    sekvenser = [[(omr_av.get(sid), hpl_xy[sid]) for sid in m['monster'] if sid in hpl_xy] for m in monster]
    linjer_omr, xy_omr = {}, {}
    for m in monster:
        for sid in m['monster']:
            linjer_omr.setdefault(omr_av.get(sid), set()).add(m['linje'])
            if sid in hpl_xy:
                xy_omr.setdefault(omr_av.get(sid), []).append(hpl_xy[sid])
    alla_omr = np.array([omr_av.get(sid) for sid in alla.index])
    stad_omr = set(linjer_omr)

    def lucka(z, borttagna):
        """Största avstånd mellan kvarvarande grannar runt z (på alla mönster där z ingår)."""
        st = 0.0
        for seq in sekvenser:
            kvar = [(q, p) for q, p in seq if q not in borttagna or q == z]
            for i, (q, p) in enumerate(kvar):
                if q == z and 0 < i < len(kvar) - 1:
                    a, b = kvar[i - 1][1], kvar[i + 1][1]
                    st = max(st, math.hypot(a[0] - b[0], a[1] - b[1]))
        return st

    def unik_tackning(z, borttagna):
        """Invånare som saknar annan hållplats inom 400 m om z (och redan borttagna) dras in från stadslinjerna.
        Hållplatser som även trafikeras av landsbygdslinjer finns kvar för dem."""
        tot = 0.0
        for gr, b in zip(grann, bef):
            if not gr:
                continue
            o = set(alla_omr[gr])
            if z in o:
                kvar = {q for q in o if q not in borttagna and q != z}
                if not kvar and all(set(alla.linjer.iat[j].split(',')) <= set(C.STADSLINJER) for j in gr):
                    tot += b
        return tot

    bedom = {}
    borttagna = set()
    ordning = sorted((z for z in stad_omr if z is not None and z in xy_omr), key=lambda z: (past.get(z, 0.0), z))
    for z in ordning:
        lag = past.get(z, 0.0) < LAG_PAST
        L = lucka(z, borttagna); U = unik_tackning(z, borttagna)
        k2, k3 = L <= MAX_LUCKA_M, U < UNIK_MAX
        undantag = z == C.CENTRUM or 'vändplan' in z.lower()
        sasong = any(w in z.lower() for w in SASONG)
        if undantag:
            bed = 'Undantas (ändhållplats/vändplats)'
        elif z not in har_data:
            bed = 'Saknar påstigningsdata'
        elif lag and k2 and k3 and not (z in startseg or sasong):
            bed = 'Kandidat för indragning'; borttagna.add(z)
        elif lag and (k2 or k3):
            bed = 'Bör prövas'
        else:
            bed = 'Behålls'
        orsak = []
        if z in startseg:
            orsak.append('påstigande underskattat (startsegment, kap. 1)')
        if sasong:
            orsak.append('skol-/säsongsberoende, sommardata')
        p = np.mean(xy_omr[z], axis=0)
        bedom[z] = {'omrade': z, 'linjer': ','.join(sorted(linjer_omr[z])), 'x': p[0], 'y': p[1],
                    'pastigande_vardag': round(past.get(z, 0.0), 3), 'lucka_efter_indragning_m': round(L),
                    'unik_tackning_inv': round(U), 'lagt_pastigande': lag, 'lucka_ok': k2, 'liten_unik_tackning': k3,
                    'bedomning': bed, 'kommentar': '; '.join(orsak)}
    ov = pd.DataFrame(bedom.values()).sort_values(['bedomning', 'pastigande_vardag', 'omrade'])
    ov['lon'], ov['lat'] = tr.transform(ov.x.values, ov.y.values)

    # ---------------- indikativa hållplatslägen i områden som kräver ändrad linjesträckning
    tp = utom.groupby('ruta_id').apply(lambda d: pd.Series({'x': np.average(d.x, weights=d.bef), 'y': np.average(d.y, weights=d.bef)}))
    behov = behov.drop(columns=['x', 'y']).join(tp)
    behov['lon'], behov['lat'] = tr.transform(behov.x.values, behov.y.values)

    # ---------------- spara
    nya.to_csv(P / 'a3_nya_hallplatser.csv', index=False)
    behov.to_csv(P / 'a3_behov_ny_linjestrackning.csv')
    gpd.GeoDataFrame(behov.reset_index(), geometry=gpd.points_from_xy(behov.x, behov.y), crs=C.CRS_METRISK) \
        .to_file(P / 'a3_hallplatsforslag.gpkg', layer='behov_ny_linjestrackning', driver='GPKG')
    ov.to_csv(P / 'a3_hallplatsbedomning.csv', index=False)
    gpd.GeoDataFrame(nya.drop(columns=['segment']), geometry=gpd.points_from_xy(nya.x, nya.y), crs=C.CRS_METRISK) \
        .to_file(P / 'a3_hallplatsforslag.gpkg', layer='nya_hallplatser', driver='GPKG')
    gpd.GeoDataFrame(ov, geometry=gpd.points_from_xy(ov.x, ov.y), crs=C.CRS_METRISK) \
        .to_file(P / 'a3_hallplatsforslag.gpkg', layer='hallplatsbedomning', driver='GPKG')
    mh = pkt.mariehamn
    res = {'nya_hallplatser': int(len(nya)),
           'ny_tackning_inv': int(nya.ny_tackning_inv.sum()) if len(nya) else 0,
           'lyft_fran_svag_inv': int(nya.lyft_fran_svag_inv.sum()) if len(nya) else 0,
           'mariehamn_inom_400m_fore': round(float(pkt.loc[mh & (pkt.avg_alla > 0), 'bef'].sum() / pkt.loc[mh, 'bef'].sum()), 4),
           'mariehamn_inom_400m_efter': round(float(pkt.loc[mh & (efter_n > 0), 'bef'].sum() / pkt.loc[mh, 'bef'].sum()), 4),
           'mariehamn_svag_fore': round(float(pkt.loc[mh & pkt.avg_alla.between(1, 29), 'bef'].sum() / pkt.loc[mh, 'bef'].sum()), 4),
           'mariehamn_svag_efter': round(float(pkt.loc[mh & (efter_n >= 1) & (efter_n <= 29), 'bef'].sum() / pkt.loc[mh, 'bef'].sum()), 4),
           'otackt_utom_korvag_inv': int(utom.bef.sum()),
           'bedomning': ov.bedomning.value_counts().to_dict()}
    with open(P / 'a3_sammanfattning.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print(nya.drop(columns=['segment', 'x', 'y']).to_string(index=False))
    print(behov.to_string())
    print(ov[ov.bedomning.isin(['Kandidat för indragning', 'Bör prövas', 'Saknar påstigningsdata'])]
          .drop(columns=['x', 'y', 'lon', 'lat', 'lagt_pastigande']).to_string(index=False))


if __name__ == '__main__':
    main()
