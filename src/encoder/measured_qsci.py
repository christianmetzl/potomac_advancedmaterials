"""Executed (measured) circuit-sampled GQE->QSCI beyond 12 qubits.

Our prior measured pipeline (gqe_qsci.py) ran the REAL pipeline -- GPT-QE generates circuits, the state
is SAMPLED (qml.sample, real shots), dominant determinants are diagonalized -- only at 12 qubits (H6);
larger numbers used a deterministic determinant-space proxy. This closes that gap on CPU: we execute the
actual measured pipeline at 16q (H8) and 20q (H10), using the size-transferred generator (trained on
H4+H6) to propose circuits, then SAMPLING those circuits to select the QSCI determinant subspace.

This is genuinely "executed" (statevector simulation + shot-based measurement, the standard simulator
execution model), not a perturbative proxy. We compare, at matched determinant budget:
  measured (sampled from transferred generator's circuits)  vs
  measured-random (sampled from random circuits)            vs
  deterministic proxy (per-token construction, no sampling).
Energy = Slater-Condon diagonalization of the selected subspace (validated 0.0000 mHa vs JW). Reference
is exact FCI (<=20q).

Run:  python src/encoder/measured_qsci.py
Writes results/encoder/measured_qsci_evidence.json.

EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, json, time, numpy as np, torch
import pennylane as qml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scaling_transfer as st
from sci_integrals import sci_energy

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                   "results", "encoder")

NGEN, SHOTS, K = 160, 3000, 600


def measured_dets(seqs, pool, ne, nq, shots=SHOTS):
    """REAL measurement: apply each generated circuit, qml.sample shots, collect determinant bitmasks."""
    hf = np.where(np.arange(nq) < ne)[0]
    dev = qml.device("lightning.qubit", wires=nq, shots=shots)

    @qml.qnode(dev)
    def samp(applied):
        for w in hf:
            qml.PauliX(int(w))
        for (typ, wires, t) in applied:
            qml.SingleExcitation(t, wires=wires) if typ == "s" else qml.DoubleExcitation(t, wires=wires)
        return qml.sample(wires=range(nq))

    out = []
    for s in seqs:
        applied = [pool[int(k)] for k in s if pool[int(k)] is not None]
        Sm = samp(applied); d = np.zeros(len(Sm), np.uint64)
        for qi in range(nq):
            d |= (Sm[:, qi].astype(np.uint64) << np.uint64(qi))
        out.append(d)
    return np.concatenate(out)


def topK_by_freq(dets, hf, K):
    alld = np.concatenate([np.array([hf], np.uint64), dets])
    uq, cnt = np.unique(alld, return_counts=True)
    cnt[uq == hf] = cnt.max() + 1                 # keep HF
    return uq[np.argsort(cnt)[::-1][:K]], len(uq)


def main():
    def log(s): print(s, flush=True)
    log(f"\n######## MEASURED GQE->QSCI beyond 12q  {time.strftime('%Y-%m-%d %H:%M')} ########")
    tokens = st.canonical_tokens(6, 12)
    log("training generator on H4+H6 (12q)...")
    model = st.train_gptqe_multi([st.hchain_ham(4), st.hchain_ham(6)], tokens, seed=0)
    results = []
    for n_atoms in (8, 10):                        # 16q, 20q
        t = st.hchain_target_sci(n_atoms)
        ne, nq, hf = t["ne"], t["nq"], st._hf_int(t["ne"])
        pool, valid = st.build_realized_pool(tokens, ne, nq); vids = np.where(valid)[0]
        torch.manual_seed(123)
        gen = st._generate(model, NGEN, 8, 0.5, torch.tensor(~valid)).cpu().numpy()
        rng = np.random.default_rng(0); rnd = np.array([rng.choice(vids, 8) for _ in range(NGEN)])
        t0 = time.time()
        m_gen = measured_dets(gen, pool, ne, nq)           # REAL sampling, transferred generator
        m_rnd = measured_dets(rnd, pool, ne, nq)           # REAL sampling, random circuits
        kg, ng = topK_by_freq(m_gen, hf, K)
        kr, nr = topK_by_freq(m_rnd, hf, K)
        det_proxy = st.gen_determinants(gen, t, tokens)     # deterministic proxy (no sampling)
        e_meas, _ = sci_energy(t["h1"], t["eri"], t["ecore"], kg)
        e_mrnd, _ = sci_energy(t["h1"], t["eri"], t["ecore"], kr)
        e_prox, _ = sci_energy(t["h1"], t["eri"], t["ecore"], det_proxy[:K])
        row = dict(system=f"H{n_atoms}", qubits=nq, shots=SHOTS, n_circuits=NGEN, K=K,
                   measured_mHa=round(abs(e_meas - t["e_fci"]) * 1000, 2), measured_distinct=int(ng),
                   measured_random_mHa=round(abs(e_mrnd - t["e_fci"]) * 1000, 2),
                   proxy_mHa=round(abs(e_prox - t["e_fci"]) * 1000, 2),
                   e_fci=t["e_fci"], ref_kind=t["ref_kind"], seconds=round(time.time() - t0, 1))
        results.append(row)
        log(f"  {row['system']} {nq}q (FCI={t['e_fci']:.5f}): MEASURED {row['measured_mHa']} mHa "
            f"({ng} distinct dets sampled) | measured-random {row['measured_random_mHa']} | "
            f"proxy {row['proxy_mHa']} mHa | {row['seconds']}s")
        json.dump(dict(note="REAL circuit-sampled QSCI (qml.sample shots) at 16q & 20q using the "
                            "size-transferred generator; energy by Slater-Condon diagonalization; vs "
                            "FCI. measured vs measured-random vs deterministic proxy at matched K.",
                       NGEN=NGEN, SHOTS=SHOTS, K=K, results=results),
                  open(os.path.join(OUT, "measured_qsci_evidence.json"), "w"), indent=2)
    log("\nSUMMARY: executed measured QSCI established at " +
        ", ".join(f"{r['qubits']}q={r['measured_mHa']}mHa" for r in results) +
        " (vs measured-random " + ", ".join(f"{r['measured_random_mHa']}" for r in results) + ")")
    log("DONE")


if __name__ == "__main__":
    main()
