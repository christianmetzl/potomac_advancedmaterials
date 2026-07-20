"""Stretched-geometry truncation-error-vs-correlation sweep — the Phase 2 §5 promise
("report ... truncation error versus correlation") delivered at CPU tier, zero credits.

STATUS / HONESTY: this is a POST-CAMPAIGN SUPPLEMENTARY study, not part of preregistration_v1/v2.
The protocol below (geometries, chi ladders, schedules, QSCI growth parameters) is FROZEN by
committing this file BEFORE execution; the evidence JSON records the commit hash it ran from.
No pass/fail gates are defined post hoc — results are reported as measured against exact anchors.

Protocol (frozen):
  Part A — H10 STO-6G, 20 qubits, exact anchor. R in {0.74, 1.00, 1.50, 2.00, 2.50} Angstrom.
    * FCI on the identical MO integrals (pyscf direct_spin1) = exact reference.
    * CCSD(T) on the same RHF (breakdown-vs-correlation context; convergence recorded, never hidden).
    * DMRG chi in {50, 100, 200, 400}: block2 via e1_chi800_counteraudit.run_dmrg — the SAME frozen
      schedule as every committed reference ([100,150,200,chi*5], noises [1e-4..0], thrds 1e-8, SU2).
      Truncation error := E_DMRG(chi) - E_FCI, exact by construction.
    * QSCI growth (qsci_int.IntEngine, the engine of the committed 38/40q runs), HF seed,
      grow_per_iter=400, grow_iters=80, kcap=25000, eps1=1e-5 (the 20q-verified screen),
      hij_floor=1e-5, tcap=2400 s. Error vs FCI reported as measured.
  Part B — H20 STO-6G, 40 qubits, at-scale ladder. R in {0.74, 1.50, 2.50}.
    * DMRG chi in {100, 200, 400, 800} (mandatory), same frozen schedule/path (e1.h20_integrals +
      e1.run_dmrg). Truncation gap := E(chi) - E(800); a LOWER BOUND on true truncation error
      (no exact anchor exists at 40q).
    * chi=1200 rung: OPTIONAL-IF-MEMORY (15 GB box), attempted LAST per geometry in a SUBPROCESS so
      an OOM kill cannot destroy completed evidence; failure recorded as resource-DNF, not dropped.
    * Cross-check: the (R=0.74, chi=400) rung must reproduce the committed flagship reference
      results/h20_40q_dmrg_chi400_VALIDATE.json (E=-10.292235707925087); delta recorded.
  Evidence: results/stretch_sweep_evidence.json, flushed incrementally after every rung
  (a crash loses at most the rung in flight). Raw stdout: results/stretch_sweep_rawlog.txt (tee'd
  by the launcher). Scratch per rung is deleted after use (container disk budget).

EIGENNEXUS — GIC 2026 Phase 3, supplementary (Phase 2 §5 follow-through).
"""
import os, sys, json, time, platform, resource, subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import e1_chi800_counteraudit as e1              # committed integral + frozen-schedule DMRG path
from qsci_int import IntEngine

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RES = os.path.join(_ROOT, "results")
_OUT = os.path.join(_RES, "stretch_sweep_evidence.json")

R_A = [0.74, 1.00, 1.50, 2.00, 2.50]
CHI_A = [50, 100, 200, 400]
R_B = [0.74, 1.50, 2.50]
CHI_B = [100, 200, 400, 800]
CHI_B_OPT = 1200
QSCI_PARAMS = dict(grow_iters=80, grow_per_iter=400, kcap=25000, eps1=1e-5,
                   hij_floor=1e-5, tcap=2400)
COMMITTED_H20_CHI400 = -10.292235707925087       # results/h20_40q_dmrg_chi400_VALIDATE.json
N_THREADS = 4


def _log(m):
    print(m, flush=True)


def _git_head():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=_ROOT, capture_output=True,
                              text=True, timeout=10).stdout.strip()
    except Exception:
        return "unavailable"


