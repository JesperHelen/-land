# -*- coding: utf-8 -*-
"""Lägger in PM:ets kartlager i QGIS, grupperade per kapitel och per utredningsalternativ, med sparade stilar,
och sparar projektet som linjenatsutredning.qgz bredvid GeoPackage-filen.

Kör i QGIS: Insticksprogram > Python-konsol > Visa redigerare > Öppna skript (denna fil) > Kör skript.
Ligger skriptet i samma mapp som linjenatsutredning.gpkg hittas filen automatiskt, annars får du välja den.
Därefter räcker det att öppna linjenatsutredning.qgz (Projekt > Öppna). Har du en äldre linjenatsutredning.qgz:
öppna den inte – kör skriptet i ett nytt, tomt projekt så skrivs den över med de aktuella lagren.
Varje utredningsalternativ (UA) har en grupp med huvudalternativet. Grupperna 'Systemeffekter' och 'Övriga
alternativ' är exklusiva: bara ett scenario visas i taget (klicka i det du vill se).
Vägdragning längs gatorna: kör rutta_med_osrm.py (samma mapp) – det ruttar linjerna med OSRM och uppdaterar lagren.
"""
import os

from qgis.core import QgsCoordinateReferenceSystem, QgsProject, QgsRectangle, QgsVectorLayer
from qgis.PyQt.QtWidgets import QFileDialog

try:
    GPKG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'linjenatsutredning.gpkg')
except NameError:
    GPKG = ''
if not os.path.exists(GPKG):
    GPKG, _ = QFileDialog.getOpenFileName(None, 'Välj linjenatsutredning.gpkg', '', 'GeoPackage (*.gpkg)')


def L(lager, namn=None, filter_=None, tand=True):
    """Ett lager i lagerträdet: (lagernamn i GPKG, visningsnamn, filter (OGR-uttryck), tänt vid start)."""
    return (lager, namn or lager, filter_, tand)


def G(namn, poster, tand=False, exklusiv=False):
    """En undergrupp: exklusiv = bara ett av lagren/undergrupperna kan vara tänt i taget (välj scenario)."""
    return {'grupp': namn, 'poster': poster, 'tand': tand, 'exklusiv': exklusiv}


u_ = lambda uid: f'"ua" = \'{uid}\''
sc = lambda sid: f'"scenario" = \'{sid}\''


def systemeffekt(sid, rubrik, tand=False):
    """Förändrad turtäthet (grön/röd) ovanpå turtätheten med UA:t, för ett scenario."""
    lag = [] if sid == 'idag' else [L('b4_tackning_forandring', 'Förändring mot i dag (grön bättre, röd sämre)', sc(sid))]
    return G(rubrik, lag + [L('b4_tackning_scenarier', 'Turtäthet inom 400 m' + ('' if sid == 'idag' else ' med UA:t'),
                              sc(sid))], tand)


