# -*- coding: utf-8 -*-
"""Lägger in PM:ets kartlager i QGIS, grupperade per kapitel och per linjeförslag, med sparade stilar,
och sparar projektet som linjenatsutredning.qgz bredvid GeoPackage-filen.

Kör i QGIS: Insticksprogram > Python-konsol > Visa redigerare > Öppna skript (denna fil) > Kör skript.
Ligger skriptet i samma mapp som linjenatsutredning.gpkg hittas filen automatiskt, annars får du välja den.
Därefter räcker det att öppna linjenatsutredning.qgz (Projekt > Öppna).
"""
import os

from qgis.core import QgsCoordinateReferenceSystem, QgsProject, QgsVectorLayer
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


# (grupp, [lager uppifrån och ned], tänd vid start); undergrupper anges som (namn, [...], tänd)
GRUPPER = [
    ('Kap 4 Linjeförslag', [
        ('Paket A – Möckelö Strand (1b), N2, Bo-Bil (rekommenderat)', [
            L('b4_forslag_hallplatser', 'Nya och ändrade hållplatser', '"forslag" IN (\'1b\', \'2\', \'3\')'),
            L('b4_linjer_forslag', 'Linjer i paket A', '"forslag" IN (\'1b_VÖ\', \'3\')'),
            L('b4_tackning_forandring', 'Förändrad tillgänglighet', '"scenario" = \'paket_A\''),
        ], True),
        ('Förslag 1a – Möckelö Strand, dagens gator', [
            L('b4_forslag_hallplatser', 'Ny hållplats', '"forslag" = \'1a\''),
            L('b4_forslag_korvagar', 'Ny körväg (schematisk)', '"forslag" = \'1a\''),
            L('b4_linjer_forslag', 'Linje V via Möckelö Strand', '"forslag" = \'1a\''),
            L('b4_tackning_forandring', 'Förändrad tillgänglighet (alla turer)', '"scenario" = \'1a\''),
        ], False),
        ('Förslag 1b – Möckelö Strand, förlängd Norrgårdsvägen', [
            L('b4_forslag_hallplatser', 'Ny hållplats', '"forslag" = \'1b\''),
            L('b4_forslag_korvagar', 'Ny körväg (schematisk)', '"forslag" = \'1b\''),
            L('b4_linjer_forslag', 'Linje V och Ö (bussen växlar V ↔ Ö)', '"forslag" = \'1b_VÖ\''),
            L('b4_tackning_forandring', 'Förändrad tillgänglighet', '"scenario" = \'1b_VÖ\''),
        ], False),
        ('Förslag 2 – N2 på linje Ö', [
            L('b4_forslag_hallplatser', 'Ny hållplats N2', '"forslag" = \'2\''),
            L('b4_linjer_forslag', 'Linje Ö', '"forslag" = \'2\''),
            L('b4_tackning_forandring', 'Förändrad tillgänglighet', '"scenario" = \'2\''),
        ], False),
        ('Förslag 3 – linje N via Bo-Bil', [
            L('b4_forslag_hallplatser', 'Bo-Bil (ny) och Vikingagränd (utgår)', '"forslag" = \'3\''),
            L('b4_forslag_korvagar', 'Körväg som utgår och ny körväg', '"forslag" = \'3\''),
            L('b4_linjer_forslag', 'Linje N via Bo-Bil', '"forslag" = \'3\''),
            L('b4_tackning_forandring', 'Förändrad tillgänglighet', '"scenario" = \'3\''),
        ], False),
        ('Systemeffekter – turtäthet inom 400 m', [
            L('b4_tackning_scenarier', 'Med paket A', '"scenario" = \'paket_A\''),
            L('b4_tackning_scenarier', 'I dag', '"scenario" = \'idag\'', False),
            L('b4_nyckeltal_scenarier', 'Nyckeltal per scenario (tabell)'),
        ], False),
        ('Sammanslagning av linjer (fig 4.8)', [
            L('b4_sammanslagning_omraden', 'Områden – behövd tid per tur'),
        ], False),
    ], True),
    ('Kap 3 Hållplatslägen (fig 3.1–3.2)', [L(n) for n in ['a3_nya_hallplatser', 'a3_behov_ny_linjestrackning',
                                                         'a3_hallplatsbedomning', 'a3_nya_hallplatser_400m',
                                                         'a3_behov_400m']], False),
    ('Kap 2 Täckning och turtäthet (fig 2.1–2.3)', [L('a2_tackning_per_ruta'), L('a2_tackningsytor')], False),
    ('Kap 1 OD-matris (fig 1.2–1.5)', [L('a1_zoner_pastigande'), L('a1_omfordelning_centrum'),
                                      L('a1_od_FM_korrigerad'), L('a1_od_FM_levererad', tand=False),
                                      L('a1_od_EM_korrigerad', tand=False), L('a1_od_EM_levererad', tand=False)], False),
    ('Bakgrund', [L('00_hallplatser', 'Hållplatser (avgångar per vardag)', tand=False),
                  L('00_stadslinjer_forskjutna', 'Stadslinjer i dag – vägdragning, förskjutna där de delar gata'),
                  L('00_stadslinjer', 'Stadslinjer i dag – vägdragning, en geometri per linje', tand=False),
                  L('00_befolkningsrutor', 'Befolkning 2024 (1 km-rutor)', tand=False), L('00_land', 'Land')], True),
]

projekt = QgsProject.instance()
projekt.setCrs(QgsCoordinateReferenceSystem('EPSG:3067'))
rot = projekt.layerTreeRoot()


def lagg_till(foralder, innehall):
    for post in innehall:
        if len(post) == 3:                                   # undergrupp
            namn, poster, tand = post
            g = foralder.addGroup(namn)
            g.setItemVisibilityChecked(tand)
            lagg_till(g, poster)
            g.setExpanded(tand)
            continue
        lager, namn, filter_, tand = post
        lyr = QgsVectorLayer(f'{GPKG}|layername={lager}', namn, 'ogr')   # standardstilen laddas automatiskt
        if not lyr.isValid():
            print('Kunde inte läsa lagret', lager)
            continue
        if filter_:
            lyr.setSubsetString(filter_)
        projekt.addMapLayer(lyr, False)
        nod = foralder.addLayer(lyr)
        nod.setItemVisibilityChecked(tand)
        nod.setExpanded(False)


for grupp, innehall, tand in GRUPPER:
    g = rot.addGroup(grupp)
    g.setItemVisibilityChecked(tand)
    lagg_till(g, innehall)
    g.setExpanded(tand)

QGZ = os.path.join(os.path.dirname(GPKG), 'linjenatsutredning.qgz')
if projekt.write(QGZ):
    print('Projektet sparat:', QGZ)
print('Klart: lager inlagda från', GPKG)
