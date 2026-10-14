# -*- coding: utf-8 -*-
"""B4 – Sammanslagning av linjer (genomgående linjer i centrum): tidsutrymme för längre linjer utan fler bussar.

Princip
  * Stadslinjerna N, S, V och Ö är slingor från Centrum, Nygatan med 30 min turintervall i rusning och avgång
    i en gemensam puls (:20/:50). Varje linje har i dag en egen vändtid i centrum (30 min − körtid) som måste
    rymma både regleringstid och eventuell förlängning.
  * Slås två linjer A och B ihop till en genomgående linje fortsätter fordonet direkt från A till B (och från B
    till A nästa varv). Regleringen behöver då bara tas en gång per varv. Den ena halvan får ett kort uppehåll
    i centrum (GENOMGANG = 0,5 min) och kan förlängas, medan den andra halvan behåller minst REGLERING = 3 min.
  * Med bibehållen puls: utrymme för förlängning av A = 30 − GENOMGANG − t_A, förutsatt att 30 − t_B ≥ REGLERING.
    Utan sammanslagning: 30 − REGLERING − t_A. Vinsten är därmed REGLERING − GENOMGANG = 2,5 min per tur, plus att
    A kan använda B:s överskott om pulsen släpps för B (redovisas som 'utan puls').
  * Genomgående resor: korrigerad OD-matris (A1) utlagd på nätet med de sammanslagna linjerna – resor som slipper
    byte i centrum och sparade resenärsminuter (b4_natverk.py).
  * Körtiden är medianen för rusningsturerna. Linje Ö:s skolturer (08:20, 08:45, 13:10–15:10 via Strandnäs skola
    södra) är 5–6 min längre och har därför mindre utrymme – se omloppsverifieringen för enskilda förslag.
  * Nåbarhet för områden som i dag saknar hållplats inom 400 m (A3, behov av ändrad linjesträckning): behövd
    tilläggstid per tur = 2 × avstånd till närmaste körväg × 1,3 (omvägsfaktor) / 25 km/h + 0,5 min uppehåll.
    För Möckelö Strand används beställarens restider (förslag 1a/1b).
Utdata: data/processed/b4_sammanslagning_par.csv, b4_sammanslagning_omraden.csv, b4_sammanslagning.json,
        output/kartor/b4_8_sammanslagning.png
"""
import itertools
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import b4_natverk as N  # noqa: E402
import b4_omlopp as O  # noqa: E402
import kartlib as K  # noqa: E402

P = C.PROCESSED
LINJER = ['N', 'S', 'V', 'Ö']        # 30-minuterslinjer i pulsen (J går en gång i timmen)
INTERVALL = 30.0
GENOMGANG = O.GENOMGANG_MIN          # 0,5 min – samma som i omloppsverifieringen
REGLERING = O.REKOMMENDERAD_VANDTID  # 3 min
OMVAG = 1.3
KMH = 25.0


def linjeprofil():
    return json.load(open(P / 'b4_omlopp_nyckeltal.json', encoding='utf-8'))['linjer']


def par_tabell(prof):
    rader = []
    for a, b in itertools.permutations(LINJER, 2):
        ta, tb = prof[a]['kortid_median'], prof[b]['kortid_median']
        idag = INTERVALL - REGLERING - ta
        b_klarar = INTERVALL - tb >= REGLERING
        puls = INTERVALL - GENOMGANG - ta if b_klarar else np.nan
        utan_puls = 2 * INTERVALL - ta - tb - GENOMGANG - REGLERING
        rader.append({'forlangs': a, 'partner': b, 't_forlangs': ta, 't_partner': tb,
                      'vandtid_idag': INTERVALL - ta, 'utrymme_idag': idag, 'utrymme_genomgaende': puls,
                      'utrymme_utan_puls': utan_puls, 'partner_klarar_reglering': b_klarar})
    return pd.DataFrame(rader)


def genomgaende_resor():
    zoner = list(pd.read_csv(P / 'a1_restider_min.csv', index_col=0).index)
    mon = N.monster()
    nat0 = N.Nat(mon, zoner)
    huvud = {}
    for m in mon:
        if m['linje'] in LINJER and (m['linje'] not in huvud or len(m['turer']) > len(huvud[m['linje']]['turer'])):
            huvud[m['linje']] = m
    fak = N.dagsfaktor(); ut = []
    for a, b in itertools.combinations(LINJER, 2):
        extra = []
        for x, y in ((a, b), (b, a)):
            mx, my = huvud[x], huvud[y]
            akt = np.concatenate([mx['akt'], my['akt']]); akt[len(mx['akt'])] += GENOMGANG
            extra.append({'linje': f'{x}{y}', 'stopp': mx['stopp'] + my['stopp'][1:],
                          'zoner': mx['zoner'] + my['zoner'][1:], 'akt': akt, 'turer': []})
        nat1 = N.Nat(mon + extra, zoner)
        j = N.jamfor(nat0, nat1)
        medel = lambda k: np.mean([j[p][k] for p in ('FM', 'EM')])
        ut.append({'par': f'{a}/{b}', 'direktresor_vardag': round(float(medel('resor_kortare_h') * fak), 1),
                   'sparade_resenarsminuter_vardag': round(float(-medel('resenarsminuter_h') * fak), 1)})
    return pd.DataFrame(ut)


