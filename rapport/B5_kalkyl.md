# 5 Ekonomisk kalkyl (överslag)

> **Sammanfattning.** Förslag 1a, Möckelö Strand via dagens gator, kräver en sjätte buss om alla turer
> ska trafikera den nya hållplatsen. Driftkostnaden ökar då med cirka 216 000 euro per år (176 000–259 000).
> Det motsvarar cirka 1 200 euro per år för var och en av de 179 invånare som får bättre tillgänglighet.
> Förslag 1b ger samma täckning för cirka 4 600 euro per år, enbart genom fler körda kilometer, eftersom
> bussen redan växlar mellan linje V och Ö. Paket A (1b, 2 och 3) är i praktiken kostnadsneutralt i drift
> (+2 300 euro per år).
> Därtill kommer investeringar i två nya hållplatslägen och förlängningen av Norrgårdsvägen. Ur busstrafikens
> perspektiv är vägförlängningen motiverad om den kostar mindre än 2,4–3,6 miljoner euro, vilket är
> nuvärdet av merkostnaden för 1a över 20 år.

## 5.1 Metod och antaganden

Kalkylen omfattar förändrad driftkostnad per år jämfört med i dag:

> Δ driftkostnad = Δ fordon × fordonskostnad + Δ fordonstimmar × timkostnad + Δ fordonskm × km-kostnad

- **Förändringar:** Δ fordon, Δ omloppstid (fordonstimmar) och Δ km per vardag kommer från
  omloppsverifieringen i kapitel 4.
- **Årsvolym:** 250 vardagar per år med typvardagens tidtabell. GTFS-underlaget omfattar bara hösten 2026,
  så helårsvolymen är ett antagande. Lördagstrafiken, med fem turer per linje, påverkas bara genom körda
  kilometer.
- **Enhetskostnader** (euro, prisnivå 2026):

  | Kostnadspost | Låg | Bas | Hög |
  |---|---|---|---|
  | Fordon (kapital, försäkring, uppställning), per fordon och år | 45 000 | 60 000 | 75 000 |
  | Fordonstimme (förare inkl. sociala avgifter och omkostnader) | 42 | 50 | 58 |
  | Fordonskilometer (energi, däck, underhåll) | 0,7 | 0,9 | 1,2 |
  | Nytt hållplatsläge (engångs) | 8 000 | 15 000 | 30 000 |

  Värdena utgår från Trivector (2023), *Trafikeringskostnader för buss 2019 och 2045*, för Trafikverket.
  Där anges för tätortstrafik 2019 cirka 0,65 MSEK per fordon och år och cirka 480 kr per fordonstimme.
  Värdena är omräknade till euro och uppräknade till 2026. De är schabloner och ska ersättas med
  avtalspriserna i landskapsregeringens trafikavtal.
- **Kalkylränta och tid:** nuvärden har beräknats med 3,5 % kalkylränta och 20 års kalkyltid.

## 5.2 Resultat

*Tabell 5.1. Förändrad driftkostnad per år jämfört med i dag (euro, prisnivå 2026).*

| Förslag | Bussar | Fordonstimmar per år | Fordonskm per år | Driftkostnad per år, bas (låg–hög) | Per invånare med bättre tillgänglighet |
|---|---|---|---|---|---|
| 1a alla turer | +1 | +2 900 | +13 150 | +216 000 (176 000–259 000) | 1 209 €/år |
| 1a bara 8 turer | 0 | +28 | +5 650 | +6 000 | 36 €/år |
| 1b förlängd Norrgårdsvägen | 0 | +12 | +4 400 | +4 600 (3 600–6 000) | 26 €/år |
| 2 N2 | 0 | +2 | 0 | ±0 | – |
| 3 Bo-Bil | 0 | 0 | −2 500 | −2 000 | – |
| Paket A (1b, 2, 3) | 0 | +12 | +1 900 | +2 300 (1 900–3 000) | 8 €/år |
| Paket A robust (1b på 15 av 20 turer) | 0 | +12 | +850 | +1 400 (1 100–1 800) | 5 €/år |
| Paket B (1a, 2, 3) | +1 | +2 900 | +10 700 | +214 000 (174 000–256 000) | 771 €/år |

**Förslag 1a.** Merkostnaden för 1a med alla turer domineras av den sjätte bussen, cirka 60 000 euro per år,
och dess förartimmar, cirka 145 000 euro per år. Kan operatören använda en befintlig reservbuss faller
fordonskostnaden bort, och driftkostnaden blir cirka 156 000 euro per år. Reserven för fordonsbortfall
minskar då. Att bara trafikera de 8 turer som ryms kostar lite, men ger ett oregelbundet utbud som inte
rekommenderas.

**Förlängningen av Norrgårdsvägen** har inte kostnadsberäknats. Merkostnaden för 1a jämfört med 1b är
cirka 212 000 euro per år (172 000–253 000). Med 3,5 % kalkylränta motsvarar det ett nuvärde på
2,4–3,6 miljoner euro över 20 år. En vägförlängning som kostar mindre än så är ur busstrafikens perspektiv
billigare än att köra 1a med en extra buss. Vägen ger dessutom nytta för annan trafik.

**Intäkter.** Det tillkommande påstigandet är litet i sommardata, cirka 1–4 påstigande per vardag för
paket A. Biljettintäkterna påverkar därför inte bedömningen.

![Figur 5.1](../output/kartor/b5_1_kalkyl.png)

*Figur 5.1. Förändrad driftkostnad per år per förslag (bas; strecken anger låg–hög) och nyckeltal.*

## 5.3 Osäkerheter

- **Enhetskostnader:** de är schabloner. Avtalspriserna kan avvika, särskilt för fordon, där det har
  betydelse om fordonen är eldrivna och om operatören har en reservbuss.
- **Vardagar per år:** 250 vardagar är ett antagande. Tidtabellen kan skilja mellan termin och sommar.
- **Fordonstimmar:** den extra bussen i 1a har beräknats med minsta möjliga omloppstid. Kan bussen samordnas
  med annan trafik, till exempel skolskjutsar, kan kostnaden bli lägre.
