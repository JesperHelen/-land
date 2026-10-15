# -*- coding: utf-8 -*-
"""B4 – Enskilda utredningsalternativ: individuella effekter och verifiering mot dagens omlopp.

UA (beställarens urval efter granskningen av Fas A, 2026-10-14)
  1a  Linje V till ny hållplats i Möckelö Strand via dagens gatunät (restid 3 min från hpl Möckelö Strand).
  1b  Som 1a men med Norrgårdsvägen förlängd till Hamnskärsvägen (restid 1 min till hållplatsen).
  2   Ny hållplats N2 på linje Ö (mellan Österkullagatan och Kalmarnäs vändplan, läge enligt A3).
  3   Linje N trafikerar Bo-Bil i stället för Vikingagränd (Maxinge – Bo-Bil – Bolstavägen), så att bussen
      inte behöver vänta vid Nya Godbyvägen.
  4   Linje V till flygplatsen (beställaren 2026-10-14): från Posten upp till terminalen, slinga runt terminalen och
      tillbaka till Norra Svibyvägen. Varianter: alla turer, V och Ö sammanslagna, sammanslagna med hållplatsen
      Solberget indragen på linje Ö, och 'Y' – bara de V-turer som behövs för flygen.
Antaganden
  * Möckelö Strand (beställarens restider och skiss 2026-10-14): den befintliga vägen mellan Norrgårdsvägen och
    den nya hållplatsen tar 2 min (RESTID_BEFINTLIG_VAG), förlängningen av Norrgårdsvägen från dagens vändpunkt
    (hpl Möckelö Strand) till den nya hållplatsen 1 min (RESTID_FORLANGNING). Dagens 3 min i 1a är alltså
    Möckelö Strand → Norrgårdsvägen (1 min, körs redan i dag) + den befintliga vägen (2 min).
    1a: bussen kör som i dag till Möckelö Strand och tillbaka till Norrgårdsvägen, och därefter den befintliga
        vägen till den nya hållplatsen och tillbaka: tillägg = 2 × 2 + 0,5 min uppehåll = 4,5 min per tur.
        Bussen måste kunna vända vid den nya hållplatsen.
    1b: slinga Möckelö Strand → förlängningen (1 min) → ny hållplats (0,5 min) → befintliga vägen (2 min) →
        Norrgårdsvägen. Den ersätter dagens Möckelö Strand → Norrgårdsvägen (tidtabellen: 1 min):
        tillägg = 1 + 0,5 + 2 − 1 = 2,5 min per tur. Känslighet: + 3,5 min om tidtabellens minut inte kan räknas av.
    Tilläggs-km från längden på respektive väg (befintliga vägen: OSRM om hämtad, annars beställarens skiss;
    förlängningen: rak linje). Hållplatsläget är det indikativa läget i A3.
  * N2: hållplatsen ligger på återvändsgatan mot Kalmarnäs vändplan som bussen kör i båda riktningarna;
    0,5 min per tur (ett uppehåll per tur i genomsnitt).
  * Bo-Bil: körvägen Maxinge – Bo-Bil – Bolstavägen är 27 % kortare fågelvägen än Maxinge – Vikingagränd –
    Bolstavägen. Med dagens schemalagda tid för delsträckan (1,5 min) ger det −0,4 min. Bo-Bil blir däremot
    ett verkligt uppehåll (+0,5 min), medan bussen i praktiken sällan stannar vid Vikingagränd (≈ 0,05
    påstigande per vardag). Netto +0,1 min per tur. Minskad väntan vid Nya Godbyvägen kan inte kvantifieras
    utan realtidsdata och ingår inte (försiktig bedömning).
  * Flygplatsen: körvägen enligt beställarens skiss (s01_vagdragning). Tilläggs-km = skissens längd Posten →
    terminalen → Norra Svibyvägen → Källarvägen minus dagens Posten → Källarvägen; tilläggstid = tilläggs-km i
    KMH_FLYG km/h + 0,5 min uppehåll, avrundat uppåt till halv minut (känslighet ± 1 min).
    Flygen (Finavia, avgångar 2026-10-14): 07:15 Arlanda, 11:00 Åbo, 17:10 Arlanda. Ankomsttiderna saknas i
    underlaget och antas vara 35 min före avgångarna 11:00 och 17:10 (samma flygplan vänder). 'Y': V-turer som
    är vid flygplatsen 2 h – 30 min före en avgång, och den första turen 10–40 min efter en ankomst.
  * Solberget indragen (linje Ö): bussen kör direkt mellan hållplatserna före och efter Solberget, med den
    kortaste tid som tidtabellen har för den direkta sträckan (1,6–2,5 min kortare per tur).
Verifiering (ramen 'inga fler bussar'): se b4_omlopp.py – omloppen följer normen att föraren byter linje
S ↔ N och Ö ↔ V i centrum. Varje UA prövas med alla turer i dagens tidtabell; om det inte ryms prövas vilka
turer som ryms, och om det ryms men ger fler varv utan reglering än i dag prövas en robust variant.
UA på linje V prövas dessutom som genomgående linje V–Ö ('VO', V och Ö sammanslagna): dagens omlopp ligger fast,
bussen fortsätter direkt som linje Ö (0,5 min) och Ö får avgå upp till 2 min efter pulsen. Det enda kravet är
att varvet V + Ö ryms inom timmen med minst 5 min i centrum (beställaren 2026-10-15, b4_omlopp.genomgaende_ryms).
Effekter
  * Täckning: delpunkter 50 m (A2) – avgångar inom 400 m före/efter, klassförändring.
  * Resenärer: korrigerad OD-matris (A1) utlagd på restidsnätet (b4_natverk.py) – berörda resor och
    resenärsminuter; omräknat till vardag med kvoten påstigande/vardag ÷ OD-resor/h.
  * Tillkommande påstigande: påstigande per invånare inom 400 m vid linjens bostadshållplatser (sommardata).
Utdata: data/processed/b4_ua.json, b4_omlopp_scenarier.csv, b4_tackning_ua.csv.gz, b4_ua.gpkg
"""
import json
import sys
from functools import lru_cache
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
HPL = {'Möckelö Strand': '9025302000066401', 'Norrgårdsvägen ut': '9025302000067702', 'Norrgårdsvägen in': '9025302000067701',
       'Österkullagatan': '9025302000061501', 'Kalmarnäs vändplan': '9025302000063001',
       'Maxinge': '9025302000031201', 'Vikingagränd': '9025302000063201', 'Bolstavägen': '9025302000063301',
       'Bo-Bil A': '9025302000003501', 'Bo-Bil B': '9025302000003502',
       'Posten': '9025302000035802', 'Källarvägen': '9025302000025902', 'Solberget': '9025302000062201'}
