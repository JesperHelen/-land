# -*- coding: utf-8 -*-
"""B4 – kartor och omloppsfigurer för de enskilda utredningsalternativen (Möckelö Strand, N2 linje Ö, linje N via Bo-Bil)."""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import kartlib as K  # noqa: E402
import b4_omlopp as O  # noqa: E402

P = C.PROCESSED
RES = json.load(open(P / 'b4_ua.json', encoding='utf-8'))
SCEN = pd.read_csv(P / 'b4_omlopp_scenarier.csv', dtype={'trip_id': str})
HPL = pd.read_csv(P / 'a2_hallplatser_avgangar.csv', index_col=0, dtype={'stop_id': str})
OTACKT = '#b9b4a8'
BATTRE, SAMRE, BLA = '#2f9e44', '#c0392b', '#1c5cab'
F_HPL_MOCKELO = '9025302000066401'
UTS = {'mockelo': (104450, 107350, 6682650, 6685750), 'n2': (109150, 111550, 6681850, 6685550),
       'bobil': (106950, 109350, 6685250, 6687550), 'flyg': (105450, 107850, 6685250, 6687650),
       'svang': (106650, 108450, 6683650, 6686150)}


def sv(x, d=1):
    return f'{x:.{d}f}'.replace('.', ',').replace('-', '−')


# ====================================================================== kartor
def tackningslager(ax, sid, uts=None):
    """Huvudalternativets täckning – exakta 400 m-cirklar (tackningsytor.py): befolkning som fortfarande saknar
    hållplats inom 400 m (grå) och ytor med bättre (grön) respektive sämre (röd) turtäthetsklass än i dag."""
    import geopandas as gpd
    import tackningsytor as T
    g = gpd.read_file(P / 'b4_systemeffekter_ytor.gpkg', layer='ytor')
    o = g[g[f'klass_{sid}'] == 0].dissolve(by='ruta_id', as_index=False)
    rgba = np.array([to_rgba(OTACKT)] * len(o)); rgba[:, 3] = T.tathet_alfa(o.ruta_id, 0.30, 0.55)
    o.plot(ax=ax, color=rgba, linewidth=0, zorder=1)
    f = T.forandring(g, sid)
    for r in f.itertuples():
        c = BATTRE if r.forandring == 'Bättre' else SAMRE
        f[f.forandring == r.forandring].plot(ax=ax, facecolor=to_rgba(c, 0.8), edgecolor=c, linewidth=0.8, zorder=1.5)


def bakgrund(ax, uts, titel):
    K.ny_karta(uts, ax=ax, titel=titel)
    import data_las as D
    D.befolkning().boundary.plot(ax=ax, color='white', linewidth=0.5, alpha=0.9, zorder=2)


def hallplatser(ax, uts, namn=()):
    x0, x1, y0, y1 = uts
    h = HPL[HPL.x.between(x0, x1) & HPL.y.between(y0, y1)]
    stad = h.linjer.str.contains('|'.join(C.STADSLINJER))
    ax.scatter(h.x[~stad], h.y[~stad], s=12, facecolor='white', edgecolor='#7a776f', lw=0.6, zorder=6)
    ax.scatter(h.x[stad], h.y[stad], s=16, facecolor='white', edgecolor='#1f1f1e', lw=0.7, zorder=6)
    g = h[h.namn.isin(namn)].groupby('namn')[['x', 'y']].mean()
    return [(n, (r.x, r.y), 40) for n, r in g.iterrows()]


def infobox(ax, rader, loc=(0.025, 0.975)):
    """Inga inforutor i figurerna (siffrorna redovisas i rapporttexten)."""
    return
    ax.text(loc[0], loc[1], '\n'.join(rader), transform=ax.transAxes, ha='left', va='top', fontsize=7.2,
            color=K.TEXT, zorder=30, linespacing=1.45,
            bbox=dict(boxstyle='round,pad=0.55', facecolor='white', edgecolor='#d6d5d0', lw=0.6, alpha=0.95))


def forklaring_tackning(extra=()):
    h = [Patch(facecolor=BATTRE, alpha=0.85, label='Bättre tillgänglighet'),
         Patch(facecolor=SAMRE, alpha=0.85, label='Sämre tillgänglighet'),
         Patch(facecolor=OTACKT, alpha=0.7, label='Ingen hållplats inom 400 m')]
    h += list(extra)
    h += [Line2D([], [], color=C.FARG_LINJE[l], lw=2, label=C.NAMN_LINJE[l]) for l in C.STADSLINJER]
    h += [Line2D([], [], marker='o', ls='', markerfacecolor='white', markeredgecolor='#1f1f1e', label='Hållplats')]
    return h


FARG_VO = C.FARG_LINJE['V']


def rita_vo(ax):
    """Linje V som del av den genomgående linjen V–Ö (V och Ö sammanslagna) – dagens körväg i V–Ö-färg."""
    import s01_vagdragning as V
    geo = V.segmentgeometri()
    for kedja in V.linjekedjor()['V']:
        xy_ = np.vstack([geo[s_] if i == 0 else geo[s_][1:] for i, s_ in enumerate(kedja)])
        ax.plot(xy_[:, 0], xy_[:, 1], color=FARG_VO, lw=3.0, zorder=4.5, solid_capstyle='round',
                path_effects=[K.pe.Stroke(linewidth=4.8, foreground='white'), K.pe.Normal()])


