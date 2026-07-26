"""Figure for the WE-SNC industrial worked example: the Sn-C homolysis ligand decision (Me vs n-Bu).

Left/middle: the two homolysis curves — exact-in-CAS CASSCF reference, the in-CAS CCSD(T) screen, and
the selected-CI/QSCI trust gate. Right: the decision view — per-point CCSD(T) error vs the decision
margin |BDE(Me)-BDE(Bu)|. Reads committed evidence only; no numbers are hard-coded.
Output: results/we_snc_homolysis.png.  EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def main():
    ev = json.load(open(os.path.join(_RES, "we_snc_homolysis_evidence.json")))
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.3), gridspec_kw={"width_ratios": [1, 1, 0.9]})
    names = {"me": "CH$_3$–Sn(OH)$_3$", "bu": "n-C$_4$H$_9$–Sn(OH)$_3$"}
    for ax, a in zip(axes[:2], ("me", "bu")):
        pts = ev["curves"][a]["points"]
        R = [p["R_SnC_ang"] for p in pts]
        e0 = pts[0]["E_casscf_Ha"]
        cas = [(p["E_casscf_Ha"] - e0) * 1000 for p in pts]
        cc = [(p["E_ccsdt_incas_Ha"] - e0) * 1000 if p["E_ccsdt_incas_Ha"] is not None else np.nan for p in pts]
        ax.plot(R, cas, "o-", color="#2F855A", lw=2.2, ms=7, zorder=4, label="exact in CAS (CASSCF CI)")
        ax.plot(R, cc, "s--", color="#C53030", lw=1.8, ms=7, zorder=3, label="in-CAS CCSD(T) — the screen")
        for p, x, y in zip(pts, R, cc):
            if p["E_ccsdt_incas_Ha"] is not None and not p["ccsdt_converged"]:
                ax.plot([x], [y], "s", mfc="none", mec="#C53030", ms=13, mew=1.8, zorder=5)
        sel = [p["selci_err_mHa"] for p in pts]
        ax.plot(R, [c + s for c, s in zip(cas, sel)], "^", color="#2B6CB0", ms=6, zorder=5,
                label=f"QSCI gate (max err {max(sel):.2f} mHa)")
        ax.set_title(f"{names[a]} — Sn–C homolysis", fontsize=10.5)
        ax.set_xlabel("R(Sn–C)  [Å]", fontsize=9.6)
        ax.set_ylabel("E − E(eq)  [mHa]", fontsize=9.6)
        ax.legend(fontsize=8.2, loc="lower right", framealpha=0.95)
        ax.grid(True, alpha=0.25)

    ax = axes[2]
    margin = ev["decision_margin_mHa"]
    labels, errs, colors = [], [], []
    for a in ("me", "bu"):
        for p in ev["curves"][a]["points"]:
            if p["ccsdt_err_mHa"] is None: continue
            labels.append(f"{a} {p['R_SnC_ang']:.2f}")
            errs.append(abs(p["ccsdt_err_mHa"]))
            colors.append("#C53030" if abs(p["ccsdt_err_mHa"]) > margin else "#718096")
    xs = np.arange(len(errs))
    ax.bar(xs, errs, color=colors, width=0.72)
    ax.axhline(margin, color="#1A365D", lw=2.0, ls="--")
    ax.text(0.02, margin * 1.07, f"decision margin |ΔBDE| = {margin:.1f} mHa",
            transform=ax.get_yaxis_transform(), fontsize=8.6, color="#1A365D", fontweight="bold")
    ax.set_yscale("log")
    ax.set_xticks(xs); ax.set_xticklabels(labels, rotation=70, fontsize=6.8)
    ax.set_ylabel("|in-CAS CCSD(T) error|  [mHa, log]", fontsize=9.2)
    ax.set_title("Screen error vs the decision margin\n(red = error exceeds the margin)", fontsize=9.6)
    ax.grid(True, alpha=0.25, axis="y")

    fig.suptitle("The worked industrial decision: which alkyl ligand — run through the trust gate, "
                 "exact-in-CAS verifiable", fontsize=10.6, y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(_RES, "we_snc_homolysis.png")
    fig.savefig(out, dpi=160)
    print("wrote", os.path.relpath(out))


if __name__ == "__main__":
    main()
