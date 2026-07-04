"""GPU RUN 4 (prereg P4): CrO open-shell QSCI at large CAS — up to CAS(19,19) = 38 qubits.

Two halves:
  (a) --make-ref : block2 DMRG reference in the SAME active space (CPU — can run BEFORE GPU access;
      the committed reference is what P4 is judged against).
  (b) the QSCI run: HF-seeded + perturbatively grown determinant subspace on the CAS Hamiltonian
      (device sampling optional via --sample-target once GPU/QPU credits exist; the selection
      principle is identical either way, per the committed proxy-vs-measured validation).

Pre-registered pass/fail (P4, labeled lowest-confidence): |E_QSCI - E_DMRG(same CAS)| <= 1.6 mHa.

Smoke test (CPU, run today — reproduces the committed 20q result):
    python src/gpu_run4_cro38q.py --ncas 10 --solve-casci
Reference for the 38q target (CPU, run today):
    python src/gpu_run4_cro38q.py --ncas 19 --make-ref
Production QSCI at 38q (qBraid, CPU-heavy diagonalization + optional GPU sampling):
    python src/gpu_run4_cro38q.py --ncas 19 --grow-iters 80 --kcap 500000
EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import qsci_lib as L

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
ATOM = "Cr 0 0 0; O 0 0 1.621"          # CrO 5-Pi quintet, matching the committed 20q pipeline
SPIN = 4
CHEM = 1.6


def nelecas_for(ncas):
    """Quintet CrO active spaces (4 unpaired -> n_elec must share parity with SPIN=4, i.e. be even).
    Committed CAS(10,10) uses (7,3); for odd ncas use n_elec = ncas-1 (e.g. CAS(18,19) = 38 qubits)."""
    nel = ncas if ncas % 2 == 0 else ncas - 1
    na = (nel + SPIN) // 2
    return (na, nel - na)


def make_ref(ncas, chi=400):
    """block2 DMRG in the same CAS — the committed reference the GPU QSCI is judged against."""
    from pyblock2.driver.core import DMRGDriver, SymmetryTypes
    P = L.cas_problem(ATOM, "def2-svp", SPIN, ncas, nelecas_for(ncas))
    # DMRG on the IDENTICAL CAS-embedded integrals the QSCI sees -> perfectly matched reference
    na, nb = P["na"], P["nb"]
    driver = DMRGDriver(scratch=f"/tmp/dmrg_cro{ncas}", symm_type=SymmetryTypes.SU2, n_threads=4)
    driver.initialize_system(n_sites=ncas, n_elec=na + nb, spin=na - nb, orb_sym=None)
    mpo = driver.get_qc_mpo(h1e=P["h1"], g2e=P["eri"], ecore=P["ecore"], iprint=0)
    ket = driver.get_random_mps(tag="CRO", bond_dim=min(chi, 100), nroots=1)
    t0 = time.time()
    e = driver.dmrg(mpo, ket, n_sweeps=8, bond_dims=[100, 150, 200, chi, chi, chi, chi, chi],
                    noises=[1e-4, 1e-5, 1e-6, 1e-7, 0, 0, 0, 0], thrds=[1e-8] * 8, iprint=0)
    out = dict(system="CrO 5-Pi", active_space=f"CAS({sum(nelecas_for(ncas))},{ncas})",
               qubits=2 * ncas, dmrg_chi=chi, E_dmrg=float(e),
               rohf_converged=P["rohf_converged"], wall_s=round(time.time() - t0, 1),
               note="block2 DMRG reference in the SAME CAS; committed BEFORE the GPU QSCI run (prereg P4).")
    fn = f"cro_cas{ncas}_dmrg_reference.json"
    json.dump(out, open(os.path.join(_RES, fn), "w"), indent=2)
    print(f"DMRG(chi={chi}) CAS({sum(nelecas_for(ncas))},{ncas}) = {e:.6f} Ha "
          f"[{time.time()-t0:.0f}s] -> results/{fn}", flush=True)
    return float(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ncas", type=int, default=19)
    ap.add_argument("--make-ref", action="store_true")
    ap.add_argument("--chi", type=int, default=400)
    ap.add_argument("--solve-casci", action="store_true", help="exact CASCI ref (small CAS smoke only)")
    ap.add_argument("--grow-iters", type=int, default=40)
    ap.add_argument("--grow-per-iter", type=int, default=40000)   # Option C: big batches (fast engine)
    ap.add_argument("--kcap", type=int, default=800000)
    a = ap.parse_args()

    if a.make_ref:
        make_ref(a.ncas, a.chi); return

    t0 = time.time()
    nel = nelecas_for(a.ncas)
    print(f"RUN4: CrO CAS({sum(nel)},{a.ncas}) = {2*a.ncas}q, nelecas={nel}", flush=True)
    P = L.cas_problem(ATOM, "def2-svp", SPIN, a.ncas, nel, solve_casci=a.solve_casci)
    print(f"  ROHF conv={P['rohf_converged']} | {len(P['qop'].terms)} Pauli terms "
          f"[{time.time()-t0:.0f}s]", flush=True)

    if a.solve_casci and P["e_ref"] is not None:
        e_ref, ref_kind = P["e_ref"], "CASCI (exact)"
    else:
        fn = os.path.join(_RES, f"cro_cas{a.ncas}_dmrg_reference.json")
        if not os.path.exists(fn):
            raise SystemExit(f"run --make-ref first (missing {fn})")
        d = json.load(open(fn)); e_ref, ref_kind = d["E_dmrg"], f"block2 DMRG(chi={d['dmrg_chi']}), same CAS"

    eng = L.PauliEngine(P["qop"].terms)
    devmon = L.DeviceMemMonitor().start()
    ckpt_fn = os.path.join(_RES, f"gpu_run4_cas{a.ncas}_PARTIAL.json")
    def _ckpt(it, Ei, nd, ws):                  # durable per-iteration artifact (ephemeral instance)
        er = (Ei - e_ref) * 1000
        json.dump(dict(status=f"IN-PROGRESS iter {it}/{a.grow_iters} (partial, not final)",
                       active_space=f"CAS({sum(nel)},{a.ncas})", qubits=2 * a.ncas, iter=it,
                       dets=int(nd), E_qsci=Ei, e_ref=e_ref, err_mHa=round(er, 3),
                       P4_at_iter=bool(abs(er) <= CHEM), qsci_wall_s=round(ws, 1)),
                  open(ckpt_fn, "w"), indent=2)
    E, space = eng.qsci_fast({L.hf_det(P["na"], P["nb"])}, grow_iters=a.grow_iters,
                             grow_per_iter=a.grow_per_iter, kcap=a.kcap,
                             log=lambda m: print(m, flush=True), ckpt=_ckpt)
    devmon.stop()
    if os.path.exists(ckpt_fn): os.remove(ckpt_fn)
    err = (E - e_ref) * 1000
    p4 = abs(err) <= CHEM
    dev_mem = devmon.gb()
    out = dict(run="gpu_run4", system="CrO 5-Pi", active_space=f"CAS({sum(nel)},{a.ncas})",
               qubits=2 * a.ncas, E_qsci=E, e_ref=e_ref, ref_kind=ref_kind, err_mHa=round(err, 3),
               final_space=int(len(space)), peak_host_rss_gb=round(L.peak_rss_gb(), 2),
               peak_device_mem_gb=dev_mem, engine="qsci_fast (incremental Hamiltonian, Option C)",
               wall_s=round(time.time() - t0, 1), prereg=dict(P4_chem_acc=bool(p4)))
    fn = f"gpu_run4_cas{a.ncas}_evidence.json"
    json.dump(out, open(os.path.join(_RES, fn), "w"), indent=2)
    print(f"\nRUN4 CAS({sum(nel)},{a.ncas}): {err:+.3f} mHa vs {ref_kind} | dets={len(space)} | "
          f"P4={'PASS' if p4 else 'FAIL'} | {time.time()-t0:.0f}s -> results/{fn}", flush=True)


if __name__ == "__main__":
    main()
