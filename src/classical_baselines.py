"""Classical baselines on the H-chain scaling ladder, with wall-clock.

Phase 3 Top-Action #2: every quantum result needs a matched non-quantum baseline on the SAME
instance. Our primary scaling vehicle is the linear Hn chain (STO-6G, Jordan-Wigner, 2n qubits),
on which the quantum QSCI/GQE numbers are reported. This computes the classical ladder on the
identical geometries -- HF, MP2, CCSD, CCSD(T), and FCI where tractable -- and TIMES each, so the
write-up can place a timed classical cell beside every quantum cell and show where exact classical
simulation becomes the bottleneck.

Geometry: Hn linear, uniform spacing R (default 0.74 Angstrom), STO-6G, RHF reference. The FCI
energies are cross-checked against our committed references (results/qsci_scaling_evidence.json,
dmrg_evidence.json) to confirm identical instances.

Run:  python src/classical_baselines.py            # default ladder n=2..12
      python src/classical_baselines.py 2 4 6 10    # explicit n list
Writes results/classical_baselines_evidence.json.

EIGENNEXUS - GIC 2026 Phase 3.
"""
import sys, os, time, json, numpy as np
from pyscf import gto, scf, mp, cc, fci

R_DEFAULT = 0.74
# committed FCI references (Ha), keyed by NUMBER OF H ATOMS, to confirm identical instances
REF_FCI = {4: -2.156857, 6: -3.170505, 8: -4.186089, 10: -5.202826, 14: -7.237790, 20: -10.292650}
# qubit count = 2 * number of H atoms; chain length = n_atoms
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def hchain(n_atoms, R=R_DEFAULT):
    atoms = "; ".join(f"H 0 0 {i*R:.4f}" for i in range(n_atoms))
    mol = gto.M(atom=atoms, basis="sto-6g", spin=n_atoms % 2, charge=0, verbose=0)
    return mol


def timed(fn):
    t0 = time.time(); val = fn(); return val, time.time() - t0


def run_one(n_atoms, R=R_DEFAULT, do_fci=True):
    nq = 2 * n_atoms
    mol = hchain(n_atoms, R)
    rec = {"system": f"H{n_atoms}", "qubits": nq, "n_atoms": n_atoms, "R": R}

    mf = scf.RHF(mol)
    (e_hf), t_hf = timed(lambda: mf.kernel())
    rec["HF"] = {"E": float(e_hf), "s": round(t_hf, 3)}

    (pt), t_mp2 = timed(lambda: mp.MP2(mf).kernel())
    rec["MP2"] = {"E": float(e_hf + pt[0]), "s": round(t_mp2, 3)}

    ccsd = cc.CCSD(mf)
    (_), t_cc = timed(lambda: ccsd.kernel())
    e_ccsd = float(ccsd.e_tot)
    (et), t_t = timed(lambda: ccsd.ccsd_t())
    rec["CCSD"] = {"E": e_ccsd, "s": round(t_cc, 3)}
    rec["CCSD(T)"] = {"E": float(e_ccsd + et), "s": round(t_cc + t_t, 3)}

    if do_fci:
        cisolver = fci.FCI(mf)
        (efci), t_fci = timed(lambda: cisolver.kernel()[0])
        rec["FCI"] = {"E": float(efci), "s": round(t_fci, 3)}
        ref = REF_FCI.get(n_atoms)
        rec["FCI_ref_match"] = (None if ref is None
                                else {"ref": ref, "diff_mHa": round(abs(efci - ref) * 1000, 4)})
    # errors vs FCI (or CCSD(T) if FCI absent) in mHa
    base = rec.get("FCI", {}).get("E", rec["CCSD(T)"]["E"])
    rec["err_vs_ref_mHa"] = {m: round(abs(rec[m]["E"] - base) * 1000, 3)
                             for m in ["HF", "MP2", "CCSD", "CCSD(T)"] + (["FCI"] if "FCI" in rec else [])}
    return rec


def main():
    ns = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [2, 4, 6, 8, 10, 12]
    out = {"title": "Classical baselines on Hn chains (STO-6G, R=0.74), timed",
           "note": "Matched-instance non-quantum baselines for the quantum QSCI/GQE ladder. "
                   "FCI cross-checked against committed references where available.",
           "R": R_DEFAULT, "results": []}
    for na in ns:
        do_fci = na <= 12        # full FCI tractable to ~12 H (24q); beyond, CCSD(T) is the ref
        print(f"=== H{na} ({2*na}q) FCI={'yes' if do_fci else 'no'} ===", flush=True)
        rec = run_one(na, do_fci=do_fci)
        m = rec.get("FCI_ref_match")
        print(f"  HF {rec['HF']['E']:.6f} ({rec['HF']['s']}s) | "
              f"CCSD(T) {rec['CCSD(T)']['E']:.6f} ({rec['CCSD(T)']['s']}s)"
              + (f" | FCI {rec['FCI']['E']:.6f} ({rec['FCI']['s']}s)"
                 + (f" [ref Δ={m['diff_mHa']} mHa]" if m else "") if 'FCI' in rec else ""), flush=True)
        out["results"].append(rec)
        json.dump(out, open(os.path.join(_REPO, "results", "classical_baselines_evidence.json"), "w"), indent=2)
    print("saved results/classical_baselines_evidence.json", flush=True)


if __name__ == "__main__":
    main()
