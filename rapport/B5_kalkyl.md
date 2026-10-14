# 5 Ekonomisk kalkyl (överslag)

> **Sammanfattning.** Förslagen har kalkylerats var för sig.
>
> - **1a med alla turer:** en ny hållplats i Möckelö Strand via dagens vägar kräver en sjätte buss. Driftkostnaden
>   ökar då med cirka 216 000 euro per år (175 000–258 000).
> - **1a med V och Ö sammanslagna:** bussen fortsätter direkt från linje V till linje Ö, och Ö avgår upp till
>   2 minuter efter pulsen. Då trafikerar 17 av 20 turer hållplatsen med dagens fem bussar, för cirka
>   12 000 euro per år (10 000–16 000).
> - **1b:** med förlängd Norrgårdsvägen trafikerar alla 20 turer hållplatsen, för cirka 8 000 euro per år
>   (6 000–11 000).
> - **2 (N2):** praktiskt taget kostnadsneutralt.
> - **3 (Bo-Bil):** sparar cirka 2 000 euro per år.
> - **4 (flygplatsen):**
>   - med alla turer krävs en sjätte buss, cirka 209 000 euro per år;
>   - med V och Ö sammanslagna (19–20 av 20 turer) cirka 7 000 euro per år;
>   - Y-versionen med de 8 flygturerna cirka 2 300 euro per år.
>
> Ur busstrafikens perspektiv är vägförlängningen motiverad om den kostar mindre än 2,4–3,5 miljoner euro, om
> alternativet är 1a med en extra buss. Jämfört med 1a med V och Ö sammanslagna blir driftbesparingen bara
> cirka 4 000 euro per år. Vägen motiveras då av robusthet, kortare restid och de sista tre turerna, inte av
> busstrafikens driftkostnad.

## 5.1 Metod och antaganden

Kalkylen omfattar förändrad driftkostnad per år jämfört med i dag:

> Δ driftkostnad = Δ fordon × fordonskostnad + Δ fordonstimmar × timkostnad + Δ fordonskm × km-kostnad

- **Förändringar:** Δ fordon, Δ omloppstid (fordonstimmar) och Δ km per vardag kommer från
  omloppsverifieringen i kapitel 4.
- **Årsvolym:** 250 vardagar per år med typvardagens tidtabell. GTFS-underlaget omfattar bara hösten 2026,
  så helårsvolymen är ett antagande. Lördagstrafiken, med fem turer per linje, påverkas bara genom körda
  kilometer. Samma andel av turerna som på vardagar antas gå via den nya hållplatsen.
- **Enhetskostnader** (euro, prisnivå 2026):

  | Kostnadspost | Låg | Bas | Hög |
  |---|---|---|---|
  | Fordon (kapital, försäkring, uppställning), per fordon och år | 45 000 | 60 000 | 75 000 |
  | Fordonstimme (förare inkl. sociala avgifter och omkostnader) | 42 | 50 | 58 |
  | Fordonskilometer (energi, däck, underhåll) | 0,7 | 0,9 | 1,2 |
  | Nytt hållplatsläge (engångs) | 8 000 | 15 000 | 30 000 |

  Förlängningen av Norrgårdsvägen (1b) och en vändmöjlighet vid den nya hållplatsen (1a) har inte
  kostnadsberäknats.

  Värdena utgår från Trivector (2023), *Trafikeringskostnader för buss 2019 och 2045*, för Trafikverket.
  Där anges för tätortstrafik 2019 cirka 0,65 MSEK per fordon och år och cirka 480 kr per fordonstimme.
  Värdena är omräknade till euro och uppräknade till 2026. De är schabloner och ska ersättas med
  avtalspriserna i landskapsregeringens trafikavtal.
- **Kalkylränta och tid:** nuvärden har beräknats med 3,5 % kalkylränta och 20 års kalkyltid.

## 5.2 Resultat

*Tabell 5.1. Förändrad driftkostnad per år jämfört med i dag (euro, prisnivå 2026). Varje förslag för sig.*

