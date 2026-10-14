# -*- coding: utf-8 -*-
"""Exporterar PM:et (rapport/PM_linjeforslag.md) till Word (rapport/PM_linjeforslag.docx) med pandoc.

Kräver pandoc (t.ex. pip install pypandoc_binary). Bilderna hämtas från output/kartor/ och skalas till sidbredd.
  python src/pm_export.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402

KALLA = C.RAPPORT / 'PM_linjeforslag.md'
MAL = C.RAPPORT / 'PM_linjeforslag.docx'

if __name__ == '__main__':
    import pypandoc
    pypandoc.convert_file(str(KALLA), 'docx', outputfile=str(MAL),
                          extra_args=[f'--resource-path={C.RAPPORT}', '-M', 'lang=sv-SE', '-M', 'title-meta=PM – Linjeförslag',
                                      '--toc', '--toc-depth=2', '-M', 'toc-title=Innehåll'])
    print(MAL)
