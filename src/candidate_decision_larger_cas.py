"""ROBUSTNESS of the CrO>NiO candidate ranking to ACTIVE-SPACE SIZE (answers the hostile chemist:
'does the wrong-candidate flip survive a bigger CAS, or is it a CAS(10,10) artifact?').

Re-runs the multireference (CASCI) spin-gap ranking at CAS(10,10)/CAS(12,12)/CAS(14,14) — each step adds
2 active orbitals + 2 active electrons (one alpha, one beta), holding the spin (na-nb) fixed. For each
active space we check the DECISION-LEVEL claims, not a benchmark magnitude:
    (a) both gaps > 0  (high-spin ground state — agrees with the experimental X terms), and
    (b) CrO gap > NiO gap  (CrO is the stronger high-spin center -> synthesize CrO; the ranking B3LYP inverts).

CASCI only (the multireference reference); def2-SVP; per-state ROHF -> CASCI, same recipe as the committed
CAS(10,10) run. Reported AS-MEASURED. Output: results/candidate_decision_larger_cas.json.
EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, json, time
import numpy as np
from pyscf import gto, scf, mcscf

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
HA2EV = 27.211386245988

# base CAS(10,10) config (identical to candidate_decision.py); grow by (+1 alpha,+1 beta) per +2 orbitals
CANDIDATES = {
    "CrO": dict(atom="Cr 0 0 0; O 0 0 1.621", exp="X 5-Pi (quintet, S=2)",
                highspin=dict(spin=4, nelecas=(7, 3)), lowspin=dict(spin=2, nelecas=(6, 4))),
    "NiO": dict(atom="Ni 0 0 0; O 0 0 1.627", exp="X 3-Sigma- (triplet, S=1)",
                highspin=dict(spin=2, nelecas=(6, 4)), lowspin=dict(spin=0, nelecas=(5, 5))),
}


def casci_energy(atom, spin, base_nelecas, ncas):
    add = (ncas - 10) // 2   # orbitals added on each side of base
    na, nb = base_nelecas[0] + add, base_nelecas[1] + add
    mol = gto.M(atom=atom, basis="def2-svp", spin=spin, charge=0, verbose=0)
    mf = scf.ROHF(mol); mf.max_cycle = 400; mf.conv_tol = 1e-9; mf.kernel()
    mc = mcscf.CASCI(mf, ncas, (na, nb)); mc.verbose = 0
    e = float(mc.kernel()[0])
    return e, (na, nb), bool(mf.converged)


def main():
    t0 = time.time()
    ladder = [10, 12, 14]
    results = {"CrO": {}, "NiO": {}}
    per_cas = []
    for ncas in ladder:
        row = {"ncas": ncas, "qubits": 2 * ncas}
        for name, cfg in CANDIDATES.items():
            hc, hne, hconv = casci_energy(cfg["atom"], cfg["highspin"]["spin"], cfg["highspin"]["nelecas"], ncas)
            lc, lne, lconv = casci_energy(cfg["atom"], cfg["lowspin"]["spin"], cfg["lowspin"]["nelecas"], ncas)
            gap = (lc - hc) * HA2EV     # E(low) - E(high); >0 => high-spin ground
            results[name][ncas] = round(gap, 3)
            row[f"{name}_gap_eV"] = round(gap, 3)
            row[f"{name}_nelecas_hi"] = list(hne)
            row[f"{name}_scf_converged"] = hconv and lconv
            print(f"CAS({ncas},{ncas})={2*ncas}q  {name}: gap {gap:+.3f} eV  (hi nelecas {hne}, scf_conv {hconv and lconv})", flush=True)
        row["ranking"] = "CrO>NiO" if row["CrO_gap_eV"] > row["NiO_gap_eV"] else "NiO>CrO"
        row["both_high_spin_ground"] = bool(row["CrO_gap_eV"] > 0 and row["NiO_gap_eV"] > 0)
        row["pick_to_synthesize"] = "CrO" if row["CrO_gap_eV"] > row["NiO_gap_eV"] else "NiO"
        per_cas.append(row)

    ranking_holds = all(r["ranking"] == "CrO>NiO" for r in per_cas)
    signs_hold = all(r["both_high_spin_ground"] for r in per_cas)
    out = {
        "run": "candidate_decision_larger_cas",
        "question": "Does the CrO>NiO multireference ranking (and the high-spin-ground sign) survive a larger active space?",
        "method": "per-state ROHF -> CASCI, def2-SVP; CAS grown 10->12->14 orbitals (+1 alpha,+1 beta per step, spin fixed).",
        "per_cas": per_cas,
        "ranking_holds_all_cas": bool(ranking_holds),
        "high_spin_ground_sign_holds_all_cas": bool(signs_hold),
        "verdict": (
            f"CrO>NiO ranking {'HOLDS' if ranking_holds else 'DOES NOT hold'} and the high-spin-ground sign "
            f"{'holds' if signs_hold else 'does not hold'} across CAS(10,10)/12,12/14,14 "
            f"(20/24/28q). The decision-level claim (which candidate to synthesize, and that B3LYP inverts it) "
            f"is {'robust to active-space size' if ranking_holds and signs_hold else 'NOT robust — reported as-measured'}."),
        "honest_caveats": [
            "CASCI on per-state ROHF orbitals (not state-averaged CASSCF); def2-SVP fixed basis.",
            "Growing the CAS adds frontier orbitals around the Fermi level; not an orbital-optimized (CASSCF) space.",
            "The claim tested is the ranking SIGN / which-candidate, not a benchmark-quality gap magnitude.",
            "gap magnitudes shift with CAS size (expected); the decision (CrO>NiO, both high-spin ground) is the invariant checked."],
        "wall_s": round(time.time() - t0, 1),
    }
    fn = os.path.join(_RES, "candidate_decision_larger_cas.json")
    json.dump(out, open(fn, "w"), indent=2)
    print(f"\nranking holds across CAS sizes: {ranking_holds} | high-spin-ground sign holds: {signs_hold}")
    print("saved", os.path.relpath(fn), f"({out['wall_s']}s)")


if __name__ == "__main__":
    main()