UPPEHALL = 0.5
RESTID_BEFINTLIG_VAG = 2.0     # min – befintlig väg Norrgårdsvägen ↔ ny hållplats Möckelö Strand (beställaren)
RESTID_FORLANGNING = 1.0       # min – förlängd Norrgårdsvägen, Möckelö Strand → ny hållplats (beställaren)
# Utredningsalternativ (UA): titel och huvudalternativ = den mest realistiska driftformen, som visas på kartan.
# Övriga driftformer redovisas i rapporten (alternativ som kräver fler bussar är uteslutna).
TITEL = {'1a': 'UA 1a – Möckelö Strand ny via dagens vägar', '1b': 'UA 1b – Möckelö Strand ny via förlängd Norrgårdsvägen',
         '2': 'UA 2 – N2 på linje Ö', '3': 'UA 3 – Linje N via Bo-Bil', '4': 'UA 4 – Linje V–Ö via flygplatsen'}
HUVUD_TEXT = {'1a': 'V och Ö sammanslagna (varv V + Ö inom timmen, ≥ 5 min i centrum)',
              '1b': 'V och Ö sammanslagna (varv V + Ö inom timmen, ≥ 5 min i centrum)',
              '2': 'alla turer', '3': 'alla turer',
              '4': 'V och Ö sammanslagna (varv V + Ö inom timmen, ≥ 5 min i centrum)'}
KMH_FLYG = 25.0                # km/h – medelhastighet på omvägen till flygplatsen
FLYG_AVGANGAR = ['07:15', '11:00', '17:10']     # Finavia, avgångar från Mariehamn 2026-10-14
FLYG_ANKOMSTER = ['10:25', '16:35']             # antagande: 35 min före avgångarna 11:00 och 17:10 (ersätts)
FLYG_FORE = (120, 30)          # min – bussen vid flygplatsen mellan 2 h och 30 min före avgång
FLYG_EFTER = (10, 40)          # min – bussen vid flygplatsen 10–40 min efter ankomst


