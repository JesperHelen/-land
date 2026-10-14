# 4 Justering av linjenätet

> **Status.** Delleverans i Fas B. Kapitlet redovisar dagens omlopp, de tre förslag som beställaren valde
> ut efter granskningen av Fas A (2026-10-14) och en analys av sammanslagna linjer. Förslagen har prövats
> var för sig och i två paket (avsnitt 4.6). En sammanställning för beställaren finns i
> `PM_linjeforslag.md`.

> **Sammanfattning.** Stadstrafiken körs i dag med fem bussar. Marginalerna är små: kravet på minst
> 2 minuters vändtid i centrum skulle ensamt kräva en sjätte buss. Linje V har 3 minuters vändtid och kan
> därför inte förlängas på egen hand. Linje S och Ö har 7 minuter, och linje N har 4 minuter.
>
> - **Möckelö Strand med dagens gatunät (1a):** omvägen tar 6,5 minuter per tur och ryms inte i omloppen.
>   Bara 8 av 20 turer kan trafikera hållplatsen, och de går på oregelbundna tider.
> - **Möckelö Strand med förlängd Norrgårdsvägen (1b):** omvägen tar 2,5 minuter. Förslaget ryms med alla
>   turer om linje V och Ö körs som en genomgående linje i centrum. Cirka 180 invånare får då en hållplats
>   inom 400 m.
> - **N2 på linje Ö (2):** hållplatsen ger 55 invånare en hållplats inom 400 m. Den ryms på 19 av 20 turer;
>   undantaget är skolturen 08:20.
> - **Linje N via Bo-Bil (3):** ändringen ryms och är i praktiken körtidsneutral (+0,1 min per tur). Vägen
>   blir kortare, men Bo-Bil blir ett nytt uppehåll. Cirka 45 invånare vid Bo-Bil får minst 30 avgångar per
>   vardag. Däremot förlorar 23 invånare vid Vikingagränd hållplatsen inom 400 m.
> - **Paket A** (1b med genomgående V/Ö, 2 och 3) ryms med fem bussar. Det ger 278 invånare bättre och 24
>   sämre tillgänglighet. Andelen med hållplats inom 400 m ökar från 83,6 till 85,0 %.
>
> Sammanslagning av två linjer till en genomgående linje frigör 2,5 minuter per tur för den ena linjen,
> eftersom regleringen bara behöver tas en gång per varv. Det räcker för Möckelö Strand (1b) och för
> Solberget med Solberget södra på linje Ö. Det räcker däremot inte för områdena kring linje N
> (Lillåkersvägen, Örtvägen och Österkalmare).

## 4.1 Ramen – dagens omlopp

**Metod.** Ramen för förslagen är att linjenätet ska rymmas inom dagens omloppsplaner, med samma antal
fordon och samma körtid. GTFS-underlaget saknar omloppsuppgifter (block_id), så omloppen har härletts ur
tidtabellen för en typisk vardag (tisdag 2026-09-01):

- **Turerna:** alla stadslinjeturer börjar och slutar i Centrum, Nygatan. Turerna har kedjats till omlopp
  så att antalet fordon blir det minsta som tidtabellen kräver (minimikostnadstilldelning).
- **Val mellan likvärdiga lösningar:** bland lösningar med lika många fordon har den med kortast
  omloppstid valts, och vid lika väntan samma linje. Omloppstiden är fordonstimmarna från första avgång
  till sista ankomst.
- **Vändtid:** ett fordon får ta nästa tur tidigast 1 minut efter ankomsten, vilket är den kortaste
  vändtiden i dagens tidtabell. Fortsätter fordonet direkt som en annan linje (genomgående linje) räcker
  ett uppehåll på 0,5 minut.

Ett förslag har verifierats på följande sätt:

1. Förslagets körtidsförändring läggs på berörda turer. Avgångstiderna från centrum ligger fast, så att
   pulsen och bytesmöjligheterna behålls.
2. Omloppen byggs om. Förslaget ryms om antalet fordon inte ökar och omloppstiden ökar med högst
   10 minuter per dag. Toleransen motsvarar att dagens sista tur kan bli något längre.
3. Ryms inte alla turer prövas genomgående linje. Därefter prövas turerna en i taget, och det redovisas
   hur många som ryms.

Antalet vändningar under 3 minuter redovisas som mått på robusthet.

