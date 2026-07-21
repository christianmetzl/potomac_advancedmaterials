"""E4 STEP 2 — Sn2O2 bridged tin-oxo QSCI at CAS(18,19) = 38 qubits (frozen protocol, prereg_v2).

EUV chemistry at industrial scale: the real bridged Sn-O-Sn motif, judged against the STEP 1
reference committed BEFORE this run (results/sn2o2_cas19_dmrg_reference.json — block2 DMRG chi=400
in the IDENTICAL CAS-embedded integrals, the exact CrO/P4 provenance pattern).

Integrals: e1_chi800_counteraudit.sn2o2_integrals — the SAME extraction path that produced the
committed reference (RHF def2-SVP + def2-ECP on Sn, level_shift convergence aid, CASCI
get_h1eff/get_h2eff, non-DF exact 2e integrals). The qubit operator is built from those integrals
with qsci_lib's own _qop_from_spatial (the committed spinorb/JW convention) — reference and QSCI
provably see the same Hamiltonian.

Frozen config (mirrors B2/CrO): HF-seeded qsci_fast, GROW_PER_ITER=40,000, KCAP=500,000.
Frozen judge: |E_QSCI - E_DMRG(chi=400, same CAS)| <= 1.6 mHa; if E_QSCI < E_DMRG - 0.2 mHa the
variational ordering is reported alongside the metric FAIL exactly as in the CrO/B2 disclosure.
Reported as-is, either way; nothing tuned after seeing results.

Smoke (container CPU): python src/e4_sn2o2_38q.py --smoke 6   (CAS(?,6) toy, exact-diag judge)
Production:            python src/e4_sn2o2_38q.py             (env: GROW_ITERS/STATE_FILE)
EIGENNEXUS - GIC 2026 Phase 3, extension E4 STEP 2.
"""
import os, sys, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import qsci_lib as L
import e1_chi800_counteraudit as e1

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CHEM = 1.6
GROW_PER_ITER = 40_000             # frozen (B2 mirror)
KCAP = 500_000                     # frozen (B2 mirror)
GROW_ITERS = int(os.environ.get("GROW_ITERS", 80))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", type=int, default=0, help="toy ncas with exact-diagonalization judge")
    a = ap.parse_args()
    t0 = time.time()
    ncas = a.smoke if a.smoke else 19

    P = e1.sn2o2_integrals(ncas)
    qop = L._qop_from_spatial(P["h1"], P["eri"], P["ecore"])
    nq = 2 * ncas
    print(f"E4.2: Sn2O2 {P['active_space']} = {nq}q | rhf_conv={P['rhf_converged']} | "
          f"{len(qop.terms)} Pauli terms [{time.time()-t0:.0f}s]", flush=True)

    if a.smoke:
        from pyscf import fci
        e_exact = float(fci.direct_spin1.kernel(P["h1"], P["eri"], ncas, (P["na"], P["nb"]),
                                                ecore=P["ecore"], max_cycle=300)[0])
        eng = L.PauliEngine(qop.terms)
        E, space = eng.qsci_fast({L.hf_det(P["na"], P["nb"])}, grow_iters=40, grow_per_iter=200,
                                 kcap=10**6, log=lambda m: print(m, flush=True))
        print(f"E4 SMOKE CAS({P['na']+P['nb']},{ncas}): E={E:.8f} vs exact {e_exact:.8f} -> "
              f"{abs(E-e_exact)*1e3:.4f} mHa, dets={len(space)} [{time.time()-t0:.0f}s]", flush=True)
        return

    rf = os.path.join(_RES, "sn2o2_cas19_dmrg_reference.json")
    if not os.path.exists(rf):
        raise SystemExit("E4.2 REFUSED: committed STEP 1 reference missing (sn2o2_cas19_dmrg_reference.json)")
    rd = json.load(open(rf))
    e_ref = float(rd["E_dmrg"])
    print(f"  judge: block2 DMRG(chi={rd.get('dmrg_chi', rd.get('chi'))}) same CAS, committed pre-run: "
          f"E={e_ref:.8f}", flush=True)

    eng = L.PauliEngine(qop.terms)
    state_fn = os.environ.get("STATE_FILE", os.path.join(_RES, "e4_sn2o2_state.npz"))
    ckpt_fn = os.path.join(_RES, "e4_sn2o2_PARTIAL.json")
    trace = []

    def _ckpt(it, Ei, nd, ws):
        er = (Ei - e_ref) * 1000
        trace.append(dict(iter=it, dets=int(nd), E=Ei, err_mHa=round(er, 3)))
        try:
            json.dump(dict(status=f"IN-PROGRESS iter {it}/{GROW_ITERS} (partial, not final)",
                           run="e4_sn2o2_38q", trace=trace), open(ckpt_fn, "w"), indent=2)
        except OSError as e:
            print(f"  WARNING: checkpoint flush failed ({e}); run continues", flush=True)

    E, space = eng.qsci_fast({L.hf_det(P["na"], P["nb"])}, grow_iters=GROW_ITERS,
                             grow_per_iter=GROW_PER_ITER, kcap=KCAP,
                             log=lambda m: print(m, flush=True), ckpt=_ckpt, state_file=state_fn)
    err = (E - e_ref) * 1000
    p_metric = abs(err) <= CHEM
    below = E < e_ref - 0.2e-3
    out = dict(run="e4_sn2o2_38q", system=P["system"], active_space=P["active_space"], qubits=nq,
               geometry=P.get("geometry"), E_qsci=E, e_ref=e_ref,
               ref_kind="block2 DMRG(chi=400) same CAS, committed pre-run (STEP 1)",
               err_mHa=round(err, 3), final_space=int(len(space)),
               engine="qsci_fast (incremental Hamiltonian, Option C) — identical committed engine",
               peak_host_rss_gb=round(L.peak_rss_gb(), 2), wall_s=round(time.time() - t0, 1),
               growth_trace=trace,
               prereg=dict(E4_metric_chem_acc=bool(p_metric),
                           ordering_disclosure=("E_QSCI < E_DMRG - 0.2 mHa: variational ordering "
                                                "reported (QSCI provably closer to exact), mirroring "
                                                "the CrO/B2 disclosure" if below else None)))
    fn = os.path.join(_RES, "e4_sn2o2_38q_evidence.json")
    json.dump(out, open(fn, "w"), indent=2)
    if os.path.exists(ckpt_fn): os.remove(ckpt_fn)
    print(f"\nE4.2 Sn2O2 38q: E={E:.6f} vs same-CAS DMRG -> {err:+.3f} mHa | dets={len(space)} | "
          f"metric={'PASS' if p_metric else 'FAIL'}{' + BELOW-REFERENCE ordering' if below else ''} | "
          f"{out['wall_s']}s", flush=True)
    print(f"saved {os.path.relpath(fn)}", flush=True)


if __name__ == "__main__":
    main()