def _flush(ev):
    ev["peak_host_rss_gb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2, 2)
    tmp = _OUT + ".tmp"
    json.dump(ev, open(tmp, "w"), indent=1)
    os.replace(tmp, _OUT)


def _rm_scratch(path):
    import shutil
    try:
        shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


def _dmrg_rung(P, chi, tag):
    r = e1.run_dmrg(P, chi, tag, n_threads=N_THREADS)
    _rm_scratch(r.pop("scratch", ""))
    return r


def _ccsdt(n_atoms, R):
    """CCSD(T) on the identical RHF; convergence + failures recorded, never hidden."""
    from pyscf import gto, scf, cc
    out = {}
    try:
        mol = gto.M(atom="; ".join(f"H 0 0 {i*R:.4f}" for i in range(n_atoms)),
                    basis="sto-6g", verbose=0)
        mf = scf.RHF(mol).run(conv_tol=1e-10)
        mycc = cc.CCSD(mf)
        mycc.max_cycle = 200
        mycc.verbose = 0
        mycc.kernel()
        out["ccsd_converged"] = bool(mycc.converged)
        et = mycc.ccsd_t()
        out["E_ccsd_t"] = float(mycc.e_tot + et)
    except Exception as ex:
        out["error"] = f"{type(ex).__name__}: {ex}"
    return out


def part_a(ev):
    from pyscf import fci
    for R in R_A:
        _log(f"\n[sw] ==== Part A  H10 20q  R={R:.2f} ====")
        P = e1.h20_integrals(10, R=R)
        rec = dict(R=R, e_hf=P["e_hf"], rhf_converged=P["rhf_converged"])
        e_fci = float(fci.direct_spin1.kernel(P["h1"], P["eri"], P["n_sites"],
                                              (P["na"], P["nb"]), ecore=P["ecore"],
                                              max_cycle=300)[0])
        rec["E_fci"] = e_fci
        rec["e_corr_mHa"] = round((e_fci - P["e_hf"]) * 1e3, 3)   # correlation axis, measured
        cc_rec = _ccsdt(10, R)
        if "E_ccsd_t" in cc_rec:
            cc_rec["err_vs_fci_mHa"] = round((cc_rec["E_ccsd_t"] - e_fci) * 1e3, 3)
        rec["ccsd_t"] = cc_rec
        _log(f"[sw] FCI={e_fci:.8f}  Ecorr={rec['e_corr_mHa']:.1f} mHa  CCSD(T): {cc_rec}")

        rec["dmrg"] = []
        for chi in CHI_A:
            r = _dmrg_rung(P, chi, f"swa_R{int(R*100)}_c{chi}")
            r["trunc_err_vs_fci_mHa"] = round((r["E_dmrg"] - e_fci) * 1e3, 4)
            rec["dmrg"].append(r)
            _log(f"[sw] A R={R:.2f} chi={chi}: trunc err {r['trunc_err_vs_fci_mHa']:+.4f} mHa")
            ev["part_a"] = ev.get("part_a", [])
            _upsert(ev["part_a"], rec)
            _flush(ev)

        eng = IntEngine(P["h1"], P["eri"], P["ecore"], P["qubits"])
        hf = (1 << (P["na"] + P["nb"])) - 1
        t0 = time.time()
        E, space = eng.qsci_inc([hf], log=_log, **QSCI_PARAMS)
        rec["qsci"] = dict(E=float(E), dets=int(len(space)),
                           err_vs_fci_mHa=round((E - e_fci) * 1e3, 4),
                           wall_s=round(time.time() - t0, 1), seed="HF", params=QSCI_PARAMS)
        _log(f"[sw] A R={R:.2f} QSCI: {rec['qsci']['err_vs_fci_mHa']:+.4f} mHa "
             f"@ {rec['qsci']['dets']} dets")
        _upsert(ev["part_a"], rec)
        _flush(ev)


def _upsert(lst, rec):
    for i, x in enumerate(lst):
        if x["R"] == rec["R"]:
            lst[i] = rec
            return
    lst.append(rec)


def part_b(ev):
    for R in R_B:
        _log(f"\n[sw] ==== Part B  H20 40q  R={R:.2f} ====")
        P = e1.h20_integrals(20, R=R)
        rec = dict(R=R, e_hf=P["e_hf"], rhf_converged=P["rhf_converged"], rungs=[])
        for chi in CHI_B:
            r = _dmrg_rung(P, chi, f"swb_R{int(R*100)}_c{chi}")
            rec["rungs"].append(r)
            if R == 0.74 and chi == 400:
                d = (r["E_dmrg"] - COMMITTED_H20_CHI400) * 1e3
                rec["cross_check_committed_chi400_delta_mHa"] = round(d, 6)
                _log(f"[sw] CROSS-CHECK vs committed chi400 reference: {d:+.6f} mHa")
            _log(f"[sw] B R={R:.2f} chi={chi}: E={r['E_dmrg']:.8f}  wall={r['wall_s']}s")
            ev["part_b"] = ev.get("part_b", [])
            _upsert(ev["part_b"], rec)
            _flush(ev)
        e800 = next(r["E_dmrg"] for r in rec["rungs"] if r["chi"] == 800)
        rec["trunc_gap_vs_chi800_mHa"] = {
            str(r["chi"]): round((r["E_dmrg"] - e800) * 1e3, 4) for r in rec["rungs"]}
        _upsert(ev["part_b"], rec)
        _flush(ev)


def part_b_opt(ev):
    """chi=1200 rungs, subprocess-isolated: an OOM kill loses only the rung in flight."""
    for R in R_B:
        _log(f"\n[sw] ==== Part B optional  H20 40q  R={R:.2f} chi={CHI_B_OPT} (subprocess) ====")
        side = os.path.join(_RES, f"stretch_sweep_rung_R{int(R*100)}_chi{CHI_B_OPT}.json")
        p = subprocess.run([sys.executable, os.path.abspath(__file__),
                            "--b-rung", f"{R}", str(CHI_B_OPT), side],
                           cwd=_ROOT, text=True)
        rec = next(x for x in ev["part_b"] if x["R"] == R)
        if p.returncode == 0 and os.path.exists(side):
            r = json.load(open(side))
            os.remove(side)
            rec["optional_chi1200"] = r
            e800 = next(x["E_dmrg"] for x in rec["rungs"] if x["chi"] == 800)
            rec["trunc_gap_vs_chi800_mHa"]["1200"] = round((r["E_dmrg"] - e800) * 1e3, 4)
            _log(f"[sw] B-opt R={R:.2f} chi=1200: E={r['E_dmrg']:.8f}")
        else:
            rec["optional_chi1200"] = dict(status="DNF", returncode=p.returncode,
                                           note="resource-DNF (subprocess died; 15 GB box) — "
                                                "recorded, not silently dropped")
            _log(f"[sw] B-opt R={R:.2f} chi=1200: DNF rc={p.returncode}")
        _flush(ev)


def b_rung_main(R, chi, out_path):
    P = e1.h20_integrals(20, R=R)
    r = _dmrg_rung(P, chi, f"swbo_R{int(R*100)}_c{chi}")
    json.dump(r, open(out_path, "w"), indent=1)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--b-rung":
        b_rung_main(float(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
        return
    t0 = time.time()
    ev = dict(
        title="Stretched-geometry truncation-error-vs-correlation sweep (Phase 2 §5 follow-through)",
        status_note=("POST-CAMPAIGN SUPPLEMENTARY: not in preregistration_v1/v2; protocol frozen by "
                     "committing src/stretch_sweep.py before execution (commit recorded below); no "
                     "post-hoc pass/fail gates — measured values reported against exact anchors"),
        phase2_promise="Phase 2 §5 benchmarking plan: 'report ... truncation error versus correlation'",
        cost_note="zero platform credits: container CPU (grant GPU instances retired 2026-07-19)",
        protocol_commit=_git_head(),
        machine=e1.machine_specs(N_THREADS),
        code_path_note=("integrals + DMRG via e1_chi800_counteraudit (the committed, chi400-validated "
                        "path); QSCI via qsci_int.IntEngine (the committed 38/40q growth engine)"),
        part_a=[], part_b=[],
    )
    _flush(ev)
    part_a(ev)
    part_b(ev)
    part_b_opt(ev)
    ev["total_wall_s"] = round(time.time() - t0, 1)
    ev["completed_utc_note"] = "wall timestamps live in the tee'd rawlog (no clock calls added here)"
    _flush(ev)
    _log(f"\n[sw] SWEEP COMPLETE total_wall_s={ev['total_wall_s']} -> results/stretch_sweep_evidence.json")


if __name__ == "__main__":
    main()