def _a3():
    behov = pd.read_csv(P / 'a3_behov_ny_linjestrackning.csv')
    nya = pd.read_csv(P / 'a3_nya_hallplatser.csv')
    m = behov[behov.narmaste_hpl == 'Möckelö Strand'].iloc[0]
    n2 = nya[nya.nr == 2].iloc[0]
    return (float(m.x), float(m.y)), (float(n2.x), float(n2.y))


@lru_cache(maxsize=1)
def mockelo():
    """Tider och längder för Möckelö Strand-utredningsalternativen (1a, 1b)."""
    import s01_vagdragning as V
    t = O.turer(); v = t[t.linje == 'V'].iloc[0]
    g = D.gtfs()['stop_times']; st = g[g.trip_id == v.trip_id].set_index('stop_id')
    tillbaka = float(st.loc[HPL['Norrgårdsvägen in'], 't_arr'] - st.loc[HPL['Möckelö Strand'], 't_dep'])
    fg = V.uageometri(); sg = V.segmentgeometri()
    bef = fg[('NY_MOCKELO', HPL['Norrgårdsvägen in'])]
    return {'restid_befintlig_vag_min': RESTID_BEFINTLIG_VAG, 'restid_forlangning_min': RESTID_FORLANGNING,
            'tidtabell_mockelo_norrgardsvagen_min': round(tillbaka, 2),
            'langd_befintlig_vag_m': round(bef['langd_m']), 'kalla_befintlig_vag': bef['kalla'],
            'osrm_tid_befintlig_vag_min': None if np.isnan(bef['tid_s']) else round(bef['tid_s'] / 60, 1),
            'langd_forlangning_m': round(V.langd(V.planerad_vag())),
            'langd_mockelo_norrgardsvagen_m': round(V.langd(sg[(HPL['Möckelö Strand'], HPL['Norrgårdsvägen in'])]))}


def hhmm(x):
    h, m = x.split(':'); return int(h) * 60 + int(m)


@lru_cache(maxsize=1)
def flygplatsen():
    """Tider och längder för UA 4 och när V-turerna är vid flygplatsen."""
    import s01_vagdragning as V
    fg = V.uageometri(); sg = V.segmentgeometri()
    ut_ = fg[(HPL['Posten'], 'FLYGPLATSEN')]; ti_ = fg[('FLYGPLATSEN', HPL['Källarvägen'])]
    idag = V.langd(sg[(HPL['Posten'], HPL['Källarvägen'])])
    extra = ut_['langd_m'] + ti_['langd_m'] - idag
    delta = np.ceil((extra / 1000 / KMH_FLYG * 60 + UPPEHALL) * 2) / 2
    t = O.turer(); v = t[t.linje == 'V'].iloc[0]
    g = D.gtfs()['stop_times']; st = g[g.trip_id == v.trip_id].set_index('stop_id')
    till_posten = float(st.loc[HPL['Posten'], 't_arr'] - v.avg)
    framme = till_posten + ut_['langd_m'] / 1000 / KMH_FLYG * 60       # min efter avgång från centrum
    return {'langd_posten_flygplatsen_m': round(ut_['langd_m']), 'langd_flygplatsen_kallarvagen_m': round(ti_['langd_m']),
            'langd_posten_kallarvagen_idag_m': round(idag), 'extra_km_per_tur': round(extra / 1000, 2),
            'delta_min_per_tur': float(delta), 'kalla': ut_['kalla'],
            'framme_vid_flygplatsen_min_efter_avgang': round(framme, 1), 'kmh': KMH_FLYG,
            'flyg_avgangar': FLYG_AVGANGAR, 'flyg_ankomster_antagna': FLYG_ANKOMSTER}


def flygturer(t):
    """V-turer som behövs för flygen ('Y'): {trip_id: syfte}."""
    fp = flygplatsen(); vt = t[t.linje == 'V'].sort_values('avg')
    vid = {r.trip_id: r.avg + fp['framme_vid_flygplatsen_min_efter_avgang'] for r in vt.itertuples()}
    ut = {}
    for a in FLYG_AVGANGAR:
        for k, x in vid.items():
            if hhmm(a) - FLYG_FORE[0] <= x <= hhmm(a) - FLYG_FORE[1]:
                ut.setdefault(k, []).append(f'till flyget {a}')
    for a in FLYG_ANKOMSTER:
        kand = [(x, k) for k, x in vid.items() if hhmm(a) + FLYG_EFTER[0] <= x <= hhmm(a) + FLYG_EFTER[1]]
        if kand:
            ut.setdefault(min(kand)[1], []).append(f'från flyget (ankomst {a})')
    return {k: ', '.join(v) for k, v in ut.items()}