def fig_mockelo():
    f1a, f1b = RES['ua']['1a'], RES['ua']['1b']
    m = RES['antaganden']['mockelo']
    uts = UTS['mockelo']
    fig, ax = plt.subplots(figsize=(8.6, 8.4))
    bakgrund(ax, uts, 'UA 1a och 1b – Möckelö Strand ny')
    tackningslager(ax, '1b', uts)
    K.rita_linjer(ax, lw=2.2, zorder=4)
    rita_vo(ax)
    etik = hallplatser(ax, uts, ['Möckelö Strand', 'Norrgårdsvägen', 'Lönnhagsvägen', 'Sviby bro', 'Västra Möckelö vsk.'])
    nx, ny_ = f1b['xy']
    import s01_vagdragning as V
    fg = V.uageometri()
    bef = fg[('NY_MOCKELO', '9025302000067701')]['xy']
    pl = V.planerad_vag()
    fv = FARG_VO
    halo = [K.pe.Stroke(linewidth=4.4, foreground='white'), K.pe.Normal()]
    ax.plot(bef[:, 0], bef[:, 1], color=fv, lw=2.6, zorder=5, path_effects=halo)                    # befintlig väg
    ax.plot(pl[:, 0], pl[:, 1], color=fv, lw=2.6, ls=(0, (3, 2)), zorder=5)                          # planerad väg
    for xy_ in (pl, bef):                                                                             # 1b:s körriktning
        k = len(xy_) // 2 if len(xy_) > 2 else 0
        a_, b_ = (xy_[k], xy_[k + 1]) if len(xy_) > 2 else (xy_[0] + 0.45 * (xy_[1] - xy_[0]), xy_[0] + 0.55 * (xy_[1] - xy_[0]))
        ax.annotate('', xy=tuple(b_), xytext=tuple(a_), zorder=6,
                    arrowprops=dict(arrowstyle='-|>', color=fv, lw=0, mutation_scale=14))
    ax.add_patch(plt.Circle((nx, ny_), C.TACKNING_M, facecolor='none', edgecolor=BLA, lw=1.0, ls='--', zorder=5))
    ax.scatter([nx], [ny_], s=220, marker='*', color=BLA, edgecolor='white', lw=0.8, zorder=8)
    ax.annotate(f"Förlängd Norrgårdsvägen\n(planerad, {sv(m['restid_forlangning_min'], 0)} min) – UA 1b",
                xy=tuple(pl.mean(axis=0)), xytext=(-10, 0), textcoords='offset points', fontsize=6.8,
                color=K.TEXT, ha='right', va='center', zorder=9, path_effects=K.HALO)
    kb = bef[int(len(bef) * 0.55)]
    ax.annotate(f"Befintlig väg, bl.a. Möckelövägen ({sv(m['restid_befintlig_vag_min'], 0)} min):\nUA 1a fram och tillbaka,\nUA 1b tillbaka (slinga)",
                xy=tuple(kb), xytext=(10, 0), textcoords='offset points', fontsize=6.8,
                color=K.TEXT, ha='left', va='center', zorder=9, path_effects=K.HALO)
    hinder = K.punkt_hinder(ax, [nx], [ny_], px=12)
    K.placera_etiketter(ax, etik + [('Möckelö Strand ny', (nx, ny_), 70)], fontsize=6.8, undvik=hinder)
    o1a, o1b = f1a['omlopp'], f1b['omlopp']
    vo, vb, ba = o1a['VO'], o1b['VO'], o1b['alla']
    M = sv(O.MARGINAL_VARV, 0)
    infobox(ax, [
        r'$\bf{Körtid\ per\ tur}$' + f"   UA 1a +{sv(f1a['delta_min_per_tur'])} min (2 + 0,5 + 2)   ·   "
        f"UA 1b +{sv(f1b['delta_min_per_tur'])} min (1 + 0,5 + 2 − 1)",
        r'$\bf{Krav}$' + f"   V och Ö sammanslagna: varje varv V + Ö inom timmen, minst {M} min i centrum",
        r'$\bf{UA\ 1a\ –\ huvudalternativ}$' + f"   {vo['turer_med_andring']} av {f1a['linjens_turer']} turer, 5 bussar "
        f"(som i dag: {', '.join(vo['turer_utan_andring'])})",
        f"      övriga: dagens tidtabell {o1a['ryms']['turer_med_andring']} av {f1a['linjens_turer']}; "
        f"alla turer {o1a['alla']['fordon']} bussar (utesluten)",
        r'$\bf{UA\ 1b\ –\ huvudalternativ}$' + f"   {vb['turer_med_andring']} av {f1b['linjens_turer']} turer, 5 bussar "
        f"(som i dag: {', '.join(vb['turer_utan_andring'])})",
        f"      alla {f1b['linjens_turer']} turer: 5 bussar men bara {sv(ba['min_centrum_vo'])} min i centrum i varven med Ö:s skolturer",
        r'$\bf{Effekt}$' + f"   +{f1b['tackning']['ny_tackning_inv']} invånare inom 400 m",
        f"Påstigande ≈ {sv(f1b['nytt_pastigande_vardag'][0])}–{sv(f1b['nytt_pastigande_vardag'][1])} per vardag (UA 1b, höst 2026)",
        f"Restid: +{sv(f1b['resenarer']['vardag_inkl_genomgaende'], 0)} (UA 1b) resp. "
        f"+{sv(f1a['resenarer']['vardag_inkl_genomgaende'], 0)} (UA 1a) resenärsminuter/vardag "
        f"(inkl. {sv(RES['genomgaende_vo']['resenarsminuter_vardag'])} V ↔ Ö utan byte)"])
    kalla = {'osrm': 'OSRM', 'skiss': 'beställarens skiss'}.get(m['kalla_befintlig_vag'], 'schematisk')
    extra = [Line2D([], [], marker='*', ls='', color=BLA, markersize=12, label='Ny hållplats'),
             Line2D([], [], color=fv, lw=2.4, label='Väg till ny hållplats'),
             Line2D([], [], color=fv, lw=2.4, ls=(0, (3, 2)), label='Förlängd Norrgårdsvägen (UA 1b)'),
             Line2D([], [], color=FARG_VO, lw=3, label='Västra–Östra'),
             Patch(facecolor='none', edgecolor=BLA, ls='--', label='400 m runt ny hållplats')]
    lg = K.teckenforklaring(ax, forklaring_tackning(extra), loc='lower left', fontsize=6.8)
    lg.set_bbox_to_anchor((1.02, 0.0), transform=ax.transAxes)
    K.ram(ax)
    return K.spara(fig, 'b4_2_mockelo_karta.png')


