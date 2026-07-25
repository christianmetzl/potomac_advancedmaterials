"""CANDIDATE-RANKING at CAS(10,10) — RANKING CLAIM WITHDRAWN (kept for provenance).

*** WITHDRAWN / SUPERSEDED ***: the two-candidate CrO-vs-NiO *ranking* this script computes at CAS(10,10)
is NOT robust. An active-space robustness check (src/candidate_decision_larger_cas.py ->
results/candidate_decision_larger_cas.json) shows the multireference ranking INVERTS to NiO>CrO at
CAS(12,12) and CAS(14,14) (CrO's CAS(10,10) high-spin gap was unconverged). We therefore DO NOT claim the
"synthesize CrO / B3LYP advances the wrong candidate" ranking. What SURVIVES is that CASCI/QSCI give CrO's experimentally-correct quintet
(⁵Π) ground state. NOTE: an earlier 'B3LYP alone gives the wrong sign' claim was ALSO withdrawn (an SCF
artifact; with lowest-solution SCF every functional gives the correct sign — see src/dft_baseline.py).
This script + evidence are retained only as the CAS(10,10) provenance behind that withdrawn claim.

--- original description (context for the withdrawn ranking) ---
CANDIDATE-RANKING DECISION: where a DFT-only screen advances the WRONG candidate and the
multireference (CASCI / QSCI) treatment picks the right one.

Two real transition-metal-oxide centers are ranked by their HIGH-SPIN PREFERENCE — the spin-gap
    gap = E(low-spin) - E(high-spin)  [eV];  gap > 0  =>  high-spin state is the ground state,
i.e. how robustly each is a high-spin (paramagnetic) center. A materials screen that wants the
strongest high-spin center must rank the candidates by this gap.

    Candidate A : CrO   high-spin = quintet (5-Pi, S=2) vs low-spin = triplet     [exp. ground: X 5-Pi]
    Candidate B : NiO   high-spin = triplet (3-Sigma-, S=1) vs low-spin = singlet [exp. ground: X 3-Sigma-]

FROZEN DECISION RULE (stated before the multireference numbers are computed):
    (1) compute each candidate's gap by 6 DFT functionals (committed dft_functional_spread_evidence.json)
        and by CASCI + QSCI in a fixed CAS(10,10)=20q active space;
    (2) rank the two candidates by gap under each method;
    (3) the multireference (CASCI/QSCI) ranking is the trusted answer (it agrees, by construction, with
        the experimental ground terms via the gap SIGN);
    (4) flag any DFT functional whose ranking INVERTS the multireference ranking — that functional, used
        alone to screen, would advance the wrong candidate.
Reported AS-MEASURED. HONEST SCOPE: CAS(10,10)/def2-SVP is a fixed modest active space. (The ranking below
is WITHDRAWN — see the banner above; only the single-molecule CrO quintet-ground SIGN is defensible/claimed,
and it is robust to active-space size.)
EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, json, time
import numpy as np
from pyscf import gto, scf, mcscf, ao2mo
from openfermion import InteractionOperator, get_fermion_operator, jordan_wigner
from openfermion.chem.molecular_data import spinorb_from_spatial
import scipy.sparse as sp, scipy.sparse.linalg as sla

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
HA2EV = 27.211386245988
NCAS = 10
_PC = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)
def parity(x): b = x.view(np.uint8).reshape(-1, 8); return (_PC[b].sum(1) & 1).astype(np.int8)

# candidate : atom, R, {highspin:(spin,nelecas), lowspin:(spin,nelecas)}, experimental ground term
CANDIDATES = {
    "CrO": dict(atom="Cr 0 0 0; O 0 0 1.621", exp="X 5-Pi (quintet, S=2)",
                highspin=dict(spin=4, nelecas=(7, 3)), lowspin=dict(spin=2, nelecas=(6, 4))),
    "NiO": dict(atom="Ni 0 0 0; O 0 0 1.627", exp="X 3-Sigma- (triplet, S=1)",
                highspin=dict(spin=2, nelecas=(6, 4)), lowspin=dict(spin=0, nelecas=(5, 5))),
}


def qsci_energy(qop_terms, nelecas, e_ref, tcap=40.0):
    """Selected-CI (QSCI principle) on the active-space qubit Hamiltonian; energy closest to e_ref."""
    XM = []; ZYM = []; PH = []
    for pauli, coeff in qop_terms.items():
        xm = zym = nY = 0
        for q, op in pauli:
            if op in ("X", "Y"): xm |= (1 << q)
            if op in ("Z", "Y"): zym |= (1 << q)
            if op == "Y": nY += 1
        XM.append(xm); ZYM.append(zym); PH.append(complex(coeff) * (1j) ** nY)
    XM = np.array(XM, dtype=np.uint64); ZYM = np.array(ZYM, dtype=np.uint64); PH = np.array(PH, dtype=np.complex128)
    def Hon(c): cc_ = np.uint64(c); return np.bitwise_xor(cc_, XM), PH * (1 - 2 * parity(np.bitwise_and(cc_, ZYM)))
    diagm = XM == 0; ZYMd = ZYM[diagm]; PHd = PH[diagm]
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
    space = np.array([hf], dtype=np.uint64); bestE = None; best = 1e9; t0 = time.time()
    for it in range(25):
        H = build_H(space)
        if H.shape[0] < 3: E = float(np.linalg.eigvalsh(H.toarray())[0]); c = np.array([1.0])
        else: w, v = sla.eigsh(H, k=1, which="SA"); E = float(w[0]); c = v[:, 0]
        if abs(E - e_ref) * 1000 < best: best = abs(E - e_ref) * 1000; bestE = E
        if best < 0.3 or len(space) >= 5000 or time.time() - t0 > tcap: break
        cvec = np.abs(np.asarray(c).ravel()); sig = np.where(cvec > 1e-4)[0]; sc = np.sort(space); contrib = {}
        for ci in sig:
            nc, amp = Hon(int(space[ci])); pos = np.clip(np.searchsorted(sc, nc), 0, len(space) - 1); ins = sc[pos] == nc
            for u, a in zip(nc[~ins].tolist(), (amp[~ins] * np.asarray(c).ravel()[ci]).tolist()): contrib[u] = contrib.get(u, 0) + a
        cand = np.array(list(contrib.keys()), dtype=np.uint64); num = np.array(list(contrib.values()))
        dv = diagv(cand); den = E - dv; den[np.abs(den) < 1e-9] = -1e-9
        space = np.concatenate([space, cand[np.argsort(np.abs(num) ** 2 / np.abs(den))[::-1][:400]]])
    return bestE, best


def state_energies(atom, spin, nelecas):
    mol = gto.M(atom=atom, basis="def2-svp", spin=spin, charge=0, verbose=0)
    mf = scf.ROHF(mol); mf.max_cycle = 300; mf.conv_tol = 1e-9; mf.kernel()
    mc = mcscf.CASCI(mf, NCAS, nelecas); mc.verbose = 0
    e_casci = float(mc.kernel()[0])
    h1e, ecore = mc.get_h1eff(); h2e = ao2mo.restore(1, mc.get_h2eff(), NCAS)
    one_so, two_so = spinorb_from_spatial(h1e, np.asarray(h2e.transpose(0, 2, 3, 1), order="C"))
    qop = jordan_wigner(get_fermion_operator(InteractionOperator(ecore, one_so, 0.5 * two_so)))
    e_qsci, err = qsci_energy(qop.terms, nelecas, e_casci)
    return e_casci, e_qsci, err


def main():
    dft = json.load(open(os.path.join(_RES, "dft_functional_spread_evidence.json")))["systems"]
    gaps = {"CASCI": {}, "QSCI": {}}
    for name, cfg in CANDIDATES.items():
        hc, hq, he = state_energies(cfg["atom"], cfg["highspin"]["spin"], cfg["highspin"]["nelecas"])
        lc, lq, le = state_energies(cfg["atom"], cfg["lowspin"]["spin"], cfg["lowspin"]["nelecas"])
        gaps["CASCI"][name] = round((lc - hc) * HA2EV, 3)      # E(low-spin) - E(high-spin)
        gaps["QSCI"][name] = round((lq - hq) * HA2EV, 3)
        print(f"{name}: CASCI gap={gaps['CASCI'][name]:+.3f} eV  QSCI gap={gaps['QSCI'][name]:+.3f} eV "
              f"(QSCI err hi/lo {he:.2f}/{le:.2f} mHa)", flush=True)

    A, B = "CrO", "NiO"
    methods = {**{f: {A: dft[A]["gaps_eV"][f], B: dft[B]["gaps_eV"][f]} for f in dft[A]["gaps_eV"]},
               "CASCI (this work)": gaps["CASCI"], "QSCI (this work)": gaps["QSCI"]}
    ref_rank = A if gaps["QSCI"][A] > gaps["QSCI"][B] else B     # multireference truth = which is the stronger high-spin center
    rows, inverted = [], []
    for m, g in methods.items():
        pick = A if g[A] > g[B] else B
        inv = (pick != ref_rank) and (m not in ("CASCI (this work)", "QSCI (this work)"))
        rows.append({"method": m, f"{A}_gap_eV": g[A], f"{B}_gap_eV": g[B],
                     "ranks_higher": pick, "inverts_multireference": bool(inv)})
        if inv: inverted.append(m)

    out = {
        "RANKING_STATUS": "WITHDRAWN — NOT ROBUST TO ACTIVE SPACE. The CAS(10,10) ranking below inverts to "
                          "NiO>CrO at CAS(12,12)/(14,14) (see candidate_decision_larger_cas.json); the "
                          "'synthesize CrO / B3LYP advances the wrong candidate' claim is retracted. Only the "
                          "single-molecule CrO quintet-ground SIGN (robust across CAS(10-14); cro_spin_gap.py) "
                          "is claimed. This file is retained as CAS(10,10) provenance for the withdrawn ranking.",
        "decision_at_cas10_10_WITHDRAWN": "Rank two metal-oxide centers by HIGH-SPIN PREFERENCE (spin-gap "
                    "E(low)-E(high) [eV]) — computed here at CAS(10,10) but NOT a claimed result (see RANKING_STATUS).",
        "candidates": {A: CANDIDATES[A]["exp"], B: CANDIDATES[B]["exp"]},
        "active_space": "CAS(10,10) = 20 qubits, def2-SVP, per spin state (ROHF -> CASCI; QSCI selected-CI)",
        "gap_definition": "E(low-spin) - E(high-spin) [eV]; > 0 => high-spin ground; larger => stronger high-spin center",
        "multireference_ranking_cas10_WITHDRAWN": f"{A} > {B}" if ref_rank == A else f"{B} > {A}",
        "cas_robustness": "CrO gap +1.89 (CAS10) -> +0.85 (CAS12) -> +0.88 (CAS14) eV; NiO ~1.6 -> ranking inverts to NiO>CrO. See candidate_decision_larger_cas.json.",
        "decision_table": rows,
        "functionals_that_inverted_at_cas10": inverted,
        "surviving_robust_claim": (f"{A} is quintet(⁵Π)-ground (gap > 0) at CAS(10/12/14), matching its experimental X 5-Pi "
                        f"term. The two-candidate RANKING is withdrawn (not robust). NOTE: the DFT gaps in this file "
                        f"are the ORIGINAL single-guess SCF values and are SUPERSEDED by the lowest-solution values in "
                        f"dft_functional_spread_evidence.json (B3LYP CrO = +0.835 eV, correct sign); the 'B3LYP inverts' "
                        f"reading below is an SCF artifact and is withdrawn."),
        "honest_caveats": [
            "RANKING WITHDRAWN: not robust to active-space size (inverts by CAS(12,12)); do not cite CrO>NiO.",
            "CAS(10,10)/def2-SVP is a fixed modest active space; CASCI on per-state ROHF orbitals (not state-averaged CASSCF).",
            "DFT gaps are the committed dft_functional_spread_evidence.json values; CASCI/QSCI computed here.",
            "What survives is the CAS-robust single-molecule CrO sign, not a candidate ranking."],
    }
    fn = os.path.join(_RES, "candidate_decision_evidence.json")
    json.dump(out, open(fn, "w"), indent=2)
    print("\n*** RANKING WITHDRAWN (not robust to active space; inverts by CAS(12,12)) ***")
    print(f"CAS(10,10) computed CrO/NiO gaps (provenance only, NOT a claim): ranking={ref_rank}>other, inverted-functionals={inverted or 'none'}")
    print("Surviving robust claim: single-molecule CrO quintet-ground sign (see candidate_decision_larger_cas.json)")
    print("saved", os.path.relpath(fn))


if __name__ == "__main__":
    main()
