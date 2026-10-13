# -*- coding: utf-8 -*-
"""A1 – Granskning och korrigering av OD-matrisen (FM och EM) för Mariehamns stadstrafik.

Diagnos
  D1  Var registreras påstigningar vid ändhållplatsen? (stadslinjer vs landsbygdslinjer som kontrollgrupp)
  D2  Påstigningar på de första hållplatserna efter ändhållplatsen (startsegmentet) – jämfört med
      landsbygdslinjerna från Mariehamn, Bussplan (kontrollgrupp med fungerande registrering)
  D3  Linje Ö saknas i filtret ('E' i stället för 'Ö')
  D4  Par av hållplatsområden som bara förbinds med gång ingår som "bussresor" i gravitationsmodellen
Korrigering (stegvis, samma gravitationsmodell och parametrar som den ursprungliga matrisen)
  S1  Återskapad matris med ursprunglig metod (validering mot levererad matris)
  S2  + linje Ö inkluderad
  S3  + gångpar exkluderade (resan kräver ingen buss)
  S4  + centrumöverskottet omfördelat till startsegmentets hållplatser  => korrigerad matris
Utdata: data/processed/a1_*.csv/json, output/kartor/a1_*.png
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402

LANDSBYGD_TERMINAL = 'Mariehamn, Bussplan'
STARTSEGMENT_HPL = [2, 3, 4]      # antal hållplatser efter terminalen (känslighet); basfall = 3
BAS_K = 3
CENTRALT_M = 800                  # startsegmentets hållplatser ska ligga i centrala Mariehamn


# ====================================================================== hjälpfunktioner
def vardagsurval(linjer, produktfilter=True):
    r = D.radata()
    m = r.linje.isin(linjer) & r.vardag
    if produktfilter:
        m &= r['Product Type'].astype(str).isin(D.produktfilter())
    s = r[m].copy()
    s['period'] = s.tid_min.map(D.period)
    om = D.hallplatsomraden()
    s['omrade'] = s['Stop ID'].map(om['omrade']).fillna(s['Stop Name'])
    return s


def gtfs_max_seq():
    st = D.gtfs()['stop_times']
    return st.groupby('trip_id').seq.max()


def zonkoordinater():
    om = D.hallplatsomraden().drop_duplicates('omrade').set_index('omrade')
    x, y = D.till_metrisk(om.lon.values, om.lat.values)
    return pd.DataFrame({'x': x, 'y': y, 'lat': om.lat.values, 'lon': om.lon.values}, index=om.index)


# ====================================================================== D1 registreringsposition
def d1_registrering():
    s = vardagsurval(C.STADSLINJER + C.LANDSBYGDSLINJER, produktfilter=False)
    s['gmax'] = s['Trip ID'].map(gtfs_max_seq())
    rader = []
    for ln, d in s.groupby('linje'):
        term = C.CENTRUM if ln in C.STADSLINJER else LANDSBYGD_TERMINAL
        t = d[d.omrade == term]
        if t.P.sum() == 0:
            continue
        forsta = t.loc[t['Stop Sequence'] == 1, 'P'].sum()
        sista = t.loc[(t['Stop Sequence'] == t.gmax), 'P'].sum()
        # turer utan GTFS-matchning: sista = högsta registrerade sekvens på turen och hpl = terminalen
        omatch = t[t.gmax.isna()]
        if len(omatch):
            mx = d.groupby('Trip ID')['Stop Sequence'].transform('max').loc[omatch.index]
            sista += omatch.loc[(omatch['Stop Sequence'] == mx) & (omatch['Stop Sequence'] > 1), 'P'].sum()
        rader.append({'linje': ln, 'grupp': 'Stadslinje' if ln in C.STADSLINJER else 'Landsbygdslinje',
                      'terminal': term, 'pastigande_terminal': t.P.sum(),
                      'andel_forsta_hpl': forsta / t.P.sum(), 'andel_sista_hpl': sista / t.P.sum(),
                      'andel_linjens_pastigande_vid_terminal': t.P.sum() / d.P.sum()})
    return pd.DataFrame(rader)


# ====================================================================== D2 startsegment
def _avstand_till(zon):
    zk = zonkoordinater(); p = zk.loc[zon]
    return lambda z: math.hypot(zk.loc[z, 'x'] - p.x, zk.loc[z, 'y'] - p.y) if z in zk.index else 1e9


def _utgaende_turer(s, terminal):
    """Turer (Trip ID) som någon dag registrerat påstigning på sekvens 1 vid terminalen (= utgående turer)."""
    return set(s.loc[(s['Stop Sequence'] == 1) & (s.omrade == terminal), 'Trip ID'])


def d2_benchmark():
    """Kvot R = påstigande på de k första hållplatserna efter terminalen (inom centrala Mariehamn)
    / påstigande vid terminalen. Landsbygdslinjer från Mariehamn, Bussplan – där registreringen fungerar."""
    s = vardagsurval(C.LANDSBYGDSLINJER, produktfilter=False)
    L = s[s['Trip ID'].isin(_utgaende_turer(s, LANDSBYGD_TERMINAL))].copy()
    L['d'] = L.omrade.map(_avstand_till(LANDSBYGD_TERMINAL))
    ut = []
    for k in STARTSEGMENT_HPL:
        for per in ['FM', 'EM', 'dygn']:
            d = L if per == 'dygn' else L[L.period == per]
            term = d.loc[d['Stop Sequence'] == 1, 'P'].sum()
            seg = d.loc[d['Stop Sequence'].between(2, k + 1) & (d.d <= CENTRALT_M), 'P'].sum()
            ut.append({'k_hpl': k, 'period': per, 'terminal': term, 'startsegment': seg, 'R': seg / term})
    return pd.DataFrame(ut)


def startsegment_stad(s, k):
    """Centrala hållplatsområden (≠ centrum, ≤ CENTRALT_M) på position 2..k+1 efter centrum, per stadslinje.
    Positionerna hämtas både ur GTFS (turer som startar i centrum) och ur valideringsdatan (äldre tidtabell)."""
    g = D.gtfs(); om = D.hallplatsomraden(); dC = _avstand_till(C.CENTRUM)
    t = D.turer_dag(None, C.STADSLINJER)
    st = g['stop_times'][g['stop_times'].trip_id.isin(t.trip_id)].merge(t[['trip_id', 'linje']], on='trip_id')
    st['omrade'] = st.stop_id.map(om['omrade'])
    fran_c = set(st.loc[(st.seq == 1) & (st.omrade == C.CENTRUM), 'trip_id'])
    st = st[st.trip_id.isin(fran_c) & st.seq.between(2, k + 1)]
    obs = s[s['Stop Sequence'].between(2, k + 1)]
    ut = {}
    for ln in C.STADSLINJER:
        z = set(st.loc[st.linje == ln, 'omrade']) | set(obs.loc[obs.linje == ln, 'omrade'])
        z = sorted(x for x in z if x != C.CENTRUM and dC(x) <= CENTRALT_M)
        if z:
            ut[ln] = z
    return ut


def stad_startsegment_observerat(s, k):
    seg = startsegment_stad(s, k)
    rader = []
    for ln, d in s.groupby('linje'):
        for per in ['FM', 'EM', 'dygn']:
            dd = d if per == 'dygn' else d[d.period == per]
            bc = dd.loc[dd.omrade == C.CENTRUM, 'P'].sum()
            bs = dd.loc[dd.omrade.isin(seg.get(ln, [])) & dd['Stop Sequence'].between(2, k + 1), 'P'].sum()
            rader.append({'linje': ln, 'period': per, 'k_hpl': k, 'B_centrum': bc, 'B_start': bs,
                          'kvot_obs': bs / bc if bc else np.nan, 'startsegment': ', '.join(seg.get(ln, []))})
    return pd.DataFrame(rader), seg


# ====================================================================== O/D och korrigering
def o_per_omrade(s, per):
    d = s[s.period == per]
    return d.groupby('omrade').P.sum() / (C.ANTAL_VARDAGAR * C.TIMMAR_PER_PERIOD)


def centrumkorrigering(s, R, T):
    """Omfördelar centrumöverskottet per linje och period till startsegmentets hållplatsområden.
    Överskott E = max(0, B_C − (B_C + B_S)/(1 + R)). Vikter: alla bussars påstigande i området (samma period), exkl. påstigning på turens första hållplats."""
    obs, seg = stad_startsegment_observerat(s, T)
    alla = vardagsurval(C.STADSLINJER + C.LANDSBYGDSLINJER, produktfilter=False)
    alla = alla[(alla['Stop Sequence'] > 1) & (alla.omrade != C.CENTRUM)]   # utan terminaleffekt (turens första hpl)
    flytt = []
    for per in ['FM', 'EM']:
        Rp = float(R.loc[(R.k_hpl == T) & (R.period == per), 'R'].iat[0])
        vikt_all = alla[alla.period == per].groupby('omrade').P.sum()
        for r in obs[obs.period == per].itertuples(index=False):
            sann = (r.B_centrum + r.B_start) / (1 + Rp)
            E = max(0.0, r.B_centrum - sann)
            if E <= 0 or r.linje not in seg:
                continue
            mott = seg[r.linje]
            w = np.array([max(float(vikt_all.get(z, 0.0)), 1.0) for z in mott])
            for z, a in zip(mott, E * w / w.sum()):
                flytt.append({'period': per, 'linje': r.linje, 'till_omrade': z, 'pastigande': a,
                              'resor_h': a / (C.ANTAL_VARDAGAR * C.TIMMAR_PER_PERIOD)})
    return pd.DataFrame(flytt), obs, seg


# ====================================================================== restidsnät
def restidsnat(linjer, zoner):
    """Kortaste restid (min) mellan hållplatsområden i stadslinjenätet: schemalagd åktid (GTFS, typvardag),
    bytesstraff vid byte (ej vid första påstigning) och gång ≤ 400 m mellan områden.
    Returnerar (c, endast_gang) där endast_gang anger par vars snabbaste väg inte använder buss."""
    g = D.gtfs(); om = D.hallplatsomraden(); zk = zonkoordinater().loc[zoner]
    t = D.turer_dag(None, linjer)
    st = g['stop_times'][g['stop_times'].trip_id.isin(t.trip_id)].copy()
    st['omrade'] = st.stop_id.map(om['omrade'])
    st = st.sort_values(['trip_id', 'seq'])
    monster = st.groupby('trip_id').omrade.apply(tuple)
    # åktid per mönster och position: median över turer med samma mönster
    st['nasta_arr'] = st.groupby('trip_id').t_arr.shift(-1)
    st['akt'] = st.nasta_arr - st.t_dep
    st['pos'] = st.groupby('trip_id').cumcount()
    st['monster'] = st.trip_id.map(monster)
    akt = st.groupby(['monster', 'pos']).akt.median()

    zi = {z: i for i, z in enumerate(zoner)}; nZ = len(zoner)
    # noder: lager0-zoner [0,nZ), lager1-zoner [nZ,2nZ), fordonsnoder därefter
    rad, kol, vikt = [], [], []
    def kant(a, b, w):
        rad.append(a); kol.append(b); vikt.append(max(w, 1e-6))
    nod = 2 * nZ
    for m in monster.unique():
        ids = []
        for k, z in enumerate(m):
            ids.append(nod); nod += 1
        for k, z in enumerate(m):
            if z not in zi:
                continue
            if k < len(m) - 1:                       # påstigning (ej vid slutstation)
                kant(zi[z], ids[k], 0.0)             # första påstigning: ingen bytesstraff
                kant(nZ + zi[z], ids[k], C.BYTESSTRAFF_MIN)
            if k > 0:
                kant(ids[k], nZ + zi[z], 0.0)        # avstigning -> lager 1
        for k in range(len(m) - 1):
            kant(ids[k], ids[k + 1], float(akt.get((m, k), 1.0)))
    xy = zk[['x', 'y']].to_numpy()
    dd = np.hypot(xy[:, None, 0] - xy[None, :, 0], xy[:, None, 1] - xy[None, :, 1])
    for i in range(nZ):
        for j in range(nZ):
            if i != j and dd[i, j] <= C.GANG_MAX_M:
                w = dd[i, j] / C.GANG_HAST_M_PER_MIN
                kant(i, j, w); kant(nZ + i, nZ + j, w)
    G = csr_matrix((vikt, (rad, kol)), shape=(nod, nod))
    dist = dijkstra(G, directed=True, indices=list(range(nZ)))
    gang, buss = dist[:, :nZ], dist[:, nZ:2 * nZ]
    c = np.minimum(gang, buss)
    endast_gang = gang <= buss
    np.fill_diagonal(c, 0.0)
    return (pd.DataFrame(c, index=zoner, columns=zoner),
            pd.DataFrame(endast_gang, index=zoner, columns=zoner))


# ====================================================================== gravitationsmodell
def gravitation(O, Dm, c, tillaten=None, beta=C.BETA, iter_=C.FURNESS_ITERATIONER):
    """Dubbelt begränsad modell T_ij = a_i b_j O_i D_j f(c_ij), f = exp(-β c). Diagonal = 0."""
    z = list(c.index)
    O = O.reindex(z).fillna(0).to_numpy(); Dv = Dm.reindex(z).fillna(0).to_numpy()
    Dv = Dv * O.sum() / Dv.sum()
    f = np.exp(-beta * c.to_numpy())
    np.fill_diagonal(f, 0.0)
    if tillaten is not None:
        f = f * tillaten.to_numpy()
    f[~np.isfinite(f)] = 0.0
    T = np.outer(O, Dv) * f
    for _ in range(iter_):
        rs = T.sum(1); T *= np.divide(O, rs, out=np.zeros_like(O), where=rs > 0)[:, None]
        ks = T.sum(0); T *= np.divide(Dv, ks, out=np.zeros_like(Dv), where=ks > 0)[None, :]
    return pd.DataFrame(T, index=z, columns=z)


def las_levererad(blad):
    raw = pd.read_excel(C.OD_XLSX, sheet_name=blad, header=None)
    hr = next(i for i in range(10) if any(str(v).startswith('Från') for v in raw.iloc[i]))
    nk = next(j for j, v in enumerate(raw.iloc[hr]) if str(v).startswith('Från'))
    # zonrader har löpnummer i kolumnen före namnet; summerings-/kontrollrader saknar det
    rad = [i for i in range(hr + 1, len(raw)) if pd.notna(pd.to_numeric(raw.iat[i, nk - 1], errors='coerce'))]
    namn = {str(raw.iat[i, nk]).strip() for i in rad}
    kol = [j for j in range(nk + 1, raw.shape[1]) if str(raw.iat[hr, j]).strip() in namn]
    M = raw.iloc[rad, kol].apply(pd.to_numeric, errors='coerce').fillna(0.0)
    M.index = [str(raw.iat[i, nk]).strip() for i in rad]; M.columns = [str(raw.iat[hr, j]).strip() for j in kol]
    return M


def nyckeltal(M, endast_gang=None):
    T = M.to_numpy().sum(); Cn = C.CENTRUM
    ut = {'resor_h': T, 'andel_O_centrum': M.loc[Cn].sum() / T, 'andel_D_centrum': M[Cn].sum() / T,
          'andel_resor_via_centrum': (M.loc[Cn].sum() + M[Cn].sum() - M.loc[Cn, Cn]) / T}
    if endast_gang is not None:
        eg = endast_gang.reindex(index=M.index, columns=M.columns).fillna(False).to_numpy()
        ut['andel_gangpar'] = (M.to_numpy() * eg).sum() / T
    return ut


def langt(M, namn='resor_h'):
    L = M.stack().rename(namn).reset_index(); L.columns = ['fran', 'till', namn]
    return L[L[namn] > 1e-9]


# ====================================================================== huvudflöde
def main():
    P = C.PROCESSED
    res = {}
    # ---------------- D1
    d1 = d1_registrering(); d1.to_csv(P / 'a1_d1_registreringsposition.csv', index=False)
    res['D1'] = d1.round(4).to_dict('records')
    # ---------------- D2
    R = d2_benchmark(); R.to_csv(P / 'a1_d2_benchmark_landsbygd.csv', index=False)
    stad = vardagsurval(C.STADSLINJER)                       # inkl. Ö (korrigerat filter)
    obs_rader = []
    for k in STARTSEGMENT_HPL:
        o, _ = stad_startsegment_observerat(stad, k); obs_rader.append(o)
    obs_all = pd.concat(obs_rader); obs_all.to_csv(P / 'a1_d2_startsegment_stad.csv', index=False)
    # ---------------- D3
    orig_urval = vardagsurval(['J', 'N', 'S', 'V', 'E'])
    res['D3'] = {'pastigande_vardag_med_O': float(stad.P.sum()), 'pastigande_vardag_utan_O': float(orig_urval.P.sum()),
                 'andel_saknas': float(1 - orig_urval.P.sum() / stad.P.sum())}
    # ---------------- zoner och restider
    zk = zonkoordinater()
    zoner_utan_O = sorted(set(orig_urval.omrade) | set(D.avgangar_per_hallplats(None, ['J', 'N', 'S', 'V']).stop_id.map(D.hallplatsomraden()['omrade'])))
    zoner_med_O = sorted(set(stad.omrade) | set(D.avgangar_per_hallplats(None, C.STADSLINJER).stop_id.map(D.hallplatsomraden()['omrade'])))
    zoner_utan_O = [z for z in zoner_utan_O if z in zk.index]; zoner_med_O = [z for z in zoner_med_O if z in zk.index]
    c0, g0 = restidsnat(['J', 'N', 'S', 'V'], zoner_utan_O)
    c1, g1 = restidsnat(C.STADSLINJER, zoner_med_O)
    c1.round(2).to_csv(P / 'a1_restider_min.csv')
    # ---------------- O per period
    O = {}
    for per in ['FM', 'EM']:
        O[('utan_O', per)] = o_per_omrade(orig_urval, per)
        O[('med_O', per)] = o_per_omrade(stad, per)
    flytt, obs, seg = centrumkorrigering(stad, R, BAS_K)
    flytt.to_csv(P / 'a1_centrum_omfordelning.csv', index=False)
    O_korr = {}
    for per in ['FM', 'EM']:
        o = O[('med_O', per)].copy()
        f = flytt[flytt.period == per]
        o[C.CENTRUM] -= f.resor_h.sum()
        for z, v in f.groupby('till_omrade').resor_h.sum().items():
            o[z] = o.get(z, 0.0) + v
        O_korr[per] = o
    # ---------------- stegvis gravitationsmodell
    spegel = {'FM': 'EM', 'EM': 'FM'}
    steg = {}
    for per in ['FM', 'EM']:
        lev = las_levererad(f'OD_{per}')
        s1 = gravitation(O[('utan_O', per)], O[('utan_O', spegel[per])], c0)
        s2 = gravitation(O[('med_O', per)], O[('med_O', spegel[per])], c1)
        tillat = ~g1
        s3 = gravitation(O[('med_O', per)], O[('med_O', spegel[per])], c1, tillaten=tillat)
        s4 = gravitation(O_korr[per], O_korr[spegel[per]], c1, tillaten=tillat)
        gem = sorted(set(lev.index) & set(s1.index))
        a, b = lev.loc[gem, gem].to_numpy().ravel(), s1.loc[gem, gem].to_numpy().ravel()
        steg[per] = {'S0 levererad': nyckeltal(lev, g0), 'S1 återskapad': nyckeltal(s1, g0),
                     'S2 + linje Ö': nyckeltal(s2, g1), 'S3 + gångpar exkluderade': nyckeltal(s3, g1),
                     'S4 + centrumkorrigering': nyckeltal(s4, g1)}
        steg[per]['validering'] = {'korrelation_cell': float(np.corrcoef(a, b)[0, 1]),
                                   'max_abs_avvikelse': float(np.abs(a - b).max()),
                                   'medelrestid_lev_min': float((lev.loc[gem, gem].to_numpy() * c0.loc[gem, gem].to_numpy()).sum() / lev.loc[gem, gem].to_numpy().sum())}
        langt(lev).to_csv(P / f'a1_od_{per}_levererad.csv', index=False)
        langt(s4).to_csv(P / f'a1_od_{per}_korrigerad.csv', index=False)
        s4.round(6).to_csv(P / f'a1_od_{per}_korrigerad_matris.csv')
    res['steg'] = steg
    # ---------------- sammanställningar
    bas_R = R[(R.k_hpl == BAS_K)].set_index('period').R.to_dict()
    kansl = {}
    for T in STARTSEGMENT_HPL:
        f, o, _ = centrumkorrigering(stad, R, T)
        bc = stad[(stad.omrade == C.CENTRUM) & stad.period.isin(['FM', 'EM'])].groupby('period').P.sum()
        kansl[T] = {per: float(f[f.period == per].pastigande.sum() / bc[per]) for per in ['FM', 'EM']}
    res['R_bas'] = bas_R
    res['andel_felregistrerade_centrum'] = kansl
    res['startsegment_bas'] = seg
    zon = pd.DataFrame({'omrade': zoner_med_O}).set_index('omrade').join(zk)
    for per in ['FM', 'EM']:
        zon[f'O_{per}_orig'] = O[('utan_O', per)].reindex(zon.index).fillna(0)
        zon[f'O_{per}_medO'] = O[('med_O', per)].reindex(zon.index).fillna(0)
        zon[f'O_{per}_korr'] = O_korr[per].reindex(zon.index).fillna(0)
    zon.to_csv(P / 'a1_zoner_pastigande.csv')
    bb = stad[stad['Product Type'] == 'Bussbyte 2h']
    res['bussbyte_centrum_andel_av_centrum'] = float(bb.loc[bb.omrade == C.CENTRUM, 'P'].sum() / stad.loc[stad.omrade == C.CENTRUM, 'P'].sum())
    with open(P / 'a1_sammanfattning.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: res[k] for k in ['D3', 'R_bas', 'andel_felregistrerade_centrum', 'bussbyte_centrum_andel_av_centrum']}, ensure_ascii=False, indent=1, default=float))
    for per in ['FM', 'EM']:
        print(per); print(pd.DataFrame({k: v for k, v in steg[per].items() if k != 'validering'}).T.round(3).to_string())
        print('  validering:', {k: round(v, 4) for k, v in steg[per]['validering'].items()})


if __name__ == '__main__':
    main()
