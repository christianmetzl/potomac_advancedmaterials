"""Quantum-vs-classical crossover: the two classical walls our approach removes, derived ENTIRELY
from already-measured data (no new claims, a synthesis).

Wall 1 (memory): exact statevector needs 2^n complex128 = 2^n x 16 B. The MPS tier needs only
  ~n x chi^2 x d x 16 B, using the MEASURED bond dimension chi-for-chemical-accuracy
  (chi = 50/100/400 at 20/28/40q, from mps_bonddim_evidence.json).
Wall 2 (determinants): full CI (Sz=0) dimension grows ~2.0x/qubit; the QSCI selected-determinant
  count for chemical accuracy grows ~1.38x/qubit (scaling_law_evidence.json; measured at 8-28q,
  projected at 40q). Diagonalizing the selected subspace replaces diagonalizing full CI.

All inputs are committed measured/fitted results; this script only joins and plots them. Measured
points are solid; the 40q QSCI-determinant point is the fitted projection (open marker), and the 40q
statevector/FCI-dimension points are analytic (2^n / FCI Sz=0 formula). Nothing here is a new claim.

EIGENNEXUS - GIC 2026 Phase 3.  Run: python src/crossover_study.py
"""
import os, json, math, numpy as np
from scipy.special import comb

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
GPU_MEM = 80 * 1024**3          # single 80 GB GPU
BYTES = 16                       # complex128
D = 2                            # qubit physical dimension


def fci_sz0_dim(q):
    """Dimension of the Sz=0 full-CI space for an n-qubit (n/2-spatial, half-filled) H-chain."""
    nso = q; norb = q // 2; nalpha = norb // 2  # half filling, Sz=0
    return int(comb(norb, nalpha, exact=True) ** 2)


