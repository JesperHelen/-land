# -*- coding: utf-8 -*-
"""Export av PM:ets kartlager till QGIS: en GeoPackage (EPSG:3067) med inbäddade lagerstilar.

Alla lager som ritas i kartorna (output/kartor/*.png) sparas som vektorlager i
output/gis/linjenatsutredning.gpkg. Varje lager får en standardstil i GeoPackage-tabellen layer_styles,
som QGIS läser automatiskt när lagret läggs till. Lager med flera kartor får även alternativa stilar,
som väljs i lagrets egenskaper (Symbologi > Stil). Stilarna sparas dessutom som .qml-filer i
output/gis/stilar/ för manuell inläsning.

Kör efter analysstegen:  python src/gis_export.py
"""
import datetime
import json
import math
import sqlite3
import sys
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
from shapely.geometry import LineString

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402
import kartlib as K  # noqa: E402

UT = C.ROT / 'output' / 'gis'
GPKG = UT / 'linjenatsutredning.gpkg'
STILAR = UT / 'stilar'
P = C.PROCESSED
STYLES = []          # (lager, stilnamn, qml, standard)


# ====================================================================== QML-byggstenar (QGIS 3)
def rgba(hexf, alpha=255):
    h = hexf.lstrip('#')
    return f'{int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha}'


def _props(d):
    return ''.join(f'<prop k="{k}" v={quoteattr(str(v))}/>' for k, v in d.items())


def fyll(namn, farg, alpha=255, kant='no', kantfarg='#232323', kantbredd=0.26):
    p = {'color': rgba(farg, alpha), 'style': 'solid' if alpha > 0 else 'no', 'outline_style': kant,
         'outline_color': rgba(kantfarg), 'outline_width': kantbredd, 'outline_width_unit': 'MM', 'joinstyle': 'miter'}
    return (f'<symbol type="fill" name="{namn}" alpha="1" clip_to_extent="1" force_rhr="0">'
            f'<layer class="SimpleFill" enabled="1" locked="0" pass="0">{_props(p)}</layer></symbol>')


def markor(namn, form, farg, storlek, kantfarg='#ffffff', kantbredd=0.3, alpha=255):
    p = {'name': form, 'color': rgba(farg, alpha), 'outline_color': rgba(kantfarg), 'outline_style': 'solid',
         'outline_width': kantbredd, 'outline_width_unit': 'MM', 'size': storlek, 'size_unit': 'MM',
         'scale_method': 'diameter', 'joinstyle': 'bevel', 'angle': 0, 'vertical_anchor_point': 1,
         'horizontal_anchor_point': 1}
    return (f'<symbol type="marker" name="{namn}" alpha="1" clip_to_extent="1" force_rhr="0">'
            f'<layer class="SimpleMarker" enabled="1" locked="0" pass="0">{_props(p)}</layer></symbol>')


def linje(namn, farg, bredd, pil=False, streckad=False, alpha=255, halo=False):
    lager = []
    if halo:
        lager.append(f'<layer class="SimpleLine" enabled="1" locked="0" pass="0">' + _props({
            'line_color': '255,255,255,255', 'line_width': bredd + 0.5, 'line_width_unit': 'MM',
            'capstyle': 'round', 'joinstyle': 'round', 'line_style': 'solid'}) + '</layer>')
    lager.append(f'<layer class="SimpleLine" enabled="1" locked="0" pass="0">' + _props({
        'line_color': rgba(farg, alpha), 'line_width': bredd, 'line_width_unit': 'MM', 'capstyle': 'round',
        'joinstyle': 'round', 'line_style': 'dash' if streckad else 'solid'}) + '</layer>')
    if pil:
        sub = markor(f'@{namn}@{len(lager)}', 'filled_arrowhead', farg, max(1.6, 2.6 * bredd), kantfarg=farg,
                     kantbredd=0, alpha=alpha)
        lager.append(f'<layer class="MarkerLine" enabled="1" locked="0" pass="0">' + _props({
            'placement': 'lastvertex', 'rotate': 1, 'offset': 0, 'interval': 3, 'interval_unit': 'MM'}) + sub + '</layer>')
    return f'<symbol type="line" name="{namn}" alpha="1" clip_to_extent="1" force_rhr="0">{"".join(lager)}</symbol>'


