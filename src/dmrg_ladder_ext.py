"""E5 pre-run DMRG references (H22/44q) + classical simulation-layer ladder 48-64q — CPU, zero credits.

Two deliverables, one frozen protocol (committed BEFORE execution; evidence records the commit):

  1) E5 REFERENCES (the judge, built pre-run per the re-frozen E5 entry in preregistration_v2.json):
     H22 STO-6G R=0.74 (44q), chi = 400, 800 (ladder rungs) and chi = 1200 (THE re-frozen reference).
     Identical integral path + frozen sweep schedule as every committed reference
     (e1_chi800_counteraudit.h20_integrals / run_dmrg). Output: results/h22_44q_dmrg_chi{400,800,1200}.json
     in the committed reference format. chi=1200 runs SUBPROCESS-ISOLATED (15 GB box): an OOM is
     recorded as resource-DNF and the reference is then built on the big-RAM instance BEFORE any E5
     growth starts (provenance preserved: committed before execution either way).

  2) CLASSICAL LADDER (honest framing, frozen here): H24/H26/H28/H30/H32 = 48/52/56/60/64 qubits,
     STO-6G R=0.74. DMRG chi=400 (mandatory, in-process) and chi=800 (subprocess-isolated, optional-
     if-memory), plus RHF and CCSD(T) on the identical molecules as a NON-tensor-network cross-anchor
     at equilibrium (where CCSD(T) is reliable). This is SIMULATION-LAYER HEADROOM evidence — a
     classical result about the engine's room past the goalpost. NO QSCI claim attaches to it, and it
     must never be quoted as a quantum-pipeline result; past ~44q no audit-grade independent reference
     exists (assessed and declined 2026-07-20, docs/credit_budget.md rule 3 note).

Order of execution is memory-aware and E5-priority: H22 chi400 -> chi800 -> chi1200(subproc) first
(unblocks the costliest authorized run), then ladder chi400 ascending, then ladder chi800(subproc)
ascending. Evidence results/dmrg_ladder_ext_evidence.json flushes after every rung; scratch deleted
per rung (container disk budget).

EIGENNEXUS - GIC 2026 Phase 3, E-campaign pre-work + supplementary.
"""
import os, sys, json, time, resource, subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e1_chi800_counteraudit as e1

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RES = os.path.join(_ROOT, "results")
_OUT = os.path.join(_RES, "dmrg_ladder_ext_evidence.json")

H22_CHIS_INPROC = [400, 800]
H22_CHI_JUDGE = 1200
LADDER_ATOMS = [24, 26, 28, 30, 32]
LADDER_CHI_MAND = 400
LADDER_CHI_OPT = 800
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


def _rung(n_atoms, chi, tag):
    P = e1.h20_integrals(n_atoms, R=0.74)
    r = e1.run_dmrg(P, chi, tag, n_threads=N_THREADS)
    _rm_scratch(r.pop("scratch", ""))
    r.update(rhf_converged=P["rhf_converged"], e_hf=P["e_hf"],
             active_space=P["active_space"], qubits=P["qubits"])
    return r


def _write_reference(n_atoms, chi, r, role):
    """Committed-reference-format JSON, mirroring the e1 output fields."""
    fn = f"h{n_atoms}_{2*n_atoms}q_dmrg_chi{chi}.json"
    out = dict(system=f"H{n_atoms} chain", active_space=f"H{n_atoms} STO-6G R=0.74",
               qubits=2 * n_atoms, dmrg_chi=chi, E_dmrg=r["E_dmrg"], wall_s=r["wall_s"],
               sweep_schedule=r["sweep_schedule"], rhf_converged=r["rhf_converged"],
               machine=e1.machine_specs(N_THREADS), role=role,
               code_path_note=("block2 DMRG via the committed e1_chi800_counteraudit integral path "
                               "(pyscf RHF STO-6G -> MO integrals -> block2 SU2, frozen schedule)"),
               prereg=("E5 re-frozen 2026-07-20 (results/preregistration_v2.json): chi=1200 is the "
                       "judge; chi=400/800 are ladder rungs. Committed BEFORE any E5 QSCI execution."))
    path = os.path.join(_RES, fn)
    json.dump(out, open(path, "w"), indent=2)
    _log(f"[lx] wrote results/{fn}  E={r['E_dmrg']:.10f}")
    return fn


def _ccsdt(n_atoms):
    from pyscf import gto, scf, cc
    out = {}
    try:
        mol = gto.M(atom="; ".join(f"H 0 0 {i*0.74:.4f}" for i in range(n_atoms)),
                    basis="sto-6g", verbose=0)
        mf = scf.RHF(mol).run(conv_tol=1e-10)
        out["e_hf"] = float(mf.e_tot)
        out["rhf_converged"] = bool(mf.converged)
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