**Resultat.** Dagens 93 vardagsturer kräver fem fordon (figur 4.1). Körtiden är 42,5 timmar och
omloppstiden 61,4 timmar per vardag. Av omloppstiden är 11,5 timmar vändtid i centrum och 7,5 timmar
uppställning mitt på dagen.

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

Kvällstrafiken är redan i dag upplagd så att ett fordon kan växla mellan linje V och Ö och ett annat
mellan linje N och S. V avgår :40 och Ö :10, medan N avgår :20 och S :50. De härledda omloppen använder
dessa par på kvällen.

![Figur 4.1](../output/kartor/b4_1_omlopp_idag.png)

*Figur 4.1. Härledd omloppsplan för en typisk vardag. Varje rad är ett fordon och varje stapel en tur i
linjens färg. Orange markering anger vändtid under 3 minuter. Det nedre diagrammet visar antalet fordon i
trafik.*

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
| Alla 20 turer, linje V ensam | 6 bussar – ryms inte | 6 bussar – ryms inte |
| Alla 20 turer, genomgående V/Ö | 6 bussar – ryms inte | **5 bussar – ryms** (omloppstid +2 min/dag) |
| Turer som ryms utan genomgående linje | 8 av 20 (oregelbundna tider) | 10 av 20 |
| Invånare som får hållplats inom 400 m | 179 | 179 |
| Avgångar vid nya hållplatsen | 8 per vardag | 20 per vardag |
| Uppskattat påstigande (sommarnivå) | 0,2–0,9 per vardag | 0,5–2,2 per vardag |
| Längre restid för genomresande | cirka 1 resa och 6 resenärsminuter per vardag | cirka 2 resor och 5 resenärsminuter per vardag |

**Bedömning.**

- **Variant 1a** ryms inte i dagens omlopp. Med alla turer krävs en sjätte buss, och omloppstiden ökar med
  nästan 12 timmar per vardag. Omvägen på 6,5 minuter är längre än linje V:s vändtid och längre än det
  utrymme en genomgående linje ger. De 8 turer som ryms går på oregelbundna tider och ger inte ett
  användbart utbud.
- **Variant 1b** ryms inte heller med linje V ensam, eftersom vändtiden på 3 minuter krymper till
  0,5 minut. Den ryms däremot med alla turer om linje V och Ö körs som genomgående linje i centrum (figur
  4.3). Bussen fortsätter då direkt från V till Ö efter ett kort uppehåll, och regleringen tas efter
  Ö-turen. Där är vändtiden 7 minuter, men bara 2 minuter efter Ö:s skolturer 13:10–15:10. Båda linjerna
  avgår från samma hållplatsläge i centrum, och kvällstrafiken växlar redan i dag mellan V och Ö.
- **Påstigande:** 1b ger cirka 180 invånare en hållplats med 20 avgångar per vardag. Det beräknade
  påstigandet är lågt i sommardata men bör vara högre under terminstid.

Variant 1b med genomgående V/Ö förordas för fortsatt utredning, under förutsättning att Norrgårdsvägen
förlängs.

![Figur 4.2](../output/kartor/b4_2_mockelo_karta.png)

*Figur 4.2. Förslag 1. Grönt anger invånare som får bättre tillgänglighet. Grått anger befolkning som
fortfarande saknar hållplats inom 400 m. Körvägen till den nya hållplatsen är schematisk.*

![Figur 4.3](../output/kartor/b4_3_mockelo_omlopp.png)

*Figur 4.3. Omlopp före och efter för förslag 1. Skrafferad del av en tur är tillagd körtid. Rubriker i rött
anger lösningar som kräver fler bussar än i dag. Blå markering anger att fordonet fortsätter direkt som en
annan linje.*

## 4.3 Förslag 2 – ny hållplats N2 på linje Ö

**Utformning.** Hållplatsen N2 placeras på sträckan mellan Österkullagatan och Kalmarnäs vändplan, i
läget från kapitel 3. Bussen passerar läget i båda riktningarna. Ett uppehåll per tur i genomsnitt
(0,5 minut) har antagits.

**Resultat.**

- **Omlopp:** av linjens 20 turer ryms 19 i dagens omlopp (figur 4.5). Undantaget är skolturen 08:20 via
  Strandnäs skola södra. Den kommer tillbaka till centrum 08:49 och fordonet tar nästa tur 08:50, så
  den saknar marginal. Turen kan antingen köra förbi N2, eller trafikera hållplatsen om fordonet fortsätter
  direkt som linje V 08:50 (genomgående Ö/V).
