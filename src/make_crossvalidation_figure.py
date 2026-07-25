"""Figure: two independent routes converge on the same 40-qubit exact energy.

Route B (this plot): selected-CI/QSCI E_var vs Epstein-Nesbet PT2, extrapolated to PT2 -> 0 (standard CIPSI).
Route A (horizontal band): the committed classical DMRG discarded-weight extrapolation (E6), an entirely
different method class and extrapolation variable. Reads committed evidence only.
Output: results/crossvalidation_40q.png.  EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def main():
    e3 = sorted(json.load(open(os.path.join(_RES, "e3_certificate_evidence.json")))["points"],
                key=lambda p: p["iter"])
    xv = json.load(open(os.path.join(_RES, "e3_cipsi_crossvalidation.json")))
    routeA = xv["routeA_classical_DMRG_discarded_weight"]["E_Ha"]
    routeA_unc = xv["routeA_classical_DMRG_discarded_weight"]["stated_uncertainty_mHa"] / 1000.0

    use = [p for p in e3 if p["iter"] >= 2]                      # linear regime (it0/it1 far from converged)
    x = np.array([-p["pt2_Ha"] * 1000 for p in use])             # |PT2| in mHa
    y = np.array([p["E_var"] for p in use])
    A = np.vstack([-x / 1000.0, np.ones_like(x)]).T
    slope, E0 = np.linalg.lstsq(A, y, rcond=None)[0]

    # plot RELATIVE to Route A so the agreement is read directly (0 = Route A)
    rel = (y - routeA) * 1000.0
    E0_rel = (E0 - routeA) * 1000.0
    fig, (ax, ins) = plt.subplots(1, 2, figsize=(9.6, 4.4), gridspec_kw={"width_ratios": [1.7, 1]})
    ax.axhspan(-routeA_unc * 1000, routeA_unc * 1000, color="#2B6CB0", alpha=0.20, zorder=1)
    ax.axhline(0, color="#2B6CB0", lw=2.2, zorder=2,
               label="Route A — classical DMRG, discarded weight → 0 (E6)")
    xs = np.linspace(0, x.max() * 1.08, 100)
    ax.plot(xs, (slope * (-xs / 1000.0) + E0 - routeA) * 1000.0, "--", color="#C05621", lw=1.7, zorder=3)
    ax.plot(x, rel, "o", color="#C05621", ms=9, zorder=4,
            label="Route B — selected-CI/QSCI, PT2 → 0 (E3 trace)")
    ax.plot([0], [E0_rel], "*", color="#C05621", ms=22, zorder=5)
    for p, xi, yi in zip(use, x, rel):
        ax.annotate(f"{p['dets']//1000}k dets", (xi, yi), textcoords="offset points",
                    xytext=(7, -13), fontsize=8, color="0.42")
    # every fit window, not just the favourable one — the honest claim is the WORST window
    wins = xv["agreement_routeB_minus_routeA_mHa"]
    worst_k = max(wins, key=lambda k: abs(wins[k]))
    ax.annotate("the two routes meet\n(right panel: by how much)", (0, E0_rel),
                textcoords="offset points", xytext=(26, 92), fontsize=9.2,
                color="#22543D", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#22543D", lw=1.1))
    ax.set_xlabel("|PT2| — distance from the converged limit  [mHa]   (← more determinants)", fontsize=9.6)
    ax.set_ylabel("energy relative to Route A  [mHa]", fontsize=9.6)
    ax.set_xlim(-0.2, x.max() * 1.08); ax.set_ylim(-0.55, rel.max() * 1.15)
    ax.set_title("Pinning the 40-qubit exact energy twice, independently", fontsize=10.5)
    ax.legend(fontsize=8.4, loc="upper left", framealpha=0.95)
    ax.grid(True, alpha=0.25)

    # right panel: the intercept at true scale — EVERY fit window, plus Route A's own jackknife spread
    jk = json.load(open(os.path.join(_RES, "e6_jackknife_robustness.json")))["jackknife_halfspread_mHa"]
    ins.axhspan(-jk, jk, color="#2B6CB0", alpha=0.20)
    ins.axhline(0, color="#2B6CB0", lw=1.8)
    ks = list(wins)
    ins.plot(range(len(ks)), [wins[k] for k in ks], "o", color="#C05621", ms=9)
    for i, k in enumerate(ks):
        ins.annotate(f"{wins[k]:+.3f}", (i, wins[k]), textcoords="offset points",
                     xytext=(0, 11), ha="center", fontsize=8.4,
                     color="#7B341E", fontweight="bold")
    ins.annotate(f"worst window: {wins[worst_k]:+.3f} mHa\n→ ~{1.5936/abs(wins[worst_k]):.0f}× inside chemical accuracy",
                 (1.0, -0.099), ha="center", fontsize=8.0, color="#22543D", fontweight="bold")
    ins.set_xticks(range(len(ks))); ins.set_xticklabels(ks, fontsize=8.0)
    ins.set_xlim(-0.5, len(ks) - 0.5); ins.set_ylim(-0.118, 0.075)
    ins.tick_params(axis="y", labelsize=8.0)
    ins.set_ylabel("Route B − Route A  [mHa]", fontsize=8.8)
    ins.set_title(f"EVERY Route-B fit window (none omitted)\nblue band = Route A jackknife ±{jk} mHa",
                  fontsize=8.6, pad=4)
    ins.grid(True, alpha=0.25)
    fig.suptitle("Two method classes, two extrapolation variables, no shared code path — same answer",
                 fontsize=9.4, y=0.985, color="0.30")
    fig.tight_layout(rect=[0, 0, 1, 0.965])
    out = os.path.join(_RES, "crossvalidation_40q.png")
    fig.savefig(out, dpi=160)
    print(f"wrote {os.path.relpath(out)}  |  RouteA={routeA:.9f}  RouteB(it2-it5)={E0:.9f}  Δ={(E0-routeA)*1000:+.4f} mHa")


if __name__ == "__main__":
    main()
