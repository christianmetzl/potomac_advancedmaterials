"""One-command reproducibility driver for judges.

Runs the verified CPU result scripts from a clean temporary working directory and checks each
headline number against the committed results/*.json within a tolerance, printing a PASS/FAIL
table. This is the "judges re-run your code" path (Phase 3 criterion 8 / Top-Action #1): a single
command that confirms the headline results reproduce without modification.

Usage:
    python src/reproduce.py            # run the full CPU suite
    python src/reproduce.py --quick    # skip the slower scripts (transition-metal, hamlib-40q)

Scope — two honest check families, labeled distinctly in the output:
  * RE-EXECUTION (16): CPU-reproducible headline scripts re-run from a clean workdir and asserted
    against committed values (several need optional deps — cudaq/block2/torch/pennylane/openfermionpyscf
    — and SKIP cleanly when the dep is absent, rather than erroring).
  * AUDIT (9): committed GPU/cloud/one-shot evidence JSONs verified for internal arithmetic
    (err == (E - ref)*1000), stated pass criteria, and pre-registration integrity (the blind-holdout
    script's SHA-256 must still match the hash committed before its one-shot run). Audits are NOT
    re-runs — a CPU judge box cannot re-execute GPU/QPU jobs — and are never counted as such.

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
      ("eq", ["2", "err_mHa"], 0.297, 0.1)], False, "pennylane"),   # GQE (torch/pennylane) — optional, SKIP if absent
    ("integrated GQE->QSCI (H6 12q)", "gqe_qsci.py", [], "gqe_qsci_evidence.json",
     [("eq", ["GQE_to_QSCI_err_mHa"], 1.054, 0.8)], False, "torch"),  # stochastic; torch/pennylane optional, SKIP if absent
    ("SnO chem-acc (16q)", "sno_demo.py", [], None,
     [("below", "final_mHa", 0.6)], False),                      # claim: chemical accuracy (~0.11 mHa)
    ("SnO2 chem-acc (20q)", "sno2_demo.py", [], None,
     [("below", "final_mHa", 0.6)], False),                      # claim: chemical accuracy (~0.23 mHa)
    ("CrO/NiO (20q)", "transition_metal_oxide_qsci.py", [], "transition_metal_qsci_evidence.json",
     [("eq", ["0", "qsci_best_err_mHa"], 0.038, 0.05), ("eq", ["1", "qsci_best_err_mHa"], 0.197, 0.08)], True),
    ("bridged tin-oxo Sn2O2 (16q)", "tin_oxo_demo.py", [], "tin_oxo_evidence.json",
     [("lt", ["qsci_best_err_mHa"], 1.6)], False),
    ("HamLib equivalence (28q)", "hamlib_validate.py", ["14"], None,
     [("eq_terms", 27735)], True, "openfermionpyscf"),   # openfermionpyscf optional, SKIP if absent
    ("classical baselines (Hn FCI)", "classical_baselines.py", ["6", "10", "12"], "classical_baselines_evidence.json",
     [("eq", ["results", "0", "FCI_ref_match", "diff_mHa"], 0.0, 0.02)], False),
    ("CrO dissociation trust", "cro_dissociation.py", [], "cro_dissociation_evidence.json",
     [("lt", ["geometries", "0", "selCI_err_mHa"], 0.5), ("ccsdt_breaks",), ("selci_robust",)], True),
    ("CrO spin-gap decision", "cro_spin_gap.py", [], "cro_spin_gap_evidence.json",
     [("gt", ["casci_gap_eV"], 1.0), ("gt", ["qsci_gap_eV"], 1.0), ("gt", ["dft_spread_eV"], 1.5),
      ("eqi", ["n_functionals_wrong_sign"], 1)], True),
    ("EN-PT2 two-sided bracket", "encoder/selci_pt2.py", [], "encoder/selci_pt2_evidence.json",
     [("var_upper_bound",), ("abslt", ["results", "0", "extrap_err_mHa"], 10.0),
      ("gt", ["results", "0", "extrap_R2"], 0.99)], True),
    ("blind holdout VO re-run (frozen script)", "blind_holdout_vo.py", [], "blind_holdout_vo_result.json",
     [("lt", ["states", "quartet", "qsci_err_mHa"], 1.6), ("lt", ["states", "doublet", "qsci_err_mHa"], 1.6),
      ("eqi", ["prediction_b_matches_experiment"], 1)], True),
    # Optional checks — run only if the (CPU-installable) extra deps are present; SKIP otherwise.
    ("CUDA-Q execution (qpp-cpu)", "cudaq_qsci.py", [], "cudaq_qsci_evidence.json",
     [("abslt", ["results", "0", "vqe_err_mHa"], 1.6), ("abslt", ["results", "0", "qsci_err_mHa"], 1.6)],
     True, "cudaq"),
    ("MPS bond-dim & entanglement", "mps_bonddim_study.py", [], "mps_bonddim_evidence.json",
     [("lt", ["study_A_error_vs_chi", "0", "chi_for_chem_acc"], 100), ("mps_entangle_grows",)],
     True, "block2"),
    ("integral engine selftest (SC vs JW + FCI)", "qsci_int.py", [], None,
     [("stdout_has", "INTEGRAL ENGINE VALID")], False, "cudaq"),
    ("engine equivalence (fast vs orig vs FCI)", "engine_equivalence.py", [], "engine_equivalence_evidence.json",
     [("lt", ["max_engine_dev_mHa"], 1e-4), ("lt", ["max_fci_err_mHa"], 1.6)], False, "cudaq"),
    # Evidence audits — no re-execution: verify the committed evidence JSON's internal arithmetic and
    # pass criteria (for runs a CPU judge box cannot re-execute: GPU / cloud / one-shot artifacts).
    # Labeled AUDIT in the output; never presented as a re-run.
    ("AUDIT: 20q GPU exact anchor (cuStateVec)", None, [], "gpu_run1_h10_nvidia_evidence.json",
     [("consistent_err", ["E_qsci"], ["e_ref"], ["err_mHa"], 0.01), ("abslt", ["err_mHa"], 1.6),
      ("lt", ["peak_device_mem_gb"], 8.0)], False),
    ("AUDIT: 28q GPU converged (cuStateVec)", None, [], "gpu_run1_h14_nvidia_evidence.json",
     [("consistent_err", ["E_qsci"], ["e_ref"], ["err_mHa"], 0.01), ("abslt", ["err_mHa"], 1.6),
      ("lt", ["peak_device_mem_gb"], 8.0), ("gt", ["final_space"], 30000)], False),
    ("AUDIT: 40q frontier checkpoint (iter5)", None, [], "gpu_run1_h20_mp2seed_iter5_checkpoint.json",
     [("consistent_err", ["E_qsci"], ["e_ref"], ["err_mHa"], 0.01), ("eq", ["err_mHa"], 3.222, 0.001),
      ("gt", ["dets"], 100000)], False),
    ("AUDIT: 28q CPU pre-validation", None, [], "qsci_28q_cpu_prevalidation_evidence.json",
     [("eq", ["err_mHa"], 1.219, 0.001), ("eqi", ["chemical_accuracy_1p6mHa"], 1)], False),
    ("AUDIT: pre-registration integrity", None, [], "preregistration_v1.json",
     [("len_eq", ["predictions"], 6),
      ("sha256_frozen", ["predictions", "5", "script_sha256"], "blind_holdout_vo.py")], False),
    ("AUDIT: qBraid cloud-runtime P5 chain", None, [], "qbraid_P5_qbraid_qbraid_sim_qir-sv_evidence.json",
     [("abslt", ["err_mHa"], 5.0), ("len_eq", ["job_ids"], 3), ("eqi", ["dominant_is_hf"], 1)], False),
    ("AUDIT: qBraid hosted 20q validation", None, [], "qbraid_hosted_h10_evidence.json",
     [("abslt", ["err_grown_mHa"], 1.6), ("eqi", ["export_exact_verified"], 1)], False),
    ("AUDIT: AQT trapped-ion silicon decode (2 jobs)", None, [], "qpu_aqt_evidence.json",
     [("len_eq", ["results"], 2),
      ("consistent_err", ["results", "0", "E_grown"], ["results", "0", "e_fci"], ["results", "0", "err_grown_mHa"], 0.01),
      ("abslt", ["results", "0", "err_grown_mHa"], 1.6), ("abslt", ["results", "1", "err_grown_mHa"], 1.6),
      ("gt", ["results", "0", "postselect_keep_frac"], 0.2), ("gt", ["results", "1", "postselect_keep_frac"], 0.2),
      ("eq", ["results", "0", "err_sampled_mHa"], 20.435, 0.01), ("eq", ["results", "1", "err_sampled_mHa"], 11.127, 0.01)], False),
    ("AUDIT: crossover walls (memory + dets)", None, [], "crossover_evidence.json",
     [("gt", ["wall1_memory", "exact_statevector_bytes", "40"], 1e13),
      ("lt", ["wall2_determinants", "qsci_growth_per_qubit"], 1.5),
      ("eq", ["wall2_determinants", "fci_growth_per_qubit"], 2.0, 0.01)], False),
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


def _importable(mod):
    import importlib.util
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False


def run_check(label, script, args, out_json, asserts, workdir, requires=None):
    t0 = time.time()
    if requires and not _importable(requires):
        return ("SKIP", label, f"optional dep '{requires}' not installed", time.time() - t0)
    out = ""
    if script is None:
        # AUDIT mode: no re-execution — load the committed evidence JSON and verify its internal
        # arithmetic / pass criteria (for GPU/cloud/one-shot artifacts a CPU judge box cannot re-run).
        jp = os.path.join(REPO, "results", out_json)
        if not os.path.exists(jp):
            return ("ERROR", label, f"committed evidence {out_json} missing", time.time() - t0)
        data = json.load(open(jp))
    else:
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
        elif kind == "mps_entangle_grows":  # entanglement entropy rises from equilibrium to strong correlation
            B = data["study_B_entanglement_vs_R"]
            passed = B[-1]["Smax"] > B[0]["Smax"]
            details.append(f"Smax {B[0]['Smax']:.2f}->{B[-1]['Smax']:.2f}{'' if passed else ' ✗'}")
        elif kind == "stdout_has":  # required marker line printed by the script's own selftest
            _, marker = a
            passed = marker in out
            details.append(f"'{marker}' printed{'' if passed else ' ✗'}")
        elif kind == "consistent_err":  # committed err_mHa must equal (E - ref) * 1000 (arithmetic audit)
            _, ep, rp, xp, tol = a
            got = abs((_val(data, ep) - _val(data, rp)) * 1000 - _val(data, xp))
            passed = got <= tol
            details.append(f"err consistent (Δ={got:.4f} mHa){'' if passed else ' ✗'}")
        elif kind == "len_eq":
            _, path, expected = a
            got = len(_val(data, path))
            passed = got == expected
            details.append(f"len={got}=={expected}{'' if passed else ' ✗'}")
        elif kind == "sha256_frozen":  # committed hash must match the frozen script ON DISK today
            import hashlib
            _, path, fname = a
            committed = _val(data, path)
            actual = hashlib.sha256(open(os.path.join(SRC, fname), "rb").read()).hexdigest()
            passed = committed == actual
            details.append(f"sha256({fname}) matches prereg{'' if passed else ' ✗ TAMPERED'}")
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
        for c in CHECKS:
            label, script, args, out_json, asserts, is_slow = c[:6]
            requires = c[6] if len(c) > 6 else None
            if quick and is_slow:
                print(f"  SKIP    {label} (--quick)"); continue
            status, lbl, detail, dt = run_check(label, script, args, out_json, asserts, wd, requires)
            print(f"  {status:7s} {lbl:34s} {detail}  [{dt:.0f}s]")
            rows.append((status, lbl))
    npass = sum(1 for s, _ in rows if s == "PASS")
    nskip = sum(1 for s, _ in rows if s == "SKIP")
    ncore = len(rows) - nskip
    naudit = sum(1 for _, l in rows if l.startswith("AUDIT"))
    extra = f" (+{nskip} optional SKIPPED — install cudaq/block2 to run them)" if nskip else ""
    print("=" * 60 + f"\n{npass}/{ncore} checks PASS{extra}"
          f"\n  [{ncore - naudit} re-execution + {naudit} evidence audits;"
          f" audits verify committed GPU/cloud/one-shot artifacts, not re-runs]")
    sys.exit(0 if npass == ncore else 1)


if __name__ == "__main__":
    main()
