"""Slater-Condon determinant-subspace Hamiltonian from MO integrals — scalable QSCI to 48q+.

Building the full Jordan-Wigner Pauli operator is the bottleneck past ~40 qubits (term count ~ N^4).
But QSCI only needs matrix elements <det_I|H|det_J> within a small selected subspace, which Slater-Condon
rules compute directly from the 1- and 2-electron MO integrals — no Pauli operator, so this scales to
any qubit count (cost set by the subspace size, not 2^N or the operator length).

Spin-orbital convention matches OpenFermion/our determinants: spin-orbital p -> spatial p//2, spin p%2
(interleaved). Validated against the JW-based qsci_energy on H6/H10 (see _selftest()).

EIGENNEXUS - GIC 2026 Phase 3.
"""
import numpy as np


def hchain_integrals(n_atoms, R=0.74):
    """MO 1e/2e integrals (chemist (pq|rs)) + nuclear repulsion for a linear Hn chain, STO-6G RHF."""
    from pyscf import gto, scf, ao2mo
    mol = gto.M(atom="; ".join(f"H 0 0 {i*R:.4f}" for i in range(n_atoms)),
                basis="sto-6g", spin=n_atoms % 2, verbose=0)
    mf = scf.RHF(mol).run(conv_tol=1e-10)
    C = mf.mo_coeff; n = C.shape[1]
    h1 = C.T @ mf.get_hcore() @ C
    eri = ao2mo.restore(1, ao2mo.kernel(mol, C), n)        # (pq|rs) chemist, MO basis
    return dict(h1=h1, eri=eri, ecore=float(mol.energy_nuc()), n_orb=n,
                ne=mol.nelectron, e_hf=float(mf.e_tot))


def _occ(det):
    o = []
    d = int(det); i = 0
    while d:
        if d & 1:
            o.append(i)
        d >>= 1; i += 1
    return o


def _phase_single(occI, p, q):
    """Phase for moving electron p->q given common ordered occupation. Count occupied between them."""
    lo, hi = (p, q) if p < q else (q, p)
    c = sum(1 for x in occI if lo < x < hi)
    return -1.0 if (c & 1) else 1.0


class SCI:
    """Spin-orbital Slater-Condon engine over spatial integrals (interleaved spin-orbitals)."""
    def __init__(self, h1, eri, ecore):
        self.h1 = h1; self.eri = eri; self.ec = ecore

    def h(self, p, q):                                     # <p|h|q>, spin-orbital
        return self.h1[p // 2, q // 2] if (p & 1) == (q & 1) else 0.0

    def phys(self, p, q, r, s):                            # <pq|rs> physicist = (pr|qs) chemist, spin-checked
        if (p & 1) != (r & 1) or (q & 1) != (s & 1):
            return 0.0
        return self.eri[p // 2, r // 2, q // 2, s // 2]

    def aphys(self, p, q, r, s):                           # antisymmetrized <pq||rs>
        return self.phys(p, q, r, s) - self.phys(p, q, s, r)

    def diag(self, occ):
        e = self.ec + sum(self.h(i, i) for i in occ)
        for a in range(len(occ)):
            for b in range(a + 1, len(occ)):
                e += self.aphys(occ[a], occ[b], occ[a], occ[b])
        return e

    def element(self, dI, dJ):
        if dI == dJ:
            return self.diag(_occ(dI))
        oI, oJ = set(_occ(dI)), set(_occ(dJ))
        onlyI = sorted(oI - oJ); onlyJ = sorted(oJ - oI)
        if len(onlyI) == 1:                                # single excitation p(in I)->q(in J)
            p, q = onlyI[0], onlyJ[0]
            common = sorted(oI & oJ)
            val = self.h(p, q) + sum(self.aphys(p, m, q, m) for m in common)
            return val * _phase_single(sorted(oI), p, q)
        if len(onlyI) == 2:                                # double excitation pq -> rs
            p, q = onlyI; r, s = onlyJ
            val = self.aphys(p, q, r, s)
            # phase: product of the two single-move phases on the ordered lists
            ph = _phase_double(sorted(oI), sorted(oJ), p, q, r, s)
            return val * ph
        return 0.0


def _phase_double(occI, occJ, p, q, r, s):
    """Phase for a double excitation, via the standard ordered-list sign convention."""
    # positions in each determinant's sorted occupation
    def sign_remove(occ, x):
        idx = occ.index(x)
        return (-1.0 if (idx & 1) else 1.0), occ[:idx] + occ[idx + 1:]
    s1, oI1 = sign_remove(occI, p)
    s2, oI2 = sign_remove(oI1, q)
    s3, oJ1 = sign_remove(occJ, r)
    s4, oJ2 = sign_remove(oJ1, s)
    return s1 * s2 * s3 * s4


def sci_energy(h1, eri, ecore, dets, k_eig=1):
    """Lowest eigenvalue of H in the determinant subspace (Slater-Condon)."""
    import scipy.sparse as sp, scipy.sparse.linalg as sla
    eng = SCI(h1, eri, ecore)
    S = list(dict.fromkeys(int(d) for d in dets))         # unique, order-preserving
    n = len(S)
    H = np.zeros((n, n))
    for i in range(n):
        H[i, i] = eng.element(S[i], S[i])
        for j in range(i + 1, n):
            v = eng.element(S[i], S[j]); H[i, j] = v; H[j, i] = v
    if n < 50:
        return float(np.linalg.eigvalsh(H)[0]), n
    return float(sla.eigsh(sp.csr_matrix(H), k=k_eig, which="SA")[0][0]), n


def _selftest():
    """Validate Slater-Condon vs JW-based qsci_energy on H6/H10 random determinant subspaces."""
    import numpy as np, sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import scaling_transfer as st
    from qsci_score import qsci_energy
    for n_atoms in (6, 10):
        rec = st.hchain_ham(n_atoms); integ = hchain_integrals(n_atoms)
        ne, nq = rec["ne"], rec["nq"]; tokens = st.canonical_tokens(6, 12)
        pool, valid = st.build_realized_pool(tokens, ne, nq); vids = np.where(valid)[0]
        rng = np.random.default_rng(0); hf = st._hf_int(ne); dets = [np.uint64(hf)]
        for _ in range(60):
            tok = pool[int(rng.choice(vids))]; d = hf
            for w in tok[1]:
                d ^= (1 << w)
            dets.append(np.uint64(d))
        dets = np.array(dets, dtype=np.uint64)
        e_jw, _ = qsci_energy(rec["qop"], dets)
        e_sc, _ = sci_energy(integ["h1"], integ["eri"], integ["ecore"], dets)
        print(f"H{n_atoms} {nq}q: JW={e_jw:.6f}  Slater-Condon={e_sc:.6f}  diff={abs(e_jw-e_sc)*1000:.4f} mHa")


if __name__ == "__main__":
    _selftest()
