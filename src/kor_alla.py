# -*- coding: utf-8 -*-
"""Kör hela analyskedjan i rätt ordning (Fas A, Fas B4, kartor och GIS-export).

  python src/kor_alla.py            # allt, inkl. vägdragning via OSRM (kräver internet)
  python src/kor_alla.py --utan-osrm  # hoppa över OSRM-hämtningen (använd befintlig cache/raka streck)
"""
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
STEG = ['s01_vagdragning', 'a1_od_granskning', 'a1_kartor', 'a2_tackning', 'a2_kartor',
        'a3_hallplatser', 'a3_kartor', 'b4_omlopp', 'b4_forslag', 'b4_kartor', 'b4_sammanslagning', 'gis_export']

if __name__ == '__main__':
    steg = [s for s in STEG if not ('--utan-osrm' in sys.argv and s == 's01_vagdragning')]
    for s in steg:
        print(f'=== {s}', flush=True)
        r = subprocess.run([sys.executable, str(SRC / f'{s}.py')], cwd=SRC.parent)
        if r.returncode != 0:
            sys.exit(f'Avbrutet: {s} misslyckades')
    print('Klart.')
