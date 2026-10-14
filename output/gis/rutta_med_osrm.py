# -*- coding: utf-8 -*-
"""Ruttar stadslinjerna och linjeförslagen längs gatunätet med OSRM – direkt i QGIS.

Kör i QGIS: Insticksprogram > Python-konsol > Visa redigerare > Öppna skript (denna fil) > Kör skript.
Ligger skriptet i samma mapp som linjenatsutredning.gpkg hittas filen automatiskt, annars får du välja den.
Kräver internetåtkomst till OSRM (standard: router.project-osrm.org, data © OpenStreetMap-bidragsgivare).
Anropen går via QGIS nätverksinställningar (proxy m.m.). Publika servern tillåter ungefär ett anrop per sekund.

Skriptet
  1. läser lagret 00_segment (ett segment per hållplatspar) och ruttar varje segment som inte redan är ruttat;
     en OSRM-rutt som är orimligt lång (> 2,5 × fågelvägen + 300 m) avvisas och segmentet behålls rakt;
  2. skriver vägdragningen till 00_segment (kalla = 'osrm', langd_m, tid_s);
  3. byter ut de raka delarna i 00_stadslinjer, b4_linjer_forslag och b4_forslag_korvagar mot de ruttade
     (planerade vägar, t.ex. Norrgårdsvägens förlängning i förslag 1b, behålls schematiska);
  4. räknar om 00_stadslinjer_forskjutna, så att linjer som delar gata får egna spår även längs de ruttade gatorna;
  5. laddar om lagren i projektet.
Skriptet kan köras igen; redan ruttade segment hoppas över (sätt RUTTA_OM_ALLA = True för att rutta om).
Vill du föra över vägdragningen till analyskedjan (kartor, km, hållplatskandidater):
  python src/s01_vagdragning.py --fran-gis   och därefter   python src/kor_alla.py --utan-osrm
"""
import json
import math
import os
import statistics
import time
import urllib.request

OSRM_URL = 'https://router.project-osrm.org'   # egen server: t.ex. 'http://localhost:5000'
PAUS_S = 1.0                                   # paus mellan anrop (publika servern: ≈ 1 anrop/s)
RUTTA_OM_ALLA = False                          # True = rutta om även segment som redan är ruttade
MAX_OMVAG = (2.5, 300.0)                       # faktor, tillägg (m) – längre OSRM-rutt avvisas
SAMMA_GATA_M = 15.0                            # linjer inom detta avstånd och parallella räknas gå på samma gata
STEG_M = 6.0                                   # samplingssteg för förskjutningen (m)
ORDNING = {l: i for i, l in enumerate(['J', 'N', 'S', 'V', 'Ö'])}
LINJELAGER = ['00_stadslinjer', 'b4_linjer_forslag', 'b4_forslag_korvagar']

try:
    from qgis.core import (QgsBlockingNetworkRequest, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                           QgsFeature, QgsGeometry, QgsPointXY, QgsProject, QgsVectorLayer)
    QGIS_FINNS = True
except ImportError:                              # utanför QGIS (t.ex. test av beräkningsdelarna)
    QGIS_FINNS = False


# ====================================================================== beräkningar (ren Python)
def hamta_json(url):
    """GET → JSON. I QGIS via QgsBlockingNetworkRequest (följer QGIS proxyinställningar), annars urllib."""
    if QGIS_FINNS:
        try:
            from qgis.PyQt.QtCore import QUrl
            from qgis.PyQt.QtNetwork import QNetworkRequest
            nr = QNetworkRequest(QUrl(url))
            nr.setRawHeader(b'User-Agent', b'linjenatsutredning-mariehamn/1.0')
            req = QgsBlockingNetworkRequest()
            kod = req.get(nr, True)
            ok = getattr(QgsBlockingNetworkRequest, 'NoError', None)
            if ok is None:
                ok = QgsBlockingNetworkRequest.ErrorCode.NoError
            if kod != ok:
                raise IOError(req.errorMessage())
            return json.loads(bytes(req.reply().content()).decode('utf-8'))
        except Exception as e:                    # försök med urllib innan vi ger upp
            fel = e
            try:
                return _urllib_json(url)
            except Exception:
                raise fel
    return _urllib_json(url)


def _urllib_json(url):
    r = urllib.request.Request(url, headers={'User-Agent': 'linjenatsutredning-mariehamn/1.0'})
    with urllib.request.urlopen(r, timeout=20) as svar:
        return json.loads(svar.read().decode('utf-8'))


