"""WHEN CAN YOU TRUST YOUR CLASSICAL REFERENCE? — a measured reliability map.

The convergence-oracle result (38q) showed that a committed DMRG(chi=400) reference carried a silent
truncation error. The obvious practitioner question is: *when* does that happen — when do I actually need
an independent check? This answers it from committed evidence, with ground truth.

Two axes on which a "validated" bond dimension silently fails:

  AXIS 1 — CORRELATION STRENGTH (measured against EXACT FCI at 20 qubits):
      at fixed chi, DMRG truncation error grows by ~3 orders of magnitude as a bond is stretched from
      equilibrium into the strongly-correlated regime.
  AXIS 2 — SYSTEM SIZE (lower-bounded by the chi-ladder at 40 qubits):
      chi=400 is EXACT at 20q for every geometry tested (<=0.0002 mHa) — yet the same chi=400 at 40q is off
      by at least 0.92 mHa at equilibrium and at least 177 mHa stretched.

Conclusion (the honest, useful rule): a bond dimension validated on a smaller or easier system tells you
nothing about its error on a larger or harder one, and DMRG gives no internal signal either way. That is
precisely the regime where an independent variational check earns its keep.

Reads results/stretch_sweep_evidence.json only; no new computation.
Output: results/reference_reliability.json.  EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, json

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CHEM_ACC_MHA = 1.5936


def main():
    d = json.load(open(os.path.join(_RES, "stretch_sweep_evidence.json")))

    # --- AXIS 1: 20q, exact FCI known ---
    axis1 = []
    for r in d["part_a"]:
        errs = {g["chi"]: g.get("trunc_err_vs_fci_mHa") for g in r["dmrg"]}
        axis1.append({"R_ang": r["R"], "ccsd_t_err_mHa": r["ccsd_t"]["err_vs_fci_mHa"],
                      "dmrg_trunc_err_vs_exact_FCI_mHa": {str(k): v for k, v in sorted(errs.items())}})
    def _c(chi, i):
        return axis1[i]["dmrg_trunc_err_vs_exact_FCI_mHa"].get(str(chi))
    growth = {}
    for chi in (50, 100, 200):
        a, b = _c(chi, 0), _c(chi, -1)
        if a and b and a > 0:
            growth[f"chi{chi}"] = {"equilibrium_mHa": a, "stretched_mHa": b, "growth_factor": round(b / a, 1)}

    # --- AXIS 2: same chi=400, 20q (exact) vs 40q (lower bound) ---
    axis2 = []
    for r in d["part_b"]:
        E = {g["chi"]: g["E_dmrg"] for g in r["rungs"]}
        if 400 in E and 800 in E:
            axis2.append({"R_ang": r["R"], "chi400_error_lower_bound_mHa": round((E[400] - E[800]) * 1000, 2)})
    chi400_20q = {str(a["R_ang"]): a["dmrg_trunc_err_vs_exact_FCI_mHa"].get("400") for a in axis1}

    out = {
        "run": "reference_reliability_map",
        "question": "When does a classical DMRG reference become silently untrustworthy?",
        "axis1_correlation_strength": {
            "basis": "20 qubits (H10), EXACT FCI known — these are true errors, not estimates",
            "rows": axis1, "growth_equilibrium_to_stretched": growth,
            "finding": ("At fixed bond dimension, truncation error grows ~3 orders of magnitude from "
                        "equilibrium into the strongly-correlated regime. A chi that looks perfectly "
                        "converged at equilibrium can be an order of magnitude OUTSIDE chemical accuracy "
                        "where bonds break — with no internal signal.")},
        "axis2_system_size": {
            "basis": "the SAME chi=400: exact at 20q, lower-bounded by the chi-ladder at 40q",
            "chi400_error_at_20q_mHa": chi400_20q, "chi400_error_at_40q_lower_bound": axis2,
            "finding": ("chi=400 is exact at 20q at EVERY geometry tested (<=0.0002 mHa), yet the same "
                        "chi=400 at 40q is off by at least 0.92 mHa at equilibrium and at least 177 mHa "
                        "stretched. A bond dimension validated on a smaller system does not transfer.")},
        "chem_acc_mHa": CHEM_ACC_MHA,
        "headline": ("Two independent axes silently break a 'validated' classical reference: correlation "
                     "strength (~2000x error growth at fixed chi, measured against exact FCI at 20q) and "
                     "system size (chi=400 exact at 20q, >=0.92 mHa off at 40q). This is the measured "
                     "mechanism behind the 38q reference correction — and the rule for when an independent "
                     "variational check is needed."),
        "honest_caveats": [
            "Axis 1 is ground truth (exact FCI at 20q). Axis 2 values are LOWER BOUNDS: the chi=400->chi=800 "
            "gap under-counts chi=400's true error because chi=800 is itself not exact.",
            "H_n chains are a strong-correlation model system, not a materials benchmark; the qualitative "
            "rule (error grows with correlation and with size) is the claim, not a transferable constant.",
            "The 40q rungs use a frozen sweep schedule; a differently-tuned DMRG could land elsewhere.",
            "No new computation — analysis of already-committed evidence (stretch_sweep_evidence.json)."],
    }
    fn = os.path.join(_RES, "reference_reliability.json")
    json.dump(out, open(fn, "w"), indent=2)
    print("AXIS 1 — 20q, vs EXACT FCI (truncation error, mHa):")
    for a in axis1:
        e = a["dmrg_trunc_err_vs_exact_FCI_mHa"]
        print(f"   R={a['R_ang']:.2f}  CCSD(T)={a['ccsd_t_err_mHa']:>9.3f} | " +
              "  ".join(f"chi{c}={e.get(c)}" for c in ("50", "100", "200", "400")))
    for k, v in growth.items():
        print(f"   {k}: {v['equilibrium_mHa']} -> {v['stretched_mHa']} mHa = {v['growth_factor']}x")
    print("\nAXIS 2 — same chi=400:")
    print(f"   at 20q: {chi400_20q}  (exact)")
    for a in axis2:
        print(f"   at 40q, R={a['R_ang']:.2f}: >= {a['chi400_error_lower_bound_mHa']} mHa")
    print("\nsaved", os.path.relpath(fn))


if __name__ == "__main__":
    main()
