"""GPU RUN 1 — 40q H20 QSCI via HEAT-BATH-CI screened growth (integral engine).

Sibling to gpu_run1_h20_mp2seed.py. Same MP2 seed and same committed DMRG(chi=400) reference, but
the growth uses the integral (Slater-Condon) engine with eps1 heat-bath candidate screening
(IntEngine.qsci_inc). eps1 caps the candidate pool BEFORE dedup — the selection-scan cost that
explodes at 100k+ determinants — VERIFIED at 20q to shrink the pool 2.8-9.5x with the energy
preserved (0.087->0.088 mHa at eps1=1e-5). Big batches keep the number of (expensive) eigensolves
low. Durable per-iteration checkpoint. Nothing tuned after seeing results; no threshold moved.

Smoke (CPU, reaches FCI):  python src/gpu_run1_h20_hbci.py --atoms 6 --smoke
40q production (overnight): python src/gpu_run1_h20_hbci.py
EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "encoder"))
import qsci_lib as L
from qsci_int import IntEngine

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CHEM = 1.6


def dmrg_reference(qubits):
    d = json.load(open(os.path.join(_RES, "mps_bonddim_evidence.json")))
    for s in d["study_A_error_vs_chi"]:
        if s["qubits"] == qubits:
            best = min(s["points"], key=lambda p: p["E"])
            return float(best["E"]), f"block2 DMRG(chi={best['chi']}) [committed, predates access]"
    raise RuntimeError(f"{qubits}q not in mps_bonddim_evidence.json")


def mp2_seed(P, exc):
    hf = L.hf_det(P["ne"]); seed = {hf}
    for p, q, r, s in zip(exc["p"], exc["q"], exc["r"], exc["s"]):
        d = (hf & ~((1 << p) | (1 << q))) | (1 << r) | (1 << s)
        if bin(d).count("1") == P["ne"]:
            seed.add(d)
    return seed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--atoms", type=int, default=20)
    ap.add_argument("--topm", type=int, default=256)
    ap.add_argument("--grow-iters", type=int, default=40)
    ap.add_argument("--grow-per-iter", type=int, default=100000)
    ap.add_argument("--kcap", type=int, default=1_200_000)
    ap.add_argument("--eps1", type=float, default=1e-4)
    ap.add_argument("--smoke", action="store_true", help="small run vs exact FCI")
    a = ap.parse_args()

    t0 = time.time()
    do_fci = a.smoke or a.atoms <= 10
    P = L.hchain_problem(a.atoms, do_fci=do_fci)
    exc = L.mp2_excitation_lists(P["t2"], P["nocc"], P["nq"], top_m=a.topm)
    seed = mp2_seed(P, exc)
    if do_fci:
        e_ref, ref_kind = P["e_fci"], "FCI (exact)"
    else:
        e_ref, ref_kind = dmrg_reference(P["nq"])
    gi, gpi, kc = (20, 2000, 100000) if a.smoke else (a.grow_iters, a.grow_per_iter, a.kcap)
    print(f"HBCI RUN: H{a.atoms} ({P['nq']}q) | MP2 seed {len(seed)} | eps1={a.eps1} | "
          f"grow {gi}x{gpi} kcap {kc} | ref={ref_kind}", flush=True)

    eng = IntEngine(P["h1"], P["eri"], P["ecore"], P["nq"])
    ckpt_fn = os.path.join(_RES, f"gpu_run1_h{a.atoms}_hbci_PARTIAL.json")

    def _ckpt(it, Ei, nd, ws):
        er = (Ei - e_ref) * 1000
        json.dump(dict(status=f"IN-PROGRESS iter {it}/{gi} (partial, not final)", system=f"H{a.atoms}",
                       qubits=P["nq"], engine="qsci_inc HBCI (integral, eps1 screen)", eps1=a.eps1,
                       iter=it, dets=int(nd), nnz=eng.nnz(), E_qsci=Ei, e_ref=e_ref,
                       err_mHa=round(er, 3), P1_at_iter=bool(abs(er) <= CHEM),
                       qsci_wall_s=round(ws, 1)), open(ckpt_fn, "w"), indent=2)

    E, space = eng.qsci_inc(seed, grow_iters=gi, grow_per_iter=gpi, kcap=kc, hij_floor=0.0,
                            eps1=a.eps1, log=lambda m: print(m, flush=True), ckpt=_ckpt)
    err = (E - e_ref) * 1000
    p1 = abs(err) <= CHEM
    out = dict(run="gpu_run1_hbci", system=f"H{a.atoms}", qubits=P["nq"],
               engine="qsci_inc HBCI (integral engine, eps1 heat-bath candidate screening)",
               eps1=a.eps1, seed="MP2", E_qsci=E, e_ref=e_ref, ref_kind=ref_kind,
               err_mHa=round(err, 3), final_dets=int(len(space)), nnz=eng.nnz(),
               peak_host_rss_gb=round(L.peak_rss_gb(), 2), wall_s=round(time.time() - t0, 1),
               prereg=dict(P1_chem_acc=bool(p1)))
    fn = f"gpu_run1_h{a.atoms}_hbci_evidence.json"
    json.dump(out, open(os.path.join(_RES, fn), "w"), indent=2)
    if os.path.exists(ckpt_fn) and not a.smoke: os.remove(ckpt_fn)
    print(f"\nHBCI H{a.atoms}: E={E:.6f} vs {ref_kind} -> {err:+.3f} mHa | {len(space)} dets | "
          f"nnz={eng.nnz()} | P1={'PASS' if p1 else 'FAIL'} | {time.time()-t0:.0f}s -> results/{fn}", flush=True)


if __name__ == "__main__":
    main()
