# 4 Justering av linjenätet

> **Status.** Delleverans i Fas B. Kapitlet redovisar dagens omlopp, de tre förslag som beställaren valde
> ut efter granskningen av Fas A (2026-10-14) och en analys av sammanslagna linjer. Förslagen har prövats
> var för sig och i två paket (avsnitt 4.6). En sammanställning för beställaren finns i
> `PM_linjeforslag.md`.

> **Sammanfattning.** Stadstrafiken körs i dag med fem bussar. Förarna byter linje i centrum enligt en fast
> norm: Syd ↔ Norr (S ↔ N) och Öst ↔ Väst (Ö ↔ V). Bussen som har kört linje V fortsätter alltså som linje Ö
> och tvärtom. Marginalerna är små: med krav på 2 minuters vändtid i stället för 1 skulle det krävas en
> sjätte buss.
>
> - **Möckelö Strand med dagens gatunät (1a):** omvägen tar 6,5 minuter per tur och ryms inte i omloppen.
>   Bara 8 av 20 turer kan trafikera hållplatsen, och de går på oregelbundna tider.
> - **Möckelö Strand med förlängd Norrgårdsvägen (1b):** omvägen tar 2,5 minuter. Förslaget ryms med alla
>   20 turer. Bytet V → Ö blir 0,5 minut, och regleringen tas vid bytet Ö → V. Kring Ö:s skolturer blir
>   regleringen då kortare än 3 minuter per varv. En robust variant trafikerar Möckelö Strand med 15 av 20
>   turer. Cirka 180 invånare får en hållplats inom 400 m.
> - **N2 på linje Ö (2):** hållplatsen ger 55 invånare en hållplats inom 400 m och ryms med alla 20 turer.
> - **Linje N via Bo-Bil (3):** ändringen ryms och är i praktiken körtidsneutral (+0,1 min per tur). Vägen
>   blir kortare, men Bo-Bil blir ett nytt uppehåll. Cirka 45 invånare vid Bo-Bil får minst 30 avgångar per
>   vardag. Däremot förlorar 23 invånare vid Vikingagränd hållplatsen inom 400 m.
> - **Paket A** (1b, 2 och 3) ryms med fem bussar. Det ger 278 invånare bättre och 24 sämre tillgänglighet.
>   Andelen med hållplats inom 400 m ökar från 83,6 till 85,0 %.
>
> Eftersom bussarna redan växlar mellan linjerna i paren räcker det att lägga regleringen vid det ena bytet
> i varvet. Då kan den ena linjen förlängas med upp till 2,5 minuter mer per tur än i dag. Det räcker för
> Möckelö Strand (1b) och för Solberget och Solberget södra på linje Ö. Det räcker däremot inte för
> områdena kring linje N (Lillåkersvägen, Örtvägen och Österkalmare).

## 4.1 Ramen – dagens omlopp

**Metod.** Ramen för förslagen är att linjenätet ska rymmas inom dagens omloppsplaner, med samma antal
fordon och samma körtid. GTFS-underlaget saknar omloppsuppgifter (block_id), så omloppen har härletts ur
tidtabellen för en typisk vardag (tisdag 2026-09-01):

- **Turerna:** alla stadslinjeturer börjar och slutar i Centrum, Nygatan. Turerna har kedjats till omlopp
  så att antalet fordon blir det minsta som tidtabellen kräver (minimikostnadstilldelning).
- **Norm för linjebyten:** enligt beställaren byter föraren linje vid varje vändning i centrum, Syd ↔ Norr
  (S ↔ N) och Öst ↔ Väst (Ö ↔ V), så långt tidtabellen medger. Omloppen följer den normen, och ett fordon
  fortsätter aldrig på samma linje. Linje J, som går en gång i timmen, kör i egen slinga.
- **Val mellan likvärdiga lösningar:** bland lösningar med lika många fordon har den med kortast
  omloppstid valts. Omloppstiden är fordonstimmarna från första avgång till sista ankomst.
- **Vändtid:** ett fordon får ta nästa tur tidigast 1 minut efter ankomsten, vilket är den kortaste
  vändtiden i dagens tidtabell. Vid byte inom paret (t.ex. V → Ö) räcker 0,5 minut, eftersom regleringen
  då kan tas vid nästa byte i varvet.

