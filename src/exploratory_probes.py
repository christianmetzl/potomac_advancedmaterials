"""EXPLORATORY probes (NOT pre-registered; no pass/fail committed; indicative only).

(1) x2c scalar-relativistic single-points: how much does spin-free X2C shift the CrO
    quintet-triplet and VO quartet-doublet CASCI gaps, at the committed geometries/CAS?
    -> results/x2c_exploratory.json
(2) AVAS overlap check of the committed CrO CAS(10,10) window: does an automated
    atomic-valence active-space selector reproduce ~10 orbitals / ~10 electrons of
    Cr 3d/4s + O 2p character? -> results/avas_check_exploratory.json

HONEST caveat baked into the outputs: def2-SVP is a non-relativistically contracted basis,
so the X2C shift here is indicative of the *sign/scale* of scalar-relativistic effects, not a
quantitative correction (that needs an x2c/ANO-RCC-type basis). AVAS thresholds are heuristic.
EIGENNEXUS - GIC 2026 Phase 3, exploratory addendum.
"""
import os, json, time
import numpy as np
from pyscf import gto, scf, mcscf

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
HA2EV = 27.211386245988

# committed setups (SCF recipe matched EXACTLY per source: cro_spin_gap.py uses plain ROHF with NO
# level_shift; blind_holdout_vo.py uses level_shift=0.3 + retry). Using the wrong SCF recipe steers
# open-shell TM ROHF to a different orbital solution and changes the CAS reference -> wrong gap.
CRO = dict(atom="Cr 0 0 0; O 0 0 1.621", basis="def2-svp", ncas=10, level_shift=0.0, retry=False,
           states={"quintet": dict(spin=4, nelecas=(7, 3)),
                   "triplet": dict(spin=2, nelecas=(6, 4))},
           gap="E(triplet)-E(quintet)", exp_ground="quintet (X 5-Pi)")
VO = dict(atom="V 0 0 0; O 0 0 1.589", basis="def2-svp", ncas=10, level_shift=0.3, retry=True,
          states={"quartet": dict(spin=3, nelecas=(7, 4)),
                  "doublet": dict(spin=1, nelecas=(6, 5))},
          gap="E(doublet)-E(quartet)", exp_ground="quartet (X 4-Sigma-)")


def _casci_energy(atom, basis, spin, ncas, nelecas, scalar_rel, level_shift=0.0, retry=False):
    mol = gto.M(atom=atom, basis=basis, spin=spin, charge=0, verbose=0)
    mf = scf.ROHF(mol)
    if scalar_rel:
        mf = mf.sfx2c1e()                     # spin-free (scalar) X2C one-electron
    mf.level_shift = level_shift; mf.max_cycle = 300; mf.conv_tol = 1e-9; mf.kernel()
    if retry and not mf.converged:
        mf.level_shift = 0.0; mf.init_guess = "atom"; mf.kernel()
    mc = mcscf.CASCI(mf, ncas, nelecas); mc.verbose = 0
    e = float(mc.kernel()[0])
    return e, bool(mf.converged)