def main():
    mps = json.load(open(os.path.join(_RES, "mps_bonddim_evidence.json")))
    chi_meas = {s["qubits"]: s["chi_for_chem_acc"] for s in mps["study_A_error_vs_chi"]}   # {20:50,28:100,40:400}
    qsci = json.load(open(os.path.join(_RES, "qsci_scaling_evidence.json")))
    sel_meas = {r["qubits"]: r["dets_for_chem_acc"] for r in qsci["results"]
                if isinstance(r["dets_for_chem_acc"], int)}                                  # 8..28q measured
    sl = json.load(open(os.path.join(_RES, "encoder", "scaling_law_evidence.json")))
    sel_proj_40 = sl["extrapolated_dets_for_chem_acc"]["40"]                                 # projected at 40q

    qs = list(range(8, 41, 2))
    sv_mem = {q: (2 ** q) * BYTES for q in qs}
    mps_mem = {q: q * (chi ** 2) * D * BYTES for q, chi in chi_meas.items()}
    fci_dim = {q: fci_sz0_dim(q) for q in qs}

    # key crossover numbers at 40q
    sv40 = sv_mem[40]; mps40 = mps_mem[40]
    out = {
        "title": "Quantum-vs-classical crossover (synthesis of measured data; no new claims)",
        "wall1_memory": {
            "exact_statevector_bytes": {str(q): sv_mem[q] for q in qs},
            "mps_bytes_from_measured_chi": {str(q): mps_mem[q] for q in chi_meas},
            "measured_chi": {str(k): v for k, v in chi_meas.items()},
            "at_40q": {
                "statevector": f"{sv40/1024**4:.1f} TB",
                "mps_measured_chi400": f"{mps40/1024**2:.0f} MB",
                "reduction_x": round(sv40 / mps40, 0),
                "fits_single_80GB_GPU": mps40 < GPU_MEM,
            },
        },
        "wall2_determinants": {
            "fci_sz0_dimension": {str(q): fci_dim[q] for q in (8, 12, 20, 28, 40)},
            "qsci_selected_measured": {str(k): v for k, v in sel_meas.items()},
            "qsci_selected_projected_40q": sel_proj_40,
            "fci_growth_per_qubit": 2.0,
            "qsci_growth_per_qubit": sl["fit"]["selected_growth_per_qubit"],
            "at_40q": {
                "fci_dim": fci_dim[40],
                "qsci_selected_projected": sel_proj_40,
                "fraction_pct": round(100 * sel_proj_40 / fci_dim[40], 6),
            },
        },
        "honest_caveats": [
            "Pure synthesis of committed results; statevector/FCI-dim are analytic (2^n / Sz=0 formula), "
            "MPS memory uses MEASURED chi (block2), QSCI-selected dets are measured at 8-28q and the 1.38x/"
            "qubit-fit PROJECTION at 40q (not yet reached on CPU).",
            "Memory model n*chi^2*d is the leading-order MPS tensor cost; real overhead is larger but the "
            "exponential-vs-polynomial separation is the point, not the constant.",
            "This shows where the classical walls are removed; it is NOT a head-to-head wall-clock win "
            "(the at-scale GPU run that would measure that is still owed)."],
    }
    json.dump(out, open(os.path.join(_RES, "crossover_evidence.json"), "w"), indent=2)
    print(f"40q memory: statevector {sv40/1024**4:.1f} TB  vs  MPS(chi=400) {mps40/1024**2:.0f} MB "
          f"({sv40/mps40:.0f}x, fits 80GB GPU={mps40<GPU_MEM})", flush=True)
    print(f"40q determinants: FCI Sz0 {fci_dim[40]:.3e}  vs  QSCI selected (proj) {sel_proj_40:.3e} "
          f"({100*sel_proj_40/fci_dim[40]:.4f}% of CI)", flush=True)

    # ---- figure ----
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(8.4, 3.3))
    # Panel A: memory
    axA.plot(qs, [sv_mem[q] for q in qs], "-", color="#c0392b", lw=1.6, label="exact statevector (2ⁿ·16 B)")
    axA.plot(list(chi_meas), [mps_mem[q] for q in chi_meas], "-o", color="#1f6fb2", lw=1.6, ms=6,
             label="MPS, measured χ (n·χ²·d)")
    axA.axhline(GPU_MEM, ls=":", color="#1f9d55", lw=1.4)
    axA.text(8, GPU_MEM*1.3, "single 80 GB GPU", fontsize=7, color="#1f9d55")
    axA.annotate(f"{sv40/1024**4:.0f} TB", (40, sv40), fontsize=7, color="#c0392b", ha="right", va="bottom")
    axA.annotate(f"{mps40/1024**2:.0f} MB", (40, mps40), fontsize=7, color="#1f6fb2", ha="right", va="top")
    axA.set_yscale("log"); axA.set_xlabel("qubits", fontsize=9); axA.set_ylabel("memory (bytes)", fontsize=9)
    axA.set_title("Wall 1: memory — MPS (measured χ) vs statevector", fontsize=8.5)
    axA.legend(fontsize=6.8, loc="upper left"); axA.tick_params(labelsize=8)
    # Panel B: determinants
    fq = [8, 12, 20, 28, 40]
    axB.plot(fq, [fci_dim[q] for q in fq], "-s", color="#c0392b", lw=1.6, ms=5, label="full CI (Sz=0) dimension")
    sm_q = sorted(sel_meas); axB.plot(sm_q, [sel_meas[q] for q in sm_q], "-o", color="#1f6fb2", lw=1.6, ms=5,
             label="QSCI selected dets (measured)")
    axB.plot([40], [sel_proj_40], "o", mfc="white", mec="#1f6fb2", mew=1.6, ms=7, label="QSCI selected (projected 40q)")
    axB.set_yscale("log"); axB.set_xlabel("qubits", fontsize=9); axB.set_ylabel("dimension / # determinants", fontsize=9)
    axB.set_title("Wall 2: determinants — QSCI selection vs full CI", fontsize=8.5)
    axB.legend(fontsize=6.8, loc="upper left"); axB.tick_params(labelsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(_RES, "crossover.png"), dpi=200)
    print("saved results/crossover_evidence.json + results/crossover.png", flush=True)


if __name__ == "__main__":
    main()
