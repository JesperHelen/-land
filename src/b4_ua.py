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
  5   Linje V tar över svängen Stenhuggarvägen – Cedersvägen – Klintvägen och linje N kör rakt på Västra utfarten
      (operatörens förslag via beställaren 2026-11-15). Linje N: Sjukhuset → Västra macken → Elverksgatan;
      linje V: Åsvägen → Stenhuggarvägen → Cedersvägen → Klintvägen → Tekniska verken. Avfarten till
      Stenhuggarvägen ligger norr om hållplatsen Västra macken, så V stannar vid Stenhuggarvägen (50 m bort).
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
  * Bo-Bil: linje Norra är enkelriktad och Maxinge har bara hållplats på västra sidan, så bussen passerar Maxinge
    söderut. För att nå Bo-Bil vänder bussen i rondellen söder om Maxinge, kör norrut till rondellen norr om
    Maxinge, Michaelsvägen österut och Godbyvägen söderut till Bo-Bil (västra sidan) och vidare till Bolstavägen
    (beställaren 2026-11-23). Körtiden skalas med vägavståndet (OSRM) Maxinge – Bo-Bil – Bolstavägen mot
    Maxinge – Vikingagränd – Bolstavägen och dagens schemalagda tid för delsträckan (1,5 min). Bo-Bil blir däremot
    ett verkligt uppehåll (+0,5 min), medan bussen i praktiken sällan stannar vid Vikingagränd (≈ 0,05
    påstigande per vardag). Netto +0,1 min per tur. Minskad väntan vid Nya Godbyvägen kan inte kvantifieras
    utan realtidsdata och ingår inte (försiktig bedömning).
  * Flygplatsen: körvägen enligt beställarens skiss (s01_vagdragning). Tilläggs-km = skissens längd Posten →
    terminalen → Norra Svibyvägen → Källarvägen minus dagens Posten → Källarvägen; tilläggstid = tilläggs-km i
    KMH_FLYG km/h + 0,5 min uppehåll, avrundat uppåt till halv minut (känslighet ± 1 min).
    Flygen (bokningssidan, beställaren 2026-11-15): avgångar 07:15 Arlanda, 11:00 Åbo, 17:10 Arlanda; ankomster
    10:35 från Arlanda, 16:45 från Åbo, 21:35 från Arlanda. 'Y': V-turer som är vid flygplatsen 2 h – 1,5 h före
    en avgång (FLYG_FORE), och den tur som lämnar flygplatsen närmast 30 min efter en ankomst (20–45 min,
    FLYG_EFTER). Flyg som ingen tur i dagens tidtabell når prövas som extra turer (flyg_extraturer).
  * Svängen (UA 5): linje N kör i dag Sjukhuset → Elverksgatan via Stenhuggarvägen, Cedersvägen och Klintvägen på
    3,0 min; rak väg på Västra utfarten tar enligt tidtabellen för linje Ö cirka 2,3 min. Operatören bedömer
    vinsten till 'ett par minuter' (verklig körtid): DELTA_SVANG = 2 min, känslighet 1 min. Linje N blir lika
    mycket kortare (alla turer) som linje V blir längre (de V-turer som ryms).
  * Solberget indragen (linje Ö): bussen kör direkt mellan hållplatserna före och efter Solberget, med den
    kortaste tid som tidtabellen har för den direkta sträckan (1,6–2,5 min kortare per tur).
Verifiering (ramen 'inga fler bussar'): se b4_omlopp.py – omloppen följer normen att föraren byter linje
S ↔ N och Ö ↔ V i centrum. Varje UA prövas med alla turer i dagens tidtabell; om det inte ryms prövas vilka
turer som ryms, och om det ryms men ger fler varv utan reglering än i dag prövas en robust variant.
UA på linje V prövas dessutom som genomgående linje V–Ö ('VO', V och Ö sammanslagna): dagens omlopp ligger fast,
bussen fortsätter direkt som linje Ö (0,5 min) och Ö startar när V har kommit tillbaka. Det enda kravet är att
varvet V + Ö ryms inom 55 min, dvs. minst 5 min i centrum, helst inom 50 min (beställaren 2026-10-15,
b4_omlopp.genomgaende_ryms).
Effekter
  * Täckning: delpunkter 50 m (A2) – avgångar inom 400 m före/efter, klassförändring.
  * Resenärer: korrigerad OD-matris (A1) utlagd på restidsnätet (b4_natverk.py) – berörda resor och
    resenärsminuter; omräknat till vardag med kvoten påstigande/vardag ÷ OD-resor/h.
  * Tillkommande påstigande: påstigande per invånare inom 400 m vid linjens bostadshållplatser (tvättad höstdata 2026).
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
       'Posten': '9025302000035802', 'Källarvägen': '9025302000025902', 'Solberget': '9025302000062201',
       'Sjukhuset': '9025302000039601', 'Stenhuggarvägen': '9025302000062401', 'Cedersvägen': '9025302000062701',
       'Klintvägen': '9025302000062901', 'Elverksgatan': '9025302000063701',
       'Västra macken in': '9025302000055901', 'Tekniska verken in': '9025302000049201', 'Åsvägen': '9025302000067401'}
UPPEHALL = 0.5
RESTID_BEFINTLIG_VAG = 2.0     # min – befintlig väg Norrgårdsvägen ↔ ny hållplats Möckelö Strand (beställaren)
RESTID_FORLANGNING = 1.0       # min – förlängd Norrgårdsvägen, Möckelö Strand → ny hållplats (beställaren)
# Utredningsalternativ (UA): titel och huvudalternativ = den mest realistiska driftformen, som visas på kartan.
# Övriga driftformer redovisas i rapporten (alternativ som kräver fler bussar är uteslutna).
TITEL = {'1a': 'UA 1a – Möckelö Strand ny via dagens vägar', '1b': 'UA 1b – Möckelö Strand ny via förlängd Norrgårdsvägen',
         '2': 'UA 2 – N2 på linje Ö', '3': 'UA 3 – Linje N via Bo-Bil', '4': 'UA 4 – Linje V–Ö via flygplatsen',
         '5': 'UA 5 – Linje V via Cedersvägen, linje N rakt på Västra utfarten'}