def omraden(prof):
    """A3-områden utanför räckhåll: behövd tilläggstid per tur och om den ryms (i dag / genomgående)."""
    import s01_vagdragning as V
    behov = pd.read_csv(P / 'a3_behov_ny_linjestrackning.csv')
    geo = V.segmentgeometri()
    seg_linje = V.segment_linjer()
    rader = []
    for r in behov.itertuples():
        bast = None
        for (s0, s1), xy in geo.items():
            lin = [l for l in seg_linje[(s0, s1)] if l in C.STADSLINJER]
            if not lin:
                continue
            # avstånd punkt–polylinje
            p = np.array([r.x, r.y])
            for q0, q1 in zip(xy[:-1], xy[1:]):
                v = q1 - q0; L2 = float(v @ v)
                tt = 0.0 if L2 == 0 else float(np.clip((p - q0) @ v / L2, 0, 1))
                d = float(np.hypot(*(q0 + tt * v - p)))
                for l in lin:
                    if bast is None or d < bast[0] - 1e-6 or (abs(d - bast[0]) < 1e-6 and l < bast[1]):
                        bast = (d, l)
        d, l = bast
        behov_min = 2 * d * OMVAG / 1000 / KMH * 60 + 0.5
        if r.narmaste_hpl == 'Möckelö Strand':
            behov_min = 2 * 1.0 + 0.5                     # förslag 1b (förlängd Norrgårdsvägen)
        rader.append({'omrade': r.narmaste_hpl, 'inv': r.inv, 'x': r.x, 'y': r.y, 'linje': l, 'avstand_m': round(d),
                      'behov_min_per_tur': round(behov_min, 1)})
    df = pd.DataFrame(rader)
    utr = {l: (INTERVALL - REGLERING - prof[l]['kortid_median'] if l in LINJER else np.nan) for l in C.STADSLINJER}
    utr_g = {l: INTERVALL - GENOMGANG - prof[l]['kortid_median'] if l in LINJER else np.nan for l in C.STADSLINJER}
    df['utrymme_idag'] = df.linje.map(utr)
    df['utrymme_genomgaende'] = df.linje.map(utr_g)
    df['bedomning'] = np.where(df.behov_min_per_tur <= df.utrymme_idag, 'Ryms i dag',
                      np.where(df.behov_min_per_tur <= df.utrymme_genomgaende, 'Ryms med genomgående linje',
                               np.where(df.linje == 'J', 'Linje J (timtrafik) – prövas separat',
                                        'Kräver större omläggning')))
    return df