- **Täckning:** 55 invånare får en hållplats inom 400 m med 19–20 avgångar per vardag.
- **Påstigande:** det uppskattade påstigandet är 0,4–1,8 per vardag på sommarnivå. Linje Ö har stadsnätets
  högsta påstigande per invånare.
- **Ombordvarande:** förlusten för resenärer som redan sitter på bussen är försumbar, cirka 1
  resenärsminut per vardag.

**Bedömning.** Förslaget ryms i dagens omlopp med ett undantag som kan hanteras och rekommenderas.

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

## 4.5 Sammanslagning av linjer – genomgående linjer i centrum

**Princip.** Varje linje har i dag en egen vändtid i centrum. Den måste rymma både regleringstid och en
eventuell förlängning. Om två linjer A och B slås ihop till en genomgående linje fortsätter fordonet
direkt från A till B och nästa varv från B till A. Regleringen behöver då bara tas en gång per varv:

- Linje A får ett kort uppehåll i centrum (0,5 minut) och kan förlängas med 30 − 0,5 − körtiden.
- Linje B måste behålla minst 3 minuters reglering.

Med pulsen i centrum kvar ger sammanslagningen därför 2,5 minuter mer per tur än om linjen förlängs på
egen hand, där 3 minuters reglering krävs (tabell 4.2). Släpps pulsen för den ena halvan kan hela
överskottet för paret användas, men då försämras bytesmöjligheterna i centrum.

*Tabell 4.2. Utrymme för förlängning per tur utan fler bussar (30 minuters turintervall).*

| Linje (körtid) | Egen linje, ≥ 3 min reglering | Genomgående, pulsen kvar | Bästa par utan puls |
|---|---|---|---|
| N (26 min) | 1 min | 3,5 min | 7,5 min (med S eller Ö) |
| S (23 min) | 4 min | 6,5 min | 10,5 min (med Ö) |
| V (27 min) | 0 min | 2,5 min | 6,5 min (med S eller Ö) |
| Ö (23 min, skolturer 28–29) | 4 min | 6,5 min | 10,5 min (med S) |

**Behov.** Behovet har jämförts med de nio områden som enligt kapitel 3 kräver ändrad linjesträckning
(figur 4.8). Behövd tid per tur har beräknats som två gånger avståndet till närmaste körväg × 1,3 i
hastigheten 25 km/h plus 0,5 minuts uppehåll. För Möckelö Strand har beställarens restid för 1b använts.

- **Ryms med genomgående linje:**
  - Möckelö Strand (linje V, 2,5 min);
  - Solberget (linje Ö, cirka 5 min);
  - Solberget södra (linje Ö, cirka 4 min).
- **Ryms inte:** Lillåkersvägen (6,5 min), Örtvägen (4,4 min) och Österkalmare (10 min) ligger vid linje N.
  Deras behov är större än de 3,5 minuter som en genomgående linje ger N. Detsamma gäller Dalkullavägen på
  linje V och Strömsnäs på linje Ö. Områdena norr och nordost om centrum kräver därför en större
  omläggning av linje N och Ö.

Utrymmet i ett par kan bara användas en gång. Förlängs linje V till Möckelö Strand i paret V/Ö har Ö kvar
sitt eget utrymme på 4 minuter per tur, men inte 6,5 minuter.

**Resor som blir direkta.** Genomgående linjer ger också resor utan byte i centrum. Paret S/Ö ger flest
direkta resor, cirka 2 per vardag. Övriga par ger under 1 resa per vardag. Med sommarens låga resande är
effekten liten, men den visar vilka par som har mest gemensam efterfrågan.

**Val av par.** Paren V/Ö och N/S är naturliga. Linjerna i paren avgår från samma hållplatsläge i
centrum (V och Ö från läge 66202, N och S från läge 66201), och kvällstrafiken använder redan dessa par.

![Figur 4.8](../output/kartor/b4_8_sammanslagning.png)

*Figur 4.8. Sammanslagning av linjer. Till vänster områden utan hållplats inom 400 m med behövd tid per
tur. Uppe till höger tidsutrymmet per linje utan och med genomgående linje. Nere till höger resor per
vardag som blir direkta.*

## 4.6 Samlad bild av de enskilda förslagen