def osrm_rutt(lon1, lat1, lon2, lat2, url=None):
    """Rutt mellan två punkter: ([(lon, lat), ...], längd m, tid s)."""
    url = (f'{(url or OSRM_URL).rstrip("/")}/route/v1/driving/{lon1:.6f},{lat1:.6f};{lon2:.6f},{lat2:.6f}'
           '?overview=full&geometries=geojson&steps=false')
    j = hamta_json(url)
    if j.get('code') != 'Ok' or not j.get('routes'):
        raise ValueError(f"OSRM svarade {j.get('code')}")
    rt = j['routes'][0]
    return [tuple(c) for c in rt['geometry']['coordinates']], float(rt['distance']), float(rt['duration'])


def nyckel(p0, p1):
    """Segmentnyckel av ändpunkterna (hållplatsernas koordinater), avrundade till decimeter."""
    return (round(p0[0], 1), round(p0[1], 1), round(p1[0], 1), round(p1[1], 1))


def sampla(pts, steg):
    """Punkter var steg:e meter längs polylinjen och enhetstangent i varje punkt (som numpy.gradient)."""
    s = [0.0]
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        s.append(s[-1] + math.hypot(x1 - x0, y1 - y0))
    L = s[-1]
    if L == 0:
        return [pts[0]], [(1.0, 0.0)]
    n = max(2, int(L / steg) + 1)
    P, j = [], 0
    for i in range(n):
        v = L * i / (n - 1)
        while j < len(s) - 2 and s[j + 1] < v:
            j += 1
        d = s[j + 1] - s[j]
        t = 0.0 if d == 0 else min(max((v - s[j]) / d, 0.0), 1.0)
        P.append((pts[j][0] + t * (pts[j + 1][0] - pts[j][0]), pts[j][1] + t * (pts[j + 1][1] - pts[j][1])))
    T = []
    for i in range(n):
        a, b = (P[max(i - 1, 0)], P[min(i + 1, n - 1)])
        k = 2.0 if 0 < i < n - 1 else 1.0
        dx, dy = (b[0] - a[0]) / k, (b[1] - a[1]) / k
        l_ = max(math.hypot(dx, dy), 1e-9)
        T.append((dx / l_, dy / l_))
    return P, T


def sparanalys(kedjor, steg=STEG_M, radie=SAMMA_GATA_M):
    """kedjor: [(linje, kedjenr, [(x, y), ...])]. Bestämmer för varje samplad punkt linjens spår bland linjer som
    går längs samma gata (inom radie, parallella), med tecken relativt linjens egen riktning."""
    prov = [(ln, ki) + sampla(pts, steg) for ln, ki, pts in kedjor]
    alla = []                                                  # (ordning, x, y, tx, ty)
    for ln, ki, P, T in prov:
        alla += [(ORDNING[ln], p[0], p[1], t[0], t[1]) for p, t in zip(P, T)]
    rut = {}
    for i, (_, x, y, _, _) in enumerate(alla):
        rut.setdefault((int(math.floor(x / radie)), int(math.floor(y / radie))), []).append(i)
    ut = []
    for ln, ki, P, T in prov:
        mitt = ORDNING[ln]; slot, tecken = [], []
        for (x, y), (tx, ty) in zip(P, T):
            cx, cy = int(math.floor(x / radie)), int(math.floor(y / radie))
            gr = [g for dx in (-1, 0, 1) for dy in (-1, 0, 1) for g in rut.get((cx + dx, cy + dy), [])
                  if math.hypot(alla[g][1] - x, alla[g][2] - y) <= radie]
            par = [g for g in gr if abs(alla[g][3] * tx + alla[g][4] * ty) > 0.85]
            linjer = sorted({alla[g][0] for g in par} | {mitt})
            if len(linjer) < 2:
                slot.append(0.0); tecken.append(1.0)
                continue
            ref = linjer[0]
            if ref == mitt:
                tref = (tx, ty)
            else:
                g = min((g for g in par if alla[g][0] == ref), key=lambda g: math.hypot(alla[g][1] - x, alla[g][2] - y))
                tref = (alla[g][3], alla[g][4])
            slot.append(linjer.index(mitt) - (len(linjer) - 1) / 2)
            tecken.append(1.0 if tref[0] * tx + tref[1] * ty > 0 else -1.0)
        ut.append((ln, ki, P, slot, tecken))
    return ut