HUVUD_TEXT = {'1a': 'V och Ö sammanslagna (varv V + Ö inom timmen, ≥ 5 min i centrum)',
              '1b': 'V och Ö sammanslagna (varv V + Ö inom timmen, ≥ 5 min i centrum)',
              '2': 'alla turer', '3': 'alla turer',
              '4': 'V och Ö sammanslagna (varv V + Ö inom timmen, ≥ 5 min i centrum)',
              '5': 'V och Ö sammanslagna (varv V + Ö inom timmen, ≥ 5 min i centrum); linje N alla turer'}
# UA 5 (Axbuss via beställaren 2026-11-15): linje V tar över svängen Stenhuggarvägen – Cedersvägen – Klintvägen och linje N
# kör rakt på Västra utfarten. Svängen tar enligt operatören "ett par minuter"; tidtabellen ger cirka 1 minut.
DELTA_SVANG = 2.0              # min per tur – svängen (operatörens uppgift); känslighet 1 min (tidtabellen)
KMH_FLYG = 25.0                # km/h – medelhastighet på omvägen till flygplatsen
# Flygen enligt bokningssidan (beställaren 2026-11-15, vardagar i november 2026; flygbolag Amapola Flyg)
FLYG_AVGANGAR = {'07:15': 'Stockholm-Arlanda (HP 281)', '11:00': 'Åbo (HP 285)', '17:10': 'Stockholm-Arlanda (HP 283)'}
FLYG_ANKOMSTER = {'10:35': 'från Stockholm-Arlanda (HP 282)', '16:45': 'från Åbo (HP 286)',
                  '21:35': 'från Stockholm-Arlanda (HP 284)'}
FLYG_FORE = (120, 90)          # min – bussen vid flygplatsen 2 h till 1,5 h före avgång (beställaren)
FLYG_EFTER = (25, 45, 30)      # min – bussen lämnar flygplatsen cirka 30 min efter landning (godtas 25–45 min)
EXTRA_VAND = 3.0               # min – minsta uppehåll före och efter en extra tur i omloppet


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
            'flyg_avgangar': FLYG_AVGANGAR, 'flyg_ankomster': FLYG_ANKOMSTER,
            'fore_avgang_min': list(FLYG_FORE), 'efter_ankomst_min': list(FLYG_EFTER)}


def _flygkrav():
    """Varje flyg och tidsfönstret då bussen ska vara vid flygplatsen (min efter midnatt) och måltiden."""
    ut = []
    for a, txt in FLYG_AVGANGAR.items():
        ut.append({'flyg': f'avgång {a} till {txt}', 'typ': 'avgång', 'tid': a, 'fran': hhmm(a) - FLYG_FORE[0],
                   'till': hhmm(a) - FLYG_FORE[1], 'mal': hhmm(a) - (FLYG_FORE[0] + FLYG_FORE[1]) / 2})
    for a, txt in FLYG_ANKOMSTER.items():
        ut.append({'flyg': f'ankomst {a} {txt}', 'typ': 'ankomst', 'tid': a, 'fran': hhmm(a) + FLYG_EFTER[0],
                   'till': hhmm(a) + FLYG_EFTER[1], 'mal': hhmm(a) + FLYG_EFTER[2]})
    return sorted(ut, key=lambda k: k['fran'])


def flygmatchning(t):
    """Den V-tur i dagens tidtabell som passar varje flyg (vid flygplatsen inom fönstret, närmast måltiden)."""
    fp = flygplatsen(); vt = t[t.linje == 'V'].sort_values('avg')
    vid = {r.trip_id: r.avg + fp['framme_vid_flygplatsen_min_efter_avgang'] for r in vt.itertuples()}
    tl = t.set_index('trip_id'); ut = []
    for k in _flygkrav():
        kand = sorted((abs(x - k['mal']), x, tid) for tid, x in vid.items() if k['fran'] - 1e-9 <= x <= k['till'] + 1e-9)
        r = {kk: k[kk] for kk in ('flyg', 'typ', 'tid')}
        r['fonster'] = f"{O.hm(k['fran'])}–{O.hm(k['till'])}"
        if kand:
            _, x, tid = kand[0]
            r.update({'trip_id': tid, 'v_tur': O.hm(tl.at[tid, 'avg']), 'vid_flygplatsen': O.hm(x),
                      'min_fore_eller_efter_flyget': int(round(abs(x - hhmm(k['tid']))))})
        ut.append(r)
    return ut


def flygturer(t):
    """V-turer som behövs för flygen ('Y'): {trip_id: syfte}."""
    ut = {}
    for r in flygmatchning(t):
        if r.get('trip_id'):
            ut.setdefault(r['trip_id'], []).append(('till flyget ' if r['typ'] == 'avgång' else 'från flyget ') + r['tid'])
    return {k: ', '.join(v) for k, v in ut.items()}


