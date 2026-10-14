# -*- coding: utf-8 -*-
"""B4 – Enskilda linjeförslag: individuella effekter och verifiering mot dagens omlopp.

Förslag (beställarens urval efter granskningen av Fas A, 2026-10-14)
  1a  Linje V till ny hållplats i Möckelö Strand via dagens gatunät (restid 3 min till hållplatsen).
  1b  Som 1a men med Norrgårdsvägen förlängd till Hamnskärsvägen (restid 1 min till hållplatsen).
  2   Ny hållplats N2 på linje Ö (mellan Österkullagatan och Kalmarnäs vändplan, läge enligt A3).
  3   Linje N trafikerar Bo-Bil i stället för Vikingagränd (Maxinge – Bo-Bil – Bolstavägen), så att bussen
      inte behöver vänta vid Nya Godbyvägen.
Antaganden
  * Möckelö Strand: bussen kör från dagens vändpunkt (hpl Möckelö Strand) till den nya hållplatsen och tillbaka
    till dagens körväg: tillägg = 2 × restid + 0,5 min uppehåll. Hållplatsläget är det indikativa läget i A3
    (befolkningsviktad tyngdpunkt för den otäckta delen av rutan). Tilläggs-km = 2 × restid × 25 km/h.
  * N2: hållplatsen ligger på återvändsgatan mot Kalmarnäs vändplan som bussen kör i båda riktningarna;
    0,5 min per tur (ett uppehåll per tur i genomsnitt).
  * Bo-Bil: körvägen Maxinge – Bo-Bil – Bolstavägen är 27 % kortare fågelvägen än Maxinge – Vikingagränd –
    Bolstavägen. Med dagens schemalagda tid för delsträckan (1,5 min) ger det −0,4 min. Bo-Bil blir däremot
    ett verkligt uppehåll (+0,5 min), medan bussen i praktiken sällan stannar vid Vikingagränd (≈ 0,05
    påstigande per vardag). Netto +0,1 min per tur. Minskad väntan vid Nya Godbyvägen kan inte kvantifieras
    utan realtidsdata och ingår inte (försiktig bedömning).
Verifiering (ramen 'inga fler bussar'): se b4_omlopp.py – omloppen följer normen att föraren byter linje
S ↔ N och Ö ↔ V i centrum. Varje förslag prövas med alla turer; om det inte ryms prövas vilka turer som ryms,
och om det ryms men ger fler varv utan reglering än i dag prövas en robust variant.
Effekter
  * Täckning: delpunkter 50 m (A2) – avgångar inom 400 m före/efter, klassförändring.
  * Resenärer: korrigerad OD-matris (A1) utlagd på restidsnätet (b4_natverk.py) – berörda resor och
    resenärsminuter; omräknat till vardag med kvoten påstigande/vardag ÷ OD-resor/h.
  * Tillkommande påstigande: påstigande per invånare inom 400 m vid linjens bostadshållplatser (sommardata).
Utdata: data/processed/b4_forslag.json, b4_omlopp_scenarier.csv, b4_tackning_forslag.csv.gz, b4_forslag.gpkg
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402
import b4_omlopp as O  # noqa: E402
import b4_natverk as N  # noqa: E402
from a2_tackning import avgangar_inom, hallplatser_med_avgangar, klass  # noqa: E402

P = C.PROCESSED
HPL = {'Möckelö Strand': '9025302000066401', 'Norrgårdsvägen ut': '9025302000067702',
       'Österkullagatan': '9025302000061501', 'Kalmarnäs vändplan': '9025302000063001',
       'Maxinge': '9025302000031201', 'Vikingagränd': '9025302000063201', 'Bolstavägen': '9025302000063301',
       'Bo-Bil A': '9025302000003501', 'Bo-Bil B': '9025302000003502'}
KMH_NY_STRACKA = 25.0
UPPEHALL = 0.5


def _a3():
    behov = pd.read_csv(P / 'a3_behov_ny_linjestrackning.csv')
    nya = pd.read_csv(P / 'a3_nya_hallplatser.csv')
    m = behov[behov.narmaste_hpl == 'Möckelö Strand'].iloc[0]
    n2 = nya[nya.nr == 2].iloc[0]
    return (float(m.x), float(m.y)), (float(n2.x), float(n2.y))


def forslag():
    mockelo, n2 = _a3()
    ut = []
    for fid, restid, gata in [('1a', 3.0, 'dagens gatunät'), ('1b', 1.0, 'Norrgårdsvägen förlängd till Hamnskärsvägen')]:
        ut.append({'id': fid, 'namn': f'Linje V till Möckelö Strand ({gata})', 'kort': f'{fid} Möckelö Strand',
                   'linje': 'V', 'typ': 'ny', 'xy': mockelo, 'hpl_namn': 'Möckelö Strand ny',
                   'segment': (HPL['Möckelö Strand'], None), 'restid_enkel': restid,
                   'delta': 2 * restid + UPPEHALL, 'km_tur': 2 * restid * KMH_NY_STRACKA / 60,
                   'genomgaende': [('V', 'Ö')]})
    ut.append({'id': '2', 'namn': 'Ny hållplats N2 på linje Ö', 'kort': '2 N2 linje Ö', 'linje': 'Ö', 'typ': 'ny',
               'xy': n2, 'hpl_namn': 'N2', 'segment': (HPL['Österkullagatan'], HPL['Kalmarnäs vändplan']),
               'delta': UPPEHALL, 'km_tur': 0.0, 'genomgaende': [('Ö', 'V')]})
    ut.append({'id': '3', 'namn': 'Linje N via Bo-Bil i stället för Vikingagränd', 'kort': '3 N via Bo-Bil',
               'linje': 'N', 'typ': 'byt', 'bort': HPL['Vikingagränd'], 'till': [HPL['Bo-Bil A'], HPL['Bo-Bil B']],
               'delta': None, 'km_tur': None, 'genomgaende': []})
    return ut


def stopp_xy():
    g = D.gtfs()['stops'].set_index('stop_id')
    x, y = D.till_metrisk(g.lon.values, g.lat.values)
    return pd.DataFrame({'x': x, 'y': y, 'namn': g.stop_name.values}, index=g.index)


def bobil_delta(xy):
    """Körtidsförändring för N via Bo-Bil, skalad från dagens schemalagda tid Maxinge -> Bolstavägen."""
    t = O.turer(); n = t[t.linje == 'N'].iloc[0]
    g = D.gtfs()['stop_times']; st = g[g.trip_id == n.trip_id].set_index('stop_id')
    tid_idag = st.loc[HPL['Bolstavägen'], 't_arr'] - st.loc[HPL['Maxinge'], 't_dep']
    d = lambda a, b: float(np.hypot(*(xy.loc[a, ['x', 'y']].to_numpy() - xy.loc[b, ['x', 'y']].to_numpy())))
    bobil = xy.loc[[HPL['Bo-Bil A'], HPL['Bo-Bil B']], ['x', 'y']].mean()
    db = lambda a: float(np.hypot(*(xy.loc[a, ['x', 'y']].to_numpy() - bobil.to_numpy())))
    idag = d(HPL['Maxinge'], HPL['Vikingagränd']) + d(HPL['Vikingagränd'], HPL['Bolstavägen'])
    ny = db(HPL['Maxinge']) + db(HPL['Bolstavägen'])
    kortare = round(float(tid_idag * (ny / idag - 1)), 1)
    return {'tid_idag_min': float(tid_idag), 'faglvag_idag_m': idag, 'faglvag_ny_m': ny,
            'kortare_vag_min': kortare, 'uppehall_bobil_min': UPPEHALL,
            'delta_min': round(kortare + UPPEHALL, 1), 'delta_km': round((ny - idag) * 1.25 / 1000, 2)}


# ====================================================================== omlopp
def omlopp_scenarier(f, t, r, ref):
    """Verifierar förslaget mot omloppen (normen: byte S ↔ N och Ö ↔ V, se b4_omlopp). 'alla': alla berörda turer.
    Ryms de inte prövas turerna en i taget ('ryms'). Ryms de men ger fler varv utan reglering än i dag prövas
    vilka turer som kan ändras utan det ('robust')."""
    linjeturer = t[t.linje == f['linje']]
    if f['typ'] == 'ny' and f['segment'][1] is None:          # Möckelö: turer som passerar vändpunkten
        berorda = linjeturer[linjeturer.monster.map(lambda m: f['segment'][0] in m)].trip_id
    else:
        berorda = linjeturer.trip_id
    d = {tid: f['delta'] for tid in berorda}
    kmd = {tid: f['km_tur'] for tid in berorda}
    scen = {}
    plan, nt, ok = O.verifiera(t, d, r, km_delta=kmd, referens=ref)
    scen['alla'] = {'plan': plan, 'nt': nt, 'ok': ok, 'robust': O.ar_robust(nt, r), 'turer': list(berorda)}
    for namn, robust in (('ryms', False), ('robust', True)):
        if (namn == 'ryms' and ok) or (namn == 'robust' and (not ok or scen['alla']['robust'])):
            continue
        valda = O.turer_som_ryms(t, list(berorda), f['delta'], r, robust=robust, referens=ref)
        plan, nt, ok2 = O.verifiera(t, {k: f['delta'] for k in valda}, r, km_delta={k: f['km_tur'] for k in valda},
                                    referens=ref)
        scen[namn] = {'plan': plan, 'nt': nt, 'ok': ok2, 'robust': O.ar_robust(nt, r), 'turer': valda}
    return scen


def drift(scen):
    """Driftform: alla turer om de ryms, annars de turer som ryms."""
    return 'alla' if scen['alla']['ok'] else 'ryms'


# ====================================================================== täckning
def tackning(pkt, hpl0, f, turer_som_trafikerar, xy):
    h = hpl0.copy()
    if f['typ'] == 'ny':
        ny = pd.DataFrame({'turer': [frozenset(turer_som_trafikerar)], 'linjer': [f['linje']],
                           'avgangar': [len(turer_som_trafikerar)], 'x': [f['xy'][0]], 'y': [f['xy'][1]],
                           'namn': [f['hpl_namn']]}, index=['NY'])
        h = pd.concat([h, ny])
    else:
        tn = frozenset(turer_som_trafikerar)
        h.at[f['bort'], 'turer'] = h.at[f['bort'], 'turer'] - tn
        for s in f['till']:
            if s in h.index:
                h.at[s, 'turer'] = h.at[s, 'turer'] | tn
            else:
                h.loc[s] = {'turer': tn, 'linjer': f['linje'], 'avgangar': len(tn), 'x': xy.at[s, 'x'],
                            'y': xy.at[s, 'y'], 'namn': xy.at[s, 'namn']}
        h = h[h.turer.map(len) > 0]
    # bara delpunkter nära ändringen behöver räknas om
    cx, cy = (f['xy'] if f['typ'] == 'ny' else xy.loc[[f['bort']] + f['till'], ['x', 'y']].mean())
    nara = np.hypot(pkt.x - cx, pkt.y - cy) <= 1500
    p = pkt[nara].copy()
    p['avg_efter'], _ = avgangar_inom(p, h)
    p['klass_efter'] = p.avg_efter.map(klass)
    p['klass_fore'] = p.klass
    sum_ = lambda m: round(float(p.loc[m, 'bef'].sum()))
    ut = {'ny_tackning_inv': sum_((p.avg_alla == 0) & (p.avg_efter > 0)),
          'forlorad_tackning_inv': sum_((p.avg_alla > 0) & (p.avg_efter == 0)),
          'lyft_fran_svag_inv': sum_(p.klass_fore.isin([1, 2]) & (p.klass_efter >= 3)),
          'battre_klass_inv': sum_(p.klass_efter > p.klass_fore),
          'samre_klass_inv': sum_(p.klass_efter < p.klass_fore)}
    if f['typ'] == 'ny':
        ut['inv_inom_400m_ny_hpl'] = sum_(np.hypot(p.x - f['xy'][0], p.y - f['xy'][1]) <= C.TACKNING_M)
    return ut, p[['x', 'y', 'bef', 'avg_alla', 'avg_efter', 'klass_fore', 'klass_efter']]


def pastigande_per_inv(pkt):
    """Påstigande per vardag och invånare inom 400 m vid bostadshållplatser (utanför centrum, ej skolor m.m.)."""
    bed = pd.read_csv(P / 'a3_hallplatsbedomning.csv')
    cx, cy = bed.loc[bed.omrade == C.CENTRUM, ['x', 'y']].iloc[0]
    tr = cKDTree(bed[['x', 'y']].to_numpy()); d, i = tr.query(pkt[['x', 'y']].to_numpy())
    pop = pd.Series(pkt.bef.to_numpy()[d <= C.TACKNING_M]).groupby(bed.omrade.to_numpy()[i][d <= C.TACKNING_M]).sum()
    b = bed[np.hypot(bed.x - cx, bed.y - cy) > 800].copy()
    b = b[~b.omrade.str.lower().str.contains('skola|gymnasi|lyceum|idrott|yrkes|restaurangskolan|sportfält|hallen|sjukhus|maxinge|terminal')]
    b['pop'] = b.omrade.map(pop).fillna(0); b = b[b['pop'] > 30]
    ut = {'alla': float(b.pastigande_vardag.sum() / b['pop'].sum())}
    for ln in C.STADSLINJER:
        d_ = b[b.linjer.str.contains(ln)]
        if len(d_):
            ut[ln] = float(d_.pastigande_vardag.sum() / d_['pop'].sum())
    ut['per_hpl'] = (b.set_index('omrade').pastigande_vardag / b.set_index('omrade')['pop']).to_dict()
    return ut


# ====================================================================== resenärer (OD-utläggning)
def resenarseffekt(f, zoner, mon0, nat0, andel_turer, extra=None):
    mon1 = []
    for m in mon0:
        m = dict(m); m['akt'] = m['akt'].copy()
        if m['linje'] == f['linje']:
            s = list(m['stopp'])
            if f['typ'] == 'ny':
                a, b = f['segment']
                for k in range(len(s) - 1):
                    if s[k] == a and (b is None or s[k + 1] == b):
                        m['akt'][k] += f['delta']
                        break
            else:
                if f['bort'] in s:
                    k = s.index(f['bort'])
                    z = list(m['zoner']); z[k] = 'Bo-Bil'; m['zoner'] = tuple(z)
                    m['akt'][k - 1] += f['delta'] / 2; m['akt'][k] += f['delta'] / 2
        mon1.append(m)
    nat1 = N.Nat(mon1, zoner)
    j = N.jamfor(nat0, nat1)
    fak = N.dagsfaktor()
    ut = {}
    for per in ('FM', 'EM'):
        ut[per] = {k: round(v * andel_turer, 3) for k, v in j[per].items()}
    medel = lambda k: np.mean([j[p][k] for p in ('FM', 'EM')]) * andel_turer
    ut['vardag'] = {'berorda_resor': round(float(medel('resor_langre_h') + medel('resor_kortare_h')) * fak, 1),
                    'resenarsminuter': round(float(medel('resenarsminuter_h')) * fak, 1),
                    'resor_utan_forbindelse': round(float(medel('resor_utan_forbindelse_h')) * fak, 2)}
    return ut


# ====================================================================== huvudflöde
def main():
    t = O.turer()
    plan0 = O.bygg_omlopp(t); nt0 = O.nyckeltal(plan0); r = O.ram(t)
    ref = O.kopplingar(plan0)
    xy = stopp_xy()
    pkt = pd.read_csv(P / 'a2_delpunkter.csv.gz')
    hpl0 = hallplatser_med_avgangar()
    rate = pastigande_per_inv(pkt)
    zoner = list(pd.read_csv(P / 'a1_restider_min.csv', index_col=0).index)
    mon0 = N.monster(); nat0 = N.Nat(mon0, zoner)
    bb = bobil_delta(xy)
    import s01_vagdragning as V
    fg = V.forslagsgeometri()

    kontroll = {f'{a_}→{b_}': {'kalla': v_['kalla'], 'langd_m': round(v_['langd_m']),
                                'tid_min': None if np.isnan(v_['tid_s']) else round(v_['tid_s'] / 60, 1)}
                for (a_, b_), v_ in fg.items()}
    res = {'idag': nt0, 'osrm_kontroll_nya_delstrackor': kontroll,
           'antaganden': {'uppehall_min': UPPEHALL, 'kmh_ny_stracka': KMH_NY_STRACKA,
                                        'bobil': bb, 'pastigande_per_inv': {k: v for k, v in rate.items() if k != 'per_hpl'},
                                        'dagsfaktor': round(N.dagsfaktor(), 2)},
           'forslag': {}}
    planer, tack, geo = [plan0.assign(scenario='idag', delta=0.0)], [], []
    for f in forslag():
        if f['typ'] == 'byt':
            f['delta'], f['km_tur'] = bb['delta_min'], bb['delta_km']
        scen = omlopp_scenarier(f, t, r, ref)
        val = drift(scen)
        trafikerar = scen[val]['turer']
        alla_linjeturer = int((t.linje == f['linje']).sum())
        tk, p = tackning(pkt, hpl0, f, trafikerar, xy)
        tack.append(p.assign(forslag=f['id']))
        andel = len(trafikerar) / max(len(scen['alla']['turer']), 1)
        re = resenarseffekt(f, zoner, mon0, nat0, andel)
        r_ln = rate.get(f['linje'], rate['alla'])
        nara = None
        if f['typ'] == 'ny':
            nara = 'Möckelö Strand' if f['linje'] == 'V' else 'Kalmarnäs vändplan'
        r_hi = rate['per_hpl'].get(nara, r_ln) if nara else r_ln
        ut = {'namn': f['namn'], 'linje': f['linje'], 'delta_min_per_tur': f['delta'], 'km_per_tur': round(f['km_tur'], 2),
              'linjens_turer': alla_linjeturer, 'turer_som_trafikerar': len(trafikerar), 'driftform': val,
              'omlopp': {k: {**s['nt'], 'ryms': bool(s['ok']), 'robust': bool(s['robust']),
                             'turer_med_andring': len(s['turer'])} for k, s in scen.items()},
              'tackning': tk, 'resenarer': re}
        if f['typ'] == 'ny':
            ut['nytt_pastigande_vardag'] = [round(tk['ny_tackning_inv'] * r_ln * andel, 2),
                                            round(tk['ny_tackning_inv'] * max(r_hi, r_ln) * andel, 2)]
            ut['xy'] = list(map(float, f['xy']))
        res['forslag'][f['id']] = ut
        for k, s in scen.items():
            pl = s['plan'].copy(); pl['scenario'] = f"{f['id']}_{k}"
            planer.append(pl)
        # geometri för GIS/kartor
        if f['typ'] == 'ny':
            geo.append({'forslag': f['id'], 'objekt': 'ny hållplats', 'namn': f['hpl_namn'], 'linje': f['linje'],
                        'avgangar': len(trafikerar), 'geometry': Point(*f['xy'])})
            if f['segment'][1] is None:
                a = xy.loc[f['segment'][0], ['x', 'y']].to_numpy(float)
                ut_ = fg[(f['segment'][0], 'NY_MOCKELO')]
                if f['id'] == '1a' and ut_['kalla'] == 'osrm':          # dagens gator: vägdragning från OSRM
                    g_, vagd = LineString(ut_['xy']), 'OSRM'
                else:
                    g_, vagd = LineString([a, f['xy']]), 'schematisk' + (' (planerad väg)' if f['id'] == '1b' else '')
                geo.append({'forslag': f['id'], 'objekt': 'ny körväg', 'vagdragning': vagd, 'namn': f['namn'],
                            'linje': f['linje'], 'avgangar': len(trafikerar), 'geometry': g_})
        else:
            v = xy.loc[f['bort'], ['x', 'y']].to_numpy(float)
            bo = xy.loc[f['till'], ['x', 'y']].mean().to_numpy(float)
            mx = xy.loc[HPL['Maxinge'], ['x', 'y']].to_numpy(float); bv = xy.loc[HPL['Bolstavägen'], ['x', 'y']].to_numpy(float)
            sg = V.segmentgeometri()
            gammal = [sg.get((HPL['Maxinge'], f['bort'])), sg.get((f['bort'], HPL['Bolstavägen']))]
            g_gammal = LineString(np.vstack([gammal[0], gammal[1][1:]])) if all(x is not None for x in gammal) \
                else LineString([mx, v, bv])
            ny_ = [fg[(HPL['Maxinge'], HPL['Bo-Bil B'])], fg[(HPL['Bo-Bil B'], HPL['Bolstavägen'])]]
            g_ny = LineString(np.vstack([ny_[0]['xy'], ny_[1]['xy'][1:]]))
            vag_ny = 'OSRM' if all(n['kalla'] == 'osrm' for n in ny_) else 'schematisk'
            vag_gl = 'OSRM' if V.kalla_text().startswith('Linjernas') else 'schematisk'
            geo += [{'forslag': '3', 'objekt': 'hållplats utgår för linje N', 'namn': 'Vikingagränd', 'linje': 'N', 'avgangar': 0, 'geometry': Point(*v)},
                    {'forslag': '3', 'objekt': 'ny hållplats för linje N', 'namn': 'Bo-Bil', 'linje': 'N', 'avgangar': len(trafikerar), 'geometry': Point(*bo)},
                    {'forslag': '3', 'objekt': 'körväg utgår', 'vagdragning': vag_gl, 'namn': 'Maxinge – Vikingagränd – Bolstavägen', 'linje': 'N', 'avgangar': 0, 'geometry': g_gammal},
                    {'forslag': '3', 'objekt': 'ny körväg', 'vagdragning': vag_ny, 'namn': 'Maxinge – Bo-Bil – Bolstavägen', 'linje': 'N', 'avgangar': len(trafikerar), 'geometry': g_ny}]
        print(f"{f['id']}: Δ {f['delta']} min/tur, driftform {val}, {len(trafikerar)}/{alla_linjeturer} turer, "
              f"täckning {tk}, resenärer/vardag {re['vardag']}")
        for k, s in scen.items():
            print(f"   {k:18s} ryms={s['ok']}  fordon={s['nt']['fordon']} turer={len(s['turer'])} min_vand={s['nt']['min_vandtid']} "
                  f"under_rek={s['nt']['vandningar_under_rek']} omloppstid={s['nt']['omloppstid_h']} körtid={s['nt']['korttid_h']}")

    pd.concat(planer).drop(columns=['monster']).to_csv(P / 'b4_omlopp_scenarier.csv', index=False)
    pd.concat(tack).round({'x': 1, 'y': 1, 'bef': 5}).to_csv(P / 'b4_tackning_forslag.csv.gz', index=False)
    gpd.GeoDataFrame(geo, crs=C.CRS_METRISK).to_file(P / 'b4_forslag.gpkg', layer='forslag', driver='GPKG')
    with open(P / 'b4_forslag.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=float)


if __name__ == '__main__':
    main()
