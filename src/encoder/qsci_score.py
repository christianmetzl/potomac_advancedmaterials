"""Bit-packed QSCI energy engine (reused from sno_demo.py) for the final integrated
number: given determinants sampled from a generated state, build H in that subspace
and diagonalize. numpy 2.x has no np.bit_count -> byte-lookup popcount.

EIGENNEXUS - GIC 2026 Phase 3.
"""
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sla

_PC = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)


def _parity(x):
    b = x.view(np.uint8).reshape(-1, 8)
    return (_PC[b].sum(1) & 1).astype(np.int8)


def make_engine(qop):
    """Return Hon(det)->(connected dets, amplitudes) for the qubit operator qop."""
    XM = []; ZYM = []; PH = []
    for pauli, coeff in qop.terms.items():
        xm = zym = 0; nY = 0
        for q, o in pauli:
            if o in ("X", "Y"): xm |= (1 << q)
            if o in ("Z", "Y"): zym |= (1 << q)
            if o == "Y": nY += 1
        XM.append(xm); ZYM.append(zym); PH.append(complex(coeff) * (1j) ** nY)
    XM = np.array(XM, np.uint64); ZYM = np.array(ZYM, np.uint64); PH = np.array(PH, np.complex128)

    def Hon(c):
        cc = np.uint64(c)
        return np.bitwise_xor(cc, XM), PH * (1 - 2 * _parity(np.bitwise_and(cc, ZYM)))
    return Hon


def qsci_energy(qop, dets):
    """Lowest eigenvalue of H projected onto the (deduplicated) determinant subspace."""
    Hon = make_engine(qop)
    S = np.unique(np.asarray(dets, dtype=np.uint64))
    sc = np.sort(S); order = np.argsort(S); n = len(S)
    R, C, V = [], [], []
    for i, c in enumerate(S):
        nc, amp = Hon(int(c))
        pos = np.clip(np.searchsorted(sc, nc), 0, n - 1)
        v = sc[pos] == nc
        j = order[pos[v]]
        R.append(j); C.append(np.full(j.shape, i)); V.append(amp[v])
    H = sp.csr_matrix((np.concatenate(V), (np.concatenate(R), np.concatenate(C))),
                      shape=(n, n), dtype=complex)
    if n < 3:
        return float(np.linalg.eigvalsh(H.toarray())[0]), n
    return float(sla.eigsh(H, k=1, which="SA")[0][0]), n
