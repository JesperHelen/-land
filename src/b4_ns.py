# -*- coding: utf-8 -*-
"""B4.5 – Genomgående linje N–S (och S–Ö utan puls) mot omläggningarna i nordost och Bo-Bil.

Fråga (beställaren 2026-10-14/15): kan linje N förlängas till de områden som i b4_sammanslagning bedömdes kräva
större omläggning (Lillåkersvägen 6,5 min, Österkalmare 10,3 min; Örtvägen 4,4 min ryms först utan puls) om N och S
slås ihop till en genomgående linje, med Bo-Bil (UA 3) och ev. indragna hållplatser på S, utan fler bussar?

Metod (samma krav som V–Ö, b4_omlopp.genomgaende_ryms)
  * Dagens omlopp ligger fast. Varje N-tur prövas för sig: N-turen får tillägget d, bussen fortsätter direkt som S
    (0,5 min) och S startar när N har kommit tillbaka. Kravet: varvet N + S ryms inom timmen med minst 5 min i
    centrum (MARGINAL_VARV). 'Med puls' = S får inte avgå efter pulsen; 'utan puls' = S får avgå senare.
  * Tillägg d per område = behövd tid per tur ur b4_sammanslagning_omraden.csv (+ 0,1 min om Bo-Bil ingår, UA 3).
  * Indragna hållplatser på S (A3-kandidater: Hamngatan, Neptunigatan, Skillnadsgatan, Torggatan, Gröna Udden) har
    ingen direkt tidtabellstid att räkna av (grannhållplatserna följer aldrig direkt på varandra), så effekten prövas
    som känslighet: S-turen blir S_KORTARE min kortare. Påstigandet är 0,01–0,05 per vardag, dvs. i praktiken inget
    uppehåll – ett par tiondels minuter per hållplats är en övre gräns.
  * Utan puls i parbyte: S ↔ Ö (och N ↔ V) i stället för normen S ↔ N, Ö ↔ V – prövas med omlopp byggt för det paret
    (max 5 bussar). Ö förlängs till Strömsnäs/Solberget; V:s UA (1a, 1b, 4) prövas mot partnern N.
Utdata: data/processed/b4_ns.json, b4_ns_scenarier.csv, b4_ns_kapacitet.csv, b4_ns_omraden.gpkg,
        output/kartor/b4_16_ns.png, output/kartor/geojson/b4_ns_*.geojson
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402
import b4_omlopp as O  # noqa: E402
import b4_ua as F  # noqa: E402
import kartlib as K  # noqa: E402

P = C.PROCESSED
GEOJSON = C.ROT / 'output' / 'kartor' / 'geojson'
BOBIL = 0.1                                   # min per N-tur (UA 3, b4_ua.bobil_delta)
S_KORTARE = [0.5, 1.0, 2.0]                   # min kortare körtid per S-tur (känslighet för indragna hållplatser på S)
PAR_SO = (('S', 'Ö'), ('Ö', 'S'), ('N', 'V'), ('V', 'N'))     # alternativt bytespar (utan puls i dagens par)
ID_N = {'Örtvägen': 'ortvagen', 'Lillåkersvägen': 'lillaker', 'Österkalmare': 'osterkalmare'}
ID_O = {'Strömsnäs': 'stromsnas', 'Solberget': 'solberget', 'Solberget södra': 'solberget_s'}
GRID = [round(x * 0.5, 1) for x in range(0, 25)]


def prova(t, plan, linje, partner, kand, d, bas=None, max_skift=None):
    valda, skift = O.genomgaende_ryms(t, kand, d, plan, partner=partner, linje=linje, bas=bas, max_skift=max_skift)
    p = O.plan_fast(plan, O.med_andring(t, {**(bas or {}), **{k: (bas or {}).get(k, 0.0) + d for k in valda}}, skift))
    c = O.varv_vo(p, linje, partner).set_index('trip_id').centrum_min
    c = c[c.index.isin(valda)]
    return {'turer': len(valda), 'turer_tot': len(kand), 'valda': valda, 'skift': skift,
            'min_centrum': round(float(c.min()), 1) if len(c) else None,
            'max_skift_min': round(max(skift.values()), 1) if skift else 0.0,
            'skiftade_turer': sum(1 for v in skift.values() if v > 0.05),
            'fordon': O.nyckeltal(p)['fordon']}


def main():
    t = O.turer()
    plan0 = O.bygg_omlopp(t); r = O.ram(t)
    omr = pd.read_csv(P / 'b4_sammanslagning_omraden.csv').set_index('omrade')
    sol = F.solberget_delta(t)
    stur = list(t[t.linje == 'S'].trip_id)
    s_kortare = lambda x: {k: -x for k in stur}
    ntur = list(t[t.linje == 'N'].trip_id)
    otur = list(t[t.linje == 'Ö'].trip_id)
    vtur = list(t[t.linje == 'V'].trip_id)

    # ---------------------------------------------------------------- N/S i dagens par
    rader, res = [], {'parametrar': {'marginal_varv_min': O.MARGINAL_VARV, 'genomgang_min': O.GENOMGANG_MIN,
                                      'bobil_min': BOBIL, 'fordon_idag': r['fordon']},
                      'scenarier': {}}
    def scen(id_, namn, linje, partner, plan, kand, d, bas=None, pulsgrans=None, grupp=''):
        for puls, ms in (('med puls', 0.0), ('utan puls', None)):
            x = prova(t, plan, linje, partner, kand, d, bas, ms)
            rad = {'id': id_, 'namn': namn, 'grupp': grupp, 'linje': linje, 'partner': partner, 'puls': puls,
                   'tillagg_min': round(d, 1), 'turer': x['turer'], 'turer_tot': x['turer_tot'],
                   'min_centrum': x['min_centrum'], 'max_skift_min': x['max_skift_min'],
                   'skiftade_turer': x['skiftade_turer'], 'fordon': x['fordon']}
            rader.append(rad); res['scenarier'][f'{id_}|{puls}'] = {**rad, 'valda': [O.hm(t.set_index('trip_id').at[k, 'avg']) for k in x['valda']]}
            print(f"{id_:22s} {puls:9s} d={d:4.1f}  {x['turer']:2d}/{x['turer_tot']:2d}  centrum≥{x['min_centrum']}  "
                  f"skift ≤ {x['max_skift_min']} ({x['skiftade_turer']} turer)  bussar {x['fordon']}")

    for namn, nr in ID_N.items():
        d = float(omr.at[namn, 'behov_min_per_tur'])
        scen(f'N_{nr}', f'N–S: {namn}', 'N', 'S', plan0, ntur, d, grupp='N/S')
        scen(f'N_{nr}_bobil', f'N–S: {namn} + Bo-Bil', 'N', 'S', plan0, ntur, d + BOBIL, grupp='N/S')
        for x in S_KORTARE:
            scen(f'N_{nr}_bobil_s{x:g}', f'N–S: {namn} + Bo-Bil + S {x:g} min kortare', 'N', 'S', plan0, ntur, d + BOBIL,
                 bas=s_kortare(x), grupp='N/S')
    scen('N_bobil', 'N–S: Bo-Bil (UA 3)', 'N', 'S', plan0, ntur, BOBIL, grupp='N/S')

    # ---------------------------------------------------------------- kapacitet: hur stort tillägg ryms per tur
    kap = []
    for d in GRID:
        for namn, bas in (('utan indragning', None), ('S 1 min kortare', s_kortare(1.0))):
            for puls, ms in (('med puls', 0.0), ('utan puls', None)):
                x = prova(t, plan0, 'N', 'S', ntur, d, bas, ms)
                kap.append({'par': 'N/S', 'forlangd_linje': 'N', 'tillagg_min': d, 'indragning': namn, 'puls': puls,
                            'turer': x['turer'], 'turer_tot': x['turer_tot']})
    # ---------------------------------------------------------------- annat bytespar: S ↔ Ö och N ↔ V
    alt = O.bygg_omlopp(t, par=PAR_SO)
    nt_alt = O.nyckeltal(alt)
    res['alternativt_par'] = {'par': 'S↔Ö, N↔V', 'fordon': nt_alt['fordon'], 'omloppstid_h': nt_alt['omloppstid_h'],
                              'min_vandtid': nt_alt['min_vandtid'], 'samma_linje': nt_alt['samma_linje']}
    print('Alternativt par', res['alternativt_par'])
    for d in GRID:
        for namn, bas in (('utan indragning', None), ('Solberget indragen', sol)):
            x = prova(t, alt, 'Ö', 'S', otur, d, bas, None)
            kap.append({'par': 'S/Ö', 'forlangd_linje': 'Ö', 'tillagg_min': d, 'indragning': namn, 'puls': 'utan puls',
                        'turer': x['turer'], 'turer_tot': x['turer_tot']})
        x = prova(t, alt, 'V', 'N', vtur, d, None, None)
        kap.append({'par': 'N/V', 'forlangd_linje': 'V', 'tillagg_min': d, 'indragning': 'utan indragning',
                    'puls': 'utan puls', 'turer': x['turer'], 'turer_tot': x['turer_tot']})
        x = prova(t, plan0, 'V', 'Ö', vtur, d, None, None)
        kap.append({'par': 'V/Ö', 'forlangd_linje': 'V', 'tillagg_min': d, 'indragning': 'utan indragning',
                    'puls': 'utan puls', 'turer': x['turer'], 'turer_tot': x['turer_tot']})
    kap = pd.DataFrame(kap)
    for namn, nr in ID_O.items():
        d = float(omr.at[namn, 'behov_min_per_tur'])
        scen(f'O_{nr}_VO', f'Ö–V (dagens par): {namn}', 'Ö', 'V', plan0, otur, d, grupp='Ö/V')
        scen(f'O_{nr}_SO', f'Ö–S (S↔Ö): {namn}', 'Ö', 'S', alt, otur, d, grupp='Ö/S')
        scen(f'O_{nr}_SO_sol', f'Ö–S (S↔Ö): {namn}, Solberget indragen', 'Ö', 'S', alt, otur, d, bas=sol, grupp='Ö/S')
    for id_, d in (('1a', 4.5), ('1b', 2.5), ('4', 4.0)):
        scen(f'V_UA{id_}_VN', f'V–N (N↔V): UA {id_}', 'V', 'N', alt, vtur, d, grupp='V/N')
        scen(f'V_UA{id_}_VO', f'V–Ö (dagens par): UA {id_}', 'V', 'Ö', plan0, vtur, d, grupp='V/Ö')

    # ---------------------------------------------------------------- täckning för områdena (400 m)
    pkt = pd.read_csv(P / 'a2_delpunkter.csv.gz')
    hpl0 = F.hallplatser_med_avgangar(); xy = F.stopp_xy()
    tack = {}
    for namn in [*ID_N, *ID_O]:
        o = omr.loc[namn]
        tk, _ = F.tackning(pkt, hpl0, {'typ': 'ny', 'linje': o.linje, 'xy': (float(o.x), float(o.y)), 'hpl_namn': namn},
                           ntur if o.linje == 'N' else otur, xy)
        tack[namn] = {**tk, 'linje': o.linje, 'avstand_m': float(o.avstand_m), 'behov_min_per_tur': float(o.behov_min_per_tur)}
    res['tackning_alla_turer'] = tack

    df = pd.DataFrame(rader)
    df.to_csv(P / 'b4_ns_scenarier.csv', index=False)
    kap.to_csv(P / 'b4_ns_kapacitet.csv', index=False)
    with open(P / 'b4_ns.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=float)
    geo = geodata(df, omr, tack)
    print(df.to_string()); print(tack)
    print(figur(df, kap, omr, res))
    return geo


def geodata(df, omr, tack):
    """Områdena med utfallet per scenario som GeoPackage + GeoJSON (QGIS)."""
    rader = []
    for namn, o in omr.iterrows():
        rad = {'omrade': namn, 'inv': float(o.inv), 'linje': o.linje, 'avstand_m': float(o.avstand_m),
               'behov_min_per_tur': float(o.behov_min_per_tur), 'bedomning_b4_3': o.bedomning,
               'geometry': Point(o.x, o.y)}
        for k, v in tack.get(namn, {}).items():
            if k in ('ny_tackning_inv', 'inv_inom_400m_ny_hpl'):
                rad[k] = v
        sc = df[(df.namn.str.contains(namn, regex=False))]
        for s_ in sc.itertuples():
            rad[f"{s_.id}_{'p' if s_.puls == 'med puls' else 'u'}"] = f'{s_.turer}/{s_.turer_tot}'
        rader.append(rad)
    g = gpd.GeoDataFrame(rader, crs=C.CRS_METRISK)
    g.to_file(P / 'b4_ns_omraden.gpkg', layer='omraden', driver='GPKG')
    GEOJSON.mkdir(parents=True, exist_ok=True)
    g.to_crs(C.CRS_WGS84).to_file(GEOJSON / 'b4_ns_omraden.geojson', driver='GeoJSON')
    return g


def figur(df, kap, omr, res):
    fig = plt.figure(figsize=(13.6, 8.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.0], wspace=0.18, left=0.02, right=0.98, top=0.9, bottom=0.12)
    ax = fig.add_subplot(gs[0, 0])
    K.ny_karta((104900, 112500, 6679800, 6688100), ax=ax, titel='Områden utan hållplats inom 400 m – N–S genomgående')
    K.rita_linjer(ax, lw=1.7, zorder=4)
    farg = {'ryms': '#2f9e44', 'delvis': '#e0a800', 'ryms ej': '#c0392b', 'ej prövat här': '#9a978f'}
    for namn, o in omr.iterrows():
        s_ = None
        if o.linje == 'N':
            id_ = ID_N.get(namn)
            if id_:
                s_ = df[(df.id == f'N_{id_}_bobil_s1') & (df.puls == 'utan puls')].iloc[0]
        elif o.linje == 'Ö':
            id_ = ID_O.get(namn)
            if id_:
                s_ = df[(df.id == f'O_{id_}_SO_sol') & (df.puls == 'utan puls')].iloc[0]
        kl = 'ej prövat här' if s_ is None else 'ryms ej' if s_.turer == 0 else ('ryms' if s_.turer == s_.turer_tot else 'delvis')
        ax.scatter([o.x], [o.y], s=40 + o.inv * 0.9, marker='D', color=farg[kl], edgecolor='white', lw=0.8, zorder=8)
        txt = f"{namn}\n+{str(o.behov_min_per_tur).replace('.', ',')} min" + (f" · {s_.turer}/{s_.turer_tot} turer" if s_ is not None else '')
        ax.annotate(txt, (o.x, o.y), xytext=(6, 5), textcoords='offset points', fontsize=6.4, color=K.TEXT, zorder=9)
    h = [Line2D([], [], marker='D', ls='', color=c, markersize=7, label=k) for k, c in farg.items()]
    h += [Line2D([], [], color=C.FARG_LINJE[l], lw=2, label=f'Linje {l}') for l in C.STADSLINJER]
    ax.legend(handles=h, loc='upper left', bbox_to_anchor=(0.0, -0.01), ncol=4, fontsize=6.8, frameon=False)
    K.ram(ax)

    ax2 = fig.add_subplot(gs[0, 1])
    stil = {('utan indragning', 'med puls'): ('#b9b4a8', 'N–S, S i pulsen'), ('utan indragning', 'utan puls'): ('#1c5cab', 'N–S, S startar när N kommit tillbaka'),
            ('S 1 min kortare', 'utan puls'): ('#159a9c', '… och S 1 min kortare (indragna hållplatser)')}
    for (ind, puls), (c, lbl) in stil.items():
        k = kap[(kap.par == 'N/S') & (kap.indragning == ind) & (kap.puls == puls)]
        ax2.plot(k.tillagg_min, k.turer, color=c, lw=2, label=lbl, drawstyle='steps-post')
    k = kap[(kap.par == 'S/Ö') & (kap.indragning == 'utan indragning')]
    ax2.plot(k.tillagg_min, k.turer / k.turer_tot * 22, color='#e15759', lw=1.6, ls='--', label='Ö–S (S↔Ö), skalat till 22 turer',
             drawstyle='steps-post')
    for namn, c in (('Örtvägen', '#7a776f'), ('Lillåkersvägen', '#7a776f'), ('Österkalmare', '#7a776f')):
        d = float(omr.at[namn, 'behov_min_per_tur'])
        ax2.axvline(d, color=c, lw=0.8, ls=':'); ax2.text(d + 0.1, 0.4, namn, rotation=90, fontsize=7, color=c, va='bottom')
    ax2.set_xlabel('tillägg per N-tur (min)', fontsize=8); ax2.set_ylabel('antal N-turer som ryms (av 22)', fontsize=8)
    ax2.set_xlim(0, 12); ax2.set_ylim(0, 23); ax2.grid(color='#e6e4de', lw=0.6); ax2.set_axisbelow(True)
    ax2.legend(loc='upper right', fontsize=7.2, frameon=False)
    for s in ['top', 'right']:
        ax2.spines[s].set_visible(False)
    ax2.set_title('Hur stort tillägg ryms? (varvet inom timmen, ≥ 5 min i centrum)', loc='left', fontsize=10, fontweight='bold')
    fig.suptitle('B4.5 – Genomgående linje N–S och alternativa byten (S↔Ö) utan fler bussar', x=0.01, ha='left',
                 fontsize=12.5, fontweight='bold')
    ut = C.KARTOR / 'b4_16_ns.png'
    fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


if __name__ == '__main__':
    main()