def fig_n2():
    f = RES['ua']['2']
    uts = UTS['n2']
    fig, ax = plt.subplots(figsize=(7.4, 9.0))
    bakgrund(ax, uts, 'UA 2 – ny hållplats N2 på linje Ö')
    tackningslager(ax, '2', uts)
    K.rita_linjer(ax, lw=2.2, zorder=4)
    etik = hallplatser(ax, uts, ['Kalmarnäs vändplan', 'Österkullagatan', 'Solberget', 'Solberget södra', 'Kalmsta'])
    nx, ny_ = f['xy']
    ax.add_patch(plt.Circle((nx, ny_), C.TACKNING_M, facecolor='none', edgecolor=BLA, lw=1.0, ls='--', zorder=5))
    ax.scatter([nx], [ny_], s=220, marker='*', color=BLA, edgecolor='white', lw=0.8, zorder=8)
    hinder = K.punkt_hinder(ax, [nx], [ny_], px=12)
    K.placera_etiketter(ax, etik + [('N2', (nx, ny_), 70)], fontsize=6.8, undvik=hinder)
    o = f['omlopp']
    infobox(ax, [
        r'$\bf{Körtid\ per\ tur}$' + f"   +{sv(f['delta_min_per_tur'])} min (ett uppehåll)",
        r'$\bf{Omlopp\ (5\ bussar)}$',
        f"Alla {f['linjens_turer']} turer ryms ({o['alla']['fordon']} bussar)",
        "08:20-turen: kort byte Ö → V 08:50 (0,5 min)",
        r'$\bf{Effekt}$' + f"   +{f['tackning']['ny_tackning_inv']} invånare inom 400 m",
        f"Påstigande ≈ {sv(f['nytt_pastigande_vardag'][0])}–{sv(f['nytt_pastigande_vardag'][1])} per vardag (höst 2026)",
        f"Ombordvarande: +{sv(f['resenarer']['vardag']['resenarsminuter'], 0)} resenärsminut per vardag"], loc=(0.03, 0.975))
    extra = [Line2D([], [], marker='*', ls='', color=BLA, markersize=12, label='Ny hållplats N2'),
             Patch(facecolor='none', edgecolor=BLA, ls='--', label='400 m runt N2')]
    lg = K.teckenforklaring(ax, forklaring_tackning(extra), loc='lower left', fontsize=6.8)
    lg.set_bbox_to_anchor((1.02, 0.0), transform=ax.transAxes)
    K.ram(ax)
    return K.spara(fig, 'b4_4_n2_karta.png')


