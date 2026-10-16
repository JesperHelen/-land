# B4.5 Genomgående linje N/S – prövning mot nordostområdena

## Syfte och metod
Beställaren har bett om en prövning av om linje N och S kan slås samman till en genomgående linje (bussen
fortsätter från N till S efter 0,5 min, i enlighet med förarnas byten Syd ↔ Norr i dagens omlopp) så att
linje N kan förlängas mot Örtvägen, Lillåkersvägen och Österkalmare utan fler bussar. Kravet är detsamma som för
V/Ö: varvet N + S ryms inom 60 min med minst 5 min i centrum, och dagens omlopp i övrigt är oförändrat.
Varje N-tur har prövats för sig mot det härledda omloppet (`src/b4_ns.py`, `b4_omlopp.genomgaende_ryms`); största
förlängning per tur har sökts i steg om 0,1 min (sökgräns 12 min). Följande tidsutrymmen har prövats: enbart
sammanslagning, sammanslagning med Bo-Bil i stället för Vikingagränd (UA 3), sammanslagning med indragna hållplatser
på linje S, samt båda tillsammans.

## Resultat
**Tidsutrymme (analytiskt, mediankörtid N 26 min, S 23 min).**

| Par | Pulsen kvar, marginal 5 min | Partnern startar senare, 5 min | Utan puls, marginal 3,5 min |
|---|---|---|---|
| N → S | 3,5 min | 6,0 min | 7,5 min |
| S → Ö | 6,5 min | 9,0 min | 10,5 min |

**Tidsutrymme per N-tur (omloppsverifierat).** Sammanslagning ger 6,0 min på 17 av 22 N-turer; 07:50-turen har bara 1,0 min eftersom varvet redan i dag har 6 min i
centrum, och turerna 09:50, 17:50 och 20:20 samt 13:20 (fyra turer) har obegränsat utrymme eftersom bussen därefter ställs upp
(redovisas som sökgränsen 12 min). Bo-Bil ger inget utrymme (nettoeffekt +0,1 min: 0,4 min kortare väg men 0,5 min
uppehåll) och sänker utrymmet till 5,9 min. Indragning av de fem kandidaterna på S (Gröna Udden, Torggatan,
Neptunigatan, Skillnadsgatan, Hamngatan; **antagande 0,25 min per hållplats**, dvs. 1,25 min per tur) ökar utrymmet till 7,1–7,2 min.

**Antal av 22 N-turer som ryms per område.**

| Område | Invånare | Behov | Sammanslagning | + Bo-Bil | + indragna hpl på S | + båda |
|---|---|---|---|---|---|---|
| Örtvägen | 125 | 4,4 min | 21 | 21 | 21 | 21 |
| Lillåkersvägen | 183 | 6,5 min | 4 | 4 | 21 | 21 |
| Österkalmare | 90 | 10,3 min | 4 | 4 | 4 | 4 |

## Slutsatser
1. Örtvägen kan trafikeras av 21 av 22 N-turer enbart genom sammanslagning av N och S (07:50 faller bort).
2. Lillåkersvägen kräver ett tillskott av tid: indragning av de fem S-hållplatserna gör att 21 av 22 turer ryms, men
   resultatet bygger på det antagna tidsvärdet per hållplats och på att påstigandet (sommardata) bekräftas med terminsdata.
3. Österkalmare (+10,3 min) ryms inte; området kräver omläggning (B4.6).
4. Bo-Bil bidrar inte med tidsutrymme och påverkar därför inte sammanslagningens kapacitet.
5. Utan puls (utrymme 7,5 min för N/S och 10,5 min för S/Ö vid marginal 3,5 min) skulle Lillåkersvägen rymmas utan
   indragna hållplatser, men marginalen understiger då beställarens krav på 5 min och pulsen i centrum går förlorad.
   S/Ö är dessutom ingen koppling i dagens omlopp och kräver ny omloppsstruktur; varianten är endast prövad analytiskt.

Underlag: `data/processed/b4_ns.json`, `b4_ns_turer.csv`, `b4_ns_omraden.geojson`; figur `output/kartor/b4_16_ns.png`.
