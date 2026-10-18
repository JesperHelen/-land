# -*- coding: utf-8 -*-
"""B4.5 – Sammanslagning av linje N och S (genomgående linje N–S) tillsammans med Bo-Bil och nordöstra områden.

Frågor (PROGRESS.md, B4.5)
  1. Ryms linje N via Bo-Bil (UA 3) om N och S slås ihop till en genomgående linje (bussen fortsätter N → S)?
  2. Räcker N:s tidsutrymme (3,5 min med bibehållen puls) – och hur mycket mer ger en genomgående linje där S får
     starta när N har kommit tillbaka (utan puls), eventuellt med indragna hållplatser på S (A3: Gröna Udden, Torggatan,
     Neptunigatan, Skillnadsgatan, Hamngatan) – för att nå Örtvägen (4,4 min) och Lillåkersvägen (6,5 min)?
  3. Varianter utan puls: N/S (7,5 min) och S/Ö (10,5 min) enligt beställarens överslag, omräknade med kravet på
     5 min i centrum per varv; S/Ö prövas mot Ö:s områden (Solberget, Strömsnäs).
Metod (som V–Ö i b4_omlopp.genomgaende_ryms)
  * Dagens omlopp ligger fast (varje N-tur fortsätter som den S-tur som samma buss kör i dag, N → S i 21 av 22 fall).
    Varv = N-tur + S-turen bussen fortsätter med. Kravet: hela varvet inom timmen med minst MARGINAL_VARV = 5 min
    i centrum (genomgången N → S 0,5 min plus uppehållet före bussens nästa avgång), eller minst som i dag.
  * Policy för S: 'puls' (S avgår som i dag, högst 2 min senare) | 'fri' (S startar när N har kommit tillbaka,
    ingen gräns efter pulsen) | 'fri + S-indragning' (som 'fri', och de fem A3-kandidaterna på S dras in – 0,5 min
    kortare körtid per indragen hållplats som turen passerar, samma uppehållstid som en ny hållplats får i UA 2).
  * 'N ensam': ingen sammanslagning; N-turerna får tillägget om omloppet (b4_omlopp.bygg_omlopp) fortfarande
    ryms med dagens antal fordon och omloppstid (turer_som_ryms).
  * Behövd tilläggstid för Örtvägen, Lillåkersvägen och Österkalmare: b4_sammanslagning.omraden (2 × avstånd × 1,3 /
    25 km/h + 0,5 min). Bo-Bil (UA 3) +0,1 min per tur ingår i alla N-scenarier.
  * Tillkommande täckning: ny hållplats i områdets mittpunkt (indikativt, A3) som trafikeras av de N-turer som ryms.
    Indragningen av S-hållplatser: täckningsförlust enligt delpunkterna (A2).
  * Kostnad: samma enhetskostnader som B5 (bas), förändrad omloppstid och fordonskm mot i dag.
Utdata: data/processed/b4_ns.json, b4_ns_kurva.csv, b4_ns_scenarier.csv, b4_ns.gpkg; GeoJSON i output/gis/geojson/b4_ns_*.geojson;
        output/kartor/b4_16_ns_karta.png, b4_17_ns_omlopp.png
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import shapely  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from shapely.geometry import LineString, Point  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402
import b4_omlopp as O  # noqa: E402
import b4_natverk as N  # noqa: E402
import b4_ua as F  # noqa: E402
import b4_sammanslagning as SS  # noqa: E402
import b5_kalkyl as B5  # noqa: E402
import kartlib as K  # noqa: E402
from a2_tackning import avgangar_inom, hallplatser_med_avgangar, klass  # noqa: E402

P = C.PROCESSED
GEOJSON = C.ROT / 'output' / 'gis' / 'geojson'
S_KANDIDATER = ['Gröna Udden', 'Torggatan', 'Neptunigatan', 'Skillnadsgatan', 'Hamngatan']   # A3, kandidater för indragning på S
SPARAD_PER_HPL = F.UPPEHALL          # min per indragen hållplats och tur
PULS_TOL = 2.0                       # min – 'puls': S avgår högst så mycket efter dagens avgång
KURVA_D = np.arange(0, 10.01, 0.5)
OMRADEN_N = ['Örtvägen', 'Lillåkersvägen', 'Österkalmare']
OMRADEN_O = ['Solberget', 'Solberget södra', 'Strömsnäs']
POLICY = [('ensam', 'N ensam (dagens omlopp)'), ('puls', 'N–S, S i pulsen (≤ 2 min senare)'),
          ('fri', 'N–S, S startar när N kommit tillbaka'), ('fri_s', 'N–S, som ovan + S-hållplatser indragna')]


# ====================================================================== underlag
def s_indragning(t):
    """S-hållplatserna som kan dras in och körtidsbesparing per S-tur: ({trip_id: −min}, [stop_id], DataFrame)."""
    om = D.hallplatsomraden()['omrade']
    stopp = [s for s, o in om.items() if o in S_KANDIDATER]
    ut, ids = {}, set()
    for r in t[t.linje == 'S'].itertuples():
        n = [s for s in r.monster if s in set(stopp)]
        if n:
            ut[r.trip_id] = -SPARAD_PER_HPL * len(n); ids.update(n)
    return ut, sorted(ids), om


def fordelning_par(t, plan, a, b):
    p = plan.reset_index(drop=True); nx = p.nasta.to_numpy(); lin = p.linje.to_numpy()
    return int(sum(1 for i in np.where(lin == a)[0] if nx[i] >= 0 and lin[nx[i]] == b)), int((lin == a).sum())


def tackning_borttag(pkt, hpl0, stop_ids, trip_ids):
    """Täckningsförändring när S-turerna slutar stanna vid stop_ids (delpunkter 50 m, A2)."""
    h = hpl0.copy(); tn = frozenset(trip_ids)
    for s in stop_ids:
        if s in h.index:
            h.at[s, 'turer'] = h.at[s, 'turer'] - tn
    h = h[h.turer.map(len) > 0]
    xy = hpl0.loc[[s for s in stop_ids if s in hpl0.index], ['x', 'y']].to_numpy()
    d = np.min(np.hypot(pkt.x.to_numpy()[:, None] - xy[None, :, 0], pkt.y.to_numpy()[:, None] - xy[None, :, 1]), axis=1)
    p = pkt[d <= 1500].copy()
    p['avg_efter'], _ = avgangar_inom(p, h); p['klass_efter'] = p.avg_efter.map(klass); p['klass_fore'] = p.klass
    s_ = lambda m: round(float(p.loc[m, 'bef'].sum()))
    return {'forlorad_tackning_inv': s_((p.avg_alla > 0) & (p.avg_efter == 0)),
            'samre_klass_inv': s_(p.klass_efter < p.klass_fore), 'battre_klass_inv': s_(p.klass_efter > p.klass_fore)}


# ====================================================================== omlopp
def prova(t, plan0, r, ref, linje, partner, kand, d, policy, sol=None, marginal=O.MARGINAL_VARV, plan_ensam=None):
    """Turer (av kand) som ryms med tillägget d min per tur under policyn. Returnerar (turer, skift, dd, plan)."""
    if policy == 'ensam':
        v = O.turer_som_ryms(t, kand, d, r, referens=ref)
        dd = {k: d for k in v}
        plan = O.bygg_omlopp(O.med_andring(t, dd), referens=ref)
        return v, {}, dd, plan
    bas = dict(sol) if policy == 'fri_s' and sol else {}
    ms = {'puls': PULS_TOL, 'fri': None, 'fri_s': None}[policy]
    v, sk = O.genomgaende_ryms(t, kand, d, plan0, partner=partner, max_skift=ms, bas=bas, marginal=marginal, linje=linje)
    dd = dict(bas)
    for k in v:
        dd[k] = dd.get(k, 0.0) + d
    plan = O.plan_fast(plan0.reset_index(drop=True), O.med_andring(t, dd, sk))
    return v, sk, dd, plan


def med_km(plan, v, km_tillagg, km_bobil):
    """Fordonskm: Bo-Bil (km_bobil per N-tur, alla N-turer) och omvägen (km_tillagg på turerna v)."""
    p = plan.copy()
    p['km'] = p.km + np.where(p.linje == 'N', km_bobil, 0.0) + np.where(p.trip_id.isin(set(v)), km_tillagg, 0.0)
    return p


def min_centrum(plan, linje, partner, turer):
    c = O.varv_vo(plan, linje, partner).set_index('trip_id').centrum_min.reindex(turer)
    c = c[np.isfinite(c)]
    return round(float(c.min()), 1) if len(c) else None


def kostnad(nt0, nt1, km_per_tur, n_turer):
    d_h = (nt1['omloppstid_h'] - nt0['omloppstid_h']) * B5.VARDAGAR
    d_km = (nt1['km'] - nt0['km']) * B5.VARDAGAR + B5.LORDAGSTURER * km_per_tur * (n_turer / 22) * B5.LORDAGAR
    e = B5.ENHET
    return {'delta_fordon': nt1['fordon'] - nt0['fordon'], 'delta_fordonstimmar_ar': round(d_h), 'delta_km_ar': round(d_km),
            'drift_ar_bas_eur': round((nt1['fordon'] - nt0['fordon']) * e['fordon_per_ar']['bas'] + d_h * e['per_fordonstimme']['bas']
                                      + d_km * e['per_km']['bas'])}


# ====================================================================== huvudflöde
def main():
    GEOJSON.mkdir(parents=True, exist_ok=True)
    t = O.turer(); ref_plan = O.bygg_omlopp(t); ref = O.kopplingar(ref_plan); r = O.ram(t)
    plan0 = O.bygg_omlopp(t, referens=ref); nt0 = O.nyckeltal(plan0)
    prof = SS.linjeprofil()
    sol, sol_hpl, omr_namn = s_indragning(t)
    tl = t.set_index('trip_id')
    n_trips = list(t[t.linje == 'N'].trip_id)
    kopp_ns = fordelning_par(t, plan0, 'N', 'S')
    xy = F.stopp_xy(); pkt = pd.read_csv(P / 'a2_delpunkter.csv.gz'); hpl0 = hallplatser_med_avgangar()
    bobil = F.bobil_delta(xy); d_bobil = bobil['delta_min']

    # ---- 1. parvis tidsutrymme utan puls (varv inom timmen), marginal 5 min (krav) och 3,5 min (beställarens överslag)
    par = []
    for a, b in [('N', 'S'), ('S', 'Ö'), ('V', 'Ö'), ('N', 'V'), ('N', 'Ö'), ('S', 'V')]:
        ta, tb = prof[a]['kortid_median'], prof[b]['kortid_median']
        par.append({'par': f'{a}/{b}', 'kortid_a': ta, 'kortid_b': tb, 'summa_min': ta + tb,
                    'utrymme_marginal_5': 60 - O.MARGINAL_VARV - ta - tb, 'utrymme_marginal_3_5': 60 - 3.5 - ta - tb,
                    'utrymme_puls_a': min(60 - O.MARGINAL_VARV - ta - tb, 30 - O.GENOMGANG_MIN - ta),
                    'utrymme_puls_b': min(60 - O.MARGINAL_VARV - ta - tb, 30 - O.GENOMGANG_MIN - tb)})
    par = pd.DataFrame(par)

    # ---- 2. kurva: antal N-turer som ryms vid tillägget d, per policy (Bo-Bil ingår ej här)
    kurva = []
    for pol, _ in POLICY:
        for d in KURVA_D:
            v, sk, _, plan = prova(t, plan0, r, ref, 'N', 'S', n_trips, float(d), pol, sol)
            kurva.append({'policy': pol, 'tillagg_min': float(d), 'turer': len(v), 'turer_tot': len(n_trips),
                          'min_centrum_min': min_centrum(plan, 'N', 'S', v) if pol != 'ensam' else None,
                          'max_skift_s_min': round(max(sk.values()), 1) if sk else 0.0})
    kurva = pd.DataFrame(kurva)
    # marginalkänslighet: största d där alla (≥ 21 av 22) N-turer ryms, fri policy
    maxd = {}
    for m in (3.5, 5.0):
        ok = [float(d) for d in KURVA_D if len(prova(t, plan0, r, ref, 'N', 'S', n_trips, float(d), 'fri', sol, marginal=m)[0]) >= 21]
        maxd[f'{m:g}'] = max(ok)

    # ---- 3. scenarier: Bo-Bil + område
    omr = pd.read_csv(P / 'b4_sammanslagning_omraden.csv').set_index('omrade')
    omv = SS.omraden(prof).set_index('omrade')
    rader, planer, geo_h = [], {}, []
    s_trips = list(t[t.linje == 'S'].trip_id)
    sol_tk = tackning_borttag(pkt, hpl0, sol_hpl, s_trips)
    for namn in OMRADEN_N:
        o = omv.loc[namn]; behov = float(o.behov_min_per_tur); d = round(behov + d_bobil, 1)
        km = round(2 * float(o.avstand_m) * SS.OMVAG / 1000, 2)
        for pol, ptxt in POLICY:
            v, sk, dd, plan = prova(t, plan0, r, ref, 'N', 'S', n_trips, d, pol, sol)
            plan = med_km(plan, v, km, bobil['delta_km'])
            nt = O.nyckeltal(plan)
            nytk = {}
            if v:
                f = {'typ': 'ny', 'linje': 'N', 'xy': (float(o.x), float(o.y)), 'hpl_namn': namn}
                nytk, _ = F.tackning(pkt, hpl0, f, v, xy)
            rader.append({'omrade': namn, 'inv_utan_tackning': float(o.inv), 'behov_min_per_tur': behov, 'bobil_min': d_bobil,
                          'tillagg_min': d, 'policy': pol, 'policy_text': ptxt, 'turer': len(v), 'turer_tot': len(n_trips),
                          'turer_som_i_dag': ', '.join(O.hm(tl.at[x, 'avg']) for x in sorted(set(n_trips) - set(v), key=lambda x: tl.at[x, 'avg'])),
                          'fordon': nt['fordon'], 'omloppstid_h': nt['omloppstid_h'],
                          'min_centrum_min': min_centrum(plan, 'N', 'S', v) if pol != 'ensam' else None,
                          's_senare_max_min': round(max(sk.values()), 1) if sk else 0.0,
                          's_turer_senare': len(sk), 's_hpl_indragna': pol == 'fri_s',
                          'ny_tackning_inv': nytk.get('ny_tackning_inv', 0), 'lyft_fran_svag_inv': nytk.get('lyft_fran_svag_inv', 0),
                          'battre_klass_inv': nytk.get('battre_klass_inv', 0),
                          **{k: v_ for k, v_ in kostnad(nt0, nt, km, len(v)).items()}})
            planer[(namn, pol)] = (plan, set(v), sk)
            rader[-1]['km_per_tur'] = km
    sc = pd.DataFrame(rader)
    # bara Bo-Bil + N–S (utan nytt område)
    v, sk, dd, plan = prova(t, plan0, r, ref, 'N', 'S', n_trips, d_bobil, 'fri', sol)
    bb = {'tillagg_min': d_bobil, 'turer': len(v), 'turer_tot': len(n_trips), 'min_centrum_min': min_centrum(plan, 'N', 'S', v)}
    vp, _, _, pp = prova(t, plan0, r, ref, 'N', 'S', n_trips, d_bobil, 'puls', sol)
    bb['turer_puls'] = len(vp)

    # ---- 4. utan puls: S/Ö (omlopp byggt med paren S↔Ö och N↔V)
    par_so = (('S', 'Ö'), ('Ö', 'S'), ('N', 'V'), ('V', 'N'))
    plan_so = O.bygg_omlopp(t, par=par_so, referens=ref); nt_so = O.nyckeltal(plan_so)
    o_trips = list(t[t.linje == 'Ö'].trip_id)
    kopp_so = fordelning_par(t, plan_so, 'Ö', 'S')
    so = []
    for namn in OMRADEN_O:
        o = omv.loc[namn]; behov = float(o.behov_min_per_tur)
        for pol in ('puls', 'fri', 'fri_s'):
            for m in (3.5, 5.0):
                v, sk, dd, plan = prova(t, plan_so, r, ref, 'Ö', 'S', o_trips, behov, pol, sol, marginal=m)
                so.append({'omrade': namn, 'behov_min_per_tur': behov, 'policy': pol, 'marginal_min': m, 'turer': len(v),
                           'turer_tot': len(o_trips), 's_senare_max_min': round(max(sk.values()), 1) if sk else 0.0})
    so = pd.DataFrame(so)
    maxd_so = {}
    for m in (3.5, 5.0):
        for pol in ('fri', 'fri_s'):
            ok = [float(d) for d in KURVA_D if len(prova(t, plan_so, r, ref, 'Ö', 'S', o_trips, float(d), pol, sol, marginal=m)[0]) >= 18]
            maxd_so[f'{pol}_{m:g}'] = max(ok) if ok else None

    # ---- 5. resenärer: genomgående N/S och S/Ö
    zoner = list(pd.read_csv(P / 'a1_restider_min.csv', index_col=0).index)
    mon0 = N.monster(); nat0 = N.Nat(mon0, zoner); fak = N.dagsfaktor()
    gen = {}
    for a, b in (('N', 'S'), ('S', 'Ö')):
        j = N.jamfor(nat0, N.Nat(N.genomgaende(mon0, a, b, O.GENOMGANG_MIN), zoner))
        mu = lambda k: float(np.mean([j[p][k] for p in ('FM', 'EM')])) * fak
        gen[f'{a}/{b}'] = {'resor_slipper_byte_vardag': round(mu('resor_kortare_h'), 1),
                           'resenarsminuter_sparade_vardag': round(-mu('resenarsminuter_h'), 1)}

    res = {'dagens_kopplingar_N_till_S': kopp_ns, 'dagens_kopplingar_Ö_till_S_i_alternativt_omlopp': kopp_so,
           'omlopp_idag': nt0, 'omlopp_par_SO_NV': nt_so,
           'sparad_tid_s_indragning': {'hpl': sol_hpl, 'turer': len(sol), 'min_per_hpl': SPARAD_PER_HPL,
                                       'max_min_per_tur': float(max(-v for v in sol.values())), 'tackning': sol_tk,
                                       'omraden': S_KANDIDATER},
           'bobil_med_ns': bb, 'bobil_delta': bobil, 'max_tillagg_alla_turer_fri': maxd, 'max_tillagg_so_fri': maxd_so,
           'genomgaende_resor': gen, 'par': par.round(2).to_dict('records'),
           'scenarier': sc.to_dict('records'), 'so_omraden': so.to_dict('records')}
    with open(P / 'b4_ns.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=float)
    kurva.to_csv(P / 'b4_ns_kurva.csv', index=False); sc.to_csv(P / 'b4_ns_scenarier.csv', index=False)
    so.to_csv(P / 'b4_ns_so.csv', index=False); par.to_csv(P / 'b4_ns_par.csv', index=False)

    # ---- GIS
    gis(t, omv, sc, xy, sol_hpl, omr_namn, hpl0, sol)
    print(par.round(1).to_string()); print(json.dumps({k: res[k] for k in res if k not in ('scenarier', 'so_omraden', 'par', 'omlopp_idag')},
                                                      ensure_ascii=False, indent=1, default=float)[:3500])
    print(sc[['omrade', 'policy', 'tillagg_min', 'turer', 'fordon', 'min_centrum_min', 's_senare_max_min', 'ny_tackning_inv',
              'lyft_fran_svag_inv', 'drift_ar_bas_eur']].to_string())
    print(so.to_string())
    print(kurva.pivot(index='tillagg_min', columns='policy', values='turer').to_string())
    print(figur_karta(t, omv, sc, kurva, xy, sol_hpl, sol_tk, maxd))
    print(figur_omlopp(plan0, planer, sc))


# ====================================================================== GIS (GeoPackage + GeoJSON)
def skriv_geo(gdf, namn):
    gdf.to_file(P / 'b4_ns.gpkg', layer=namn, driver='GPKG')
    gdf.to_crs(4326).to_file(GEOJSON / f'b4_ns_{namn}.geojson', driver='GeoJSON')


def gis(t, omv, sc, xy, sol_hpl, omr_namn, hpl0, sol):
    import s01_vagdragning as V
    gp = P / 'b4_ns.gpkg'
    if gp.exists():
        gp.unlink()
    sg = V.segmentgeometri(); hxy = V.alla_xy()[0]; mon = V.monster_per_linje()
    kedja = lambda s: [sg.get((a, b), np.array([hxy[a], hxy[b]])) for a, b in zip(s[:-1], s[1:])]
    n_, s_ = list(mon['N'][0][0]), list(mon['S'][0][0])
    ml = lambda d: shapely.MultiLineString([LineString(x) for x in d])
    lin = gpd.GeoDataFrame([{'linje': 'N', 'beskrivning': 'Linje N, dagens sträckning'},
                            {'linje': 'S', 'beskrivning': 'Linje S, dagens sträckning'},
                            {'linje': 'N–S', 'beskrivning': 'Genomgående linje N–S (N följt av S, bussen fortsätter i centrum)'}],
                           geometry=[ml(kedja(n_)), ml(kedja(s_)), ml(kedja(n_) + kedja(s_))], crs=C.CRS_METRISK)
    skriv_geo(lin, 'linjer')
    rad = []
    for namn, d in sc.groupby('omrade'):
        o = omv.loc[namn]
        r = {'omrade': namn, 'linje': 'N', 'inv': float(o.inv), 'behov_min_per_tur': float(o.behov_min_per_tur),
             'tillagg_inkl_bobil_min': float(d.tillagg_min.iloc[0]), 'geometry': Point(float(o.x), float(o.y))}
        for _, x in d.iterrows():
            r[f'turer_{x.policy}'] = int(x.turer); r[f'ny_tackning_inv_{x.policy}'] = int(x.ny_tackning_inv)
        r['turer_tot'] = int(d.turer_tot.iloc[0])
        rad.append(r)
    skriv_geo(gpd.GeoDataFrame(rad, crs=C.CRS_METRISK), 'omraden')
    s_tab = hpl0.loc[[s for s in sol_hpl if s in hpl0.index]]
    skriv_geo(gpd.GeoDataFrame({'hpl': [omr_namn[s] for s in s_tab.index], 'stop_id': s_tab.index,
                                'sparad_min_per_hpl_och_tur': SPARAD_PER_HPL},
                               geometry=gpd.points_from_xy(s_tab.x, s_tab.y), crs=C.CRS_METRISK), 'sandragna_hpl')


# ====================================================================== figurer
def figur_karta(t, omv, sc, kurva, xy, sol_hpl, sol_tk, maxd):
    fig = plt.figure(figsize=(13.8, 8.0))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 0.95], wspace=0.12, left=0.02, right=0.985, top=0.9, bottom=0.17)
    ax = fig.add_subplot(gs[0])
    K.ny_karta((106000, 112300, 6682300, 6688200), ax=ax, titel='Linje N–S: nordöstra områden och S-hållplatser som kan dras in')
    K.rita_linjer(ax, lw=1.9, zorder=4)
    farg = {0: '#c0392b', 1: '#e8890c', 2: '#2f9e44'}
    pts = []
    for namn in OMRADEN_N:
        d = sc[sc.omrade == namn].set_index('policy')
        o = omv.loc[namn]
        frac = {p: d.at[p, 'turer'] / d.at[p, 'turer_tot'] for p in ('puls', 'fri', 'fri_s')}
        k = 2 if frac['puls'] >= 0.9 else 1 if (frac['fri'] >= 0.9 or frac['fri_s'] >= 0.9) else 0
        ax.scatter([o.x], [o.y], s=60 + o.inv * 0.9, marker='D', color=farg[k], edgecolor='white', lw=0.8, zorder=8)
        txt = (f"{namn} ({int(round(o.inv, -1))} inv.), +{str(d.tillagg_min.iloc[0]).replace('.', ',')} min\n"
               f"turer: S i pulsen {d.at['puls', 'turer']}, fri {d.at['fri', 'turer']}, + indragning {d.at['fri_s', 'turer']} av {d.turer_tot.iloc[0]}")
        pts.append((txt, (o.x, o.y), 60))
    ax.scatter(xy.loc[sol_hpl, 'x'], xy.loc[sol_hpl, 'y'], s=34, marker='X', color='#7a776f', edgecolor='white', lw=0.6, zorder=8)
    K.placera_etiketter(ax, pts, fontsize=6.6, undvik=K.punkt_hinder(ax, [p[1][0] for p in pts], [p[1][1] for p in pts], px=9))
    h = [Line2D([], [], marker='D', ls='', color=farg[2], markersize=7, label='Ryms (≥ 90 % av N-turerna) med S i pulsen'),
         Line2D([], [], marker='D', ls='', color=farg[1], markersize=7, label='Ryms först när S får starta senare / S-hållplatser dras in'),
         Line2D([], [], marker='D', ls='', color=farg[0], markersize=7, label='Ryms inte (kräver större omläggning)'),
         Line2D([], [], marker='X', ls='', color='#7a776f', markersize=7, label='S-hållplats som kan dras in (A3)')]
    h += [Line2D([], [], color=C.FARG_LINJE[l], lw=2, label=f'Linje {l}') for l in C.STADSLINJER]
    ax.legend(handles=h, loc='upper left', bbox_to_anchor=(0.0, -0.01), ncol=2, fontsize=6.8, frameon=False)
    K.ram(ax)

    ax2 = fig.add_subplot(gs[1])
    stil = {'ensam': ('#9a968c', '-', 'N ensam (dagens omlopp)'), 'puls': ('#1c5cab', '-', 'N–S, S i pulsen'),
            'fri': ('#159a9c', '-', 'N–S, S startar när N kommit tillbaka'), 'fri_s': ('#2f9e44', '--', 'N–S, fri + S-hållplatser indragna')}
    for pol, (c, ls, lbl) in stil.items():
        k = kurva[kurva.policy == pol]
        ax2.plot(k.tillagg_min, k.turer, color=c, ls=ls, lw=2, label=lbl, drawstyle='steps-post')
    for namn in OMRADEN_N:
        x = float(omv.at[namn, 'behov_min_per_tur'])
        ax2.axvline(x, color='#52514e', lw=0.7, ls=':'); ax2.text(x + 0.08, 1.0, namn, rotation=90, fontsize=7, va='bottom', color=K.TEXT)
    ax2.set_xlabel('tillägg per N-tur (min)', fontsize=8); ax2.set_ylabel('antal N-turer som ryms (av 22)', fontsize=8)
    ax2.set_xlim(0, 10); ax2.set_ylim(0, 23.5); ax2.tick_params(labelsize=7.5)
    ax2.grid(color='#e6e4de', lw=0.6); ax2.set_axisbelow(True)
    for s in ['top', 'right']:
        ax2.spines[s].set_visible(False)
    ax2.legend(loc='upper right', fontsize=7.2, frameon=False)
    ax2.set_title('Hur lång omväg ryms? (varvet N + S inom timmen, ≥ 5 min i centrum)', loc='left', fontsize=9.5, fontweight='bold')
    fig.suptitle('Genomgående linje N–S med Bo-Bil – Örtvägen, Lillåkersvägen och Österkalmare', x=0.01, ha='left', fontsize=12.5,
                 fontweight='bold')
    ut = C.KARTOR / 'b4_16_ns_karta.png'
    fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


def figur_omlopp(plan0, planer, sc):
    # Lillåkersvägen (störst omväg som ryms med indragning) före/efter
    val = [('Örtvägen', 'fri'), ('Lillåkersvägen', 'fri_s')]
    fig, axs = plt.subplots(3, 1, figsize=(12.4, 8.6), gridspec_kw={'hspace': 0.5})
    O.rita_omlopp(axs[0], plan0, titel='Dagens omlopp')
    for ax, (namn, pol) in zip(axs[1:], val):
        plan, v, sk = planer[(namn, pol)]
        row = sc[(sc.omrade == namn) & (sc.policy == pol)].iloc[0]
        txt = {'fri': 'S startar när N kommit tillbaka', 'fri_s': 'S startar när N kommit tillbaka, S-hållplatser indragna'}[pol]
        O.rita_omlopp(ax, plan, titel=f'Linje N–S med Bo-Bil och {namn} (+{row.tillagg_min:g} min per N-tur, {row.turer} av {row.turer_tot} turer) – {txt}',
                      andrade=v)
    O.omlopp_forklaring(fig, y=-0.01)
    ut = C.KARTOR / 'b4_17_ns_omlopp.png'
    fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


if __name__ == '__main__':
    main()