Ett förslag har verifierats på följande sätt:

1. Förslagets körtidsförändring läggs på berörda turer. Avgångstiderna från centrum ligger fast, så att
   pulsen och bytesmöjligheterna behålls.
2. Omloppen byggs om. Förslaget ryms om antalet fordon inte ökar och omloppstiden ökar med högst
   10 minuter per dag. Toleransen motsvarar att dagens sista tur kan bli något längre.
3. Ryms inte alla turer prövas turerna en i taget, och det redovisas hur många som ryms.
4. **Robusthet:** varje varv, dvs. två på varandra följande byten, bör ha minst 3 minuters reglering vid
   något av bytena. Antalet varv utan sådan reglering redovisas. I dag finns ett sådant varv (linje J
   13:17–15:20). Ger ett förslag fler sådana varv redovisas också en robust variant.

**Resultat.** Dagens 93 vardagsturer kräver fem fordon (figur 4.1). Två bussar växlar mellan S och N, två
mellan V och Ö, och en kör linje J. Körtiden är 42,5 timmar och omloppstiden 61,4 timmar per vardag.

Linjerna N, S, V och Ö avgår från centrum i en gemensam puls (:20 och :50) med 30 minuters intervall i
rusningstid. Linje J går ungefär en gång i timmen. Vändtiden i centrum varierar mellan linjerna:

| Linje | Turer per vardag | Körtid per tur (median) | Vändtid i centrum (median) |
|---|---|---|---|
| J | 9 | 48 min (41–62) | 5,5 min (1–19) |
| N | 22 | 26 min | 4 min |
| S | 22 | 23 min | 7 min |
| V | 20 | 27 min | 3 min |
| Ö | 20 | 23 min (skolturer 28–29) | 7 min (1–2 efter skolturer) |

Marginalerna är små. Med 2 minuters lägsta vändtid i stället för 1 minut skulle det krävas sex fordon,
eftersom linje J vänder på 1 minut 14:19–14:20 och 15:19–15:20 och fordonen växlar linje 08:45–08:50.
Vändtiderna i tabellen är också bytestiderna i paren: efter en V-tur har bussen 3 minuter innan den
fortsätter som Ö, och efter en Ö-tur 7 minuter innan den fortsätter som V.

![Figur 4.1](../output/kartor/b4_1_omlopp_idag.png)

*Figur 4.1. Härledd omloppsplan för en typisk vardag, med förarnas norm för linjebyten (S ↔ N, V ↔ Ö).
Varje rad är ett fordon och varje stapel en tur i linjens färg. Markeringar anger byten under 3 minuter.
Det nedre diagrammet visar antalet fordon i trafik.*

## 4.2 Förslag 1 – linje V till ny hållplats i Möckelö Strand

**Utformning.** Linje V vänder i dag vid hållplatsen Möckelö Strand. Den nya hållplatsen placeras i det
indikativa läget från kapitel 3, cirka 700 m söder om dagens vändpunkt. Två varianter har prövats:

- **1a – dagens gatunät:** restid 3 minuter till den nya hållplatsen enligt beställaren.
- **1b – Norrgårdsvägen förlängs till Hamnskärsvägen:** restid 1 minut.

Bussen antas köra till den nya hållplatsen och samma väg tillbaka. Tillägget per tur blir då två gånger
restiden plus 0,5 minuts uppehåll, dvs. 6,5 minuter (1a) respektive 2,5 minuter (1b). Kan bussen i stället
fortsätta i en slinga utan att vända blir tillägget ungefär hälften.

*Tabell 4.1. Förslag 1 – effekter och verifiering mot dagens omlopp.*

