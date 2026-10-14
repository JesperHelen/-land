# Kartlager för QGIS

Alla kartor i PM:et finns som GIS-lager i **`linjenatsutredning.gpkg`** (GeoPackage, koordinatsystem
**EPSG:3067 ETRS-TM35FIN**, samma som befolkningsrutorna).

## Öppna i QGIS

- **Enklast:** dra in `linjenatsutredning.gpkg` i QGIS och markera de lager du vill se. Varje lager har en
  inbäddad standardstil som laddas automatiskt, med samma färger och klasser som PNG-kartorna.
- **Alla lager på en gång, grupperade per kapitel och per linjeförslag:** öppna QGIS Python-konsol
  (*Insticksprogram > Python-konsol*), klicka *Visa redigerare*, öppna `oppna_i_qgis.py` och kör det. Skriptet
  sparar projektet som `linjenatsutredning.qgz` i samma mapp; därefter räcker det att öppna projektfilen.
- **Alternativa stilar** (där ett lager används i flera figurer): *Lageregenskaper > Symbologi > Stil* (nederst i
  dialogen) och välj stil i listan. Stilarna finns även som `.qml`-filer i `stilar/` (*Stil > Läs in stil*).
- **Bakgrundskarta:** lägg till t.ex. OpenStreetMap via *XYZ Tiles* i webbläsarpanelen och lägg den underst.
  Lagret `00_land` behövs då inte.

## Lager och figurer

| Figur i PM | Lager | Stil |
|---|---|---|
| Bakgrund i alla kartor | `00_land`, `00_stadslinjer_forskjutna`, `00_hallplatser`, `00_befolkningsrutor` | Standard |
| (Linjerna utan förskjutning, en geometri per linje) | `00_stadslinjer` | Standard |
| 1.2 Omfördelning av centrumpåstigningar | `a1_omfordelning_centrum` | Flyttade påstigningar |
| 1.3 Påstigande före/efter korrigering | `a1_zoner_pastigande` | *Påstigande ursprungligt* / *Påstigande korrigerat* |
| 1.4 OD-flöden FM | `a1_od_FM_levererad`, `a1_od_FM_korrigerad` | Standard (bredd och färg efter resor/h) |
| 1.5 OD-flöden EM | `a1_od_EM_levererad`, `a1_od_EM_korrigerad` | Standard |
| 2.1 Täckning 400 m och turtäthet | `a2_tackningsytor` | *Täckning 400 m* (vänster) / *Turtäthet inom 400 m* (höger) |
| 2.2 Turtäthet Mariehamn | `a2_tackningsytor`, `00_hallplatser` | Turtäthet inom 400 m |
| 2.3 Svag faktisk tillgänglighet | `a2_tackningsytor`, `a2_tackning_per_ruta` | *Svag faktisk tillgänglighet* / *Invånare med svag tillgänglighet per ruta* |
| 3.1 Nya hållplatslägen | `a3_nya_hallplatser`, `a3_nya_hallplatser_400m`, `a3_behov_ny_linjestrackning`, `a3_behov_400m` | Standard |
| 3.2 Bedömning av hållplatser | `a3_hallplatsbedomning` | Hållplatsbedömning |
| 4.2, 4.4, 4.6 Linjeförslag 1–3 | `b4_forslag_hallplatser`, `b4_forslag_korvagar` (fält `forslag`: 1a, 1b, 2, 3), `b4_tackning_forandring` (fält `scenario`) | Standard |
| 4.9 Linjerna i förslagen (bl.a. genomgående V/Ö) | `b4_linjer_forslag` (fält `forslag`: 1a, 1b_VÖ, 2, 3) | Linjer i förslagen |
| 4.11–4.12 Systemeffekter, turtäthet före/efter | `b4_tackning_scenarier` (fält `scenario`: idag, paket_A), `b4_tackning_forandring` (scenario paket_A) | Turtäthet inom 400 m |
| Nyckeltal per scenario (bussar, omloppstid, km, täckning, kostnad) | `b4_nyckeltal_scenarier` (tabell utan geometri) | – |
| 4.8 Sammanslagning av linjer | `b4_sammanslagning_omraden` | Behövd tid per tur |
| 4.1, 4.3, 4.5, 4.7, 4.10 Omlopp | – (diagram, ingen geografi) | Data: `data/processed/b4_omlopp_scenarier.csv`, `b4_paket_omlopp.csv` |

