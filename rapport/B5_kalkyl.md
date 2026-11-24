# 5 Kostnad – fordonskilometer och fordon

> **Sammanfattning.** Kostnaden för varje utredningsalternativ (UA) redovisas som förändrade
> fordonskilometer och om linjen kräver fler fordon än i dag för att kunna hållas. I dag körs stadslinjerna
> Norra, Södra, Västra och Östra med fem fordon och cirka 1 287 fordonskilometer per vardag. Alla huvudalternativ (★) ryms med
> dagens fem fordon.
>
> - **UA 1a – Möckelö Strand ny via dagens vägar:**
>   - ★ med Västra och Östra sammanslagna (16 av 20 turer): +44 fordonskm per vardag, cirka +11 500 per år; inga fler
>     fordon;
>   - alla turer med dagens tidtabell kräver ett sjätte fordon (+55 fordonskm per vardag) och är utesluten.
> - **UA 1b – Möckelö Strand ny via förlängd Norrgårdsvägen ★:** Västra och Östra sammanslagna, 16 av 20 turer:
>   +25 fordonskm per vardag, cirka +6 500 per år; inga fler fordon.
> - **UA 2 – N2 på linje Östra ★:** ±0 fordonskm (hållplatsen ligger på linjens väg); inga fler fordon.
> - **UA 3 – Linje Norra via Bo-Bil ★:** +10 fordonskm per vardag, eftersom bussen måste vända vid Maxinge för att
>   nå Bo-Bil (450 m per tur); inga fler fordon.
> - **UA 4 – Linje Västra–Östra via flygplatsen:**
>   - ★ Västra och Östra sammanslagna (16 av 20 turer): +27 fordonskm per vardag, cirka +7 200 per år; inga fler fordon;
>   - UA 4Y med de tre flygturerna: +5 fordonskm per vardag; inga fler fordon;
>   - extra turer för de tre flyg som dagens tidtabell inte når (avgång 07:15, ankomst 10:35 och 21:35):
>     +44 fordonskm per vardag, cirka +10 900 per år; körs av befintliga fordon;
>   - bara förlängning av Västra kräver ett sjätte fordon och är utesluten.
> - **UA 5 – Linje Västra via Cedersvägen, linje Norra rakt på Västra utfarten ★:** −1 fordonskm per vardag, eftersom
>   linje Norras väg rakt på är kortare än svängen; inga fler fordon. Varianten med bara linje Norra rakt på ger
>   −4 fordonskm per vardag.
>
> - **UA 6 – Linje Norra i båda riktningarna (kräver extra buss):** +257 fordonskm per vardag och ett extra fordon.
> - **UA 7 – Kvällstrafik efter efterfrågan:** −3 fordonskm per vardag (Västras tre kvällsturer körs som Norra
>   moturs); inga fler fordon. Därtill kostnaden för några anropsstyrda resor på Västra per kväll.
>
> Kilometrarna är vägavstånd längs gatunätet (OSRM).

## 5.1 Metod

- **Fordon och fordonskilometer per vardag** kommer från omloppsverifieringen i kapitel 4: antalet fordon som
  behövs för att köra typvardagens tidtabell med alternativet, och de körda kilometrarna i omloppen.
- **Fler fordon** behövs när tidtabellen med alternativet inte kan köras med dagens fem fordon (de alternativ
  som då krävs har uteslutits, eftersom ramen är inga fler fordon).
- **Årsvolym:** 250 vardagar per år med typvardagens tidtabell, plus lördagstrafiken med fem turer per linje.
  Samma andel av turerna som på vardagar antas gå via den nya sträckan. GTFS-underlaget omfattar bara hösten
  2026, så helårsvolymen är ett antagande.

## 5.2 Resultat

*Tabell 5.1. Fordon och fordonskilometer jämfört med i dag (fem fordon, cirka 1 287 fordonskm per vardag).
Varje UA för sig.*

