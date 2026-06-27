"""DFT functional-dependence baseline on open-shell transition-metal oxides.

Hardens the Phase 3 §1 motivation ("DFT's 0.3-0.5 eV functional-dependent errors make candidate
rankings unreliable") with real numbers. For open-shell TM oxides the spin-state splitting is the
textbook functional-sensitive quantity: we compute the low-/high-spin gap of CrO and NiO with several
density functionals and report the SPREAD across functionals (the functional-choice uncertainty).
A single quantum/multireference method gives one value; DFT gives a 0.3-0.5+ eV-wide band.

Run:  python src/dft_baseline.py
Writes results/dft_functional_spread_evidence.json.

EIGENNEXUS - GIC 2026 Phase 3.
"""
import json, os, numpy as np
from pyscf import gto, dft

HA2EV = 27.211386245988
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNCTIONALS = ["PBE", "BP86", "TPSS", "B3LYP", "PBE0", "TPSSh"]

# (atom, metal basis, O basis, bond length A, [(label, multiplicity), ...]); first multiplicity = expected GS
SYSTEMS = {
    "CrO": dict(atoms=lambda R: f"Cr 0 0 0; O 0 0 {R}", R=1.621, basis="def2-svp",
                spins=[("quintet", 5), ("triplet", 3)]),
    "NiO": dict(atoms=lambda R: f"Ni 0 0 0; O 0 0 {R}", R=1.627, basis="def2-svp",
                spins=[("triplet", 3), ("singlet", 1)]),
}


def uks_energy(atom, basis, mult, xc):
    spin = mult - 1                                   # number of unpaired electrons (2S)
    mol = gto.M(atom=atom, basis=basis, spin=spin, charge=0, verbose=0)
    mf = dft.UKS(mol); mf.xc = xc
    mf = mf.density_fit()                             # RI for speed/robustness
    mf.conv_tol = 1e-8; mf.max_cycle = 200
    e = mf.kernel()
    return float(e) if mf.converged else None


def main():
    out = {"title": "DFT functional-dependence: spin-state splitting of open-shell TM oxides",
           "note": "Gap = E(low-spin) - E(high-spin), eV. Spread across functionals = functional-choice "
                   "uncertainty, the error a single quantum/multireference number removes.",
           "functionals": FUNCTIONALS, "systems": {}}
    for name, spec in SYSTEMS.items():
        atom = spec["atoms"](spec["R"]); (hs_lbl, hs_m), (ls_lbl, ls_m) = spec["spins"]
        print(f"=== {name} ({hs_lbl} m={hs_m} vs {ls_lbl} m={ls_m}) ===", flush=True)
        gaps = {}
        for xc in FUNCTIONALS:
            e_hs = uks_energy(atom, spec["basis"], hs_m, xc)
            e_ls = uks_energy(atom, spec["basis"], ls_m, xc)
            if e_hs is None or e_ls is None:
                print(f"  {xc:7s}: SCF not converged (skipped)", flush=True); continue
            gap = (e_ls - e_hs) * HA2EV
            gaps[xc] = round(gap, 3)
            print(f"  {xc:7s}: gap({ls_lbl}-{hs_lbl}) = {gap:+.3f} eV", flush=True)
        if gaps:
            vals = np.array(list(gaps.values()))
            spread = float(vals.max() - vals.min())
            out["systems"][name] = dict(gap_def=f"E({ls_lbl})-E({hs_lbl})", gaps_eV=gaps,
                                        spread_eV=round(spread, 3), n_functionals=len(gaps))
            print(f"  -> functional spread = {spread:.3f} eV across {len(gaps)} functionals\n", flush=True)
        json.dump(out, open(os.path.join(_REPO, "results", "dft_functional_spread_evidence.json"), "w"), indent=2)
    spreads = [v["spread_eV"] for v in out["systems"].values()]
    if spreads:
        print(f"SUMMARY: spin-gap functional spread {min(spreads):.2f}-{max(spreads):.2f} eV "
              f"(motivates quantum accuracy; cf. chemical accuracy 1.6 mHa = 0.044 eV)", flush=True)
    print("saved results/dft_functional_spread_evidence.json", flush=True)


if __name__ == "__main__":
    main()
