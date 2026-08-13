# Busslinjeoptimering för Åland med genetisk algoritm

Detta repo innehåller en Jupyter Notebook som med en **genetisk algoritm (GA)** tar fram ett förslag på
busslinjenät för Åland som **minimerar passagerarnas upplevda restid** under eftermiddagens rusningstrafik (EM).

Det är Åland-motsvarigheten till Mandl-notebooken i repot `Genetic_Algorithm_UTRP`
(`Mandl Python/Working Mandl.ipynb`), men med verklig indata och en mer realistisk restidsmodell
(väntetid utifrån turtäthet samt bytesstraff).

## Innehåll

```
-land/
├── notebooks/
│   └── aland_busslinjer_ga.ipynb   # Huvudleverans – kör denna
├── data/
│   ├── hallplatser.geojson         # Hållplatser (koordinater)
│   ├── centroid_nyckel.csv         # Centroider/zoner (zon_id, lon, lat)
│   └── OD_matris.xlsx              # OD-matris (efterfrågan zon→zon, EM)
├── output/                         # Genereras vid körning (restidscache, resultat, karta)
├── requirements.txt
└── README.md
```

## Kom igång

1. Installera beroenden:
   ```bash
   pip install -r requirements.txt
   ```
2. (Rekommenderas) Starta en egen **OSRM**-server med Ålands kartdata och ange dess adress i
   parametercellen (`OSRM_BASE_URL`). Utan OSRM faller notebooken tillbaka på en enkel
   fågelvägsuppskattning så att den ändå går att köra – men resultaten blir då grövre.
3. Öppna och kör `notebooks/aland_busslinjer_ga.ipynb` uppifrån och ned.

## Parametrar du själv sätter (cellen *Parametrar*)

| Parameter | Betydelse |
|---|---|
| `ANTAL_LINJER` | Antal busslinjer |
| `LINJE_LANGD_MIN_KM` / `MAX_KM` | Tillåtet längdspann per linje (km) |
| `CENTRAL_NAMN` / `CENTRAL_KOORD` | Central hållplats som **alla** linjer måste passera |
| `HEADWAY_MIN` | Turtäthet (min). Skalär = samma för alla linjer; lista = per linje |
| `OSRM_BASE_URL` | OSRM-serverns adress (egen server eller publik demo) |
| `KLUSTER_M` | Slår ihop hållplatser inom detta avstånd (riktningspar) |
| `POP_STORLEK`, `GENERATIONER`, `MUTATIONSGRAD` | GA-inställningar |

## Restidsmodell (optimeringskriterier)

Upplevd restid för en resa beräknas som:

```
åktid (OSRM)  +  antal byten · 5 min  +  antal påstigningar · (2 · headway/2)
```

- **Åktid** mellan hållplatser hämtas från OSRM (bil-profil).
- **Byte** straffas med **+5 min**.
- **Väntetid** beräknas schablonmässigt som `headway / 2` (gäller rusningstrafik, inte tidtabell),
  och varje väntad minut väger **×2** upplevda minuter. Detta gäller varje påstigning (start + varje byte).

Målfunktionen är efterfrågeviktad medelrestid plus ett straff för efterfrågan som saknar förbindelse.

## Restidscache

Åktiderna mellan alla hållplatspar sparas i `output/restider_hallplatser.csv`
(`from_id, to_id, duration_s, distance_m`). **Före varje körning** kontrolleras att cachen täcker alla
aktuella hållplatser – om du har uppdaterat hållplatslistan och någon saknas beräknas matrisen om automatiskt.

## Resultat

När notebooken körts skapas i `output/`:
- `restider_hallplatser.csv` – restidscache (OSRM),
- `basta_linjenat.csv` – bästa linjenätet (linje, ordning, hållplats, koordinat),
- `linjenat_karta.png` – karta över det optimerade nätet.
