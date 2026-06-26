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


# (label, script, args, output-json-basename, [(json-path, expected, tol_mHa_or_abs), ...], quick?)
CHECKS = [
    ("two-stage GQE (H2/H4/H6)", "stage2_refinement.py", [], "stage2_refinement_evidence.json",
     [(["0", "err_mHa"], 0.0, 0.05), (["1", "err_mHa"], 0.009, 0.05), (["2", "err_mHa"], 0.297, 0.1)], False),
    ("integrated GQE->QSCI (H6 12q)", "gqe_qsci.py", [], "gqe_qsci_evidence.json",
     [(["GQE_to_QSCI_err_mHa"], 1.054, 0.6)], False),     # stochastic sampling -> looser tol
    ("SnO (16q)", "sno_demo.py", [], None,
     [("__stdout_mHa__", 0.113, 0.08)], False),
    ("SnO2 (20q)", "sno2_demo.py", [], None,
     [("__stdout_mHa__", 0.225, 0.10)], False),
    ("CrO/NiO (20q)", "transition_metal_oxide_qsci.py", [], "transition_metal_qsci_evidence.json",
     [(["0", "qsci_best_err_mHa"], 0.038, 0.05), (["1", "qsci_best_err_mHa"], 0.197, 0.08)], True),
    ("HamLib equivalence (28q)", "hamlib_validate.py", ["14"], None,
     [("__stdout_terms__", 27735, 0)], True),
    ("classical baselines (Hn FCI)", "classical_baselines.py", ["6", "10"], "classical_baselines_evidence.json",
     [(["results", "0", "FCI_ref_match", "diff_mHa"], 0.0, 0.01)], False),
]


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
        jp = os.path.join(workdir, out_json)
        if not os.path.exists(jp):
            return ("ERROR", label, f"{out_json} not produced", time.time() - t0)
        data = json.load(open(jp))

    details = []
    ok = True
    for path, expected, tol in asserts:
        if path == "__stdout_mHa__":
            got = next((float(t.split("mHa")[0].strip().split()[-1])
                        for line in out.splitlines() if "mHa" in line and "error" in line.lower()
                        for t in [line.split(":")[-1]]), None)
            unit = "mHa"
        elif path == "__stdout_terms__":
            got = next((int(w) for line in out.splitlines() if "ours=" in line
                        for w in line.replace("ours=", " ").split() if w.isdigit()), None)
            unit = "terms"
        else:
            got = _val(data, path); unit = ""
        passed = got is not None and abs(got - expected) <= tol + (1e-9 if tol == 0 else 0)
        ok = ok and passed
        details.append(f"{got}~{expected}{unit}{'' if passed else ' ✗'}")
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
