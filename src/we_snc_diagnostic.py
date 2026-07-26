"""WE-SNC diagnostic — WHY the Me/Bu BDE comparison is withheld: natural-orbital occupations at stretch.

The frozen study (we_snc_homolysis.py) produced curves whose diagnostics disagree qualitatively at
R(Sn-C)=4.60 A: Me dominant-determinant weight 0.38 (diradical forming) vs Bu 0.76 (still near
single-reference), and in-CAS CCSD(T) agrees with the Bu CAS reference to ~0.14 mHa at every point —
i.e. the Bu active space appears NOT to contain the Sn-C homolysis physics at stretch. This script makes
that diagnosis quantitative: CASSCF(8,8) natural-orbital occupation numbers (NOONs) at R=4.60 for both
ligands. A genuine homolysis has a sigma/sigma* pair with occupations ~1/1; occupations near 2/0 mean the
active space rotated away from the breaking bond (a well-known CAS screening failure mode).
Output: results/we_snc_diagnostic.json.  EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from we_snc_homolysis import rsn_oh3, NCAS, NELECAS
from pyscf import gto, scf, mcscf
from pyscf.mcscf import avas

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def noons_at(R, alkyl):
    mol = gto.M(atom=rsn_oh3(R, alkyl), basis="def2-svp", ecp={"Sn": "def2-svp"},
                spin=0, charge=0, verbose=0)
    mf = scf.RHF(mol); mf.level_shift = 0.3; mf.max_cycle = 300; mf.conv_tol = 1e-9; mf.kernel()
    iC = [i for i in range(mol.natm) if mol.atom_symbol(i) == "C"][0]
    _, _, guess = avas.avas(mf, ["Sn 5p", f"{iC} C 2p"], threshold=0.2, canonicalize=True)
    mc = mcscf.CASSCF(mf, NCAS, NELECAS); mc.verbose = 0; mc.max_cycle_macro = 80
    mc.kernel(guess)
    # natural occupations of the active space from the CASCI 1-RDM
    casdm1 = mc.fcisolver.make_rdm1(mc.ci, NCAS, NELECAS)
    occ = np.sort(np.linalg.eigvalsh(casdm1))[::-1]
    return bool(mc.converged), [round(float(o), 3) for o in occ]


def main():
    out = {"diagnostic": "CASSCF(8,8) active-space natural-orbital occupations at R(Sn-C)=4.60 A",
           "question": ("is each curve a genuine homolysis at stretch (a sigma/sigma* pair ~1/1, "
                        "diradical) or did the active space rotate away from the breaking Sn-C bond?"),
           "points": {}}
    for alkyl in ("me", "bu"):
        conv, occ = noons_at(4.60, alkyl)
        frontier = [o for o in occ if 0.2 < o < 1.8]
        out["points"][alkyl] = {"casscf_converged": conv, "noons": occ,
                                "frontier_occupations_0.2-1.8": frontier,
                                "diradical_pair_present": bool(any(0.7 < o < 1.3 for o in occ))}
        print(f"{alkyl} R=4.60: conv={conv} NOONs={occ}")
    me_dir = out["points"]["me"]["diradical_pair_present"]
    bu_dir = out["points"]["bu"]["diradical_pair_present"]
    out["verdict"] = (
        f"Me diradical pair present: {me_dir}; Bu diradical pair present: {bu_dir}. " +
        ("The two CASSCF(8,8) solutions are QUALITATIVELY INEQUIVALENT at stretch: the Me active space "
         "contains the breaking sigma/sigma*(Sn-C) pair, the Bu active space does not (it rotated onto "
         "other orbitals). The frozen in-model BDE comparison (P-WE3) is therefore NOT chemically "
         "meaningful and the ligand ranking is WITHHELD — reported as the workflow catching a silent "
         "active-space inconsistency, exactly the class of error an unaudited CAS screen would ship."
         if me_dir != bu_dir else
         "Both solutions show the same qualitative character; the BDE comparison stands as-frozen."))
    fn = os.path.join(_RES, "we_snc_diagnostic.json")
    json.dump(out, open(fn, "w"), indent=1)
    print(out["verdict"]); print("saved", os.path.relpath(fn))


if __name__ == "__main__":
    main()
