"""GPU RUN 1 — 40q H20 QSCI, MP2-SEEDED variant (sibling to gpu_run1_h20_mps.py).

Motivation (documented honestly): at 40q the tensornet-mps CIRCUIT sampler has a large FIXED
MPS-contraction cost that is ~independent of shot count (measured: 200k shots -> 9549s; 2k shots
still sampling at >22 min). That cost starves the determinant-growth phase, which is where accuracy
comes from. This driver seeds the QSCI subspace directly from the MP2 double-excitation determinants
(HF + top-M doubles) instead of circuit sampling — exactly the seed the committed 28q CPU
pre-validation used (results/qsci_28q_cpu_prevalidation_evidence.json). The determinant GROWTH is
identical regardless of seed source, and the GPU circuit sampler is already proven exact at 20q
(+0.000 mHa vs FCI, gpu_run1_h10_nvidia_evidence.json) and chem-accurate at 28q (+0.395 mHa vs
DMRG chi=400, gpu_run1_h14_nvidia_evidence.json).

Scope of what this tests:
  * P1 (energy vs committed DMRG(chi=400)) — legitimately tested (growth is seed-independent).
  * P2 (converged determinant budget in [3e5,4e6]) — legitimately tested.
  * P3 (peak DEVICE memory < 8 GB of the tensornet-mps run) — NOT tested here: this path does no MPS
    sampling, so there is no MPS device footprint to judge. Host RSS is reported for transparency and
    P3 is left None. (The 40q MPS device-memory question is separate; attempt-1 saw 12.06 GB there.)

Nothing is tuned after seeing results; no threshold is moved. Per-iteration durable checkpoint.
"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qsci_lib as L

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CHEM = 1.6
ATOMS = 20
TOPM = 256
GROW_ITERS = 60
GROW_PER_ITER = 30000
KCAP = 1_500_000


def dmrg_reference(qubits):
    """Committed DMRG(best chi) energy — identical loader to gpu_run1_h20_mps.dmrg_reference."""
    d = json.load(open(os.path.join(_RES, "mps_bonddim_evidence.json")))
    for s in d["study_A_error_vs_chi"]:
        if s["qubits"] == qubits:
            best = min(s["points"], key=lambda p: p["E"])
            return float(best["E"]), f"block2 DMRG(chi={best['chi']}) [committed evidence, predates access]"
    raise RuntimeError(f"{qubits}q point not found in mps_bonddim_evidence.json")


def mp2_seed_dets(P, exc):
    """HF determinant + one determinant per top-M MP2 double excitation (p,q occupied -> r,s virtual).
    This is the determinant support the compressed-UCC circuit populates when sampled, built directly."""
    hf = L.hf_det(P["ne"])
    seed = {hf}
    for p, q, r, s in zip(exc["p"], exc["q"], exc["r"], exc["s"]):
        d = (hf & ~((1 << p) | (1 << q))) | (1 << r) | (1 << s)
        if bin(d).count("1") == P["ne"]:          # number-conserving guard (should always hold)
            seed.add(d)
    return seed


def main():
    t0 = time.time()
    print(f"RUN1-MP2SEED: H{ATOMS} ({2*ATOMS}q) | seed=MP2(top{TOPM}) | grow {GROW_ITERS}x{GROW_PER_ITER} kcap {KCAP}", flush=True)
    P = L.hchain_problem(ATOMS, do_fci=False)
    exc = L.mp2_excitation_lists(P["t2"], P["nocc"], P["nq"], top_m=TOPM)
    seed = mp2_seed_dets(P, exc)
    t_build = time.time() - t0
    print(f"  MP2 seed |space|={len(seed)} (HF + {len(exc['th'])} doubles) | build {t_build:.1f}s", flush=True)

    e_ref, ref_kind = dmrg_reference(P["nq"])
    print(f"  reference: {ref_kind} E={e_ref:.6f}", flush=True)

    devmon = L.DeviceMemMonitor().start()   # transparency; growth is CPU/scipy so expect ~idle GPU
    eng = L.PauliEngine(P["qop"].terms)
    ckpt_fn = os.path.join(_RES, "gpu_run1_h20_mp2seed_PARTIAL.json")

    def _ckpt(it, Ei, nd, ws):
        er = (Ei - e_ref) * 1000
        json.dump(dict(status=f"IN-PROGRESS iter {it}/{GROW_ITERS} (partial, not final)",
                       run="gpu_run1_mp2seed", system=f"H{ATOMS}", qubits=P["nq"], seed="MP2",
                       iter=it, dets=int(nd), E_qsci=Ei, e_ref=e_ref, err_mHa=round(er, 3),
                       P1_at_iter=bool(abs(er) <= CHEM), qsci_wall_s=round(ws, 1)),
                  open(ckpt_fn, "w"), indent=2)

    t2 = time.time()
    E, space = eng.qsci_fast(seed, grow_iters=GROW_ITERS, grow_per_iter=GROW_PER_ITER,
                             kcap=KCAP, log=lambda m: print(m, flush=True), ckpt=_ckpt)
    t_qsci = time.time() - t2
    devmon.stop()
    err = (E - e_ref) * 1000
    host_mem = L.peak_rss_gb()
    dev_mem = devmon.gb()

    p1 = abs(err) <= CHEM
    p2 = (3e5 <= len(space) <= 4e6)
    out = dict(run="gpu_run1_mp2seed", system=f"H{ATOMS}", qubits=P["nq"], seed="MP2 (top-M doubles + HF)",
               top_m_excitations=len(exc["th"]), seed_dets=len(seed), final_space=int(len(space)),
               E_qsci=E, e_ref=e_ref, ref_kind=ref_kind, err_mHa=round(err, 3),
               peak_host_rss_gb=round(host_mem, 2), peak_device_mem_gb=dev_mem,
               p3_note="P3 (MPS device memory) NOT tested by the MP2-seed path; no MPS sampling here",
               engine="qsci_fast (incremental Hamiltonian, Option C)",
               wall_s=dict(build=round(t_build, 1), qsci=round(t_qsci, 1), total=round(time.time() - t0, 1)),
               prereg=dict(P1_chem_acc=bool(p1), P2_det_band=bool(p2), P3_mem_lt_8gb=None))
    fn = os.path.join(_RES, "gpu_run1_h20_mp2seed_evidence.json")
    json.dump(out, open(fn, "w"), indent=2)
    if os.path.exists(ckpt_fn):
        os.remove(ckpt_fn)
    print(f"\nRUN1-MP2SEED H{ATOMS}: E={E:.6f} vs {ref_kind} -> {err:+.3f} mHa | dets={len(space)} | "
          f"device {('%.2f GB' % dev_mem) if dev_mem is not None else 'n/a'} | total {out['wall_s']['total']}s", flush=True)
    print(f"prereg: P1(<=1.6 mHa)={'PASS' if p1 else 'FAIL'} P2(dets in [3e5,4e6])={'PASS' if p2 else 'FAIL'} "
          f"P3(device<8GB)=N/A (MP2-seed path, no MPS)", flush=True)
    print(f"saved {os.path.relpath(fn)}", flush=True)


if __name__ == "__main__":
    main()
