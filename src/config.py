# -*- coding: utf-8 -*-
"""Gemensamma sökvägar och parametrar för linjenätsutredningen (Mariehamn stadstrafik)."""
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]

# --- Indata (rådata, ändras inte) ---
RADATA_XLSX = ROT / 'Analys_resemönster.xlsx'          # påstigandedata (Radata) + hållplatsregister
PASTIGANDE_XLSX = ROT / 'data' / 'raw' / 'Databas_vardag_host.xlsx'   # tvättad påstigandedata, vardag höst 2026 (N, S, V, Ö)
OD_XLSX = ROT / 'data' / 'raw' / 'Analys_resemonster_OD.xlsx'   # tidigare framtagen OD-matris (FM/EM)
GTFS_DIR = ROT / 'gtfs_latest'                           # GTFS, Ålands landskapsregering (fr.o.m. 2026-08-18)
BEFOLKNING_SHP = ROT / 'Befolkning' / 'Befolk_2024.shp'  # befolkning 2024, rutor 1000×1000 m

# --- Utdata ---
PROCESSED = ROT / 'data' / 'processed'
KARTOR = ROT / 'output' / 'kartor'
RAPPORT = ROT / 'rapport'
for _p in (PROCESSED, KARTOR, RAPPORT):
    _p.mkdir(parents=True, exist_ok=True)

# --- Koordinatsystem ---
CRS_WGS84 = 'EPSG:4326'
CRS_METRISK = 'EPSG:3067'      # ETRS-TM35FIN (samma som befolkningsrutorna)

# --- Studerat linjenät: Mariehamns stadstrafik (AxBuss) ---
STADSLINJER = ['J', 'N', 'S', 'V', 'Ö']                 # route_short_name
STADSLINJER_ROUTE_ID = {'J': '11', 'N': '12', 'S': '13', 'Ö': '14', 'V': '15'}
LANDSBYGDSLINJER = ['1', '2', '3', '4', '5', '6']       # buss, används som kontrollgrupp/tillgänglighet
CENTRUM = 'Centrum, Nygatan'

# --- Tidsfönster och dagsurval (samma som i ursprunglig OD-analys) ---
FM = (6, 9)          # förmiddagsrusning 06–09
EM = (15, 18)        # eftermiddagsrusning 15–18
TIMMAR_PER_PERIOD = 3
ANTAL_VARDAGAR = 92  # nämnare i ursprunglig analys (Filter!E35), mätperiod 2026-05-08 – 2026-09-14
LINJER_NY_DATA = ['N', 'S', 'V', 'Ö']   # linjer i den tvättade höstdatan; linje J finns bara i den tidigare sommardatan

# --- Gravitationsmodell (samma parametrar som ursprunglig OD-matris) ---
BETA = 0.1                 # restidskänslighet (1/min), f(c) = exp(-β·c)
BYTESSTRAFF_MIN = 5.0      # väntan + omstigning vid byte
GANG_MAX_M = 400.0         # gångkoppling mellan hållplatsområden (fågelväg)
GANG_HAST_M_PER_MIN = 75.0
FURNESS_ITERATIONER = 200

# --- Täckning ---
TACKNING_M = 400.0         # avstånd till hållplats (fågelväg) som räknas som "nära"
DELRUTA_M = 50.0           # upplösning för fördelning av rutbefolkning inom 1 km-rutan

# --- Kartstil ---
FARG_LINJE = {'J': '#ff72df', 'N': '#6f4388', 'S': '#00a884', 'V': '#005be6', 'Ö': '#a86f00'}   # beställarens färger
NAMN_LINJE = {'J': 'Järsö', 'N': 'Norra', 'S': 'Södra', 'V': 'Västra', 'Ö': 'Östra'}         # fullständiga linjenamn
NAMN_VO = 'Västra–Östra'                                                                     # genomgående linje V–Ö


import re as _re
_BOKSTAV = _re.compile(r'(?<![\w/.\-])([JNSVÖ])(:s)?(?![\w])')


def fullnamn(t):
    """Byter linjebokstäver i löptext mot fullständiga linjenamn: 'linje V–Ö' -> 'linje Västra–Östra',
    'V och Ö' -> 'Västra och Östra', 'Ö:s' -> 'Östras'. Hållplatsnamn som N2 och N1–N5 berörs inte."""
    if not isinstance(t, str) or not t:
        return t
    return _BOKSTAV.sub(lambda m: NAMN_LINJE[m.group(1)] + ('s' if m.group(2) else ''), t)


def linjenamn(l):
    """'V' -> 'Västra', 'V–Ö' -> 'Västra–Östra'."""
    return NAMN_VO if l in ('V–Ö', 'VO') else NAMN_LINJE.get(l, l)