def linje_forskjuten(namn, farg, bredd, mm_per_spar=1.1, attr='forskjutning'):
    """Linjesymbol (vit kant + färg) vars förskjutning i mm styrs av attributet (spår × mm_per_spar)."""
    uttryck = quoteattr('"' + attr + '" * ' + str(mm_per_spar))
    dd = ('<data_defined_properties><Option type="Map"><Option type="QString" name="name" value=""/>'
          '<Option type="Map" name="properties"><Option type="Map" name="offset">'
          '<Option type="bool" name="active" value="true"/>'
          f'<Option type="QString" name="expression" value={uttryck}/>'
          '<Option type="int" name="type" value="3"/></Option></Option>'
          '<Option type="QString" name="type" value="collection"/></Option></data_defined_properties>')
    lager = ''
    for f, b in [('#ffffff', bredd + 0.45), (farg, bredd)]:
        lager += ('<layer class="SimpleLine" enabled="1" locked="0" pass="0">' + _props({
            'line_color': rgba(f), 'line_width': b, 'line_width_unit': 'MM', 'capstyle': 'round', 'joinstyle': 'round',
            'line_style': 'solid', 'offset': 0, 'offset_unit': 'MM'}) + dd + '</layer>')
    return f'<symbol type="line" name="{namn}" alpha="1" clip_to_extent="1" force_rhr="0">{lager}</symbol>'


def r_enkel(sym):
    return f'<renderer-v2 type="singleSymbol" symbollevels="0" forceraster="0" enableorderby="0"><symbols>{sym}</symbols></renderer-v2>'


def r_kategori(attr, kat, symbolfn, ordning=None):
    """kat: [(värde, etikett, symbolargument...)] ; symbolfn(namn, *arg) -> symbol-XML."""
    cats = ''.join(f'<category value={quoteattr(str(v))} label={quoteattr(l)} symbol="{i}" render="true"/>'
                   for i, (v, l, *_) in enumerate(kat))
    syms = ''.join(symbolfn(str(i), *a) for i, (v, l, *a) in enumerate(kat))
    ob = (f' enableorderby="1"><orderby><orderByClause asc="1" nullsFirst="0">{escape(ordning)}</orderByClause></orderby'
          if ordning else ' enableorderby="0"')
    return (f'<renderer-v2 type="categorizedSymbol" attr={quoteattr(attr)} symbollevels="0" forceraster="0"{ob}>'
            f'<categories>{cats}</categories><symbols>{syms}</symbols></renderer-v2>')


def r_klassad(attr, klasser, symbolfn, ordning=None):
    """klasser: [(lägre, övre, etikett, symbolargument...)]."""
    rng = ''.join(f'<range lower="{lo}" upper="{hi}" label={quoteattr(l)} symbol="{i}" render="true"/>'
                  for i, (lo, hi, l, *_) in enumerate(klasser))
    syms = ''.join(symbolfn(str(i), *a) for i, (lo, hi, l, *a) in enumerate(klasser))
    ob = (f' enableorderby="1"><orderby><orderByClause asc="1" nullsFirst="0">{escape(ordning)}</orderByClause></orderby'
          if ordning else ' enableorderby="0"')
    return (f'<renderer-v2 type="graduatedSymbol" attr={quoteattr(attr)} graduatedMethod="GraduatedColor" '
            f'symbollevels="0" forceraster="0"{ob}><ranges>{rng}</ranges><symbols>{syms}</symbols></renderer-v2>')


def etiketter(uttryck, storlek=7.5, farg='#1f1f1e', placering=0, avstand=1.2):
    return ('<labeling type="simple"><settings calloutType="simple">'
            f'<text-style fieldName={quoteattr(uttryck)} isExpression="1" fontSize="{storlek}" fontSizeUnit="Point" '
            f'textColor="{rgba(farg)}" textOpacity="1" fontFamily="Arial" namedStyle="Regular" fontWeight="50">'
            '<text-buffer bufferDraw="1" bufferSize="0.8" bufferSizeUnits="MM" bufferColor="255,255,255,255" '
            'bufferOpacity="0.9" bufferJoinStyle="128"/></text-style>'
            '<text-format multilineAlign="0" wrapChar="|"/>'
            f'<placement placement="{placering}" dist="{avstand}" distUnits="MM" quadOffset="4" priority="5"/>'
            '<rendering obstacle="1" scaleVisibility="0" fontLimitPixelSize="0" upsidedownLabels="0" '
            'displayAll="0" drawLabels="1"/></settings></labeling>')


def qml(renderer, opacitet=1.0, labeling=''):
    return ("<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>\n"
            f'<qgis version="3.28.0" styleCategories="Symbology|Labeling|Rendering" labelsEnabled="{1 if labeling else 0}">'
            f'{renderer}{labeling}<blendMode>0</blendMode><featureBlendMode>0</featureBlendMode>'
            f'<layerOpacity>{opacitet}</layerOpacity></qgis>')


def stil(lager, namn, xml, standard=False):
    STYLES.append((lager, namn, xml, standard))


# ====================================================================== lager
def skriv(gdf, namn):
    gdf = gdf.set_crs(C.CRS_METRISK, allow_override=True) if gdf.crs is None else gdf.to_crs(C.CRS_METRISK)
    gdf.to_file(GPKG, layer=namn, driver='GPKG')
    return namn


