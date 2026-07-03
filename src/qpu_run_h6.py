"""QPU RUN (prereg P5): real-hardware QSCI determinant selection — H6, 12 qubits, IonQ/IBM via qBraid.

Flight protocol (fixed pre-hardware; prereg P5 threshold UNCHANGED): THREE pooled submissions
totalling >= 10,000 shots on the same 36-excitation wire set — job 1 with fixed MP2 first-order
angles, jobs 2-3 with reproducibly SEEDED random angles (rng seed 7). Rationale is our own committed
evidence: at low shot budgets diffuse circuits maximize determinant COVERAGE (the measured-random
finding), and QSCI needs coverage, not optimal angles. Pre-flight on the noiseless simulator this
protocol reaches +1.5 mHa (3.4x headroom under the 5 mHa threshold); single-job MP2-only reached
only ~16 mHa and was rejected BEFORE hardware. No on-device optimization; bitstrings post-selected
to the correct electron number; H diagonalized classically in the sampled subspace.

Pre-registered pass/fail (P5): |E_QSCI - FCI| <= 5 mHa. Raw counts are saved and committed REGARDLESS
of pass/fail.

Dry run today (CPU, identical code path):  python src/qpu_run_h6.py --target qpp-cpu
Noisy rehearsal (CPU density matrix):      python src/qpu_run_h6.py --target density-matrix-cpu --depol 0.01
On qBraid hardware (examples; exact target string per qBraid docs at run time):
    python src/qpu_run_h6.py --target ionq [--machine <name>] --shots 10000
    python src/qpu_run_h6.py --target quantinuum --shots 10000
EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cudaq
import qsci_lib as L

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default=os.environ.get("CUDAQ_TARGET_QPU", "qpp-cpu"))
    ap.add_argument("--machine", default=None, help="hardware machine name if the target needs one")
    ap.add_argument("--shots", type=int, default=10000)
    ap.add_argument("--topm", type=int, default=36, help="excitations kept (controls 2q-gate depth)")
    ap.add_argument("--seed", type=int, default=7, help="frozen RNG seed for the diversifier jobs")
    ap.add_argument("--depol", type=float, default=0.0, help="rehearsal-only depolarizing rate")
    a = ap.parse_args()

    t0 = time.time()
    P = L.hchain_problem(6)                     # 12 qubits, exact FCI reference
    exc = L.mp2_excitation_lists(P["t2"], P["nocc"], P["nq"], top_m=a.topm)
    n2q = 13 * len(exc["th"])                   # double_excitation_opt ~= 13 CNOTs each (upper bound)
    print(f"QPU RUN: H6 12q | target={a.target} shots={a.shots} | {len(exc['th'])} excitations "
          f"(~{n2q} two-qubit gates) | fixed MP2 angles, no on-device optimization", flush=True)

    if a.machine:
        cudaq.set_target(a.target, machine=a.machine)
        tgt = None
    else:
        tgt = a.target
    nm = None
    if a.depol > 0:
        from cudaq_noise import noise_model
        nm = noise_model(a.depol)
    import numpy as np
    rng = np.random.default_rng(a.seed)
    jobs = [dict(exc),
            dict(exc, th=list(rng.uniform(-1.2, 1.2, len(exc["th"])))),
            dict(exc, th=list(rng.uniform(-1.2, 1.2, len(exc["th"]))))]
    per = a.shots // 3
    dets = {}; nraw = 0
    for jn, jexc in enumerate(jobs, 1):
        dj, nr = L.sample_dets(P["nq"], P["ne"], jexc, shots=per, target=tgt, noise_model=nm)
        nraw += nr
        for d, c in dj.items(): dets[d] = dets.get(d, 0) + c
        print(f"  job {jn}/3 ({'MP2 angles' if jn == 1 else 'seeded random'}): "
              f"+{len(dj)} dets ({per} shots)", flush=True)
    kept = sum(dets.values())
    print(f"  pooled: {len(dets)} number-conserving dets "
          f"({kept}/{3*per} shots kept after post-selection)", flush=True)

    eng = L.PauliEngine(P["qop"].terms)
    E, space = eng.qsci(set(dets) | {L.hf_det(P["ne"])})          # pure sampled subspace (the P5 claim)
    Eg, _ = eng.qsci(set(dets) | {L.hf_det(P["ne"])}, grow_iters=3, grow_per_iter=200)  # secondary
    err = (E - P["e_fci"]) * 1000
    p5 = abs(err) <= 5.0
    out = dict(run="qpu_run_h6", qubits=12, target=a.target, machine=a.machine, shots=a.shots,
               protocol="3 pooled jobs: MP2 angles + 2 seeded-random (seed=%d); threshold per prereg P5" % a.seed,
               excitations=len(exc["th"]), two_qubit_gate_upper_bound=n2q,
               raw_bitstrings=int(nraw), postselected_shots=int(kept),
               raw_counts={str(k): v for k, v in sorted(dets.items(), key=lambda kv: -kv[1])},
               E_qsci_sampled=E, E_qsci_grown=Eg, e_fci=P["e_fci"],
               err_sampled_mHa=round(err, 3), err_grown_mHa=round((Eg - P["e_fci"]) * 1000, 3),
               prereg=dict(P5_within_5mHa=bool(p5)),
               wall_s=round(time.time() - t0, 1),
               note="3-job pooled protocol (MP2 + 2 seeded-random angles), no on-device optimization, "
                    "post-selection on electron number; raw counts committed regardless (prereg P5).")
    fn = f"qpu_run_h6_{a.target.replace('-','')}_evidence.json"
    json.dump(out, open(os.path.join(_RES, fn), "w"), indent=2)
    print(f"\nQPU RUN H6: sampled-subspace {err:+.3f} mHa (P5<=5: {'PASS' if p5 else 'FAIL'}) | "
          f"grown {(Eg-P['e_fci'])*1000:+.3f} mHa | {time.time()-t0:.0f}s -> results/{fn}", flush=True)


if __name__ == "__main__":
    main()
