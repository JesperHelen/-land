# Kartlager för QGIS

Alla kartor i PM:et finns som GIS-lager i **`linjenatsutredning.gpkg`** (GeoPackage, koordinatsystem
**EPSG:3067 ETRS-TM35FIN**, samma som befolkningsrutorna).

## Öppna i QGIS

- **Enklast:** dra in `linjenatsutredning.gpkg` i QGIS och markera de lager du vill se. Varje lager har en
  inbäddad standardstil som laddas automatiskt, med samma färger och klasser som PNG-kartorna.
- **Alla lager på en gång, grupperade per kapitel och per utredningsalternativ:** öppna **`linjenatsutredning.qgz`**
  (*Projekt > Öppna*). Projektfilen är skapad med `oppna_i_qgis.py` och öppnas inzoomad på Mariehamn.
  Skriptet kan köras om (QGIS Python-konsol: *Insticksprogram > Python-konsol*, *Visa redigerare*, öppna
  `oppna_i_qgis.py`, kör) – kör det i ett nytt, tomt projekt. En äldre sparad `.qgz` från en tidigare leverans
  saknar de nya lagren och scenarierna och ska inte användas.
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
| 4.2, 4.4, 4.6 utredningsalternativ 1–3 | `b4_ua_hallplatser`, `b4_ua_korvagar` (fält `ua`: 1a, 1b, 2, 3; `objekt`: befintlig väg / planerad väg / utgår) | Standard |
| Linjerna i UA (huvudalternativ) | `b4_ua_linjer` (fält `ua`: 1a, 1b och 4 = linje V–Ö, 2, 3) | Linjer i utredningsalternativen (huvudalternativ) |
| 4.10 UA 4 – linje V–Ö via flygplatsen | `b4_ua_hallplatser`, `b4_ua_korvagar`, `b4_ua_linjer` (ua 4), `b4_tackning_forandring` (scenario 4_VO) | Standard |
| 4.13–4.14 Systemeffekter, turtäthet före/efter | `b4_tackning_scenarier` och `b4_tackning_forandring` (fält `scenario`: idag, 1a, 1a_ryms, 1a_VO, 1b, 2, 3, 4, 4_VO, 4_VO_sol, 4_Y) | Turtäthet inom 400 m / Förändrad turtäthetsklass |
| Nyckeltal per scenario (bussar, omloppstid, km, täckning, kostnad) | `b4_nyckeltal_scenarier` (tabell utan geometri) | – |
| 4.8 Sammanslagning av linjer | `b4_sammanslagning_omraden` | Behövd tid per tur |
| 4.1, 4.3, 4.5, 4.7, 4.9, 4.11, 4.12 Omlopp och tidsbudget | – (diagram, ingen geografi) | Data: `data/processed/b4_omlopp_scenarier.csv`, `b4_systemeffekter_omlopp.csv` |
| Via-punkter för OSRM ("gömda stopp") | `00_viapunkter` (fält `from_stop`, `to_stop`, `kommentar`) | Via-punkter för OSRM |

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
   - `b4_ua_linjer` och `b4_ua_korvagar`, dvs. utredningsalternativens linjer och nya delsträckor (den befintliga
     vägen Norrgårdsvägen – Möckelö Strand ny, Maxinge – Bo-Bil – Bolstavägen, Posten – flygplatsen). Förlängningen av Norrgårdsvägen
     (1b) är en planerad väg och behålls schematisk (fältet `planerad_del`).
3. Lagren laddas om i projektet. Fältet `vagdragning` anger OSRM, och `00_segment` visar källan, OSRM:s längd och
   körtid per segment. En OSRM-rutt som är orimligt lång (mer än 2,5 × fågelvägen + 300 m) avvisas och behålls
   rak (`kalla = osrm_avvisad`) för kontroll.

**Via-punkter ("gömda stopp").** Väljer OSRM en annan väg än bussen – t.ex. huvudvägen i stället för bussens
gata, eller en vändning vid en hållplats – lägg en punkt på rätt gata i lagret **`00_viapunkter`** (gruppen
*Bakgrund*: *Växla redigering*, *Lägg till punktobjekt*, spara) och kör `rutta_med_osrm.py` igen. Rutten tvingas
då över punkten (utan vändning där). Fälten `from_stop`/`to_stop` (hållplatsernas id, se `00_segment`) kan
lämnas tomma: punkten gäller då det närmaste hållplatssegmentet, och alltid även segmentet i motsatt riktning.
Lagret innehåller från början en punkt: linje V Lönnhagsvägen – Norrgårdsvägen kör vägen söder om huvudvägen
och vänder inte vid hållplatsen. Segment med via-punkter ruttas om varje gång skriptet körs. Samma punkter finns
i `src/s01_vagdragning.py` (`VIA_PUNKTER`) för analyskedjan.