def fig_bobil():
    f = RES['ua']['3']
    uts = UTS['bobil']
    fig, ax = plt.subplots(figsize=(8.6, 8.4))
    bakgrund(ax, uts, 'UA 3 – linje N via Bo-Bil')
    tackningslager(ax, '3', uts)
    K.rita_linjer(ax, lw=2.2, zorder=4, alpha=0.9)
    etik = hallplatser(ax, uts, ['Maxinge', 'Vikingagränd', 'Bolstavägen', 'Bo-Bil', 'Hjortronstigen', 'Lillåkersvägen'])
    g = {n: HPL[HPL.namn == n][['x', 'y']].mean() for n in ['Maxinge', 'Vikingagränd', 'Bolstavägen', 'Bo-Bil']}
    mx, vg, bv, bb = (g[k] for k in ['Maxinge', 'Vikingagränd', 'Bolstavägen', 'Bo-Bil'])
    import s01_vagdragning as V
    sg_ = V.segmentgeometri(); fg_ = V.uageometri()
    MX, VG, BV, BB = '9025302000031201', '9025302000063201', '9025302000063301', '9025302000003501'
    gl = np.vstack([sg_[(MX, VG)], sg_[(VG, BV)][1:]]) if (MX, VG) in sg_ and (VG, BV) in sg_ else \
        np.array([[mx.x, mx.y], [vg.x, vg.y], [bv.x, bv.y]])
    ny_xy = np.vstack([fg_[(MX, BB)]['xy'], fg_[(BB, BV)]['xy'][1:]])
    ax.plot(gl[:, 0], gl[:, 1], color='#3d3d3a', lw=3.2, ls=(0, (1.2, 1.6)), zorder=6,
            solid_capstyle='round')
    ax.plot(ny_xy[:, 0], ny_xy[:, 1], color=C.FARG_LINJE['N'], lw=2.6, ls=(0, (3, 2)), zorder=6)
    _pilar(ax, ny_xy, C.FARG_LINJE['N'], steg=170, uts=uts, ms=13)        # körriktning (Norra är enkelriktad)
    ax.scatter([vg.x], [vg.y], s=90, marker='X', color=SAMRE, edgecolor='white', lw=0.7, zorder=8)
    ax.scatter([bb.x], [bb.y], s=220, marker='*', color=BLA, edgecolor='white', lw=0.8, zorder=8)
    for p, c in [(vg, SAMRE), (bb, BLA)]:
        ax.add_patch(plt.Circle((p.x, p.y), C.TACKNING_M, facecolor='none', edgecolor=c, lw=1.0, ls='--', zorder=5))
    hinder = K.punkt_hinder(ax, [vg.x, bb.x], [vg.y, bb.y], px=11)
    K.placera_etiketter(ax, etik, fontsize=6.8, undvik=hinder)
    a = RES['antaganden']['bobil']; t = f['tackning']
    infobox(ax, [
        r'$\bf{Körtid\ per\ tur}$' + f"   {'+' if a['delta_min'] > 0 else ''}{sv(a['delta_min'])} min "
        f"({sv(a['kortare_vag_min'])} kortare väg, +{sv(a['uppehall_bobil_min'])} uppehåll Bo-Bil)",
        "väntan vid Nya Godbyvägen ej medräknad – talar för kortare tid",
        r'$\bf{Omlopp}$' + f"   ryms – alla {f['linjens_turer']} turer, {f['omlopp']['alla']['fordon']} bussar, "
        f"vändtid N 4 → {sv(4 - a['delta_min'])} min",
        r'$\bf{Effekt}$' + f"   Bo-Bil får linje N: {t['lyft_fran_svag_inv']} inv. lyfts ur svag tillgänglighet",
        f"Vikingagränd utgår: {t['forlorad_tackning_inv']} inv. utan hållplats inom 400 m",
        f"(påstigande Vikingagränd i dag ≈ 0,05 per vardag)",
        f"Resenärer: {'+' if f['resenarer']['vardag']['resenarsminuter'] > 0 else ''}"
        f"{sv(f['resenarer']['vardag']['resenarsminuter'], 0)} resenärsminuter per vardag"], loc=(0.025, 0.975))
    extra = [Line2D([], [], color='#3d3d3a', lw=3, ls=(0, (1.2, 1.6)), label='Körväg som utgår'),
             Line2D([], [], color=C.FARG_LINJE['N'], lw=2.4, ls=(0, (3, 2)), label='Ny körväg linje N'),
             Line2D([], [], marker='X', ls='', color=SAMRE, markersize=8, label='Vikingagränd (utgår för N)'),
             Line2D([], [], marker='*', ls='', color=BLA, markersize=12, label='Bo-Bil (ny för N)')]
    lg = K.teckenforklaring(ax, forklaring_tackning(extra), loc='lower left', fontsize=6.8)
    lg.set_bbox_to_anchor((1.02, 0.0), transform=ax.transAxes)
    K.ram(ax)
    return K.spara(fig, 'b4_6_bobil_karta.png')


def _pilar(ax, xy, farg, steg=230.0, uts=None, ms=15, zorder=7):
    """Riktningspilar längs en linje ((N,2)-array i körriktningen) med ungefär steg m mellanrum."""
    L = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])
    for d in np.arange(steg / 2, L[-1], steg):
        j = int(np.searchsorted(L, d)); j = min(max(j, 1), len(xy) - 1)
        a, b = xy[j - 1], xy[j]
        if uts and not (uts[0] < b[0] < uts[1] and uts[2] < b[1] < uts[3]):
            continue
        ax.annotate('', xy=tuple(b), xytext=tuple(a), zorder=zorder,
                    arrowprops=dict(arrowstyle='-|>', color=farg, lw=0, mutation_scale=ms))


def _kedja(stopp, sg, fg):
    """Hållplatsföljd → sammanhängande linje längs gatunätet (OSRM)."""
    delar = []
    for a, b in zip(stopp[:-1], stopp[1:]):
        if (a, b) in sg:
            delar.append(sg[(a, b)])
        elif (a, b) in fg:
            delar.append(fg[(a, b)]['xy'])
    return K.sammanfoga(delar, tol=60)


