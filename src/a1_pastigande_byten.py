# -*- coding: utf-8 -*-
"""Påstigande per hållplats (FM och EM), var resenärerna byter och var skolresorna börjar.

  * Påstigande FM (06–09) och EM (15–18) per hållplatsområde: den tvättade höstdatan (linjerna Norra, Södra,
    Västra, Östra) och sommardatan för Järsö, medel per vardag (data_las.pastigande).
  * Byten:
      - modell: den korrigerade OD-matrisen (A1) utlagd på restidsnätet (b4_natverk, bytesstraff 5 min, gång
        ≤ 400 m). Ett byte räknas där resenären stiger på en annan linje än den hen kom med; resor per timme;
      - biljett: valideringar med biljettypen "Bussbyte 2h" i sommardatan (stadslinjerna, vardagar), som visar var
        bytet görs för den som köper enkelbiljett. Kortresenärers byten syns inte i valideringarna.
  * Skolresor: valideringar med skolkort ("Skolkort läsår 2025-2026/2026-2027", "Glömt skolkort") i sommardatan,
    stadslinjerna, medel per skoldag (vardagar med minst 20 skolkortsvalideringar: 12 maj–5 juni och
    20 aug–14 sep 2026). FM 06–09; EM 12–18, eftersom skoldagen slutar från lunch (Östras skolturer 13:10–15:10).
Utdata: data/processed/a1_pastigande_hallplats.csv, a1_byten_*.csv, a1_skolresor_hallplats.csv,
        output/data/pastigande_byten_skolresor.xlsx och kartorna a1_6–a1_8.
"""
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402
import kartlib as K  # noqa: E402

P = C.PROCESSED
UT = C.ROT / 'output' / 'data'
SKOLKORT = ('Skolkort läsår 2025-2026', 'Skolkort läsår 2026-2027', 'Glömt skolkort')
SKOL_EM = (12, 18)
MIN_SKOLKORT_DAG = 20
zon = pd.read_csv(P / 'a1_zoner_pastigande.csv', index_col=0)
POS = {z: np.array([r.x, r.y]) for z, r in zon.iterrows()}


def _period(tid_min, fm=C.FM, em=C.EM):
    if fm[0] * 60 <= tid_min < fm[1] * 60:
        return 'FM'
    if em[0] * 60 <= tid_min < em[1] * 60:
        return 'EM'
    return None


def pastigande():
    """Påstigande per hållplatsområde och linje, FM och EM (per vardag och per timme)."""
    p = D.pastigande()
    p = p[p.period.notna()]
    t = p.groupby(['omrade', 'period', 'linje']).P.sum().unstack(['period', 'linje']).fillna(0.0)
    ut = pd.DataFrame(index=sorted(set(p.omrade)))
    for per, (a, b) in (('FM', C.FM), ('EM', C.EM)):
        d = p[p.period == per].groupby(['omrade', 'linje']).P.sum().unstack().reindex(columns=C.STADSLINJER).fillna(0)
        ut[f'{per}_vardag'] = d.sum(axis=1)
        ut[f'{per}_per_timme'] = ut[f'{per}_vardag'] / (b - a)
        ut[f'{per}_linjer'] = d.apply(lambda r: ', '.join(f"{C.NAMN_LINJE[l]} {r[l]:.1f}".replace('.', ',')
                                                          for l in C.STADSLINJER if r[l] >= 0.05), axis=1)
    ut = ut.fillna({'FM_vardag': 0, 'EM_vardag': 0, 'FM_per_timme': 0, 'EM_per_timme': 0}).fillna('')
    ut = ut[(ut.FM_vardag + ut.EM_vardag) > 0].sort_values('FM_vardag', ascending=False)
    ut.index.name = 'hallplatsomrade'
    return ut.round(2)