| | 1a dagens gatunät | 1b förlängd Norrgårdsvägen |
|---|---|---|
| Körtid per tur | +6,5 min | +2,5 min |
| Fordonskilometer per vardag | +20 km (8 turer) | +17 km (20 turer) |
| Alla 20 turer | 6 bussar – ryms inte (omloppstid +11,6 h/dag) | **5 bussar – ryms** (omloppstid +3 min/dag) |
| Turer som ryms | 8 av 20 (oregelbundna tider) | 20 av 20 |
| Varv med < 3 min reglering (i dag 1) | 1 | 8 – robust variant: 15 av 20 turer, 1 varv |
| Invånare som får hållplats inom 400 m | 179 | 179 |
| Avgångar vid nya hållplatsen | 8 per vardag | 20 per vardag |
| Uppskattat påstigande (sommarnivå) | 0,2–0,9 per vardag | 0,5–2,2 per vardag |
| Längre restid för genomresande | cirka 1 resa och 6 resenärsminuter per vardag | cirka 2 resor och 5 resenärsminuter per vardag |

**Bedömning.**

- **Variant 1a** ryms inte i dagens omlopp. Med alla turer krävs en sjätte buss, och omloppstiden ökar med
  nästan 12 timmar per vardag. Omvägen på 6,5 minuter är längre än bytestiden V → Ö (3 minuter) och längre
  än det utrymme som finns om all reglering läggs vid bytet Ö → V. De 8 turer som ryms går på oregelbundna
  tider och ger inte ett användbart utbud.
- **Variant 1b** ryms med alla 20 turer (figur 4.3). Bussen växlar redan i dag från V till Ö. Med 1b blir
  bytet V → Ö 0,5 minut, och regleringen, 6,5 minuter, tas vid bytet Ö → V. Kring Ö:s skolturer (07:50–08:50
  och 13:40–15:40) blir regleringen kortare än 3 minuter per varv. I en robust variant körs omvägen inte på
  V-turerna 07:50, 08:50, 13:40, 14:40 och 15:40. Hållplatsen får då 15 avgångar per vardag i stället för 20.
- **Påstigande:** 1b ger cirka 180 invånare en hållplats med 20 avgångar per vardag. Det beräknade
  påstigandet är lågt i sommardata men bör vara högre under terminstid.

Variant 1b förordas för fortsatt utredning, under förutsättning att Norrgårdsvägen förlängs. Robustheten
kring Ö:s skolturer bör stämmas av mot verkliga körtider innan alla turer läggs via Möckelö Strand.

![Figur 4.2](../output/kartor/b4_2_mockelo_karta.png)

*Figur 4.2. Förslag 1. Grönt anger invånare som får bättre tillgänglighet. Grått anger befolkning som
fortfarande saknar hållplats inom 400 m. Körvägen till den nya hållplatsen är schematisk.*

![Figur 4.3](../output/kartor/b4_3_mockelo_omlopp.png)

*Figur 4.3. Omlopp före och efter för förslag 1. Skrafferad del av en tur är tillagd körtid. Rubriker i rött
anger lösningar som kräver fler bussar än i dag. Blå markering anger kort byte inom linjeparet.*

## 4.3 Förslag 2 – ny hållplats N2 på linje Ö

**Utformning.** Hållplatsen N2 placeras på sträckan mellan Österkullagatan och Kalmarnäs vändplan, i
läget från kapitel 3. Bussen passerar läget i båda riktningarna. Ett uppehåll per tur i genomsnitt
(0,5 minut) har antagits.

**Resultat.**

- **Omlopp:** alla 20 turer ryms med fem bussar (figur 4.5), och förslaget är lika robust som i dag.
  Skolturen 08:20 kommer tillbaka 08:49,5 och bussen fortsätter som linje V 08:50 efter ett kort byte.
- **Täckning:** 55 invånare får en hållplats inom 400 m med 20 avgångar per vardag.
- **Påstigande:** det uppskattade påstigandet är 0,4–1,8 per vardag på sommarnivå. Linje Ö har stadsnätets
  högsta påstigande per invånare.
- **Ombordvarande:** förlusten för resenärer som redan sitter på bussen är försumbar, cirka 1
  resenärsminut per vardag.

**Bedömning.** Förslaget ryms i dagens omlopp och rekommenderas.

![Figur 4.4](../output/kartor/b4_4_n2_karta.png)

*Figur 4.4. Förslag 2, ny hållplats N2 på linje Ö.*

