# -*- coding: utf-8 -*-
"""B4 – Omloppsplan (fordonsomlopp) för stadslinjerna och verifiering av utredningsalternativ mot den.

GTFS saknar block_id, så omloppen härleds ur tidtabellen för typvardagen:
  * Norm (beställaren 2026-10-14): föraren byter linje vid varje vändning i centrum, i paren Syd ↔ Norr (S ↔ N)
    och Öst ↔ Väst (Ö ↔ V), så långt tidtabellen medger. Ett fordon fortsätter därför sällan på samma linje;
    linje J (timtrafik) kopplas där det passar. Byte inom paret får ske med kort uppehåll (≥ GENOMGANG_MIN);
    regleringen tas då vid nästa byte i varvet.
  * Alla stadslinjeturer börjar och slutar i Centrum, Nygatan. Turerna kedjas till omlopp med minsta möjliga
    antal fordon (minimikostnadstilldelning, scipy linear_sum_assignment). Ett fordon kan ta en tur som avgår
    tidigast MIN_VANDTID efter fordonets ankomst. Bland lösningar med minsta antal fordon väljs kortast
    omloppstid (summa över fordonen av tiden från första avgång till sista ankomst, dvs. fordonstimmar) och så
    långt möjligt byte enligt normparen. Fordonsbehovet blir därmed det minsta som tidtabellen kräver. Uppehåll
    i centrum ≤ 60 min redovisas som vändtid (reglering), längre uppehåll som uppställning.
  * Dagens minsta vändtid i tidtabellen är 1 min (bl.a. linje J 14:19 → 14:20); med 2 min krävs ett sjätte fordon.
    Kravet för utredningsalternativen sätts därför till samma nivå som i dag: vändtid ≥ 1 min.
  * Robusthet: varje varv (två på varandra följande turer) ska ha minst REKOMMENDERAD_VANDTID reglering vid något
    av bytena. Antalet varv utan sådan reglering redovisas; ett UA är robust om det inte blir fler än i dag.
Verifiering av ett UA (ramen 'inga fler bussar')
  * UA:ts körtidsförändring läggs på berörda turer (ankomsten till centrum senareläggs, avgångstiderna –
    pulsen i centrum – ligger fast). Omloppen byggs om. UA:t ryms om antalet fordon inte ökar och
    omloppstiden (fordonstimmar) inte ökar mer än OMLOPPSTID_TOL.
  * Ryms inte alla turer prövas turerna en i taget i tidsordning; redovisas hur många som ryms.
  * Robusthet redovisas som antal vändningar under REKOMMENDERAD_VANDTID och total regleringstid.
  * Genomgående linje V–Ö (V och Ö sammanslagna, beställaren 2026-10-15): dagens omlopp ligger fast, så att
    varje V-tur fortsätter som den Ö-tur som samma buss kör i dag (plan_fast). Bussen fortsätter direkt som Ö
    efter GENOMGANG_MIN; Ö flyttas så att den startar när V har kommit tillbaka (ingen gräns efter pulsen,
    MAX_SKIFT_PARTNER = None). Det enda kravet är att hela varvet V + Ö ryms inom 55 min, dvs. minst
    MARGINAL_VARV = 5 min i centrum (genomgången V → Ö plus uppehållet före bussens nästa avgång), helst inom
    50 min (MARGINAL_VARV_ONSKAD = 10 min), se varv_vo och genomgaende_ryms. Varv som redan i dag har mindre
    marginal (V 07:50 + Ö:s skoltur 08:20, 4 min) godtas oförändrade.
Utdata: data/processed/b4_omlopp_idag.csv, b4_omlopp_nyckeltal.json, output/kartor/b4_1_omlopp_idag.png
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402
from scipy.optimize import linear_sum_assignment  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402

MIN_VANDTID = 1.0              # min – dagens lägsta vändtid i tidtabellen (krav)
GENOMGANG_MIN = 0.5            # min – kortaste uppehåll vid byte inom normparet (bussen fortsätter som partnerlinjen)
NORMPAR = (('S', 'N'), ('N', 'S'), ('Ö', 'V'), ('V', 'Ö'))   # föraren byter Syd ↔ Norr och Öst ↔ Väst
REKOMMENDERAD_VANDTID = 3.0    # min – robusthetsnivå (redovisas, inget krav)
DEPA_GRANS = 60.0              # min – längre uppehåll redovisas som uppställning i stället för vändtid
SAMMA_LINJE_STRAFF = 8.0       # min – fordonet fortsätter på samma linje (undviks enligt normen; gäller ej linje J)
ANNAT_BYTE_STRAFF = 2.0        # min – byte till en linje utanför normparet
REFERENS_BONUS = 0.3           # min – vid lika väntan behålls dagens koppling (stabila omlopp före/efter)
OMLOPPSTID_TOL = 10.0          # min/dag – tillåten ökning av omloppstiden (≈ 0,2 %; t.ex. att dagens sista tur blir längre)
MAX_SKIFT_PARTNER = None       # genomgående linje: Ö startar när V har kommit tillbaka (ingen gräns, beställaren 2026-10-15)
MARGINAL_VARV = 5.0            # min – genomgående linje V–Ö: minst så mycket i centrum per varv (varvet ≤ 55 min, krav)
MARGINAL_VARV_ONSKAD = 10.0    # min – helst så mycket (varvet ≤ 50 min)
TEXT, TEXT2 = '#1f1f1e', '#52514e'


# ====================================================================== turer
def turer(datum=None):
    """Stadslinjernas turer en typvardag: avgång/ankomst centrum (min efter midnatt), körtid, hållplatsföljd, km."""
    import s01_vagdragning as V
    g = D.gtfs(); t = D.turer_dag(datum, C.STADSLINJER)
    st = g['stop_times'][g['stop_times'].trip_id.isin(t.trip_id)].sort_values(['trip_id', 'seq'])
    geo = V.segmentgeometri()
    xy, _ = V.hallplats_xy()

    def km(m):
        s = 0.0
        for a, b in zip(m[:-1], m[1:]):
            p = geo.get((a, b), np.array([xy[a], xy[b]]) if a in xy and b in xy else np.zeros((2, 2)))
            s += float(np.hypot(*np.diff(p, axis=0).T).sum())
        return s / 1000
    f = st.groupby('trip_id').agg(avg=('t_dep', 'min'), ank=('t_arr', 'max'), forsta=('stop_id', 'first'),
                                  sista=('stop_id', 'last'), monster=('stop_id', tuple))
    f = f.join(t.set_index('trip_id')[['linje']])
    f['kortid'] = f.ank - f.avg
    f['km'] = f.monster.map(km)
    f['n_hpl'] = f.monster.map(len)
    return f.reset_index().sort_values(['avg', 'linje']).reset_index(drop=True)


# ====================================================================== omlopp
def bygg_omlopp(t, min_vand=MIN_VANDTID, par=NORMPAR, genomgang_min=GENOMGANG_MIN, referens=None, **_):
    """Kedjar turer till omlopp med minsta antal fordon enligt normen (byte inom par, t.ex. V → Ö, får ske med
    kort uppehåll genomgang_min). referens: mängd (trip_id, trip_id) med dagens kopplingar som behålls vid lika
    väntan. Returnerar kopia med kolumnerna buss, nasta (index), vand_efter (min), genomgang (byte inom paret)."""
    t = t.reset_index(drop=True)
    n = len(t)
    avg, ank, lin = t.avg.to_numpy(), t.ank.to_numpy(), t.linje.to_numpy()
    gen = set(map(tuple, par))
    parlinjer = {a for a, _ in gen}
    ref = referens or set()
    tid = t.trip_id.to_numpy()
    K, OMOJLIG = 1e6, 1e9
    kost = np.full((n, 2 * n), OMOJLIG)
    kost[:, n:] = K                                               # ingen efterföljare = omloppet slutar
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            vant = avg[j] - ank[i]
            krav = genomgang_min if (lin[i], lin[j]) in gen else min_vand
            if vant >= krav - 1e-9:
                if (lin[i], lin[j]) in gen:
                    straff = 0.0                             # byte enligt normen
                elif lin[i] == lin[j]:
                    straff = SAMMA_LINJE_STRAFF if lin[i] in parlinjer else 0.0
                else:
                    straff = ANNAT_BYTE_STRAFF
                if (tid[i], tid[j]) in ref:
                    straff -= REFERENS_BONUS
                kost[i, j] = vant + straff
    r, c = linear_sum_assignment(kost)
    nasta = np.full(n, -1)
    for i, j in zip(r, c):
        if j < n and kost[i, j] < K:
            nasta[i] = j
    har_fore = np.zeros(n, bool); har_fore[nasta[nasta >= 0]] = True
    buss = np.zeros(n, int); nr = 0
    for s in np.argsort(avg):
        if har_fore[s]:
            continue
        nr += 1; k = s
        while k >= 0:
            buss[k] = nr; k = nasta[k]
    # numrera fordonen efter första avgång
    forsta = pd.Series(avg).groupby(buss).min().sort_values()
    om = {b: i + 1 for i, b in enumerate(forsta.index)}
    ut = t.copy()
    ut['buss'] = [om[b] for b in buss]
    ut['nasta'] = nasta
    ut['vand_efter'] = [avg[j] - ank[i] if j >= 0 else np.nan for i, j in enumerate(nasta)]
    ut['genomgang'] = [bool(j >= 0 and (lin[i], lin[j]) in gen and avg[j] - ank[i] <= DEPA_GRANS)
                       for i, j in enumerate(nasta)]
    return ut


def nyckeltal(o):
    v = o.vand_efter.dropna()
    v_i_trafik = v[v <= DEPA_GRANS]
    vand = o.loc[o.vand_efter.notna() & ~o.genomgang, 'vand_efter']        # vändningar (ej genomgång)
    span = o.groupby('buss').apply(lambda d: d.ank.max() - d.avg.min(), include_groups=False)
    return {'fordon': int(o.buss.nunique()),
            'turer': int(len(o)),
            'korttid_h': round(float(o.kortid.sum() / 60), 2),
            'omloppstid_h': round(float(span.sum() / 60), 2),
            'regleringstid_h': round(float(v_i_trafik.sum() / 60), 2),
            'uppstallning_h': round(float(v[v > DEPA_GRANS].sum() / 60), 2),
            'km': round(float(o.km.sum()), 1),
            'min_vandtid': round(float(v.min()), 1),
            'vandningar_under_rek': int((vand < REKOMMENDERAD_VANDTID - 1e-9).sum()),
            'varv_utan_reglering': varv_utan_reglering(o),
            'varv_vo_under_marginal': int((varv_vo(o).centrum_min < MARGINAL_VARV - 1e-9).sum()),
            'varv_vo_under_onskad': int((varv_vo(o).centrum_min < MARGINAL_VARV_ONSKAD - 1e-9).sum()),
            'min_centrum_vo': round(float(varv_vo(o).centrum_min.min()), 1),
            'byten_enligt_norm': int(o.genomgang.sum()), 'samma_linje': samma_linje(o),
            'genomgangar': int(o.genomgang.sum()),
            'forsta_avg': round(float(o.avg.min()), 1), 'sista_ank': round(float(o.ank.max()), 1)}


def varv_utan_reglering(o):
    """Antal varv (två på varandra följande byten i centrum, båda ≤ 60 min) där inget byte har minst
    REKOMMENDERAD_VANDTID reglering."""
    n = 0
    for _, d in o.sort_values('avg').groupby('buss'):
        v = d.vand_efter.to_numpy()
        for a, b in zip(v[:-1], v[1:]):
            if np.isnan(a) or np.isnan(b) or a > DEPA_GRANS or b > DEPA_GRANS:
                continue
            if max(a, b) < REKOMMENDERAD_VANDTID - 1e-9:
                n += 1
    return n


def varv_vo(o, linje='V', partner='Ö'):
    """Varv på linje V–Ö: varje V-tur och den tur som bussen fortsätter med. Tid i centrum = uppehållet efter
    V-turen (genomgång till Ö) + uppehållet efter Ö-turen till bussens nästa avgång. Slutar bussen eller ställs
    upp (> DEPA_GRANS) räknas den delen som obegränsad. Fortsätter bussen med en annan linje än Ö är varvet bara
    V-turen och tiden i centrum uppehållet efter den."""
    p = o.reset_index(drop=True)
    lin, nx, v = p.linje.to_numpy(), p.nasta.to_numpy(), p.vand_efter.to_numpy()
    ut = []
    for i in np.where(lin == linje)[0]:
        j = nx[i]
        if j < 0 or v[i] > DEPA_GRANS:
            ut.append((p.trip_id.iat[i], p.avg.iat[i], p.kortid.iat[i], None, None, np.nan, np.inf))
            continue
        c = v[i]
        if lin[j] == partner:
            c += v[j] if (nx[j] >= 0 and v[j] <= DEPA_GRANS) else np.inf
        ut.append((p.trip_id.iat[i], p.avg.iat[i], p.kortid.iat[i], p.trip_id.iat[j], lin[j], p.kortid.iat[j], c))
    return pd.DataFrame(ut, columns=['trip_id', 'avg', 'kortid', 'foljer', 'foljer_linje', 'foljer_kortid',
                                     'centrum_min'])


def varv_ok(o, idag, marginal=MARGINAL_VARV):
    """Varje varv V–Ö har minst marginal min i centrum, eller (varv som redan i dag har mindre) minst som i dag."""
    a = varv_vo(o).set_index('trip_id').centrum_min
    b = varv_vo(idag).set_index('trip_id').centrum_min.reindex(a.index)
    return bool((a >= np.minimum(marginal, b) - 1e-9).all())


def samma_linje(o):
    """Antal kopplingar (≤ 60 min) där fordonet fortsätter på samma linje (linje J undantagen)."""
    lin = o.linje.to_numpy(); n = 0
    for i, j in enumerate(o.nasta):
        if j >= 0 and lin[i] == lin[j] and lin[i] != 'J' and o.vand_efter.iat[i] <= DEPA_GRANS:
            n += 1
    return n


def fordon_i_trafik(o, steg=1.0):
    """Antal fordon i trafik (kör eller väntar ≤ DEPA_GRANS) per minut."""
    tid = np.arange(np.floor(o.avg.min()) - 10, np.ceil(o.ank.max()) + 10, steg)
    n = np.zeros(len(tid))
    for r in o.itertuples():
        slut = r.ank + (r.vand_efter if (not np.isnan(r.vand_efter) and r.vand_efter <= DEPA_GRANS) else 0.0)
        n += (tid >= r.avg) & (tid < slut)
    return tid, n


# ====================================================================== verifiering
def med_andring(t, delta, skift=None):
    """delta: {trip_id: min} läggs på turens ankomst (avgången ligger fast). skift: {trip_id: min} – turen avgår
    (och ankommer) så mycket senare än i dag (partnerlinjen vid genomgående linje)."""
    t = t.copy()
    t['delta'] = t.trip_id.map(delta).fillna(0.0).astype(float)
    t['skift'] = t.trip_id.map(skift or {}).fillna(0.0).astype(float)
    t['avg'] = t.avg + t.skift
    t['ank'] = t.ank + t.skift + t.delta
    t['kortid'] = t.ank - t.avg
    return t


def ram(t):
    """Ramen från dagens omlopp: antal fordon, omloppstid och antal varv utan reglering (robusthet)."""
    nt = nyckeltal(bygg_omlopp(t))
    return {'fordon': nt['fordon'], 'omloppstid_h': nt['omloppstid_h'], 'varv_utan_reglering': nt['varv_utan_reglering']}


def kopplingar(plan):
    """Dagens kopplingar (trip_id, nästa trip_id) – referens så att omloppen efter en ändring liknar dagens."""
    tid = plan.trip_id.to_numpy()
    return {(tid[i], tid[j]) for i, j in enumerate(plan.nasta) if j >= 0}


def inom_ram(nt, r, robust=False):
    ok = nt['fordon'] <= r['fordon'] and nt['omloppstid_h'] <= r['omloppstid_h'] + OMLOPPSTID_TOL / 60 + 1e-9
    if robust:
        ok = ok and nt['varv_utan_reglering'] <= r.get('varv_utan_reglering', 10 ** 6)
    return ok


def ar_robust(nt, r):
    return nt['varv_utan_reglering'] <= r.get('varv_utan_reglering', 10 ** 6)


def plan_fast(plan0, tt):
    """Dagens omlopp (samma kedjor, plan0 från bygg_omlopp(t)) med ändrade tider tt (med_andring(t, …))."""
    assert (plan0.trip_id.to_numpy() == tt.trip_id.to_numpy()).all()
    p = plan0.copy()
    for c in ('avg', 'ank', 'kortid', 'km', 'delta', 'skift'):
        if c in tt:
            p[c] = tt[c].to_numpy()
    avg, ank, nx = p.avg.to_numpy(), p.ank.to_numpy(), p.nasta.to_numpy()
    p['vand_efter'] = [avg[j] - ank[i] if j >= 0 else np.nan for i, j in enumerate(nx)]
    return p


def verifiera(t, delta, r, km_delta=None, skift=None, fast=None, **kw):
    """Bygger omlopp med UA:ts körtider. Returnerar (plan, nyckeltal, ryms inom ramen).
    fast: dagens plan – genomgående linje V–Ö med dagens kedjor; ryms = kravet på tid i centrum per varv."""
    tt = med_andring(t, delta, skift)
    if km_delta:
        tt['km'] = tt.km + tt.trip_id.map(km_delta).fillna(0.0)
    if fast is not None:
        plan = plan_fast(fast, tt)
        nt = nyckeltal(plan)
        return plan, nt, bool(nt['fordon'] <= r['fordon'] and np.nanmin(plan.vand_efter) >= GENOMGANG_MIN - 1e-9
                              and varv_ok(plan, fast))
    plan = bygg_omlopp(tt, **kw)
    nt = nyckeltal(plan)
    return plan, nt, inom_ram(nt, r)


def turer_som_ryms(t, kandidater, d, r, robust=False, bas=None, varv=None, **kw):
    """Prövar turerna en i taget (tidsordning) – behåller ändringen om UA:t fortfarande ryms i ramen
    (robust=True: och inte ger fler varv utan reglering än i dag; varv = dagens plan: och varje varv V + Ö har
    minst MARGINAL_VARV min i centrum). bas: andra åtgärders tillägg {trip_id: min}."""
    valda = []; bas = bas or {}
    for tid in t[t.trip_id.isin(kandidater)].sort_values('avg').trip_id:
        prov = dict(bas)
        for k in valda + [tid]:
            prov[k] = prov.get(k, 0.0) + d
        p = bygg_omlopp(med_andring(t, prov), **kw)
        if inom_ram(nyckeltal(p), r, robust) and (varv is None or varv_ok(p, varv)):
            valda.append(tid)
    return valda


def genomgaende_ryms(t, kandidater, d, plan0, partner='Ö', max_skift=MAX_SKIFT_PARTNER, bas=None,
                     marginal=MARGINAL_VARV, sol=None, sol_over=None, detalj=False, linje='V'):
    """Genomgående linje V–Ö med dagens omlopp (plan0 = bygg_omlopp(t)): V-turen får UA:ts tillägg d om varvet
    (V-turen + Ö-turen som bussen fortsätter med) fortfarande har minst marginal min i centrum. Ö startar då
    direkt efter V (GENOMGANG_MIN); max_skift (None = ingen gräns) begränsar hur sent efter pulsen. bas: andra
    ändringar {trip_id: min} (t.ex. kortare körtid för Ö). Varven är oberoende av varandra, så turerna prövas
    var för sig. sol: {trip_id: −min} – en hållplats (Solberget) kan dras in på enskilda Ö-turer: på Ö-turen
    efter en ändrad V-tur om varvet annars inte ryms (eller, om sol_over anges, om Ö startar mer än sol_over min
    efter pulsen). linje/partner: normparet (V/Ö, N/S, …). Returnerar (valda turer, {trip_id: skift}) och med detalj=True även Ö-turerna utan hållplatsen."""
    bas, sol = dict(bas or {}), dict(sol or {})
    p0 = plan0.reset_index(drop=True)
    tid, lin, nx = p0.trip_id.to_numpy(), p0.linje.to_numpy(), p0.nasta.to_numpy()
    pos = {k: i for i, k in enumerate(tid)}
    t0 = plan_fast(p0, med_andring(t, bas))
    idag = varv_vo(plan_fast(p0, med_andring(t, {})), linje, partner).set_index('trip_id').centrum_min
    valda, skift, utan = [], {}, []
    for k in t[t.trip_id.isin(kandidater)].sort_values('avg').trip_id:
        i = pos[k]; j = nx[i]
        s_, behov = {}, 0.0
        genom = j >= 0 and lin[j] == partner and t0.vand_efter.iat[i] <= DEPA_GRANS
        if genom:
            behov = t0.ank.iat[i] + d + GENOMGANG_MIN - t0.avg.iat[j]
            if max_skift is not None and behov > max_skift + 1e-9:
                continue
            if behov > 0:
                s_ = {tid[j]: round(behov, 2)}
        if genom and tid[j] in sol:
            val = [True] if sol_over is not None and behov > sol_over + 1e-9 else [False, True]
        else:
            val = [False]
        for indrag in val:
            dd = {**bas, k: bas.get(k, 0.0) + d}
            if indrag:
                dd[tid[j]] = dd.get(tid[j], 0.0) + sol[tid[j]]
            p = plan_fast(p0, med_andring(t, dd, s_))
            c = varv_vo(p, linje, partner).set_index('trip_id').centrum_min
            if c[k] >= min(marginal, idag[k]) - 1e-9 and np.nanmin(p.vand_efter) >= GENOMGANG_MIN - 1e-9:
                valda.append(k); skift.update(s_)
                if indrag:
                    utan.append(tid[j])
                break
    return (valda, skift, utan) if detalj else (valda, skift)


# ====================================================================== figurer
def hm(m):
    m = int(round(m)); return f'{m // 60:02d}:{m % 60:02d}'


def rita_omlopp(ax, plan, titel=None, andrade=(), t0=6.5 * 60, t1=21.5 * 60, etikett_vand=True):
    """Gantt: ett band per fordon, staplar per tur i linjefärg. Förlängd del av ändrade turer skrafferas;
    vändningar under rekommenderad nivå markeras (röd < 1 min, orange < 3 min)."""
    andrade = set(andrade)
    nb = plan.buss.max()
    for r in plan.itertuples():
        y = nb - r.buss
        f = C.FARG_LINJE[r.linje]
        d = getattr(r, 'delta', 0.0) if r.trip_id in andrade else 0.0
        ax.add_patch(Rectangle((r.avg, y - 0.34), r.kortid - d, 0.68, facecolor=f, edgecolor='white', lw=0.5, zorder=3))
        if d > 0:
            ax.add_patch(Rectangle((r.ank - d, y - 0.34), d, 0.68, facecolor='white', edgecolor=f, hatch='//////',
                                   lw=0.6, zorder=3))
        elif d < 0:                                                # kortare körtid: tunn markering vid den nya ankomsten
            ax.plot([r.ank, r.ank], [y - 0.34, y + 0.34], color='#1f1f1e', lw=0.9, zorder=4)
        sk = getattr(r, 'skift', 0.0)
        if sk > 0:                                                 # avgår senare än i dag
            ax.add_patch(Rectangle((r.avg - sk, y - 0.34), sk, 0.68, facecolor='none', edgecolor='#1f1f1e', ls=(0, (1, 1)),
                                   lw=0.6, zorder=3))
        if r.kortid >= 14:
            ax.text(r.avg + (r.kortid - max(d, 0)) / 2, y, r.linje, ha='center', va='center', fontsize=6.3,
                    color='white', fontweight='bold', zorder=4)
        if etikett_vand and not np.isnan(r.vand_efter) and r.vand_efter < REKOMMENDERAD_VANDTID - 1e-9:
            farg = '#c0392b' if r.vand_efter < MIN_VANDTID - 1e-9 else '#e8590c'
            if getattr(r, 'genomgang', False):
                farg = '#1c5cab'
            ax.plot([r.ank, r.ank + r.vand_efter], [y + 0.43, y + 0.43], color=farg, lw=2.2, solid_capstyle='butt', zorder=5)
            ax.plot([r.ank + r.vand_efter / 2], [y + 0.43], marker='v', color=farg, ms=3.2, zorder=5)
    ax.set_ylim(-0.7, nb - 0.3)
    ax.set_yticks(range(nb)); ax.set_yticklabels([f'Buss {nb - i}' for i in range(nb)], fontsize=7.5)
    ax.set_xlim(t0, t1)
    xt = np.arange(np.ceil(t0 / 60) * 60, t1 + 1, 60)
    ax.set_xticks(xt); ax.set_xticklabels([hm(x) for x in xt], fontsize=7)
    ax.set_xticks(np.arange(np.ceil(t0 / 30) * 30, t1 + 1, 30), minor=True)
    ax.grid(axis='x', which='major', color='#dcdad3', lw=0.6, zorder=0)
    ax.grid(axis='x', which='minor', color='#efeee9', lw=0.4, zorder=0)
    ax.tick_params(axis='y', length=0)
    for s in ['top', 'right', 'left']:
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color('#b9b6ad')
    if titel:
        ax.set_title(titel, loc='left', fontsize=9.5, fontweight='bold', pad=4)


def omlopp_forklaring(fig, extra=(), y=0.005, ncol=None):
    h = [Patch(facecolor=C.FARG_LINJE[l], label=f'Linje {l}') for l in C.STADSLINJER]
    h += list(extra)
    h += [Line2D([], [], color='#e8590c', lw=2.2, label=f'Vändtid < {REKOMMENDERAD_VANDTID:g} min'),
          Line2D([], [], color='#c0392b', lw=2.2, label=f'Vändtid < {MIN_VANDTID:g} min (ryms ej)')]
    lg = fig.legend(handles=h, loc='lower left', bbox_to_anchor=(0.01, y), ncol=ncol or len(h), fontsize=7,
                    frameon=False, handlelength=1.6, columnspacing=1.2)
    return lg


def fig_idag(t, plan):
    nt = nyckeltal(plan)
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(12.4, 5.6), gridspec_kw={'height_ratios': [3.2, 1.0], 'hspace': 0.32})
    rita_omlopp(ax, plan, titel=f'Härledd omloppsplan, typvardag {D.typvardag():%Y-%m-%d} – {nt["fordon"]} fordon')
    tid, n = fordon_i_trafik(plan)
    ax2.fill_between(tid, n, step='post', color='#9aa7b4', alpha=0.55, lw=0)
    ax2.step(tid, n, where='post', color='#3d4a57', lw=0.9)
    ax2.set_xlim(ax.get_xlim()); ax2.set_xticks(ax.get_xticks()); ax2.set_xticklabels(ax.get_xticklabels())
    ax2.set_ylim(0, nt['fordon'] + 0.6); ax2.set_yticks(range(0, nt['fordon'] + 1))
    ax2.tick_params(labelsize=7); ax2.grid(axis='both', color='#e6e4de', lw=0.5)
    for s in ['top', 'right']:
        ax2.spines[s].set_visible(False)
    ax2.set_title('Fordon i trafik (kör eller vänder i centrum)', loc='left', fontsize=8.5, fontweight='bold', pad=3)
    txt = (f"Turer {nt['turer']}   ·   körtid {nt['korttid_h']:.1f} h   ·   omloppstid {nt['omloppstid_h']:.1f} h "
           f"(därav vändtid i centrum {nt['regleringstid_h']:.1f} h, uppställning {nt['uppstallning_h']:.1f} h)   ·   "
           f"{nt['km']:.0f} km   ·   minsta vändtid {nt['min_vandtid']:g} min")
    fig.text(0.01, 0.955, txt.replace('.', ','), fontsize=7.5, color=TEXT2)
    omlopp_forklaring(fig, y=-0.035)
    fig.subplots_adjust(left=0.06, right=0.99, top=0.9, bottom=0.08)
    ut = C.KARTOR / 'b4_1_omlopp_idag.png'
    fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


# ====================================================================== huvudflöde
def linjeprofil(t, plan):
    """Körtid och vändtid per linje i rusning (06–09, 15–18) – underlag för UA och sammanslagning."""
    r = plan[plan.avg.between(6 * 60, 18 * 60)]
    ut = {}
    for ln, d in r.groupby('linje'):
        d = d.sort_values('avg')
        intervall = d.avg.diff().median()
        ut[ln] = {'turer_dag': int((t.linje == ln).sum()), 'kortid_median': float(d.kortid.median()),
                  'kortid_max': float(d.kortid.max()), 'turintervall_rusning': float(intervall),
                  'vandtid_median': float(d.vand_efter[d.vand_efter <= DEPA_GRANS].median()),
                  'vandtid_min': float(d.vand_efter.min()),
                  'km_tur': round(float(d.km.median()), 2)}
    return ut


def main():
    P = C.PROCESSED
    t = turer()
    plan = bygg_omlopp(t)
    kansl = {f'{L:g}': int(bygg_omlopp(t, min_vand=L).buss.nunique()) for L in (0.0, 1.0, 2.0, 3.0)}
    plan.drop(columns=['monster']).assign(avg_hm=plan.avg.map(hm), ank_hm=plan.ank.map(hm)).to_csv(
        P / 'b4_omlopp_idag.csv', index=False)
    res = {'typvardag': str(D.typvardag()), 'idag': nyckeltal(plan), 'fordon_vid_minsta_vandtid': kansl,
           'linjer': linjeprofil(t, plan),
           'genomgangar_idag': [f"{plan.linje[i]}→{plan.linje[j]} {hm(plan.ank[i])}–{hm(plan.avg[j])}"
                                for i, j in enumerate(plan.nasta) if j >= 0 and plan.linje[i] != plan.linje[j]
                                and plan.vand_efter[i] <= DEPA_GRANS]}
    with open(P / 'b4_omlopp_nyckeltal.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print(fig_idag(t, plan))


if __name__ == '__main__':
    main()
