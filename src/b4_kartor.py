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
PKT = pd.read_csv(P / 'a2_delpunkter.csv.gz')
TACK = pd.read_csv(P / 'b4_tackning_ua.csv.gz', dtype={'ua': str})
HPL = pd.read_csv(P / 'a2_hallplatser_avgangar.csv', index_col=0)
OTACKT = '#b9b4a8'
BATTRE, SAMRE, BLA = '#2f9e44', '#c0392b', '#1c5cab'
F_HPL_MOCKELO = '9025302000066401'
UTS = {'mockelo': (104450, 107350, 6682650, 6685750), 'n2': (109150, 111550, 6681850, 6685550),
       'bobil': (106950, 109350, 6685250, 6687550), 'flyg': (105450, 107850, 6685250, 6687650)}


def sv(x, d=1):
    return f'{x:.{d}f}'.replace('.', ',').replace('-', '−')


# ====================================================================== kartor
def raster(ax, p, farger, h=C.DELRUTA_M):
    x0, y0 = p.x.min() - h / 2, p.y.min() - h / 2
    ix = ((p.x - x0) // h).astype(int).to_numpy(); iy = ((p.y - y0) // h).astype(int).to_numpy()
    img = np.zeros((iy.max() + 1, ix.max() + 1, 4))
    img[iy, ix] = farger
    ax.imshow(img, origin='lower', extent=(x0, x0 + img.shape[1] * h, y0, y0 + img.shape[0] * h),
              interpolation='nearest', zorder=1)


def tackningslager(ax, fid, uts):
    """Otäckt befolkning efter UA:t (grå) och förändrade delpunkter (grön = bättre, röd = sämre)."""
    x0, x1, y0, y1 = uts
    p = PKT[PKT.x.between(x0 - 100, x1 + 100) & PKT.y.between(y0 - 100, y1 + 100)].copy()
    t = TACK[TACK.ua == fid].set_index(['x', 'y'])
    p = p.set_index(['x', 'y'])
    p['klass_efter'] = p.klass
    gem = p.index.intersection(t.index)
    p.loc[gem, 'klass_efter'] = t.loc[gem, 'klass_efter']
    p = p.reset_index()
    rb = PKT.groupby('ruta_id').bef.sum(); tmax = rb.max()
    tat = p.ruta_id.map(rb)
    alfa = (0.30 + 0.55 * np.sqrt(tat / tmax)).to_numpy()
    rgba = np.zeros((len(p), 4))
    otackt = (p.klass_efter == 0).to_numpy()
    rgba[otackt] = to_rgba(OTACKT); rgba[otackt, 3] = alfa[otackt]
    bat, sam = p.klass_efter > p.klass, p.klass_efter < p.klass
    # grön/röd bara i bebodda rutor; tätheten styr inte färgen här (förändringen ska synas)
    rgba[bat.to_numpy()] = to_rgba(BATTRE, 0.85); rgba[sam.to_numpy()] = to_rgba(SAMRE, 0.85)
    raster(ax, p, rgba)
    return {'battre': float(p.loc[bat, 'bef'].sum()), 'samre': float(p.loc[sam, 'bef'].sum())}


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
    ax.text(loc[0], loc[1], '\n'.join(rader), transform=ax.transAxes, ha='left', va='top', fontsize=7.2,
            color=K.TEXT, zorder=30, linespacing=1.45,
            bbox=dict(boxstyle='round,pad=0.55', facecolor='white', edgecolor='#d6d5d0', lw=0.6, alpha=0.95))


def forklaring_tackning(extra=()):
    h = [Patch(facecolor=BATTRE, alpha=0.85, label='Bättre tillgänglighet (ny täckning/fler avgångar)'),
         Patch(facecolor=SAMRE, alpha=0.85, label='Sämre tillgänglighet'),
         Patch(facecolor=OTACKT, alpha=0.7, label='Ingen hållplats inom 400 m (efter UA:t)')]
    h += list(extra)
    h += [Line2D([], [], color=C.FARG_LINJE[l], lw=2, label=f'Linje {l}') for l in C.STADSLINJER]
    h += [Line2D([], [], marker='o', ls='', markerfacecolor='white', markeredgecolor='#1f1f1e', label='Hållplats')]
    return h


FARG_VO = '#8c3b74'


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
    bakgrund(ax, uts, 'UA 1a och UA 1b – Möckelö Strand ny (linje V–Ö, V och Ö sammanslagna)')
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
    ax.annotate(f"Befintlig väg ({sv(m['restid_befintlig_vag_min'], 0)} min):\nUA 1a fram och tillbaka,\nUA 1b tillbaka (slinga)",
                xy=tuple(kb), xytext=(10, 0), textcoords='offset points', fontsize=6.8,
                color=K.TEXT, ha='left', va='center', zorder=9, path_effects=K.HALO)
    hinder = K.punkt_hinder(ax, [nx], [ny_], px=12)
    K.placera_etiketter(ax, etik + [('Möckelö Strand ny', (nx, ny_), 70)], fontsize=6.8, undvik=hinder)
    o1a, o1b = f1a['omlopp'], f1b['omlopp']
    vo, vor = o1a.get('VO', o1a['alla']), o1a.get('VO_robust', o1a.get('VO', o1a['alla']))
    infobox(ax, [
        r'$\bf{Körtid\ per\ tur}$' + f"   UA 1a +{sv(f1a['delta_min_per_tur'])} min (2 + 0,5 + 2)   ·   "
        f"UA 1b +{sv(f1b['delta_min_per_tur'])} min (1 + 0,5 + 2 − 1)",
        r'$\bf{UA\ 1a\ –\ huvudalternativ}$' + f"   V och Ö sammanslagna (Ö ≤ 2 min efter pulsen):",
        f"      {vo['turer_med_andring']} av {f1a['linjens_turer']} turer, 5 bussar ({vor['turer_med_andring']} lika robust som i dag)",
        f"      övriga: dagens tidtabell {o1a['ryms']['turer_med_andring']} av {f1a['linjens_turer']}; "
        f"alla turer {o1a['alla']['fordon']} bussar (utesluten)",
        r'$\bf{UA\ 1b\ –\ huvudalternativ}$' + f"   alla {f1b['linjens_turer']} turer, 5 bussar – bytet V → Ö 0,5 min",
        f"      (robust: {o1b.get('robust', o1b['alla'])['turer_med_andring']} av {f1b['linjens_turer']})",
        r'$\bf{Effekt}$' + f"   +{f1b['tackning']['ny_tackning_inv']} invånare inom 400 m",
        f"Påstigande ≈ {sv(f1b['nytt_pastigande_vardag'][0])}–{sv(f1b['nytt_pastigande_vardag'][1])} per vardag (UA 1b, sommarnivå)",
        f"Genomresande: +{sv(f1b['resenarer']['vardag']['resenarsminuter'], 0)} (UA 1b) resp. "
        f"+{sv(f1a['resenarer']['vardag']['resenarsminuter'], 0)} (UA 1a) resenärsminuter per vardag"])
    kalla = {'osrm': 'OSRM', 'skiss': 'beställarens skiss'}.get(m['kalla_befintlig_vag'], 'schematisk')
    extra = [Line2D([], [], marker='*', ls='', color=BLA, markersize=12, label='Ny hållplats (läge enligt A3)'),
             Line2D([], [], color=fv, lw=2.4, label=f'Befintlig väg till ny hållplats ({kalla})'),
             Line2D([], [], color=fv, lw=2.4, ls=(0, (3, 2)), label='Förlängd Norrgårdsvägen (UA 1b, schematisk)'),
             Line2D([], [], color=FARG_VO, lw=3, label='Linje V–Ö (V och Ö sammanslagna)'),
             Patch(facecolor='none', edgecolor=BLA, ls='--', label='400 m runt ny hållplats')]
    lg = K.teckenforklaring(ax, forklaring_tackning(extra), loc='lower left', fontsize=6.8)
    lg.set_bbox_to_anchor((1.02, 0.0), transform=ax.transAxes)
    K.ram(ax)
    return K.spara(fig, 'b4_2_mockelo_karta.png')


def fig_n2():
    f = RES['ua']['2']
    uts = UTS['n2']
    fig, ax = plt.subplots(figsize=(7.4, 9.0))
    bakgrund(ax, uts, 'UA 2: ny hållplats N2 på linje Ö')
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
        f"Påstigande ≈ {sv(f['nytt_pastigande_vardag'][0])}–{sv(f['nytt_pastigande_vardag'][1])} per vardag (sommarnivå)",
        f"Ombordvarande: +{sv(f['resenarer']['vardag']['resenarsminuter'], 0)} resenärsminut per vardag"], loc=(0.03, 0.975))
    extra = [Line2D([], [], marker='*', ls='', color=BLA, markersize=12, label='Ny hållplats N2 (läge enligt A3)'),
             Patch(facecolor='none', edgecolor=BLA, ls='--', label='400 m runt N2')]
    lg = K.teckenforklaring(ax, forklaring_tackning(extra), loc='lower left', fontsize=6.8)
    lg.set_bbox_to_anchor((1.02, 0.0), transform=ax.transAxes)
    K.ram(ax)
    return K.spara(fig, 'b4_4_n2_karta.png')