def flyg_extraturer(t, plan=None):
    """Extra V-turer via flygplatsen för flyg som ingen tur i dagens tidtabell når. Avgång från centrum avrundad till
    5 min så att bussen är vid flygplatsen nära måltiden; körs av ett omlopp som står stilla (minst EXTRA_VAND min
    före och efter) – annars förlängs det omlopp som ger minst förlängning. Extra fordonstimmar = turens körtid
    plus eventuell förlängning av omloppet (försiktigt: även en tur i en befintlig paus räknas)."""
    fp = flygplatsen(); plan = O.omlopp_operator(t) if plan is None else plan
    v0 = t[t.linje == 'V'].iloc[0]
    kortid = float(v0.kortid + fp['delta_min_per_tur']); km = float(v0.km + fp['extra_km_per_tur'])
    fram = fp['framme_vid_flygplatsen_min_efter_avgang']
    ut = []
    for k, m in zip(_flygkrav(), flygmatchning(t)):
        if m.get('trip_id'):
            continue
        avg = 5 * round((k['mal'] - fram) / 5); ank = avg + kortid; vid = avg + fram
        kand = []
        for (b, om), d in plan.groupby(['buss', 'omlopp']):
            if om == 'J':
                continue
            upptagen = ((d.avg < ank + EXTRA_VAND) & (d.ank > avg - EXTRA_VAND)).any()
            if upptagen:
                continue
            forl = max(0.0, d.avg.min() - (avg - EXTRA_VAND)) + max(0.0, ank + EXTRA_VAND - d.ank.max())
            fore, efter = d[d.ank <= avg], d[d.avg >= ank]
            kand.append((forl, str(om), O.hm(fore.ank.max()) if len(fore) else None,
                         O.hm(efter.avg.min()) if len(efter) else None))
        forl, om, fore, efter = min(kand) if kand else (np.nan, None, None, None)
        ut.append({'flyg': k['flyg'], 'fonster': m['fonster'], 'avg_centrum': O.hm(avg), 'vid_flygplatsen': O.hm(vid),
                   'ank_centrum': O.hm(ank),
                   'min_fore_eller_efter_flyget': int(round(abs(vid - hhmm(k['tid'])))),
                   'omlopp': om, 'omlopp_ledigt_fran': fore, 'omlopp_nasta_tur': efter,
                   'forlangning_min': round(float(forl), 1), 'inom_omloppet': bool(forl == 0),
                   'kortid_min': round(kortid, 1), 'km': round(km, 2),
                   'fordonstimmar': round((kortid + forl) / 60, 2)})
    return ut


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


# ---------------------------------------------------------------------- UA 5: svängen
SVANG = {'n_fore': ['Sjukhuset', 'Stenhuggarvägen', 'Cedersvägen', 'Klintvägen', 'Elverksgatan'],
         'n_efter': ['Sjukhuset', 'Västra macken in', 'Elverksgatan'],
         'v_fore': ['Åsvägen', 'Västra macken in', 'Tekniska verken in'],
         'v_efter': ['Åsvägen', 'Stenhuggarvägen', 'Cedersvägen', 'Klintvägen', 'Tekniska verken in']}


@lru_cache(maxsize=1)
def _xy():
    return stopp_xy()


def _avst(a, b):
    xy = _xy()
    return float(np.hypot(*(xy.loc[a, ['x', 'y']].to_numpy(float) - xy.loc[b, ['x', 'y']].to_numpy(float))))


@lru_cache(maxsize=1)
def svang():
    """Längder och tidtabellstider för UA 5 (svängen Stenhuggarvägen – Cedersvägen – Klintvägen)."""
    import s01_vagdragning as V
    sg = V.segmentgeometri(); fg = V.uageometri(); H = HPL
    def L(a, b):                                               # vägavstånd längs gatunätet (OSRM)
        k = (H[a], H[b])
        return V.langd(sg[k]) if k in sg else (fg[k]['langd_m'] if k in fg else 1.25 * _avst(*k))
    kedja = lambda s_: sum(L(a, b) for a, b in zip(s_[:-1], s_[1:]))
    n_idag, n_rak = kedja(SVANG['n_fore']), kedja(SVANG['n_efter'])
    v_idag, v_svang = kedja(SVANG['v_fore']), kedja(SVANG['v_efter'])
    t = O.turer(); g = D.gtfs()['stop_times']
    def tid(ln, a, b):
        r = t[t.linje == ln].iloc[0]; st = g[g.trip_id == r.trip_id].set_index('stop_id')
        return float(st.loc[H[b], 't_arr'] - st.loc[H[a], 't_dep'])
    n_tt = tid('N', 'Sjukhuset', 'Elverksgatan')
    o_tt = tid('Ö', 'Sjukhuset', 'Tekniska verken in')
    hast = (n_idag / 1000) / (n_tt / 60)                       # km/h i svängen enligt tidtabellen
    rak_tt = o_tt + _avst(H['Tekniska verken in'], H['Elverksgatan']) / 1000 / hast * 60
    gang = {k: round(min(_avst(H[k], H[x]) for x in ('Västra macken in', 'Tekniska verken in', 'Elverksgatan')))
            for k in ('Stenhuggarvägen', 'Cedersvägen', 'Klintvägen')}           # fågelvägen (gång)
    return {'langd_n_svang_m': round(n_idag), 'langd_n_rak_m': round(n_rak),
            'langd_v_idag_m': round(v_idag), 'langd_v_svang_m': round(v_svang),
            'km_n_per_tur': round((n_rak - n_idag) / 1000, 3), 'km_v_per_tur': round((v_svang - v_idag) / 1000, 3),
            'tidtabell_n_sjukhuset_elverksgatan_min': round(n_tt, 2),
            'tidtabell_o_sjukhuset_tekniska_verken_min': round(o_tt, 2),
            'tidtabell_v_vastra_macken_tekniska_verken_min': round(tid('V', 'Västra macken in', 'Tekniska verken in'), 2),
            'rak_vag_enligt_tidtabell_min': round(rak_tt, 2), 'vinst_enligt_tidtabell_min': round(n_tt - rak_tt, 2),
            'delta_operatoren_min': DELTA_SVANG, 'avstand_till_vastra_utfarten_m': gang}


def _ersatt(m, fore, efter, tid):
    """Byter delsträckan fore (hållplatser i följd) mot efter i mönstret m; tid = ny total åktid, fördelad efter
    fågelvägen mellan hållplatserna."""
    s = list(m['stopp']); n = len(fore)
    i = next((i for i in range(len(s) - n + 1) if s[i:i + n] == fore), None)
    if i is None:
        return m, False
    om = D.hallplatsomraden()['omrade']
    d = [_avst(a, b) for a, b in zip(efter[:-1], efter[1:])]
    akt = list(m['akt'])
    m = dict(m)
    m['stopp'] = tuple(s[:i] + efter + s[i + n:])
    m['zoner'] = tuple(list(m['zoner'])[:i] + [om.get(x, '?') for x in efter] + list(m['zoner'])[i + n:])
    m['akt'] = np.array(akt[:i] + [tid * x / sum(d) for x in d] + akt[i + n - 1:], float)
    return m, True


