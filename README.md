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

## Två notebooks

| Notebook | Vad den gör |
|---|---|
| `notebooks/gtfs_natverk.ipynb` | **GTFS-utforskning** – läs in GTFS, se hela nätet på en interaktiv karta, klicka på en linje för avgångar/dag, avgångar/timme i förmiddags- (06–09) och eftermiddagsrusning (15–18) samt riktning, och välj ut linjer att arbeta vidare med. |
| `notebooks/aland_busslinjer_ga.ipynb` | **Optimering** (genetisk algoritm) – för närvarande pausad, se ovan. |

### GTFS-verktyget (`gtfs_natverk.ipynb`)
1. Sätt `GTFS_PATH` till din GTFS-mapp eller `.zip` (lämnas den tom används det medföljande exemplet i
   `data/gtfs_sample/`; i Colab erbjuds uppladdning).
2. Statistik beräknas för ett vardagsdygn (väljs automatiskt) med rusning FM 06–09 och EM 15–18.
3. Kryssa linjer (ipywidgets) → kartan framhäver dem. Pilar (▶) visar färdriktning; linjer åt båda hållen får
   två parallella spår, enkelriktade bara ett. Klicka på en linje för statistik.
4. Urvalet sparas i `output/valda_linjer.csv` för det fortsatta arbetet.

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
| `HEADWAY_MIN` | Turtäthet (min). Skalär = samma för alla linjer; lista = per linje (standard `[60,60,60,60,60,120]` = dagens nät) |
| `OSRM_BASE_URL` | OSRM-serverns adress (egen server eller publik demo) |
| `KLUSTER_M` | Slår ihop hållplatser inom detta avstånd (riktningspar) |
| `GANG_RADIE_M` | Hur långt en resenär kan gå till en trafikerad hållplats |
| `POP_STORLEK`, `GENERATIONER`, `MUTATIONSGRAD` | GA-inställningar |

## Dagens linjenät som utgångspunkt

Notebooken rekonstruerar dagens sex Ålandstrafik-linjer (Eckerö, Geta, Saltvik, Sund–Vårdö, Lumparland,
Emkarby–Gölby) från deras ändpunkter/korridorer, utvärderar dem med samma restidsmodell och **använder dem
som frö** åt den genetiska algoritmen – så att det optimerade nätet aldrig blir sämre än dagens. En
jämförelsetabell visar dagens vs optimerat.

> **Notera:** Rekonstruktionen fångar rätt korridorer/ändpunkter men inte den exakta hållplatsföljden inne i
> Mariehamn, så dagens *modellerade* andel obetjänad är en pessimistisk överskattning. För ett exakt nuläge:
> importera Ålandstrafikens **GTFS** (exakt hållplatsföljd + tidtabell) och ersätt `bygg_dagens_linjenat`.

## Gångåtkomst

Varje resenär kan gå en kort bit (upp till `GANG_RADIE_M`, standard 600 m) till/från en trafikerad hållplats.
Utan detta skulle glesa nät framstå som orimligt dåliga.

## Interaktiva kartor

Både dagens och det optimerade nätet ritas som **interaktiva Folium-kartor** (zooma, panorera, klicka på
hållplatser för namn) och sparas som fristående HTML i `output/`. Saknas Folium ritas en statisk karta i stället.

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
- `dagens_linjenat.html` – interaktiv karta över dagens nät,
- `optimerat_linjenat.html` – interaktiv karta över det optimerade nätet.