def fig_bobil():
    f = RES['ua']['3']
    uts = UTS['bobil']
    fig, ax = plt.subplots(figsize=(8.6, 8.4))
    bakgrund(ax, uts, 'UA 3: linje N via Bo-Bil i stället för Vikingagränd')
    tackningslager(ax, '3', uts)
    K.rita_linjer(ax, lw=2.2, zorder=4, alpha=0.9)
    etik = hallplatser(ax, uts, ['Maxinge', 'Vikingagränd', 'Bolstavägen', 'Bo-Bil', 'Hjortronstigen', 'Lillåkersvägen'])
    g = {n: HPL[HPL.namn == n][['x', 'y']].mean() for n in ['Maxinge', 'Vikingagränd', 'Bolstavägen', 'Bo-Bil']}
    mx, vg, bv, bb = (g[k] for k in ['Maxinge', 'Vikingagränd', 'Bolstavägen', 'Bo-Bil'])
    import s01_vagdragning as V
    sg_ = V.segmentgeometri(); fg_ = V.uageometri()
    MX, VG, BV, BB = '9025302000031201', '9025302000063201', '9025302000063301', '9025302000003502'
    gl = np.vstack([sg_[(MX, VG)], sg_[(VG, BV)][1:]]) if (MX, VG) in sg_ and (VG, BV) in sg_ else \
        np.array([[mx.x, mx.y], [vg.x, vg.y], [bv.x, bv.y]])
    ny_xy = np.vstack([fg_[(MX, BB)]['xy'], fg_[(BB, BV)]['xy'][1:]])
    ax.plot(gl[:, 0], gl[:, 1], color='#3d3d3a', lw=3.2, ls=(0, (1.2, 1.6)), zorder=6,
            solid_capstyle='round')
    ax.plot(ny_xy[:, 0], ny_xy[:, 1], color=C.FARG_LINJE['N'], lw=2.6, ls=(0, (3, 2)), zorder=6)
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
    extra = [Line2D([], [], color='#3d3d3a', lw=3, ls=(0, (1.2, 1.6)), label='Körväg som utgår (schematisk)'),
             Line2D([], [], color=C.FARG_LINJE['N'], lw=2.4, ls=(0, (3, 2)), label='Ny körväg linje N (schematisk)'),
             Line2D([], [], marker='X', ls='', color=SAMRE, markersize=8, label='Vikingagränd – utgår för linje N'),
             Line2D([], [], marker='*', ls='', color=BLA, markersize=12, label='Bo-Bil – ny hållplats för linje N')]
    lg = K.teckenforklaring(ax, forklaring_tackning(extra), loc='lower left', fontsize=6.8)
    lg.set_bbox_to_anchor((1.02, 0.0), transform=ax.transAxes)
    K.ram(ax)
    return K.spara(fig, 'b4_6_bobil_karta.png')


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
        d = (o['omloppstid_h'] - RES['idag']['omloppstid_h']) * 60
        t += '   ·   omloppstid ' + f"{'+' if d >= 0 else ''}{sv(d, 0)} min/dag"
        t += f"   ·   varv < 3 min reglering: {o['varv_utan_reglering']} (i dag {RES['idag']['varv_utan_reglering']})"
        return t, o['ryms']
    if k == 'alla':
        t = f"{fid} – alla {tot} turer ändrade: {o['fordon']} bussar"
        t += (' – ryms' + ('' if o.get('robust', True) else ' (kort reglering kring Ö:s skolturer)')) if o['ryms'] \
            else ' – ryms inte'
    elif k == 'robust':
        t = f"{fid} robust – {n} av {tot} turer ändrade: {o['fordon']} bussar – ryms"
    elif k.startswith('VO'):
        t = (f"{fid} V och Ö sammanslagna{', Solberget indragen' if 'sol' in k else ''}"
             f"{' (robust)' if k.endswith('robust') else ''} – {n} av {tot} turer ändrade, "
             f"{len(o['skiftade_turer'])} Ö-turer avgår ≤ 2 min senare: {o['fordon']} bussar – ryms")
    else:
        t = f"{fid} – {n} av {tot} turer ändrade (de som ryms): {o['fordon']} bussar – ryms"
    d = (o['omloppstid_h'] - RES['idag']['omloppstid_h']) * 60
    t += '   ·   omloppstid ' + (f"+{sv(d / 60)} h/dag" if d >= 60 else f"{'+' if d >= 0 else ''}{sv(d, 0)} min/dag")
    t += f"   ·   varv < 3 min reglering: {o['varv_utan_reglering']} (i dag {RES['idag']['varv_utan_reglering']})"
    return t, o['ryms']


