"""Conditional-encoder transfer experiment (revised metric, see docs/encoder_design.md §0,§6,§7).

Held-out molecule: SnO. Compares three generators, identical capacity/budget:
  B0  - from scratch on SnO (no transfer, no conditioning)
  B1  - jointly pre-trained on {CO,SiO,GeO}xR with NO conditioning (zeros), then SnO
  COND- jointly pre-trained WITH MP2 conditioning, then SnO (descriptor fed)

Measures (per seed):
  (1) zero-shot raw GQE energy on SnO   : COND(desc) vs B1(zeros) vs random
  (2) few-shot transfer curve           : best raw GQE mHa vs SnO eval budget, B0/B1/COND
  (3) chemical-accuracy endpoint        : best COND circuits -> QSCI -> mHa to FCI

Writes results/encoder/transfer_evidence.json and transfer_curve.png. Every number traceable.

EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, time, json, copy, numpy as np, torch
import pennylane as qml
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gqe_scaling import build_pool
import molecules as M
from cond_gptqe import CondGPTQE, expand_cond
from train_conditional import build_dataset, gqe_train, make_energy_fn
from qsci_score import qsci_energy

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
OUT = os.path.join(_REPO, "results", "encoder")
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "run.log"), "a")
def log(s):
    print(s, flush=True); LOG.write(s + "\n"); LOG.flush()

# --- config ---
TRAIN = ["CO", "SiO", "GeO"]; FACTORS = [0.95, 1.0, 1.05]; HELD = "SnO"
NCAS, NELEC, SEQ, NEMB = 6, 6, 8, 96
PRE_IT, FT_IT, BATCH, BETA = 150, 50, 64, 300.0
ZS_N = 256                      # zero-shot sample count
SEEDS = [0, 1, 2]


def zeroshot(model, data, use_cond, n=ZS_N, temp=0.7, seed=0):
    torch.manual_seed(1000 + seed)
    rec = data["rec"]; efci = rec["e_cas"]
    dim = model.desc_dim
    c = expand_cond(data["cond"] if use_cond else np.zeros(dim, np.float32), n)
    seqs = model.generate(n, SEQ, c, temp).cpu().numpy()
    E = np.array([data["energy"](s) for s in seqs])
    return dict(mean_mHa=float((E.mean() - efci) * 1000),
                best_mHa=float((E.min() - efci) * 1000)), seqs, E


def random_zeroshot(data, n=ZS_N, seed=0):
    rng = np.random.default_rng(seed); efci = data["rec"]["e_cas"]
    V = len(data["pool"])
    E = np.array([data["energy"](rng.integers(0, V, SEQ)) for _ in range(n)])
    return dict(mean_mHa=float((E.mean() - efci) * 1000), best_mHa=float((E.min() - efci) * 1000))


def qsci_endpoint(data, seqs, topk=120, shots=3000):
    """Sample determinants from the best generated circuits and diagonalize (QSCI)."""
    rec = data["rec"]; nq, ne = rec["nq"], rec["ne"]; pool = data["pool"]
    hf_occ = np.zeros(nq, int); hf_occ[:ne] = 1
    # pick the lowest-energy circuits
    E = np.array([data["energy"](s) for s in seqs])
    pick = seqs[np.argsort(E)[:topk]]
    sdev = qml.device("lightning.qubit", wires=nq, shots=shots)

    @qml.qnode(sdev)
    def samp(seq):
        for w in np.where(hf_occ)[0]:
            qml.PauliX(int(w))
        for i in seq:
            typ, wires, t = pool[int(i)]
            qml.SingleExcitation(t, wires=list(wires)) if typ == "s" else qml.DoubleExcitation(t, wires=list(wires))
        return qml.sample(wires=range(nq))

    dets = []
    for seq in pick:
        Sm = samp(seq); d = np.zeros(len(Sm), np.uint64)
        for qi in range(nq):
            d |= (Sm[:, qi].astype(np.uint64) << np.uint64(qi))
        dets.append(d)
    alld = np.concatenate(dets)
    uq, cnt = np.unique(alld, return_counts=True)
    keep = uq[np.argsort(cnt)[::-1][:400]]
    e_q, nd = qsci_energy(rec["qop"], keep)
    return dict(qsci_mHa=float(abs(e_q - rec["e_cas"]) * 1000), n_distinct=int(len(uq)), n_used=int(nd))


def run_seed(seed):
    t0 = time.time()
    log(f"\n===== SEED {seed} =====")
    # datasets
    train_data, std = build_dataset(TRAIN, FACTORS, NCAS, NELEC)            # fits standardizer on train
    held_data, _ = build_dataset([HELD], FACTORS, NCAS, NELEC, standardizer=std, fit=False)  # SnO at several R
    sno = next(d for d in held_data if abs(d["rec"]["R"] - M.REGISTRY[HELD]["Re"]) < 1e-6)    # R_eq point
    vocab = len(train_data[0]["pool"]); dim = std.dim
    log(f"train={len(train_data)} pts, held-out={HELD}, vocab={vocab}, desc_dim={dim}, "
        f"SnO HF={sno['rec']['hf_energy']:.6f} FCI={sno['rec']['e_cas']:.6f}")

    # --- pre-train COND and B1 (same arch/budget) ---
    cond_model = CondGPTQE(vocab, SEQ, dim, n_embd=NEMB)
    log(f"pre-train COND ({cond_model.n_params:,} params)...")
    gqe_train(cond_model, train_data, PRE_IT, BATCH, SEQ, BETA, use_cond=True, log=log, seed=seed)
    b1_model = CondGPTQE(vocab, SEQ, dim, n_embd=NEMB)
    log("pre-train B1 (no conditioning)...")
    gqe_train(b1_model, train_data, PRE_IT, BATCH, SEQ, BETA, use_cond=False, log=log, seed=seed)

    # --- (1) zero-shot on SnO at several bond lengths (tests cross-molecule + R generalization) ---
    zs_per_R = []
    for d in held_data:
        R = d["rec"]["R"]
        zc, _, _ = zeroshot(cond_model, d, use_cond=True, seed=seed)
        zb, _, _ = zeroshot(b1_model, d, use_cond=False, seed=seed)
        zr = random_zeroshot(d, seed=seed)
        zs_per_R.append(dict(R=R, COND=zc, B1=zb, RANDOM=zr))
        log(f"[zero-shot SnO R={R:.3f}] COND mean={zc['mean_mHa']:.2f} best={zc['best_mHa']:.2f} | "
            f"B1 mean={zb['mean_mHa']:.2f} best={zb['best_mHa']:.2f} | "
            f"RND mean={zr['mean_mHa']:.2f} best={zr['best_mHa']:.2f}")
    # aggregate over R for the seed-level record (used by the summary)
    def amean(method, field): return float(np.mean([x[method][field] for x in zs_per_R]))
    zs_cond = dict(mean_mHa=amean("COND", "mean_mHa"), best_mHa=amean("COND", "best_mHa"))
    zs_b1 = dict(mean_mHa=amean("B1", "mean_mHa"), best_mHa=amean("B1", "best_mHa"))
    zs_rand = dict(mean_mHa=amean("RANDOM", "mean_mHa"), best_mHa=amean("RANDOM", "best_mHa"))

    # --- (2) few-shot transfer curves on SnO ---
    def finetune(model, use_cond, tag):
        m = copy.deepcopy(model) if model is not None else CondGPTQE(vocab, SEQ, dim, n_embd=NEMB)
        out = gqe_train(m, [sno], FT_IT, BATCH, SEQ, BETA, use_cond=use_cond, seed=seed)
        h = out["history"][id(sno["rec"])]
        log(f"[few-shot {tag}] final best={h['best_mHa'][-1]:.2f} mHa")
        return dict(evals=h["evals"], best_mHa=h["best_mHa"]), out["best_seq"][id(sno["rec"])], m
    c_b0, _, _ = finetune(None, False, "B0-scratch")
    c_b1, _, _ = finetune(b1_model, False, "B1-warmstart")
    c_cond, best_seq_cond, cond_ft = finetune(cond_model, True, "COND")

    # --- (3) chemical-accuracy endpoint: QSCI on best COND circuits (post fine-tune) ---
    _, seqs_cond_ft, _ = zeroshot(cond_ft, sno, use_cond=True, n=160, temp=0.8, seed=seed)
    qe = qsci_endpoint(sno, seqs_cond_ft)
    log(f"[QSCI endpoint COND] {qe['qsci_mHa']:.3f} mHa to FCI "
        f"({qe['n_used']} dets from {qe['n_distinct']} distinct)")

    return dict(seed=seed, vocab=vocab, desc_dim=dim,
                SnO=dict(HF=sno["rec"]["hf_energy"], FCI=sno["rec"]["e_cas"],
                         corr_mHa=(sno["rec"]["hf_energy"] - sno["rec"]["e_cas"]) * 1000),
                zeroshot=dict(COND=zs_cond, B1=zs_b1, RANDOM=zs_rand, per_R=zs_per_R),
                fewshot=dict(B0=c_b0, B1=c_b1, COND=c_cond),
                qsci_endpoint=qe, seconds=round(time.time() - t0, 1))


def main():
    log(f"\n######## TRANSFER EXPERIMENT {time.strftime('%Y-%m-%d %H:%M')} ########")
    results = []
    for s in SEEDS:
        results.append(run_seed(s))
        json.dump(dict(config=dict(train=TRAIN, factors=FACTORS, held=HELD, ncas=NCAS,
                                   seq=SEQ, pre_it=PRE_IT, ft_it=FT_IT, batch=BATCH, beta=BETA,
                                   zeroshot_n=ZS_N, seeds=SEEDS),
                       results=results),
                  open(os.path.join(OUT, "transfer_evidence.json"), "w"), indent=2)
        log(f"saved transfer_evidence.json after seed {s}")
    # summary across seeds
    def agg(path):
        vals = []
        for r in results:
            o = r
            for k in path: o = o[k]
            vals.append(o)
        return float(np.mean(vals)), float(np.std(vals))
    zc = agg(["zeroshot", "COND", "best_mHa"]); zb = agg(["zeroshot", "B1", "best_mHa"])
    zcm = agg(["zeroshot", "COND", "mean_mHa"]); zbm = agg(["zeroshot", "B1", "mean_mHa"])
    qq = agg(["qsci_endpoint", "qsci_mHa"])
    log("\n======== SUMMARY (mean +/- std over seeds) ========")
    log(f"zero-shot best mHa : COND {zc[0]:.2f}+/-{zc[1]:.2f}  B1 {zb[0]:.2f}+/-{zb[1]:.2f}")
    log(f"zero-shot mean mHa : COND {zcm[0]:.2f}+/-{zcm[1]:.2f}  B1 {zbm[0]:.2f}+/-{zbm[1]:.2f}")
    log(f"QSCI endpoint mHa  : COND {qq[0]:.3f}+/-{qq[1]:.3f}")
    make_figure(results)
    log("DONE")


def make_figure(results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    # transfer curves (seed 0)
    r0 = results[0]
    for tag, c in [("B0", "tab:gray"), ("B1", "tab:orange"), ("COND", "tab:blue")]:
        d = r0["fewshot"][tag]
        ax[0].plot(d["evals"], d["best_mHa"], label=tag, color=c, lw=2)
    ax[0].axhline(1.6, ls="--", c="k", lw=1, label="chem. acc. (QSCI)")
    ax[0].set_xlabel("SnO circuit evaluations"); ax[0].set_ylabel("best raw GQE error (mHa)")
    ax[0].set_yscale("log"); ax[0].set_title("Few-shot transfer on held-out SnO (seed 0)")
    ax[0].legend()
    # zero-shot bars (mean over seeds)
    labels = ["RANDOM", "B1", "COND"]
    means = [np.mean([r["zeroshot"][k]["best_mHa"] for r in results]) for k in labels]
    errs = [np.std([r["zeroshot"][k]["best_mHa"] for r in results]) for k in labels]
    ax[1].bar(labels, means, yerr=errs, color=["tab:gray", "tab:orange", "tab:blue"])
    ax[1].set_ylabel("zero-shot best raw GQE error (mHa)")
    ax[1].set_title("Zero-shot SnO (lower = better)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "transfer_curve.png"), dpi=130)
    log("saved transfer_curve.png")


if __name__ == "__main__":
    main()
