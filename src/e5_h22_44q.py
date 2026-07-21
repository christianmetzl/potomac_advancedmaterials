"""E5 — 44-qubit H22 frontier (frozen + RE-FROZEN protocol, preregistration_v2.json).

Past the challenge goalpost, predicted in advance. STO-6G H22 chain, R=0.74 A, 44 qubits.
MP2-seeded (HF + top-256 doubles, mirroring the committed 40q flagship), IDENTICAL committed engine:
qsci_lib.PauliEngine.qsci_fast, GROW_PER_ITER=150,000, KCAP=3,000,000.

JUDGE (re-frozen 2026-07-20 after the E5 conditional fired on E1-at-40q textual case B):
results/h22_44q_dmrg_chi1200.json — block2 DMRG chi=1200, committed BEFORE this run. This runner
REFUSES to start production without that file. The chi=800/chi=400 rungs are reported alongside as
the ladder diagnostic, per the re-frozen entry.

Frozen predictions (judged independently, as-is):
  i  : determinant budget for chemical accuracy within [6e5, 7e6]
       (recorded = dets at the first iteration with |E - E_chi1200| <= 1.6 mHa)
  ii : |E_QSCI - E_DMRG(chi=1200)| <= 1.6 mHa at terminal
A non-converged attempt is reported as such with full logs (least-grounded extension, labeled so).

Smoke (container CPU): python src/e5_h22_44q.py --smoke 6    (H6 toy, FCI judge, mechanics only)
Production:            python src/e5_h22_44q.py              (env: GROW_ITERS/STATE_FILE)
EIGENNEXUS - GIC 2026 Phase 3, extension E5.
"""
import os, sys, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qsci_lib as L

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
ATOMS = 22
TOPM = 256
CHEM = 1.6
GROW_PER_ITER = 150_000            # frozen
KCAP = 3_000_000                   # frozen
GROW_ITERS = int(os.environ.get("GROW_ITERS", 60))
DET_BAND = (6e5, 7e6)              # frozen prediction i


def mp2_seed_dets(P, exc):
    hf = L.hf_det(P["ne"]); seed = {hf}
    for p, q, r, s in zip(exc["p"], exc["q"], exc["r"], exc["s"]):
        d = (hf & ~((1 << p) | (1 << q))) | (1 << r) | (1 << s)
        if bin(d).count("1") == P["ne"]: seed.add(d)
    return seed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", type=int, default=0)
    a = ap.parse_args()
    t0 = time.time()

    n_atoms = a.smoke if a.smoke else ATOMS
    P = L.hchain_problem(n_atoms, do_fci=bool(a.smoke))
    exc = L.mp2_excitation_lists(P["t2"], P["nocc"], P["nq"], top_m=(16 if a.smoke else TOPM))
    seed = mp2_seed_dets(P, exc)

    if a.smoke:
        eng = L.PauliEngine(P["qop"].terms)
        E, space = eng.qsci_fast(seed, grow_iters=30, grow_per_iter=100, kcap=10**6,
                                 log=lambda m: print(m, flush=True))
        print(f"E5 SMOKE H{n_atoms}: E={E:.8f} vs FCI -> {abs(E-P['e_fci'])*1e3:.4f} mHa, "
              f"dets={len(space)} [{time.time()-t0:.0f}s]", flush=True)
        return

    jf = os.path.join(_RES, "h22_44q_dmrg_chi1200.json")
    if not os.path.exists(jf):
        raise SystemExit("E5 REFUSED: judge reference results/h22_44q_dmrg_chi1200.json missing — "
                         "it must be committed BEFORE execution (re-frozen protocol). Build it via "
                         "src/dmrg_ladder_ext.py (or its --rung 22 1200 fallback) first.")
    e1200 = float(json.load(open(jf))["E_dmrg"])
    lad = {}
    for chi in (400, 800):
        f = os.path.join(_RES, f"h22_44q_dmrg_chi{chi}.json")
        if os.path.exists(f):
            lad[chi] = float(json.load(open(f))["E_dmrg"])
    print(f"E5: H22 44q | judge DMRG(chi=1200)={e1200:.8f} (committed pre-run) | ladder {lad} | "
          f"seed MP2 top{TOPM} ({len(seed)} dets) | grow {GROW_ITERS}x{GROW_PER_ITER} kcap {KCAP}",
          flush=True)

    eng = L.PauliEngine(P["qop"].terms)
    state_fn = os.environ.get("STATE_FILE", os.path.join(_RES, "e5_h22_state.npz"))
    ckpt_fn = os.path.join(_RES, "e5_h22_PARTIAL.json")
    trace = []

    def _ckpt(it, Ei, nd, ws):
        er = (Ei - e1200) * 1000
        trace.append(dict(iter=it, dets=int(nd), E=Ei, err_vs_chi1200_mHa=round(er, 3)))
        json.dump(dict(status=f"IN-PROGRESS iter {it}/{GROW_ITERS} (partial, not final)",
                       run="e5_h22_44q", trace=trace), open(ckpt_fn, "w"), indent=2)

    E, space = eng.qsci_fast(seed, grow_iters=GROW_ITERS, grow_per_iter=GROW_PER_ITER, kcap=KCAP,
                             log=lambda m: print(m, flush=True), ckpt=_ckpt, state_file=state_fn)
    err = (E - e1200) * 1000
    p_ii = abs(err) <= CHEM
    first = next((p for p in trace if abs(p["err_vs_chi1200_mHa"]) <= CHEM), None)
    p_i = bool(first and DET_BAND[0] <= first["dets"] <= DET_BAND[1])
    out = dict(run="e5_h22_44q", system="H22", qubits=44, seed=f"MP2 top-{TOPM} + HF",
               seed_dets=len(seed), final_space=int(len(space)), E_qsci=E,
               e_dmrg_chi1200=e1200, err_vs_chi1200_mHa=round(err, 3),
               ladder_refs={str(k): v for k, v in lad.items()},
               ladder_gaps_mHa={str(k): round((v - e1200) * 1000, 3) for k, v in lad.items()},
               engine="qsci_fast (incremental Hamiltonian, Option C) — identical committed engine",
               peak_host_rss_gb=round(L.peak_rss_gb(), 2), wall_s=round(time.time() - t0, 1),
               growth_trace=trace,
               prereg=dict(
                   prediction_i_det_band=dict(hit=p_i, band=list(DET_BAND),
                                              first_chem_acc_point=first),
                   prediction_ii_chem_acc_vs_chi1200=bool(p_ii),
                   judge="re-frozen chi=1200 (preregistration_v2.json, refrozen_2026-07-20)"))
    fn = os.path.join(_RES, "e5_h22_evidence.json")
    json.dump(out, open(fn, "w"), indent=2)
    if os.path.exists(ckpt_fn): os.remove(ckpt_fn)
    print(f"\nE5 H22 44q: E={E:.6f} vs chi1200 -> {err:+.3f} mHa | dets={len(space)} | "
          f"pred_i={'PASS' if p_i else 'FAIL'} pred_ii={'PASS' if p_ii else 'FAIL'} | "
          f"{out['wall_s']}s", flush=True)
    print(f"saved {os.path.relpath(fn)}", flush=True)


if __name__ == "__main__":
    main()
