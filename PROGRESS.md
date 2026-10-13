# Linjenätsutredning Mariehamn – arbetslogg

Bocka av varje steg när det är klart och committat. Nästa körning fortsätter vid första obockade steget.

## Fas A – analys och datagranskning
- [x] **A0 Förberedelser** – mappstruktur (`src/`, `data/processed/`, `output/kartor/`, `rapport/`), gemensam
      konfiguration (`src/config.py`), kustlinje/landmask ur GSHHG (`src/s00_kustlinje.py` → `data/processed/kontext_land.gpkg`).
- [x] **A1 Granskning och korrigering av OD-matrisen** (grund för B4–B5)
      `src/a1_od_granskning.py`, `src/a1_kartor.py` → `data/processed/a1_*`, `output/kartor/a1_*.png`,
      `rapport/A1_datagranskning_od.md`. Resultat: felregistrering vid ändhållplatsen (stadslinjer registrerar
      centrum-påstigning på föregående turs sista hpl); 21 % FM / 15 % EM av centrums påstigning felregistrerad
      (intervall 10–21 %); linje Ö saknades (filter 'E'); gångpar 2 %. Andel resor till/från centrum 79 % → 63 %.
      **Korrigerad matris: `data/processed/a1_od_{FM,EM}_korrigerad.csv` – använd i B4–B5.**
- [ ] **A2 Täckningsgrad med turtäthet**
- [ ] **A3 Förslag på nya hållplatslägen och överflödiga hållplatser**
- [ ] ⏸ **STOPP – invänta beställarens granskning av Fas A innan Fas B påbörjas**

## Fas B – förslag, kalkyl och rapport (efter godkännande)
- [ ] B4 Justering av linjenätet – tre förslag, verifierade mot dagens omloppsplaner
- [ ] B5 Grov ekonomisk kalkyl
- [ ] B6 Färdigställ PM

## Underlag (inventerat i A0)
| Underlag | Fil | Kommentar |
|---|---|---|
| Påstigandedata | `Analys_resemönster.xlsx` (flik Radata) | Valideringar per tur/hållplats/biljettyp, 2026-05-08 – 2026-09-14 (121 dagar, 92 vardagar). Sommarperiod. |
| OD-matris FM/EM | `data/raw/Analys_resemonster_OD.xlsx` | Dubbelt begränsad gravitationsmodell (β = 0,1), 83 hållplatsområden. Kopierad hit från uppladdad fil. |
| GTFS | `gtfs_latest/` | Ålands landskapsregering, giltig fr.o.m. 2026-08-18. Stadslinjer J, N, S, Ö, V (route_id 11–15). Saknar shapes.txt. |
| Befolkning | `Befolkning/Befolk_2024.shp` | 154 rutor 1×1 km, EPSG:3067, 17 697 invånare. |
| Befintlig täckning | `täckningsgrad*.png` | QGIS-kartor (400 m), utan siffror – räknas om i A2 med samma princip. |
| Kustlinje | `data/processed/kontext_land.gpkg` | GSHHG full upplösning (via PyPI `basemap-data-hires`), landmask och kartbakgrund. |

## Noteringar till nästa körning
- Typvardag i GTFS: tisdag 2026-09-01 (`data_las.typvardag()`); restider ur GTFS (ingen shapes.txt).
- Gemensamma moduler: `src/data_las.py` (inläsning), `src/kartlib.py` (kartstil, bågar, etiketter).
- Internet: endast PyPI och repo-GitHub nås. Inga baskarte-tjänster/OSRM – kartor byggs av egna lager.
- Python-paket utöver requirements: geopandas, shapely, pyproj, pyogrio (installeras med pip).