def _subproc_rung(n_atoms, chi):
    side = os.path.join(_RES, f"ladder_rung_h{n_atoms}_chi{chi}.json")
    p = subprocess.run([sys.executable, os.path.abspath(__file__),
                        "--rung", str(n_atoms), str(chi), side], cwd=_ROOT, text=True)
    if p.returncode == 0 and os.path.exists(side):
        r = json.load(open(side))
        os.remove(side)
        return r, None
    return None, dict(status="DNF", returncode=p.returncode,
                      note="resource-DNF (subprocess died; 15 GB box) — recorded, not dropped")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--rung":
        n, chi, out_path = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        r = _rung(n, chi, f"lxs_h{n}_c{chi}")
        json.dump(r, open(out_path, "w"), indent=1)
        return

    t0 = time.time()
    ev = dict(
        title="E5 pre-run DMRG references (H22/44q) + classical simulation-layer ladder 48-64q",
        status_note=("Protocol frozen by committing this file before execution; E5 judge = chi1200 "
                     "per the re-frozen entry (preregistration_v2.json). Ladder is CLASSICAL headroom "
                     "evidence: no QSCI claim attaches, and no audit-grade independent reference "
                     "exists past ~44q — labeled accordingly wherever cited."),
        cost_note="zero platform credits: session container CPU (4 threads, 15 GB)",
        protocol_commit=_git_head(),
        machine=e1.machine_specs(N_THREADS),
        h22_references=[], ladder=[],
    )
    _flush(ev)

    # ---- 1) E5 references: H22 chi 400/800 in-process, chi 1200 subprocess ----
    for chi in H22_CHIS_INPROC:
        _log(f"\n[lx] ==== H22 44q reference rung chi={chi} ====")
        r = _rung(22, chi, f"lx_h22_c{chi}")
        fn = _write_reference(22, chi, r, role="E5 ladder rung (chi=%d)" % chi)
        ev["h22_references"].append(dict(chi=chi, file=fn, E_dmrg=r["E_dmrg"], wall_s=r["wall_s"]))
        _flush(ev)
    _log(f"\n[lx] ==== H22 44q JUDGE rung chi={H22_CHI_JUDGE} (subprocess-isolated) ====")
    r, dnf = _subproc_rung(22, H22_CHI_JUDGE)
    if r is not None:
        fn = _write_reference(22, H22_CHI_JUDGE, r, role="E5 JUDGE reference (re-frozen chi=1200)")
        ev["h22_references"].append(dict(chi=H22_CHI_JUDGE, file=fn, E_dmrg=r["E_dmrg"],
                                         wall_s=r["wall_s"]))
    else:
        ev["h22_references"].append(dict(chi=H22_CHI_JUDGE, **dnf,
                                         fallback="build on the big-RAM instance BEFORE E5 growth "
                                                  "starts; commit precedes execution either way"))
    _flush(ev)

    # ---- 2) classical ladder: chi400 ascending, then chi800 subprocesses ascending ----
    for n in LADDER_ATOMS:
        _log(f"\n[lx] ==== Ladder H{n} {2*n}q chi={LADDER_CHI_MAND} ====")
        rec = dict(n_atoms=n, qubits=2 * n, ccsd_t=_ccsdt(n))
        r = _rung(n, LADDER_CHI_MAND, f"lx_h{n}_c{LADDER_CHI_MAND}")
        rec["dmrg_chi400"] = dict(E_dmrg=r["E_dmrg"], wall_s=r["wall_s"])
        if "E_ccsd_t" in rec["ccsd_t"]:
            rec["dmrg400_minus_ccsdt_mHa"] = round(
                (r["E_dmrg"] - rec["ccsd_t"]["E_ccsd_t"]) * 1e3, 3)
        ev["ladder"].append(rec)
        _log(f"[lx] H{n}: chi400 E={r['E_dmrg']:.8f}  vs CCSD(T) "
             f"{rec.get('dmrg400_minus_ccsdt_mHa', 'n/a')} mHa")
        _flush(ev)
    for n in LADDER_ATOMS:
        _log(f"\n[lx] ==== Ladder H{n} {2*n}q chi={LADDER_CHI_OPT} (subprocess-isolated) ====")
        r, dnf = _subproc_rung(n, LADDER_CHI_OPT)
        rec = next(x for x in ev["ladder"] if x["n_atoms"] == n)
        if r is not None:
            rec["dmrg_chi800"] = dict(E_dmrg=r["E_dmrg"], wall_s=r["wall_s"])
            rec["chi_gap_400_800_mHa"] = round(
                (rec["dmrg_chi400"]["E_dmrg"] - r["E_dmrg"]) * 1e3, 4)
            _log(f"[lx] H{n}: chi800 E={r['E_dmrg']:.8f}  gap400-800 "
                 f"{rec['chi_gap_400_800_mHa']} mHa")
        else:
            rec["dmrg_chi800"] = dnf
        _flush(ev)

    ev["total_wall_s"] = round(time.time() - t0, 1)
    _flush(ev)
    _log(f"\n[lx] LADDER + E5 REFERENCES COMPLETE total_wall_s={ev['total_wall_s']}")


if __name__ == "__main__":
    main()
