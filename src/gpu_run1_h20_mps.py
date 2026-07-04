"""GPU RUN 1 (prereg P1+P2+P3): 40-qubit H20 GQE/QSCI with CUDA-Q MPS circuit evaluation.

Pipeline: MP2-compressed circuit (top-M doubles, first-order angles) -> cudaq.sample on the chosen
backend (tensornet-mps on qBraid GPU; qpp-cpu for CPU smoke tests) -> number-conserving determinants
seed a device-seeded selected-CI (the QSCI principle) -> energy vs reference.

Reference: exact FCI for smoke sizes (<=20q); at 40q the committed block2 DMRG(chi=400) energy from
results/mps_bonddim_evidence.json (pass --redo-dmrg to recompute it live).

Pre-registered pass/fail (results/preregistration_v1.json — evaluated and printed automatically):
  P1: |E_QSCI - E_ref| <= 1.6 mHa at 40q, chi=400 MPS evaluation.
  P2: determinants used for the converged energy inside [3e5, 4e6]  (fit point 1.13e6).
  P3: peak memory < 8 GB.

Smoke test (CPU, run today):   python src/gpu_run1_h20_mps.py --atoms 6 --shots 20000
Production (qBraid GPU):       CUDAQ_TARGET=tensornet-mps python src/gpu_run1_h20_mps.py --atoms 20 \
                                   --shots 200000 --topm 256 --grow-iters 60 --kcap 2000000
EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import qsci_lib as L

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CHEM = 1.6


def dmrg_reference(qubits, redo=False):
    """Committed DMRG(best chi) energy for a given qubit count (20/28/40 present in the evidence),
    or recompute with block2 (--redo-dmrg). The reference predates any qBraid access."""
    if not redo:
        d = json.load(open(os.path.join(_RES, "mps_bonddim_evidence.json")))
        for s in d["study_A_error_vs_chi"]:
            if s["qubits"] == qubits:
                best = min(s["points"], key=lambda p: p["E"])
                return float(best["E"]), f"block2 DMRG(chi={best['chi']}) [committed evidence, predates access]"
        raise RuntimeError(f"{qubits}q point not found in mps_bonddim_evidence.json "
                           f"(available: use --redo-dmrg to compute live)")
    from mps_bonddim_study import _driver_for, dmrg_at_chi
    driver, mpo = _driver_for(qubits // 2, 0.74)
    e, _ = dmrg_at_chi(driver, mpo, 400)
    return float(e), "block2 DMRG(chi=400) [recomputed]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--atoms", type=int, default=20)
    ap.add_argument("--target", default=os.environ.get("CUDAQ_TARGET", "qpp-cpu"))
    ap.add_argument("--shots", type=int, default=200000)
    ap.add_argument("--topm", type=int, default=256)
    ap.add_argument("--grow-iters", type=int, default=40)
    ap.add_argument("--grow-per-iter", type=int, default=50000)   # Option C: big batches reach the
    ap.add_argument("--kcap", type=int, default=1500000)          # P2 det band ([3e5,4e6]) in ~20 iters
    ap.add_argument("--redo-dmrg", action="store_true")
    a = ap.parse_args()

    t0 = time.time()
    print(f"RUN1: H{a.atoms} ({2*a.atoms}q) | target={a.target} shots={a.shots} topM={a.topm}", flush=True)
    P = L.hchain_problem(a.atoms, do_fci=(a.atoms <= 10))
    exc = L.mp2_excitation_lists(P["t2"], P["nocc"], P["nq"], top_m=a.topm)
    t_build = time.time() - t0

    devmon = L.DeviceMemMonitor().start()       # peak GPU device memory over sampling + QSCI (P3)
    t1 = time.time()
    dets, nraw = L.sample_dets(P["nq"], P["ne"], exc, shots=a.shots, target=a.target)
    t_sample = time.time() - t1
    print(f"  sampled {len(dets)} number-conserving dets ({nraw} raw bitstrings) in {t_sample:.1f}s", flush=True)

    if P["e_fci"] is not None:
        e_ref, ref_kind = P["e_fci"], "FCI (exact)"
    else:
        e_ref, ref_kind = dmrg_reference(P["nq"], a.redo_dmrg)   # 28q/40q committed; else --redo-dmrg

    t2 = time.time()
    eng = L.PauliEngine(P["qop"].terms)
    seed = set(dets) | {L.hf_det(P["ne"])}
    ckpt_fn = os.path.join(_RES, f"gpu_run1_h{a.atoms}_{a.target.replace('-','')}_PARTIAL.json")
    def _ckpt(it, Ei, nd, ws):                  # durable per-iteration artifact (ephemeral instance)
        er = (Ei - e_ref) * 1000
        json.dump(dict(status=f"IN-PROGRESS iter {it}/{a.grow_iters} (partial, not final)",
                       system=f"H{a.atoms}", qubits=P["nq"], target=a.target, iter=it, dets=int(nd),
                       E_qsci=Ei, e_ref=e_ref, err_mHa=round(er, 3), P1_at_iter=bool(abs(er) <= CHEM),
                       qsci_wall_s=round(ws, 1)), open(ckpt_fn, "w"), indent=2)
    E, space = eng.qsci_fast(seed, grow_iters=a.grow_iters, grow_per_iter=a.grow_per_iter,
                             kcap=a.kcap, log=lambda m: print(m, flush=True), ckpt=_ckpt)
    t_qsci = time.time() - t2
    if os.path.exists(ckpt_fn): os.remove(ckpt_fn)   # completed cleanly -> final JSON supersedes partial
    devmon.stop()
    err = (E - e_ref) * 1000
    host_mem = L.peak_rss_gb()
    dev_mem = devmon.gb()                       # peak GPU device memory (None on CPU runs)

    p1 = abs(err) <= CHEM
    p2 = (3e5 <= len(space) <= 4e6) if a.atoms == 20 else None
    # P3 is pre-registered as DEVICE memory < 8 GB. On GPU runs judge device memory; on CPU smoke
    # (no device) there is nothing to judge -> report host RSS transparently, P3 = None.
    mem_metric = dev_mem if dev_mem is not None else host_mem
    p3 = (mem_metric < 8.0) if dev_mem is not None else None
    out = dict(run="gpu_run1", system=f"H{a.atoms}", qubits=P["nq"], target=a.target,
               shots=a.shots, top_m_excitations=len(exc["th"]), sampled_dets=len(dets),
               final_space=int(len(space)), E_qsci=E, e_ref=e_ref, ref_kind=ref_kind,
               err_mHa=round(err, 3), peak_host_rss_gb=round(host_mem, 2), peak_device_mem_gb=dev_mem,
               p3_metric=("device" if dev_mem is not None else "host_rss (no GPU present)"),
               engine="qsci_fast (incremental Hamiltonian, Option C)",
               wall_s=dict(build=round(t_build, 1), sample=round(t_sample, 1), qsci=round(t_qsci, 1),
                           total=round(time.time() - t0, 1)),
               prereg=dict(P1_chem_acc=bool(p1), P2_det_band=p2,
                           P3_mem_lt_8gb=(bool(p3) if p3 is not None else None)))
    fn = f"gpu_run1_h{a.atoms}_{a.target.replace('-','')}_evidence.json"
    json.dump(out, open(os.path.join(_RES, fn), "w"), indent=2)
    memstr = (f"device {dev_mem:.2f} GB" if dev_mem is not None else f"host RSS {host_mem:.2f} GB (no GPU)")
    print(f"\nRUN1 H{a.atoms}: E={E:.6f} vs {ref_kind} -> {err:+.3f} mHa | dets={len(space)} | "
          f"{memstr} | total {time.time()-t0:.0f}s", flush=True)
    print(f"prereg: P1(<=1.6 mHa)={'PASS' if p1 else 'FAIL'}"
          + (f" P2(det band)={'PASS' if p2 else 'FAIL'}" if p2 is not None else "")
          + (f" P3(device<8GB)={'PASS' if p3 else 'FAIL'}" if p3 is not None else " P3=N/A (CPU)"), flush=True)
    print(f"saved results/{fn}", flush=True)


if __name__ == "__main__":
    main()