*Tabell 4.3. Enskilda förslag – verifiering mot dagens omlopp (5 bussar, omloppstid 61,4 h/vardag).*

| Förslag | Körtid per tur | Ryms? | Krav för att rymmas | Ny täckning (invånare) | Övrigt |
|---|---|---|---|---|---|
| 1a Möckelö Strand, dagens gator | +6,5 min | Nej (6 bussar) | – (8 av 20 turer ryms) | 179 | Oregelbundet utbud |
| 1b Möckelö Strand, förlängd Norrgårdsvägen | +2,5 min | Ja | Genomgående V/Ö | 179 | Kräver ny väg |
| 2 N2 på linje Ö | +0,5 min | Ja, 19 av 20 turer | 08:20-turen undantas eller körs genomgående Ö/V | 55 | |
| 3 Linje N via Bo-Bil | +0,1 min | Ja | – | 44 får ≥ 30 avg.; 23 förlorar | Jämnare körtid |

### Genomgående linje V/Ö och förslagspaket

Förslag 1b har utformats som en genomgående linje V/Ö (figur 4.9). Bussen avgår :20 som linje V och kör via
Möckelö Strand på 29,5 minuter. Efter ett uppehåll på 0,5 minut i centrum fortsätter den :50 som linje Ö
via N2 och tar sin reglering, 6,5 minuter, efter Ö-turen. Två bussar kör varvet med 30 minuters
förskjutning.

Förslagen har också prövats tillsammans (figur 4.10):

- **Paket A** (1b med genomgående V/Ö, 2 och 3) ryms med fem bussar. N2 trafikeras av 19 av 20 turer, och
  omloppstiden ökar med 3 minuter per vardag.
- **Paket B** (1a med alla turer, 2 och 3) kräver sex bussar och 11,6 fler fordonstimmar per vardag.

Båda paketen ger samma täckning i Mariehamn (figur 4.11–4.12):

- **Bättre tillgänglighet:** 278 invånare, varav 234 får en hållplats inom 400 m.
- **Sämre tillgänglighet:** 24 invånare, varav 23 vid Vikingagränd som förlorar sin hållplats.
- **Hållplats inom 400 m:** 83,6 % i dag och 85,0 % med paketen.
- **Minst 30 avgångar per vardag:** 55,6 % i dag och 55,9 % med paketen.

Andelen med svag tillgänglighet ökar från 28,0 till 29,1 %. Det beror på att invånare som i dag saknar
hållplats får en med 19–20 avgångar per vardag. Kostnaderna redovisas i kapitel 5.

![Figur 4.9](../output/kartor/b4_9_linje_vo.png)

*Figur 4.9. Genomgående linje V/Ö med Möckelö Strand (1b) och N2 (2).*

![Figur 4.10](../output/kartor/b4_10_paket_omlopp.png)

*Figur 4.10. Omlopp före och efter för paket A och B.*

![Figur 4.11](../output/kartor/b4_11_systemeffekter.png)

*Figur 4.11. Systemeffekter: invånare med bättre respektive sämre tillgänglighet per förslag och nyckeltal
för paketen.*

![Figur 4.12](../output/kartor/b4_12_tackning_fore_efter.png)

*Figur 4.12. Turtäthet inom 400 m i dag och med paket A.*

## 4.7 Fortsatt arbete

Nästa leverans ska redovisa följande:

1. **Kombinerat förslag V/Ö (klart, paket A).** Genomgående V/Ö med Möckelö Strand (1b) och N2 (2) ryms.
   Robustheten under Ö:s skolturer, där regleringen bara är 1,5–2 minuter per varv, behöver kontrolleras
   mot verkliga körtider.
2. **Kombinerat förslag N/S.** N/S som genomgående linje prövas tillsammans med Bo-Bil (3). Det ger
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
  (Bo-Bil). Linjerna ritas som raka streck mellan hållplatserna, eftersom vägdragning från OSRM inte kunde
  hämtas i analysmiljön. Körtiderna bör kontrolleras mot gatunätet.
- **Påstigande och restider** bygger på sommardata (2026-05-08 – 2026-09-14) och är låga i absoluta tal.
  Effekterna bör räknas om med terminsdata.
- **Hållplatslägena** för Möckelö Strand och N2 är indikativa. Befolkningen är jämnt fördelad inom varje
  1 km-ruta, så antalet invånare som får täckning beror på det exakta läget.