def bas():
    skriv(D.land()[['geometry']].assign(typ='land'), '00_land')
    stil('00_land', 'Land', qml(r_enkel(fyll('0', '#f5f3ee', kant='solid', kantfarg='#b3afa4', kantbredd=0.2))), True)

    b = D.befolkning()[['ruta_id', 'Tot_bef', 'Ald_0_14', 'Ald_15_64', 'Ald_65_x', 'geometry']].rename(
        columns={'Tot_bef': 'befolkning', 'Ald_0_14': 'alder_0_14', 'Ald_15_64': 'alder_15_64', 'Ald_65_x': 'alder_65_'})
    skriv(b, '00_befolkningsrutor')
    kl = [(0, 25, '1–24 inv.', '#fde9dc'), (25, 100, '25–99', '#f9c4a5'), (100, 300, '100–299', '#f19066'),
          (300, 800, '300–799', '#d9573a'), (800, 99999, '≥ 800', '#a92a1d')]
    stil('00_befolkningsrutor', 'Befolkning 2024', qml(r_klassad('befolkning', kl, lambda n, f: fyll(n, f, 200, 'solid', '#ffffff', 0.2))), True)
    stil('00_befolkningsrutor', 'Endast rutnät', qml(r_enkel(fyll('0', '#ffffff', 0, 'solid', '#8a877f', 0.2))))

    import s01_vagdragning as V
    geo = V.segmentgeometri(); kedjor = V.linjekedjor()
    t = D.turer_dag(None, C.STADSLINJER).groupby('linje').size()
    vag = 'OSRM' if V.kalla_text().startswith('Linjernas') else 'rak linje mellan hållplatser'
    lin = gpd.GeoDataFrame({'linje': list(kedjor), 'turer_vardag': [int(t.get(l, 0)) for l in kedjor], 'vagdragning': vag},
                           geometry=[shapely.MultiLineString([geo[s] for k in kl for s in k]) for kl in kedjor.values()],
                           crs=C.CRS_METRISK)
    skriv(lin, '00_stadslinjer')
    stil('00_stadslinjer', 'Stadslinjer', qml(r_kategori('linje', [(l, f'Linje {l}', C.FARG_LINJE[l]) for l in C.STADSLINJER],
                                                         lambda n, f: linje(n, f, 0.7, halo=True))), True)
    delar = V.forskjutna_delar()
    skriv(delar, '00_stadslinjer_forskjutna')
    stil('00_stadslinjer_forskjutna', 'Förskjutna stadslinjer',
         qml(r_kategori('linje', [(l, f'Linje {l}', C.FARG_LINJE[l]) for l in C.STADSLINJER],
                        lambda n, f: linje_forskjuten(n, f, 0.7))), True)

    h = pd.read_csv(P / 'a2_hallplatser_avgangar.csv', index_col=0).reset_index().rename(columns={'stop_id': 'stop_id'})
    hg = gpd.GeoDataFrame(h.rename(columns={'avgangar': 'avgangar_vardag'}), geometry=gpd.points_from_xy(h.x, h.y), crs=C.CRS_METRISK)
    hg['stadslinje'] = hg.linjer.apply(lambda s: any(l in str(s).split(',') for l in C.STADSLINJER))
    skriv(hg.drop(columns=['x', 'y']), '00_hallplatser')
    kl = [(0, 15, '1–14 avgångar/vardag', 1.4), (15, 30, '15–29', 1.9), (30, 60, '30–59', 2.5), (60, 999, '≥ 60', 3.2)]
    stil('00_hallplatser', 'Avgångar per vardag', qml(r_klassad('avgangar_vardag', kl, lambda n, s: markor(n, 'circle', '#ffffff', s, '#1f1f1e', 0.25))), True)