def _akt(m, fore):
    s = list(m['stopp']); n = len(fore)
    i = next((i for i in range(len(s) - n + 1) if s[i:i + n] == fore), None)
    return None if i is None else float(np.sum(m['akt'][i:i + n - 1]))


def flytta_monster(mon, f, d_v=None, d_n=None, med_v=True, andel_v=1.0):
    """UA 5: linje N kör rakt (d_n min, negativt = kortare) och linje V tar svängen (d_v min; andel_v skalar
    tillägget när bara en del av V-turerna kör svängen)."""
    d_v = f['delta'] if d_v is None else d_v; d_n = f['delta_n'] if d_n is None else d_n
    ut = []
    for m in mon:
        if m['linje'] == f['fran_linje'] and _akt(m, f['n_fore']) is not None:
            m, _ = _ersatt(m, f['n_fore'], f['n_efter'], max(_akt(m, f['n_fore']) + d_n, 0.3))
        elif med_v and m['linje'] == f['linje'] and _akt(m, f['v_fore']) is not None:
            m, _ = _ersatt(m, f['v_fore'], f['v_efter'], _akt(m, f['v_fore']) + d_v * andel_v)
        ut.append(m)
    return ut


def flytta_hallplatser(h, f, turer_v, turer_n, xy):
    """UA 5: linje N:s turer lämnar svängen och stannar vid Västra macken; linje V:s turer (turer_v) trafikerar
    Cedersvägen och Klintvägen."""
    h = h.copy()
    for fore, efter, tn, ln in ((f['n_fore'], f['n_efter'], frozenset(turer_n), f['fran_linje']),
                                (f['v_fore'], f['v_efter'], frozenset(turer_v), f['linje'])):
        if not tn:
            continue
        for s in set(fore) - set(efter):
            if s in h.index:
                h.at[s, 'turer'] = h.at[s, 'turer'] - tn
                h.at[s, 'linjer'] = ','.join(x for x in str(h.at[s, 'linjer']).split(',') if x != ln)
        for s in set(efter) - set(fore):
            if s in h.index:
                h.at[s, 'turer'] = h.at[s, 'turer'] | tn
                lj = [x for x in str(h.at[s, 'linjer']).split(',') if x]
                h.at[s, 'linjer'] = ','.join(sorted(set(lj) | {ln}))
            else:
                h.loc[s] = {'turer': tn, 'linjer': ln, 'avgangar': len(tn), 'x': xy.at[s, 'x'], 'y': xy.at[s, 'y'],
                            'namn': xy.at[s, 'namn']}
    h = h[h.turer.map(len) > 0].copy()
    h['avgangar'] = h.turer.map(len)
    return h


