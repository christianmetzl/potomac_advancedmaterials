"""Determinant-count scaling law: quantify that QSCI cost grows far slower than the Hilbert space.

The scalability (primary) criterion is currently a table the reader must eyeball. This fits it. Using the
committed determinants-for-chemical-accuracy points (results/qsci_scaling_evidence.json):
    8q:27  12q:148  20q:2401  28q:18201,
we fit the determinant requirement vs qubit count and compare its growth to the exact spin-conserving FCI
space, then extrapolate the determinant budget at 40/48/56q. This is the numerical backbone of the
scaling claim. Honest: it is an empirical fit on 4 points (R^2 reported); the FCI fractions
(75%/37%/3.8%/0.15%) independently show the vanishing fraction.

Run: python src/encoder/scaling_law.py   Writes results/encoder/scaling_law_evidence.json + .png.
EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, json, numpy as np
from math import comb

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "results", "encoder")

# (qubits, n_atoms, dets_for_chem_acc) from qsci_scaling_evidence.json
PTS = [(8, 4, 27), (12, 6, 148), (20, 10, 2401), (28, 14, 18201)]


def fci_dim(n_atoms):
    """Spin-conserving (Sz=0) FCI determinant count for Hn / STO-6G: C(n, n/2)^2."""
    return comb(n_atoms, n_atoms // 2) ** 2


def main():
    q = np.array([p[0] for p in PTS], float)
    nd = np.array([p[2] for p in PTS], float)
    # exponential fit: ndets ~ A * exp(b*q)  -> log-linear
    b, logA = np.polyfit(q, np.log(nd), 1)
    A = np.exp(logA)
    pred = A * np.exp(b * q)
    ss_res = np.sum((np.log(nd) - np.log(pred)) ** 2)
    ss_tot = np.sum((np.log(nd) - np.log(nd).mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    eff_base = np.exp(b)                     # per-qubit growth factor of the SELECTED space
    extrap = {qq: int(A * np.exp(b * qq)) for qq in (40, 48, 56)}
    fci = {p[0]: fci_dim(p[1]) for p in PTS}
    frac = {p[0]: round(p[2] / fci_dim(p[1]) * 100, 3) for p in PTS}
    out = {
        "title": "QSCI determinant-count scaling law",
        "points_qubits_dets": [[p[0], p[2]] for p in PTS],
        "fit": {"form": "ndets ~ A*exp(b*qubits)", "A": round(float(A), 4), "b_per_qubit": round(float(b), 4),
                "selected_growth_per_qubit": round(float(eff_base), 3), "r2_logspace": round(float(r2), 4)},
        "fci_growth_per_qubit": 2.0,
        "interpretation": (f"The importance-selected determinant count grows ~{eff_base:.2f}x per qubit, "
                           f"vs 2.00x per qubit for the full Sz=0 FCI space — so the fraction of FCI space "
                           f"needed for chemical accuracy collapses with size."),
        "fci_fraction_pct": frac,
        "fci_dim": {str(k): v for k, v in fci.items()},
        "extrapolated_dets_for_chem_acc": extrap,
        "caveat": "Empirical fit on 4 points (log-space R^2 reported); extrapolation is indicative, not a "
                  "guarantee, and assumes the selected-CI/QSCI selection remains effective at larger size.",
    }
    json.dump(out, open(os.path.join(OUT, "scaling_law_evidence.json"), "w"), indent=2)
    print(f"selected-space growth {eff_base:.2f}x/qubit vs FCI 2.00x/qubit; log-R2={r2:.4f}", flush=True)
    print("FCI fraction:", frac, flush=True)
    print("extrapolated dets-for-chem-acc:", extrap, flush=True)
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        qq = np.array([8, 12, 20, 28, 40, 48, 56])
        fig, ax = plt.subplots(figsize=(7, 4.3))
        ax.plot(qq, [fci_dim({8:4,12:6,20:10,28:14,40:20,48:24,56:28}[int(x)]) for x in qq], "s--",
                color="tab:red", label="full FCI space (Sz=0) ~ 2$^{q}$")
        ax.plot(qq, A * np.exp(b * qq), "-", color="tab:blue", alpha=0.6, label=f"fit: selected dets (~{eff_base:.2f}$^q$)")
        ax.plot(q, nd, "o", color="tab:blue", ms=8, label="measured dets for chem. acc.")
        ax.set_yscale("log"); ax.set_xlabel("qubits"); ax.set_ylabel("determinants (log)")
        ax.set_title("QSCI selected-determinant count grows far slower than FCI")
        ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(OUT, "scaling_law.png"), dpi=130)
        print("saved scaling_law.png", flush=True)
    except Exception as e:
        print(f"(figure skipped: {e})", flush=True)


if __name__ == "__main__":
    main()