def fig_svangen():
    """UA 5 – var linje N och V kör i dag och med UA 5 (två kartor sida vid sida på OSM-bakgrund)."""
    import bakgrundskarta as BK
    import s01_vagdragning as V
    from shapely.geometry import LineString as LS
    f = RES['ua']['5']; u = f['ua5']; o = f['omlopp']
    H = {'Sjukhuset': '9025302000039601', 'Stenhuggarvägen': '9025302000062401', 'Cedersvägen': '9025302000062701',
         'Klintvägen': '9025302000062901', 'Elverksgatan': '9025302000063701', 'Västra macken': '9025302000055901',
         'Tekniska verken': '9025302000049201', 'Åsvägen': '9025302000067401', 'Räddningsverket': '9025302000064201',
         'Ålandsplan': '9025302000056701', 'Nabben': '9025302000032401'}
    sg = V.segmentgeometri(); fg = V.uageometri(); mon = V.monster_per_linje()
    nm, vm = list(mon['N'][0][0]), list(mon['V'][0][0])
    def ersatt(s_, fore, efter):
        i = next(i for i in range(len(s_)) if s_[i:i + len(fore)] == fore)
        return s_[:i] + efter + s_[i + len(fore):]
    sv_ = [H[k] for k in ('Sjukhuset', 'Stenhuggarvägen', 'Cedersvägen', 'Klintvägen', 'Elverksgatan')]
    nm5 = ersatt(nm, sv_, [H['Sjukhuset'], H['Västra macken'], H['Elverksgatan']])
    vm5 = ersatt(vm, [H['Åsvägen'], H['Västra macken'], H['Tekniska verken']],
                 [H['Åsvägen'], H['Stenhuggarvägen'], H['Cedersvägen'], H['Klintvägen'], H['Tekniska verken']])
    scen = [('I dag', nm, vm), ('UA 5', nm5, vm5)]
    uts = (107170, 107900, 6684150, 6685420)
    xy = HPL.groupby(level=0)[['x', 'y']].first()
    fig, axs = plt.subplots(1, 2, figsize=(13.2, 11.6), gridspec_kw={'wspace': 0.03})
    FN, FV = C.FARG_LINJE['N'], C.FARG_LINJE['V']
    for ax, (rub, n_, v_) in zip(axs, scen):
        BK.rita(ax, uts, stil='gra')
        ax.set_xlim(uts[0], uts[1]); ax.set_ylim(uts[2], uts[3]); ax.set_aspect('equal')
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_edgecolor('#d0d0cc'); sp.set_linewidth(0.7)
        ax.set_title(rub, loc='left', pad=4)
        for ln, stopp, farg, off in (('N', n_, FN, 5.0), ('V', v_, FV, -5.0)):
            for d in _kedja(stopp, sg, fg):
                try:
                    d2 = np.asarray(LS(d).offset_curve(off).coords)
                    if len(d2) < 2 or np.hypot(*(d2[0] - d[0])) > 30:
                        d2 = d
                except Exception:
                    d2 = d
                ax.plot(d2[:, 0], d2[:, 1], color=farg, lw=4.4, zorder=5, solid_capstyle='round',
                        solid_joinstyle='round', path_effects=[K.pe.Stroke(linewidth=6.8, foreground='white'), K.pe.Normal()])
                _pilar(ax, d2, farg, steg=240, uts=uts, ms=22)
        # hållplatser: färgade efter vilken linje (N eller V) som stannar där
        n_set, v_set = set(n_), set(v_)
        etik = []
        for namn_, sid in H.items():
            if sid not in xy.index:
                continue
            x_, y_ = xy.loc[sid, ['x', 'y']]
            if not (uts[0] < x_ < uts[1] and uts[2] < y_ < uts[3]):
                continue
            i_n, i_v = sid in n_set, sid in v_set
            if not (i_n or i_v):
                ax.scatter([x_], [y_], s=26, facecolor='white', edgecolor='#7a776f', lw=0.8, zorder=8)
                etik.append((namn_, (x_, y_), 30)); continue
            fc = FN if i_n and not i_v else FV if i_v and not i_n else 'white'
            ax.scatter([x_], [y_], s=90, facecolor=fc, edgecolor='#1f1f1e' if (i_n and i_v) else 'white', lw=1.4,
                       zorder=9)
            etik.append((namn_, (x_, y_), 60))
        hinder = K.punkt_hinder(ax, [p[1][0] for p in etik], [p[1][1] for p in etik], px=9)
        K.placera_etiketter(ax, etik, fontsize=7.0, undvik=hinder)
    K.skalstock(axs[0], langd_m=200)
    hnd = [Line2D([], [], color=FN, lw=4, label='Norra'),
           Line2D([], [], color=FV, lw=4, label='Västra'),
           Line2D([], [], marker='o', ls='', markerfacecolor=FN, markeredgecolor='white', markersize=9, label='Hållplats för N'),
           Line2D([], [], marker='o', ls='', markerfacecolor=FV, markeredgecolor='white', markersize=9, label='Hållplats för V'),
           Line2D([], [], marker='o', ls='', markerfacecolor='white', markeredgecolor='#1f1f1e', markersize=9,
                  label='Hållplats för N och V')]
    fig.legend(handles=hnd, loc='upper center', ncol=5, fontsize=7.5, frameon=False,
               bbox_to_anchor=(0.5, axs[0].get_position().y0 - 0.005))
    fig.suptitle('UA 5 – svängen via Cedersvägen byter från linje N till V', x=0.125, ha='left',
                 y=axs[0].get_position().y1 + 0.035)
    return K.spara(fig, 'b4_17_svangen_karta.png')


