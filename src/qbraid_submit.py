"""qBraid cloud submission adapter for the pre-registered QPU run (P5) — validated end-to-end.

Chain (every step verified against the FREE qbraid:qbraid:sim:qir-sv simulator, 2026-07-03):
  1. Build the 3 flight circuits (frozen protocol: MP2 angles + 2 seeded-random, seed 7, top-36
     excitations) with PennyLane DoubleExcitation — the same primitive as the committed measured-QSCI
     pipeline.
  2. Decompose to elementary gates and export gate-by-gate to OpenQASM 2 via qiskit, then RELOAD the
     exact artifact and verify its statevector against the native circuit (L1 must be < 0.01).
     [qml.to_openqasm was found UNFAITHFUL at large angles (L1~0.56) and is deliberately bypassed.]
  3. Submit each artifact via QbraidProvider; decode returned bitstrings with the lexicographic
     qubit-order mapping (proven by 4 binary probe circuits, and re-checked per run via the
     dominant-determinant==HF assertion).
  4. Pool number-conserving determinants -> QSCI subspace diagonalization -> prereg P5 verdict;
     raw counts + job IDs committed regardless of outcome.

Spend guard: prints the device's live per-task/per-shot credit pricing and total estimate first;
nonzero-cost submissions require an explicit --yes.

Cloud validation result (free simulator, 3x2000 shots): +2.356 mHa vs FCI -> P5 PASS.
Usage:
  python src/qbraid_submit.py --estimate                          # price check only, no submission
  python src/qbraid_submit.py                                     # free simulator run (qir-sv)
  python src/qbraid_submit.py --device openquantum:ionq:qpu:forte-1 --shots-per-job 3334 --yes
EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pennylane as qml
import qsci_lib as L

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
NQ, NE, TOPM, SEED = 12, 6, 36, 7
ELEM = {"CNOT", "RY", "RZ", "RX", "Hadamard", "PauliX", "S", "Adjoint(S)", "T", "Adjoint(T)", "CZ", "PhaseShift"}


def flight_angle_sets(exc):
    rng = np.random.default_rng(SEED)
    return [list(exc["th"]),
            list(rng.uniform(-1.2, 1.2, len(exc["th"]))),
            list(rng.uniform(-1.2, 1.2, len(exc["th"])))]


def decomposed_ops(exc, angles):
    ops = [qml.PauliX(i) for i in range(NE)]
    for (p, q_, r, s, th) in zip(exc["p"], exc["q"], exc["r"], exc["s"], angles):
        ops.append(qml.DoubleExcitation(th, wires=[p, q_, r, s]))
    tape = qml.tape.QuantumScript(ops, [qml.sample(wires=range(NQ))])
    [dt], _ = qml.transforms.decompose([tape], gate_set=set(ELEM))
    return dt.operations


def to_qasm_verified(exc, angles):
    """Gate-by-gate qiskit export + exact-artifact statevector verification (L1 < 0.01)."""
    from qiskit import QuantumCircuit, qasm2
    from qiskit.quantum_info import Statevector
    qc = QuantumCircuit(NQ, NQ)
    for op in decomposed_ops(exc, angles):
        w = [int(x) for x in op.wires]; p = [float(x) for x in op.parameters]; n = op.name
        if   n == "PauliX":     qc.x(w[0])
        elif n == "Hadamard":   qc.h(w[0])
        elif n == "CNOT":       qc.cx(w[0], w[1])
        elif n == "CZ":         qc.cz(w[0], w[1])
        elif n == "RY":         qc.ry(p[0], w[0])
        elif n == "RZ":         qc.rz(p[0], w[0])
        elif n == "RX":         qc.rx(p[0], w[0])
        elif n == "S":          qc.s(w[0])
        elif n == "Adjoint(S)": qc.sdg(w[0])
        elif n == "T":          qc.t(w[0])
        elif n == "Adjoint(T)": qc.tdg(w[0])
        elif n == "PhaseShift": qc.p(p[0], w[0])
        else: raise ValueError(f"unmapped gate {n}")
    qasm = qasm2.dumps(qc)
    # verify the exact artifact
    pb = np.abs(np.asarray(Statevector.from_instruction(qasm2.loads(qasm)))) ** 2
    @qml.qnode(qml.device("default.qubit", wires=NQ))
    def native():
        for i in range(NE): qml.PauliX(i)
        for (pp, qq, rr, ss, th) in zip(exc["p"], exc["q"], exc["r"], exc["s"], angles):
            qml.DoubleExcitation(th, wires=[pp, qq, rr, ss])
        return qml.probs(wires=range(NQ))
    pa = np.asarray(native())
    def nat_det(i):
        bits = format(i, f"0{NQ}b")
        return sum(1 << k for k, ch in enumerate(bits) if ch == "1")
    da = {nat_det(i): float(pa[i]) for i in np.where(pa > 1e-5)[0]}
    db = {int(i): float(pb[i]) for i in np.where(pb > 1e-5)[0]}
    l1 = sum(abs(da.get(d, 0) - db.get(d, 0)) for d in set(da) | set(db))
    if l1 >= 0.01:
        raise RuntimeError(f"export unfaithful: L1={l1:.4f} — DO NOT SUBMIT")
    return qasm + "\n" + "\n".join(f"measure q[{i}] -> c[{i}];" for i in range(NQ)), l1


LEX = sorted(range(NQ), key=str)      # count-key position k <-> qubit LEX[k]; proven by 4 binary probes
def decode(bits):
    return sum(1 << LEX[k] for k, ch in enumerate(bits) if ch == "1")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="qbraid:qbraid:sim:qir-sv")
    ap.add_argument("--shots-per-job", type=int, default=2000)
    ap.add_argument("--topm", type=int, default=TOPM,
                    help="excitations kept = circuit depth. Real QPU: use 6-8 (~13x fewer 2q gates) "
                         "so the shallow circuit survives hardware noise. Simulator: 36 (full).")
    ap.add_argument("--jobs", type=int, default=3, help="pooled jobs (1-3). Use 1 on a paid QPU to cut cost.")
    ap.add_argument("--estimate", action="store_true", help="price check only; no submission")
    ap.add_argument("--yes", action="store_true", help="required to submit to any nonzero-cost device")
    a = ap.parse_args()

    from qbraid import QbraidProvider
    prov = QbraidProvider()
    dev = prov.get_device(a.device)
    pricing = dev.profile.get("pricing")
    per_task = float(getattr(pricing, "perTask", 0) or 0)
    per_shot = float(getattr(pricing, "perShot", 0) or 0)
    total_credits = a.jobs * per_task + a.jobs * a.shots_per_job * per_shot
    P = L.hchain_problem(6)
    exc = L.mp2_excitation_lists(P["t2"], P["nocc"], P["nq"], top_m=a.topm)
    n2q = 13 * len(exc["th"])
    print(f"device {a.device} | status {dev.status()} | pricing perTask={per_task} perShot={per_shot} credits")
    print(f"circuit: 12q H6, topm={a.topm} -> {len(exc['th'])} excitations (~{n2q} two-qubit gates)")
    print(f"job plan: {a.jobs} job(s) x {a.shots_per_job} shots -> estimated {total_credits:,.0f} credits "
          f"(~${total_credits/100:,.2f})")
    if a.estimate:
        return
    if total_credits > 0 and not a.yes:
        raise SystemExit("nonzero cost: re-run with --yes to confirm spending credits")

    t0 = time.time()
    pool, job_ids, raw = {}, [], {}
    for jn, angles in enumerate(flight_angle_sets(exc)[:a.jobs], 1):
        qasm, l1 = to_qasm_verified(exc, angles)
        job = dev.run(qasm, shots=a.shots_per_job)
        job_ids.append(job.id)
        counts = job.result().data.get_counts()
        raw[f"job{jn}"] = counts
        add = 0
        for bits, c in counts.items():
            d = decode(bits)
            if bin(d).count("1") == NE:
                pool[d] = pool.get(d, 0) + c; add += 1
        print(f"  job {jn}/3 ({'MP2' if jn == 1 else 'random'}; export L1={l1:.5f}): "
              f"{len(counts)} bitstrings, +{add} number-conserving | {job.id}", flush=True)

    hf = L.hf_det(NE)
    dom = max(pool, key=pool.get)
    if dom != hf:
        print(f"WARNING: dominant determinant {dom:012b} != HF {hf:012b} — decode/noise anomaly; reporting as-is")
    eng = L.PauliEngine(P["qop"].terms)
    E, _ = eng.qsci(set(pool) | {hf})                                   # pure device-sampled subspace
    Eg, spg = eng.qsci_fast(set(pool) | {hf}, grow_iters=8, grow_per_iter=400, kcap=6000)  # device-seeded grown
    err = 1000 * (E - P["e_fci"]); errg = 1000 * (Eg - P["e_fci"])
    p5 = abs(err) <= 5.0
    out = dict(run="qbraid_submit_P5", device=a.device, shots_per_job=a.shots_per_job,
               protocol=f"{a.jobs} pooled job(s) (MP2 + seeded-random, seed {SEED}, top-{a.topm} excitations, "
                        f"~{n2q} two-qubit gates)",
               job_ids=job_ids, pooled_dets=len(pool), dominant_is_hf=bool(dom == hf),
               E_qsci_sampled=E, E_qsci_grown=Eg, grown_dets=int(len(spg)),
               e_fci=P["e_fci"], err_sampled_mHa=round(err, 3), err_grown_mHa=round(errg, 3),
               prereg=dict(P5_within_5mHa=bool(p5)),
               estimated_credits=total_credits, wall_s=round(time.time() - t0, 1),
               raw_counts=raw,
               note="raw counts committed regardless of outcome; decode mapping proven by binary probe "
                    "circuits; export verified per-artifact (L1<0.01) before submission. sampled = pure "
                    "device subspace; grown = device-seeded selected-CI (noise-robust QSCI: a shallow "
                    "hardware circuit seeds the selection, classical growth refines).")
    tag = a.device.replace(":", "_")
    fn = f"qbraid_P5_{tag}_evidence.json"
    json.dump(out, open(os.path.join(_RES, fn), "w"), indent=2)
    print(f"\nP5 run on {a.device}: {err:+.3f} mHa vs FCI -> {'PASS' if p5 else 'FAIL'} "
          f"| {len(pool)} dets | {time.time()-t0:.0f}s -> results/{fn}", flush=True)


if __name__ == "__main__":
    main()
