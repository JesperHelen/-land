# -*- coding: utf-8 -*-
"""B4.5 – Sammanslagning av linje N och S (genomgående N–S) och förlängning av N mot nordost.

Frågor (beställaren 2026-10-14/15)
  * Ryms en genomgående linje N–S när bussen redan i dag byter S ↔ N i centrum? Kravet är detsamma som för V–Ö:
    varje varv (N-tur + S-tur) ryms inom timmen med minst MARGINAL_VARV = 5 min i centrum.
  * Vilka av områdena i nordost (Örtvägen, Lillåkersvägen, Österkalmare; A3) får plats i N:s tidsutrymme, och hur
    ändras det om N går via Bo-Bil (UA 3, +0,1 min/tur) och om hållplatser på S dras in (A3, 6 kandidater)?
  * Varianter utan puls: S startar när N har kommit tillbaka (ingen gräns efter pulsen), med puls (S avgår i
    pulsen) och däremellan (S avgår högst 2 min efter pulsen). Känslighet för kravet på tid i centrum (3,5 min).
Metod: dagens omlopp ligger fast (b4_omlopp.genomgaende_ryms med linje N, partner S). N-turen får tillägget d; S
startar direkt efter N (0,5 min) om det behövs och varvet prövas tur för tur. Bussantalet och omloppstiden
ändras inte, eftersom kedjorna är dagens.
Tilläggstid per område: 2 × avstånd till närmaste körväg × 1,3 / 25 km/h + 0,5 min (b4_sammanslagning.omraden).
Utdata: data/processed/b4_ns.csv, b4_ns_turer.csv, b4_ns.json, b4_ns.gpkg (lager 'omraden'),
        output/kartor/b4_16_ns.png, output/gis/geojson/b4_ns_omraden.geojson
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402
import b4_omlopp as O  # noqa: E402
import b4_ua as F  # noqa: E402
import b4_sammanslagning as SL  # noqa: E402
import kartlib as K  # noqa: E402

P = C.PROCESSED
# policy för när S får starta: (namn, max efter pulsen i min; None = ingen gräns)
POLICY = [('puls', 0.0), ('högst 2 min efter pulsen', 2.0), ('utan puls', None)]
MARGINALER = [O.MARGINAL_VARV, 3.5]
S_INDRAG = ['Gröna Udden', 'Torggatan', 'Neptunigatan', 'Skillnadsgatan', 'Hamngatan']   # A3: kandidater på linje S


def indragning_s(t):
    """Kortare körtid per S-tur om A3:s indragningskandidater på S dras in: {trip_id: −min}. Det finns ingen
    tidtabellstid för sträckor som hoppar över hållplatserna, så besparingen antas vara UPPEHALL (0,5 min, retardation,
    uppehåll och acceleration) per indragen hållplats – en försiktig uppskattning som ska kontrolleras mot körtider."""
    g = D.gtfs(); hn = g['stops'].set_index('stop_id').stop_name
    ut = {}
    for r in t[t.linje == 'S'].itertuples():
        n = sum(1 for k in r.monster[1:-1] if hn[k] in S_INDRAG)
        if n:
            ut[r.trip_id] = -round(n * F.UPPEHALL, 2)
    return ut


def tillagg(bb):
    """Kandidater: tillägg per N-tur (min)."""
    om = pd.read_csv(P / 'b4_sammanslagning_omraden.csv')
    n = om[om.linje == 'N'].set_index('omrade')
    d = {'Bo-Bil (UA 3)': bb['delta_min'],
         'Örtvägen': float(n.behov_min_per_tur['Örtvägen']),
         'Lillåkersvägen': float(n.behov_min_per_tur['Lillåkersvägen']),
         'Österkalmare': float(n.behov_min_per_tur['Österkalmare'])}
    d['Örtvägen + Bo-Bil'] = round(d['Örtvägen'] + bb['delta_min'], 1)
    d['Lillåkersvägen + Bo-Bil'] = round(d['Lillåkersvägen'] + bb['delta_min'], 1)
    d['Österkalmare + Bo-Bil'] = round(d['Österkalmare'] + bb['delta_min'], 1)
    return d, n


def kor(t, plan0, ntur, d, marginal, max_skift, sol):
    """Antal N-turer som ryms i genomgående N–S, och hur många av dem som kräver att S-hållplatser dras in."""
    v, s_, utan = O.genomgaende_ryms(t, ntur, d, plan0, partner='S', linje='N', max_skift=max_skift,
                                     marginal=marginal, sol=sol, detalj=True)
    return v, s_, utan


def main():
    t = O.turer(); plan0 = O.bygg_omlopp(t)
    ntur = list(t[t.linje == 'N'].sort_values('avg').trip_id)
    xy = F.stopp_xy(); bb = F.bobil_delta(xy)
    dd, nomr = tillagg(bb)
    sol = indragning_s(t)
    tl = t.set_index('trip_id')
    nt0 = O.nyckeltal(plan0)

    # dagens varv N + S
    v0 = O.varv_vo(plan0, 'N', 'S').set_index('trip_id')
    idag = pd.DataFrame({'avg': [O.hm(tl.at[k, 'avg']) for k in v0.index], 'foljer': v0.foljer_linje.values,
                         'centrum_min': v0.centrum_min.round(1).values})

    tid_ = plan0.trip_id.to_numpy()
    foljer = {tid_[i]: tid_[j] for i, j in enumerate(plan0.nasta) if j >= 0}
    rader, turer = [], []
    ref = {'basfall (genomgående N–S utan förlängning)': 0.0, **dd}
    for namn, d in ref.items():
        for marginal in MARGINALER:
            for pol, ms in POLICY:
                for med_sol in (False, True):
                    v, s_, utan = kor(t, plan0, ntur, d, marginal, ms, sol if med_sol else None)
                    rader.append({'tillagg': namn, 'min_per_tur': d, 'marginal_min': marginal, 'policy': pol,
                                  'indragning_S': med_sol, 'n_turer': len(v), 'av': len(ntur),
                                  'varav_med_indragning': len(utan),
                                  'max_skift_S_min': max(s_.values()) if s_ else 0.0})
                    if marginal == O.MARGINAL_VARV:
                        for k in ntur:
                            turer.append({'tillagg': namn, 'policy': pol, 'indragning_S': med_sol, 'tur_N': O.hm(tl.at[k, 'avg']),
                                          'ryms': k in v, 'skift_S_min': s_.get(foljer.get(k), 0.0) if k in v else np.nan})
    df = pd.DataFrame(rader)
    df.to_csv(P / 'b4_ns.csv', index=False)
    pd.DataFrame(turer).to_csv(P / 'b4_ns_turer.csv', index=False)

    # utrymme utan puls (teoretiskt, vanligt varv): N–S 60 − marginal − t_N − t_S
    prof = SL.linjeprofil()
    utr = {m: {'N/S': round(60 - m - prof['N']['kortid_median'] - prof['S']['kortid_median'], 1),
               'S/N': round(60 - m - prof['S']['kortid_median'] - prof['N']['kortid_median'], 1),
               'S/Ö': round(60 - m - prof['S']['kortid_median'] - prof['Ö']['kortid_median'], 1)} for m in MARGINALER}

    # områdena: bedömning mot basfallets bästa policy
    om = []
    for namn in ('Örtvägen', 'Lillåkersvägen', 'Österkalmare'):
        r = nomr.loc[namn]
        for medb in (False, True):
            k = namn + (' + Bo-Bil' if medb else '')
            s = df[(df.tillagg == k) & (df.marginal_min == O.MARGINAL_VARV)]
            om.append({'omrade': namn, 'inv': float(r.inv), 'x': float(r.x), 'y': float(r.y), 'med_bobil': medb,
                       'behov_min_per_tur': dd[k],
                       **{f"{p}{' +indr.' if m else ''}": int(s[(s.policy == p) & (s.indragning_S == m)].n_turer.iloc[0])
                          for p, _ in POLICY for m in (False, True)}})
    om = pd.DataFrame(om)

    res = {'parametrar': {'marginal_krav_min': O.MARGINAL_VARV, 'marginal_kanslighet_min': MARGINALER[1],
                          'genomgang_min': O.GENOMGANG_MIN, 'n_turer_N': len(ntur), 'bobil_delta_min': bb['delta_min'],
                          'tillagg_min_per_tur': dd, 'indragna_hpl_S': S_INDRAG,
                          'indragning_S_min_per_tur': {O.hm(tl.at[k, 'avg']): v for k, v in
                                                       sorted(sol.items(), key=lambda kv: tl.at[kv[0], 'avg'])}},
           'dagens_varv_NS': idag.to_dict('records'), 'dagens_fordon': nt0['fordon'],
           'utrymme_utan_puls_vanligt_varv_min': utr,
           'scenarier': df.to_dict('records'), 'omraden': om.drop(columns=['x', 'y']).to_dict('records')}
    json.dump(res, open(P / 'b4_ns.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)

    gdf = gpd.GeoDataFrame(om.drop(columns=['x', 'y']), geometry=[Point(x, y) for x, y in zip(om.x, om.y)],
                           crs=C.CRS_METRISK)
    gdf.to_file(P / 'b4_ns.gpkg', layer='omraden', driver='GPKG')
    (C.ROT / 'output' / 'gis' / 'geojson').mkdir(parents=True, exist_ok=True)
    gdf.to_crs(4326).to_file(C.ROT / 'output' / 'gis' / 'geojson' / 'b4_ns_omraden.geojson', driver='GeoJSON')

    print(idag.to_string()); print(utr)
    pd.set_option('display.width', 250)
    print(df[df.marginal_min == O.MARGINAL_VARV].to_string())
    print(om.drop(columns=['x', 'y']).to_string())
    print(figur(df, dd, ntur))


def figur(df, dd, ntur):
    d = df[(df.marginal_min == O.MARGINAL_VARV)]
    namn = list(dd) if False else ['basfall (genomgående N–S utan förlängning)'] + list(dd)
    fig, ax = plt.subplots(figsize=(11.5, 5.8))
    y = np.arange(len(namn)); h = 0.13
    farg = {('puls', False): '#9db8dc', ('puls', True): '#5f8cc7',
            ('högst 2 min efter pulsen', False): '#8fd1d2', ('högst 2 min efter pulsen', True): '#159a9c',
            ('utan puls', False): '#f0b27a', ('utan puls', True): '#d8731f'}
    for i, ((pol, m), c) in enumerate(farg.items()):
        v = [int(d[(d.tillagg == n) & (d.policy == pol) & (d.indragning_S == m)].n_turer.iloc[0]) for n in namn]
        ax.barh(y + (i - 2.5) * h, v, height=h * 0.92, color=c, label=f"S {pol}{', S-hpl indragna' if m else ''}")
        for yy, x in zip(y + (i - 2.5) * h, v):
            ax.text(x + 0.15, yy, str(x), va='center', fontsize=6.5, color=K.TEXT)
    ax.set_yticks(y)
    ax.set_yticklabels([n.replace(' (genomgående N–S utan förlängning)', '') + (f' (+{dd[n]:g} min)'.replace('.', ',') if n in dd else '')
                        for n in namn], fontsize=8)
    ax.invert_yaxis(); ax.set_xlim(0, len(ntur) + 2)
    ax.axvline(len(ntur), color='#52514e', lw=0.8, ls=':')
    ax.set_xlabel(f'antal av linje N:s {len(ntur)} turer där varvet N + S ryms inom timmen med minst 5 min i centrum', fontsize=8)
    ax.grid(axis='x', color='#e6e4de', lw=0.6); ax.set_axisbelow(True)
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    ax.legend(fontsize=7, frameon=False, loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=3)
    ax.set_title('Genomgående N–S: turer som ryms per förlängning av linje N', loc='left', fontsize=11, fontweight='bold')
    ut = C.KARTOR / 'b4_16_ns.png'
    fig.savefig(ut, dpi=200, bbox_inches='tight'); plt.close(fig)
    return ut


if __name__ == '__main__':
    main()
