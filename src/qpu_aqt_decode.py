"""Harvest + decode the AQT IBEX Q1 flight (probe + shallow + depth-ladder) whenever it completes.

Idempotent: run anytime. If jobs are still queued it reports status and exits 2. When all are
COMPLETED it (a) decodes the probe to pin the count-key bit order (X-on-qubit-0 -> exactly one
position flips), (b) decodes both physics jobs with that pinned convention, (c) post-selects
number-conserving determinants, (d) computes the pure device-sampled QSCI energy and the
device-seeded grown energy vs exact FCI (12q H6), and (e) writes results/qpu_aqt_evidence.json.
Raw counts committed regardless of outcome; any FAIL is reported as-is.

Usage:  python src/qpu_aqt_decode.py
EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
NQ, NE = 12, 6
LEX = sorted(range(NQ), key=str)


def get_counts(prov, job_id, tries=8):
    from qbraid.runtime.native import QbraidJob
    for a in range(tries):
        try:
            c = QbraidJob(job_id, client=prov.client).result().data.get_counts()
            if c:
                return c
        except Exception as e:
            print(f"  fetch retry {a+1}: {str(e)[:80]}", flush=True)
        time.sleep(10)
    raise RuntimeError(f"no counts for {job_id}")


def main():
    sub = json.load(open(os.path.join(_RES, "qpu_aqt_submission.json")))
    from qbraid.runtime import QbraidProvider
    from qbraid.runtime.native import QbraidJob
    prov = QbraidProvider()

    ids = {"probe": sub["probe_job"]}
    ids.update({j["tag"]: j["job_id"] for j in sub["jobs"]})
    status = {}
    for k, v in ids.items():
        status[k] = str(QbraidJob(v, client=prov.client).status()).split(".")[-1]
    print("status:", status, flush=True)
    if any(s == "FAILED" for s in status.values()):
        print("At least one job FAILED — harvesting what completed; failures billed nothing.", flush=True)
    if not all(s in ("COMPLETED", "FAILED") for s in status.values()):
        print("not all final yet — re-run later", flush=True)
        sys.exit(2)

    # (a) probe -> pin bit order
    conv = "LEX"
    if status["probe"] == "COMPLETED":
        pc = get_counts(prov, ids["probe"])
        top = max(pc, key=pc.get)
        pos = [k for k, ch in enumerate(top) if ch == "1"]
        exp_lex = [LEX.index(0)]
        if pos == exp_lex:
            conv = "LEX"
        elif pos == [0]:
            conv = "PLAIN"                        # key position k == qubit k
        elif pos == [NQ - 1]:
            conv = "REVERSED"                     # little-endian
        else:
            conv = f"UNKNOWN({pos})"
        print(f"probe: dominant {top} ({pc[top]}/{sum(pc.values())}) -> convention {conv}", flush=True)
    else:
        print("probe FAILED — falling back to LEX + dominant==HF sanity on physics jobs", flush=True)

    def decode(bits):
        if conv == "PLAIN":
            return sum(1 << k for k, ch in enumerate(bits) if ch == "1")
        if conv == "REVERSED":
            return sum(1 << (NQ - 1 - k) for k, ch in enumerate(bits) if ch == "1")
        return sum(1 << LEX[k] for k, ch in enumerate(bits) if ch == "1")   # LEX default

    import qsci_lib as L
    P = L.hchain_problem(6)
    eng = L.PauliEngine(P["qop"].terms)
    hf = L.hf_det(NE)
    out = dict(run="qpu_aqt_flight", device=sub["device"], convention=conv,
               shots_per_job=sub["shots_per_job"], probe_status=status["probe"], results=[])
    for j in sub["jobs"]:
        tag, jid = j["tag"], j["job_id"]
        if status[tag] != "COMPLETED":
            out["results"].append(dict(tag=tag, job_id=jid, status=status[tag])); continue
        counts = get_counts(prov, jid)
        pool, kept = {}, 0
        for bits, c in counts.items():
            d = decode(bits)
            if bin(d).count("1") == NE:
                pool[d] = pool.get(d, 0) + c; kept += c
        tot = sum(counts.values())
        dom = max(pool, key=pool.get) if pool else None
        E, _ = eng.qsci(set(pool) | {hf})
        Eg, spg = eng.qsci_fast(set(pool) | {hf}, grow_iters=8, grow_per_iter=400, kcap=6000)
        err, errg = 1000 * (E - P["e_fci"]), 1000 * (Eg - P["e_fci"])
        out["results"].append(dict(
            tag=tag, job_id=jid, status="COMPLETED", two_q_gate_bound=j["two_q_gate_bound"],
            raw_bitstrings=len(counts), postselected_shots=int(kept), total_shots=int(tot),
            postselect_keep_frac=round(kept / max(tot, 1), 4),
            dominant_is_hf=bool(dom == hf), pooled_dets=len(pool),
            E_sampled=E, err_sampled_mHa=round(err, 3),
            E_grown=Eg, err_grown_mHa=round(errg, 3), grown_dets=int(len(spg)),
            e_fci=P["e_fci"], raw_counts=counts))
        print(f"{tag}: keep {kept}/{tot} ({kept/max(tot,1):.0%}) | dets {len(pool)} | dom==HF {dom==hf} | "
              f"sampled {err:+.2f} mHa | grown {errg:+.3f} mHa ({len(spg)} dets)", flush=True)
    fn = os.path.join(_RES, "qpu_aqt_evidence.json")
    json.dump(out, open(fn, "w"), indent=2)
    print(f"-> {fn}", flush=True)


if __name__ == "__main__":
    main()