# (grupp, [lager och undergrupper uppifrån och ned], tänd vid start)
# En grupp per utredningsalternativ (UA) med huvudalternativet – det mest realistiska. Övriga driftformer
# (bl.a. uteslutna som kräver fler bussar) finns i gruppen "Övriga alternativ" och redovisas i rapporten.
GRUPPER = [
    ('Kap 4 Utredningsalternativ (UA)', [
        G('UA 1a – Möckelö Strand ny via dagens vägar (V och Ö sammanslagna)', [
            L('b4_ua_hallplatser', 'Ny hållplats', u_('1a')),
            L('b4_ua_korvagar', 'Körväg: befintlig väg fram och tillbaka (2 + 2 min)', u_('1a')),
            L('b4_tackning_forandring', 'Förändrad turtäthet (16 av 20 turer)', sc('1a_VO')),
            L('b4_ua_linjer', 'Linje V–Ö (V och Ö sammanslagna)', u_('1a')),
        ], True),
        G('UA 1b – Möckelö Strand ny via förlängd Norrgårdsvägen (slinga, V och Ö sammanslagna)', [
            L('b4_ua_hallplatser', 'Ny hållplats', u_('1b')),
            L('b4_ua_korvagar', 'Körväg: förlängningen (planerad, 1 min) och befintlig väg tillbaka (2 min)', u_('1b')),
            L('b4_tackning_forandring', 'Förändrad turtäthet (16 av 20 turer)', sc('1b')),
            L('b4_ua_linjer', 'Linje V–Ö (bussen fortsätter V → Ö efter 0,5 min)', u_('1b')),
        ]),
        G('UA 2 – N2 på linje Ö', [
            L('b4_ua_hallplatser', 'Ny hållplats N2', u_('2')),
            L('b4_tackning_forandring', 'Förändrad turtäthet', sc('2')),
            L('b4_ua_linjer', 'Linje Ö', u_('2')),
        ]),
        G('UA 3 – Linje N via Bo-Bil', [
            L('b4_ua_hallplatser', 'Bo-Bil (ny) och Vikingagränd (utgår)', u_('3')),
            L('b4_ua_korvagar', 'Körväg som utgår och ny körväg', u_('3')),
            L('b4_tackning_forandring', 'Förändrad turtäthet', sc('3')),
            L('b4_ua_linjer', 'Linje N via Bo-Bil', u_('3')),
        ]),
        G('UA 4 – Linje V–Ö via flygplatsen (V och Ö sammanslagna)', [
            L('b4_ua_hallplatser', 'Ny hållplats vid terminalen', u_('4')),
            L('b4_ua_korvagar', 'Körväg Posten – flygplatsen – Norra Svibyvägen', u_('4')),
            L('b4_tackning_forandring', 'Förändrad turtäthet (16 av 20 turer)', sc('4_VO')),
            L('b4_ua_linjer', 'Linje V–Ö via flygplatsen', u_('4')),
        ]),
        G('Systemeffekter – turtäthet inom 400 m, huvudalternativ per UA (välj ett)', [
            systemeffekt('idag', 'I dag'),
            systemeffekt('1a_VO', 'UA 1a – V och Ö sammanslagna (16 av 20 turer)', True),
            systemeffekt('1b', 'UA 1b – förlängd Norrgårdsvägen, V och Ö sammanslagna (16 av 20 turer)'),
            systemeffekt('2', 'UA 2 – N2 på linje Ö'),
            systemeffekt('3', 'UA 3 – Linje N via Bo-Bil'),
            systemeffekt('4_VO', 'UA 4 – V och Ö sammanslagna (16 av 20 turer)'),
        ], False, exklusiv=True),
        G('Övriga alternativ (redovisas i rapporten, välj ett)', [
            systemeffekt('1a', 'UA 1a alla turer, dagens tidtabell – utesluten (6 bussar)'),
            systemeffekt('1a_ryms', 'UA 1a dagens tidtabell (8 av 20 turer)'),
            systemeffekt('4', 'UA 4 alla turer, dagens tidtabell – utesluten (6 bussar)'),
            systemeffekt('4_VO_sol', 'UA 4 V och Ö sammanslagna, Solberget indragen (16 av 20 turer)'),
            systemeffekt('4_Y', 'UA 4Y bara flygturerna (8 av 8), V och Ö sammanslagna'),
        ], False, exklusiv=True),
        G('Sammanslagning av linjer (fig 4.8)', [L('b4_sammanslagning_omraden', 'Områden – behövd tid per tur')]),
        L('b4_nyckeltal_scenarier', 'Nyckeltal per UA och driftform (tabell)'),
    ], True),
    ('Kap 3 Hållplatslägen (fig 3.1–3.2)', [L(n) for n in ['a3_nya_hallplatser', 'a3_behov_ny_linjestrackning',
                                                         'a3_hallplatsbedomning', 'a3_nya_hallplatser_400m',
                                                         'a3_behov_400m']], False),
    ('Kap 2 Täckning och turtäthet (fig 2.1–2.3)', [L('a2_tackning_per_ruta'), L('a2_tackningsytor')], False),
    ('Kap 1 OD-matris (fig 1.2–1.5)', [L('a1_zoner_pastigande'), L('a1_omfordelning_centrum'),
                                      L('a1_od_FM_korrigerad'), L('a1_od_FM_levererad', tand=False),
                                      L('a1_od_EM_korrigerad', tand=False), L('a1_od_EM_levererad', tand=False)], False),
    ('Bakgrund', [L('00_hallplatser', 'Hållplatser (avgångar per vardag)', tand=False),
                  L('00_viapunkter', 'Via-punkter för OSRM ("gömda stopp", redigerbara)', tand=False),
                  L('00_stadslinjer_forskjutna', 'Stadslinjer i dag – vägdragning, förskjutna där de delar gata'),
                  L('00_stadslinjer', 'Stadslinjer i dag – vägdragning, en geometri per linje', tand=False),
                  L('00_segment', 'Segment hållplats–hållplats (källa: OSRM, skiss eller rak)', tand=False),
                  L('00_befolkningsrutor', 'Befolkning 2024 (1 km-rutor)', tand=False), L('00_land', 'Land')], True),
]