def forskjutna_delar(kedjor, steg=STEG_M):
    """Linjedelar med konstant spår: [(linje, kedjenr, förskjutning, [(x, y), ...])]."""
    ut = []
    for ln, ki, P, slot, tecken in sparanalys(kedjor, steg):
        s0 = [round(a * b * 2) / 2 for a, b in zip(slot, tecken)]
        s = [statistics.median(s0[max(i - 2, 0):i + 3]) for i in range(len(s0))]   # tar bort flimmer i korsningar
        start = 0
        for i in range(1, len(s) + 1):
            if i == len(s) or s[i] != s[start]:
                if i - start >= 2:
                    ut.append((ln, ki, float(s[start]), P[start:i + (1 if i < len(s) else 0)]))
                start = i
    return ut


# ====================================================================== QGIS
def gpkg_sokvag():
    try:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'linjenatsutredning.gpkg')
    except NameError:
        p = ''
    if not os.path.exists(p):
        from qgis.PyQt.QtWidgets import QFileDialog
        p, _ = QFileDialog.getOpenFileName(None, 'Välj linjenatsutredning.gpkg', '', 'GeoPackage (*.gpkg)')
    return p


def oppna(gpkg, lager):
    lyr = QgsVectorLayer(f'{gpkg}|layername={lager}', lager, 'ogr')
    if not lyr.isValid():
        raise RuntimeError(f'Kunde inte öppna lagret {lager} i {gpkg}')
    return lyr


def rutta_segment(seg):
    """Steg 1–2: ruttar segmenten i 00_segment och skriver tillbaka geometri och attribut."""
    tr = QgsCoordinateTransform(QgsCoordinateReferenceSystem('EPSG:4326'), seg.crs(), QgsProject.instance())
    fi = {f.name(): i for i, f in enumerate(seg.fields())}
    geom_upd, attr_upd, n_ok, n_avv = {}, {}, 0, 0
    kvar = [f for f in seg.getFeatures() if RUTTA_OM_ALLA or f['kalla'] != 'osrm']
    print(f'Ruttar {len(kvar)} segment med OSRM ({OSRM_URL}) …')
    for nr, f in enumerate(kvar, 1):
        pl = f.geometry().asPolyline() or f.geometry().asMultiPolyline()[0]
        a, b = QgsPointXY(pl[0]), QgsPointXY(pl[-1])
        rak = math.hypot(b.x() - a.x(), b.y() - a.y())
        try:
            coords, langd, tid = osrm_rutt(f['from_lon'], f['from_lat'], f['to_lon'], f['to_lat'])
        except Exception as e:
            print(f'  OSRM kunde inte nås ({e}) – avbryter. Redan ruttade segment sparas.')
            break
        if langd <= MAX_OMVAG[0] * rak + MAX_OMVAG[1]:
            pts = [a] + [tr.transform(QgsPointXY(lon, lat)) for lon, lat in coords] + [b]
            geom_upd[f.id()] = QgsGeometry.fromPolylineXY(pts)
            attr_upd[f.id()] = {fi['kalla']: 'osrm', fi['langd_m']: round(langd, 1), fi['tid_s']: round(tid, 1)}
            n_ok += 1
        else:
            attr_upd[f.id()] = {fi['kalla']: 'osrm_avvisad', fi['langd_m']: round(langd, 1), fi['tid_s']: round(tid, 1)}
            n_avv += 1
            print(f"  avvisad (omväg): {f['from_stop']} → {f['to_stop']} ({f['linjer']}), {langd:.0f} m mot {rak:.0f} m fågelväg")
        if nr % 20 == 0:
            print(f'  {nr}/{len(kvar)}')
        time.sleep(PAUS_S)
    pr = seg.dataProvider()
    if geom_upd:
        pr.changeGeometryValues(geom_upd)
    if attr_upd:
        pr.changeAttributeValues(attr_upd)
    print(f'Klart: {n_ok} segment ruttade, {n_avv} avvisade.')
    return n_ok


def segmenttabell(seg):
    """{nyckel: [QgsPointXY, ...]} för ruttade segment, {(från, till): punkter} för alla och pseudohållplatsernas läge."""
    rutt, alla, pseudo = {}, {}, {}
    for f in seg.getFeatures():
        pl = f.geometry().asPolyline() or f.geometry().asMultiPolyline()[0]
        alla[(f['from_stop'], f['to_stop'])] = [QgsPointXY(p) for p in pl]
        if f['kalla'] == 'osrm':
            rutt[nyckel((pl[0].x(), pl[0].y()), (pl[-1].x(), pl[-1].y()))] = [QgsPointXY(p) for p in pl]
        for k, p in ((f['from_stop'], pl[0]), (f['to_stop'], pl[-1])):
            if not str(k).isdigit():
                pseudo[k] = (round(p.x(), 1), round(p.y(), 1))
    return rutt, alla, pseudo


