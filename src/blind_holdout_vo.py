"""BLIND ONE-SHOT HOLDOUT: VO (vanadium monoxide) — pre-registered, frozen, run once, reported as-is.

Purpose: answer the strongest attack available against any benchmark suite — "your results are good
because you iterated until they were." This script was FROZEN and its SHA-256 committed in
results/preregistration_v1.json BEFORE it was ever executed. It is run exactly once; the outcome is
committed unedited, pass or fail.

System: VO, a transition-metal oxide never touched anywhere in this repository. Experimental ground
term: X 4-Sigma- (quartet). Method identical to the committed CrO pipeline: per-state ROHF ->
CASCI(11,10) [nelecas quartet (7,4), doublet (6,5)] in def2-SVP -> QSCI (selected-CI) on the
active-space qubit Hamiltonian.

PRE-REGISTERED PREDICTIONS (results/preregistration_v1.json, entry H1):
  (a) QSCI reproduces CASCI to <= 1.6 mHa for BOTH spin states (solver claim).
  (b) CASCI/QSCI order the quartet BELOW the doublet, matching the experimental X 4-Sigma- ground
      term (chemistry claim -- the genuinely blind part: a modest CAS may get this wrong; if it does,
      that is the reported result).
Failure of (b) -- or SCF non-convergence -- is reported as-is; nothing is tuned after the first run.

EIGENNEXUS - GIC 2026 Phase 3.  Run once: python src/blind_holdout_vo.py
"""
import os, json, time, numpy as np
from pyscf import gto, scf, mcscf, ao2mo
from openfermion import InteractionOperator, get_fermion_operator, jordan_wigner
from openfermion.chem.molecular_data import spinorb_from_spatial
import scipy.sparse as sp, scipy.sparse.linalg as sla

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
_PC = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)
def parity(x): b = x.view(np.uint8).reshape(-1, 8); return (_PC[b].sum(1) & 1).astype(np.int8)

R = 1.589   # VO experimental re (Angstrom), NIST diatomic constants
NCAS = 10
STATES = {"quartet": dict(spin=3, nelecas=(7, 4)), "doublet": dict(spin=1, nelecas=(6, 5))}
HA2EV = 27.211386245988


def qsci_err(qop_terms, nelecas, e_ref, tcap=60.0):
    XM = []; ZYM = []; PH = []
    for pauli, coeff in qop_terms.items():
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
    na, nb = nelecas; hf = 0
    for i in range(na): hf |= (1 << (2 * i))
    for i in range(nb): hf |= (1 << (2 * i + 1))
    space = np.array([hf], dtype=np.uint64); best = 1e9; bestE = None; t0 = time.time()
    for it in range(25):
        H = build_H(space)
        if H.shape[0] < 6:
            w, v = np.linalg.eigh(H.toarray()); E = float(w[0]); c = np.asarray(v[:, 0]).ravel()
        else:
            w, v = sla.eigsh(H, k=1, which="SA"); E = float(w[0]); c = np.asarray(v[:, 0]).ravel()
        if abs(E - e_ref) * 1000 < best: best = abs(E - e_ref) * 1000; bestE = E
        if best < 0.3 or len(space) >= 6000 or time.time() - t0 > tcap: break
        cvec = np.abs(c); sig = np.where(cvec > 1e-4)[0]; sc = np.sort(space); contrib = {}
        for ci in sig:
            nc, amp = Hon(int(space[ci])); pos = np.clip(np.searchsorted(sc, nc), 0, len(space) - 1); ins = sc[pos] == nc
            for u, a in zip(nc[~ins].tolist(), (amp[~ins] * c[ci]).tolist()): contrib[u] = contrib.get(u, 0) + a
        if not contrib: break
        cand = np.array(list(contrib.keys()), dtype=np.uint64); num = np.array(list(contrib.values()))
        dv = diagv(cand); den = E - dv; den[np.abs(den) < 1e-9] = -1e-9
        space = np.concatenate([space, cand[np.argsort(np.abs(num) ** 2 / np.abs(den))[::-1][:400]]])
    return bestE, best


def main():
    t0 = time.time(); out = {"system": "VO (blind one-shot holdout)", "R_ang": R,
        "active_space": f"CAS(11,{NCAS}) = 20 qubits", "basis": "def2-SVP (all-electron)",
        "experimental_ground_term": "X 4-Sigma- (quartet)", "states": {}, "run_once": True}
    E = {}
    for st, spec in STATES.items():
        try:
            mol = gto.M(atom=f"V 0 0 0; O 0 0 {R}", basis="def2-svp", spin=spec["spin"], charge=0, verbose=0)
            mf = scf.ROHF(mol); mf.level_shift = 0.3; mf.max_cycle = 300; mf.conv_tol = 1e-9; mf.kernel()
            if not mf.converged:
                mf.level_shift = 0.0; mf.init_guess = "atom"; mf.kernel()
            mc = mcscf.CASCI(mf, NCAS, spec["nelecas"]); mc.verbose = 0
            e_casci = float(mc.kernel()[0])
            h1e, ecore = mc.get_h1eff(); h2e = ao2mo.restore(1, mc.get_h2eff(), NCAS)
            one_so, two_so = spinorb_from_spatial(h1e, np.asarray(h2e.transpose(0, 2, 3, 1), order="C"))
            qop = jordan_wigner(get_fermion_operator(InteractionOperator(ecore, one_so, 0.5 * two_so)))
            eq, err = qsci_err(qop.terms, spec["nelecas"], e_casci)
            E[st] = e_casci
            out["states"][st] = {"rohf_converged": bool(mf.converged), "CASCI_Ha": e_casci,
                                 "QSCI_Ha": eq, "qsci_err_mHa": round(err, 3),
                                 "prediction_a_solver_chemacc": bool(err <= 1.6)}
            print(f"{st}: ROHF conv={mf.converged}  CASCI={e_casci:.6f}  QSCI err={err:.3f} mHa", flush=True)
        except Exception as e:
            out["states"][st] = {"error": str(e)}
            print(f"{st}: FAILED — {e}", flush=True)
    if len(E) == 2:
        gap = (E["doublet"] - E["quartet"]) * HA2EV
        out["gap_doublet_minus_quartet_eV"] = round(gap, 3)
        out["predicted_ground_state"] = "quartet" if gap > 0 else "doublet"
        out["prediction_b_matches_experiment"] = bool(gap > 0)
        print(f"\ngap(doublet-quartet) = {gap:+.3f} eV -> ground state: {out['predicted_ground_state']} "
              f"(experiment: quartet X4Sigma-) -> prediction (b) {'HOLDS' if gap>0 else 'FAILS'}", flush=True)
    out["wall_s"] = round(time.time() - t0, 1)
    json.dump(out, open(os.path.join(_RES, "blind_holdout_vo_result.json"), "w"), indent=2)
    print("saved results/blind_holdout_vo_result.json (as-is, no tuning)", flush=True)


if __name__ == "__main__":
    main()
