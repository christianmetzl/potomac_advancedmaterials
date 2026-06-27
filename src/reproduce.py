"""One-command reproducibility driver for judges.

Runs the verified CPU result scripts from a clean temporary working directory and checks each
headline number against the committed results/*.json within a tolerance, printing a PASS/FAIL
table. This is the "judges re-run your code" path (Phase 3 criterion 8 / Top-Action #1): a single
command that confirms the headline results reproduce without modification.

Usage:
    python src/reproduce.py            # run the full CPU suite
    python src/reproduce.py --quick    # skip the slower scripts (transition-metal, hamlib-40q)

Scope: the CPU-reproducible headline numbers (the same set verified in
docs/reproducibility_audit_2026-06-21.md). GPU/qBraid scaling runs are out of scope here.

EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, json, time, tempfile, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "src")


def _val(d, path):
    for k in path:
        d = d[int(k)] if isinstance(d, list) else d[k]
    return d


# Assert kinds:
#   ("eq",  json-path, expected, tol)         -> |value - expected| <= tol (exact-reproducible numbers)
#   ("below", "final_mHa", threshold)         -> final "...error... X mHa" line value < threshold (claim = chem. acc.)
#   ("eq_terms", expected)                    -> HamLib "terms: ours=N" == expected
# Sn-oxide / QSCI-accuracy claims use a "below chemical accuracy" threshold rather than brittle exact-match,
# because the scientific claim is chemical accuracy and PySCF-version numerics shift the 3rd decimal.
CHECKS = [
    ("two-stage GQE (H2/H4/H6)", "stage2_refinement.py", [], "stage2_refinement_evidence.json",
     [("eq", ["0", "err_mHa"], 0.0, 0.05), ("eq", ["1", "err_mHa"], 0.009, 0.05),
      ("eq", ["2", "err_mHa"], 0.297, 0.1)], False),
    ("integrated GQE->QSCI (H6 12q)", "gqe_qsci.py", [], "gqe_qsci_evidence.json",
     [("eq", ["GQE_to_QSCI_err_mHa"], 1.054, 0.8)], False),     # stochastic sampling -> loose tol
    ("SnO chem-acc (16q)", "sno_demo.py", [], None,
     [("below", "final_mHa", 0.6)], False),                      # claim: chemical accuracy (~0.11 mHa)
    ("SnO2 chem-acc (20q)", "sno2_demo.py", [], None,
     [("below", "final_mHa", 0.6)], False),                      # claim: chemical accuracy (~0.23 mHa)
    ("CrO/NiO (20q)", "transition_metal_oxide_qsci.py", [], "transition_metal_qsci_evidence.json",
     [("eq", ["0", "qsci_best_err_mHa"], 0.038, 0.05), ("eq", ["1", "qsci_best_err_mHa"], 0.197, 0.08)], True),
    ("HamLib equivalence (28q)", "hamlib_validate.py", ["14"], None,
     [("eq_terms", 27735)], True),
    ("classical baselines (Hn FCI)", "classical_baselines.py", ["6", "10"], "classical_baselines_evidence.json",
     [("eq", ["results", "0", "FCI_ref_match", "diff_mHa"], 0.0, 0.02)], False),
    ("CrO dissociation trust", "cro_dissociation.py", [], "cro_dissociation_evidence.json",
     [("lt", ["geometries", "0", "selCI_err_mHa"], 0.5), ("ccsdt_breaks",), ("selci_robust",)], True),
    ("CrO spin-gap decision", "cro_spin_gap.py", [], "cro_spin_gap_evidence.json",
     [("gt", ["casci_gap_eV"], 1.0), ("gt", ["qsci_gap_eV"], 1.0), ("gt", ["dft_spread_eV"], 1.5),
      ("eqi", ["n_functionals_wrong_sign"], 1)], True),
    ("EN-PT2 two-sided bracket", "encoder/selci_pt2.py", [], "encoder/selci_pt2_evidence.json",
     [("var_upper_bound",), ("abslt", ["results", "0", "extrap_err_mHa"], 10.0),
      ("gt", ["results", "0", "extrap_R2"], 0.99)], True),
]


def _find_json(out_json, workdir):
    """Scripts write either to CWD (workdir) or to the repo's results/ (abspath). Check both."""
    for cand in (os.path.join(workdir, out_json), os.path.join(REPO, "results", out_json)):
        if os.path.exists(cand):
            return cand
    return None