![Figur 4.5](../output/kartor/b4_5_n2_omlopp.png)

*Figur 4.5. Omlopp före och efter för förslag 2.*

## 4.4 Förslag 3 – linje N via Bo-Bil i stället för Vikingagränd

**Utformning.** Linje N kör i dag Maxinge – Vikingagränd – Bolstavägen. I förslaget kör linjen i stället
Maxinge – Bo-Bil – Bolstavägen och stannar vid hållplatsen Bo-Bil på Nya Godbyvägen. Syftet är att bussen
inte ska behöva vänta vid Nya Godbyvägen för att komma till Maxinge. Bo-Bil trafikeras i dag främst av
landsbygdslinjerna 2–4.

**Resultat.**

- **Körtid:** den nya körvägen är cirka 27 % kortare fågelvägen. Med dagens schemalagda tid för
  delsträckan ger det 0,4 minut kortare körtid per tur. Bo-Bil blir däremot ett verkligt uppehåll
  (+0,5 minut), medan bussen i dag sällan stannar vid Vikingagränd. Netto blir körtiden +0,1 minut per tur,
  dvs. i praktiken oförändrad. Fordonskilometrarna minskar med cirka 9 km per vardag. Den minskade väntan
  vid Nya Godbyvägen ingår inte, eftersom den inte kan beräknas utan realtidsdata. Den talar för kortare och
  jämnare körtid.
- **Omlopp:** förslaget ryms med alla 22 turer och fem bussar (figur 4.7). Linje N:s vändtid blir 3,9
  minuter i stället för 4.
- **Bo-Bil:** hållplatsen får linje N:s 22 avgångar utöver landsbygdslinjernas. Cirka 45 invånare får
  därmed minst 30 avgångar per vardag i stället för 15–29.
- **Vikingagränd:** 23 invånare förlorar hållplats inom 400 m. Påstigandet vid Vikingagränd är i dag
  cirka 0,05 per vardag, dvs. fem påstigningar under 92 vardagar, och hållplatsen bedömdes redan i
  kapitel 3 som en hållplats som bör prövas.
- **Restid:** förändringen för genomresande på linje N är försumbar, cirka 2 resenärsminuter per vardag.

**Bedömning.** Förslaget ryms och förbättrar körtidens tillförlitlighet. Den förlorade täckningen vid
Vikingagränd är liten men bör vägas in. Den kan mildras om hållplatsen N3 söder om Maxinge (kapitel 3)
genomförs samtidigt.

![Figur 4.6](../output/kartor/b4_6_bobil_karta.png)

*Figur 4.6. Förslag 3. Rött anger invånare som får sämre tillgänglighet och grönt invånare som får bättre.
Körvägarna är schematiska.*

![Figur 4.7](../output/kartor/b4_7_bobil_omlopp.png)

*Figur 4.7. Omlopp före och efter för förslag 3.*

## 4.5 Sammanslagning av linjer – reglering vid bytet till partnerlinjen

**Princip.** Bussarna växlar redan i dag mellan linjerna i paren S ↔ N och Ö ↔ V. Varje byte har i dag en
egen reglering, lika med linjens vändtid. Läggs all reglering vid det ena bytet i varvet blir det andra
bytet kort:

- Linje A får ett kort byte i centrum (0,5 minut) och kan förlängas med 30 − 0,5 − körtiden.
- Partnerlinjen B behåller minst 3 minuters reglering vid sitt byte.

Med pulsen i centrum kvar ger det 2,5 minuter mer per tur än om varje byte ska ha minst 3 minuters
reglering (tabell 4.2). Släpps pulsen för den ena linjen kan hela parets överskott användas, men då
försämras bytesmöjligheterna i centrum. Om bytet dessutom skyltas som en genomgående linje kan resenärerna
sitta kvar på bussen.

*Tabell 4.2. Utrymme för förlängning per tur utan fler bussar (30 minuters turintervall).*

