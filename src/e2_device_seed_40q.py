"""E2 — device-sampled selection at the 40q flagship (frozen protocol, preregistration_v2.json).

Consumes the COMMITTED device sample results/p3_sample_dets.json VERBATIM as the growth seed
(102 number-conserving determinants sampled from the compressed-UCC circuit on tensornet-mps/A100,
200k shots, top-256 MP2 doubles — produced alongside the P3 evidence; the frozen protocol explicitly
allows this reuse, zeroing E2's sampling cost). Growth is the IDENTICAL committed engine and schedule
as the MP2-seeded flagship run: qsci_lib.PauliEngine.qsci_fast, GROW_PER_ITER=150000, KCAP=450000
(matching the committed terminal determinant count 450,257).

Frozen judge: |E_device-seeded - E_MP2-seeded(-10.290969)| <= 0.5 mHa at the matched determinant
count -> seed-independence CONFIRMED at 40q (retires the 'proxy at scale' caveat). Deviation > 0.5
mHa is itself the reported FINDING (caveat stays). Err vs the committed DMRG references reported
alongside in both cases. Nothing tuned after seeing results.

Smoke (container CPU): python src/e2_device_seed_40q.py --smoke 6   (H6 toy, FCI judge, mechanics only)
Production:            python src/e2_device_seed_40q.py             (env: GROW_ITERS/STATE_FILE)
EIGENNEXUS - GIC 2026 Phase 3, extension E2.
"""
import os, sys, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qsci_lib as L

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
E_MP2_SEEDED = -10.290969          # frozen in preregistration_v2.json E2
TOL_MHA = 0.5                      # frozen
GROW_PER_ITER = 150_000            # frozen
KCAP = 450_000                     # frozen
GROW_ITERS = int(os.environ.get("GROW_ITERS", 60))


def committed_refs():
    """chi=400 committed flagship reference + E1 chi=800 — reported alongside per the frozen text."""
    d = json.load(open(os.path.join(_RES, "mps_bonddim_evidence.json")))
    e400 = None
    for s in d["study_A_error_vs_chi"]:
        if s["qubits"] == 40:
            e400 = float(min(s["points"], key=lambda p: p["E"])["E"])
    e800 = json.load(open(os.path.join(_RES, "h20_40q_dmrg_chi800.json")))["E_dmrg"]
    return e400, float(e800)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", type=int, default=0, help="toy H_n mechanics smoke (no evidence written)")
    a = ap.parse_args()
    t0 = time.time()

    if a.smoke:
        P = L.hchain_problem(a.smoke, do_fci=True)
        exc = L.mp2_excitation_lists(P["t2"], P["nocc"], P["nq"], top_m=16)
        hf = L.hf_det(P["ne"]); seed = {hf}
        for p, q, r, s in zip(exc["p"], exc["q"], exc["r"], exc["s"]):
            d = (hf & ~((1 << p) | (1 << q))) | (1 << r) | (1 << s)
            if bin(d).count("1") == P["ne"]: seed.add(d)
        eng = L.PauliEngine(P["qop"].terms)
        E, space = eng.qsci_fast(seed, grow_iters=30, grow_per_iter=100, kcap=10**6,
                                 log=lambda m: print(m, flush=True))
        print(f"E2 SMOKE H{a.smoke}: E={E:.8f} vs FCI -> {abs(E-P['e_fci'])*1e3:.4f} mHa, "
              f"dets={len(space)} [{time.time()-t0:.0f}s]", flush=True)
        return

    sd = json.load(open(os.path.join(_RES, "p3_sample_dets.json")))
    seed = {int(d) for d, _cnt in sd["determinants"]}
    assert sd["qubits"] == 40 and sd["n_number_conserving_dets"] == len(seed) == 102
    print(f"E2: H20 40q | seed = COMMITTED device sample ({len(seed)} dets, {sd['shots']} shots, "
          f"{sd['target']}) | grow {GROW_ITERS}x{GROW_PER_ITER} kcap {KCAP}", flush=True)

    P = L.hchain_problem(20, do_fci=False)
    e400, e800 = committed_refs()
    eng = L.PauliEngine(P["qop"].terms)
    state_fn = os.environ.get("STATE_FILE", os.path.join(_RES, "e2_device_seed_state.npz"))
    ckpt_fn = os.path.join(_RES, "e2_device_seed_PARTIAL.json")
    trace = []

    def _ckpt(it, Ei, nd, ws):
        dv = (Ei - E_MP2_SEEDED) * 1000
        trace.append(dict(iter=it, dets=int(nd), E=Ei, dev_vs_mp2seed_mHa=round(dv, 3),
                          err_vs_chi400_mHa=round((Ei - e400) * 1000, 3)))
        json.dump(dict(status=f"IN-PROGRESS iter {it}/{GROW_ITERS} (partial, not final)",
                       run="e2_device_seed", trace=trace), open(ckpt_fn, "w"), indent=2)

    E, space = eng.qsci_fast(seed, grow_iters=GROW_ITERS, grow_per_iter=GROW_PER_ITER, kcap=KCAP,
                             log=lambda m: print(m, flush=True), ckpt=_ckpt, state_file=state_fn)
    dev = (E - E_MP2_SEEDED) * 1000
    match = abs(dev) <= TOL_MHA
    out = dict(run="e2_device_seed_40q", system="H20", qubits=40,
               seed="COMMITTED device sample p3_sample_dets.json (verbatim, per frozen protocol)",
               seed_dets=len(seed), final_space=int(len(space)), E_qsci=E,
               e_mp2_seeded_frozen=E_MP2_SEEDED, deviation_vs_mp2seed_mHa=round(dev, 3),
               matched_det_count_note=f"committed terminal was 450,257; this run capped at {KCAP}",
               err_vs_dmrg_chi400_mHa=round((E - e400) * 1000, 3),
               err_vs_dmrg_chi800_mHa=round((E - e800) * 1000, 3),
               engine="qsci_fast (incremental Hamiltonian, Option C) — identical committed engine",
               peak_host_rss_gb=round(L.peak_rss_gb(), 2), wall_s=round(time.time() - t0, 1),
               growth_trace=trace,
               prereg=dict(E2_seed_independence=bool(match), tol_mHa=TOL_MHA,
                           verdict=("seed-independence CONFIRMED at 40q; proxy-at-scale caveat retired"
                                    if match else
                                    "seed-dependence at scale — reported as the FINDING; caveat stays")))
    fn = os.path.join(_RES, "e2_device_seed_evidence.json")
    json.dump(out, open(fn, "w"), indent=2)
    if os.path.exists(ckpt_fn): os.remove(ckpt_fn)
    print(f"\nE2: E={E:.6f} | dev vs MP2-seeded {dev:+.3f} mHa (tol {TOL_MHA}) -> "
          f"{'PASS (seed-independent)' if match else 'FINDING (seed-dependent)'} | "
          f"dets={len(space)} | vs chi400 {out['err_vs_dmrg_chi400_mHa']:+.3f} / "
          f"chi800 {out['err_vs_dmrg_chi800_mHa']:+.3f} mHa | {out['wall_s']}s", flush=True)
    print(f"saved {os.path.relpath(fn)}", flush=True)


if __name__ == "__main__":
    main()
