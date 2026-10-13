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
- [x] **A2 Täckningsgrad med turtäthet**
      `src/a2_tackning.py`, `src/a2_kartor.py` → `data/processed/a2_*`, `output/kartor/a2_*.png`,
      `rapport/A2_tackning_turtathet.md`. Mariehamn: 84 % inom 400 m men bara 56 % med ≥ 30 avg/vardag;
      svag faktisk tillgänglighet (hpl nära, ≤ 29 avg) 28 % ≈ 4 150 inv.; otäckt 16 % ≈ 2 430 inv.
      Delpunkter 50 m med klass i `a2_delpunkter.csv.gz` – används i A3.
- [x] **A3 Förslag på nya hållplatslägen och överflödiga hållplatser**
      `src/a3_hallplatser.py`, `src/a3_kartor.py` → `data/processed/a3_*`, `output/kartor/a3_*.png`,
      `rapport/A3_hallplatslagen.md`. 5 nya lägen längs dagens linjer (N1–N5: +136 inv. täckning, 95 lyfts ur svag);
      9 områden (≈ 1 130 inv.) kräver ändrad linjesträckning → indata B4 (`a3_behov_ny_linjestrackning.csv`);
      6 kandidater för indragning (5 på S, 1 på V), 13 bör prövas.
- [x] ⏸ **STOPP – Fas A klar. Invänta beställarens granskning innan Fas B påbörjas** (Fas A klar 2026-10-13)

## Fas B – förslag, kalkyl och rapport (efter godkännande)
- [ ] B4 Justering av linjenätet – tre förslag, verifierade mot dagens omloppsplaner
- [ ] B5 Grov ekonomisk kalkyl
- [ ] B6 Färdigställ PM

## Att ta ställning till vid granskningen av Fas A
1. **OD-korrigeringen (A1):** godtas landsbygdslinjerna som kontrollgrupp och startsegmentet (3 hpl, ≤ 800 m)
   som basfall? Korrigerad matris (63 % av resorna via centrum) blir underlag för B4–B5.
2. **Svag faktisk tillgänglighet (A2):** gränsen sattes till < 30 avgångar per vardag (sämre än halvtimmestrafik).
3. **Hållplatskriterier (A3):** lågt påstigande < 0,1/vardag, lucka efter indragning ≤ 600 m, < 25 inv. förlorar
   täckning. Påstigandet är sommardata – indragning föreslås först efter kontroll med terminsdata.
4. **Fas B, linjeförslag:** utgå från områdena i `a3_behov_ny_linjestrackning.csv` (norr/nordost mellan linje N
   och Ö, Möckelö Strand, Dalkullavägen) och körtidsutrymmet från indragna hållplatser på linje S/V.
   Omloppsverifiering kräver omloppsdata (block) – GTFS saknar block_id; härleds ur tidtabellen i B4.

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