def fig_omlopp(namn, paneler, rubrik):
    h = 1.75
    fig, axs = plt.subplots(len(paneler), 1, figsize=(12.4, 0.75 + h * len(paneler)), squeeze=False)
    for ax, (scen, fid, k) in zip(axs[:, 0], paneler):
        pl = SCEN[SCEN.scenario == scen].copy()
        andrade = set(pl.loc[pl.delta != 0, 'trip_id'])
        if scen == 'idag':
            titel, ok = (f"I dag – {RES['idag']['fordon']} bussar (växlar S ↔ N och V ↔ Ö), omloppstid "
                         f"{sv(RES['idag']['omloppstid_h'])} h", True)
        else:
            titel, ok = panel_titel(fid, k)
        O.rita_omlopp(ax, pl, titel=titel, andrade=andrade)
        ax.title.set_color(K.TEXT if ok else SAMRE)
        if not ok:
            for lbl in ax.get_yticklabels():
                if lbl.get_text() == f"Buss {pl.buss.max()}":
                    lbl.set_color(SAMRE); lbl.set_fontweight('bold')
    fig.suptitle(rubrik, x=0.01, ha='left', fontsize=11.5, fontweight='bold')
    extra = [Patch(facecolor='white', edgecolor='#52514e', hatch='//////', label='Tillagd körtid'),
             Line2D([], [], color=BLA, lw=2.2, label='Kort byte inom linjeparet (< 3 min)')]
    if any(SCEN.loc[SCEN.scenario == p[0], 'skift'].fillna(0).gt(0).any() for p in paneler):
        extra.append(Patch(facecolor='none', edgecolor='#1f1f1e', ls=(0, (1, 1)), label='Avgår senare än i dag'))
    O.omlopp_forklaring(fig, extra=extra, y=-0.01)
    fig.tight_layout(rect=(0, 0.035, 1, 0.975), h_pad=0.9)
    ut = C.KARTOR / namn
    fig.savefig(ut, dpi=200, bbox_inches='tight', pad_inches=0.08); plt.close(fig)
    return ut