@lru_cache(maxsize=1)
def direkttider():
    """Kortaste tidtabellstid mellan två hållplatser som följer direkt på varandra (alla turmönster)."""
    t = O.turer(); g = D.gtfs()['stop_times']; ut = {}
    for _, d in t.groupby(t.monster.map(tuple)):
        s_ = g[g.trip_id == d.trip_id.iloc[0]].sort_values('seq')
        ids, ta = list(s_.stop_id), list(s_.t_arr)
        for i in range(len(ids) - 1):
            k = (ids[i], ids[i + 1]); ut[k] = min(ut.get(k, 99.0), ta[i + 1] - ta[i])
    return ut


def solberget_delta(t):
    """Kortare körtid per Ö-tur om hållplatsen Solberget dras in: {trip_id: −min}."""
    g = D.gtfs()['stop_times']; dt = direkttider(); ut = {}
    for r in t[t.linje == 'Ö'].itertuples():
        s_ = g[g.trip_id == r.trip_id].sort_values('seq'); ids, ta = list(s_.stop_id), list(s_.t_arr)
        if HPL['Solberget'] in ids:
            k = ids.index(HPL['Solberget'])
            ut[r.trip_id] = -round((ta[k + 1] - ta[k - 1]) - dt[(ids[k - 1], ids[k + 1])], 2)
    return ut


