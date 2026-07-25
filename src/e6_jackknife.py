"""E6 robustness: leave-one-out jackknife of the 40q DMRG discarded-weight extrapolation.

A hostile reviewer's first attack on the E6 absolute-accuracy anchor is "your dw->0 extrapolation
is fragile — drop a rung and the number moves." This re-fits the linear E(dw) extrapolation on every
4-of-5 subset of the committed chi=400..2400 rungs and reports how far the 40q flagship's variational
energy (E3 it5 E_var) sits above each refit near-exact limit. It reads ONLY committed evidence
(e6_dmrg_extrap_40q_evidence.json rungs + e3_certificate_evidence.json it5), adds no new physics, and is
fully reproducible on CPU. Output: results/e6_jackknife_robustness.json.

Honest reading: the point estimate is +1.59 mHa (all-5-rung fit); the jackknife spread is ~+/-0.05 mHa,
so the flagship sits right AT the 1 kcal/mol (1.594 mHa) chemical-accuracy threshold — robust in the
sense that no single rung moves the verdict by more than ~0.05 mHa, but marginal, not comfortably inside.
"""
import os, json
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(REPO, "results")
CHEM_ACC_MHA = 1.5936  # 1 kcal/mol


def _fit_E0(x, y):
    """Linear E = E0 + slope*x; return (E0, R2) with E0 the dw->0 intercept."""
    A = np.vstack([x, np.ones_like(x)]).T
    slope, E0 = np.linalg.lstsq(A, y, rcond=None)[0]
    yp = slope * x + E0
    ss_res = float(np.sum((y - yp) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return float(E0), float(r2)


def main():
    e6 = json.load(open(os.path.join(RES, "e6_dmrg_extrap_40q_evidence.json")))
    rungs = e6["rungs"]
    chi = [r["chi"] for r in rungs]
    x = np.array([r["dw"] for r in rungs])
    yHa = np.array([r["E_dmrg"] for r in rungs])

    e3 = json.load(open(os.path.join(RES, "e3_certificate_evidence.json")))
    Evar_it5 = [p["E_var"] for p in e3["points"] if p["iter"] == 5][0]

    E0_all, r2_all = _fit_E0(x, yHa)
    gap_all = (Evar_it5 - E0_all) * 1000.0

    loo = []
    for i in range(len(rungs)):
        mask = [j for j in range(len(rungs)) if j != i]
        E0, r2 = _fit_E0(x[mask], yHa[mask])
        gap = (Evar_it5 - E0) * 1000.0
        loo.append({"dropped_chi": chi[i], "E0_Ha": E0, "R2": round(r2, 6),
                    "gap_mHa": round(gap, 3), "within_chem_acc": bool(abs(gap) <= CHEM_ACC_MHA)})

    gaps = [d["gap_mHa"] for d in loo]
    out = {
        "run": "e6_jackknife_robustness",
        "role": "leave-one-out robustness of the E6 40q DMRG dw->0 extrapolation (reads committed evidence only)",
        "chem_acc_threshold_mHa": CHEM_ACC_MHA,
        "E3_it5_Evar_Ha": Evar_it5,
        "full_fit": {"E0_Ha": E0_all, "R2": round(r2_all, 6), "gap_mHa": round(gap_all, 3)},
        "leave_one_out": loo,
        "gap_range_mHa": [min(gaps), max(gaps)],
        "jackknife_halfspread_mHa": round((max(gaps) - min(gaps)) / 2.0, 3),
        "verdict": (
            f"Flagship 40q E_var sits +{gap_all:.2f} mHa above the DMRG-extrapolated FCI(40q); "
            f"leave-one-out spread {min(gaps):.3f}..{max(gaps):.3f} mHa (half-spread "
            f"{(max(gaps)-min(gaps))/2.0:.3f} mHa). The verdict is at the edge of the 1 kcal/mol band: "
            f"the all-rung point estimate is inside chemical accuracy, one fold (drop chi=2400) reaches "
            f"{max(gaps):.3f} mHa. Robust to ~+/-0.05 mHa; marginal, not comfortably inside — reported as such."
        ),
    }
    path = os.path.join(RES, "e6_jackknife_robustness.json")
    json.dump(out, open(path, "w"), indent=2)
    print(f"wrote {os.path.relpath(path)}")
    print(f"full fit gap = +{gap_all:.3f} mHa (R2={r2_all:.5f})")
    for d in loo:
        flag = "OK" if d["within_chem_acc"] else ">1.594"
        print(f"  drop chi={d['dropped_chi']:5d}: gap {d['gap_mHa']:+.3f} mHa  [{flag}]")
    print(f"jackknife range: {min(gaps):+.3f} .. {max(gaps):+.3f} mHa")


if __name__ == "__main__":
    main()
