"""A REAL bridged tin-oxo fragment (Sn-O-Sn), not a diatomic — closing the "EUV motif" gap.

EUV photoresists are tin-oxo CLUSTERS (Sn-O-Sn bridged cages), but our executed Sn results so far are
SnO / linear O=Sn=O. This runs the smallest genuine bridged unit, the Sn2O2 rhombus (two Sn-O-Sn bridges),
through the same all-electron-ECP CASCI -> QSCI path, to show the pipeline reaches the real motif's
electronic structure, not just diatomics.

HONEST: this is a minimal cluster fragment, not the full footballene cage; def2-SVP + def2 ECP on Sn,
a fixed modest CAS. The claim is chemical accuracy of QSCI vs the CASCI reference on a genuine Sn-O-Sn
system. If it does not reach chemical accuracy, that is reported as-is (a harder multireference target).

EIGENNEXUS - GIC 2026 Phase 3.  Run: python src/tin_oxo_demo.py
"""
import os, json, time, numpy as np
from pyscf import gto, scf, mcscf, ao2mo
from openfermion import InteractionOperator, get_fermion_operator, jordan_wigner
from openfermion.chem.molecular_data import spinorb_from_spatial
import scipy.sparse as sp, scipy.sparse.linalg as sla

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
_PC = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)
def parity(x): b = x.view(np.uint8).reshape(-1, 8); return (_PC[b].sum(1) & 1).astype(np.int8)

NCAS, NELECAS = 8, 8       # CAS(8,8) -> 16 qubits

