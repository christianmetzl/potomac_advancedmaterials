"""Engine-equivalence check: the fast incremental engine (qsci_fast) must match the original
PauliEngine.qsci AND exact FCI on H4/H6, both pure-seeded and CIPSI-grown.

This is the correctness gate that guarded the Option-C adoption (max deviation ~1e-11 mHa when
introduced); re-run here so judges can verify the engine the GPU/40q results rely on is exact.
Writes engine_equivalence_evidence.json for reproduce.py.

EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import qsci_lib as L


def mp2_seed(P, top_m=64):
    exc = L.mp2_excitation_lists(P["t2"], P["nocc"], P["nq"], top_m=top_m)
    hf = L.hf_det(P["ne"]); seed = {hf}
    for p, q, r, s in zip(exc["p"], exc["q"], exc["r"], exc["s"]):
        d = hf
        for o in (p, q): d &= ~(1 << o)
        for o in (r, s): d |= (1 << o)
        if bin(d).count("1") == P["ne"]:
            seed.add(d)
    return seed


def main():
    t0 = time.time()
    rows, max_dev, max_fci = [], 0.0, 0.0
    for na, gi, gpi in [(4, 15, 60), (6, 30, 150)]:
        P = L.hchain_problem(na, do_fci=True)
        eng = L.PauliEngine(P["qop"].terms)
        seed = mp2_seed(P)
        E0, s0 = eng.qsci(set(seed), grow_iters=gi, grow_per_iter=gpi, kcap=10**9)
        E1, s1 = eng.qsci_fast(set(seed), grow_iters=gi, grow_per_iter=gpi, kcap=10**9)
        dev = abs(E0 - E1) * 1e3
        fci_err = abs(E1 - P["e_fci"]) * 1e3
        max_dev = max(max_dev, dev); max_fci = max(max_fci, fci_err)
        rows.append(dict(system=f"H{na}", qubits=P["nq"], E_qsci=E0, E_qsci_fast=E1,
                         e_fci=P["e_fci"], engine_dev_mHa=dev, fci_err_mHa=round(fci_err, 6),
                         dets=int(len(s1)), dets_match=bool(len(s0) == len(s1))))
        print(f"H{na} ({P['nq']}q): qsci={E0:.9f} fast={E1:.9f} dev={dev:.2e} mHa "
              f"fci_err={fci_err:.4f} mHa", flush=True)
    out = dict(title="Engine equivalence: qsci_fast (incremental) vs original qsci vs exact FCI",
               results=rows, max_engine_dev_mHa=max_dev, max_fci_err_mHa=round(max_fci, 6),
               wall_s=round(time.time() - t0, 1))
    json.dump(out, open("engine_equivalence_evidence.json", "w"), indent=2)
    ok = max_dev < 1e-4 and max_fci < 1.6
    print(f"ENGINES {'EQUIVALENT' if ok else 'DIVERGENT'}: max dev {max_dev:.2e} mHa, "
          f"max FCI err {max_fci:.4f} mHa", flush=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