def alternativ():
    mockelo_, n2 = _a3()
    m = mockelo()
    gem = {'linje': 'V', 'typ': 'ny', 'xy': mockelo_, 'hpl_namn': 'Möckelö Strand ny',
           'segment': (HPL['Möckelö Strand'], None), 'genomgaende': [('V', 'Ö')]}
    ut = [{**gem, 'id': '1a', 'namn': 'Linje V till Möckelö Strand ny via dagens vägar', 'kort': '1a Möckelö Strand',
           'titel': TITEL['1a'], 'huvud': 'VO',
           'korvag': 'Norrgårdsvägen → befintlig väg → ny hållplats → samma väg tillbaka (efter Möckelö Strand som i dag)',
           'delta': 2 * RESTID_BEFINTLIG_VAG + UPPEHALL,
           'km_tur': 2 * m['langd_befintlig_vag_m'] / 1000},
          {**gem, 'id': '1b', 'namn': 'Linje V till Möckelö Strand ny via förlängd Norrgårdsvägen (slinga)',
           'titel': TITEL['1b'], 'huvud': 'VO',
           'kort': '1b Möckelö Strand',
           'korvag': 'Möckelö Strand → förlängd Norrgårdsvägen → ny hållplats → befintlig väg → Norrgårdsvägen',
           'delta': RESTID_FORLANGNING + UPPEHALL + RESTID_BEFINTLIG_VAG - m['tidtabell_mockelo_norrgardsvagen_min'],
           'delta_konservativ': RESTID_FORLANGNING + UPPEHALL + RESTID_BEFINTLIG_VAG,
           'km_tur': (m['langd_forlangning_m'] + m['langd_befintlig_vag_m'] - m['langd_mockelo_norrgardsvagen_m']) / 1000}]
    ut.append({'id': '2', 'namn': 'Ny hållplats N2 på linje Ö', 'kort': '2 N2 linje Ö', 'linje': 'Ö', 'typ': 'ny',
               'titel': TITEL['2'], 'huvud': 'alla',
               'xy': n2, 'hpl_namn': 'N2', 'segment': (HPL['Österkullagatan'], HPL['Kalmarnäs vändplan']),
               'delta': UPPEHALL, 'km_tur': 0.0, 'genomgaende': [('Ö', 'V')]})
    ut.append({'id': '3', 'namn': 'Linje N via Bo-Bil i stället för Vikingagränd', 'kort': '3 N via Bo-Bil',
               'titel': TITEL['3'], 'huvud': 'alla',
               'linje': 'N', 'typ': 'byt', 'bort': HPL['Vikingagränd'], 'till': [HPL['Bo-Bil A'], HPL['Bo-Bil B']],
               'delta': None, 'km_tur': None, 'genomgaende': []})
    import s01_vagdragning as V
    fp = flygplatsen()
    ut.append({'id': '4', 'namn': 'Linje V till flygplatsen', 'kort': '4 V till flygplatsen', 'linje': 'V', 'typ': 'ny',
               'titel': TITEL['4'], 'huvud': 'VO',
               'xy': V.FLYGPLATSEN_XY, 'hpl_namn': 'Flygplatsen', 'segment': (HPL['Posten'], HPL['Källarvägen']),
               'korvag': 'Posten → flygplatsen (slinga runt terminalen) → Norra Svibyvägen → Källarvägen',
               'delta': fp['delta_min_per_tur'], 'km_tur': fp['extra_km_per_tur'], 'genomgaende': [('V', 'Ö')],
               'solberget': True, 'flygturer': True, 'kansl': [fp['delta_min_per_tur'] - 1, fp['delta_min_per_tur'] + 1]})
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
    """Verifierar UA:t mot omloppen (normen: byte S ↔ N och Ö ↔ V, se b4_omlopp).
      alla          alla berörda turer
      ryms          (om alla inte ryms) turerna prövas en i taget
      robust        (om alla ryms men ger fler varv utan reglering än i dag) turer som kan ändras utan det
      VO            (linje V) genomgående linje V–Ö: varv V + Ö inom timmen med minst 5 min i centrum
      VO_sol        (UA 4) dito med Solberget indragen; Y_VO, Y_VO_sol bara turerna för flygen
      konservativ…  (1b) känslighet med den högre körtiden delta_konservativ"""
    linjeturer = t[t.linje == f['linje']]
    if f['typ'] == 'ny' and f['segment'][1] is None:          # Möckelö: turer som passerar vändpunkten
        berorda = list(linjeturer[linjeturer.monster.map(lambda m: f['segment'][0] in m)].trip_id)
    else:
        berorda = list(linjeturer.trip_id)
    scen = {}

    plan0 = O.bygg_omlopp(t, referens=ref)                    # dagens omlopp – fast vid genomgående linje V–Ö
    v_regel = f['linje'] == 'V'                                # linje V: kravet på tid i centrum per varv V + Ö
    vv = plan0 if v_regel else None

    def kor(namn, valda, d, skift=None, bas=None, vo=False):
        dd = dict(bas or {})
        for k in valda:
            dd[k] = dd.get(k, 0.0) + d
        plan, nt, ok = O.verifiera(t, dd, r, km_delta={k: f['km_tur'] for k in valda}, skift=skift, referens=ref,
                                   fast=plan0 if vo else None)
        if v_regel and not vo:
            ok = ok and O.varv_ok(plan, plan0)
        rob = (nt['varv_vo_under_marginal'] <= O.nyckeltal(plan0)['varv_vo_under_marginal']) if v_regel else O.ar_robust(nt, r)
        scen[namn] = {'plan': plan, 'nt': nt, 'ok': ok, 'robust': rob, 'turer': list(valda), 'vo': vo,
                      'skift': dict(skift or {}), 'delta': d, 'solberget': bool(bas)}

    def vo(namn, kand, d, bas=None):
        v, s_ = O.genomgaende_ryms(t, kand, d, plan0, bas=bas)
        kor(namn, v, d, s_, bas=bas, vo=True)

    def pröva(prefix, d):
        p = prefix + '_' if prefix else ''
        kor(p + 'alla', berorda, d)
        bas = scen[p + 'alla']
        if not bas['ok']:
            kor(p + 'ryms', O.turer_som_ryms(t, berorda, d, r, varv=vv, referens=ref), d)
        elif not bas['robust'] and f['linje'] != 'V':
            kor(p + 'robust', O.turer_som_ryms(t, berorda, d, r, robust=True, referens=ref), d)
        if f['linje'] == 'V':
            vo(p + 'VO', berorda, d)

    pröva('', f['delta'])
    if f.get('delta_konservativ'):
        pröva('konservativ', f['delta_konservativ'])
    if f.get('solberget'):                                     # dito med Solberget indragen på linje Ö
        vo('VO_sol', berorda, f['delta'], solberget_delta(t))
    if f.get('flygturer'):                                     # 'Y': bara turerna för flygen
        y = list(flygturer(t))
        kor('Y_ryms', O.turer_som_ryms(t, y, f['delta'], r, varv=vv, referens=ref), f['delta'])
        vo('Y_VO', y, f['delta'])
        vo('Y_VO_sol', y, f['delta'], solberget_delta(t))
    for d in f.get('kansl', []):                               # känslighet för körtiden (V och Ö sammanslagna)
        vo(f'kansl_{d:g}_VO', berorda, d)
    return scen


