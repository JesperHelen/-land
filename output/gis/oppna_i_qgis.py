# -*- coding: utf-8 -*-
"""Lägger in PM:ets kartlager i QGIS, grupperade per kapitel, med sparade stilar.

Kör i QGIS: Insticksprogram > Python-konsol > Visa redigerare > Öppna skript (denna fil) > Kör skript.
Ligger skriptet i samma mapp som linjenatsutredning.gpkg hittas filen automatiskt, annars får du välja den.
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

# (grupp, [lager uppifrån och ned], tänd vid start)
GRUPPER = [
    ('Kap 3 Hållplatslägen (fig 3.1–3.2)', ['a3_nya_hallplatser', 'a3_behov_ny_linjestrackning', 'a3_hallplatsbedomning',
                                           'a3_nya_hallplatser_400m', 'a3_behov_400m'], True),
    ('Kap 2 Täckning och turtäthet (fig 2.1–2.3)', ['a2_tackning_per_ruta', 'a2_tackningsytor'], False),
    ('Kap 1 OD-matris (fig 1.2–1.5)', ['a1_zoner_pastigande', 'a1_omfordelning_centrum', 'a1_od_FM_korrigerad',
                                      'a1_od_FM_levererad', 'a1_od_EM_korrigerad', 'a1_od_EM_levererad'], False),
    ('Bakgrund', ['00_hallplatser', '00_stadslinjer_forskjutna', '00_stadslinjer', '00_befolkningsrutor', '00_land'], True),
]
EJ_TANDA = {'00_stadslinjer', '00_befolkningsrutor', '00_hallplatser', 'a1_od_FM_levererad', 'a1_od_EM_korrigerad', 'a1_od_EM_levererad'}

projekt = QgsProject.instance()
projekt.setCrs(QgsCoordinateReferenceSystem('EPSG:3067'))
rot = projekt.layerTreeRoot()
for grupp, lager, tand in GRUPPER:
    g = rot.addGroup(grupp)
    g.setItemVisibilityChecked(tand)
    for namn in lager:
        lyr = QgsVectorLayer(f'{GPKG}|layername={namn}', namn, 'ogr')   # standardstilen laddas automatiskt
        if not lyr.isValid():
            print('Kunde inte läsa lagret', namn)
            continue
        projekt.addMapLayer(lyr, False)
        nod = g.addLayer(lyr)
        nod.setItemVisibilityChecked(namn not in EJ_TANDA)
        nod.setExpanded(False)
print('Klart: lager inlagda från', GPKG)