| Linje (körtid) | Reglering ≥ 3 min vid varje byte | Reglering vid partnerns byte, pulsen kvar | Utan puls (paret) |
|---|---|---|---|
| N (26 min), partner S | 1 min | 3,5 min | 7,5 min |
| S (23 min), partner N | 4 min | 6,5 min | 7,5 min |
| V (27 min), partner Ö | 0 min | 2,5 min | 6,5 min |
| Ö (23 min, skolturer 28–29), partner V | 4 min | 6,5 min | 6,5 min |

**Behov.** Behovet har jämförts med de nio områden som enligt kapitel 3 kräver ändrad linjesträckning
(figur 4.8). Behövd tid per tur har beräknats som två gånger avståndet till närmaste körväg × 1,3 i
hastigheten 25 km/h plus 0,5 minuts uppehåll. För Möckelö Strand har beställarens restid för 1b använts.

- **Ryms med reglering hos partnerlinjen:**
  - Möckelö Strand (linje V, 2,5 min);
  - Solberget (linje Ö, cirka 5 min);
  - Solberget södra (linje Ö, cirka 4 min).
- **Ryms inte:** Lillåkersvägen (6,5 min), Örtvägen (4,4 min) och Österkalmare (10 min) ligger vid linje N.
  Deras behov är större än de 3,5 minuter som N kan få. Detsamma gäller Dalkullavägen på
  linje V och Strömsnäs på linje Ö. Områdena norr och nordost om centrum kräver därför en större
  omläggning av linje N och Ö.

Utrymmet i ett par kan bara användas en gång. Förlängs linje V till Möckelö Strand i paret V/Ö har Ö kvar
sitt eget utrymme på 4 minuter per tur, men inte 6,5 minuter.

**Resor som kan bli direkta.** Skyltas bytet som genomgående linje kan resenärerna sitta kvar. För dagens
par ger det under 1 resa per vardag vardera (N/S och V/Ö). Paret S/Ö skulle ge flest, cirka 2 per vardag,
men är inte ett av dagens par. Med sommarens låga resande är effekten liten. Paren avgår från samma
hållplatsläge i centrum (V och Ö från läge 66202, N och S från läge 66201).

![Figur 4.8](../output/kartor/b4_8_sammanslagning.png)

*Figur 4.8. Sammanslagning av linjer. Till vänster områden utan hållplats inom 400 m med behövd tid per
tur. Uppe till höger tidsutrymmet per linje med reglering vid varje byte och vid partnerns byte. Nere till
höger resor per vardag som kan bli direkta om bytet skyltas som genomgående linje.*

## 4.6 Samlad bild av de enskilda förslagen

*Tabell 4.3. Enskilda förslag – verifiering mot dagens omlopp (5 bussar, omloppstid 61,4 h/vardag).*

| Förslag | Körtid per tur | Ryms? | Krav för att rymmas | Ny täckning (invånare) | Övrigt |
|---|---|---|---|---|---|
| 1a Möckelö Strand, dagens gator | +6,5 min | Nej (6 bussar) | – (8 av 20 turer ryms) | 179 | Oregelbundet utbud |
| 1b Möckelö Strand, förlängd Norrgårdsvägen | +2,5 min | Ja, 20 av 20 | Bytet V → Ö 0,5 min; robust variant 15 av 20 | 179 | Kräver ny väg |
| 2 N2 på linje Ö | +0,5 min | Ja, 20 av 20 | – | 55 | |
| 3 Linje N via Bo-Bil | +0,1 min | Ja | – | 44 får ≥ 30 avg.; 23 förlorar | Jämnare körtid |

### Omloppsparet V ↔ Ö och förslagspaket

Med 1b och N2 ser varvet för paret V ↔ Ö ut så här (figur 4.9):

1. Bussen avgår :20 som linje V och kör via Möckelö Strand på 29,5 minuter.
2. Efter ett byte på 0,5 minut fortsätter den :50 som linje Ö via N2.
3. Efter Ö-turen tar bussen sin reglering, 6,5 minuter, innan nästa V-tur.

Två bussar kör varvet med 30 minuters förskjutning, som i dag.

Förslagen har också prövats tillsammans (figur 4.10):

- **Paket A** (1b, 2 och 3, alla turer) ryms med fem bussar. Omloppstiden ökar med 3 minuter per vardag.
  Kring Ö:s skolturer finns 8 varv med mindre än 3 minuters reglering, mot 1 i dag.