def drift(f, scen):
    """Huvudalternativ (den mest realistiska driftformen, f['huvud']); annars alla turer om de ryms, annars
    genomgående V/Ö om det prövats, annars de turer som ryms."""
    if f.get('huvud') in scen and scen[f['huvud']]['ok']:
        return f['huvud']
    return 'alla' if scen['alla']['ok'] else ('VO' if 'VO' in scen else 'ryms')


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


def genomgaende_effekt(zoner, mon0, nat0):
    """Restidsvinst när V och Ö slås ihop: resor mellan V- och Ö-området sitter kvar i centrum (inget byte)."""
    j = N.jamfor(nat0, N.Nat(N.genomgaende(mon0, 'V', 'Ö', O.GENOMGANG_MIN), zoner)); fak = N.dagsfaktor()
    medel = lambda k: float(np.mean([j[p][k] for p in ('FM', 'EM')])) * fak
    return {'resor_kortare_vardag': round(medel('resor_kortare_h'), 1),
            'resenarsminuter_vardag': round(medel('resenarsminuter_h'), 1),
            'min_per_resa': round(medel('resenarsminuter_h') / max(medel('resor_kortare_h'), 1e-9), 1)}


# ====================================================================== geometri
def geometri(f, trafikerar, xy, fg, sg):
    """UA:ts objekt för kartor och GIS. Linjer som MultiLineString med en del per hållplatssegment (kan bytas
    mot OSRM-rutter i QGIS, rutta_med_osrm.py); planerad_del = 'från>till' för en väg som inte finns i dag."""
    import shapely
    import s01_vagdragning as V
    ml = lambda *d: shapely.MultiLineString([LineString(x) for x in d])
    n = len(trafikerar)
    if f['typ'] == 'ny':
        ut = [{'ua': f['id'], 'objekt': 'ny hållplats', 'namn': f['hpl_namn'], 'linje': f['linje'], 'avgangar': n,
               'geometry': Point(*f['xy'])}]
        if f['id'] == '4':
            a_, b_ = fg[(HPL['Posten'], 'FLYGPLATSEN')], fg[('FLYGPLATSEN', HPL['Källarvägen'])]
            vag = {'osrm': 'OSRM', 'skiss': 'beställarens skiss'}.get(a_['kalla'], 'schematisk')
            ut += [{'ua': '4', 'objekt': 'ny körväg, befintlig väg', 'vagdragning': vag,
                    'namn': 'Posten – flygplatsen – Norra Svibyvägen', 'linje': 'V', 'avgangar': n, 'planerad_del': '',
                    'geometry': ml(a_['xy'], b_['xy'])}]
        elif f['linje'] == 'V':
            ni, ny = HPL['Norrgårdsvägen in'], 'NY_MOCKELO'
            bef = fg[(ni, ny)]
            vag = {'osrm': 'OSRM', 'skiss': 'beställarens skiss'}.get(bef['kalla'], 'schematisk')
            if f['id'] == '1a':
                ut.append({'ua': '1a', 'objekt': 'ny körväg, befintlig väg', 'vagdragning': vag,
                           'namn': 'Norrgårdsvägen – Möckelö Strand ny, fram och tillbaka (2 min)', 'linje': 'V',
                           'avgangar': n, 'planerad_del': '', 'geometry': ml(bef['xy'], fg[(ny, ni)]['xy'])})
            else:
                ut.append({'ua': '1b', 'objekt': 'ny körväg, planerad väg', 'vagdragning': 'schematisk (planerad väg)',
                           'namn': 'Förlängd Norrgårdsvägen: Möckelö Strand – Möckelö Strand ny (1 min)', 'linje': 'V',
                           'avgangar': n, 'planerad_del': '>'.join(V.PLANERAD_VAG), 'geometry': ml(V.planerad_vag())})
                ut.append({'ua': '1b', 'objekt': 'ny körväg, befintlig väg', 'vagdragning': vag,
                           'namn': 'Möckelö Strand ny – Norrgårdsvägen (2 min)', 'linje': 'V', 'avgangar': n,
                           'planerad_del': '', 'geometry': ml(fg[(ny, ni)]['xy'])})
        return ut
    v = xy.loc[f['bort'], ['x', 'y']].to_numpy(float)
    bo = xy.loc[f['till'], ['x', 'y']].mean().to_numpy(float)
    mx, bv, bb = HPL['Maxinge'], HPL['Bolstavägen'], HPL['Bo-Bil B']
    xy_ = lambda a: xy.loc[a, ['x', 'y']].to_numpy(float)
    g_gammal = ml(sg.get((mx, f['bort']), np.array([xy_(mx), v])), sg.get((f['bort'], bv), np.array([v, xy_(bv)])))
    ny_ = [fg[(mx, bb)], fg[(bb, bv)]]
    vag_ny = 'OSRM' if all(x['kalla'] == 'osrm' for x in ny_) else 'schematisk'
    vag_gl = 'OSRM' if V.kalla_text().startswith('Linjernas') else 'schematisk'
    return [{'ua': '3', 'objekt': 'hållplats utgår för linje N', 'namn': 'Vikingagränd', 'linje': 'N', 'avgangar': 0,
             'geometry': Point(*v)},
            {'ua': '3', 'objekt': 'ny hållplats för linje N', 'namn': 'Bo-Bil', 'linje': 'N', 'avgangar': n,
             'geometry': Point(*bo)},
            {'ua': '3', 'objekt': 'körväg utgår', 'vagdragning': vag_gl, 'namn': 'Maxinge – Vikingagränd – Bolstavägen',
             'linje': 'N', 'avgangar': 0, 'planerad_del': '', 'geometry': g_gammal},
            {'ua': '3', 'objekt': 'ny körväg, befintlig väg', 'vagdragning': vag_ny, 'namn': 'Maxinge – Bo-Bil – Bolstavägen',
             'linje': 'N', 'avgangar': n, 'planerad_del': '', 'geometry': ml(ny_[0]['xy'], ny_[1]['xy'])}]


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
    gen_vo = genomgaende_effekt(zoner, mon0, nat0)
    bb = bobil_delta(xy)
    import s01_vagdragning as V
    fg = V.uageometri(); sg = V.segmentgeometri()

    kontroll = {f'{a_}→{b_}': {'kalla': v_['kalla'], 'langd_m': round(v_['langd_m']),
                                'tid_min': None if np.isnan(v_['tid_s']) else round(v_['tid_s'] / 60, 1)}
                for (a_, b_), v_ in fg.items()}
    sol = solberget_delta(t)
    bed = pd.read_csv(P / 'a3_hallplatsbedomning.csv')
    sol_tk, _ = tackning(pkt, hpl0, {'typ': 'byt', 'linje': 'Ö', 'bort': HPL['Solberget'], 'till': []},
                         list(t[t.linje == 'Ö'].trip_id), xy)
    tl0 = t.set_index('trip_id')
    res_sol = {'besparing_min_per_tur': {O.hm(tl0.at[k, 'avg']): -v for k, v in sorted(sol.items(), key=lambda kv: tl0.at[kv[0], 'avg'])},
               'tackning': sol_tk,
               'pastigande_vardag': float(bed.loc[bed.omrade == 'Solberget', 'pastigande_vardag'].sum())
               if 'pastigande_vardag' in bed else None}
    res_flyg = {**flygplatsen(), 'flygturer': {O.hm(tl0.at[k, 'avg']): v for k, v in
                                               sorted(flygturer(t).items(), key=lambda kv: tl0.at[kv[0], 'avg'])}}
    res = {'idag': nt0, 'genomgaende_vo': gen_vo, 'osrm_kontroll_nya_delstrackor': kontroll, 'solberget_indragen': res_sol, 'flygplatsen': res_flyg,
           'antaganden': {'uppehall_min': UPPEHALL, 'mockelo': mockelo(), 'max_skift_partner_min': O.MAX_SKIFT_PARTNER,
                          'bobil': bb, 'pastigande_per_inv': {k: v for k, v in rate.items() if k != 'per_hpl'},
                          'dagsfaktor': round(N.dagsfaktor(), 2)},
           'ua': {}}
    tl = t.set_index('trip_id')
    planer, tack, geo = [plan0.assign(scenario='idag', delta=0.0, skift=0.0)], [], []
    for f in alternativ():
        if f['typ'] == 'byt':
            f['delta'], f['km_tur'] = bb['delta_min'], bb['delta_km']
        scen = omlopp_scenarier(f, t, r, ref)
        val = drift(f, scen)
        trafikerar = scen[val]['turer']
        alla_linjeturer = int((t.linje == f['linje']).sum())
        tk, p = tackning(pkt, hpl0, f, trafikerar, xy)
        tack.append(p.assign(ua=f['id']))
        andel = len(trafikerar) / max(len(scen['alla']['turer']), 1)
        re = resenarseffekt(f, zoner, mon0, nat0, andel)
        if scen[val].get('vo'):                                # V och Ö sammanslagna: genomresande sitter kvar
            re['genomgaende_vo'] = gen_vo
            re['vardag_inkl_genomgaende'] = round(re['vardag']['resenarsminuter'] + gen_vo['resenarsminuter_vardag'], 1)
        r_ln = rate.get(f['linje'], rate['alla'])
        nara = None
        if f['typ'] == 'ny':
            nara = {'1a': 'Möckelö Strand', '1b': 'Möckelö Strand', '2': 'Kalmarnäs vändplan'}.get(f['id'])
        r_hi = rate['per_hpl'].get(nara, r_ln) if nara else r_ln
        alla_berorda = set(scen['alla']['turer'])
        ut = {'namn': f['namn'], 'titel': f['titel'], 'huvudalternativ': val, 'huvud_text': HUVUD_TEXT[f['id']],
              'linje': f['linje'], 'korvag': f.get('korvag', ''),
              'delta_min_per_tur': round(f['delta'], 2), 'km_per_tur': round(f['km_tur'], 2),
              'delta_konservativ_min_per_tur': f.get('delta_konservativ'),
              'linjens_turer': alla_linjeturer, 'turer_som_trafikerar': len(trafikerar), 'driftform': val,
              'omlopp': {k: {**s['nt'], 'ryms': bool(s['ok']), 'robust': bool(s['robust']),
                             'turer_med_andring': len(s['turer']), 'delta_min_per_tur': s['delta'],
                             'turer_utan_andring': [O.hm(tl.at[x, 'avg']) for x in sorted(alla_berorda - set(s['turer']),
                                                                                          key=lambda x: tl.at[x, 'avg'])],
                             'skiftade_turer': {O.hm(tl.at[x, 'avg']): v for x, v in sorted(s['skift'].items(),
                                                                                            key=lambda kv: tl.at[kv[0], 'avg'])},
                             'genomgaende_vo': bool(s.get('vo')),
                             'varv_centrum_min': {O.hm(tl.at[r_.trip_id, 'avg']): (None if not np.isfinite(r_.centrum_min)
                                                                                   else round(r_.centrum_min, 1))
                                                  for r_ in O.varv_vo(s['plan']).itertuples()}}
                         for k, s in scen.items()},
              'tackning': tk, 'resenarer': re}
        if f['typ'] == 'ny':
            ut['nytt_pastigande_vardag'] = [round(tk['ny_tackning_inv'] * r_ln * andel, 2),
                                            round(tk['ny_tackning_inv'] * max(r_hi, r_ln) * andel, 2)]
            ut['xy'] = list(map(float, f['xy']))
        res['ua'][f['id']] = ut
        for k, s in scen.items():
            pl = s['plan'].copy(); pl['scenario'] = f"{f['id']}_{k}"
            planer.append(pl)
        geo += geometri(f, trafikerar, xy, fg, sg)
        print(f"{f['id']}: Δ {f['delta']} min/tur, {round(f['km_tur'], 2)} km/tur, driftform {val}, "
              f"{len(trafikerar)}/{alla_linjeturer} turer, täckning {tk}, resenärer/vardag {re['vardag']}")
        for k, s in scen.items():
            print(f"   {k:22s} ryms={s['ok']} robust={s['robust']} fordon={s['nt']['fordon']} turer={len(s['turer'])} "
                  f"skift={len(s['skift'])} varv={s['nt']['varv_utan_reglering']} min_vand={s['nt']['min_vandtid']} "
                  f"vo<5={s['nt']['varv_vo_under_marginal']} min_centrum={s['nt']['min_centrum_vo']} "
                  f"omloppstid={s['nt']['omloppstid_h']} km={s['nt']['km']}")

    pd.concat(planer).drop(columns=['monster']).to_csv(P / 'b4_omlopp_scenarier.csv', index=False)
    pd.concat(tack).round({'x': 1, 'y': 1, 'bef': 5}).to_csv(P / 'b4_tackning_ua.csv.gz', index=False)
    gpd.GeoDataFrame(geo, crs=C.CRS_METRISK).to_file(P / 'b4_ua.gpkg', layer='ua', driver='GPKG')
    with open(P / 'b4_ua.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=float)


if __name__ == '__main__':
    main()
