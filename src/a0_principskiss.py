# -*- coding: utf-8 -*-
"""Principskiss över stadstrafikens linjenät i dag: grova drag och körriktningar (schematisk, ej skalenlig).

Linjedragningen följer hållplatsföljderna i GTFS (vanligaste turmönstret per linje):
  Västra: Centrum – Ålandsplan – Tekniska verken – Västra macken – Sviby bro – Lönnhagsvägen – Möckelö Strand och
          tillbaka till Lönnhagsvägen – Posten – Källarvägen – Dalkullavägen – Åsvägen – Västra macken – Centrum.
  Östra:  Centrum – Nabben – Kalmsta – Solberget – Kalmarnäs vändplan och tillbaka – Nabben – Sjukhuset –
          Västra macken – Centrum (skolturer via Strandnäs skola).
  Norra:  Centrum – Polishuset – Doktorsvägen – Maxinge – Bolstavägen – Hindersbölevägen – Nabben – Sjukhuset –
          Cedersvägen – Yrkesgymnasiet – Norragatan – Centrum (enkelriktad slinga).
  Södra:  Centrum – Torget – Hamnterminalen – Ytternäs skola – Lervik – Övernäsgården – Stadshuset – Centrum.
  Järsö:  Centrum – Torget – Ytternäs skola – Lervik – Järsö och tillbaka via Övernäs skola – Norragatan – Centrum.
Utdata: output/kartor/a0_principskiss.png
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import kartlib as K  # noqa: E402

F = C.FARG_LINJE
# Noder (x, y) i skissens koordinater (y uppåt)
NOD = {'Möckelö': (0.8, 6.2), 'Lönnhagen': (2.6, 8.6), 'Posten': (2.6, 12.4), 'Sviby': (4.4, 12.4),
       'Sjukhuset': (4.6, 8.6), 'Maxinge': (5.1, 12.6), 'Norra knut': (5.1, 10.6), 'Hindersböle': (7.3, 9.9),
       'Nabben': (7.7, 8.6), 'Strandnäs': (7.0, 8.6), 'Solberget': (10.2, 9.0), 'Kalmarnäs': (10.2, 6.2),
       'Yrkesgymnasiet': (4.3, 6.4), 'Centrum': (5.6, 5.5), 'Hamnterminalen': (4.3, 3.6), 'Ytternäs': (5.4, 1.6),
       'Östernäs': (6.5, 2.5), 'S-mark': (6.5, 3.9), 'Lervik': (5.4, 0.4), 'Järsö': (5.4, -0.6)}


def linje(ax, pts, farg, pilar='en', lw=4.2, ls='-', steg=None, z=4):
    """Ritar en linje genom punkterna med vit kontur och pilar mitt på varje delsträcka.
    pilar: 'en' (körriktningen = punkternas ordning), 'bada' (dubbelpil) eller None."""
    xy = np.array(pts, float)
    ax.plot(xy[:, 0], xy[:, 1], color=farg, lw=lw, ls=ls, solid_capstyle='round', solid_joinstyle='round', zorder=z,
            path_effects=[K.pe.Stroke(linewidth=lw + 2.6, foreground='white'), K.pe.Normal()])
    if not pilar:
        return
    for a, b in zip(xy[:-1], xy[1:]):
        L = np.hypot(*(b - a))
        if L < 0.95:
            continue
        n = max(1, int(L // 2.6)) if steg is None else steg
        u = (b - a) / L; v = np.array([-u[1], u[0]])
        for k in range(n):
            m = a + (b - a) * (k + 1) / (n + 1)
            riktningar = (1, -1) if pilar == 'bada' else (1,)
            for r in riktningar:
                c = m + (0.2 * r * u if pilar == 'bada' else 0)
                spets = c + r * u * 0.2; bas = c - r * u * 0.14
                tri = np.array([spets, bas + v * 0.17, bas - v * 0.17])
                ax.add_patch(plt.Polygon(tri, closed=True, facecolor=farg, edgecolor='white', lw=1.0,
                                         joinstyle='miter', zorder=z + 0.5))


def etikett(ax, xy, text, dx=0.0, dy=0.0, ha='left'):
    x, y = xy
    t = ax.text(x + dx, y + dy, text, fontsize=8.2, ha=ha, va='center', zorder=12, color=K.TEXT,
                bbox=dict(boxstyle='round,pad=0.32,rounding_size=0.35', facecolor='white', edgecolor='#2b2b2b', lw=0.9))
    return t


def hpl(ax, xy, stor=False):
    ax.scatter([xy[0]], [xy[1]], s=150 if stor else 34, facecolor='white', edgecolor='#1f1f1e', lw=1.6 if stor else 1.2,
               zorder=11)


def andpunkt(ax, xy, bokstav, farg):
    ax.scatter([xy[0]], [xy[1]], s=330, color=farg, edgecolor='white', lw=1.6, zorder=13)
    ax.text(xy[0], xy[1], bokstav, ha='center', va='center', fontsize=8.5, fontweight='bold', color='white', zorder=14,
            gid='behall')


def figur():
    fig, ax = plt.subplots(figsize=(8.2, 10.6))
    ax.set_xlim(-0.6, 11.6); ax.set_ylim(-1.4, 13.6); ax.set_aspect('equal'); ax.axis('off')
    V, O, N, S, J = F['V'], F['Ö'], F['N'], F['S'], F['J']
    # ---- Västra: Centrum ↔ Västra macken (Sjukhuset), slingan via Sviby, Möckelö fram och tillbaka
    linje(ax, [(5.05, 5.75), (4.45, 6.9), (4.45, 8.45)], V, 'bada')                     # Centrum – Västra macken
    linje(ax, [(4.45, 8.45), (2.6, 8.45)], V, 'en')                                       # Sviby bro → Lönnhagsvägen
    linje(ax, [(2.6, 8.45), (0.8, 6.2)], V, 'bada')                                       # Möckelö Strand
    linje(ax, [(2.6, 8.45), (2.6, 12.4), (4.3, 12.4), (4.3, 8.75)], V, 'en')              # Posten – Dalkulla – Åsvägen
    # ---- Östra: Centrum → Nabben → Solberget ↔ Kalmarnäs, tillbaka via Sjukhuset – Västra macken
    linje(ax, [(5.95, 5.75), (6.25, 8.45), (10.2, 8.45)], O, 'en')                        # ut via Nabben, Kalmsta
    linje(ax, [(10.2, 9.0), (10.2, 6.2)], O, 'bada')                                      # Solberget – Kalmarnäs
    linje(ax, [(10.2, 8.45), (10.2, 9.0)], O, None)
    linje(ax, [(10.2, 8.75), (4.6, 8.75)], O, 'en', z=3.8)                                # tillbaka mot Sjukhuset
    linje(ax, [(4.6, 8.75), (4.6, 6.9), (5.2, 5.75)], O, 'en', z=3.6)                     # Västra macken → Centrum
    ax.plot([6.55, 6.55, 7.0, 7.0], [8.45, 9.15, 9.15, 8.45], color=O, lw=2.0, ls=(0, (2, 1.6)), zorder=3.5)  # skolturer
    # ---- Norra: Centrum → Doktorsvägen → Maxinge → Hindersböle → Nabben → Sjukhuset → Yrkesgymnasiet → Centrum
    linje(ax, [(5.65, 5.75), (5.65, 10.6)], N, 'en')                                      # upp via Polishuset, Doktorsv.
    linje(ax, [(5.65, 10.6), (5.65, 12.6)], N, 'bada')                                    # Maxinge (vänder)
    linje(ax, [(5.65, 10.6), (7.0, 10.6), (7.3, 9.9), (7.6, 9.4), (7.6, 9.05), (4.75, 9.05)], N, 'en', z=4.2)
    linje(ax, [(4.75, 9.05), (4.85, 7.9), (4.1, 7.3), (4.3, 6.4), (4.6, 5.65), (5.2, 5.5)], N, 'en')
    # ---- Södra: Centrum → Torget → Hamnterminalen → Ytternäs → Lervik → Östernäs → Centrum
    linje(ax, [(5.3, 5.35), (4.3, 5.0), (4.3, 3.6), (5.25, 3.3), (5.25, 0.55), (6.5, 0.55), (6.5, 3.9),
               (6.1, 4.9), (5.85, 5.3)], S, 'en')
    # ---- Järsö: Centrum ↔ Ytternäs ↔ Lervik ↔ Järsö, tillbaka via Övernäs skola – Norragatan
    linje(ax, [(5.55, 5.3), (5.55, 4.6), (5.55, 0.4), (5.55, -0.6)], J, 'bada')
    linje(ax, [(5.55, 4.6), (4.75, 4.6), (4.75, 5.3), (5.25, 5.45)], J, 'en', z=3.9)
    # ---- hållplatser och etiketter
    hpl(ax, NOD['Centrum'], stor=True); etikett(ax, NOD['Centrum'], 'Centrum', dx=0.55)
    for n, dx, dy, ha in [('Sjukhuset', -0.25, 0.45, 'right'), ('Strandnäs', 0.0, -0.55, 'center'),
                          ('Hindersböle', 0.15, 0.35, 'left'), ('Solberget', 0.0, 0.5, 'center'),
                          ('Yrkesgymnasiet', -0.3, 0.0, 'right'), ('Hamnterminalen', -0.3, 0.0, 'right'),
                          ('Ytternäs', -0.3, 0.0, 'right'), ('Östernäs', 0.3, 0.0, 'left')]:
        xy = {'Sjukhuset': (4.45, 8.6), 'Strandnäs': (7.6, 8.75), 'Hindersböle': (7.3, 9.9), 'Solberget': (10.2, 9.0),
              'Yrkesgymnasiet': (4.3, 6.4), 'Hamnterminalen': (4.3, 3.6), 'Ytternäs': (5.25, 1.8),
              'Östernäs': (6.5, 2.4)}[n]
        hpl(ax, xy); etikett(ax, xy, n, dx=dx, dy=dy, ha=ha)
    etikett(ax, (4.3, 12.4), 'Sviby', dy=0.55, ha='center')
    andpunkt(ax, (0.8, 6.2), 'V', V); etikett(ax, (0.8, 6.2), 'Möckelö', dx=0.45)
    andpunkt(ax, (5.65, 12.6), 'N', N); etikett(ax, (5.65, 12.6), 'Maxinge', dx=0.45)
    andpunkt(ax, (10.2, 6.2), 'Ö', O); etikett(ax, (10.2, 6.2), 'Kalmarnäs', dx=-0.45, ha='right')
    andpunkt(ax, (6.5, 3.9), 'S', S)
    andpunkt(ax, (5.55, -0.6), 'J', J); etikett(ax, (5.55, -0.6), 'Järsö', dx=0.45)
    # teckenförklaring
    from matplotlib.lines import Line2D
    hnd = [Line2D([], [], color=F[l], lw=4, label=C.NAMN_LINJE[l]) for l in ('V', 'Ö', 'N', 'S', 'J')]
    hnd += [Line2D([], [], color=O, lw=2, ls=(0, (2, 1.6)), label='Östras skolturer via Strandnäs skola')]
    K.teckenforklaring(ax, hnd, loc='lower left')
    ax.set_title('Stadstrafikens linjenät i dag – principskiss', loc='left')
    return K.spara(fig, 'a0_principskiss.png')


if __name__ == '__main__':
    print(figur())