def byt_delar(lyr, rutt, pseudo):
    """Steg 3: byter raka hållplatssegment i flerdelsgeometrier mot ruttade."""
    fi = {f.name(): i for i, f in enumerate(lyr.fields())}
    geom_upd, attr_upd = {}, {}
    for f in lyr.getFeatures():
        planerad = pseudo.get(f['planerad_vag_till']) if 'planerad_vag_till' in fi and f['planerad_vag_till'] else None
        delar, n_rutt, n_tot = [], 0, 0
        for d in f.geometry().asMultiPolyline():
            k = nyckel((d[0].x(), d[0].y()), (d[-1].x(), d[-1].y()))
            skyddad = planerad is not None and (k[:2] == planerad or k[2:] == planerad)
            if skyddad:
                delar.append([QgsPointXY(p) for p in d])
                continue
            n_tot += 1
            if k in rutt:
                delar.append(rutt[k]); n_rutt += 1
            else:
                delar.append([QgsPointXY(p) for p in d])
        geom_upd[f.id()] = QgsGeometry.fromMultiPolylineXY(delar)
        if 'vagdragning' in fi:
            txt = 'OSRM' if n_rutt == n_tot else ('delvis OSRM' if n_rutt else f['vagdragning'])
            if planerad is not None:
                txt += '; planerad väg schematisk'
            attr_upd[f.id()] = {fi['vagdragning']: txt}
    lyr.dataProvider().changeGeometryValues(geom_upd)
    if attr_upd:
        lyr.dataProvider().changeAttributeValues(attr_upd)


def gor_forskjutna(gpkg, alla):
    """Steg 4: räknar om 00_stadslinjer_forskjutna från linjernas kedjor (00_linjekedjor) och segmenten."""
    tab = oppna(gpkg, '00_linjekedjor')
    kedjor = {}
    for f in tab.getFeatures():
        kedjor.setdefault((f['linje'], int(f['kedja'])), []).append((int(f['ordning']), f['from_stop'], f['to_stop']))
    indata = []
    for (ln, ki), lista in sorted(kedjor.items(), key=lambda kv: (ORDNING.get(kv[0][0], 99), kv[0][1])):
        pts = []
        for _, a, b in sorted(lista):
            seg_pts = alla.get((a, b))
            if seg_pts is None:
                continue
            pts += [(p.x(), p.y()) for p in (seg_pts if not pts else seg_pts[1:])]
        if len(pts) >= 2:
            indata.append((ln, ki, pts))
    delar = forskjutna_delar(indata)
    lyr = oppna(gpkg, '00_stadslinjer_forskjutna')
    pr = lyr.dataProvider()
    pr.truncate()
    nya = []
    for ln, ki, fs, pts in delar:
        f = QgsFeature(lyr.fields())
        f['linje'], f['kedja'], f['forskjutning'] = ln, ki, fs
        f.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(x, y) for x, y in pts]))
        nya.append(f)
    pr.addFeatures(nya)
    print(f'00_stadslinjer_forskjutna: {len(nya)} linjedelar.')


def ladda_om(gpkg):
    for lyr in QgsProject.instance().mapLayers().values():
        if lyr.providerType() == 'ogr' and os.path.normcase(gpkg) in os.path.normcase(lyr.source()):
            lyr.dataProvider().reloadData()
            lyr.triggerRepaint()
    try:
        from qgis.utils import iface
        iface.mapCanvas().refreshAllLayers()
    except Exception:
        pass


def main():
    gpkg = gpkg_sokvag()
    if not gpkg:
        print('Ingen GeoPackage vald.')
        return
    seg = oppna(gpkg, '00_segment')
    rutta_segment(seg)
    rutt, alla, pseudo = segmenttabell(oppna(gpkg, '00_segment'))
    if not rutt:
        print('Inga ruttade segment – lagren lämnas oförändrade.')
        return
    for namn in LINJELAGER:
        byt_delar(oppna(gpkg, namn), rutt, pseudo)
        print(f'{namn}: uppdaterat.')
    gor_forskjutna(gpkg, alla)
    ladda_om(gpkg)
    print('Klart. Vägdragningen finns nu i lagren (fältet vagdragning anger OSRM).')


if QGIS_FINNS:
    main()
