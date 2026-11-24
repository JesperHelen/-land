# -*- coding: utf-8 -*-
"""Målpunktskarta: skolor, arbetsplatsområden, sjukhus, köpcentrum, hamnar och fritidsanläggningar i Mariehamn.

Underlag: OpenStreetMap via OpenMapTiles-vektorplattor (lagren poi och landuse, zoom 14; bakgrundskarta.osm).
  * Skolor: poi school (utom förskolor/daghem), college, university; ytor landuse school/college/university.
  * Arbetsplatsområden: ytor landuse industrial och commercial; myndigheter (poi office/government).
  * Sjukhus: poi hospital (utom kliniker); yta landuse hospital.
  * Köpcentrum: poi shop/mall; ytor landuse retail.
  * Hamnar: poi ferry_terminal och harbor (gästhamnar/marinor).
  * Fritidsanläggningar: poi sports_centre, stadium, swimming_pool, ice_rink; yta landuse stadium.
Utdata: output/kartor/a1_9_malpunkter.png, output/data/malpunkter.csv
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import kartlib as K  # noqa: E402
import bakgrundskarta as BK  # noqa: E402

UTS = (105700, 109700, 6680200, 6687400)
KAT = {   # kategori: (färg, markör, storlek)
    'Skolor': ('#e8590c', 's', 46),
    'Sjukhus': ('#c92a2a', 'P', 120),
    'Köpcentrum': ('#7048e8', 'D', 60),
    'Hamnar': ('#1971c2', 'v', 70),
    'Fritidsanläggningar': ('#2f9e44', '^', 60),
    'Arbetsplatsområden': ('#8c6d46', 'o', 22),
}
YTOR = {'Arbetsplatsområden': (('industrial', 'commercial'), '#c9a97c'), 'Köpcentrum': (('retail',), '#c5b8f2'),
        'Skolor': (('school', 'college', 'university'), '#f7c59f'), 'Sjukhus': (('hospital',), '#f2a7a7'),
        'Fritidsanläggningar': (('stadium',), '#b7e0b0')}
ETIKETT = {'Ålands centralsjukhus', 'Maxinge', 'Strandnäs Skola', 'Ytternäs skola', 'Övernäs skola', 'Ålands lyceum',
           'Ålands yrkesgymnasium', 'Högskolan på Åland', 'Västerhamn (färjeterminal)', 'Medimar', 'MSF Gästhamn', 'Lervikshamnen',
           'ÅSS Marina', 'Wiklöf Holding Arena', 'Baltichallen', 'Mariebad', 'Islandia', 'Bollhalla', 'Ålandstravet',
           'Backebergs sportfält', 'Centrumgallerior', 'Självstyrelsegården'}


def kategori(r):
    c, s = r['class'], r['subclass']
    if c in ('school', 'college', 'university') and s != 'kindergarten' and 'daghem' not in str(r['name']).lower():
        return 'Skolor'
    if c == 'hospital' and s == 'hospital':
        return 'Sjukhus'
    if c == 'shop' and s == 'mall':
        return 'Köpcentrum'
    if c in ('ferry_terminal', 'harbor'):
        return 'Hamnar'
    if c in ('sports_centre', 'stadium', 'swimming_pool', 'ice_rink'):
        return 'Fritidsanläggningar'
    if c == 'office' and s == 'government':
        return 'Arbetsplatsområden'
    return None


def malpunkter():
    BK.LAGER = tuple(dict.fromkeys(BK.LAGER + ('poi',)))
    BK.osm.cache_clear()
    o = BK.osm(UTS, 14)
    p = o['poi'].copy()
    p['kategori'] = p.apply(kategori, axis=1)
    p = p[p.kategori.notna()].copy()
    p['x'] = p.geometry.centroid.x; p['y'] = p.geometry.centroid.y
    p = p[p.x.between(UTS[0], UTS[1]) & p.y.between(UTS[2], UTS[3])]
    p['nyckel'] = p.name.fillna('') + p.x.round(-2).astype(str) + p.y.round(-2).astype(str)
    p = p.drop_duplicates(['kategori', 'nyckel'])
    p = p[~(p.name.isna() & p.kategori.isin(['Skolor', 'Hamnar']) & p.duplicated(['kategori'], keep=False)
            & (p.groupby('kategori').x.transform('size') > 0) & False)]
    # gallerierna i centrum (Sittkoff, Zeipels, Telegrafen, Torggallerian) som en målpunkt
    cen = p[(p.kategori == 'Köpcentrum') & p.name.isin(['Sittkoff', 'ZEIPELS', 'Telegrafen', 'Torggallerian'])]
    if len(cen):
        rad = cen.iloc[[0]].copy(); rad['name'] = 'Centrumgallerior'; rad['x'] = cen.x.mean(); rad['y'] = cen.y.mean()
        p = pd.concat([p.drop(cen.index), rad])
    # hamnar: färjeterminalerna i Västerhamn som en målpunkt, gästhamnar bara med namn
    ft = p[(p.kategori == 'Hamnar') & (p.subclass == 'ferry_terminal')]
    if len(ft):
        rad = ft.iloc[[0]].copy(); rad['name'] = 'Västerhamn (färjeterminal)'; rad['x'] = ft.x.mean(); rad['y'] = ft.y.mean()
        p = pd.concat([p.drop(ft.index), rad])
    p = p[~((p.kategori == 'Hamnar') & (p.subclass != 'ferry_terminal') & p.name.isna())]
    p.loc[(p.kategori == 'Sjukhus') & p.name.isna(), 'name'] = 'Medimar'
    lu = o['landuse']
    ut = p[['kategori', 'class', 'subclass', 'name', 'x', 'y']].sort_values(['kategori', 'name'])
    return ut, lu


def figur(p, lu):
    fig, ax = plt.subplots(figsize=(8.6, 12.4))
    K.ny_karta(UTS, ax=ax, titel='Målpunkter i Mariehamn')
    for kat, (klasser, farg) in YTOR.items():
        y = lu[lu['class'].isin(klasser) & lu.geom_type.isin(['Polygon', 'MultiPolygon'])]
        if len(y):
            y.plot(ax=ax, color=farg, alpha=0.75 if kat == 'Arbetsplatsområden' else 0.6, linewidth=0, zorder=1.2)
    K.rita_linjer(ax, alpha=0.35, lw=1.1, zorder=2, etikett=False)
    for kat, (farg, mk, s) in KAT.items():
        d = p[p.kategori == kat]
        storlek = np.where(d.subclass.eq('marina'), s * 0.75, np.where(d.subclass.eq('ferry_terminal'), s * 1.5, s))
        ax.scatter(d.x, d.y, s=storlek, marker=mk, color=farg, edgecolor='white', lw=0.7, zorder=8)
    namn = p[p.name.isin(ETIKETT)].drop_duplicates('name')
    namn = namn.assign(etikett=namn.name.replace({'Strandnäs Skola': 'Strandnäs skola', 
                                                    'Wiklöf Holding Arena': 'Idrottsparken'}))
    prio = ['Sjukhus', 'Köpcentrum', 'Skolor', 'Hamnar', 'Fritidsanläggningar', 'Arbetsplatsområden']
    namn['prio'] = namn.kategori.map({k: i for i, k in enumerate(prio)})
    hinder = K.punkt_hinder(ax, p.x, p.y, px=5)
    K.placera_etiketter(ax, [(r.etikett, (r.x, r.y), 40) for r in namn.sort_values('prio').itertuples()],
                        fontsize=6.3, undvik=hinder)
    hnd = [Line2D([], [], marker=mk, ls='', markerfacecolor=f, markeredgecolor='white', markersize=8, label=k)
           for k, (f, mk, _) in KAT.items() if k != 'Arbetsplatsområden']
    hnd += [Patch(facecolor=YTOR['Arbetsplatsområden'][1], label='Arbetsplatsområden (industri, kontor)'),
            Patch(facecolor=YTOR['Köpcentrum'][1], label='Handelsområden')]
    K.teckenforklaring(ax, hnd, loc='upper left')
    K.ram(ax)
    return K.spara(fig, 'a1_9_malpunkter.png')


if __name__ == '__main__':
    p, lu = malpunkter()
    ut = C.ROT / 'output' / 'data'; ut.mkdir(parents=True, exist_ok=True)
    p.round(0).to_csv(ut / 'malpunkter.csv', index=False)
    print(p.groupby('kategori').size().to_dict())
    print(figur(p, lu))