- **Paket A robust** trafikerar Möckelö Strand med 15 av 20 V-turer. Det ryms med fem bussar och är lika
  robust som i dag.
- **Paket B** (1a med alla turer, 2 och 3) kräver sex bussar och 11,6 fler fordonstimmar per vardag.

Båda paketen ger samma täckning i Mariehamn (figur 4.11–4.12):

- **Bättre tillgänglighet:** 278 invånare, varav 234 får en hållplats inom 400 m.
- **Sämre tillgänglighet:** 24 invånare, varav 23 vid Vikingagränd som förlorar sin hållplats.
- **Hållplats inom 400 m:** 83,6 % i dag och 85,0 % med paketen.
- **Minst 30 avgångar per vardag:** 55,6 % i dag och 55,9 % med paketen.

Andelen med svag tillgänglighet ökar från 28,0 till 29,1 %. Det beror på att invånare som i dag saknar
hållplats får en med 15–20 avgångar per vardag. Kostnaderna redovisas i kapitel 5.

![Figur 4.9](../output/kartor/b4_9_linje_vo.png)

*Figur 4.9. Omloppsparet V ↔ Ö med Möckelö Strand (1b) och N2 (2).*

![Figur 4.10](../output/kartor/b4_10_paket_omlopp.png)

*Figur 4.10. Omlopp före och efter för paket A, paket A robust och paket B.*

![Figur 4.11](../output/kartor/b4_11_systemeffekter.png)

*Figur 4.11. Systemeffekter: invånare med bättre respektive sämre tillgänglighet per förslag och nyckeltal
för paketen.*

![Figur 4.12](../output/kartor/b4_12_tackning_fore_efter.png)

*Figur 4.12. Turtäthet inom 400 m i dag och med paket A.*

## 4.7 Fortsatt arbete

Nästa leverans ska redovisa följande:

1. **Kombinerat förslag V ↔ Ö (klart, paket A).** Möckelö Strand (1b) och N2 (2) ryms. Robustheten kring
   Ö:s skolturer behöver kontrolleras mot verkliga körtider.
2. **Paret N ↔ S.** Reglering vid bytet N → S prövas tillsammans med Bo-Bil (3). Det ger
   utrymme för linje N att nå Örtvägen och Lillåkersvägen, alternativt att sammanslagningen kombineras med
   indragning av hållplatser på linje S enligt kapitel 3.
3. **Nordost.** En omläggning av linje N och Ö norr och nordost om centrum prövas för Lillåkersvägen,
   Örtvägen, Solberget och Österkalmare, med och utan bibehållen puls.
4. **Tre samlade linjeförslag.** Förslagen verifieras mot omloppen och redovisas med körtidspåverkan, och
   därefter görs den ekonomiska kalkylen (kapitel 5).

## 4.8 Osäkerheter

- **Omloppen** är härledda ur tidtabellen och kan avvika från operatörens faktiska omloppsplaner. Förarnas
  raster och tjänstgöring ingår inte. Verifieringen bör stämmas av mot operatörens omloppsplaner.
- **Körtider för nya delsträckor** bygger på beställarens restider (Möckelö Strand) och fågelvägsavstånd
  (Bo-Bil). När vägdragningen hämtas från OSRM (`python src/kor_alla.py`) ruttas även förslagens nya
  delsträckor, och OSRM:s körtider redovisas för kontroll i `b4_forslag.json`. I den här versionen kunde OSRM
  inte nås från analysmiljön, så linjerna är ritade som raka streck mellan hållplatserna.
- **Normen för linjebyten** (S ↔ N, Ö ↔ V) bygger på beställarens uppgift och bör stämmas av mot
  operatörens omloppsplaner.
- **Påstigande och restider** bygger på sommardata (2026-05-08 – 2026-09-14) och är låga i absoluta tal.
  Effekterna bör räknas om med terminsdata.
- **Hållplatslägena** för Möckelö Strand och N2 är indikativa. Befolkningen är jämnt fördelad inom varje
  1 km-ruta, så antalet invånare som får täckning beror på det exakta läget.