def a1():
    zon = pd.read_csv(P / 'a1_zoner_pastigande.csv', index_col=0)
    zon['sum_orig'] = zon.O_FM_orig + zon.O_EM_orig
    zon['sum_korr'] = zon.O_FM_korr + zon.O_EM_korr
    zg = gpd.GeoDataFrame(zon.reset_index().drop(columns=['x', 'y']), geometry=gpd.points_from_xy(zon.x, zon.y), crs=C.CRS_METRISK)
    skriv(zg, 'a1_zoner_pastigande')
    kl = lambda a: [(0, 0.1, '< 0,1 resor/h', 1.2), (0.1, 0.3, '0,1–0,3', 2.0), (0.3, 1, '0,3–1', 3.0), (1, 3, '1–3', 4.6), (3, 99, '≥ 3', 7.0)]
    sym = lambda n, s: markor(n, 'circle', '#3987e5', s, '#184f95', 0.3, alpha=200)
    stil('a1_zoner_pastigande', 'Påstigande korrigerat (fig 1.3 höger)', qml(r_klassad('sum_korr', kl(0), sym, '"sum_korr"'),
         labeling=etiketter('if("sum_korr" >= 1, "omrade", \'\')')), True)
    stil('a1_zoner_pastigande', 'Påstigande ursprungligt (fig 1.3 vänster)', qml(r_klassad('sum_orig', kl(0), sym, '"sum_orig"'),
         labeling=etiketter('if("sum_orig" >= 1, "omrade", \'\')')))

    pos = {z: np.array([r.x, r.y]) for z, r in zon.iterrows()}
    f = pd.read_csv(P / 'a1_centrum_omfordelning.csv')
    f = f.pivot_table(index='till_omrade', columns='period', values='resor_h', aggfunc='sum').fillna(0)
    f['resor_h_FM_EM'] = f.sum(axis=1)
    c = pos[C.CENTRUM]
    fg = gpd.GeoDataFrame({'fran': C.CENTRUM, 'till': f.index, 'resor_h_FM': f.get('FM', 0).values,
                           'resor_h_EM': f.get('EM', 0).values, 'resor_h_FM_EM': f.resor_h_FM_EM.values},
                          geometry=[LineString([c, pos[z]]) for z in f.index], crs=C.CRS_METRISK)
    skriv(fg, 'a1_omfordelning_centrum')
    kl = [(0, 0.02, '< 0,02 resor/h', 0.3), (0.02, 0.1, '0,02–0,1', 0.6), (0.1, 0.3, '0,1–0,3', 1.1), (0.3, 9, '≥ 0,3', 1.8)]
    stil('a1_omfordelning_centrum', 'Flyttade påstigningar (fig 1.2)', qml(r_klassad('resor_h_FM_EM', kl, lambda n, w: linje(n, '#c0392b', w, pil=True)),
         labeling=etiketter('if("resor_h_FM_EM" >= 0.02, "till" || \' +\' || format_number("resor_h_FM_EM", 2), \'\')', placering=2)), True)

    blå = ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b']
    kl = [(0, 0.01, '< 0,01 resor/h', blå[0], 0.15), (0.01, 0.05, '0,01–0,05', blå[1], 0.3), (0.05, 0.1, '0,05–0,1', blå[2], 0.6),
          (0.1, 0.25, '0,1–0,25', blå[3], 1.1), (0.25, 99, '≥ 0,25', blå[4], 1.9)]
    for per, fig in [('FM', '1.4'), ('EM', '1.5')]:
        for typ in ['levererad', 'korrigerad']:
            L = pd.read_csv(P / f'a1_od_{per}_{typ}.csv')
            L = L[(L.fran != L.till) & L.fran.isin(pos) & L.till.isin(pos)].sort_values('resor_h', ascending=False)
            L['andel_kum'] = (L.resor_h.cumsum() / L.resor_h.sum()).round(4)
            L['i_karta'] = L.andel_kum <= 0.85
            L['rang'] = np.arange(1, len(L) + 1)
            L = L[L.resor_h >= 0.001]
            geoms = []
            for r in L.itertuples():
                B, _ = K._bage(pos[r.fran], pos[r.till], n=30)
                geoms.append(LineString(B))
            namn = f'a1_od_{per}_{typ}'
            skriv(gpd.GeoDataFrame(L.round({'resor_h': 5}), geometry=geoms, crs=C.CRS_METRISK), namn)
            stil(namn, f'OD-flöden {per} {typ} (fig {fig})',
                 qml(r_klassad('resor_h', kl, lambda n, fa, w: linje(n, fa, w, pil=True), '"resor_h"')), True)