| Förslag | Bussar | Fordonstimmar per år | Fordonskm per år | Driftkostnad per år, bas (låg–hög) | Per invånare med bättre tillgänglighet |
|---|---|---|---|---|---|
| 1a dagens vägar, alla 20 turer | +1 | +2 860 | +14 300 | +216 000 (175 000–258 000) | 1 206 €/år |
| 1a dagens vägar, dagens tidtabell (9 av 20 turer) | 0 | +38 | +6 400 | +7 700 (6 100–9 900) | 43 €/år |
| 1a dagens vägar, V och Ö sammanslagna (17 av 20 turer) | 0 | +28 | +12 100 | +12 300 (9 600–16 100) | 69 €/år |
| 1b förlängd Norrgårdsvägen, slinga (20 av 20 turer) | 0 | +12 | +8 400 | +8 200 (6 400–10 800) | 46 €/år |
| 2 N2 på linje Ö | 0 | +2 | 0 | ±0 | – |
| 3 Linje N via Bo-Bil | 0 | 0 | −2 500 | −2 200 | – |
| 4 flygplatsen, alla 20 turer | +1 | +2 850 | +7 300 | +209 000 (170 000–249 000) | 10 452 €/år |
| 4 flygplatsen, V och Ö sammanslagna (19 av 20 turer) | 0 | +22 | +6 900 | +7 300 (5 800–9 600) | 366 €/år |
| 4 flygplatsen, dito + Solberget indragen (20 av 20) | 0 | +12 | +7 300 | +7 200 (5 600–9 400) | 358 €/år |
| 4Y flygturerna (8 av 8), dito | 0 | −10 | +3 100 | +2 300 (1 800–3 200) | 115 €/år |

Kostnaden per invånare med bättre tillgänglighet är inte rättvisande för förslag 4. Nyttan gäller främst
flygresenärer, som inte finns i OD-matrisen.

**Förslag 1a med alla turer.** Merkostnaden domineras av den sjätte bussen, cirka 60 000 euro per år, och
dess förartimmar, cirka 143 000 euro per år. Kan operatören använda en befintlig reservbuss faller
fordonskostnaden bort, och driftkostnaden blir cirka 156 000 euro per år. Reserven för fordonsbortfall
minskar då.

**Förslag 1a med V och Ö sammanslagna.** Bussen fortsätter direkt som linje Ö efter en halv minut, och 14
Ö-turer avgår upp till 2 minuter efter pulsen (avsnitt 4.5). Kostnaden är nästan bara körda kilometer
(omvägen är 2,7 km per tur). Antalet bussar och fordonstimmar är i praktiken oförändrat.

**Förlängningen av Norrgårdsvägen** har inte kostnadsberäknats. Jämförelsen beror på alternativet:

- **Mot 1a med en extra buss:** merkostnaden är cirka 208 000 euro per år (169 000–247 000). Med 3,5 %
  kalkylränta motsvarar det ett nuvärde på 2,4–3,5 miljoner euro över 20 år. En vägförlängning som kostar
  mindre än så är billigare än att köra 1a med en extra buss.
- **Mot 1a med V och Ö sammanslagna:** skillnaden i driftkostnad är bara cirka 4 000 euro per år, ett nuvärde
  på cirka 0,06 miljoner euro. Vägen ger i stället:
  - en kortare omväg, 2,5 i stället för 4,5 minuter per tur;
  - alla 20 turer i stället för 17;
  - Ö kan behålla sina avgångar i pulsen.

Vägen ger dessutom nytta för annan trafik.

**Intäkter.** Det tillkommande påstigandet är litet i sommardata, cirka 1–2 påstigande per vardag vid den nya
hållplatsen i Möckelö Strand. Biljettintäkterna påverkar därför inte bedömningen.

![Figur 5.1](../output/kartor/b5_1_kalkyl.png)

*Figur 5.1. Förändrad driftkostnad per år per förslag (bas; strecken anger låg–hög) och nyckeltal.*

## 5.3 Osäkerheter

- **Enhetskostnader:** de är schabloner. Avtalspriserna kan avvika, särskilt för fordon, där det har
  betydelse om fordonen är eldrivna och om operatören har en reservbuss.
- **Vardagar per år:** 250 vardagar är ett antagande. Tidtabellen kan skilja mellan termin och sommar.
- **Fordonstimmar:** den extra bussen i 1a har beräknats med minsta möjliga omloppstid. Kan bussen samordnas
  med annan trafik, till exempel skolskjutsar, kan kostnaden bli lägre.
- **Kilometer för den befintliga vägen** till Möckelö Strand ny är mätta i beställarens skiss (cirka 1,36 km
  enkel väg). Med OSRM-vägdragning kan längden ändras något.