def fig_flygtider():
    """UA 4: flygen (avgångar och ankomster), fönstret då bussen ska vara vid flygplatsen och de V-turer som når
    flygen – i huvudalternativet, i UA 4Y och som extra turer."""
    import b5_kalkyl as B5
    fp = RES['flygplatsen']; f = RES['ua']['4']; vo = f['omlopp'][f['huvudalternativ']]
    tl = SCEN[SCEN.scenario == 'idag'].set_index('trip_id')
    hm = lambda x: int(x[:2]) * 60 + int(x[3:])
    fram = fp['framme_vid_flygplatsen_min_efter_avgang']
    v = SCEN[(SCEN.scenario == 'idag') & (SCEN.linje == 'V')].sort_values('avg')
    via = set(SCEN[(SCEN.scenario == f"4_{f['huvudalternativ']}") & (SCEN.delta > 0)].trip_id)
    m = fp['matchning']; ex = {e['flyg']: e for e in fp['extraturer']}
    fig, ax = plt.subplots(figsize=(12.4, 4.6))
    rader = [r['flyg'] for r in m]
    ny = len(rader)
    for yy, r in enumerate(m):
        a, b = r['fonster'].split('–')
        ax.axhspan(yy - 0.32, yy + 0.32, xmin=0, xmax=0, color='none')
        ax.fill_betweenx([yy - 0.3, yy + 0.3], hm(a), hm(b), color='#cfe3f8', zorder=1, lw=0)
        t_ = hm(r['tid'])
        ax.scatter([t_], [yy], marker='^' if r['typ'] == 'avgång' else 'v', s=110, color='#1f1f1e', zorder=4)
        ax.annotate(f"{r['tid']}", (t_, yy), xytext=(0, 9), textcoords='offset points', ha='center', fontsize=7,
                    color=K.TEXT, zorder=5)
        if r.get('v_tur'):
            x = hm(r['vid_flygplatsen'])
            ax.scatter([x], [yy], marker='o', s=70, color=FARG_VO, edgecolor='white', lw=0.8, zorder=5)
            ax.annotate(f"{r['vid_flygplatsen']}", (x, yy), xytext=(0, -13),
                        textcoords='offset points', ha='center', fontsize=6.8, color=FARG_VO, zorder=5)
        elif r['flyg'] in ex:
            e = ex[r['flyg']]; x = hm(e['vid_flygplatsen'])
            ax.scatter([x], [yy], marker='o', s=70, color='#e8590c', edgecolor='white', lw=0.8, zorder=5)
            ax.annotate(f"{e['vid_flygplatsen']}",
                        (x, yy), xytext=(0, -13), textcoords='offset points', ha='center', fontsize=6.8, color='#e8590c',
                        zorder=5)
    # alla V-turer vid flygplatsen (huvudalternativet) och de som kör som i dag
    yv = ny + 0.4
    for r in v.itertuples():
        x = r.avg + fram
        ax.plot([x, x], [yv - 0.25, yv + 0.25], color=FARG_VO if r.trip_id in via else '#b9b4a8', lw=2.2, zorder=3)
    ax.set_yticks(list(range(ny)) + [yv])
    ax.set_yticklabels(rader + ['V-turer vid flygplatsen, UA 4 ★'], fontsize=7.4)
    ax.set_ylim(yv + 0.7, -0.8)
    tick = list(range(5 * 60, 23 * 60 + 1, 60))
    ax.set_xticks(tick); ax.set_xticklabels([f'{t // 60:02d}' for t in tick], fontsize=7.4)
    ax.set_xlim(5 * 60 - 10, 23 * 60 + 10); ax.grid(axis='x', color='#e6e4de', lw=0.6); ax.set_axisbelow(True)
    for s_ in ['top', 'right']:
        ax.spines[s_].set_visible(False)
    hnd = [Patch(facecolor='#cfe3f8', label='Bussen ska vara vid flygplatsen'),
           Line2D([], [], marker='^', ls='', color='#1f1f1e', markersize=8, label='Flyget avgår'),
           Line2D([], [], marker='v', ls='', color='#1f1f1e', markersize=8, label='Flyget landar'),
           Line2D([], [], marker='o', ls='', color=FARG_VO, markersize=8, label='Västra-tur via flygplatsen'),
           Line2D([], [], marker='o', ls='', color='#e8590c', markersize=8, label='Extra V-tur'),
           Line2D([], [], color='#b9b4a8', lw=2.2, label='V-tur som i dag')]
    ax.legend(handles=hnd, loc='upper right', fontsize=7, ncol=1, frameon=True, facecolor='white', edgecolor='#e0ded7')
    fig.suptitle('UA 4 – flygen och bussen vid flygplatsen (vardag)', x=0.01, ha='left')
    ut = C.KARTOR / 'b4_19_flygtider.png'
    K.fullnamn_fig(fig); fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