def main():
    t0 = time.time()
    # Sn2O2 rhombus: Sn on x-axis, O on y-axis; Sn-O ~2.05 A (Sn-Sn 3.0, O-O 2.8)
    mol = gto.M(atom="Sn 1.5 0 0; Sn -1.5 0 0; O 0 1.4 0; O 0 -1.4 0",
                basis={"Sn": "def2-svp", "O": "def2-svp"}, ecp={"Sn": "def2-svp"},
                spin=0, charge=0, verbose=0)
    mf = scf.RHF(mol); mf = mf.density_fit(); mf.level_shift = 0.3; mf.max_cycle = 300; mf.conv_tol = 1e-9
    mf.kernel()
    if not mf.converged:                       # retry from a cleaner guess without level shift
        mf.level_shift = 0.0; mf.init_guess = "atom"; mf.kernel()
    print(f"Sn2O2 rhombus: RHF={mf.e_tot:.6f} conv={mf.converged} | {mol.nao} orb, {mol.nelectron} e (Sn ECP) | {time.time()-t0:.0f}s", flush=True)

    mc = mcscf.CASCI(mf, NCAS, NELECAS); mc.verbose = 0
    e_fci = float(mc.kernel()[0])
    h1e, ecore = mc.get_h1eff(); h2e = ao2mo.restore(1, mc.get_h2eff(), NCAS)
    one_so, two_so = spinorb_from_spatial(h1e, np.asarray(h2e.transpose(0, 2, 3, 1), order="C"))
    qop = jordan_wigner(get_fermion_operator(InteractionOperator(ecore, one_so, 0.5 * two_so)))
    nq = 2 * NCAS
    print(f"Sn2O2 CAS({NELECAS},{NCAS}): {nq} qubits, {len(qop.terms)} Pauli terms, CASCI={e_fci:.6f}", flush=True)

    # QSCI (selected-CI) on the bridged tin-oxo Hamiltonian
    XM = []; ZYM = []; PH = []
    for pauli, coeff in qop.terms.items():
        xm = zym = nY = 0
        for q, op in pauli:
            if op in ("X", "Y"): xm |= (1 << q)
            if op in ("Z", "Y"): zym |= (1 << q)
            if op == "Y": nY += 1
        XM.append(xm); ZYM.append(zym); PH.append(complex(coeff) * (1j) ** nY)
    XM = np.array(XM, dtype=np.uint64); ZYM = np.array(ZYM, dtype=np.uint64); PH = np.array(PH, dtype=np.complex128)
    diagm = XM == 0; ZYMd = ZYM[diagm]; PHd = PH[diagm]
    def Hon(c): cc = np.uint64(c); return np.bitwise_xor(cc, XM), PH * (1 - 2 * parity(np.bitwise_and(cc, ZYM)))
    def diagv(cf):
        out = np.empty(len(cf))
        for i, c in enumerate(cf): out[i] = np.sum(PHd * (1 - 2 * parity(np.bitwise_and(np.uint64(int(c)), ZYMd)))).real
        return out
    def build_H(space):
        sc = np.sort(space); order = np.argsort(space); n = len(space); R_ = []; C = []; V = []
        for i, c in enumerate(space):
            nc, amp = Hon(int(c)); pos = np.clip(np.searchsorted(sc, nc), 0, n - 1); v = sc[pos] == nc
            j = order[pos[v]]; R_.append(j); C.append(np.full(j.shape, i)); V.append(amp[v])
        return sp.csr_matrix((np.concatenate(V), (np.concatenate(R_), np.concatenate(C))), shape=(n, n), dtype=complex)
    hf = (1 << NELECAS) - 1; space = np.array([hf], dtype=np.uint64); best = 1e9
    for it in range(12):
        H = build_H(space)
        E = float(np.linalg.eigvalsh(H.toarray())[0]) if H.shape[0] < 3 else float(sla.eigsh(H, k=1, which="SA")[0][0])
        if H.shape[0] >= 3:
            w, v = sla.eigsh(H, k=1, which="SA"); E = float(w[0]); c = np.asarray(v[:, 0]).ravel()
        else:
            c = np.array([1.0])
        best = min(best, abs(E - e_fci) * 1000)
        print(f"  |space|={len(space):4d} E={E:.6f} err={abs(E-e_fci)*1000:.3f} mHa", flush=True)
        if best < 0.5 or len(space) >= 4000 or time.time() - t0 > 240: break
        cvec = np.abs(c); sig = np.where(cvec > 1e-4)[0]; sc = np.sort(space); contrib = {}
        for ci in sig:
            nc, amp = Hon(int(space[ci])); pos = np.clip(np.searchsorted(sc, nc), 0, len(space) - 1); ins = sc[pos] == nc
            for u, a in zip(nc[~ins].tolist(), (amp[~ins] * c[ci]).tolist()): contrib[u] = contrib.get(u, 0) + a
        if not contrib: break
        cand = np.array(list(contrib.keys()), dtype=np.uint64); num = np.array(list(contrib.values()))
        dv = diagv(cand); den = E - dv; den[np.abs(den) < 1e-9] = -1e-9
        space = np.concatenate([space, cand[np.argsort(np.abs(num) ** 2 / np.abs(den))[::-1][:300]]])

    out = {"system": "Sn2O2 rhombus (bridged Sn-O-Sn tin-oxo fragment)", "qubits": nq,
           "active_space": f"CAS({NELECAS},{NCAS})", "basis": "def2-SVP + def2 ECP on Sn",
           "rhf_converged": bool(mf.converged), "n_pauli_terms": len(qop.terms),
           "CASCI_energy_Ha": e_fci, "qsci_best_err_mHa": round(best, 3),
           "reached_chemical_accuracy": bool(best <= 1.6),
           "note": "genuine bridged Sn-O-Sn unit (not a diatomic / not linear O=Sn=O); minimal cluster "
                   "fragment, not the full footballene cage. Honest scope: fixed modest CAS/basis.",
           "honest_caveats": [
               "Minimal Sn-O-Sn fragment, not the industrial tin-oxo cage; def2-SVP + ECP, fixed CAS(8,8).",
               "Claim is QSCI chemical accuracy vs the CASCI reference on a real bridged tin-oxo motif."]}
    json.dump(out, open(os.path.join(_RES, "tin_oxo_evidence.json"), "w"), indent=2)
    print(f"\nSn2O2 QSCI best error vs CASCI: {best:.3f} mHa ({nq}q) | chem-acc={best<=1.6} | total {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
