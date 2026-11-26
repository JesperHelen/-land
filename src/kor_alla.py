# -*- coding: utf-8 -*-
"""Kör hela analyskedjan i rätt ordning (Fas A, Fas B4, kartor och GIS-export).

  python src/kor_alla.py            # allt, inkl. vägdragning via OSRM (kräver internet)
  python src/kor_alla.py --utan-osrm  # hoppa över OSRM-hämtningen (använd befintlig cache/raka streck)
"""
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
STEG = ['s01_vagdragning', 'a0_principskiss', 'a1_od_granskning', 'a1_kartor', 'a1_pastigande_byten', 'a1_malpunkter', 'a2_tackning', 'a2_kartor',
        'a3_hallplatser', 'a3_kartor', 'b4_omlopp', 'b4_ua3_slinga', 'b4_ua', 'b4_sammanslagning', 'b4_systemeffekter', 'b4_kartor', 'ppt_bilder', 'b4_ua6_norra', 'b4_ua7_kvall', 'b4_ua8_jomala',
        'b5_kalkyl', 'gis_export', 'pm_export']

if __name__ == '__main__':
    steg = [s for s in STEG if not ('--utan-osrm' in sys.argv and s == 's01_vagdragning')]
    try:
        import pypandoc  # noqa: F401  (Word-export av PM:et kräver pandoc)
    except ImportError:
        steg = [s for s in steg if s != 'pm_export']
        print('pypandoc saknas – PM:et exporteras inte till Word (pip install pypandoc_binary)')
    for s in steg:
        print(f'=== {s}', flush=True)
        r = subprocess.run([sys.executable, str(SRC / f'{s}.py')], cwd=SRC.parent)
        if r.returncode != 0:
            sys.exit(f'Avbrutet: {s} misslyckades')
    print('Klart.')