def a2():
    pkt = pd.read_csv(P / 'a2_delpunkter.csv.gz')
    h = C.DELRUTA_M
    namn = ['Ingen hållplats inom 400 m', 'Mycket låg (1–14 avg/vardag)', 'Låg (15–29)', 'Medel (30–59)', 'God (≥ 60)']
    pkt['geometry'] = shapely.box(pkt.x - h / 2, pkt.y - h / 2, pkt.x + h / 2, pkt.y + h / 2)
    g = gpd.GeoDataFrame(pkt[['ruta_id', 'klass', 'bef', 'geometry']], crs=C.CRS_METRISK)
    y = g.dissolve(by=['ruta_id', 'klass'], aggfunc={'bef': 'sum'}).reset_index()
    y['klass_nr'] = y.klass.astype(int)
    y['klass'] = y.klass_nr.map(dict(enumerate(namn)))
    y['inom_400m'] = np.where(y.klass_nr > 0, 'Ja', 'Nej')
    y['svag_tillg'] = y.klass_nr.map({0: 'Ingen hållplats inom 400 m', 1: 'Mycket låg (1–14)', 2: 'Låg (15–29)'}).fillna('Minst 30 avgångar')
    y = y.rename(columns={'bef': 'invanare'}).round({'invanare': 1})
    skriv(y[['ruta_id', 'klass_nr', 'klass', 'inom_400m', 'svag_tillg', 'invanare', 'geometry']], 'a2_tackningsytor')
    farger = ['#cfcbc2', '#c6dbf5', '#7fb0ec', '#2a78d6', '#0d366b']
    stil('a2_tackningsytor', 'Turtäthet inom 400 m (fig 2.1 höger, 2.2)',
         qml(r_kategori('klass', [(n, n, f) for n, f in zip(namn, farger)], lambda s, f: fyll(s, f)), 0.85), True)
    stil('a2_tackningsytor', 'Täckning 400 m (fig 2.1 vänster)',
         qml(r_kategori('inom_400m', [('Ja', 'Inom 400 m', '#3987e5'), ('Nej', 'Utanför 400 m', '#cfcbc2')], lambda s, f: fyll(s, f)), 0.85))
    stil('a2_tackningsytor', 'Svag faktisk tillgänglighet (fig 2.3)',
         qml(r_kategori('svag_tillg', [('Mycket låg (1–14)', '1–14 avgångar/vardag', '#c0392b', 255),
                                       ('Låg (15–29)', '15–29 avgångar/vardag', '#f28e2b', 255),
                                       ('Ingen hållplats inom 400 m', 'Ingen hållplats inom 400 m', '#a8a49a', 255),
                                       ('Minst 30 avgångar', 'Minst 30 avgångar/vardag', '#ffffff', 0)],
                        lambda s, f, a: fyll(s, f, a)), 0.85))

    r = gpd.read_file(P / 'a2_tackning_rutor.gpkg').rename(columns={'Tot_bef': 'befolkning'})
    for k in ['andel_inom_400m', 'andel_minst_15_avg', 'avg_befviktat']:
        r[k] = r[k].round(3)
    for k in ['inv_svag', 'inv_otackt']:
        r[k] = r[k].round(0)
    skriv(r, 'a2_tackning_per_ruta')
    kl = [(0, 30, '< 30 inv.', '#ffffff', 0), (30, 100, '30–99', '#fbd5b5', 220), (100, 250, '100–249', '#f6a96c', 220),
          (250, 500, '250–499', '#ec7a2c', 220), (500, 99999, '≥ 500', '#c0392b', 220)]
    stil('a2_tackning_per_ruta', 'Invånare med svag tillgänglighet per ruta (fig 2.3)',
         qml(r_klassad('inv_svag', kl, lambda n, f, a: fyll(n, f, a, 'solid', '#ffffff', 0.3)),
             labeling=etiketter('if("inv_svag" >= 30, round("inv_svag", -1), \'\')', placering=1, farg='#b03a1a')), True)
    kl2 = [(0, 30, '< 30 inv.', '#ffffff', 0), (30, 100, '30–99', '#dcd9d2', 220), (100, 250, '100–249', '#b5b1a7', 220),
           (250, 99999, '≥ 250', '#7a776f', 220)]
    stil('a2_tackning_per_ruta', 'Invånare utan hållplats inom 400 m per ruta',
         qml(r_klassad('inv_otackt', kl2, lambda n, f, a: fyll(n, f, a, 'solid', '#ffffff', 0.3)),
             labeling=etiketter('if("inv_otackt" >= 30, round("inv_otackt", -1), \'\')', placering=1, farg='#5f5b52')))


def a3():
    nya = pd.read_csv(P / 'a3_nya_hallplatser.csv')
    ng = gpd.GeoDataFrame(nya.drop(columns=['x', 'y', 'segment']), geometry=gpd.points_from_xy(nya.x, nya.y), crs=C.CRS_METRISK)
    ng['id'] = 'N' + ng.nr.astype(str)
    skriv(ng, 'a3_nya_hallplatser')
    stil('a3_nya_hallplatser', 'Nya hållplatslägen (fig 3.1)', qml(r_enkel(markor('0', 'star', '#1c5cab', 5.0, '#ffffff', 0.3)),
         labeling=etiketter('"id" || \': linje \' || "linjer" || \' (+\' || "nytta_inv" || \' inv.)\'')), True)
    skriv(ng.assign(geometry=ng.buffer(C.TACKNING_M)), 'a3_nya_hallplatser_400m')
    stil('a3_nya_hallplatser_400m', '400 m runt nya lägen', qml(r_enkel(fyll('0', '#1c5cab', 25, 'dash', '#1c5cab', 0.3))), True)

    b = pd.read_csv(P / 'a3_behov_ny_linjestrackning.csv')
    bg = gpd.GeoDataFrame(b.drop(columns=['x', 'y']), geometry=gpd.points_from_xy(b.x, b.y), crs=C.CRS_METRISK)
    skriv(bg, 'a3_behov_ny_linjestrackning')
    stil('a3_behov_ny_linjestrackning', 'Kräver ändrad linjesträckning (fig 3.1)',
         qml(r_enkel(markor('0', 'diamond', '#e8590c', 3.6, '#ffffff', 0.3)),
             labeling=etiketter('"narmaste_hpl" || \' ≈\' || round("inv", -1) || \' inv.\'')), True)
    skriv(bg.assign(geometry=bg.buffer(C.TACKNING_M)), 'a3_behov_400m')
    stil('a3_behov_400m', '400 m runt indikativa lägen', qml(r_enkel(fyll('0', '#e8590c', 25, 'dash', '#e8590c', 0.3))), True)

    o = pd.read_csv(P / 'a3_hallplatsbedomning.csv')
    o['pastigande_92_vardagar'] = (o.pastigande_vardag * C.ANTAL_VARDAGAR).round(0)
    og = gpd.GeoDataFrame(o.drop(columns=['x', 'y']), geometry=gpd.points_from_xy(o.x, o.y), crs=C.CRS_METRISK)
    for k in ['lagt_pastigande', 'lucka_ok', 'liten_unik_tackning']:
        og[k] = og[k].astype(bool)
    skriv(og, 'a3_hallplatsbedomning')
    kat = [('Behålls', 'Behålls', 'circle', '#ffffff', 1.6, '#7a776f'),
           ('Undantas (ändhållplats/vändplats)', 'Undantas (ändhållplats/vändplats)', 'square', '#1f1f1e', 2.2, '#ffffff'),
           ('Saknar påstigningsdata', 'Saknar påstigningsdata', 'circle', '#ffffff', 2.2, '#1c5cab'),
           ('Bör prövas', 'Bör prövas', 'circle', '#f28e2b', 2.8, '#ffffff'),
           ('Kandidat för indragning', 'Kandidat för indragning', 'cross_fill', '#c0392b', 3.4, '#ffffff')]
    stil('a3_hallplatsbedomning', 'Hållplatsbedömning (fig 3.2)',
         qml(r_kategori('bedomning', kat, lambda n, form, f, s, k: markor(n, form, f, s, k, 0.3)),
             labeling=etiketter('if("bedomning" IN (\'Kandidat för indragning\', \'Bör prövas\'), '
                                '"omrade" || \' (\' || "pastigande_92_vardagar" || \')\', \'\')')), True)