# ====================================================================== figur
def figur(par, resor, omr, prof):
    fig = plt.figure(figsize=(13.6, 9.4))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 0.92], height_ratios=[1.0, 0.85], wspace=0.30, hspace=0.38,
                          left=0.02, right=0.98, top=0.92, bottom=0.14)
    ax = fig.add_subplot(gs[:, 0])
    K.ny_karta((104900, 112100, 6680300, 6688100), ax=ax, titel='Områden utan hållplats inom 400 m – behövd tid per tur')
    K.rita_linjer(ax, lw=1.9, zorder=4)
    farg = {'Ryms i dag': '#2f9e44', 'Ryms med genomgående linje': '#1c5cab',
            'Kräver större omläggning': '#c0392b', 'Linje J (timtrafik) – prövas separat': '#7a776f'}
    for r in omr.itertuples():
        ax.scatter([r.x], [r.y], s=40 + r.inv * 0.9, marker='D', color=farg[r.bedomning], edgecolor='white',
                   lw=0.8, zorder=8, alpha=0.95)
    etik = [(f"{r.omrade} ({int(round(r.inv, -1))} inv.)\nlinje {r.linje}: +{str(r.behov_min_per_tur).replace('.', ',')} min/tur",
             (r.x, r.y), 90) for r in omr.sort_values('inv', ascending=False).itertuples()]
    K.placera_etiketter(ax, etik, fontsize=6.4, undvik=K.punkt_hinder(ax, omr.x, omr.y, px=9))
    h = [Line2D([], [], marker='D', ls='', color=c, markersize=7, label=k) for k, c in farg.items()]
    h += [Line2D([], [], color=C.FARG_LINJE[l], lw=2, label=f'Linje {l}') for l in C.STADSLINJER]
    ax.legend(handles=h, loc='upper left', bbox_to_anchor=(0.0, -0.01), ncol=3, fontsize=6.8, frameon=False,
              handlelength=1.6, columnspacing=1.4)
    K.ram(ax)

    # tidsutrymme per linje
    ax2 = fig.add_subplot(gs[0, 1])
    y = np.arange(len(LINJER))
    idag = [INTERVALL - REGLERING - prof[l]['kortid_median'] for l in LINJER]
    gen = []
    for l in LINJER:
        d = par[(par.forlangs == l) & par.partner_klarar_reglering]
        gen.append(float(d.utrymme_genomgaende.max()) if len(d) else np.nan)
    ax2.barh(y + 0.2, idag, height=0.36, color='#b9b4a8', label=f'Egen linje (≥ {REGLERING:g} min reglering)')
    ax2.barh(y - 0.2, gen, height=0.36, color='#1c5cab',
             label=f'Genomgående ({GENOMGANG:g} min uppehåll, reglering i andra halvan)'.replace('.', ','))
    for yy, a, b in zip(y, idag, gen):
        ax2.text(max(a, 0) + 0.1, yy + 0.2, f'{a:g}'.replace('.', ','), va='center', fontsize=7.5, color=K.TEXT)
        ax2.text(b + 0.1, yy - 0.2, f'{b:g}'.replace('.', ','), va='center', fontsize=7.5, color=K.TEXT)
    ax2.axvline(0, color='#52514e', lw=0.8)
    ax2.set_yticks(y); ax2.set_yticklabels([f"Linje {l} ({prof[l]['kortid_median']:.0f} min)" for l in LINJER], fontsize=8)
    ax2.invert_yaxis()
    ax2.set_xlabel('min per tur som linjen kan förlängas (30 min turintervall, puls i centrum)', fontsize=7.5)
    ax2.set_xlim(-1.5, 8); ax2.tick_params(labelsize=7.5)
    ax2.grid(axis='x', color='#e6e4de', lw=0.6); ax2.set_axisbelow(True)
    for s in ['top', 'right']:
        ax2.spines[s].set_visible(False)
    ax2.legend(loc='upper left', bbox_to_anchor=(0.0, -0.16), fontsize=6.8, frameon=False, ncol=1)
    ax2.set_title('Tidsutrymme för längre linje utan fler bussar', loc='left', fontsize=10, fontweight='bold')

    # direktresor per par
    ax3 = fig.add_subplot(gs[1, 1])
    r = resor.sort_values('direktresor_vardag', ascending=True)
    ax3.barh(np.arange(len(r)), r.direktresor_vardag, color='#7fb0ec', height=0.6)
    for i, (v, m) in enumerate(zip(r.direktresor_vardag, r.sparade_resenarsminuter_vardag)):
        ax3.text(v + 0.1, i, f'{v:.1f} resor · {m:.0f} min sparade'.replace('.', ','), va='center', fontsize=7, color=K.TEXT)
    ax3.set_yticks(np.arange(len(r))); ax3.set_yticklabels([f'{p} genomgående' for p in r.par], fontsize=8)
    ax3.set_xlim(0, max(r.direktresor_vardag.max() * 1.6, 1))
    ax3.set_xlabel('resor per vardag som slipper byte i centrum (sommarnivå)', fontsize=7.5)
    ax3.tick_params(labelsize=7.5); ax3.grid(axis='x', color='#e6e4de', lw=0.6); ax3.set_axisbelow(True)
    for s in ['top', 'right']:
        ax3.spines[s].set_visible(False)
    ax3.set_title('Resor som blir direkta', loc='left', fontsize=10, fontweight='bold')
    fig.suptitle('Sammanslagning av linjer – genomgående linjer i centrum', x=0.01, ha='left', fontsize=12.5,
                 fontweight='bold')
    ut = C.KARTOR / 'b4_8_sammanslagning.png'
    fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


def main():
    prof = linjeprofil()
    par = par_tabell(prof)
    resor = genomgaende_resor()
    omr = omraden(prof)
    par.to_csv(P / 'b4_sammanslagning_par.csv', index=False)
    omr.to_csv(P / 'b4_sammanslagning_omraden.csv', index=False)
    res = {'parametrar': {'intervall': INTERVALL, 'genomgang_min': GENOMGANG, 'reglering_min': REGLERING},
           'par': par.round(2).to_dict('records'), 'genomgaende_resor': resor.to_dict('records'),
           'omraden': omr.drop(columns=['x', 'y']).round(1).to_dict('records')}
    with open(P / 'b4_sammanslagning.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=float)
    print(par.round(1).to_string()); print(resor.to_string()); print(omr.drop(columns=['x', 'y']).to_string())
    print(figur(par, resor, omr, prof))


if __name__ == '__main__':
    main()