def n_vandtider(plan, linje='N'):
    """Uppehållet i centrum efter linjens turer (vändning/byte till partnerlinjen) – min, median, antal < 3 min."""
    v = plan.loc[(plan.linje == linje) & plan.vand_efter.notna() & (plan.vand_efter <= O.DEPA_GRANS), 'vand_efter']
    return {'min': round(float(v.min()), 1), 'median': round(float(v.median()), 1),
            'under_3_min': int((v < O.REKOMMENDERAD_VANDTID - 1e-9).sum()), 'antal': int(len(v)),
            'summa_h': round(float(v.sum() / 60), 2)}


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
    ut.append({'id': '3', 'namn': 'Linje N via Bo-Bil i stället för Vikingagränd, norra slingan baklänges', 'kort': '3 N via Bo-Bil',
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
    sv = svang(); t = O.turer(); H = HPL; xy = _xy()
    ced = [H['Cedersvägen'], H['Klintvägen']]
    ut.append({'id': '5', 'namn': 'Linje V via Cedersvägen, linje N rakt på Västra utfarten', 'kort': '5 Svängen till V',
               'titel': TITEL['5'], 'huvud': 'VO', 'linje': 'V', 'fran_linje': 'N', 'typ': 'flytta',
               **{k: [H[x] for x in v] for k, v in SVANG.items()},
               'korvag': 'Linje V: Åsvägen → Stenhuggarvägen – Cedersvägen – Klintvägen → Tekniska verken; '
                         'linje N: Sjukhuset → Västra utfarten (Västra macken) → Elverksgatan',
               'hpl_namn': 'Cedersvägen och Klintvägen', 'xy': tuple(xy.loc[ced, ['x', 'y']].mean().to_numpy(float)),
               'delta': DELTA_SVANG, 'delta_n': -DELTA_SVANG, 'km_tur': sv['km_v_per_tur'], 'km_n': sv['km_n_per_tur'],
               'turer_n': list(t[t.linje == 'N'].sort_values('avg').trip_id), 'genomgaende': [('V', 'Ö')],
               'kansl': [1.0]})
    return ut


def stopp_xy():
    g = D.gtfs()['stops'].set_index('stop_id')
    x, y = D.till_metrisk(g.lon.values, g.lat.values)
    return pd.DataFrame({'x': x, 'y': y, 'namn': g.stop_name.values}, index=g.index)


def bobil_delta(xy=None):
    """UA 3: Norras norra slinga körs baklänges via Bo-Bil (b4_ua3_slinga.py): väglängd och körtid per varv."""
    u = json.load(open(P / 'b4_ua3_slinga.json', encoding='utf-8'))
    return {'variant': 'norra slingan baklänges', 'varv_idag_m': u['varv_idag_m'], 'varv_ny_m': u['varv_ny_m'],
            'kortid_idag_min': u['kortid_idag_min'], 'kortid_ny_min': u['kortid_ny_min'], 'uppehall_bobil_min': UPPEHALL,
            'delta_min': u['delta_min'], 'delta_km': u['delta_km']}


def ua3_monster(mon0):
    """Restidsnätets mönster med Norras norra slinga baklänges via Bo-Bil (samma som b4_ua3_slinga)."""
    u = json.load(open(P / 'b4_ua3_slinga.json', encoding='utf-8'))
    om = D.hallplatsomraden()['omrade']
    n0p = max([m for m in mon0 if m['linje'] == 'N'], key=lambda m: len(m['turer']))
    return [m if m is not n0p else {**m, 'stopp': tuple(u['stopp_ny']),
                                    'zoner': tuple(om.reindex(u['stopp_ny']).fillna('Bo-Bil')),
                                    'akt': np.array(u['akt_ny'])} for m in mon0]


# ====================================================================== omlopp
def omlopp_scenarier(f, t, r, ref):
    """Verifierar UA:t mot omloppen (normen: byte S ↔ N och Ö ↔ V, se b4_omlopp).
      alla          alla berörda turer
      ryms          (om alla inte ryms) turerna prövas en i taget
      robust        (om alla ryms men ger fler varv utan reglering än i dag) turer som kan ändras utan det
      VO            (linje V) genomgående linje V–Ö: varv V + Ö inom timmen med minst 5 min i centrum
      VO_sol        (UA 4) dito med Solberget indragen; Y_VO, Y_VO_sol bara turerna för flygen
      konservativ…  (1b) känslighet med den högre körtiden delta_konservativ
      kansl_…       känslighet för körtiden (UA 4: VO; UA 5: alla, ryms och VO med 1 min)
      N             (UA 5) variant: bara linje N rakt på, ingen linje i svängen (dagens omlopp)
    UA 5 (typ 'flytta'): linje N:s turer blir alla delta min kortare (bas), linje V:s turer delta min längre."""
    linjeturer = t[t.linje == f['linje']]
    if f['typ'] == 'ny' and f['segment'][1] is None:          # Möckelö: turer som passerar vändpunkten
        berorda = list(linjeturer[linjeturer.monster.map(lambda m: f['segment'][0] in m)].trip_id)
    else:
        berorda = list(linjeturer.trip_id)
    scen = {}

    plan0 = O.omlopp_operator(t)                              # dagens omlopp (operatörens) – fast vid linje V–Ö
    v_regel = f['linje'] == 'V'                                # linje V: kravet på tid i centrum per varv V + Ö
    vv = O.bygg_omlopp(t, referens=ref) if v_regel else None
    flytta = f['typ'] == 'flytta'
    nbas = (lambda d: {k: -d for k in f['turer_n']}) if flytta else (lambda d: None)   # UA 5: linje N kortare

    def kor(namn, valda, d, skift=None, bas=None, vo=False, fast=None, sol=False):
        dd = dict(bas or {})
        for k in valda:
            dd[k] = dd.get(k, 0.0) + d
        fast = fast if fast is not None else (plan0 if vo else None)
        km = {k: f['km_tur'] for k in valda}
        if flytta:
            km.update({k: f['km_n'] for k in f['turer_n']})
        plan, nt, ok = O.verifiera(t, dd, r, km_delta=km, skift=skift, referens=ref, fast=fast)
        if v_regel and not vo:
            ok = ok and O.varv_ok(plan, vv)
        rob = (nt['varv_vo_under_marginal'] <= O.nyckeltal(fast if fast is not None else vv)['varv_vo_under_marginal']) \
            if v_regel else O.ar_robust(nt, r)
        scen[namn] = {'plan': plan, 'nt': nt, 'ok': ok, 'robust': rob, 'turer': list(valda), 'vo': vo,
                      'skift': dict(skift or {}), 'delta': d, 'solberget': sol}

    def vo(namn, kand, d, bas=None, plan=None, sol=False):
        plan = plan0 if plan is None else plan
        v, s_ = O.genomgaende_ryms(t, kand, d, plan, bas=bas)
        kor(namn, v, d, s_, bas=bas, vo=True, fast=plan, sol=sol)

    def pröva(prefix, d):
        p = prefix + '_' if prefix else ''
        b = nbas(d)
        kor(p + 'alla', berorda, d, bas=b)
        bas = scen[p + 'alla']
        if not bas['ok']:
            kor(p + 'ryms', O.turer_som_ryms(t, berorda, d, r, bas=b, varv=vv, referens=ref), d, bas=b)
        elif not bas['robust'] and f['linje'] != 'V':
            kor(p + 'robust', O.turer_som_ryms(t, berorda, d, r, robust=True, bas=b, referens=ref), d, bas=b)
        if f['linje'] == 'V':
            vo(p + 'VO', berorda, d, bas=b)

    pröva('', f['delta'])
    if flytta:                                                 # variant: bara linje N rakt på, svängen utan buss
        kor('N', [], f['delta'], bas=nbas(f['delta']), vo=True)
        scen['N']['vo'] = False
    if f.get('delta_konservativ'):
        pröva('konservativ', f['delta_konservativ'])
    if f.get('solberget'):                                     # dito med Solberget indragen på linje Ö
        vo('VO_sol', berorda, f['delta'], solberget_delta(t), sol=True)
    if f.get('flygturer'):                                     # 'Y': bara turerna för flygen
        y = list(flygturer(t))
        kor('Y_ryms', O.turer_som_ryms(t, y, f['delta'], r, varv=vv, referens=ref), f['delta'])
        vo('Y_VO', y, f['delta'])
        vo('Y_VO_sol', y, f['delta'], solberget_delta(t), sol=True)
    for d in f.get('kansl', []):                               # känslighet för körtiden
        if flytta:
            pröva(f'kansl_{d:g}', d)
        else:
            vo(f'kansl_{d:g}_VO', berorda, d)
    return scen


def drift(f, scen):
    """Huvudalternativ (den mest realistiska driftformen, f['huvud']); annars alla turer om de ryms, annars
    genomgående V/Ö om det prövats, annars de turer som ryms."""
    if f.get('huvud') in scen and scen[f['huvud']]['ok']:
        return f['huvud']
    return 'alla' if scen['alla']['ok'] else ('VO' if 'VO' in scen else 'ryms')


KANSL_OMVAG = [3.0, 4.0, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0]      # min/tur – omvägen till flygplatsen (känslighet)
KANSL_POLICY = [('A', 'Varvet V + Ö ≤ 55 min (krav), Solberget kvar', O.MARGINAL_VARV, False),
                ('B', 'Varvet V + Ö ≤ 55 min (krav), Solberget indragen där det behövs', O.MARGINAL_VARV, True),
                ('C', 'Varvet V + Ö ≤ 50 min (helst), Solberget kvar', O.MARGINAL_VARV_ONSKAD, False),
                ('D', 'Varvet V + Ö ≤ 50 min (helst), Solberget indragen där det behövs', O.MARGINAL_VARV_ONSKAD, True)]


def kanslighet_ua4(t, plan0, pkt, hpl0, xy, pastigande_solberget):
    """UA 4 (V och Ö sammanslagna): känslighet för omvägens körtid, kravet på varvet (≤ 55 min, helst ≤ 50) och
    indragning av Solberget bara på de Ö-turer där varvet annars inte ryms. Ö startar när V har kommit tillbaka.
    Alla V-turer och UA 4Y (flygturerna)."""
    sol = solberget_delta(t); tl = t.set_index('trip_id')
    urval = [('alla', list(t[t.linje == 'V'].trip_id)), ('Y', list(flygturer(t)))]
    f_sol = {'typ': 'byt', 'linje': 'Ö', 'bort': HPL['Solberget'], 'till': []}
    tack = {}
    rader = []
    for u, kand in urval:
        for d in KANSL_OMVAG:
            for pid, txt, marg, med_sol in KANSL_POLICY:
                v, sk, utan = O.genomgaende_ryms(t, kand, d, plan0, marginal=marg, sol=sol if med_sol else None,
                                                 detalj=True)
                dd = {k: d for k in v}
                for j in utan:
                    dd[j] = dd.get(j, 0.0) + sol[j]
                p = O.plan_fast(plan0.reset_index(drop=True), O.med_andring(t, dd, sk))
                c = O.varv_vo(p).set_index('trip_id').centrum_min.reindex(v)
                c = c[np.isfinite(c)]
                sena = [sk.get(j, 0.0) + (sol[j] if j in utan else 0.0) for j in set(sk) | set(utan)]
                key = tuple(sorted(utan))
                if utan and key not in tack:
                    tack[key] = tackning(pkt, hpl0, f_sol, list(utan), xy)[0]
                tk = tack.get(key, {})
                rader.append({'urval': u, 'omvag_min': d, 'policy': pid, 'policy_text': txt, 'marginal_min': marg,
                              'turer': len(v), 'turer_tot': len(kand),
                              'turer_som_i_dag': [O.hm(tl.at[x, 'avg']) for x in sorted(set(kand) - set(v),
                                                                                      key=lambda x: tl.at[x, 'avg'])],
                              'o_turer_utan_solberget': [O.hm(tl.at[x, 'avg']) for x in sorted(utan, key=lambda x: tl.at[x, 'avg'])],
                              'solberget_avgangar': int((t.linje == 'Ö').sum()) - len(utan),
                              'o_max_efter_pulsen_min': round(max(sk.values()), 1) if sk else 0.0,
                              'o_max_senare_i_centrum_min': round(max(sena), 1) if sena else 0.0,
                              'min_centrum_min': round(float(c.min()), 1) if len(c) else None,
                              'solberget_samre_klass_inv': tk.get('samre_klass_inv', 0),
                              'solberget_utan_hallplats_inv': tk.get('forlorad_tackning_inv', 0),
                              'solberget_berorda_pastigande_vardag': round(pastigande_solberget * len(utan) /
                                                                           int((t.linje == 'Ö').sum()), 2)})
    return rader


# ====================================================================== täckning
def tackning(pkt, hpl0, f, turer_som_trafikerar, xy):
    h = hpl0.copy()
    if f['typ'] == 'flytta':
        h = flytta_hallplatser(h, f, turer_som_trafikerar, f['turer_n'], xy)
    elif f['typ'] == 'ny':
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
    if f['typ'] == 'flytta':
        cx, cy = xy.loc[sorted(set(f['n_fore']) | set(f['v_efter'])), ['x', 'y']].mean()
    else:
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
    if f['typ'] == 'flytta':
        # UA 5: linje N kör rakt på alla turer; svängen trafikeras av linje V på andelen andel_turer av V-turerna,
        # på övriga turer finns bara gång till Västra utfarten – viktat medel av de två fallen
        j1 = N.jamfor(nat0, N.Nat(flytta_monster(mon0, f), zoner))
        j0 = N.jamfor(nat0, N.Nat(flytta_monster(mon0, f, med_v=False), zoner)) if andel_turer < 1 else j1
        j = {p: {k: andel_turer * j1[p][k] + (1 - andel_turer) * j0[p][k] for k in j1[p]} for p in ('FM', 'EM')}
        return _resenarer_ut(j, 1.0)
    if f.get('id') == '3':                                     # UA 3: norra slingan baklänges via Bo-Bil
        return _resenarer_ut(N.jamfor(nat0, N.Nat(ua3_monster(mon0), zoner)), andel_turer)
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
    return _resenarer_ut(N.jamfor(nat0, nat1), andel_turer)


def _resenarer_ut(j, andel_turer):
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


def ua5_detaljer(f, scen, val, t, zoner, mon0, nat0):
    """UA 5: påstigande i svängen, resenärer som åker genom svängen på linje N, restid för resor till och från
    svängens hållplatser och linje N:s uppehåll i centrum före och efter."""
    H = HPL; bed = pd.read_csv(P / 'a3_hallplatsbedomning.csv').set_index('omrade')
    past = {k: round(float(bed.at[k, 'pastigande_vardag']), 2) for k in ('Stenhuggarvägen', 'Cedersvägen', 'Klintvägen')}
    fak = N.dagsfaktor()
    mi = next(i for i, m in enumerate(mon0) if m['linje'] == f['fran_linje'] and H['Sjukhuset'] in m['stopp'])
    k_ = list(mon0[mi]['stopp']).index(H['Sjukhuset'])
    gen = []
    for per in ('FM', 'EM'):
        fl, ps = nat0.utlagg(N.od_matris(per))
        gen.append(fl.get((mi, k_), 0.0))
    genom = float(np.mean(gen)) * fak                          # resenärer ombord Sjukhuset → Stenhuggarvägen per vardag
    om = D.hallplatsomraden()['omrade']
    zs = sorted({om[x] for x in f['n_fore'][1:-1]})
    andel = len(scen[val]['turer']) / max(len(scen['alla']['turer']), 1)
    c0 = nat0.restider()
    c1 = N.Nat(flytta_monster(mon0, f), zoner).restider().reindex(index=nat0.zoner, columns=nat0.zoner)
    c1u = N.Nat(flytta_monster(mon0, f, med_v=False), zoner).restider().reindex(index=nat0.zoner, columns=nat0.zoner)
    zon = {}
    for z in zs:
        T = sum(N.od_matris(p).reindex(index=nat0.zoner, columns=nat0.zoner).fillna(0.0) for p in ('FM', 'EM')) / 2
        m = T.index.isin([z])[:, None] | T.columns.isin([z])[None, :]
        Tm = T.to_numpy() * m
        d = andel * (c1 - c0).to_numpy() + (1 - andel) * (c1u - c0).to_numpy()
        fin = np.isfinite(d)
        zon[z] = {'resor_vardag': round(float(Tm.sum()) * fak, 2),
                  'resenarsminuter_vardag': round(float((Tm[fin] * d[fin]).sum()) * fak, 1)}
    plan0 = O.omlopp_operator(t)
    return {'svang': svang(), 'pastigande_vardag': past, 'pastigande_vardag_summa': round(sum(past.values()), 2),
            'genomresande_n_vardag': round(genom, 1),
            'tidsvinst_genomresande_min_vardag': round(genom * -f['delta_n'], 1),
            'resor_till_fran_svangen': zon,
            'n_uppehall_centrum_idag': n_vandtider(plan0), 'n_uppehall_centrum_efter': n_vandtider(scen[val]['plan']),
            'v_turer_via_svangen': len(scen[val]['turer']), 'v_turer_tot': len(scen['alla']['turer']),
            'n_turer': len(f['turer_n'])}


# ====================================================================== geometri
def geometri(f, trafikerar, xy, fg, sg):
    """UA:ts objekt för kartor och GIS. Linjer som MultiLineString med en del per hållplatssegment (kan bytas
    mot OSRM-rutter i QGIS, rutta_med_osrm.py); planerad_del = 'från>till' för en väg som inte finns i dag."""
    import shapely
    import s01_vagdragning as V
    ml = lambda *d: shapely.MultiLineString([LineString(x) for x in d])
    n = len(trafikerar)
    if f['typ'] == 'flytta':
        H = HPL; P_ = lambda k: xy.loc[H[k], ['x', 'y']].to_numpy(float)
        seg = lambda a, b: sg[(H[a], H[b])] if (H[a], H[b]) in sg else \
            (fg[(H[a], H[b])]['xy'] if (H[a], H[b]) in fg else np.array([P_(a), P_(b)]))
        vag = 'OSRM' if V.kalla_text().startswith('Linjernas') else 'schematisk'
        nn = len(f['turer_n'])
        ut = [{'ua': '5', 'objekt': 'körväg utgår', 'vagdragning': vag, 'linje': 'N', 'avgangar': 0, 'planerad_del': '',
               'namn': 'Linje N: Sjukhuset – Stenhuggarvägen – Cedersvägen – Klintvägen – Elverksgatan (svängen)',
               'geometry': ml(seg('Sjukhuset', 'Stenhuggarvägen'), seg('Stenhuggarvägen', 'Cedersvägen'),
                              seg('Cedersvägen', 'Klintvägen'), seg('Klintvägen', 'Elverksgatan'))},
              {'ua': '5', 'objekt': 'ny körväg, befintlig väg', 'vagdragning': vag, 'linje': 'N', 'avgangar': nn,
               'planerad_del': '', 'namn': 'Linje N rakt på Västra utfarten: Sjukhuset – Västra macken – Elverksgatan',
               'geometry': ml(seg('Sjukhuset', 'Västra macken in'), seg('Västra macken in', 'Elverksgatan'))},
              {'ua': '5', 'objekt': 'ny körväg, befintlig väg', 'vagdragning': vag, 'linje': 'V', 'avgangar': n,
               'planerad_del': '',
               'namn': 'Linje V via svängen: Åsvägen – Stenhuggarvägen – Cedersvägen – Klintvägen – Tekniska verken',
               'geometry': ml(seg('Åsvägen', 'Stenhuggarvägen'), seg('Stenhuggarvägen', 'Cedersvägen'),
                              seg('Cedersvägen', 'Klintvägen'), seg('Klintvägen', 'Tekniska verken in'))}]
        for k in ('Stenhuggarvägen', 'Cedersvägen', 'Klintvägen'):
            ut.append({'ua': '5', 'objekt': 'hållplats byter linje N → V', 'namn': k, 'linje': 'V', 'avgangar': n,
                       'geometry': Point(*P_(k))})
        ut.append({'ua': '5', 'objekt': 'hållplats byter linje V → N', 'linje': 'N', 'avgangar': nn,
                   'namn': 'Västra macken (Stenhuggarvägen 50 m)', 'geometry': Point(*P_('Västra macken in'))})
        return ut
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
    mx, bv = HPL['Maxinge'], HPL['Bolstavägen']
    xy_ = lambda a: xy.loc[a, ['x', 'y']].to_numpy(float)
    g_gammal = ml(sg.get((mx, f['bort']), np.array([xy_(mx), v])), sg.get((f['bort'], bv), np.array([v, xy_(bv)])))
    u = json.load(open(P / 'b4_ua3_slinga.json', encoding='utf-8'))
    k = u['stopp_ny'].index(bv)                                  # Bolstavägen -> Bo-Bil -> Maxinge
    ny_ = [np.array(u['geometri_ny'][k]), np.array(u['geometri_ny'][k + 1])]
    vag_gl = 'OSRM' if V.kalla_text().startswith('Linjernas') else 'schematisk'
    return [{'ua': '3', 'objekt': 'hållplats utgår för linje N', 'namn': 'Vikingagränd', 'linje': 'N', 'avgangar': 0,
             'geometry': Point(*v)},
            {'ua': '3', 'objekt': 'ny hållplats för linje N', 'namn': 'Bo-Bil', 'linje': 'N', 'avgangar': n,
             'geometry': Point(*bo)},
            {'ua': '3', 'objekt': 'körväg utgår', 'vagdragning': vag_gl, 'namn': 'Maxinge – Vikingagränd – Bolstavägen',
             'linje': 'N', 'avgangar': 0, 'planerad_del': '', 'geometry': g_gammal},
            {'ua': '3', 'objekt': 'ny körväg, befintlig väg (norra slingan baklänges)', 'vagdragning': 'OSRM',
             'namn': 'Bolstavägen – Bo-Bil – Michaelsvägen – Maxinge', 'linje': 'N', 'avgangar': n, 'planerad_del': '',
             'geometry': ml(*ny_)}]


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
                                               sorted(flygturer(t).items(), key=lambda kv: tl0.at[kv[0], 'avg'])},
                'matchning': flygmatchning(t), 'extraturer': flyg_extraturer(t)}
    res = {'idag': nt0, 'genomgaende_vo': gen_vo, 'osrm_kontroll_nya_delstrackor': kontroll, 'solberget_indragen': res_sol, 'flygplatsen': res_flyg,
           'antaganden': {'uppehall_min': UPPEHALL, 'mockelo': mockelo(), 'max_skift_partner_min': O.MAX_SKIFT_PARTNER,
                          'bobil': bb, 'pastigande_per_inv': {k: v for k, v in rate.items() if k != 'per_hpl'},
                          'dagsfaktor': round(N.dagsfaktor(), 2)},
           'ua': {}}
    tl = t.set_index('trip_id')
    planer, tack, geo = [O.omlopp_operator(t).assign(scenario='idag', delta=0.0, skift=0.0)], [], []   # dagens = operatörens
    for f in alternativ():
        if f['typ'] == 'byt':
            f['delta'], f['km_tur'] = bb['delta_min'], bb['delta_km']
        scen = omlopp_scenarier(f, t, r, ref)
        val = drift(f, scen)
        trafikerar = scen[val]['turer']
        if f['typ'] == 'flytta':
            print('   UA 5 svängen:', svang())
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
        if f['typ'] == 'flytta':
            ut['km_n_per_tur'] = f['km_n']; ut['delta_n_min_per_tur'] = f['delta_n']
            ut['ua5'] = ua5_detaljer(f, scen, val, t, zoner, mon0, nat0)
            for d_ in f.get('kansl', []):                      # resenärer med känslighetens körtid
                k_ = f'kansl_{d_:g}_' + ('VO' if f'kansl_{d_:g}_VO' in scen else 'alla')
                a_ = len(scen[k_]['turer']) / max(len(scen['alla']['turer']), 1)
                ut['ua5'][f'resenarer_kansl_{d_:g}'] = resenarseffekt({**f, 'delta': d_, 'delta_n': -d_}, zoner, mon0,
                                                                      nat0, a_)['vardag']
            ut['ua5']['bara_n_rakt_pa'] = {'resenarer': resenarseffekt(f, zoner, mon0, nat0, 0.0)['vardag'],
                                           'tackning': tackning(pkt, hpl0, f, [], xy)[0]}
            print('   UA 5:', json.dumps({k: v for k, v in ut['ua5'].items() if k != 'svang'}, ensure_ascii=False,
                                         default=float))
        if f.get('flygturer'):                                 # vilka flyg varje driftform når
            fm = flygmatchning(t)
            ut['flyg_per_driftform'] = {k: [m['flyg'] for m in fm if m.get('trip_id') in set(s['turer'])]
                                        for k, s in scen.items()}
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

    kansl = kanslighet_ua4(t, O.omlopp_operator(t), pkt, hpl0, xy, res_sol['pastigande_vardag'] or 0.0)
    res['ua']['4']['kanslighet_solberget'] = kansl
    pd.DataFrame(kansl).assign(**{k: lambda d_, k=k: d_[k].map(', '.join) for k in ('turer_som_i_dag', 'o_turer_utan_solberget')}) \
        .to_csv(P / 'b4_kanslighet_ua4.csv', index=False)
    for r_ in kansl:
        print(f"   känslighet {r_['urval']:4s} {r_['omvag_min']:.1f} {r_['policy']}: {r_['turer']:2d}/{r_['turer_tot']} "
              f"Ö utan Solberget {len(r_['o_turer_utan_solberget']):2d}  Ö efter pulsen ≤ {r_['o_max_efter_pulsen_min']} "
              f"senare i centrum ≤ {r_['o_max_senare_i_centrum_min']}  centrum ≥ {r_['min_centrum_min']}  "
              f"Solberget sämre {r_['solberget_samre_klass_inv']} utan {r_['solberget_utan_hallplats_inv']}")
    pd.concat(planer).drop(columns=['monster']).to_csv(P / 'b4_omlopp_scenarier.csv', index=False)
    pd.concat(tack).round({'x': 1, 'y': 1, 'bef': 5}).to_csv(P / 'b4_tackning_ua.csv.gz', index=False)
    gpd.GeoDataFrame(geo, crs=C.CRS_METRISK).to_file(P / 'b4_ua.gpkg', layer='ua', driver='GPKG')
    with open(P / 'b4_ua.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=float)


if __name__ == '__main__':
    main()
