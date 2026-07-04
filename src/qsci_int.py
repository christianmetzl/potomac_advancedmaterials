"""Integral-based QSCI growth (the 40q enabler).

The JW-Pauli engine (qsci_lib.PauliEngine.qsci_fast) evaluates <I|H|J> by iterating ~N^4 Pauli terms,
which dominates cost past ~28 qubits. Slater-Condon rules give <I|H|J> directly from the 1-/2-electron
MO integrals in O(1) per connected pair, and connections are ONLY single/double excitations — so both
the Hamiltonian build and the CIPSI candidate scan cost scale with the subspace/excitation structure,
NOT with 2^N or the operator length. This makes 40q growth to ~1e6 determinants tractable.

Validated bit-for-bit against PauliEngine.qsci_fast and exact FCI (see validate_qsci_int in scratchpad).
EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "encoder"))
import numpy as np
import scipy.sparse as sp, scipy.sparse.linalg as sla
from sci_integrals import SCI, _occ

_PC = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)
def _poppar(x):
    """Parity of popcount of each uint64 in array x."""
    b = np.ascontiguousarray(x, dtype=np.uint64).view(np.uint8).reshape(-1, 8)
    return (_PC[b].sum(1) & 1).astype(np.int64)


class IntEngine:
    """Determinant-subspace QSCI on MO integrals (Slater-Condon), spin-orbital interleaved."""

    def __init__(self, h1, eri, ecore, nq):
        self.sci = SCI(h1, eri, ecore)
        self.nq = nq
        self.eri = np.asarray(eri)
        self.spin = np.array([q & 1 for q in range(nq)], dtype=np.int64)   # spin of each spin-orbital

    # ---- vectorized phase for a double excitation (i,j removed; a,b added) from source det I -----
    @staticmethod
    def _pcount_below(D, x):
        """popcount of bits of D (uint64 array) strictly below bit position x (int array), parity."""
        mask = (np.uint64(1) << x.astype(np.uint64)) - np.uint64(1)
        return _poppar(D & mask)

    def _double_phase(self, I, i, j, a, b):
        """(-1)^(...) sign for a†_a a†_b a_j a_i on |I>, matching sci_integrals._phase_double.
        i<j are removed (occupied in I), a<b added (virtual)."""
        one = np.uint64(1)
        s1 = self._pcount_below(I, i)
        Ip = I ^ (one << i.astype(np.uint64))
        s2 = self._pcount_below(Ip, j)
        J = I ^ (one << i.astype(np.uint64)) ^ (one << j.astype(np.uint64)) \
              ^ (one << a.astype(np.uint64)) ^ (one << b.astype(np.uint64))
        s3 = self._pcount_below(J, a)
        Jr = J ^ (one << a.astype(np.uint64))
        s4 = self._pcount_below(Jr, b)
        return 1.0 - 2.0 * ((s1 + s2 + s3 + s4) & 1)

    def _doubles_vec(self, d):
        """All spin-conserving double excitations from det d: (candidate dets, matrix elements)."""
        occ = np.array(_occ(d), dtype=np.int64)
        virt = np.array([a for a in range(self.nq) if not (d >> a) & 1], dtype=np.int64)
        oi_i, oj_i = np.triu_indices(len(occ), 1)
        va_i, vb_i = np.triu_indices(len(virt), 1)
        oi = occ[oi_i]; oj = occ[oj_i]; va = virt[va_i]; vb = virt[vb_i]
        # cross product occ-pairs x virt-pairs
        OI = np.repeat(oi, len(va)); OJ = np.repeat(oj, len(va))
        VA = np.tile(va, len(oi)); VB = np.tile(vb, len(oi))
        sp = self.spin
        keep = (sp[OI] + sp[OJ]) == (sp[VA] + sp[VB])          # spin-conserving
        OI, OJ, VA, VB = OI[keep], OJ[keep], VA[keep], VB[keep]
        if len(OI) == 0:
            return np.empty(0, dtype=np.uint64), np.empty(0)
        one = np.uint64(1)
        cand = (np.uint64(d) ^ (one << OI.astype(np.uint64)) ^ (one << OJ.astype(np.uint64))
                ^ (one << VA.astype(np.uint64)) ^ (one << VB.astype(np.uint64)))
        e = self.eri; h = OI // 2; hj = OJ // 2; ha = VA // 2; hb = VB // 2
        # aphys(i,j,a,b) = <ij|ab> - <ij|ba> ; phys(p,q,r,s)=eri[p//2,r//2,q//2,s//2] with spin checks
        d1 = ((sp[OI] == sp[VA]) & (sp[OJ] == sp[VB])) * e[h, ha, hj, hb]
        d2 = ((sp[OI] == sp[VB]) & (sp[OJ] == sp[VA])) * e[h, hb, hj, ha]
        elem = (d1 - d2) * self._double_phase(np.uint64(d) * np.ones(len(OI), dtype=np.uint64),
                                              OI, OJ, VA, VB)
        return cand, elem

    def _singles_vec(self, d):
        """All same-spin single excitations from det d: (candidate dets, matrix elements)."""
        occ = np.array(_occ(d), dtype=np.int64)
        virt = np.array([a for a in range(self.nq) if not (d >> a) & 1], dtype=np.int64)
        out_c, out_e = [], []
        for i in occ.tolist():
            for a in virt.tolist():
                if (i & 1) == (a & 1):
                    out_c.append(d ^ (1 << i) ^ (1 << a))
                    out_e.append(self.sci.element(d, d ^ (1 << i) ^ (1 << a)))
        return (np.array(out_c, dtype=np.uint64) if out_c else np.empty(0, dtype=np.uint64),
                np.array(out_e) if out_e else np.empty(0))

    def connections_elem(self, d):
        """All connected dets (single+double) and their <d|H|cand> elements (vectorized doubles)."""
        cs, es = self._singles_vec(d); cd, ed = self._doubles_vec(d)
        return np.concatenate([cs, cd]), np.concatenate([es, ed])

    # ---- diagonal energies (vectorized per-batch over the same SCI.diag formula) -------------
    def diag_many(self, dets):
        sci = self.sci
        return np.array([sci.diag(_occ(int(d))) for d in dets], dtype=float)

    # ---- candidate connections: single + double excitations from a determinant ---------------
    def _connections(self, d):
        """All determinants connected to d by a single or double excitation (same electron count),
        as a numpy uint64 array (candidates; may include dets already in the space)."""
        occ = _occ(d)
        nq = self.nq
        virt = [a for a in range(nq) if not (d >> a) & 1]
        out = []
        # singles i->a, same spin (opposite-spin single has zero matrix element)
        for i in occ:
            si = i & 1
            for a in virt:
                if (a & 1) == si:
                    out.append(d ^ (1 << i) ^ (1 << a))
        # doubles ij->ab; spin must match as (si,sj)->(sa,sb) up to the antisymmetrized element
        no = len(occ); nv = len(virt)
        for x in range(no):
            i = occ[x]
            for y in range(x + 1, no):
                j = occ[y]
                dij = d ^ (1 << i) ^ (1 << j)
                sij = (i & 1) + (j & 1)                      # total beta count removed
                for u in range(nv):
                    a = virt[u]
                    for v in range(u + 1, nv):
                        b = virt[v]
                        if (a & 1) + (b & 1) == sij:          # spin-conserving pair
                            out.append(dij ^ (1 << a) ^ (1 << b))
        return np.array(out, dtype=np.uint64) if out else np.empty(0, dtype=np.uint64)

    # ---- subspace Hamiltonian (sparse) via Slater-Condon on connected pairs (vectorized) ------
    def build_H(self, space):
        n = len(space)
        sc = np.sort(space); order = np.argsort(space)
        R = [np.arange(n)]; C = [np.arange(n)]; V = [self.diag_many(space)]   # diagonal
        for k, d in enumerate(space):
            cand, elem = self.connections_elem(int(d))
            if len(cand) == 0: continue
            pos = np.clip(np.searchsorted(sc, cand), 0, n - 1)
            ins = sc[pos] == cand
            j = order[pos[ins]]; v = elem[ins]
            up = j > k                                                   # upper triangle once
            jj = j[up]; vv = v[up]
            if len(jj):
                R += [np.full(len(jj), k), jj]; C += [jj, np.full(len(jj), k)]; V += [vv, vv]
        return sp.csr_matrix((np.concatenate(V), (np.concatenate(R), np.concatenate(C))),
                             shape=(n, n))

    def ground(self, space, warm=None):
        H = self.build_H(space)
        n = H.shape[0]
        if n < 6:
            w, v = np.linalg.eigh(H.toarray()); return float(w[0]), v[:, 0]
        v0 = None
        if warm is not None:
            v0 = np.zeros(n); v0[:len(warm)] = np.real(warm)
        w, v = sla.eigsh(H, k=1, which="SA", v0=v0)
        return float(w[0]), np.asarray(v[:, 0]).ravel()

    # ---- QSCI with CIPSI growth (integral-based candidate scan) -------------------------------
    def qsci(self, seed_dets, grow_iters=0, grow_per_iter=400, kcap=6000, tcap=1e9, log=None):
        space = np.array(sorted(set(int(d) for d in seed_dets)), dtype=np.uint64)
        t0 = time.time(); E, cvec = self.ground(space)
        if log: log(f"  QSCI# seed |space|={len(space)}  E={E:.6f}  [{time.time()-t0:.0f}s]")
        for it in range(grow_iters):
            if len(space) >= kcap or time.time() - t0 > tcap: break
            sc = np.sort(space)
            cand = np.empty(0, dtype=np.uint64); num = np.empty(0)      # compacted, memory-bounded
            sig = np.where(np.abs(cvec) > 1e-4)[0]
            BATCH = 400
            for b0 in range(0, len(sig), BATCH):
                us, as_ = [cand], [num]
                for ci in sig[b0:b0 + BATCH]:
                    conn, elem = self.connections_elem(int(space[ci]))
                    pos = np.clip(np.searchsorted(sc, conn), 0, len(space) - 1)
                    ext = sc[pos] != conn
                    us.append(conn[ext]); as_.append(elem[ext] * cvec[ci])
                allu = np.concatenate(us); alla = np.concatenate(as_)
                cand, inv = np.unique(allu, return_inverse=True)
                num = np.zeros(len(cand)); np.add.at(num, inv, alla)
            if len(cand) == 0: break
            den = E - self.diag_many(cand); den[np.abs(den) < 1e-9] = -1e-9
            keep = cand[np.argsort(num ** 2 / np.abs(den))[::-1][:grow_per_iter]]
            newd = np.setdiff1d(keep, space)
            if len(newd) == 0: break
            space = np.concatenate([space, newd])
            E, cvec = self.ground(space, warm=cvec)
            if log: log(f"  QSCI# grow it{it+1} |space|={len(space)}  E={E:.6f}  [{time.time()-t0:.0f}s]")
        return E, space


def _selftest():
    """Reproducible: Slater-Condon subspace H == JW engine, and grown QSCI == exact FCI (H4/H6)."""
    import qsci_lib as L
    ok = True
    for na in (4, 6):
        P = L.hchain_problem(na, do_fci=True)
        peng = L.PauliEngine(P["qop"].terms)
        ieng = IntEngine(P["h1"], P["eri"], P["ecore"], P["nq"])
        hf = L.hf_det(P["ne"])
        exc = L.mp2_excitation_lists(P["t2"], P["nocc"], P["nq"], top_m=64)
        seed = {hf}
        for p, q_, r, s in zip(exc["p"], exc["q"], exc["r"], exc["s"]):
            d = hf
            for o in (p, q_): d &= ~(1 << o)
            for o in (r, s): d |= (1 << o)
            if bin(d).count("1") == P["ne"]: seed.add(d)
        sp_ = np.array(sorted(seed), dtype=np.uint64)
        Ej, _ = peng.ground(sp_); Ei, _ = ieng.ground(sp_)
        Eg, spg = ieng.qsci(seed, grow_iters=40, grow_per_iter=200, kcap=10**9)
        dA, dF = abs(Ej - Ei) * 1e3, abs(Eg - P["e_fci"]) * 1e3
        ok &= dA < 1e-6 and dF < 1.6
        print(f"H{na} {P['nq']}q: SC-vs-JW |dE|={dA:.2e} mHa; grown vs FCI={dF:.4f} mHa ({len(spg)}d) "
              f"{'OK' if dA < 1e-6 and dF < 1.6 else 'BAD'}")
    print("INTEGRAL ENGINE VALID" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    import sys as _s
    _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    _s.exit(0 if _selftest() else 1)
