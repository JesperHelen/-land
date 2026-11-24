# -*- coding: utf-8 -*-
"""B5 – Kostnad för utredningsalternativen, uttryckt i fordonskilometer och antal fordon.

Beställaren redovisar kostnaden som
  * förändrade fordonskilometer (per vardag och per år) och
  * om linjen kräver fler fordon än i dag för att kunna hållas.
Inga eurobelopp räknas fram.

  * Δfordon och Δkm per vardag kommer från omloppsverifieringen (b4_systemeffekter.json). Varje UA för sig.
  * Årsvolym: VARDAGAR vardagar med typvardagens tidtabell, plus lördagstrafiken (5 turer per linje enligt GTFS)
    med samma andel turer via den nya sträckan som på vardagar. GTFS-underlaget täcker hösten 2026, så
    helårsvolymen är ett antagande.
  * UA 4: extra V-turer via flygplatsen för de flyg som dagens tidtabell inte når (b4_ua.flyg_extraturer).
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
SCEN = ['1a', '1a_ryms', '1a_VO', '1b', '2', '3', '4', '4_VO', '4_VO_sol', '4_Y', '5', '5_ryms', '5_N']
HUVUD = {'1a_VO', '1b', '2', '3', '4_VO', '5'}
EXTRA = 'flyg_extra'


def kort(sid, v):
    n, tot = v['turer'], v['turer_tot']
    return {'1a': 'UA 1a dagens vägar – alla turer',
            '1a_ryms': f'UA 1a dagens vägar – dagens tidtabell ({n} av {tot} turer)',
            '1a_VO': f'UA 1a ★ dagens vägar – V och Ö sammanslagna ({n} av {tot} turer)',
            '1b': f'UA 1b ★ förlängd Norrgårdsvägen – V och Ö sammanslagna ({n} av {tot} turer)',
            '2': 'UA 2 ★ N2 på linje Ö', '3': 'UA 3 ★ linje N via Bo-Bil',
            '4': 'UA 4 flygplatsen – alla turer',
            '4_VO': f'UA 4 ★ flygplatsen – V och Ö sammanslagna ({n} av {tot} turer)',
            '4_VO_sol': f'UA 4 flygplatsen – dito + Solberget indragen ({n} av {tot})',
            '4_Y': f'UA 4Y flygturerna ({n} av {tot}), V och Ö sammanslagna',
            '5': f'UA 5 ★ svängen till linje V – V och Ö sammanslagna ({n} av {tot} V-turer)',
            '5_ryms': f'UA 5 svängen till linje V – dagens drift ({n} av {tot} V-turer)',
            '5_N': 'UA 5 variant – bara linje N rakt på'}[sid]


KORT_FIG = {'1a': 'UA 1a alla turer', '1a_ryms': 'UA 1a dagens tidtabell', '1a_VO': 'UA 1a ★ Västra + Östra',
            '1b': 'UA 1b ★ Västra + Östra', '2': 'UA 2 ★', '3': 'UA 3 ★', '4': 'UA 4 alla turer', '4_VO': 'UA 4 ★ Västra + Östra',
            '4_VO_sol': 'UA 4 + Solberget indragen', '4_Y': 'UA 4Y flygturerna',
            EXTRA: 'UA 4 extra turer för flygen', '5': 'UA 5 ★ Västra + Östra', '5_ryms': 'UA 5 dagens drift', '6': 'UA 6 Norra båda riktningar', '7': 'UA 7 kväll: Norra båda håll',
            '5_N': 'UA 5 bara Norra rakt på'}


def main():
    se = json.load(open(P / 'b4_systemeffekter.json', encoding='utf-8'))
    uas = json.load(open(P / 'b4_ua.json', encoding='utf-8'))
    rader = []
    for sid in SCEN:
        v = se[sid]; d = v['forandring_omlopp']; fid = v['ua']
        andel = v['turer'] / max(v['turer_tot'], 1)
        km_ar = d['km'] * VARDAGAR + LORDAGSTURER * uas['ua'][fid]['km_per_tur'] * andel * LORDAGAR
        rader.append({'scenario': sid, 'namn': kort(sid, v), 'huvudalternativ': sid in HUVUD,
                      'fordon': v['omlopp']['fordon'], 'delta_fordon': d['fordon'],
                      'fordonskm_vardag': round(v['omlopp']['km'], 1), 'delta_km_vardag': round(d['km'], 1),
                      'delta_km_ar': int(round(km_ar, -2)),
                      'ny_tackning_inv': v['forandring_invanare_mariehamn']['ny_tackning'],
                      'battre_inv': v['forandring_invanare_mariehamn']['battre_klass']})
    ex = uas['flygplatsen']['extraturer']
    km_ex = sum(e['km'] for e in ex)
    rader.append({'scenario': EXTRA, 'namn': 'UA 4 extra turer för flyg som dagens tidtabell inte når',
                  'huvudalternativ': False, 'fordon': se['idag']['omlopp']['fordon'], 'delta_fordon': 0,
                  'fordonskm_vardag': round(se['idag']['omlopp']['km'] + km_ex, 1), 'delta_km_vardag': round(km_ex, 1),
                  'delta_km_ar': int(round(km_ex * VARDAGAR, -2)), 'ny_tackning_inv': 0, 'battre_inv': 0})
    if (P / 'b4_ua6_norra.json').exists():                 # UA 6: Norra även moturs (utanför ramen, +1 fordon)
        u6 = json.load(open(P / 'b4_ua6_norra.json', encoding='utf-8'))
        rader.append({'scenario': '6', 'namn': 'UA 6 linje Norra i båda riktningarna (+22 turer moturs)',
                      'huvudalternativ': False, 'fordon': se['idag']['omlopp']['fordon'] + u6['fordon_extra'],
                      'delta_fordon': u6['fordon_extra'],
                      'fordonskm_vardag': round(se['idag']['omlopp']['km'] + u6['fordonskm_vardag'], 1),
                      'delta_km_vardag': u6['fordonskm_vardag'],
                      'delta_km_ar': int(round(u6['fordonskm_vardag'] * VARDAGAR
                                               + LORDAGSTURER * u6['km_varv'] * LORDAGAR, -2)),
                      'ny_tackning_inv': 0, 'battre_inv': u6['inv_lyft_till_minst_30']})
    if (P / 'b4_ua7_kvall.json').exists():                 # UA 7: Västra och Östra anropsstyrda efter kl. 18
        u7 = json.load(open(P / 'b4_ua7_kvall.json', encoding='utf-8'))
        rader.append({'scenario': '7', 'namn': 'UA 7 kvällstrafik: Norra i båda riktningarna efter kl. 18 i stället för Västra',
                      'huvudalternativ': False, 'fordon': se['idag']['omlopp']['fordon'], 'delta_fordon': 0,
                      'fordonskm_vardag': round(se['idag']['omlopp']['km'] + u7['fordonskm_vardag'], 1),
                      'delta_km_vardag': u7['fordonskm_vardag'], 'delta_km_ar': u7['fordonskm_ar'],
                      'ny_tackning_inv': 0, 'battre_inv': 0})
    df = pd.DataFrame(rader)
    res = {'antaganden': {'vardagar_per_ar': VARDAGAR, 'lordagar_per_ar': LORDAGAR,
                          'lordagsturer_per_linje': LORDAGSTURER},
           'idag': {'fordon': se['idag']['omlopp']['fordon'], 'fordonskm_vardag': se['idag']['omlopp']['km']},
           'scenarier': df.to_dict('records'),
           'flyg_extraturer': [{'flyg': e['flyg'], 'avg_centrum': e['avg_centrum'], 'km': e['km'],
                                'omlopp': e['omlopp'], 'inom_omloppet': e['inom_omloppet']} for e in ex]}
    df.to_csv(P / 'b5_kalkyl.csv', index=False)
    with open(P / 'b5_kalkyl.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=float)
    print(df[['scenario', 'fordon', 'delta_fordon', 'delta_km_vardag', 'delta_km_ar']].to_string())
    print(figur(df))


def figur(df):
    ordning = ['1a', '1a_ryms', '1a_VO', '1b', '2', '3', '4', '4_VO', '4_VO_sol', '4_Y', EXTRA, '5', '5_ryms', '5_N', '6', '7']
    ordning = [o for o in ordning if o in set(df.scenario)]
    d = df.set_index('scenario').loc[ordning]
    fig, ax = plt.subplots(figsize=(8.6, 6.2))
    y = np.arange(len(d))
    ROD, BLA = '#c0392b', '#3987e5'
    farg = [ROD if f > 0 else BLA for f in d.delta_fordon]
    ax.barh(y, d.delta_km_vardag, height=0.58, color=farg)
    for yy, (km, f) in enumerate(zip(d.delta_km_vardag, d.delta_fordon)):
        t = f'{km:+.0f} km'.replace('-', '−').replace('+0 km', '±0 km').replace('−0 km', '±0 km')
        if f > 0:
            t += f'  ·  +{f} fordon'
        ax.text(max(km, 0) + 1.2, yy, t, va='center', fontsize=7.2, color=ROD if f > 0 else K.TEXT)
    ax.axvline(0, color='#52514e', lw=0.8)
    ax.set_yticks(y); ax.set_yticklabels([KORT_FIG[s] for s in d.index], fontsize=7.6)
    ax.invert_yaxis(); ax.set_xlim(min(-8, d.delta_km_vardag.min() * 1.3), max(75, d.delta_km_vardag.max() * 1.25))
    ax.set_xlabel('Fordonskilometer per vardag jämfört med i dag', fontsize=8)
    ax.tick_params(labelsize=7.5); ax.grid(axis='x', color='#e6e4de', lw=0.6); ax.set_axisbelow(True)
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    ax.legend(handles=[Patch(facecolor=BLA, label='Ryms med dagens fordon'),
                       Patch(facecolor=ROD, label='Kräver fler fordon')],
              loc='lower right', fontsize=7, frameon=True, facecolor='white', edgecolor='#e0ded7')
    ax.set_title('Fordonskilometer och fordon jämfört med i dag')
    ut = C.KARTOR / 'b5_1_kalkyl.png'
    K.fullnamn_fig(fig); fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


if __name__ == '__main__':
    main()
