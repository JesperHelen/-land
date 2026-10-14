# -*- coding: utf-8 -*-
"""B5 – Grov ekonomisk kalkyl (överslag) för linjeförslagen.

Driftkostnad per år = Δfordon × fordonskostnad + Δfordonstimmar × timkostnad + Δfordonskm × km-kostnad.
  * Δfordon, Δomloppstid (fordonstimmar) och Δkm per vardag kommer från omloppsverifieringen (b4_paket.json).
  * Årsvolym: VARDAGAR vardagar med samma tidtabell som typvardagen. Lördagstrafiken (5 turer per linje N, S, V
    och Ö enligt GTFS) påverkas bara genom km. GTFS-underlaget täcker hösten 2026; helårsvolymen är ett antagande.
  * Enhetskostnader (EUR, prisnivå 2026, tre nivåer): orienterande värden från Trivector (2023), Trafikeringskostnader
    för buss 2019 och 2045 (Trafikverket), tätortstrafik 2019 – ca 0,65 MSEK per fordon och år och ca 480 kr per
    fordonstimme – omräknade (10,6 SEK/EUR) och uppräknade ca 15 %. Ska ersättas med avtalspriserna i Ålands
    landskapsregerings trafikavtal när de finns tillgängliga.
  * Investeringar (engångs): nya hållplatslägen. Förlängningen av Norrgårdsvägen kostnadsberäknas inte; i stället
    redovisas vilken vägkostnad som motsvarar nuvärdet av merkostnaden för 1a (break-even).
Utdata: data/processed/b5_kalkyl.json, b5_kalkyl.csv, output/kartor/b5_1_kalkyl.png
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import kartlib as K  # noqa: E402

P = C.PROCESSED
VARDAGAR = 250
LORDAGAR = 52
LORDAGSTURER = 5
NIVAER = ['låg', 'bas', 'hög']
ENHET = {   # EUR, 2026
    'fordon_per_ar': {'låg': 45_000, 'bas': 60_000, 'hög': 75_000},
    'per_fordonstimme': {'låg': 42, 'bas': 50, 'hög': 58},
    'per_km': {'låg': 0.7, 'bas': 0.9, 'hög': 1.2},
    'ny_hallplats': {'låg': 8_000, 'bas': 15_000, 'hög': 30_000},
}
KALKYLRANTA = 0.035
KALKYLTID = 20
SCEN = ['1a', '1a_del', '1b_VÖ', '2', '3', 'paket_A', 'paket_A_robust', 'paket_B']
KORT = {'1a': '1a Möckelö Strand, dagens gator – alla turer (6 bussar)',
        '1a_del': '1a – bara de 8 turer som ryms',
        '1b_VÖ': '1b Möckelö Strand, förlängd Norrgårdsvägen',
        '2': '2 N2 på linje Ö', '3': '3 Linje N via Bo-Bil',
        'paket_A': 'Paket A: 1b, 2, 3', 'paket_A_robust': 'Paket A robust: 1b på 15 av 20 turer, 2, 3',
        'paket_B': 'Paket B: 1a, 2, 3'}


def lordag_km(atg_ids, atg_km):
    linje = {'1a': 'V', '1b': 'V', '2': 'Ö', '3': 'N'}
    return sum(LORDAGSTURER * atg_km[a] for a in atg_ids if a in linje)


def main():
    paket = json.load(open(P / 'b4_paket.json', encoding='utf-8'))
    forslag = json.load(open(P / 'b4_forslag.json', encoding='utf-8'))['forslag']
    atg_km = {a: forslag[a]['km_per_tur'] for a in forslag}
    rader, res = [], {}
    for sid in SCEN:
        v = paket[sid]; d = v['forandring_omlopp']
        km_ar = d['km'] * VARDAGAR + lordag_km(v['atgarder'], atg_km) * LORDAGAR
        h_ar = d['omloppstid_h'] * VARDAGAR
        nya = len([a for a in v['atgarder'] if a in ('1a', '1b', '2')])
        r = {'scenario': sid, 'namn': KORT[sid], 'delta_fordon': d['fordon'], 'delta_fordonstimmar_ar': round(h_ar),
             'delta_km_ar': round(km_ar), 'nya_hallplatser': nya,
             'ny_tackning_inv': v['forandring_invanare_mariehamn']['ny_tackning'],
             'battre_inv': v['forandring_invanare_mariehamn']['battre_klass']}
        for n in NIVAER:
            fo = d['fordon'] * ENHET['fordon_per_ar'][n]
            ti = h_ar * ENHET['per_fordonstimme'][n]
            km = km_ar * ENHET['per_km'][n]
            r[f'fordon_{n}'] = round(fo); r[f'tid_{n}'] = round(ti); r[f'km_{n}'] = round(km)
            r[f'drift_ar_{n}'] = round(fo + ti + km)
            r[f'investering_{n}'] = nya * ENHET['ny_hallplats'][n]
        r['drift_per_battre_inv_bas'] = round(r['drift_ar_bas'] / r['battre_inv']) if r['battre_inv'] else None
        rader.append(r)
    df = pd.DataFrame(rader)
    an = (1 - (1 + KALKYLRANTA) ** -KALKYLTID) / KALKYLRANTA
    b = df.set_index('scenario')
    diff = {n: float(b.at['1a', f'drift_ar_{n}'] - b.at['1b_VÖ', f'drift_ar_{n}']) for n in NIVAER}
    res = {'antaganden': {'vardagar_per_ar': VARDAGAR, 'lordagar_per_ar': LORDAGAR, 'lordagsturer_per_linje': LORDAGSTURER,
                          'enhetskostnader_eur_2026': ENHET, 'kalkylranta': KALKYLRANTA, 'kalkyltid_ar': KALKYLTID,
                          'nuvardesfaktor': round(an, 2)},
           'scenarier': df.to_dict('records'),
           'break_even_vagforlangning': {n: {'merkostnad_1a_jfr_1b_per_ar': round(diff[n]),
                                             'nuvarde_eur': round(diff[n] * an)} for n in NIVAER}}
    df.to_csv(P / 'b5_kalkyl.csv', index=False)
    with open(P / 'b5_kalkyl.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=float)
    print(df[['scenario', 'delta_fordon', 'delta_fordonstimmar_ar', 'delta_km_ar', 'drift_ar_låg', 'drift_ar_bas',
              'drift_ar_hög', 'investering_bas', 'drift_per_battre_inv_bas']].to_string())
    print(res['break_even_vagforlangning'])
    print(figur(df, res))


def figur(df, res):
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(14.0, 5.6), gridspec_kw={'width_ratios': [1.25, 1.0], 'wspace': 0.36})
    d = df.set_index('scenario').loc[SCEN]
    y = np.arange(len(d))
    delar = [('fordon_bas', 'Fordon (kapital, försäkring)', '#3d4a57'), ('tid_bas', 'Fordonstimmar (förare)', '#7fb0ec'),
             ('km_bas', 'Fordonskilometer (energi, underhåll)', '#f28e2b')]
    vanster_pos = np.zeros(len(d)); vanster_neg = np.zeros(len(d))
    for k, lbl, f in delar:
        v = d[k].to_numpy() / 1000
        start = np.where(v >= 0, vanster_pos, vanster_neg)
        ax.barh(y, v, left=start, height=0.56, color=f, label=lbl)
        vanster_pos += np.where(v >= 0, v, 0); vanster_neg += np.where(v < 0, v, 0)
    tot = d.drift_ar_bas.to_numpy() / 1000
    a_, b_ = d['drift_ar_låg'].to_numpy() / 1000, d['drift_ar_hög'].to_numpy() / 1000
    lo, hi = np.minimum(a_, b_), np.maximum(a_, b_)
    ax.errorbar(tot, y, xerr=[tot - lo, hi - tot], fmt='none', ecolor='#1f1f1e', elinewidth=0.8, capsize=3, zorder=5)
    for yy, t, h_ in zip(y, tot, hi):
        ax.text(max(h_, t, 0) + 4, yy, f'{t:+,.0f} k€/år'.replace(',', ' ').replace('-', '−'), va='center', fontsize=7.6,
                color=K.TEXT)
    ax.axvline(0, color='#52514e', lw=0.8)
    ax.set_yticks(y); ax.set_yticklabels([KORT[s].replace(': ', ':\n').replace(' – ', '\n') for s in d.index], fontsize=7.6)
    ax.invert_yaxis(); ax.set_xlim(-15, 320)
    ax.set_xlabel('förändrad driftkostnad, tusen euro per år (bas; streck = låg–hög)', fontsize=8)
    ax.tick_params(labelsize=7.5); ax.grid(axis='x', color='#e6e4de', lw=0.6); ax.set_axisbelow(True)
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    ax.legend(loc='upper left', bbox_to_anchor=(0, -0.12), ncol=3, fontsize=7.2, frameon=False)
    ax.set_title('Driftkostnad jämfört med i dag', loc='left', fontsize=10, fontweight='bold')

    ax2.axis('off')
    be = res['break_even_vagforlangning']
    tkort = {'1a': '1a alla turer', '1a_del': '1a 8 turer', '1b_VÖ': '1b', '2': '2 N2', '3': '3 Bo-Bil',
             'paket_A': 'Paket A', 'paket_A_robust': 'Paket A robust', 'paket_B': 'Paket B'}
    cell = [[tkort[s], f"{d.at[s, 'delta_fordon']:+d}", f"{d.at[s, 'delta_fordonstimmar_ar']:+,d}".replace(',', ' '),
             f"{d.at[s, 'delta_km_ar']:+,d}".replace(',', ' '), f"{d.at[s, 'investering_bas'] / 1000:,.0f}".replace(',', ' '),
             '–' if d.at[s, 'drift_per_battre_inv_bas'] is None or pd.isna(d.at[s, 'drift_per_battre_inv_bas'])
             else f"{d.at[s, 'drift_per_battre_inv_bas']:,.0f}".replace(',', ' ')] for s in SCEN]
    cell = [[r[0]] + [c.replace('-', '−') for c in r[1:]] for r in cell]
    tb = ax2.table(cellText=cell, colLabels=['Förslag', 'Bussar', 'Fordons-\ntimmar/år', 'Fordons-\nkm/år',
                                             'Hållplats\nk€', 'Drift €/år\nper inv. som\nfår det bättre'],
                   loc='upper left', cellLoc='right', colLoc='right', colWidths=[0.19, 0.1, 0.16, 0.16, 0.13, 0.22])
    tb.auto_set_font_size(False); tb.set_fontsize(7.2); tb.scale(1, 1.55)
    for (r_, c_), ce in tb.get_celld().items():
        ce.set_edgecolor('#e0ded7'); ce.set_linewidth(0.5)
        if c_ == 0:
            ce.get_text().set_ha('left'); ce._loc = 'left'
        if r_ == 0:
            ce.set_facecolor('#f1efe9'); ce.get_text().set_fontweight('bold'); ce.set_height(ce.get_height() * 2.1)
    dec = lambda x: f'{x:.1f}'.replace('.', ',')
    txt = (r'$\bf{Break\text{-}even\ för\ förlängd\ Norrgårdsvägen}$' + '\n'
           f"Merkostnaden för 1a jämfört med 1b är {be['bas']['merkostnad_1a_jfr_1b_per_ar'] / 1000:.0f} k€ per år (bas).\n"
           f"Nuvärde över {KALKYLTID} år ({dec(KALKYLRANTA * 100)} % kalkylränta): "
           f"{dec(be['låg']['nuvarde_eur'] / 1e6)}–{dec(be['hög']['nuvarde_eur'] / 1e6)} M€.\n"
           'En vägförlängning som kostar mindre än så är billigare än att\nköra 1a med en extra buss.')
    ax2.text(0.0, 0.02, txt, transform=ax2.transAxes, fontsize=7.6, color=K.TEXT, va='bottom',
             linespacing=1.5, bbox=dict(boxstyle='round,pad=0.5', facecolor='#f7f6f2', edgecolor='#d6d5d0', lw=0.6))
    ax2.set_title('Nyckeltal per förslag', loc='left', fontsize=10, fontweight='bold')
    fig.suptitle('Överslagskalkyl – förändrad driftkostnad per år (EUR, prisnivå 2026)', x=0.01, ha='left',
                 fontsize=12, fontweight='bold')
    ut = C.KARTOR / 'b5_1_kalkyl.png'
    fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


if __name__ == '__main__':
    main()