Skriptet kan köras igen; redan ruttade segment hoppas över. Vill du att även analyserna och PNG-kartorna ska
använda vägdragningen: `python src/s01_vagdragning.py --fran-gis` och därefter `python src/kor_alla.py --utan-osrm`
(eller `python src/kor_alla.py` direkt på en dator med internet).

## Utredningsalternativen (UA) i QGIS

Gruppen *Kap 4 Utredningsalternativ (UA)* har en undergrupp per UA (filter på fälten `ua`/`scenario`):

- *UA 1a* (tänd vid start)
- *UA 1b*
- *UA 2*
- *UA 3*
- *UA 4*

Varje undergrupp visar **huvudalternativet**, dvs. den mest realistiska driftformen: ny hållplats, körväg, linjen
och **förändrad turtäthet** (gröna celler = bättre, röda = sämre än i dag). I UA 1a, UA 1b och UA 4 visas linje V
och Ö som en genomgående linje V–Ö (V och Ö sammanslagna, varje varv V + Ö inom timmen med minst 5 minuter i
centrum). UA 4 visar linje V–Ö via flygplatsen; Solberget behålls. Tänd och släck grupperna för att jämföra.

**Systemeffekter – huvudalternativ per UA (välj ett)** är en *exklusiv* grupp: tänd gruppen och klicka i ett
scenario. Varje scenario visar turtäthetsklassen inom 400 m och, ovanpå, cellerna som förändras mot i dag.

**Övriga alternativ** innehåller de andra driftformerna, bl.a. de uteslutna som kräver fler bussar. De redovisas
i rapporten:

- UA 1a, alla turer med dagens tidtabell;
- UA 1a, dagens tidtabell;
- UA 4, alla turer med dagens tidtabell;
- UA 4 med Solberget indragen (samma turer, större marginal);
- UA 4Y, bara flygturerna.

Förändringarna är lokala – zooma in vid Möckelö Strand, Kalmarnäs, Bo-Bil, flygplatsen eller Solberget för att se
dem. Nyckeltalen finns i tabellen *Nyckeltal per UA och driftform* (högerklick > *Öppna attributtabell*), med
fälten `huvudalternativ` och `utesluten`. Filtren kan ändras under *Lageregenskaper > Källa > Frågebyggare*.

## Om lager saknas, är tomma eller osynliga

- **Använd den levererade `linjenatsutredning.qgz`** eller kör `oppna_i_qgis.py` i ett nytt, tomt projekt. En
  äldre sparad projektfil pekar på lager och filter som inte längre finns. I tidigare leveranser var lagret
  `b4_tackning_forandring` dessutom tomt (fel i exporten, rättat 2026-10-14).
- **Förändringarna är lokala.** Zooma in vid Möckelö Strand, Kalmarnäs, Bo-Bil, flygplatsen eller Solberget.
  På kartan över hela Mariehamn ser scenarierna nästan likadana ut.
- **"unable to open database file" i QGIS:s logg:** QGIS öppnar GeoPackage i WAL-läge, och det fungerar inte i
  alla mappar, t.ex. synkade mappar (OneDrive/SharePoint) och nätverksdiskar. Kopiera mappen `output/gis` till en
  lokal disk, eller sätt miljövariabeln `OGR_SQLITE_JOURNAL=DELETE` (*Inställningar > Alternativ > System >
  Miljö*, lägg till variabeln och starta om QGIS).

## Att tänka på

- **OD-bågarna** är ritade som bågar från ursprung till destination, som böjer åt höger i färdriktningen. Fältet
  `i_karta` anger de flöden som tillsammans står för 85 % av resorna, dvs. de som visas i PM:ets figurer. Lagren
  innehåller alla flöden ≥ 0,001 resor/h.
- **`a2_tackningsytor`** och **`b4_tackning_scenarier`** är befolkningsrutornas landdel uppdelad efter
  tillgänglighetsklass. Gränserna är exakta 400 m-cirklar runt hållplatserna (inte rutor), så ytorna blir runda
  även i stor skala. Fältet `invanare` anger beräknat antal invånare i ytan, med antagandet att befolkningen är
  jämnt fördelad inom 1 km-rutan. `b4_tackning_forandring` är de delar av cirklarna där klassen ändras mot i dag.
- **Indikativa hållplatslägen** i `a3_behov_ny_linjestrackning` är befolkningsviktade tyngdpunkter och ska
  anpassas till gatunätet.
- Lagren skapas om med `python src/gis_export.py` efter att analysstegen har körts.
