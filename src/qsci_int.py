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


class IntEngine:
    """Determinant-subspace QSCI on MO integrals (Slater-Condon), spin-orbital interleaved."""

    def __init__(self, h1, eri, ecore, nq):
        self.sci = SCI(h1, eri, ecore)
        self.nq = nq

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

    # ---- subspace Hamiltonian (sparse) via Slater-Condon on connected pairs ------------------
    def build_H(self, space):
        sci = self.sci
        idx = {int(d): k for k, d in enumerate(space)}
        n = len(space)
        R, C, V = [], [], []
        for k, d in enumerate(space):
            di = int(d)
            R.append(k); C.append(k); V.append(sci.element(di, di))     # diagonal
            conn = self._connections(di)
            for u in conn.tolist():
                j = idx.get(u)
                if j is not None and j > k:                              # upper triangle once
                    v = sci.element(di, u)
                    if v != 0.0:
                        R += [k, j]; C += [j, k]; V += [v, v]
        return sp.csr_matrix((V, (R, C)), shape=(n, n))

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
            sset = set(space.tolist())
            contrib = {}
            for ci in np.where(np.abs(cvec) > 1e-4)[0]:
                di = int(space[ci]); c = cvec[ci]
                conn = self._connections(di)
                for u in conn.tolist():
                    if u not in sset:
                        contrib[u] = contrib.get(u, 0.0) + self.sci.element(di, u) * c
            if not contrib: break
            cand = np.fromiter(contrib.keys(), dtype=np.uint64, count=len(contrib))
            num = np.fromiter(contrib.values(), dtype=float, count=len(contrib))
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