## Linjer som delar gata

`00_stadslinjer_forskjutna` delar upp linjerna där de går tillsammans med andra linjer. Fältet `forskjutning`
anger linjens spår (…, −1, −0,5, 0, 0,5, 1, …), och stilen förskjuter linjen `forskjutning × 1,1 mm` vid
ritning. Linjerna hålls därmed isär i alla skalor. Spåravståndet ändras i *Symbologi > Förskjutning*
(uttrycket `"forskjutning" * 1.1`).

## Vägdragning längs gatorna (OSRM) – direkt i QGIS

Linjerna levereras som raka streck mellan hållplatserna, eftersom OSRM inte kunde nås från analysmiljön.
Vägdragningen hämtas enklast i QGIS:

1. Öppna QGIS Python-konsol (*Insticksprogram > Python-konsol*), klicka *Visa redigerare*, öppna
   **`rutta_med_osrm.py`** (samma mapp som GeoPackage-filen) och kör det. Datorn behöver internetåtkomst till
   `router.project-osrm.org` (eller egen OSRM-server, ändra `OSRM_URL` i skriptets början).
2. Skriptet ruttar varje hållplatssegment i lagret `00_segment` (ca 130 st, ungefär ett anrop per sekund,
   dvs. 2–3 minuter) och uppdaterar sedan:
   - `00_stadslinjer` och `00_stadslinjer_forskjutna` i gruppen *Bakgrund*; förskjutningen där linjer delar gata
     räknas om längs de ruttade gatorna;
   - `b4_linjer_forslag` och `b4_forslag_korvagar`, dvs. förslagens linjer och nya delsträckor (Möckelö Strand
     via dagens gator, Maxinge – Bo-Bil – Bolstavägen). Förlängningen av Norrgårdsvägen (1b) är en planerad väg
     och behålls schematisk.
3. Lagren laddas om i projektet. Fältet `vagdragning` anger OSRM, och `00_segment` visar källan, OSRM:s längd och
   körtid per segment. En OSRM-rutt som är orimligt lång (mer än 2,5 × fågelvägen + 300 m) avvisas och behålls
   rak (`kalla = osrm_avvisad`) för kontroll.

Skriptet kan köras igen; redan ruttade segment hoppas över. Vill du att även analyserna och PNG-kartorna ska
använda vägdragningen: `python src/s01_vagdragning.py --fran-gis` och därefter `python src/kor_alla.py --utan-osrm`
(eller `python src/kor_alla.py` direkt på en dator med internet).

## Linjeförslagen i QGIS

Skriptet lägger förslagen i gruppen *Kap 4 Linjeförslag* med en undergrupp per förslag (filter på fälten
`forslag`/`scenario`): *Paket A* (tänd vid start), *Förslag 1a*, *1b*, *2*, *3*, *Systemeffekter* och
*Sammanslagning av linjer*. Tänd/släck undergrupperna för att jämföra. Filtren kan ändras under
*Lageregenskaper > Källa > Frågebyggare*. Nya körvägar är schematiska (raka) tills vägdragning finns.

## Att tänka på

- **OD-bågarna** är ritade som bågar från ursprung till destination, som böjer åt höger i färdriktningen. Fältet
  `i_karta` anger de flöden som tillsammans står för 85 % av resorna, dvs. de som visas i PM:ets figurer. Lagren
  innehåller alla flöden ≥ 0,001 resor/h.
- **`a2_tackningsytor`** är befolkningsrutornas landdel uppdelad efter tillgänglighetsklass (50 m upplösning).
  Fältet `invanare` anger beräknat antal invånare i ytan, med antagandet att befolkningen är jämnt fördelad
  inom 1 km-rutan.
- **Indikativa hållplatslägen** i `a3_behov_ny_linjestrackning` är befolkningsviktade tyngdpunkter och ska
  anpassas till gatunätet.
- Lagren skapas om med `python src/gis_export.py` efter att analysstegen har körts.
