# -*- coding: utf-8 -*-
"""Kartor för presentationen (avstämningsmötet): samma kartor som i B4 men utan figurtitel och med en kort
teckenförklaring inne i kartan, så att de passar bredvid text på en bild.
Utdata: output/ppt/*.png
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import kartlib as K  # noqa: E402
import b4_kartor as B  # noqa: E402

UT = C.ROT / 'output' / 'ppt'
LINJER = set(C.NAMN_LINJE.values())


def _spara_ppt(behall=(), loc='lower right'):
    """Ersätter K.spara: tar bort titel, flyttar in teckenförklaringen och sparar under output/ppt."""
    def spara(fig, namn):
        for ax in fig.axes:
            ax.set_title(''); ax.set_xlabel(''); ax.set_ylabel('')
            lg = ax.get_legend()
            if lg is None:
                continue
            h, l = lg.legend_handles, [t.get_text() for t in lg.get_texts()]
            par = [(a, b) for a, b in zip(h, l) if b not in LINJER or b in behall]
            lg.remove()
            K.teckenforklaring(ax, [a for a, _ in par], loc=loc, fontsize=7.4)
            leg = ax.get_legend()
            for t, (_, b) in zip(leg.get_texts(), par):
                t.set_text(b)
        UT.mkdir(parents=True, exist_ok=True)
        ut = UT / namn
        K.fullnamn_fig(fig)
        fig.savefig(ut, dpi=220, bbox_inches='tight', pad_inches=0.02)
        plt.close(fig)
        return ut
    return spara


def main():
    org = K.spara
    try:
        for fn, behall, loc in ((B.fig_mockelo, (), 'upper left'), (B.fig_n2, ('Östra',), 'lower left'),
                                (B.fig_bobil, (), 'lower right'), (B.fig_flygplatsen_zoom, (), 'upper left')):
            K.spara = _spara_ppt(behall, loc)
            print(fn())
    finally:
        K.spara = org


if __name__ == '__main__':
    main()