| UA | Fordon | Fler fordon? | Fordonskm per vardag | Fordonskm per år |
|---|---|---|---|---|
| UA 1a dagens vägar, alla 20 turer – utesluten | 6 | **Ja, +1** | +55 | +14 400 |
| UA 1a dagens vägar, dagens tidtabell (8 av 20 turer) | 5 | Nej | +22 | +5 800 |
| UA 1a ★ dagens vägar, Västra och Östra sammanslagna (16 av 20 turer) | 5 | Nej | +44 | +11 500 |
| UA 1b ★ förlängd Norrgårdsvägen, Västra och Östra sammanslagna (16 av 20 turer) | 5 | Nej | +25 | +6 500 |
| UA 2 ★ N2 på linje Östra | 5 | Nej | ±0 | ±0 |
| UA 3 ★ Linje Norra via Bo-Bil | 5 | Nej | +10 | +2 600 |
| UA 4 flygplatsen, alla 20 turer – utesluten | 6 | **Ja, +1** | +34 | +9 000 |
| UA 4 ★ flygplatsen, Västra och Östra sammanslagna (16 av 20 turer) | 5 | Nej | +27 | +7 200 |
| UA 4 flygplatsen, dito + Solberget indragen (16 av 20) | 5 | Nej | +27 | +7 200 |
| UA 4Y flygturerna (3 av 3), Västra och Östra sammanslagna | 5 | Nej | +5 | +1 700 |
| UA 4 extra turer för flygen 07:15, 10:35 och 21:35 (tabell 5.2) | 5 | Nej | +44 | +10 900 |
| UA 5 ★ svängen till linje Västra, Västra och Östra sammanslagna (17 av 20 Västra-turer) | 5 | Nej | −1 | −200 |
| UA 5 svängen till linje Västra, dagens drift (16 av 20 Västra-turer) | 5 | Nej | −1 | −200 |
| UA 5 variant: bara linje Norra rakt på (svängen utan buss) | 5 | Nej | −4 | −1 000 |
| UA 6 linje Norra i båda riktningarna (22 turer moturs, kräver extra buss) | 6 | **Ja, +1** | +257 | +67 200 |
| UA 7 kvällstrafik: Norra åt båda hållen efter kl. 18 i stället för Västra | 5 | Nej | −3 | −900 |

**Extra turer för flygen (UA 4).** Tre flyg nås inte av dagens Västra-turer. De extra turerna är Västra-turer via
flygplatsen (32 minuter, 14,5 km längs vägarna) och körs av ett fordon som står stilla, så inget extra fordon
behövs.

*Tabell 5.2. Extra Västra-turer för flygen.*

| Flyg | Extra tur | Körs av | Fordonskm per vardag | Fler fordon? |
|---|---|---|---|---|
| Avgång 07:15 | 05:15 (vid flygplatsen 05:32) | omlopp 204, som i dag börjar 06:50 | +14,5 | Nej |
| Ankomst 10:35 | 10:50 (vid flygplatsen 11:07) | omlopp 204, i uppehållet 10:16–14:20 | +14,5 | Nej |
| Ankomst 21:35 | 21:50 (vid flygplatsen 22:07) | omlopp 205, efter sista turen 21:13 | +14,5 | Nej |
| **Summa** | | | **+43,5** | **Nej** |

Turen 10:50 ryms i ett uppehåll i omlopp 204, men uppehållet används troligen för förarens rast. Morgon- och
kvällsturen förlänger trafikdygnet för omlopp 204 och 205; anropsstyrd trafik eller taxi kan vara ett
alternativ för dessa flyg.

**UA 1a och 1b.** Med alla turer via Möckelö Strand ny ryms inte varven Västra + Östra inom timmen, och ett sjätte
fordon behövs. Med Västra och Östra sammanslagna ryms 16 av 20 turer med dagens fem fordon (avsnitt 4.5). Omvägen är
2,7 km per tur via dagens vägar (1a) och 1,6 km per tur via förlängd Norrgårdsvägen (1b), vilket ger +44
respektive +25 fordonskm per vardag. Förlängningen av Norrgårdsvägen sparar alltså cirka 19 fordonskm per
vardag (cirka 5 000 per år) jämfört med 1a, och ger dessutom större marginal i centrum (minst 7,5 i stället
för 5,5 minuter per varv) och att Östra kan behålla sina avgångar i pulsen.

**UA 4.** Med alla turer via flygplatsen behövs ett sjätte fordon. Med Västra och Östra sammanslagna ryms 16 av 20
turer med dagens fem fordon. Omvägen är 1,7 km per tur. Att dra in Solberget på några Östra-turer ger inga fler
turer och ändrar inte fordonskilometrarna nämnvärt.

**UA 5.** Längs gatunätet är Norras väg rakt på cirka 185 m kortare per tur än svängen, och Västra kör lika mycket
längre. Eftersom Norra kör fler turer genom svängen än Västra minskar fordonskilometrarna något. Antalet fordon ändras
inte.

**Intäkter.** Det tillkommande påstigandet vid den nya hållplatsen i Möckelö Strand beräknas till 1,5–6,5 per
vardag med höstens nivå, dvs. cirka 400–1 600 resor per år.

![Figur 5.1](../output/kartor/b5_1_kalkyl.png)

*Figur 5.1. Förändrade fordonskilometer per vardag per UA jämfört med i dag. Rött anger att alternativet kräver
fler fordon.*

## 5.3 Osäkerheter

- **Vardagar per år:** 250 vardagar är ett antagande. Tidtabellen kan skilja mellan termin och sommar.
- **Fordon:** antalet fordon gäller typvardagens tidtabell med omloppen enligt kapitel 4. Operatörens
  reservfordon ingår inte.
- **Kilometer** är vägavstånd längs gatunätet (OSRM). Den befintliga vägen till Möckelö Strand ny är 1,37 km
  enkel väg, i stort sett som i beställarens skiss.