def main():
    print(fig_mockelo()); print(fig_n2()); print(fig_bobil())
    print(fig_omlopp('b4_3_mockelo_omlopp.png',
                     [('idag', None, None), ('1a_alla', '1a', 'alla'), ('1a_ryms', '1a', 'ryms'), ('1a_VO', '1a', 'VO'),
                      ('1b_alla', '1b', 'alla'), ('1b_robust', '1b', 'robust')],
                     'UA 1a och UA 1b Möckelö Strand ny – omlopp före och efter (★ = huvudalternativ)'))
    print(fig_omlopp('b4_5_n2_omlopp.png', [('idag', None, None), ('2_alla', '2', 'alla')],
                     'UA 2 N2 på linje Ö – omlopp före och efter'))
    print(fig_omlopp('b4_7_bobil_omlopp.png', [('idag', None, None), ('3_alla', '3', 'alla')],
                     'UA 3 linje N via Bo-Bil – omlopp före och efter'))
    print(fig_omlopp('b4_12_flygplatsen_omlopp.png',
                     [('idag', None, None), ('4_alla', '4', 'alla'), ('4_ryms', '4', 'ryms'), ('4_VO', '4', 'VO'),
                      ('4_VO_sol', '4', 'VO_sol'), ('4_Y_VO_sol', '4', 'Y_VO_sol')],
                     'UA 4 linje V–Ö via flygplatsen – omlopp före och efter (★ = huvudalternativ)'))


if __name__ == '__main__':
    main()
