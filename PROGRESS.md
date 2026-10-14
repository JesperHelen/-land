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
Beställarens granskning 2026-10-14: börja med individuella effekter av (1) linje till ny hållplats i Möckelö
Strand – dagens gatunät (restid 3 min) och med Norrgårdsvägen förlängd till Hamnskärsvägen (1 min), (2) N2 på
linje Ö, (3) linje N via Bo-Bil i stället för Vikingagränd. Analysera sammanslagning av linjer (längre linjer
utan fler bussar) och lägg till i todo. Visualisera omloppen före och efter.

- [ ] **B4 Justering av linjenätet** – `rapport/B4_linjenat.md`
  - [x] **B4.1 Dagens omlopp** – `src/b4_omlopp.py` → `data/processed/b4_omlopp_idag.csv`, `b4_omlopp_nyckeltal.json`,
        `output/kartor/b4_1_omlopp_idag.png`. Härledda ur GTFS (min antal fordon, kortast omloppstid): 5 bussar,
        93 turer, körtid 42,5 h, omloppstid 61,4 h. Minsta vändtid 1 min (med 2 min krävs 6 bussar). Vändtid i
        centrum: N 4, S 7, V 3, Ö 7 (1–2 efter skolturer), J 1–19 min. Verifieringsregel: samma antal fordon,
        omloppstid +≤ 10 min/dag, avgångstider (pulsen) oförändrade, vändtid ≥ 1 min (genomgående ≥ 0,5 min).
  - [x] **B4.2 Enskilda förslag** – `src/b4_natverk.py` (restidsnät + OD-utläggning, = A1), `src/b4_forslag.py`,
        `src/b4_kartor.py` → `b4_forslag.json`, `b4_omlopp_scenarier.csv`, `b4_tackning_forslag.csv.gz`,
        `b4_forslag.gpkg`, figurer `b4_2`–`b4_7`. Resultat: 1a +6,5 min/tur ryms ej (6 bussar; 8/20 turer ryms);
        1b +2,5 min/tur ryms med genomgående V/Ö (alla 20 turer, 5 bussar), +179 inv.; 2 N2 +0,5 min ryms på 19/20
        (08:20-skolturen), +55 inv.; 3 Bo-Bil −0,4 min ryms, 44 inv. lyfts ur svag, 23 inv. förlorar (Vikingagränd).
  - [x] **B4.3 Sammanslagning av linjer (screening)** – `src/b4_sammanslagning.py` → `b4_sammanslagning_*.csv/json`,
        `output/kartor/b4_8_sammanslagning.png`. Genomgående linje ger +2,5 min/tur (reglering en gång per varv):
        utrymme N 3,5 / S 6,5 / V 2,5 / Ö 6,5 min (pulsen kvar). Räcker för Möckelö Strand (V), Solberget och
        Solberget södra (Ö); inte för Lillåkersvägen, Örtvägen, Österkalmare (N) → kräver större omläggning.
  - [ ] **B4.4 Todo – sammanslagning:** pröva genomgående **V/Ö** med 1b + N2 tillsammans i omloppen (kontrollera
        robusthet under Ö:s skolturer 13:10–15:10, reglering 2 min/varv).
  - [ ] **B4.5 Todo – sammanslagning:** pröva genomgående **N/S** + Bo-Bil; använd N:s 3,5 min (ev. + indragna
        hållplatser på S) mot Örtvägen/Lillåkersvägen. Pröva även varianter utan puls (N/S 7,5 min, S/Ö 10,5 min).
  - [ ] **B4.6 Todo – nordost:** omläggning av N och Ö norr/nordost (Lillåkersvägen, Örtvägen, Solberget, Österkalmare).
  - [ ] **B4.7 Tre samlade linjeförslag** verifierade mot omloppen med körtidspåverkan per förslag.
  - [ ] Stäm av härledda omlopp mot operatörens omloppsplaner (om de kan fås) och körtider för nya delsträckor.
- [ ] B5 Grov ekonomisk kalkyl (underlag: km/omloppstid per förslag i `b4_forslag.json`)
- [ ] B6 Färdigställ PM

## Att ta ställning till vid granskningen av Fas A
1. **OD-korrigeringen (A1):** godtas landsbygdslinjerna som kontrollgrupp och startsegmentet (3 hpl, ≤ 800 m)
   som basfall? Korrigerad matris (63 % av resorna via centrum) blir underlag för B4–B5.
2. **Svag faktisk tillgänglighet (A2):** gränsen sattes till < 30 avgångar per vardag (sämre än halvtimmestrafik).
3. **Hållplatskriterier (A3):** lågt påstigande < 0,1/vardag, lucka efter indragning ≤ 600 m, < 25 inv. förlorar
   täckning. Påstigandet är sommardata – indragning föreslås först efter kontroll med terminsdata.
4. ~~**Fas B, linjeförslag:**~~ (beställaren valde förslag 2026-10-14, se Fas B) – utgå från områdena i `a3_behov_ny_linjestrackning.csv` (norr/nordost mellan linje N
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
- **GIS-export för QGIS:** `src/gis_export.py` → `output/gis/linjenatsutredning.gpkg` (EPSG:3067, stilar inbäddade
  i `layer_styles`, även som .qml i `output/gis/stilar/`). Kör om efter varje steg; lägg till Fas B-lagren där.
- **Vägdragning (OSRM) + förskjutning av linjer på samma gata:** `src/s01_vagdragning.py` (cache
  `data/processed/vagdragning_segment.gpkg`). OSRM blockerat i molnmiljön → i nuläget raka streck (kalla='rak').
  När `router.project-osrm.org` är tillåten (eller lokalt): `python src/kor_alla.py` kör om hela kedjan
  (s01 → A1–A3 → kartor → GIS). A3:s kandidatlägen följer då gatunätet – granska om resultaten i A3.
- **Fas B4:** körs med `python src/b4_omlopp.py && python src/b4_forslag.py && python src/b4_kartor.py &&
  python src/b4_sammanslagning.py` (ingår i `kor_alla.py`). Förslagen definieras i `b4_forslag.forslag()`;
  tilläggstid för Möckelö = 2 × restid + 0,5 min (fram och tillbaka) – beställaren bör bekräfta tolkningen.
- Internet: endast PyPI och repo-GitHub nås. Inga baskarte-tjänster/OSRM – kartor byggs av egna lager.
- Python-paket utöver requirements: geopandas, shapely, pyproj, pyogrio (installeras med pip).