def byten_modell():
    """Byten enligt nätutläggningen av OD-matrisen: per zon och linjepar (resor per timme), FM och EM."""
    import b4_natverk as N
    zoner = list(pd.read_csv(P / 'a1_restider_min.csv', index_col=0).index)
    mon = N.monster(); nat = N.Nat(mon, zoner); nZ = nat.nZ
    rader = []
    for per in ('FM', 'EM'):
        OD = N.od_matris(per).reindex(index=nat.zoner, columns=nat.zoner).fillna(0.0).to_numpy()
        for i in range(nZ):
            for j in range(nZ):
                T = OD[i, j]
                if T <= 0 or i == j:
                    continue
                mal = j if nat.dist[i, j] <= nat.dist[i, nZ + j] else nZ + j
                if not np.isfinite(nat.dist[i, mal]):
                    continue
                vag = [mal]
                while vag[-1] != i and vag[-1] >= 0:
                    vag.append(nat.pred[i, vag[-1]])
                vag = vag[::-1]
                linje = None
                for u, v in zip(vag[:-1], vag[1:]):
                    if v >= 2 * nZ and u < 2 * nZ:                  # påstigning
                        ny = mon[nat._fordonsnod(v)[0]]['linje']
                        if u >= nZ and linje is not None:           # har redan åkt buss: byte
                            rader.append({'period': per, 'zon': nat.zoner[u - nZ], 'fran_linje': linje,
                                          'till_linje': ny, 'resor_h': T})
                        linje = ny
    b = pd.DataFrame(rader)
    b = b[b.fran_linje != b.till_linje]          # byte mellan två turmönster på samma linje är inget linjebyte
    per_zon = b.pivot_table(index='zon', columns='period', values='resor_h', aggfunc='sum').fillna(0.0)
    per_zon = per_zon.reindex(columns=['FM', 'EM']).fillna(0.0).sort_values('FM', ascending=False)
    per_zon.columns = ['FM_resor_per_timme', 'EM_resor_per_timme']
    par = b.groupby(['period', 'zon', 'fran_linje', 'till_linje']).resor_h.sum().reset_index()
    par['fran_linje'] = par.fran_linje.map(C.NAMN_LINJE); par['till_linje'] = par.till_linje.map(C.NAMN_LINJE)
    par = par.sort_values(['period', 'resor_h'], ascending=[False, False])
    tot = {per: float(N.od_matris(per).to_numpy().sum()) for per in ('FM', 'EM')}
    return per_zon.round(3), par.round(3), tot


def _valideringar(produkter, perioder):
    r = D.radata()
    r = r[r.linje.isin(C.STADSLINJER) & r.vardag & r['Product Type'].astype(str).isin(produkter)].copy()
    om = D.hallplatsomraden()
    r['omrade'] = r['Stop ID'].map(om['omrade']).fillna(r['Stop Name'])
    r['period'] = r.tid_min.map(lambda t: _period(t, *perioder))
    return r


def byten_biljett():
    r = _valideringar(('Bussbyte 2h',), (C.FM, C.EM))
    dagar = D.radata().loc[lambda d: d.vardag & d.linje.isin(C.STADSLINJER)].datum.nunique()
    ut = r.groupby('omrade').P.sum().rename('vardagar_totalt').to_frame()
    for per in ('FM', 'EM'):
        ut[f'{per}_totalt'] = r[r.period == per].groupby('omrade').P.sum()
    ut = ut.fillna(0).sort_values('vardagar_totalt', ascending=False)
    ut['per_vardag'] = ut.vardagar_totalt / dagar
    return ut.round(2), dagar


def skolresor():
    r = _valideringar(SKOLKORT, (C.FM, SKOL_EM))
    per_dag = r.groupby('datum').P.sum()
    skoldagar = per_dag[per_dag >= MIN_SKOLKORT_DAG].index
    r = r[r.datum.isin(skoldagar)]
    n = len(skoldagar)
    ut = pd.DataFrame({'FM_per_skoldag': r[r.period == 'FM'].groupby('omrade').P.sum() / n,
                       'EM_per_skoldag': r[r.period == 'EM'].groupby('omrade').P.sum() / n}).fillna(0.0)
    for per in ('FM', 'EM'):
        d = r[r.period == per].groupby(['omrade', 'linje']).P.sum().unstack().reindex(columns=C.STADSLINJER).fillna(0) / n
        ut[f'{per}_linjer'] = d.reindex(ut.index).fillna(0).apply(
            lambda q: ', '.join(f"{C.NAMN_LINJE[l]} {q[l]:.1f}".replace('.', ',') for l in C.STADSLINJER if q[l] >= 0.05),
            axis=1)
    ut = ut[(ut.FM_per_skoldag + ut.EM_per_skoldag) > 0].sort_values('FM_per_skoldag', ascending=False)
    return ut.round(2), n, (min(skoldagar).date(), max(skoldagar).date())