def fig_flygplatsen_zoom():
    """UA 4 inzoomat: linje V–Ö via flygterminalen längs gatunätet (OSRM) på en OSM-bakgrund."""
    import bakgrundskarta as BK
    import s01_vagdragning as V
    fp = RES['flygplatsen']; f = RES['ua']['4']; o = f['omlopp'][f['huvudalternativ']]
    uts = (106080, 107320, 6685760, 6687320)
    fig, ax = plt.subplots(figsize=(8.4, 10.4))
    BK.rita(ax, uts, stil='gra')
    ax.set_xlim(uts[0], uts[1]); ax.set_ylim(uts[2], uts[3]); ax.set_aspect('equal')
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor('#d0d0cc'); sp.set_linewidth(0.7)
    ax.set_title('UA 4 – Västra–Östra via flygterminalen', loc='left', pad=4)
    K.rita_linjer(ax, lw=1.8, alpha=0.45, zorder=2, etikett=False)
    sg = V.segmentgeometri(); fg = V.uageometri()
    PO, KA, FL = '9025302000035802', '9025302000025902', 'FLYGPLATSEN'
    halo = [K.pe.Stroke(linewidth=6.6, foreground='white'), K.pe.Normal()]
    mon = V.monster_per_linje()['V'][0][0]
    i = list(mon).index(PO)
    delar = [sg[k] for k in zip(mon[:i], mon[1:i + 1])] + [fg[(PO, FL)]['xy'], fg[(FL, KA)]['xy']] + \
        [sg[k] for k in zip(mon[i + 1:-1], mon[i + 2:])]
    for d in K.sammanfoga(delar):
        ax.plot(d[:, 0], d[:, 1], color=FARG_VO, lw=4.2, zorder=5, solid_capstyle='round', solid_joinstyle='round',
                path_effects=halo)
    for k in [(PO, FL), (FL, KA)]:                              # körriktning
        p = fg[k]['xy']; L = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(p, axis=0).T))])
        for t_ in (0.3, 0.7):
            j = int(np.searchsorted(L, t_ * L[-1])); j = min(max(j, 1), len(p) - 1)
            ax.annotate('', xy=tuple(p[j]), xytext=tuple(p[j - 1]), zorder=6,
                        arrowprops=dict(arrowstyle='-|>', color='#4a1d3e', lw=0, mutation_scale=24))
    flx, fly = V.FLYGPLATSEN_XY
    ax.add_patch(plt.Circle((flx, fly), C.TACKNING_M, facecolor=to_rgba(BLA, 0.06), edgecolor=BLA, lw=1.0,
                            ls='--', zorder=3))
    etik = hallplatser(ax, uts, ['Posten', 'Källarvägen', 'Dalkullavägen', 'Lönnhagsvägen', 'Sviby bro'])
    ax.scatter([flx], [fly], s=320, marker='*', color=BLA, edgecolor='white', lw=1.0, zorder=8)
    hinder = K.punkt_hinder(ax, [flx], [fly], px=13)
    K.placera_etiketter(ax, etik + [('Flygterminalen', (flx, fly), 120)], fontsize=7.0, undvik=hinder)
    hnd = [Line2D([], [], color=FARG_VO, lw=4, label='Västra–Östra'),
           Line2D([], [], marker='*', ls='', color=BLA, markersize=13, label='Ny hållplats vid terminalen'),
           Patch(facecolor=to_rgba(BLA, 0.06), edgecolor=BLA, ls='--', label='400 m runt ny hållplats'),
           Line2D([], [], marker='o', ls='', markerfacecolor='white', markeredgecolor='#1f1f1e', label='Hållplats'),
           Line2D([], [], color='#9a978f', lw=1.8, alpha=0.6, label='Övriga linjer')]
    lg = K.teckenforklaring(ax, hnd, loc='lower left')
    lg.set_bbox_to_anchor((1.02, 0.0), transform=ax.transAxes)
    K.skalstock(ax, langd_m=200)
    return K.spara(fig, 'b4_20_flygplatsen_zoom.png')


def FF(m):
    return f"{m // 60} h" if m % 60 == 0 else sv(m / 60) + ' h'


# ====================================================================== omloppsfigurer
def panel_titel(fid, k):
    t, ok = _panel_titel(fid, k)
    f = RES['ua'][fid]; o = f['omlopp'][k]
    if k == f.get('huvudalternativ'):
        t = '★ ' + t
    if o['fordon'] > RES['idag']['fordon']:
        t = t.replace(' – ryms inte', ' – ryms inte (utesluten)')
    return 'UA ' + t if not t.startswith('★') else '★ UA ' + t[2:], ok


