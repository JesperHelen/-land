# Kartlager för QGIS

Alla kartor i PM:et finns som GIS-lager i **`linjenatsutredning.gpkg`** (GeoPackage, koordinatsystem
**EPSG:3067 ETRS-TM35FIN**, samma som befolkningsrutorna).

## Öppna i QGIS

- **Enklast:** dra in `linjenatsutredning.gpkg` i QGIS och markera de lager du vill se. Varje lager har en
  inbäddad standardstil som laddas automatiskt, med samma färger och klasser som PNG-kartorna.
- **Alla lager på en gång, grupperade per kapitel:** öppna QGIS Python-konsol (*Insticksprogram > Python-konsol*),
  klicka *Visa redigerare*, öppna `oppna_i_qgis.py` och kör det.
- **Alternativa stilar** (där ett lager används i flera figurer): *Lageregenskaper > Symbologi > Stil* (nederst i
  dialogen) och välj stil i listan. Stilarna finns även som `.qml`-filer i `stilar/` (*Stil > Läs in stil*).
- **Bakgrundskarta:** lägg till t.ex. OpenStreetMap via *XYZ Tiles* i webbläsarpanelen och lägg den underst.
  Lagret `00_land` behövs då inte.

## Lager och figurer

| Figur i PM | Lager | Stil |
|---|---|---|
| Bakgrund i alla kartor | `00_land`, `00_stadslinjer`, `00_hallplatser`, `00_befolkningsrutor` | Standard |
| 1.2 Omfördelning av centrumpåstigningar | `a1_omfordelning_centrum` | Flyttade påstigningar |
| 1.3 Påstigande före/efter korrigering | `a1_zoner_pastigande` | *Påstigande ursprungligt* / *Påstigande korrigerat* |
| 1.4 OD-flöden FM | `a1_od_FM_levererad`, `a1_od_FM_korrigerad` | Standard (bredd och färg efter resor/h) |
| 1.5 OD-flöden EM | `a1_od_EM_levererad`, `a1_od_EM_korrigerad` | Standard |
| 2.1 Täckning 400 m och turtäthet | `a2_tackningsytor` | *Täckning 400 m* (vänster) / *Turtäthet inom 400 m* (höger) |
| 2.2 Turtäthet Mariehamn | `a2_tackningsytor`, `00_hallplatser` | Turtäthet inom 400 m |
| 2.3 Svag faktisk tillgänglighet | `a2_tackningsytor`, `a2_tackning_per_ruta` | *Svag faktisk tillgänglighet* / *Invånare med svag tillgänglighet per ruta* |
| 3.1 Nya hållplatslägen | `a3_nya_hallplatser`, `a3_nya_hallplatser_400m`, `a3_behov_ny_linjestrackning`, `a3_behov_400m` | Standard |
| 3.2 Bedömning av hållplatser | `a3_hallplatsbedomning` | Hållplatsbedömning |

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