# ---------------------------------------------------------------- kartor (två paneler, FM och EM)
def _cirklar(ax, v, vmax, rmax, farg, kant, n_etik=8):
    for z in v.sort_values(ascending=False).index:
        if v[z] <= 0 or z not in POS:
            continue
        r = rmax * math.sqrt(v[z] / vmax)
        ax.add_patch(plt.Circle(POS[z], max(r, 22), facecolor=farg, edgecolor=kant, lw=0.6, alpha=0.78, zorder=8))
    st = [z for z in v.sort_values(ascending=False).index if z in POS and v[z] > 0][:n_etik]
    K.placera_etiketter(ax, [(z.replace('Centrum, Nygatan', 'Centrum'), POS[z], rmax * math.sqrt(v[z] / vmax))
                             for z in st], fontsize=6.4, undvik=[K.ruta_axes(ax, 0.0, 0.0, 0.4, 0.2)])


def _forklaring(ax, vmax, rmax, varden, titel, kant):
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    bx = x0 + 0.06 * (x1 - x0); by = y0 + 0.05 * (y1 - y0)
    ax.text(bx, by + 2.5 * rmax, titel, fontsize=7.0, color=K.TEXT, zorder=21, path_effects=K.HALO)
    for v in varden:
        r = rmax * math.sqrt(v / vmax)
        ax.add_patch(plt.Circle((bx + rmax, by + r), r, facecolor='none', edgecolor=kant, lw=0.7, zorder=21))
        ax.text(bx + 2 * rmax + 60, by + 2 * r, f'{v:g}'.replace('.', ','), fontsize=6.6, va='center', color=K.TEXT,
                zorder=21, path_effects=K.HALO)


def karta(fm, em, titlar, enhet, namn, farg='#495057', kant='#212529', uts='tatort', varden=None, rmax=360):
    vmax = max(fm.max(), em.max())
    snygga = [m * 10 ** e for e in range(-2, 4) for m in (1, 2, 5)]
    topp = max([t for t in snygga if t <= vmax] or [vmax])
    varden = varden or [topp, topp / 2, topp / 10]
    fig, axs = plt.subplots(1, 2, figsize=(10.4, 10.2))
    for ax, v, t in zip(axs, (fm, em), titlar):
        K.ny_karta(uts, ax=ax, titel=t)
        K.rita_linjer(ax, alpha=0.45, lw=1.2, zorder=3)
        _cirklar(ax, v, vmax, rmax, farg, kant)
    _forklaring(axs[0], vmax, rmax, varden, enhet, kant)
    K.ram(axs[0], loc=(0.6, 0.035))
    fig.tight_layout()
    return K.spara(fig, namn)


