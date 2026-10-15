# -*- coding: utf-8 -*-
"""B4 – Restidsnät med utbytbara turmönster och nätutläggning av OD-matrisen.

Samma nätmodell som i A1 (a1_od_granskning.restidsnat): hållplatsområden som zoner, schemalagd åktid per
mönster (median, GTFS typvardag), bytesstraff 5 min vid byte (ej första påstigning), gång ≤ 400 m mellan zoner.
Här kan mönstren ändras (förlängd körtid, ny/indragen hållplats, genomgående linjer) och den korrigerade
OD-matrisen (A1) läggas ut på nätet för att räkna berörda resor och restidsförändring i resenärsminuter.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import data_las as D  # noqa: E402
from a1_od_granskning import zonkoordinater  # noqa: E402


def monster(linjer=C.STADSLINJER, datum=None):
    """Turmönster per linje: [{'linje', 'stopp', 'zoner', 'akt' (min per segment), 'turer'}]."""
    g = D.gtfs(); om = D.hallplatsomraden()
    t = D.turer_dag(datum, linjer)
    st = g['stop_times'][g['stop_times'].trip_id.isin(t.trip_id)].sort_values(['trip_id', 'seq']).copy()
    st['nasta_arr'] = st.groupby('trip_id').t_arr.shift(-1)
    st['akt'] = st.nasta_arr - st.t_dep
    lin = t.set_index('trip_id').linje
    ut = {}
    for tid, d in st.groupby('trip_id'):
        k = tuple(d.stop_id)
        if k not in ut:
            ut[k] = {'linje': lin[tid], 'stopp': k, 'zoner': tuple(om['omrade'].reindex(list(k)).fillna('?')),
                     'akt_lista': [], 'turer': []}
        ut[k]['akt_lista'].append(d.akt.to_numpy()[:-1]); ut[k]['turer'].append(tid)
    res = []
    for m in ut.values():
        m['akt'] = np.median(np.vstack(m.pop('akt_lista')), axis=0)
        res.append(m)
    return res


class Nat:
    """Lagerindelat nät: lager 0 = ej påstigit, lager 1 = har åkt buss; fordonsnoder per mönster och position."""

    def __init__(self, mon, zoner):
        self.zoner = list(zoner); zi = {z: i for i, z in enumerate(self.zoner)}; nZ = len(self.zoner)
        self.nZ = nZ
        rad, kol, vikt = [], [], []
        self.fordonskant = {}                       # (u, v) -> (mönsterindex, position)
        self.mon = mon

        def kant(a, b, w):
            rad.append(a); kol.append(b); vikt.append(max(w, 1e-6))
        nod = 2 * nZ
        for mi, m in enumerate(mon):
            z = m['zoner']; ids = list(range(nod, nod + len(z))); nod += len(z)
            for k, zz in enumerate(z):
                if zz not in zi:
                    continue
                if k < len(z) - 1:
                    kant(zi[zz], ids[k], 0.0)
                    kant(nZ + zi[zz], ids[k], C.BYTESSTRAFF_MIN)
                if k > 0:
                    kant(ids[k], nZ + zi[zz], 0.0)
            for k in range(len(z) - 1):
                kant(ids[k], ids[k + 1], float(m['akt'][k]))
                self.fordonskant[(ids[k], ids[k + 1])] = (mi, k)
        zk = zonkoordinater().reindex(self.zoner)
        xy = zk[['x', 'y']].to_numpy()
        dd = np.hypot(xy[:, None, 0] - xy[None, :, 0], xy[:, None, 1] - xy[None, :, 1])
        for i in range(nZ):
            for j in range(nZ):
                if i != j and dd[i, j] <= C.GANG_MAX_M:
                    w = dd[i, j] / C.GANG_HAST_M_PER_MIN
                    kant(i, j, w); kant(nZ + i, nZ + j, w)
        self.G = csr_matrix((vikt, (rad, kol)), shape=(nod, nod))
        self.dist, self.pred = dijkstra(self.G, directed=True, indices=list(range(nZ)), return_predecessors=True)

    def restider(self):
        nZ = self.nZ
        c = np.minimum(self.dist[:, :nZ], self.dist[:, nZ:2 * nZ]); np.fill_diagonal(c, 0.0)
        return pd.DataFrame(c, index=self.zoner, columns=self.zoner)

    def utlagg(self, OD):
        """Lägger ut OD (DataFrame zon×zon, resor/h) på kortaste väg. Returnerar flöde per fordonskant
        {(mönsterindex, position): resor/h} och påstigande per (mönsterindex, position)."""
        nZ = self.nZ; flode = {}; past = {}
        OD = OD.reindex(index=self.zoner, columns=self.zoner).fillna(0.0).to_numpy()
        for i in range(nZ):
            for j in range(nZ):
                T = OD[i, j]
                if T <= 0 or i == j:
                    continue
                mal = j if self.dist[i, j] <= self.dist[i, nZ + j] else nZ + j
                if not np.isfinite(self.dist[i, mal]):
                    continue
                v = mal
                while v != i and v >= 0:
                    u = self.pred[i, v]
                    if (u, v) in self.fordonskant:
                        e = self.fordonskant[(u, v)]; flode[e] = flode.get(e, 0.0) + T
                    elif v >= 2 * nZ and u < 2 * nZ:      # påstigning
                        mi, k = self._fordonsnod(v)
                        past[(mi, k)] = past.get((mi, k), 0.0) + T
                    v = u
        return flode, past

    def _fordonsnod(self, v):
        if not hasattr(self, '_nodkarta'):
            self._nodkarta = {}
            for (a, b), (mi, k) in self.fordonskant.items():
                self._nodkarta[a] = (mi, k); self._nodkarta[b] = (mi, k + 1)
        return self._nodkarta[v]


def genomgaende(mon, x='V', y='Ö', uppehall=0.5):
    """Lägger till genomgående mönster x→y och y→x (linjerna sammanslagna): resenären sitter kvar i centrum i
    stället för att byta (inget bytesstraff, uppehåll 0,5 min). Används linjens vanligaste mönster."""
    hx = max([m for m in mon if m['linje'] == x], key=lambda m: len(m['turer']))
    hy = max([m for m in mon if m['linje'] == y], key=lambda m: len(m['turer']))
    ut = list(mon)
    for a_, b_ in ((hx, hy), (hy, hx)):
        akt = np.concatenate([a_['akt'], b_['akt']]); akt[len(a_['akt'])] += uppehall
        ut.append({'linje': a_['linje'] + b_['linje'], 'stopp': a_['stopp'] + b_['stopp'][1:],
                   'zoner': a_['zoner'] + b_['zoner'][1:], 'akt': akt, 'turer': []})
    return ut


def od_matris(per):
    return pd.read_csv(C.PROCESSED / f'a1_od_{per}_korrigerad_matris.csv', index_col=0)


def dagsfaktor():
    """Påstigande per vardag / medel av FM- och EM-matrisens resor per timme (omräkning timme -> vardag)."""
    import json
    r = json.load(open(C.PROCESSED / 'a1_sammanfattning.json', encoding='utf-8'))
    per_dag = r['D3']['pastigande_vardag_med_O'] / C.ANTAL_VARDAGAR
    h = np.mean([od_matris(p).to_numpy().sum() for p in ('FM', 'EM')])
    return per_dag / h


def jamfor(nat0, nat1):
    """Restidsförändring (resenärsminuter per timme) och antal resor med ändrad restid, FM och EM."""
    c0, c1 = nat0.restider(), nat1.restider().reindex(index=nat0.zoner, columns=nat0.zoner)
    ut = {}
    for per in ('FM', 'EM'):
        T = od_matris(per).reindex(index=nat0.zoner, columns=nat0.zoner).fillna(0.0)
        d = (c1 - c0).to_numpy(); Tm = T.to_numpy()
        fin = np.isfinite(d)
        ut[per] = {'resenarsminuter_h': float((Tm[fin] * d[fin]).sum()),
                   'resor_langre_h': float(Tm[fin & (d > 1e-6)].sum()),
                   'resor_kortare_h': float(Tm[fin & (d < -1e-6)].sum()),
                   'resor_utan_forbindelse_h': float(Tm[~fin].sum())}
    return ut


if __name__ == '__main__':
    # kontroll: samma restider som A1
    zon = list(pd.read_csv(C.PROCESSED / 'a1_restider_min.csv', index_col=0).index)
    n = Nat(monster(), zon)
    a1 = pd.read_csv(C.PROCESSED / 'a1_restider_min.csv', index_col=0)
    print('max avvikelse mot A1:', float(np.nanmax(np.abs(n.restider().round(2).to_numpy() - a1.to_numpy()))))
    fl, ps = n.utlagg(od_matris('FM'))
    print('utlagt FM (påstigningar):', round(sum(ps.values()), 2), 'OD-summa:', round(od_matris('FM').to_numpy().sum(), 2))
    print('dagsfaktor:', round(dagsfaktor(), 2))
