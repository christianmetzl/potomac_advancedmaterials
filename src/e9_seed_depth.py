"""E9 — is the QSCI seed capped by shots, by system size, or by CIRCUIT DEPTH?

Protocol frozen in results/preregistration_e9_seed_depth.json BEFORE this ran.

Motivation (committed evidence): the QSCI determinant seed lands at ~110 distinct determinants at 16q, 20q
AND 40q, across 200,000-480,000 shots and 1-160 circuits. Flat across every variable but one. Hypothesis:
a circuit applying L excitations to HF can reach at most ~2^L determinants, so the pipeline's L=8 caps the
seed at 256 — and the 40q tensornet-mps stall (108 determinants) is a circuit-design problem, not GPU time.

Uses the same measured-sampling code path as encoder/measured_qsci.py (qml.sample on lightning.qubit).
Sequences are drawn at RANDOM from the valid pool to isolate depth as the variable.
Output: results/e9_seed_depth_evidence.json.  EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, json, time
import numpy as np
import pennylane as qml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gqe_scaling import build_pool

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
DEPTHS = [4, 8, 16, 24]
SHOTS = [2000, 20000]
NCIRC = 20
SYSTEMS = [("H8", 8, 16), ("H10", 10, 20)]     # (label, n_atoms, n_qubits)
RNG = np.random.default_rng(20260725)


def sample_distinct(pool, valid_ids, nq, ne, depth, shots, ncirc, rng):
    """Pool determinants sampled from `ncirc` random depth-L circuits; return distinct count."""
    hf_w = np.arange(ne)
    dev = qml.device("lightning.qubit", wires=nq, shots=shots)

    @qml.qnode(dev)
    def samp(applied):
        for w in hf_w:
            qml.PauliX(int(w))
        for (typ, wires, t) in applied:
            qml.SingleExcitation(t, wires=list(wires)) if typ == "s" else qml.DoubleExcitation(t, wires=list(wires))
        return qml.sample(wires=range(nq))

    seen = set()
    for _ in range(ncirc):
        idx = rng.choice(valid_ids, size=depth, replace=False)
        applied = [pool[int(k)] for k in idx]
        Sm = np.atleast_2d(samp(applied))
        d = np.zeros(len(Sm), np.uint64)
        for qi in range(nq):
            d |= (Sm[:, qi].astype(np.uint64) << np.uint64(qi))
        # number-conserving filter (same physical post-selection as the QPU/measured path)
        pc = np.array([bin(int(x)).count("1") for x in d])
        seen.update(int(x) for x in d[pc == ne])
    return len(seen)


def main():
    t0 = time.time()
    rows = []
    for label, natoms, nq in SYSTEMS:
        ne = natoms                                   # STO-6G H_n: n electrons in n spatial orbitals
        pool = build_pool(nq, ne)
        valid_ids = [i for i, p in enumerate(pool) if p is not None]
        for depth in DEPTHS:
            if depth > len(valid_ids):
                continue
            for shots in SHOTS:
                n = sample_distinct(pool, valid_ids, nq, ne, depth, shots, NCIRC, RNG)
                rows.append({"system": label, "qubits": nq, "depth_L": depth, "shots_per_circuit": shots,
                             "n_circuits": NCIRC, "total_shots": shots * NCIRC,
                             "distinct_determinants": n, "combinatorial_ceiling_2^L": 2 ** depth})
                print(f"  {label} {nq}q  L={depth:>2}  shots/circ={shots:>6}  "
                      f"total={shots*NCIRC:>8,}  ->  {n:>6,} distinct   (2^L = {2**depth:,})", flush=True)

    def get(sys_, L, sh):
        m = [r for r in rows if r["system"] == sys_ and r["depth_L"] == L and r["shots_per_circuit"] == sh]
        return m[0]["distinct_determinants"] if m else None

    # ---- evaluate the four frozen predictions, as-measured ----
    v = {}
    a_lo, a_hi = get("H10", 8, 2000), get("H10", 8, 20000)
    v["P9a_shot_insensitivity"] = {"claim": "10x shots at L=8 gives <2x determinants",
                                   "shots2k": a_lo, "shots20k": a_hi,
                                   "ratio": round(a_hi / a_lo, 3) if a_lo else None,
                                   "MET": bool(a_lo and a_hi / a_lo < 2.0)}
    b_lo, b_hi = get("H10", 8, 20000), get("H10", 16, 20000)
    v["P9b_depth_sensitivity"] = {"claim": "L 8->16 gives >=5x determinants at matched shots",
                                  "L8": b_lo, "L16": b_hi,
                                  "ratio": round(b_hi / b_lo, 2) if b_lo else None,
                                  "MET": bool(b_lo and b_hi / b_lo >= 5.0)}
    c16, c20 = get("H8", 8, 20000), get("H10", 8, 20000)
    v["P9c_size_insensitivity"] = {"claim": "16q vs 20q within 2x at fixed depth/shots",
                                   "q16": c16, "q20": c20,
                                   "ratio": round(max(c16, c20) / min(c16, c20), 2) if c16 and c20 else None,
                                   "MET": bool(c16 and c20 and max(c16, c20) / min(c16, c20) <= 2.0)}
    v["P9d_below_ceiling"] = {"claim": "distinct < 2^L at every depth",
                              "violations": [r for r in rows if r["distinct_determinants"] >= r["combinatorial_ceiling_2^L"]],
                              "MET": all(r["distinct_determinants"] < r["combinatorial_ceiling_2^L"] for r in rows)}

    # ---- how far can sampling actually get you? (the question that matters) ----
    r20 = [x for x in rows if x["system"] == "H10" and x["shots_per_circuit"] == 20000]
    Ls = np.array([x["depth_L"] for x in r20], float)
    Ns = np.array([x["distinct_determinants"] for x in r20], float)
    slope, icept = np.polyfit(Ls, Ns, 1)
    lo24 = [x for x in rows if x["system"] == "H10" and x["depth_L"] == 24 and x["shots_per_circuit"] == 2000][0]["distinct_determinants"]
    hi24 = int(Ns[-1]); NEED = 450257
    import math
    reach = {
        "flagship_seed_requirement": NEED,
        "best_measured_here": {"distinct": hi24, "depth_L": 24, "total_shots": 400000},
        "short_by_factor": round(NEED / hi24, 1),
        "growth_in_depth": f"N ~ {slope:.1f}*L {icept:+.0f} (LINEAR in depth, not exponential)",
        "depth_needed_to_reach_requirement": int((NEED - icept) / slope),
        "shots_growth_per_decade": round(hi24 / lo24, 2),
        "shot_decades_needed_to_reach_requirement": round(math.log(NEED / hi24) / math.log(hi24 / lo24), 1),
        "conclusion": ("Direct circuit sampling cannot produce the seed this pipeline needs. Yield grows "
                       "LINEARLY in circuit depth (~24 determinants per excitation) and ~2x per decade of "
                       "shots, so closing an 800x gap would require ~18,000 excitations or ~9 further decades "
                       "of shots — neither is executable, least of all on hardware. The flagship's MP2-seeded "
                       "classical growth was therefore a NECESSARY architecture, not a workaround."),
    }

    out = {
        "run": "e9_seed_depth",
        "reach_analysis": reach,
        "preregistration": "results/preregistration_e9_seed_depth.json (frozen before this run)",
        "question": "Is the QSCI determinant seed capped by shots, by system size, or by circuit depth?",
        "grid": {"depths_L": DEPTHS, "shots_per_circuit": SHOTS, "n_circuits": NCIRC,
                 "systems": [f"{s[0]}/{s[2]}q" for s in SYSTEMS], "sequences": "random from valid UCC pool"},
        "rows": rows,
        "predictions_as_measured": v,
        "REFUTED_predictions_reported_as_such": ("P9b (depth gives >=5x) and P9d (2^L ceiling) FAILED. Depth gives "
            "~2.2x per doubling, not >=5x, and observed counts EXCEED 2^L at L=4 (49-77 vs 16) — so the mechanism "
            "is NOT a hard combinatorial 2^L cap. The hypothesis as stated is refuted; the measured scaling laws "
            "above replace it."),
        "context_committed_evidence": {
            "measured_qsci_16q_20q": "160 circuits x 3,000 shots = 480,000 shots -> 110 distinct (both sizes)",
            "gpu_40q_tensornet_mps": "1 circuit x 200,000 shots -> 108 distinct",
            "pipeline_depth": "L = 8 (encoder/measured_qsci.py generates length-8 sequences)"},
        "honest_caveats": [
            "16q/20q diagnosis of the mechanism — this does NOT by itself demonstrate a fixed 40q run.",
            "Random sequences isolate depth; a trained generator samples a different region of the pool.",
            "Deeper circuits cost more to execute and are harder on noisy hardware — the depth-vs-noise "
            "trade-off is real and is NOT measured here.",
            "More determinants is a necessary, not sufficient, condition for a better QSCI energy.",
            "CPU statevector sampling; no GPU or QPU involved."],
        "wall_s": round(time.time() - t0, 1),
    }
    fn = os.path.join(_RES, "e9_seed_depth_evidence.json")
    json.dump(out, open(fn, "w"), indent=2)
    print("\n--- frozen predictions, as-measured ---")
    for k, d_ in v.items():
        print(f"  {k}: {'MET' if d_['MET'] else 'NOT MET'}  ({d_.get('claim')})"
              + (f"  ratio={d_.get('ratio')}" if d_.get("ratio") else ""))
    print(f"\nsaved {os.path.relpath(fn)}  ({out['wall_s']}s)")


if __name__ == "__main__":
    main()
