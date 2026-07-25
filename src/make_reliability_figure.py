"""Figure: the two axes on which a 'validated' classical reference silently fails.
Left  — correlation strength, measured against EXACT FCI at 20 qubits (ground truth).
Right — system size: the SAME chi=400 that is exact at 20q, lower-bounded at 40q.
Reads committed evidence only. Output: results/reference_reliability.png.
"""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CHEM = 1.5936
FLOOR = 1e-3   # log-axis floor; chi=400 at 20q is 0.0000-0.0002 mHa (below resolution)


def main():
    m = json.load(open(os.path.join(_RES, "reference_reliability.json")))
    a1 = m["axis1_correlation_strength"]["rows"]
    R = np.array([r["R_ang"] for r in a1])
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(10.6, 4.3))

    # ---- LEFT: correlation axis, ground truth ----
    cols = {"50": "#C53030", "100": "#DD6B20", "200": "#2B6CB0", "400": "#2F855A"}
    for chi in ("50", "100", "200", "400"):
        y = np.array([max(r["dmrg_trunc_err_vs_exact_FCI_mHa"].get(chi, 0.0) or 0.0, FLOOR) for r in a1])
        axL.plot(R, y, "o-", color=cols[chi], lw=1.8, ms=6, label=f"DMRG χ={chi}")
    axL.axhline(CHEM, color="0.35", ls="--", lw=1.3)
    axL.text(0.78, CHEM * 1.25, "chemical accuracy", fontsize=8.2, color="0.35")
    axL.set_yscale("log"); axL.set_ylim(FLOOR * 0.7, 300)
    axL.set_xlabel("H–H bond length R [Å]   (→ stronger correlation)", fontsize=9.5)
    axL.set_ylabel("DMRG truncation error vs EXACT FCI  [mHa]", fontsize=9.5)
    axL.set_title("Axis 1 — correlation strength (20 qubits, ground truth)", fontsize=10)
    axL.annotate("χ=100 looks converged here\n(0.009 mHa)", (0.74, 0.0087),
                 textcoords="offset points", xytext=(26, 34), fontsize=8.2, color="#DD6B20",
                 arrowprops=dict(arrowstyle="->", color="#DD6B20", lw=0.9))
    axL.annotate("…and is 17.5 mHa off here\n≈2000× growth, no warning", (2.5, 17.48),
                 textcoords="offset points", xytext=(-118, -34), fontsize=8.2, color="#DD6B20",
                 arrowprops=dict(arrowstyle="->", color="#DD6B20", lw=0.9))
    axL.legend(fontsize=8, loc="upper left", framealpha=0.95)
    axL.grid(True, alpha=0.25, which="both")

    # ---- RIGHT: system-size axis ----
    a2 = m["axis2_system_size"]["chi400_error_at_40q_lower_bound"]
    R2 = np.array([r["R_ang"] for r in a2])
    y40 = np.array([r["chi400_error_lower_bound_mHa"] for r in a2])
    y20 = np.array([max(m["axis2_system_size"]["chi400_error_at_20q_mHa"].get(str(r), 0.0) or 0.0, FLOOR) for r in R2])
    axR.plot(R2, y20, "s-", color="#2F855A", lw=1.8, ms=7, label="χ=400 at 20 qubits — exact (≤0.0002 mHa)")
    axR.plot(R2, y40, "D-", color="#C53030", lw=2.0, ms=7, label="χ=400 at 40 qubits — error ≥ this")
    axR.axhline(CHEM, color="0.35", ls="--", lw=1.3)
    axR.text(0.78, CHEM * 1.3, "chemical accuracy", fontsize=8.2, color="0.35")
    axR.set_yscale("log"); axR.set_ylim(FLOOR * 0.7, 300)
    axR.set_xlabel("H–H bond length R [Å]   (→ stronger correlation)", fontsize=9.5)
    axR.set_ylabel("error of the SAME χ=400  [mHa]", fontsize=9.5)
    axR.set_title("Axis 2 — system size (same χ, 20q vs 40q)", fontsize=10)
    axR.annotate("the bond dimension that was\nverified EXACT at 20q is\n≥177 mHa off at 40q",
                 (2.5, 177.4), textcoords="offset points", xytext=(-150, -62), fontsize=8.4,
                 color="#C53030", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="#C53030", lw=1.0))
    axR.legend(fontsize=8, loc="upper left", framealpha=0.95)
    axR.grid(True, alpha=0.25, which="both")

    fig.suptitle("When can you trust a classical reference? Two axes on which a 'validated' bond dimension silently fails",
                 fontsize=11, y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.955])
    out = os.path.join(_RES, "reference_reliability.png")
    fig.savefig(out, dpi=160)
    print("wrote", os.path.relpath(out))


if __name__ == "__main__":
    main()