def main():
    UT.mkdir(parents=True, exist_ok=True)
    pa = pastigande(); pa.to_csv(P / 'a1_pastigande_hallplats.csv')
    bz, bpar, odtot = byten_modell()
    bz.to_csv(P / 'a1_byten_modell_zon.csv'); bpar.to_csv(P / 'a1_byten_modell_linjepar.csv', index=False)
    bb, nd = byten_biljett(); bb.to_csv(P / 'a1_byten_bussbyte_biljett.csv')
    sk, ns, (d0, d1) = skolresor(); sk.to_csv(P / 'a1_skolresor_hallplats.csv')
    info = pd.DataFrame({'Uppgift': [
        'Påstigande FM/EM', 'Byten (modell)', 'Byten (biljett)', 'Skolresor'], 'Underlag och metod': [
        f'Tvättad höstdata 2026 (Norra, Södra, Västra, Östra) och sommardata 2026 (Järsö). Medel per vardag. FM 06–09, '
        f'EM 15–18. Per timme = per vardag / 3.',
        f'Korrigerad OD-matris (A1) utlagd på restidsnätet, bytesstraff {C.BYTESSTRAFF_MIN:g} min, gång ≤ '
        f'{C.GANG_MAX_M:g} m. Resor per timme som byter buss i zonen. OD-matrisen: FM {odtot["FM"]:.1f} och EM '
        f'{odtot["EM"]:.1f} resor per timme.'.replace('.', ','),
        f'Valideringar med biljettypen "Bussbyte 2h", sommardata 2026, stadslinjerna, {nd} vardagar. Bara '
        f'enkelbiljetter; kortresenärers byten syns inte.',
        f'Valideringar med skolkort (läsår 2025–2026 och 2026–2027 samt "glömt skolkort"), sommardata 2026, '
        f'stadslinjerna, {ns} skoldagar (12 maj–5 juni och 20 augusti–14 september 2026, vardagar med minst '
        f'{MIN_SKOLKORT_DAG} skolkortsvalideringar). '
        f'FM 06–09, EM 12–18. Höstdatan saknar biljettyp.']})
    with pd.ExcelWriter(UT / 'pastigande_byten_skolresor.xlsx') as xw:
        info.to_excel(xw, sheet_name='Läs mig', index=False)
        pa.rename(columns={'FM_vardag': 'Påstigande FM 06–09 per vardag', 'FM_per_timme': 'FM per timme',
                           'FM_linjer': 'FM per linje', 'EM_vardag': 'Påstigande EM 15–18 per vardag',
                           'EM_per_timme': 'EM per timme', 'EM_linjer': 'EM per linje'}) \
            .to_excel(xw, sheet_name='Påstigande FM och EM', index_label='Hållplatsområde')
        bz.rename(columns={'FM_resor_per_timme': 'Byten FM (resor per timme)',
                           'EM_resor_per_timme': 'Byten EM (resor per timme)'}) \
            .to_excel(xw, sheet_name='Byten per hållplats (modell)', index_label='Hållplatsområde')
        bpar.rename(columns={'period': 'Period', 'zon': 'Hållplatsområde', 'fran_linje': 'Från linje',
                             'till_linje': 'Till linje', 'resor_h': 'Resor per timme'}) \
            .to_excel(xw, sheet_name='Byten per linjepar (modell)', index=False)
        bb.rename(columns={'vardagar_totalt': f'Bussbyte 2h, summa {nd} vardagar', 'FM_totalt': 'varav FM 06–09',
                           'EM_totalt': 'varav EM 15–18', 'per_vardag': 'Per vardag'}) \
            .to_excel(xw, sheet_name='Byten (Bussbyte 2h)', index_label='Hållplatsområde')
        sk.rename(columns={'FM_per_skoldag': 'Skolresor FM 06–09 per skoldag', 'EM_per_skoldag': 'Skolresor EM 12–18 per skoldag',
                           'FM_linjer': 'FM per linje', 'EM_linjer': 'EM per linje'}) \
            .to_excel(xw, sheet_name='Skolresor FM och EM', index_label='Hållplatsområde')
    print(UT / 'pastigande_byten_skolresor.xlsx')
    print(karta(pa.FM_vardag, pa.EM_vardag, ('Påstigande förmiddag (FM 06–09)', 'Påstigande eftermiddag (EM 15–18)'),
                'Påstigande per vardag', 'a1_6_pastigande_fm_em.png'))
    print(karta(bz.FM_resor_per_timme, bz.EM_resor_per_timme, ('Byten förmiddag (FM 06–09)', 'Byten eftermiddag (EM 15–18)'),
                'Byten per timme', 'a1_7_byten_fm_em.png', farg='#e8590c', kant='#a63e06'))
    print(karta(sk.FM_per_skoldag, sk.EM_per_skoldag, ('Skolresor förmiddag (FM 06–09)', 'Skolresor eftermiddag (EM 12–18)'),
                'Påstigande med skolkort per skoldag', 'a1_8_skolresor_fm_em.png', farg='#c92a2a', kant='#7d1a1a'))
    print(pa.head(15).to_string()); print(bz.head(10).to_string()); print(bpar.head(12).to_string())
    print(bb.head(8).to_string()); print(sk.head(12).to_string()); print(sk.sort_values('EM_per_skoldag', ascending=False).head(12).to_string())


if __name__ == '__main__':
    main()