def b4():
    g = gpd.read_file(P / 'b4_forslag.gpkg', layer='forslag')
    pk = g[g.geom_type == 'Point'].copy(); ln = g[g.geom_type == 'LineString'].copy()
    skriv(pk, 'b4_forslag_hallplatser')
    kat = [('ny hållplats', 'Ny hållplats', 'star', '#1c5cab', 5.0, '#ffffff'),
           ('ny hållplats för linje N', 'Hållplats som linje N börjar trafikera', 'star', '#1c5cab', 5.0, '#ffffff'),
           ('hållplats utgår för linje N', 'Hållplats som linje N slutar trafikera', 'cross_fill', '#c0392b', 3.4, '#ffffff')]
    stil('b4_forslag_hallplatser', 'Förslag – hållplatser (fig 4.2, 4.4, 4.6)',
         qml(r_kategori('objekt', kat, lambda n, form, f, st, k: markor(n, form, f, st, k, 0.3)),
             labeling=etiketter('"forslag" || \': \' || "namn"')), True)
    skriv(ln, 'b4_forslag_korvagar')
    kat = [('ny körväg (schematisk)', 'Ny körväg (schematisk)', '#1c5cab', True),
           ('körväg utgår (schematisk)', 'Körväg som utgår (schematisk)', '#3d3d3a', True)]
    stil('b4_forslag_korvagar', 'Förslag – körvägar (schematiska)',
         qml(r_kategori('objekt', kat, lambda n, f, st: linje(n, f, 0.8, streckad=st, halo=True))), True)

    # förändrad tillgänglighet per scenario (enskilda förslag och paket), 50 m-celler
    pk_ = json.load(open(P / 'b4_paket.json', encoding='utf-8'))
    tk = pd.read_csv(P / 'b4_paket_tackning.csv.gz')
    h = C.DELRUTA_M
    geo = shapely.box(tk.x - h / 2, tk.y - h / 2, tk.x + h / 2, tk.y + h / 2)
    delar = []
    for sid in [k for k in pk_ if k != 'idag']:
        d = tk[f'klass_{sid}'] != tk.klass_idag
        if not d.any():
            continue
        t = gpd.GeoDataFrame({'scenario': sid, 'namn': pk_[sid]['namn'],
                              'forandring': np.where(tk.loc[d, f'klass_{sid}'] > tk.loc[d, 'klass_idag'], 'Bättre', 'Sämre'),
                              'invanare': tk.loc[d, 'bef'].to_numpy()}, geometry=geo[d.to_numpy()], crs=C.CRS_METRISK)
        delar.append(t.dissolve(by=['scenario', 'namn', 'forandring'], aggfunc={'invanare': 'sum'}).reset_index())
    tg = pd.concat(delar, ignore_index=True); tg['invanare'] = tg.invanare.round(0)
    tg['geometry'] = [g_ if g_.geom_type == 'MultiPolygon' else shapely.MultiPolygon([g_]) for g_ in tg.geometry]
    skriv(gpd.GeoDataFrame(tg, crs=C.CRS_METRISK), 'b4_tackning_forandring')
    stil('b4_tackning_forandring', 'Förändrad tillgänglighet (filtrera på scenario)',
         qml(r_kategori('forandring', [('Bättre', 'Bättre (ny täckning eller fler avgångar)', '#2f9e44'),
                                       ('Sämre', 'Sämre (förlorad täckning eller färre avgångar)', '#c0392b')],
                        lambda n, f: fyll(n, f, 210)), 0.9), True)

    # turtäthetsklass i dag och med paket A (fig 4.12)
    namn = ['Ingen hållplats inom 400 m', 'Mycket låg (1–14 avg/vardag)', 'Låg (15–29)', 'Medel (30–59)', 'God (≥ 60)']
    ts = []
    for sid in ['idag', 'paket_A']:
        g_ = gpd.GeoDataFrame({'scenario': sid, 'ruta_id': tk.ruta_id, 'klass_nr': tk[f'klass_{sid}'], 'invanare': tk.bef},
                              geometry=geo, crs=C.CRS_METRISK)
        ts.append(g_.dissolve(by=['scenario', 'ruta_id', 'klass_nr'], aggfunc={'invanare': 'sum'}).reset_index())
    ts = pd.concat(ts, ignore_index=True)
    ts['klass'] = ts.klass_nr.map(dict(enumerate(namn))); ts['invanare'] = ts.invanare.round(1)
    skriv(gpd.GeoDataFrame(ts, crs=C.CRS_METRISK), 'b4_tackning_scenarier')
    farger = ['#cfcbc2', '#c6dbf5', '#7fb0ec', '#2a78d6', '#0d366b']
    stil('b4_tackning_scenarier', 'Turtäthet inom 400 m (fig 4.12)',
         qml(r_kategori('klass', [(n, n, f) for n, f in zip(namn, farger)], lambda s_, f: fyll(s_, f)), 0.85), True)

    # hela linjesträckningar per förslag (schematiska där nya delsträckor saknar vägdragning)
    import s01_vagdragning as V
    sg = V.segmentgeometri(); hxy, _ = V.hallplats_xy(); mon = V.monster_per_linje()
    fs = json.load(open(P / 'b4_forslag.json', encoding='utf-8'))['forslag']
    def kedja(stopp, ersatt=None):
        pts = []
        for a, b in zip(stopp[:-1], stopp[1:]):
            xy_ = sg.get((a, b), np.array([hxy[a], hxy[b]]))
            pts.extend(xy_ if not pts else xy_[1:])
        return LineString(pts)
    vm, om, nm = mon['V'][0][0], mon['Ö'][0][0], list(mon['N'][0][0])
    mo = '9025302000066401'; k = vm.index(mo)
    ext = LineString([hxy[mo], fs['1b']['xy']])
    v_ny = shapely.line_merge(shapely.MultiLineString([kedja(vm[:k + 1]), ext, LineString([fs['1b']['xy'], hxy[mo]]), kedja(vm[k:])]))
    o_ny = kedja(om)
    st_ = D.gtfs()['stops'].set_index('stop_id').loc[['9025302000003501', '9025302000003502']]
    bx, by = D.till_metrisk(st_.lon.values, st_.lat.values); bobil = np.array([bx.mean(), by.mean()])
    iv = nm.index('9025302000063201')
    n_ny = shapely.MultiLineString([kedja(nm[:iv]), LineString([hxy[nm[iv - 1]], bobil, hxy[nm[iv + 1]]]), kedja(nm[iv + 1:])])
    rad = [('1a', 'V', 'Linje V via Möckelö Strand, dagens gator (8 av 20 turer ryms; alla turer kräver 6 bussar)', fs['1a']['delta_min_per_tur'], v_ny),
           ('1b_VÖ', 'V/Ö', 'Genomgående linje V/Ö via Möckelö Strand (förlängd Norrgårdsvägen) och N2', fs['1b']['delta_min_per_tur'],
            shapely.MultiLineString([*(getattr(v_ny, 'geoms', [v_ny])), o_ny])),
           ('2', 'Ö', 'Linje Ö med ny hållplats N2 (19 av 20 turer)', fs['2']['delta_min_per_tur'], o_ny),
           ('3', 'N', 'Linje N via Bo-Bil i stället för Vikingagränd', fs['3']['delta_min_per_tur'], n_ny)]
    lg = gpd.GeoDataFrame([{'forslag': a, 'linje': b, 'beskrivning': c, 'korttid_per_tur_min': d} for a, b, c, d, _ in rad],
                          geometry=[shapely.MultiLineString(getattr(g_, 'geoms', [g_])) for *_, g_ in rad], crs=C.CRS_METRISK)
    skriv(lg, 'b4_linjer_forslag')
    kat = [('1a', '1a Linje V via Möckelö Strand, dagens gator', C.FARG_LINJE['V']),
           ('1b_VÖ', '1b Genomgående linje V/Ö', '#8c3b74'),
           ('2', '2 Linje Ö med N2', C.FARG_LINJE['Ö']), ('3', '3 Linje N via Bo-Bil', C.FARG_LINJE['N'])]
    stil('b4_linjer_forslag', 'Linjer i förslagen', qml(r_kategori('forslag', kat, lambda n, f: linje(n, f, 1.0, halo=True))), True)

    # nyckeltal per scenario (tabell utan geometri)
    kalk = pd.read_csv(P / 'b5_kalkyl.csv').set_index('scenario')
    rader = []
    for sid, v in pk_.items():
        t_ = v['tackning_mariehamn']; fi = v['forandring_invanare_mariehamn']
        rader.append({'scenario': sid, 'namn': v['namn'], 'ryms_i_omloppen': 'Ja' if v['ryms'] else 'Nej',
                      'bussar': v['omlopp']['fordon'], 'omloppstid_h_vardag': v['omlopp']['omloppstid_h'],
                      'fordonskm_vardag': v['omlopp']['km'],
                      'andel_inom_400m': t_['inom_400m_andel'], 'andel_minst_30_avg': t_['minst_30_avg_andel'],
                      'andel_svag': t_['svag_andel'], 'inv_battre': fi['battre_klass'], 'inv_samre': fi['samre_klass'],
                      'inv_ny_tackning': fi['ny_tackning'], 'inv_forlorad_tackning': fi['forlorad_tackning'],
                      'restid_befintliga_resenarsmin_vardag': v['resenarer']['resenarsminuter_vardag'],
                      'driftkostnad_eur_ar_bas': int(kalk.at[sid, 'drift_ar_bas']) if sid in kalk.index else 0,
                      'driftkostnad_eur_ar_lag': int(kalk.at[sid, 'drift_ar_låg']) if sid in kalk.index else 0,
                      'driftkostnad_eur_ar_hog': int(kalk.at[sid, 'drift_ar_hög']) if sid in kalk.index else 0})
    pyogrio.write_dataframe(pd.DataFrame(rader), GPKG, layer='b4_nyckeltal_scenarier', driver='GPKG')

    o = pd.read_csv(P / 'b4_sammanslagning_omraden.csv')
    og = gpd.GeoDataFrame(o.drop(columns=['x', 'y']), geometry=gpd.points_from_xy(o.x, o.y), crs=C.CRS_METRISK)
    skriv(og, 'b4_sammanslagning_omraden')
    kat = [('Ryms i dag', 'Ryms i dag', '#2f9e44'), ('Ryms med genomgående linje', 'Ryms med genomgående linje', '#1c5cab'),
           ('Kräver större omläggning', 'Kräver större omläggning', '#c0392b'),
           ('Linje J (timtrafik) – prövas separat', 'Linje J (timtrafik) – prövas separat', '#7a776f')]
    stil('b4_sammanslagning_omraden', 'Behövd tid per tur (fig 4.8)',
         qml(r_kategori('bedomning', kat, lambda n, f: markor(n, 'diamond', f, 3.6, '#ffffff', 0.3)),
             labeling=etiketter('"omrade" || \' +\' || format_number("behov_min_per_tur", 1) || \' min/tur (linje \' || "linje" || \')\'')), True)