def _final_mHa(out):
    """Value from the explicit final 'error vs FCI: X mHa' line (robust to intermediate err= lines)."""
    val = None
    for line in out.splitlines():
        ll = line.lower()
        if "final" in ll and "error" in ll and "mha" in ll:
            try:
                val = float(line.split(":")[-1].split("mHa")[0].strip().split()[-1])
            except (ValueError, IndexError):
                pass
    return val


def _terms(out):
    for line in out.splitlines():
        if "terms:" in line and "ours=" in line:
            try:
                return int(line.split("ours=")[1].split()[0])
            except (ValueError, IndexError):
                pass
    return None


def run_check(label, script, args, out_json, asserts, workdir):
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, os.path.join(SRC, script), *args],
                           cwd=workdir, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        return ("TIMEOUT", label, "exceeded 30 min", time.time() - t0)
    if p.returncode != 0:
        return ("ERROR", label, (p.stderr.strip().splitlines() or ["(no stderr)"])[-1], time.time() - t0)
    out = p.stdout
    data = None
    if out_json:
        jp = _find_json(out_json, workdir)
        if jp is None:
            return ("ERROR", label, f"{out_json} not produced", time.time() - t0)
        data = json.load(open(jp))

    details = []
    ok = True
    for a in asserts:
        kind = a[0]
        if kind == "below":
            _, _, thr = a
            got = _final_mHa(out)
            passed = got is not None and got < thr
            details.append(f"{got} mHa < {thr}{'' if passed else ' ✗'}")
        elif kind == "eq_terms":
            _, expected = a
            got = _terms(out)
            passed = got == expected
            details.append(f"{got} terms =={expected}{'' if passed else ' ✗'}")
        elif kind in ("lt", "gt", "abslt", "eqi"):
            _, path, ref = a
            got = _val(data, path)
            v = abs(got) if kind == "abslt" else got
            passed = (kind == "lt" and v < ref) or (kind == "gt" and v > ref) or \
                     (kind == "abslt" and v < ref) or (kind == "eqi" and int(v) == int(ref))
            op = {"lt": "<", "gt": ">", "abslt": "|.|<", "eqi": "=="}[kind]
            details.append(f"{got}{op}{ref}{'' if passed else ' ✗'}")
        elif kind == "ccsdt_breaks":  # CCSD(T) fails on the CrO stretch: large error or non-convergence
            geos = data["geometries"]
            errs = [abs(g["CCSDT_err_mHa"]) for g in geos if g.get("CCSDT_err_mHa") is not None]
            nonconv = any(not g["CCSDT_converged"] for g in geos)
            passed = (max(errs) > 20.0) if errs else False
            passed = passed or nonconv
            details.append(f"CCSD(T) max|err|={max(errs):.0f}mHa nonconv={nonconv}{'' if passed else ' ✗'}")
        elif kind == "selci_robust":  # selected-CI/QSCI stays accurate at every geometry
            geos = data["geometries"]
            passed = all(g["selCI_err_mHa"] < 5.0 for g in geos)
            details.append(f"selCI all<5mHa (max {max(g['selCI_err_mHa'] for g in geos):.2f}){'' if passed else ' ✗'}")
        elif kind == "var_upper_bound":  # E_var is a rigorous variational upper bound at every PT2 point
            pts = [p for r in data["results"] for p in r["points"]]
            passed = all(p["var_err_mHa"] >= -0.2 for p in pts)
            details.append(f"E_var≥FCI ∀ {len(pts)} pts{'' if passed else ' ✗'}")
        else:  # "eq"
            _, path, expected, tol = a
            got = _val(data, path)
            passed = got is not None and abs(got - expected) <= tol + 1e-9
            details.append(f"{got}~{expected}{'' if passed else ' ✗'}")
        ok = ok and passed
    return ("PASS" if ok else "FAIL", label, "; ".join(details), time.time() - t0)


def main():
    quick = "--quick" in sys.argv
    print("MATGEN-Q reproducibility driver — CPU headline results\n" + "=" * 60)
    rows = []
    with tempfile.TemporaryDirectory() as wd:
        for label, script, args, out_json, asserts, is_slow in CHECKS:
            if quick and is_slow:
                print(f"  SKIP   {label} (--quick)"); continue
            status, lbl, detail, dt = run_check(label, script, args, out_json, asserts, wd)
            print(f"  {status:7s} {lbl:34s} {detail}  [{dt:.0f}s]")
            rows.append((status, lbl))
    npass = sum(1 for s, _ in rows if s == "PASS")
    print("=" * 60 + f"\n{npass}/{len(rows)} checks PASS")
    sys.exit(0 if npass == len(rows) else 1)


if __name__ == "__main__":
    main()