def x2c_gaps():
    out = {"probe": "x2c scalar-relativistic (sfx2c1e) single-points — EXPLORATORY, not pre-registered",
           "method": "per-state ROHF (+/- sfx2c1e) -> CASCI in the committed CAS; gap in eV",
           "honest_caveat": "def2-SVP is non-relativistically contracted; the X2C shift is indicative "
                            "of sign/scale only, NOT a quantitative relativistic correction (needs an "
                            "x2c/ANO-RCC basis). No threshold or claim is attached.",
           "systems": {}}
    for name, S in [("CrO", CRO), ("VO", VO)]:
        rec = {"active_space": f"CAS({sum(next(iter(S['states'].values()))['nelecas'])},{S['ncas']})",
               "gap_definition_eV": S["gap"], "experimental_ground": S["exp_ground"], "states": {}}
        E = {"nonrel": {}, "x2c": {}}
        for st, spec in S["states"].items():
            e0, c0 = _casci_energy(S["atom"], S["basis"], spec["spin"], S["ncas"], spec["nelecas"], False,
                                   S["level_shift"], S["retry"])
            e1, c1 = _casci_energy(S["atom"], S["basis"], spec["spin"], S["ncas"], spec["nelecas"], True,
                                   S["level_shift"], S["retry"])
            E["nonrel"][st] = e0; E["x2c"][st] = e1
            rec["states"][st] = dict(CASCI_nonrel_Ha=round(e0, 6), CASCI_x2c_Ha=round(e1, 6),
                                     x2c_shift_mHa=round((e1 - e0) * 1000, 3),
                                     rohf_converged=bool(c0 and c1))
        (hi, lo) = list(S["states"].keys())[::-1]      # gap = E(second listed) - E(first listed)
        first, second = list(S["states"].keys())
        gap0 = (E["nonrel"][second] - E["nonrel"][first]) * HA2EV
        gap1 = (E["x2c"][second] - E["x2c"][first]) * HA2EV
        rec.update(gap_nonrel_eV=round(gap0, 4), gap_x2c_eV=round(gap1, 4),
                   gap_shift_meV=round((gap1 - gap0) * 1000, 2),
                   ground_state_nonrel=first if gap0 > 0 else second,
                   ground_state_x2c=first if gap1 > 0 else second,
                   ordering_flips_under_x2c=bool((gap0 > 0) != (gap1 > 0)))
        out["systems"][name] = rec
        print(f"{name}: gap nonrel={gap0:+.4f} eV  x2c={gap1:+.4f} eV  shift={{:+.1f}} meV".format((gap1-gap0)*1000), flush=True)
    return out


def avas_check():
    from pyscf.mcscf import avas
    mol = gto.M(atom=CRO["atom"], basis=CRO["basis"], spin=CRO["states"]["quintet"]["spin"],
                charge=0, verbose=0)
    mf = scf.ROHF(mol); mf.level_shift = CRO["level_shift"]; mf.max_cycle = 300  # committed CrO recipe
    mf.conv_tol = 1e-9; mf.kernel()
    ao_labels = ["Cr 3d", "Cr 4s", "O 2p"]     # target valence window for CrO
    out = {"probe": "AVAS overlap check of the committed CrO CAS(10,10) window — EXPLORATORY",
           "system": "CrO quintet, R=1.621, def2-SVP", "committed_window": "CAS(10,10) = 20 qubits",
           "avas_target_ao_labels": ao_labels, "rohf_converged": bool(mf.converged),
           "honest_caveat": "AVAS thresholds are heuristic; this checks whether an automated valence "
                            "selector lands near the hand-picked CAS(10,10), not a pass/fail claim.",
           "avas_by_threshold": []}
    for thr in (0.1, 0.2, 0.5):
        try:
            ncas, nelecas, _ = avas.avas(mf, ao_labels, threshold=thr, canonicalize=False, verbose=0)
            out["avas_by_threshold"].append(dict(threshold=thr, avas_ncas=int(ncas),
                                                 avas_nelecas=int(nelecas),
                                                 matches_committed_ncas=bool(int(ncas) == 10)))
            print(f"AVAS thr={thr}: ncas={ncas} nelecas={nelecas}", flush=True)
        except Exception as e:
            out["avas_by_threshold"].append(dict(threshold=thr, error=str(e)))
            print(f"AVAS thr={thr}: ERROR {e}", flush=True)
    near = [r for r in out["avas_by_threshold"] if r.get("avas_ncas") == 10]
    out["interpretation"] = ("At least one AVAS threshold reproduces ncas=10 (the committed window)."
                             if near else
                             "No tested AVAS threshold gives exactly ncas=10; nearest values reported. "
                             "The committed CAS(10,10) is a deliberate Cr 3d/4s + O 2p choice; AVAS "
                             "granularity differs by threshold — indicative overlap, not a mismatch verdict.")
    return out


def main():
    t0 = time.time()
    xo = x2c_gaps()
    json.dump(xo, open(os.path.join(_RES, "x2c_exploratory.json"), "w"), indent=2)
    print("wrote results/x2c_exploratory.json", flush=True)
    ao = avas_check()
    json.dump(ao, open(os.path.join(_RES, "avas_check_exploratory.json"), "w"), indent=2)
    print(f"wrote results/avas_check_exploratory.json  [total {time.time()-t0:.0f}s]", flush=True)


if __name__ == "__main__":
    main()