def _panel_titel(fid, k):
    f = RES['ua'][fid]; o = f['omlopp'][k]
    n, tot = o['turer_med_andring'], f['linjens_turer']
    if k.startswith('Y'):
        tot = len(RES['flygplatsen']['flygturer'])
        t = (f"{fid}Y flygturerna – {n} av {tot} ändrade" + (', V och Ö sammanslagna' if 'VO' in k else '')
             + (', Solberget indragen' if 'sol' in k else '') + f": {o['fordon']} bussar – " + ('ryms' if o['ryms'] else 'ryms inte'))
        return t, o['ryms']
    if k == 'alla':
        t = f"{fid} – alla {tot} turer ändrade: {o['fordon']} bussar"
        if o['fordon'] > RES['idag']['fordon']:
            t += ' – ryms inte'
        elif not o['ryms']:
            t += ' – ryms inte'
        else:
            t += ' – ryms'
    elif k == 'N':
        t = f"{fid} variant – bara linje N rakt på: {o['fordon']} bussar – ryms"
    elif k == 'robust':
        t = f"{fid} robust – {n} av {tot} turer ändrade: {o['fordon']} bussar – ryms"
    elif k.startswith('VO'):
        sk = max(o['skiftade_turer'].values()) if o['skiftade_turer'] else 0
        t = (f"{fid} V och Ö sammanslagna{', Solberget indragen' if 'sol' in k else ''} – {n} av {tot} turer ändrade"
             + f": {o['fordon']} bussar – ryms")
    else:
        t = f"{fid} dagens tidtabell – {n} av {tot} turer ändrade: {o['fordon']} bussar – ryms"
    return t, o['ryms']


def varv_text(f, o):
    if f['linje'] == 'V':
        return (f"   ·   varv V + Ö < {sv(O.MARGINAL_VARV, 0)} min i centrum: {o['varv_vo_under_marginal']} "
                f"(i dag {RES['idag']['varv_vo_under_marginal']})")
    return f"   ·   varv < 3 min reglering: {o['varv_utan_reglering']} (i dag {RES['idag']['varv_utan_reglering']})"


def fig_omlopp(namn, paneler, rubrik):
    h = 1.75
    fig, axs = plt.subplots(len(paneler), 1, figsize=(12.4, 0.75 + h * len(paneler)), squeeze=False)
    for ax, (scen, fid, k) in zip(axs[:, 0], paneler):
        pl = SCEN[SCEN.scenario == scen].copy()
        andrade = set(pl.loc[pl.delta != 0, 'trip_id'])
        if scen == 'idag':
            titel, ok = (f"I dag – {RES['idag']['fordon']} bussar", True)
        else:
            titel, ok = panel_titel(fid, k)
        O.rita_omlopp(ax, pl, titel=titel, andrade=andrade)
        ax.title.set_color(K.TEXT if ok else SAMRE)
        if not ok:
            for lbl in ax.get_yticklabels():
                if lbl.get_text() == f"Buss {pl.buss.max()}":
                    lbl.set_color(SAMRE); lbl.set_fontweight('bold')
    fig.suptitle(rubrik, x=0.01, ha='left')
    extra = [Patch(facecolor='white', edgecolor='#52514e', hatch='//////', label='Tillagd körtid'),
             Line2D([], [], color=BLA, lw=2.2, label='Kort byte (< 3 min)')]
    if any(SCEN.loc[SCEN.scenario == p[0], 'skift'].fillna(0).gt(0).any() for p in paneler):
        extra.append(Patch(facecolor='none', edgecolor='#1f1f1e', ls=(0, (1, 1)), label='Avgår senare än i dag'))
    if any(SCEN.loc[SCEN.scenario == p[0], 'delta'].fillna(0).lt(0).any() for p in paneler):
        n_kort = any(((SCEN.scenario == p[0]) & (SCEN.delta < 0) & (SCEN.linje == 'N')).any() for p in paneler)
        extra.append(Line2D([], [], color='#1f1f1e', lw=0.9, marker='|', ls='', markersize=8,
                            label='Kortare N-tur' if n_kort else 'Kortare Ö-tur'))
    O.omlopp_forklaring(fig, extra=extra, y=-0.01)
    fig.tight_layout(rect=(0, 0.035, 1, 0.975), h_pad=0.9)
    ut = C.KARTOR / namn
    K.fullnamn_fig(fig); fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


def main():
    print(fig_mockelo()); print(fig_n2()); print(fig_bobil())
    print(fig_omlopp('b4_3_mockelo_omlopp.png',
                     [('idag', None, None), ('1a_alla', '1a', 'alla'), ('1a_ryms', '1a', 'ryms'), ('1a_VO', '1a', 'VO'),
                      ('1b_alla', '1b', 'alla'), ('1b_VO', '1b', 'VO')],
                     'UA 1a och 1b – omlopp'))
    print(fig_omlopp('b4_5_n2_omlopp.png', [('idag', None, None), ('2_alla', '2', 'alla')],
                     'UA 2 – omlopp'))
    print(fig_omlopp('b4_7_bobil_omlopp.png', [('idag', None, None), ('3_alla', '3', 'alla')],
                     'UA 3 – omlopp'))
    print(fig_omlopp('b4_12_flygplatsen_omlopp.png',
                     [('idag', None, None), ('4_alla', '4', 'alla'), ('4_ryms', '4', 'ryms'), ('4_VO', '4', 'VO'),
                      ('4_VO_sol', '4', 'VO_sol'), ('4_Y_VO', '4', 'Y_VO')],
                     'UA 4 – omlopp'))
    print(fig_svangen())
    print(fig_omlopp('b4_18_svangen_omlopp.png',
                     [('idag', None, None), ('5_alla', '5', 'alla'), ('5_ryms', '5', 'ryms'), ('5_VO', '5', 'VO'),
                      ('5_N', '5', 'N')],
                     'UA 5 – omlopp'))
    print(fig_flygtider())
    print(fig_flygplatsen_zoom())


if __name__ == '__main__':
    main()
