# -*- coding: utf-8 -*-
"""B4 – Genomgående linje V/Ö, förslagspaket och systemeffekter (täckningsgrad före/efter).

Scenarier (åtgärderna definieras i b4_forslag.forslag())
  idag      Dagens linjenät.
  1a        Möckelö Strand via dagens gator, alla turer (kräver fler bussar – underlag för kostnadskalkylen).
  1a_del    1a, bara de turer som ryms i dagens omlopp.
  1b_VÖ     Möckelö Strand via förlängd Norrgårdsvägen + genomgående linje V/Ö (sammanslagning).
  2         N2 på linje Ö (de turer som ryms).
  3         Linje N via Bo-Bil i stället för Vikingagränd.
  paket_A   1b + genomgående V/Ö + 2 + 3 (ryms i dagens omlopp).
  paket_B   1a (alla turer, fler bussar) + 2 + 3.
För varje scenario: omlopp (fordon, omloppstid, körtid, km), täckningsgrad i Mariehamn (400 m, turtäthetsklasser,
svag och otäckt befolkning), resenärseffekter (OD-utläggning, genomgående resor) och tillkommande påstigande.
Genomgående V/Ö: fordonet fortsätter från linje V direkt som linje Ö (uppehåll 0,5 min i centrum, samma
hållplatsläge) och regleringen tas efter Ö-turen. Båda linjerna behåller 30 min turintervall och pulsen.
Utdata: data/processed/b4_paket.json, b4_paket_omlopp.csv, b4_paket_tackning.csv.gz,
        output/kartor/b4_9_linje_vo.png, b4_10_paket_omlopp.png, b4_11_systemeffekter.png, b4_12_tackning_fore_efter.png
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402
import kartlib as K  # noqa: E402
import b4_omlopp as O  # noqa: E402
import b4_natverk as N  # noqa: E402
import b4_forslag as F  # noqa: E402
from a2_tackning import KLASSER, avgangar_inom, hallplatser_med_avgangar, klass, sammanstall  # noqa: E402

P = C.PROCESSED
VO = [('V', 'Ö')]
SCENARIER = [
    # id, namn, åtgärder, genomgående par, driftform
    ('idag', 'I dag', [], [], 'alla'),
    ('1a', '1a Möckelö Strand, dagens gator – alla turer', ['1a'], [], 'fler_bussar'),
    ('1a_del', '1a – bara turer som ryms', ['1a'], [], 'ryms'),
    ('1b_VÖ', '1b Möckelö Strand + genomgående V/Ö', ['1b'], VO, 'ryms'),
    ('2', '2 N2 på linje Ö', ['2'], [], 'ryms'),
    ('3', '3 Linje N via Bo-Bil', ['3'], [], 'ryms'),
    ('paket_A', 'Paket A: 1b + V/Ö + 2 + 3', ['1b', '3', '2'], VO, 'ryms'),
    ('paket_B', 'Paket B: 1a (alla turer) + 2 + 3', ['1a', '3', '2'], [], 'fler_bussar'),
]
FARG_VO = '#8c3b74'


def atgarder():
    xy = F.stopp_xy()
    ut = {f['id']: f for f in F.forslag()}
    bb = F.bobil_delta(xy)
    ut['3']['delta'], ut['3']['km_tur'] = bb['delta_min'], bb['delta_km']
    return ut, xy


def berorda_turer(f, t):
    lt = t[t.linje == f['linje']]
    if f['typ'] == 'ny' and f['segment'][1] is None:
        lt = lt[lt.monster.map(lambda m: f['segment'][0] in m)]
    return list(lt.sort_values('avg').trip_id)


# ====================================================================== omlopp
def planera(t, r, ref, atg, ids, gen, driftform):
    """Lägger på åtgärderna i tur och ordning. En åtgärd som inte ryms med alla turer får bara de turer som ryms
    (prövas en i taget). 'fler_bussar': den första åtgärden körs med alla turer och får kräva fler fordon
    (redovisas som merkostnad); följande åtgärder prövas mot den nya ramen."""
    delta, km, turer = {}, {}, {}
    kw = dict(genomgaende=gen, referens=ref)
    for i, a in enumerate(ids):
        f = atg[a]; kand = berorda_turer(f, t)
        prov = dict(delta); [prov.__setitem__(k, prov.get(k, 0.0) + f['delta']) for k in kand]
        nt_prov = O.nyckeltal(O.bygg_omlopp(O.med_andring(t, prov), **kw))
        ok = O.inom_ram(nt_prov, r)
        if driftform == 'fler_bussar' and i == 0:        # första åtgärden får kräva fler bussar – ny ram
            valda = kand
            r = {'fordon': nt_prov['fordon'], 'omloppstid_h': nt_prov['omloppstid_h']}
        elif ok:
            valda = kand
        else:
            valda = []
            for tid in kand:
                p2 = dict(delta)
                for k in valda + [tid]:
                    p2[k] = p2.get(k, 0.0) + f['delta']
                if O.inom_ram(O.nyckeltal(O.bygg_omlopp(O.med_andring(t, p2), **kw)), r):
                    valda.append(tid)
        for k in valda:
            delta[k] = delta.get(k, 0.0) + f['delta']; km[k] = km.get(k, 0.0) + f['km_tur']
        turer[a] = valda
    plan, nt, ok = O.verifiera(t, delta, O.ram(t), km_delta=km, **kw)
    return plan, nt, ok, turer


# ====================================================================== täckning
def hallplatser_scenario(hpl0, atg, turer, xy):
    h = hpl0.copy()
    for a, valda in turer.items():
        f = atg[a]; tn = frozenset(valda)
        if not tn:
            continue
        if f['typ'] == 'ny':
            h.loc[f'NY_{a}'] = {'turer': tn, 'linjer': f['linje'], 'avgangar': len(tn), 'x': f['xy'][0],
                                'y': f['xy'][1], 'namn': f['hpl_namn']}
        else:
            h.at[f['bort'], 'turer'] = h.at[f['bort'], 'turer'] - tn
            for s in f['till']:
                if s in h.index:
                    h.at[s, 'turer'] = h.at[s, 'turer'] | tn
                else:
                    h.loc[s] = {'turer': tn, 'linjer': f['linje'], 'avgangar': len(tn), 'x': xy.at[s, 'x'],
                                'y': xy.at[s, 'y'], 'namn': xy.at[s, 'namn']}
    h = h[h.turer.map(len) > 0].copy()
    h['avgangar'] = h.turer.map(len)
    return h


# ====================================================================== resenärer
def monster_scenario(mon0, atg, turer, t, gen):
    """Mönster med förslagens körtider; andelen turer som trafikerar en åtgärd skalar tillägget."""
    mon = []
    for m in mon0:
        m = dict(m); m['akt'] = m['akt'].copy(); s = list(m['stopp'])
        for a, valda in turer.items():
            f = atg[a]
            if m['linje'] != f['linje'] or not valda:
                continue
            andel = len(valda) / max(len(berorda_turer(f, t)), 1)
            if f['typ'] == 'ny':
                a0, b0 = f['segment']
                for k in range(len(s) - 1):
                    if s[k] == a0 and (b0 is None or s[k + 1] == b0):
                        m['akt'][k] += f['delta'] * andel
                        break
            elif f['bort'] in s:
                k = s.index(f['bort'])
                z = list(m['zoner']); z[k] = 'Bo-Bil'; m['zoner'] = tuple(z)
                m['akt'][k - 1] += f['delta'] / 2; m['akt'][k] += f['delta'] / 2
        mon.append(m)
    for x, y in gen:                                   # genomgående: fordonet fortsätter från x till y
        hx = max([m for m in mon if m['linje'] == x], key=lambda m: len(m['turer']))
        hy = max([m for m in mon if m['linje'] == y], key=lambda m: len(m['turer']))
        for a_, b_ in ((hx, hy), (hy, hx)):
            akt = np.concatenate([a_['akt'], b_['akt']]); akt[len(a_['akt'])] += O.GENOMGANG_MIN
            mon.append({'linje': a_['linje'] + b_['linje'], 'stopp': a_['stopp'] + b_['stopp'][1:],
                        'zoner': a_['zoner'] + b_['zoner'][1:], 'akt': akt, 'turer': []})
    return mon


def resenarer(nat0, mon, zoner):
    j = N.jamfor(nat0, N.Nat(mon, zoner)); fak = N.dagsfaktor()
    medel = lambda k: float(np.mean([j[p][k] for p in ('FM', 'EM')]))
    return {'resenarsminuter_vardag': round(medel('resenarsminuter_h') * fak, 1),
            'resor_langre_vardag': round(medel('resor_langre_h') * fak, 1),
            'resor_kortare_vardag': round(medel('resor_kortare_h') * fak, 1)}


# ====================================================================== huvudflöde
def berakna():
    t = O.turer(); plan0 = O.bygg_omlopp(t); r = O.ram(t); ref = O.kopplingar(plan0)
    atg, xy = atgarder()
    pkt = pd.read_csv(P / 'a2_delpunkter.csv.gz')
    mh = pkt.mariehamn.to_numpy()
    hpl0 = hallplatser_med_avgangar()
    rate = F.pastigande_per_inv(pkt)
    zoner = list(pd.read_csv(P / 'a1_restider_min.csv', index_col=0).index)
    mon0 = N.monster(); nat0 = N.Nat(mon0, zoner)
    res, planer, kl = {}, [], {}
    for sid, namn, ids, gen, drift in SCENARIER:
        plan, nt, ok, turer = planera(t, r, ref, atg, ids, gen, drift)
        h = hallplatser_scenario(hpl0, atg, turer, xy)
        avg, _ = avgangar_inom(pkt, h)
        k = np.array([klass(v) for v in avg]); kl[sid] = k
        p = pkt.assign(k=k)
        tack_mh = sammanstall(p, 'k', mh); tack_alla = sammanstall(p, 'k')
        nya = {}
        for a, valda in turer.items():
            f = atg[a]
            if f['typ'] == 'ny' and valda:
                d_ = np.hypot(pkt.x - f['xy'][0], pkt.y - f['xy'][1]) <= C.TACKNING_M
                ny_inv = float(pkt.loc[d_ & (kl['idag'] == 0) & (k > 0), 'bef'].sum()) if 'idag' in kl else 0.0
                nya[a] = {'avgangar': len(valda), 'ny_tackning_inv': round(ny_inv),
                          'pastigande_vardag': round(ny_inv * rate.get(f['linje'], rate['alla']), 2)}
        rs = resenarer(nat0, monster_scenario(mon0, atg, turer, t, gen), zoner) if ids else \
            {'resenarsminuter_vardag': 0.0, 'resor_langre_vardag': 0.0, 'resor_kortare_vardag': 0.0}
        res[sid] = {'namn': namn, 'atgarder': ids, 'genomgaende': ['/'.join(g) for g in gen], 'driftform': drift,
                    'ryms': bool(ok), 'omlopp': nt,
                    'turer_per_atgard': {a: len(v) for a, v in turer.items()},
                    'turer_per_atgard_tot': {a: len(berorda_turer(atg[a], t)) for a in turer},
                    'tackning_mariehamn': tack_mh, 'tackning_hela_omradet': tack_alla,
                    'nya_hallplatser': nya, 'resenarer': rs}
        pl = plan.drop(columns=['monster']).copy(); pl['scenario'] = sid
        planer.append(pl)
        print(f"{sid:8s} ryms={ok} fordon={nt['fordon']} omloppstid={nt['omloppstid_h']} km={nt['km']} "
              f"turer={ {a: len(v) for a, v in turer.items()} } inom400={tack_mh['inom_400m_andel']} "
              f"≥30={tack_mh['minst_30_avg_andel']} svag={tack_mh['svag_invanare']} res={rs}")
    # förändring mot i dag
    bas = res['idag']
    k0 = kl['idag']; bef = pkt.bef.to_numpy()
    for sid, v in res.items():
        k1 = kl[sid]; sm = lambda m: int(round(float(bef[mh & m].sum())))
        v['forandring_invanare_mariehamn'] = {
            'ny_tackning': sm((k0 == 0) & (k1 > 0)), 'lyft_till_minst_30': sm((k0 > 0) & (k0 < 3) & (k1 >= 3)),
            'battre_klass': sm(k1 > k0), 'samre_klass': sm(k1 < k0), 'forlorad_tackning': sm((k0 > 0) & (k1 == 0)),
            'samre_klass_kvar_tackning': sm((k1 < k0) & (k1 > 0))}
        a, b = v['tackning_mariehamn'], bas['tackning_mariehamn']
        inv = lambda d, i: d[KLASSER[i][2]]['invanare']
        v['forandring_mariehamn'] = {
            'inom_400m_inv': -(inv(a, 0) - inv(b, 0)),
            'minst_15_inv': sum(inv(a, i) for i in range(2, 5)) - sum(inv(b, i) for i in range(2, 5)),
            'minst_30_inv': sum(inv(a, i) for i in range(3, 5)) - sum(inv(b, i) for i in range(3, 5)),
            'svag_inv': a['svag_invanare'] - b['svag_invanare'],
            'otackt_inv': inv(a, 0) - inv(b, 0)}
        v['forandring_omlopp'] = {k: round(v['omlopp'][k] - bas['omlopp'][k], 2)
                                  for k in ('fordon', 'omloppstid_h', 'korttid_h', 'km')}
    pd.concat(planer).to_csv(P / 'b4_paket_omlopp.csv', index=False)
    tk = pkt[['x', 'y', 'bef', 'ruta_id', 'mariehamn']].copy()
    for sid, k in kl.items():
        tk[f'klass_{sid}'] = k
    tk.round({'bef': 5}).to_csv(P / 'b4_paket_tackning.csv.gz', index=False)
    with open(P / 'b4_paket.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=float)
    return res


# ====================================================================== figurer
def sv(x, d=1):
    return f'{x:.{d}f}'.replace('.', ',').replace('-', '−')


def linjekedjor_xy():
    import s01_vagdragning as V
    geo = V.segmentgeometri()
    return {ln: [np.vstack([geo[s] if i == 0 else geo[s][1:] for i, s in enumerate(k)]) for k in kl]
            for ln, kl in V.linjekedjor().items()}


def fig_linje_vo(res):
    atg, xy = atgarder()
    kedjor = linjekedjor_xy()
    fig, ax = plt.subplots(figsize=(9.0, 9.0))
    K.ny_karta((104500, 111400, 6681700, 6688300), ax=ax, titel='Genomgående linje V/Ö med Möckelö Strand (1b) och N2 (2)')
    K.rita_linjer(ax, lw=1.3, alpha=0.35, zorder=3, etikett=False)
    for ln in ('V', 'Ö'):
        for i, xy_ in enumerate(kedjor[ln]):
            ax.plot(xy_[:, 0], xy_[:, 1], color=FARG_VO, lw=3.0, solid_capstyle='round', zorder=5,
                    path_effects=[K.pe.Stroke(linewidth=4.6, foreground='white'), K.pe.Normal()])
    ms = xy.loc[F.HPL['Möckelö Strand'], ['x', 'y']].to_numpy(float)
    m = atg['1b']['xy']; n2 = atg['2']['xy']
    ax.plot([ms[0], m[0]], [ms[1], m[1]], color=FARG_VO, lw=3.0, ls=(0, (2.5, 1.6)), zorder=5)
    for p, nm in [(m, 'Möckelö Strand ny'), (n2, 'N2')]:
        ax.scatter([p[0]], [p[1]], s=200, marker='*', color='#1c5cab', edgecolor='white', lw=0.8, zorder=8)
    c = xy.loc['9025302000066202', ['x', 'y']].to_numpy(float)
    ax.scatter([c[0]], [c[1]], s=110, marker='s', color='#1f1f1e', edgecolor='white', lw=0.8, zorder=8)
    hinder = K.punkt_hinder(ax, [m[0], n2[0], c[0]], [m[1], n2[1], c[1]], px=11)
    K.placera_etiketter(ax, [('Centrum, Nygatan\n(genomgång V → Ö)', tuple(c), 120), ('Möckelö Strand (ny)', tuple(m), 90),
                             ('N2', tuple(n2), 90)], fontsize=7, fet=True, undvik=hinder)
    v = res['1b_VÖ']; pa = res['paket_A']
    txt = [r'$\bf{Varv\ (2\ bussar,\ 30\ min\ turintervall\ på\ båda\ linjerna)}$',
           'Centrum :20 → linje V via Möckelö Strand (29,5 min)',
           '→ Centrum :49,5 – uppehåll 0,5 min, bussen fortsätter som linje Ö',
           '→ Centrum :50 → linje Ö via N2 (23,5 min) → Centrum :13,5',
           '→ reglering 6,5 min → linje V :20 (nästa buss 30 min senare)',
           r'$\bf{Omlopp}$' + f"   {pa['omlopp']['fordon']} bussar som i dag, omloppstid "
           f"{'+' if pa['forandring_omlopp']['omloppstid_h'] >= 0 else ''}{sv(pa['forandring_omlopp']['omloppstid_h'] * 60, 0)} min/vardag (paket A)",
           f"Skolturer linje Ö (13:10–15:10): reglering 1,5–2 min per varv"]
    ax.text(0.015, 0.985, '\n'.join(txt), transform=ax.transAxes, ha='left', va='top', fontsize=7, color=K.TEXT,
            zorder=30, linespacing=1.5, bbox=dict(boxstyle='round,pad=0.55', facecolor='white', edgecolor='#d6d5d0', lw=0.6, alpha=0.95))
    h = [Line2D([], [], color=FARG_VO, lw=3, label='Linje V/Ö (genomgående)'),
         Line2D([], [], color=FARG_VO, lw=3, ls=(0, (2.5, 1.6)), label='Förlängning till Möckelö Strand (schematisk)'),
         Line2D([], [], marker='*', ls='', color='#1c5cab', markersize=12, label='Ny hållplats'),
         Line2D([], [], marker='s', ls='', color='#1f1f1e', markersize=8, label='Genomgång i centrum'),
         Line2D([], [], color='#9a978f', lw=1.5, label='Övriga stadslinjer')]
    lg = K.teckenforklaring(ax, h, loc='lower left', fontsize=7)
    lg.set_bbox_to_anchor((1.02, 0.0), transform=ax.transAxes)
    K.ram(ax)
    return K.spara(fig, 'b4_9_linje_vo.png')


def fig_paket_omlopp(res):
    pl = pd.read_csv(P / 'b4_paket_omlopp.csv', dtype={'trip_id': str})
    paneler = [('idag', 'I dag'), ('paket_A', 'Paket A – 1b med genomgående V/Ö + N2 + Bo-Bil'),
               ('paket_B', 'Paket B – 1a med alla turer + N2 + Bo-Bil')]
    fig, axs = plt.subplots(len(paneler), 1, figsize=(12.4, 0.75 + 1.85 * len(paneler)))
    for ax, (sid, rub) in zip(axs, paneler):
        p = pl[pl.scenario == sid]
        v = res[sid]; d = v['forandring_omlopp']
        rub += f" – {v['omlopp']['fordon']} bussar"
        if sid != 'idag':
            dm = d['omloppstid_h'] * 60
            rub += f" ({'ryms' if v['ryms'] else 'ryms inte'})   ·   omloppstid "
            rub += f"+{sv(dm / 60)} h/vardag" if dm >= 60 else f"{'+' if dm >= 0 else ''}{sv(dm, 0)} min/vardag"
            rub += f"   ·   {'+' if d['km'] >= 0 else ''}{sv(d['km'], 0)} km/vardag"
        O.rita_omlopp(ax, p, titel=rub, andrade=set(p.loc[p.delta != 0, 'trip_id']))
        ax.title.set_color(K.TEXT if v['ryms'] else '#c0392b')
        if v['omlopp']['fordon'] > res['idag']['omlopp']['fordon']:
            for lbl in ax.get_yticklabels():
                if lbl.get_text() == f"Buss {v['omlopp']['fordon']}":
                    lbl.set_color('#c0392b'); lbl.set_fontweight('bold')
    fig.suptitle('Omlopp före och efter – förslagspaket', x=0.01, ha='left', fontsize=11.5, fontweight='bold')
    extra = [Patch(facecolor='white', edgecolor='#52514e', hatch='//////', label='Tillagd körtid'),
             Line2D([], [], color='#1c5cab', lw=2.2, label='Genomgående (fortsätter som annan linje)')]
    O.omlopp_forklaring(fig, extra=extra, y=-0.01)
    fig.tight_layout(rect=(0, 0.04, 1, 0.975), h_pad=0.9)
    ut = C.KARTOR / 'b4_10_paket_omlopp.png'
    fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


def fig_systemeffekter(res):
    ids = ['1a', '1a_del', '1b_VÖ', '2', '3', 'paket_A', 'paket_B']
    kort = {'1a': '1a alla turer\n(20 avg., 6 bussar)', '1a_del': '1a bara turer som ryms\n(8 avg./vardag)',
            '1b_VÖ': '1b + genomgående V/Ö\n(20 avg./vardag)',
            '2': '2 N2 linje Ö', '3': '3 N via Bo-Bil', 'paket_A': 'Paket A\n1b + V/Ö, 2, 3', 'paket_B': 'Paket B\n1a, 2, 3 (6 bussar)'}
    mat = [('ny_tackning', 'Får hållplats inom 400 m', '#2f9e44', 1),
           ('lyft_till_minst_30', 'Får minst 30 avgångar/vardag (hade 1–29)', '#1c5cab', 1),
           ('forlorad_tackning', 'Förlorar hållplats inom 400 m', '#c0392b', -1),
           ('samre_klass_kvar_tackning', 'Färre avgångar, har kvar hållplats', '#f28e2b', -1)]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.4, 5.8), gridspec_kw={'width_ratios': [1.35, 1.0], 'wspace': 0.36})
    y = np.arange(len(ids)); hgt = 0.19
    for j, (k, lbl, f, tecken) in enumerate(mat):
        v = [tecken * res[i]['forandring_invanare_mariehamn'][k] for i in ids]
        ax.barh(y + (j - 1.5) * hgt, v, height=hgt, color=f, label=lbl)
        for yy, vv in zip(y, v):
            if vv:
                ax.text(vv + (4 if vv > 0 else -4), yy + (j - 1.5) * hgt, f'{vv:+d}'.replace('-', '−'), va='center',
                        ha='left' if vv > 0 else 'right', fontsize=6.6, color=K.TEXT)
    ax.axvline(0, color='#52514e', lw=0.8)
    ax.set_yticks(y); ax.set_yticklabels([kort[i] for i in ids], fontsize=8); ax.invert_yaxis()
    ax.set_xlabel('invånare i Mariehamn med bättre (+) respektive sämre (−) tillgänglighet än i dag', fontsize=8)
    ax.set_xlim(-90, 260); ax.tick_params(labelsize=7.5); ax.grid(axis='x', color='#e6e4de', lw=0.6); ax.set_axisbelow(True)
    for s_ in ['top', 'right']:
        ax.spines[s_].set_visible(False)
    ax.legend(loc='upper left', bbox_to_anchor=(0, -0.11), ncol=2, fontsize=7.3, frameon=False)
    ax.set_title('Vem får bättre och sämre tillgänglighet?', loc='left', fontsize=10, fontweight='bold')
    rad = [('Hållplats inom 400 m', lambda t: t['inom_400m_andel']),
           ('Minst 15 avgångar/vardag', lambda t: t['minst_15_avg_andel']),
           ('Minst 30 avgångar/vardag', lambda t: t['minst_30_avg_andel']),
           ('Svag tillgänglighet (1–29 avg.)', lambda t: t['svag_andel']),
           ('Ingen hållplats inom 400 m', lambda t: 1 - t['inom_400m_andel'])]
    ax2.axis('off')
    kol = ['idag', 'paket_A', 'paket_B']
    cell = [[n] + [sv(100 * fn(res[s_]['tackning_mariehamn']), 1) + ' %' for s_ in kol] for n, fn in rad]
    cell += [['Bussar', *[str(res[s_]['omlopp']['fordon']) for s_ in kol]],
             ['Omloppstid (h/vardag)', *[sv(res[s_]['omlopp']['omloppstid_h']) for s_ in kol]],
             ['Fordonskilometer per vardag', *[sv(res[s_]['omlopp']['km'], 0) for s_ in kol]],
             ['Längre restid befintliga resenärer\n(resenärsminuter/vardag)', '–',
              *[sv(res[s_]['resenarer']['resenarsminuter_vardag'], 0) for s_ in kol[1:]]]]
    tb = ax2.table(cellText=cell, colLabels=['Mariehamn (14 821 inv.)', 'I dag', 'Paket A', 'Paket B'], loc='upper left',
                   cellLoc='right', colLoc='right', colWidths=[0.52, 0.16, 0.16, 0.16])
    tb.auto_set_font_size(False); tb.set_fontsize(7.6); tb.scale(1, 1.5)
    for (r_, c_), ce in tb.get_celld().items():
        ce.set_edgecolor('#e0ded7'); ce.set_linewidth(0.5)
        if c_ == 0:
            ce._loc = 'left'; ce.get_text().set_ha('left')
        if r_ == 0:
            ce.set_facecolor('#f1efe9'); ce.get_text().set_fontweight('bold')
        if r_ == len(cell):
            ce.set_height(ce.get_height() * 1.6)
    ax2.set_title('Nyckeltal – i dag och förslagspaket', loc='left', fontsize=10, fontweight='bold')
    fig.suptitle('Systemeffekter av linjeförslagen', x=0.01, ha='left', fontsize=12, fontweight='bold')
    ut = C.KARTOR / 'b4_11_systemeffekter.png'
    fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


def fig_tackning_fore_efter(res):
    tk = pd.read_csv(P / 'b4_paket_tackning.csv.gz')
    farg = ['#cfcbc2', '#c6dbf5', '#7fb0ec', '#2a78d6', '#0d366b']
    fig, axs = plt.subplots(1, 2, figsize=(12.6, 8.4))
    h = C.DELRUTA_M
    rb = tk.groupby('ruta_id').bef.sum(); alfa = (0.35 + 0.65 * np.sqrt(tk.ruta_id.map(rb) / rb.max())).to_numpy()
    x0, y0 = tk.x.min() - h / 2, tk.y.min() - h / 2
    ix = ((tk.x - x0) // h).astype(int).to_numpy(); iy = ((tk.y - y0) // h).astype(int).to_numpy()
    for ax, sid, rub in [(axs[0], 'idag', 'I dag'), (axs[1], 'paket_A', 'Med förslagspaket A (1b + V/Ö, 2, 3)')]:
        K.ny_karta((104700, 111500, 6679300, 6688100), ax=ax, titel=rub)
        img = np.zeros((iy.max() + 1, ix.max() + 1, 4))
        rgba = np.array([to_rgba(farg[int(k)]) for k in tk[f'klass_{sid}']]); rgba[:, 3] = alfa
        if sid != 'idag':
            bat = (tk[f'klass_{sid}'] > tk.klass_idag).to_numpy(); sam = (tk[f'klass_{sid}'] < tk.klass_idag).to_numpy()
            rgba[bat] = to_rgba('#2f9e44', 0.95); rgba[sam] = to_rgba('#c0392b', 0.95)
        img[iy, ix] = rgba
        ax.imshow(img, origin='lower', extent=(x0, x0 + img.shape[1] * h, y0, y0 + img.shape[0] * h),
                  interpolation='nearest', zorder=1)
        D.befolkning().boundary.plot(ax=ax, color='white', linewidth=0.35, alpha=0.8, zorder=2)
        ax.set_xlabel(''); ax.set_ylabel('')
        K.rita_linjer(ax, lw=1.2, alpha=0.8, zorder=4)
        t_ = res[sid]['tackning_mariehamn']
        ax.text(0.02, 0.98, f"Inom 400 m: {sv(100 * t_['inom_400m_andel'])} %\nMinst 30 avg./vardag: "
                f"{sv(100 * t_['minst_30_avg_andel'])} %\nSvag tillgänglighet: {sv(100 * t_['svag_andel'])} %",
                transform=ax.transAxes, ha='left', va='top', fontsize=7.4, color=K.TEXT, zorder=30, linespacing=1.5,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#d6d5d0', lw=0.6, alpha=0.95))
        K.ram(ax)
    hnd = [Patch(facecolor=f, label=n) for f, (_, _, n) in zip(farg, KLASSER)]
    hnd += [Patch(facecolor='#2f9e44', label='Förbättrad klass med paket A'), Patch(facecolor='#c0392b', label='Försämrad klass med paket A')]
    fig.legend(handles=hnd, loc='lower center', ncol=4, fontsize=7.4, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.suptitle('Turtäthet inom 400 m (avgångar per vardag) – före och efter', x=0.01, ha='left', fontsize=12, fontweight='bold')
    fig.tight_layout(rect=(0, 0.05, 1, 0.97))
    ut = C.KARTOR / 'b4_12_tackning_fore_efter.png'
    fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


def main():
    res = berakna()
    for f in (fig_linje_vo, fig_paket_omlopp, fig_systemeffekter, fig_tackning_fore_efter):
        print(f(res))


if __name__ == '__main__':
    main()