# ====================================================================== stiltabell
def skriv_stilar():
    """Skriver stilarna till GeoPackage-tabellen layer_styles (läses av QGIS) och som .qml-filer."""
    STILAR.mkdir(parents=True, exist_ok=True)
    for f in STILAR.glob('*.qml'):
        f.unlink()
    nu = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    con = sqlite3.connect(GPKG)
    geomkol = dict(con.execute('SELECT table_name, column_name FROM gpkg_geometry_columns').fetchall())
    con.close()
    rader = []
    for lager, namn, xml, standard in STYLES:
        rader.append({'f_table_catalog': '', 'f_table_schema': '', 'f_table_name': lager,
                      'f_geometry_column': geomkol.get(lager, 'geom'), 'styleName': namn, 'styleQML': xml,
                      'styleSLD': '', 'useAsDefault': bool(standard), 'description': namn, 'owner': '', 'ui': '',
                      'update_time': nu})
        bas = namn.split(' (')[0].replace(' ', '_').replace('/', '-')
        bas = bas.translate(str.maketrans('åäöÅÄÖ–', 'aaoAAO-')).encode('ascii', 'ignore').decode()
        fil = f"{lager}__{bas}.qml"
        (STILAR / fil).write_text(xml, encoding='utf-8')
    df = pd.DataFrame(rader)
    pyogrio.write_dataframe(df, GPKG, layer='layer_styles', driver='GPKG', layer_options={'FID': 'id'})


def main():
    UT.mkdir(parents=True, exist_ok=True)
    if GPKG.exists():
        GPKG.unlink()
    bas(); a1(); a2(); a3(); b4()
    skriv_stilar()
    lager = pyogrio.list_layers(GPKG)
    print(f'{GPKG} – {len(lager)} lager, {len(STYLES)} stilar')
    for n, t in lager:
        print(f'  {n:32s} {t}')


if __name__ == '__main__':
    main()
