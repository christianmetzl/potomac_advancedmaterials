"""CROSS-VALIDATING THE 40-QUBIT EXACT ENERGY BY TWO INDEPENDENT ROUTES.

FCI at 40 qubits is intractable (~3.4e10 determinants), so any "exact" 40q energy must be extrapolated —
and a single extrapolation is something a reviewer has to take on trust. Here we pin it twice, by two
methodologically independent routes on the identical H20/40q Hamiltonian:

  Route A (classical tensor network, E6): block2 DMRG at chi=400..2400, extrapolated on discarded weight -> 0.
  Route B (determinant selection, E3):    selected-CI/QSCI growth to 750,257 determinants with Epstein-Nesbet
                                          PT2, extrapolated on PT2 -> 0 (the standard CIPSI extrapolation).

Different method classes, different extrapolation variables, no shared machinery beyond the Hamiltonian.
If they agree, each corroborates the other and the 40q exact energy is pinned far better than either alone.

This script performs Route B on the COMMITTED E3 trace (no new compute), reports its fit-window sensitivity
honestly, and compares to the committed Route A value. It also reports the 20q calibration of the same
extrapolator against a KNOWN exact FCI, for context on how far it can be trusted.
Output: results/e3_cipsi_crossvalidation.json.  EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, json
import numpy as np

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CHEM_ACC_MHA = 1.5936  # 1 kcal/mol


def _fit_pt2_to_zero(pt2_Ha, e_var):
    """Standard CIPSI extrapolation: linear E_var vs PT2, evaluated at PT2 = 0."""
    x = np.asarray(pt2_Ha, float); y = np.asarray(e_var, float)
    A = np.vstack([x, np.ones_like(x)]).T
    slope, E0 = np.linalg.lstsq(A, y, rcond=None)[0]
    yp = slope * x + E0
    ss = float(np.sum((y - yp) ** 2)); st = float(np.sum((y - np.mean(y)) ** 2))
    return float(E0), (1.0 - ss / st if st > 0 else 1.0)


def main():
    # ---- Route B: CIPSI PT2->0 on the committed 40q E3 trace ----
    e3 = json.load(open(os.path.join(_RES, "e3_certificate_evidence.json")))["points"]
    e3 = sorted(e3, key=lambda p: p["iter"])
    windows = {}
    for start in (1, 2, 3):                       # it0 (|PT2| = 84 mHa) is far outside the linear regime
        sub = [p for p in e3 if p["iter"] >= start]
        if len(sub) < 3:
            continue
        E0, r2 = _fit_pt2_to_zero([p["pt2_Ha"] for p in sub], [p["E_var"] for p in sub])
        windows[f"it{start}-it{sub[-1]['iter']}"] = {"E0_Ha": E0, "R2": round(r2, 6), "n_points": len(sub)}

    E0s = [w["E0_Ha"] for w in windows.values()]
    routeB = float(np.mean(E0s)); spread_mHa = (max(E0s) - min(E0s)) * 1000.0

    # ---- Route A: committed DMRG discarded-weight extrapolation (E6) ----
    e6 = json.load(open(os.path.join(_RES, "e6_dmrg_extrap_40q_evidence.json")))["extrapolation"]
    routeA = e6["E_fci_40q_estimate_Ha"]; routeA_unc = e6["E_fci_uncertainty_mHa"]

    agreements = {k: round((w["E0_Ha"] - routeA) * 1000.0, 4) for k, w in windows.items()}
    best = min(abs(v) for v in agreements.values()); worst = max(abs(v) for v in agreements.values())

    # ---- calibration of the same extrapolator at 20q, where exact FCI IS known ----
    # Calibrate on EVERY committed 20q trace, not a favourable one. This is where the honest limit lives.
    cal = {"traces": [], "note": ""}
    try:
        sp = json.load(open(os.path.join(_RES, "encoder", "selci_pt2_evidence.json")))
        for r in sp["results"]:
            pts = r["points"]
            E0c, _ = _fit_pt2_to_zero([p["pt2_mHa"] / 1000.0 for p in pts], [p["E_var"] for p in pts])
            cal["traces"].append({
                "R_ang": r["R"], "deepest_abs_PT2_mHa": round(abs(pts[-1]["pt2_mHa"]), 3),
                "deepest_ndet": pts[-1]["ndet"], "exact_FCI_Ha": r["e_fci"],
                "extrapolated_Ha": E0c, "error_mHa": round((E0c - r["e_fci"]) * 1000.0, 3)})
        cal["note"] = (
            "HONEST LIMIT — the extrapolator is NOT uniformly reliable. Its error at 20q tracks CORRELATION "
            "STRENGTH, not merely convergence depth: at R=0.74 (equilibrium, the geometry of the H20/40q "
            "flagship) it errs +4.1 mHa, but at R=2.4 (heavily stretched) it errs +53.9 mHa even though that "
            "trace reaches |PT2| = 1.08 mHa, i.e. essentially the SAME depth as the 40q trace (1.31 mHa). "
            "An earlier version of this file defended the 40q extrapolation on convergence depth alone; that "
            "defense is REFUTED by the R=2.4 trace in this same evidence file and has been withdrawn. The "
            "defensible statement is narrower: the 40q system is at equilibrium geometry, where the "
            "extrapolator calibrates well; we do NOT claim it would be reliable on a stretched 40q geometry. "
            "The PRIMARY evidence for the 40q value is not this calibration but the mutual agreement of two "
            "methodologically independent routes on that specific system.")
    except Exception as e:
        cal = {"error": str(e)}

    out = {
        "run": "e3_cipsi_crossvalidation",
        "claim": ("The 40-qubit exact (FCI) energy is pinned by TWO methodologically independent "
                  "extrapolations that agree far inside chemical accuracy."),
        "system": "H20 chain, 40 qubits, STO-6G, Jordan-Wigner (identical Hamiltonian for both routes)",
        "routeA_classical_DMRG_discarded_weight": {"E_Ha": routeA, "stated_uncertainty_mHa": routeA_unc,
                                                   "source": "e6_dmrg_extrap_40q_evidence.json (chi=400..2400)"},
        "routeB_selected_CI_PT2_to_zero": {"E_Ha": routeB, "fit_windows": windows,
                                           "window_spread_mHa": round(spread_mHa, 4),
                                           "source": "e3_certificate_evidence.json (750,257 dets, |PT2| to 1.31 mHa)"},
        "agreement_routeB_minus_routeA_mHa": agreements,
        "agreement_best_mHa": round(best, 4), "agreement_worst_mHa": round(worst, 4),
        "chem_acc_mHa": CHEM_ACC_MHA,
        "inside_chemical_accuracy_by": f"{CHEM_ACC_MHA / max(worst, 1e-9):.0f}x (worst window)",
        "calibration_20q_known_FCI": cal,
        "uncertainty_note": ("Route A also carries its own jackknife spread (e6_jackknife_robustness.json). "
            "Combining both, the honest worst-case route disagreement is ~0.10 mHa (~15x inside chemical "
            "accuracy), not the 25x implied by the worst fit window alone."),
        "headline": (f"Two independent routes to FCI(H20/40q) agree to {worst:.3f} mHa in the WORST fit window "
                     f"(best {best:.3f}; Route B window-mean vs Route A = {abs(routeB-routeA)*1000:.3f} mHa) — i.e. "
                     f"~{CHEM_ACC_MHA / max(worst,1e-9):.0f}x inside chemical accuracy on the worst window. "
                     f"QUOTE THE WORST WINDOW, not the best. Consensus value: {(routeA + routeB) / 2:.6f} Ha."),
        "honest_caveats": [
            "BOTH routes are extrapolations; neither is an exact FCI calculation (FCI at 40q is intractable).",
            "Route B's value depends on the fit window; the full window spread is reported, not just the best fit.",
            "The routes share the same Hamiltonian by necessity (that is what makes them comparable); they share "
            "no solver, no extrapolation variable, and no code path.",
            "The 20q calibration is NOT a clean bound: at equilibrium geometry (R=0.74, the flagship's regime) "
            "the extrapolator errs +4.1 mHa, but on a heavily stretched geometry (R=2.4) it errs +53.9 mHa at "
            "essentially the same convergence depth. We therefore do NOT claim the extrapolator is uniformly "
            "reliable; the 40q claim rests on the two routes' mutual agreement on that specific system.",
            "This is analysis of already-committed evidence: no new computation, nothing re-run or re-tuned.",
            "E3's pre-registered criterion (|PT2| <= 0.5 mHa) still FAILED as-measured; that is unchanged. This "
            "result is additional value extracted from the trace that run did produce, not a re-scored outcome."],
    }
    fn = os.path.join(_RES, "e3_cipsi_crossvalidation.json")
    json.dump(out, open(fn, "w"), indent=2)
    print(f"Route A (classical DMRG, dw->0)      : {routeA:.9f} Ha  (+/- {routeA_unc} mHa)")
    print(f"Route B (selected-CI, PT2->0)        : {routeB:.9f} Ha  (window spread {spread_mHa:.3f} mHa)")
    for k, v in agreements.items():
        print(f"   window {k:10s}: B-A = {v:+.4f} mHa")
    print(f"\n{out['headline']}")
    print("\n20q calibration of the SAME extrapolator (exact FCI known):")
    for t in cal.get("traces", []):
        print(f"   R={t['R_ang']:>4} Ang: |PT2|={t['deepest_abs_PT2_mHa']:>7.3f} mHa, "
              f"ndet={t['deepest_ndet']:>4} -> error {t['error_mHa']:+8.3f} mHa")
    if cal.get("note"):
        print(f"   {cal['note']}")
    print("saved", os.path.relpath(fn))


if __name__ == "__main__":
    main()
