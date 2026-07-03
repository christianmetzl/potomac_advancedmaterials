"""Cloud-executed QSCI validation on qBraid's hosted simulator (free tier) — beyond 12 qubits.

Runs the flight protocol (MP2-angle circuit + 2 seeded-random diversifiers, pooled) THROUGH the
qBraid hosted runtime (qbraid:qbraid:sim:qir-sv, 30-qubit cap, 2000 shots/job, 0 credits) at
Hn sizes up to 28 qubits, then diagonalizes the sampled subspace classically (QSCI) and reports
vs FCI. Also reports the device-seeded CIPSI-grown energy (sampling seeds selection; selected-CI
refines — the committed GQE->QSCI narrative).

Faithfulness discipline (same as qbraid_submit.py): gate-by-gate qiskit export; the exact submitted
artifact is verified against the native circuit by statevector (L1<0.01) up to 24 qubits; at 28q the
exact check is skipped for memory and the identical code path + dominant==HF assertion stand in
(disclosed in the evidence JSON).

Usage:  python src/qbraid_hosted_validation.py --atoms 10          # 20q, free
        python src/qbraid_hosted_validation.py --atoms 12          # 24q, free
EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pennylane as qml
import qsci_lib as L

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
SEED = 7


def build_export(nq, ne, exc, angles, verify):
    """Decompose -> gate-by-gate qiskit -> qasm2; exact-artifact verification when verify=True."""
    from qiskit import QuantumCircuit, qasm2
    ELEM = {"CNOT", "RY", "RZ", "RX", "Hadamard", "PauliX", "S", "Adjoint(S)", "T", "Adjoint(T)", "CZ", "PhaseShift"}
    ops = [qml.PauliX(i) for i in range(ne)]
    for (p, q_, r, s, th) in zip(exc["p"], exc["q"], exc["r"], exc["s"], angles):
        ops.append(qml.DoubleExcitation(th, wires=[p, q_, r, s]))
    tape = qml.tape.QuantumScript(ops, [qml.sample(wires=range(nq))])
    [dt], _ = qml.transforms.decompose([tape], gate_set=set(ELEM))
    qc = QuantumCircuit(nq, nq)
    for op in dt.operations:
        w = [int(x) for x in op.wires]; pr = [float(x) for x in op.parameters]; n = op.name
        if   n == "PauliX":     qc.x(w[0])
        elif n == "Hadamard":   qc.h(w[0])
        elif n == "CNOT":       qc.cx(w[0], w[1])
        elif n == "CZ":         qc.cz(w[0], w[1])
        elif n == "RY":         qc.ry(pr[0], w[0])
        elif n == "RZ":         qc.rz(pr[0], w[0])
        elif n == "RX":         qc.rx(pr[0], w[0])
        elif n == "S":          qc.s(w[0])
        elif n == "Adjoint(S)": qc.sdg(w[0])
        elif n == "T":          qc.t(w[0])
        elif n == "Adjoint(T)": qc.tdg(w[0])
        elif n == "PhaseShift": qc.p(pr[0], w[0])
        else: raise ValueError(f"unmapped gate {n}")
    qasm = qasm2.dumps(qc)
    l1 = None
    if verify:
        from qiskit.quantum_info import Statevector
        pb = np.abs(np.asarray(Statevector.from_instruction(qasm2.loads(qasm)))) ** 2
        @qml.qnode(qml.device("default.qubit", wires=nq))
        def native():
            for i in range(ne): qml.PauliX(i)
            for (pp, qq, rr, ss, th) in zip(exc["p"], exc["q"], exc["r"], exc["s"], angles):
                qml.DoubleExcitation(th, wires=[pp, qq, rr, ss])
            return qml.probs(wires=range(nq))
        pa = np.asarray(native())
        def nat_det(i):
            bits = format(i, f"0{nq}b")
            return sum(1 << k for k, ch in enumerate(bits) if ch == "1")
        da = {nat_det(i): float(pa[i]) for i in np.where(pa > 1e-6)[0]}
        db = {int(i): float(pb[i]) for i in np.where(pb > 1e-6)[0]}
        l1 = sum(abs(da.get(d, 0) - db.get(d, 0)) for d in set(da) | set(db))
        if l1 >= 0.01:
            raise RuntimeError(f"export unfaithful: L1={l1:.4f}")
    return qasm + "\n" + "\n".join(f"measure q[{i}] -> c[{i}];" for i in range(nq)), l1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--atoms", type=int, default=10)
    ap.add_argument("--device", default="qbraid:qbraid:sim:qir-sv")
    ap.add_argument("--shots-per-job", type=int, default=2000)
    ap.add_argument("--topm", type=int, default=64)
    a = ap.parse_args()

    t0 = time.time()
    P = L.hchain_problem(a.atoms, do_fci=(a.atoms <= 10))
    nq, ne = P["nq"], P["ne"]
    verify = nq <= 24
    print(f"HOSTED VALIDATION: H{a.atoms} ({nq}q) on {a.device} | 3 jobs x {a.shots_per_job} shots | "
          f"exact export verification: {verify}", flush=True)
    exc = L.mp2_excitation_lists(P["t2"], P["nocc"], nq, top_m=a.topm)
    rng = np.random.default_rng(SEED)
    angle_sets = [list(exc["th"]),
                  list(rng.uniform(-1.2, 1.2, len(exc["th"]))),
                  list(rng.uniform(-1.2, 1.2, len(exc["th"])))]

    from qbraid import QbraidProvider
    dev = QbraidProvider().get_device(a.device)
    LEX = sorted(range(nq), key=str)
    def decode(bits): return sum(1 << LEX[k] for k, ch in enumerate(bits) if ch == "1")

    pool, ids = {}, []
    for jn, angles in enumerate(angle_sets, 1):
        qasm, l1 = build_export(nq, ne, exc, angles, verify)
        job = dev.run(qasm, shots=a.shots_per_job)
        ids.append(job.id)
        counts = job.result().data.get_counts()
        add = 0
        for bits, c in counts.items():
            d = decode(bits)
            if bin(d).count("1") == ne:
                pool[d] = pool.get(d, 0) + c; add += 1
        print(f"  job {jn}/3 ({'MP2' if jn == 1 else 'random'}"
              + (f", L1={l1:.5f}" if l1 is not None else ", exact-verify skipped (28q memory)")
              + f"): +{add} number-conserving dets | {job.id[-14:]}", flush=True)

    hf = L.hf_det(ne)
    dom = max(pool, key=pool.get)
    assert dom == hf, f"dominant {dom:0{nq}b} != HF — decode anomaly"
    eng = L.PauliEngine(P["qop"].terms)
    E, sp = eng.qsci(set(pool) | {hf})
    Eg, spg = eng.qsci(set(pool) | {hf}, grow_iters=10, grow_per_iter=400, kcap=6000,
                       log=lambda m: print(m, flush=True))
    ref = P["e_fci"]
    out = dict(run="qbraid_hosted_validation", system=f"H{a.atoms}", qubits=nq, device=a.device,
               shots_per_job=a.shots_per_job, top_m=len(exc["th"]), job_ids=ids,
               pooled_dets=len(pool), export_exact_verified=bool(verify),
               E_sampled=E, E_grown=Eg, e_fci=ref,
               err_sampled_mHa=(round(1000 * (E - ref), 3) if ref else None),
               err_grown_mHa=(round(1000 * (Eg - ref), 3) if ref else None),
               grown_dets=int(len(spg)), wall_s=round(time.time() - t0, 1),
               note="executed through the qBraid hosted runtime (free tier). Sampled-subspace = pure "
                    "device-selected QSCI; grown = device-seeded selected-CI (the committed GQE->QSCI "
                    "narrative). 2000-shot/job free-tier cap limits coverage at this scale — honest scope.")
    fn = f"qbraid_hosted_h{a.atoms}_evidence.json"
    json.dump(out, open(os.path.join(_RES, fn), "w"), indent=2)
    if ref:
        print(f"\nH{a.atoms} ({nq}q) CLOUD-EXECUTED: sampled {1000*(E-ref):+.2f} mHa | "
              f"device-seeded grown {1000*(Eg-ref):+.3f} mHa ({len(spg)} dets) | {time.time()-t0:.0f}s "
              f"-> results/{fn}", flush=True)
    else:
        print(f"\nH{a.atoms} ({nq}q) CLOUD-EXECUTED: E_sampled={E:.6f}, E_grown={Eg:.6f} "
              f"(no FCI ref at this size) -> results/{fn}", flush=True)


if __name__ == "__main__":
    main()