projekt = QgsProject.instance()
projekt.setCrs(QgsCoordinateReferenceSystem('EPSG:3067'))
rot = projekt.layerTreeRoot()
for g in list(rot.children()):                      # körs skriptet igen: ta bort gamla grupper med samma namn
    if g.name() in [n for n, *_ in GRUPPER]:
        rot.removeChildNode(g)
saknas = []


def lagg_till(foralder, innehall):
    for post in innehall:
        if isinstance(post, dict):                           # undergrupp
            g = foralder.addGroup(post['grupp'])
            lagg_till(g, post['poster'])
            if post['exklusiv']:
                g.setIsMutuallyExclusive(True)
                tanda = [i for i, p in enumerate(post['poster']) if isinstance(p, dict) and p['tand']]
                g.setIsMutuallyExclusive(True, tanda[0] if tanda else 0)
            g.setItemVisibilityChecked(post['tand'])
            g.setExpanded(post['tand'])
            continue
        lager, namn, filter_, tand = post
        lyr = QgsVectorLayer(f'{GPKG}|layername={lager}', namn, 'ogr')   # standardstilen laddas automatiskt
        if not lyr.isValid():
            saknas.append(lager)
            continue
        if filter_:
            lyr.setSubsetString(filter_)
            if lyr.featureCount() == 0:
                saknas.append(f'{lager} [{filter_}] – inga objekt')
        projekt.addMapLayer(lyr, False)
        nod = foralder.addLayer(lyr)
        nod.setItemVisibilityChecked(tand)
        nod.setExpanded(False)


for grupp, innehall, tand in GRUPPER:
    g = rot.addGroup(grupp)
    lagg_till(g, innehall)
    g.setItemVisibilityChecked(tand)
    g.setExpanded(tand)

# starta inzoomat på Mariehamn
MARIEHAMN = QgsRectangle(104300, 6679500, 111800, 6688300)
try:
    from qgis.core import QgsReferencedRectangle
    projekt.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(MARIEHAMN, projekt.crs()))
except Exception:
    pass
try:
    from qgis.utils import iface
    iface.mapCanvas().setExtent(MARIEHAMN); iface.mapCanvas().refresh()
except Exception:
    pass
if saknas:
    print('OBS – lager som saknas eller är tomma:', *saknas, sep='\n  ')

QGZ = os.path.join(os.path.dirname(GPKG), 'linjenatsutredning.qgz')
if projekt.write(QGZ):
    print('Projektet sparat:', QGZ)
print('Klart: lager inlagda från', GPKG)
