"""Decisive cross-family conditional-encoder transfer test.

Settles the open question raised in the Phase-3 novelty assessment: is the conditional
encoder NECESSARY, or does plain warm-start already transfer? The prior experiment
(transfer_eval.py) used a HOMOGENEOUS group-14 monoxide family {CO,SiO,GeO} -> SnO, where a
single un-conditioned policy already transfers, so conditioning added nothing (the
pre-registered WEAK result). That test cannot distinguish "encoder useless" from "family too
easy" -- because warm-start never failed, conditioning had no room to help.

This test makes warm-start work hard: a chemically DIVERSE training family spanning distinct
bonding / correlation regimes
    polar monoxides {CO, SiO, GeO}  |  polar isoelectronic {BF}
    homonuclear strong-correlation {N2}  |  ionic metal-oxide {BeO}
all closed-shell CAS(6,6)/12q, sharing the build_pool(12,6) operator vocab (a token = the same
excitation for every molecule; only the Hamiltonian/energies differ). Leave-one-out: for each
held-out molecule, pre-train two generators of identical capacity/budget on the remaining
family and compare transfer to the held-out:
    B1   - warm-start, NO conditioning (zeros descriptor): one averaged policy for all molecules
    COND - MP2-conditioned (FiLM on the molecular descriptor): can specialize per molecule

============================ PRE-REGISTERED DECISION RULE ============================
Fixed BEFORE running. Decisive held-outs = {N2 (strong-corr), BeO (ionic)} -- regimes a
polar-dominated average policy should fit poorly, so B1 error should be high there. Control
held-out = CO (well inside the training distribution; warm-start should already be good).

The encoder is VALIDATED as the Phase-3 algorithmic-innovation headline IFF, aggregated over
seeds:
  (i)  on at least one decisive held-out, COND beats B1 in zero-shot best-mHa by MORE than the
       across-seed standard deviation (i.e. clearly outside seed noise), AND
  (ii) on the control, COND is not worse than B1 beyond that noise (conditioning must not hurt
       where warm-start already works).
Otherwise -- COND ~= B1 within noise on the decisive held-outs -- the encoder is NOT necessary
for the molecule families we care about; we DROP it as the headline and lead innovation with
the integrated MPS + QSCI + operator-pool-compression scaling layer (fallback in the novelty
assessment). Either outcome is reported honestly; a clean negative is a real result.
=====================================================================================

Writes results/encoder/decisive_transfer_evidence.json and decisive_transfer.png.

EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, time, json, copy, numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import molecules as M
from cond_gptqe import CondGPTQE, expand_cond
from train_conditional import build_dataset, gqe_train

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_REPO, "results", "encoder")
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "decisive_run.log"), "a")
def log(s):
    print(s, flush=True); LOG.write(s + "\n"); LOG.flush()

# --- config (PRE_IT may be overridden by argv[1] after the timing probe) ---
FAMILY   = ["CO", "SiO", "GeO", "BF", "N2", "BeO"]
DECISIVE = ["N2", "BeO"]          # regimes the averaged warm-start should fit poorly
CONTROL  = ["CO"]                 # inside the training distribution; warm-start should be fine
FACTORS  = [0.95, 1.0, 1.05]
NCAS, NELEC, SEQ, NEMB = 6, 6, 8, 96
PRE_IT, BATCH, BETA = int(sys.argv[1]) if len(sys.argv) > 1 else 180, 64, 300.0
ZS_N = 256
SEEDS = [0, 1, 2]


def zeroshot(model, data, use_cond, n=ZS_N, temp=0.7, seed=0):
    torch.manual_seed(1000 + seed)
    efci = data["rec"]["e_cas"]; dim = model.desc_dim
    c = expand_cond(data["cond"] if use_cond else np.zeros(dim, np.float32), n)
    seqs = model.generate(n, SEQ, c, temp).cpu().numpy()
    E = np.array([data["energy"](s) for s in seqs])
    return dict(mean_mHa=float((E.mean() - efci) * 1000), best_mHa=float((E.min() - efci) * 1000))


def random_zeroshot(data, n=ZS_N, seed=0):
    rng = np.random.default_rng(seed); efci = data["rec"]["e_cas"]; V = len(data["pool"])
    E = np.array([data["energy"](rng.integers(0, V, SEQ)) for _ in range(n)])
    return dict(mean_mHa=float((E.mean() - efci) * 1000), best_mHa=float((E.min() - efci) * 1000))


def run_case(held, seed):
    train_names = [m for m in FAMILY if m != held]
    t0 = time.time()
    log(f"\n----- held-out={held}  seed={seed}  train={train_names} -----")
    train_data, std = build_dataset(train_names, FACTORS, NCAS, NELEC)             # fit std on train only
    held_all, _ = build_dataset([held], FACTORS, NCAS, NELEC, standardizer=std, fit=False)
    held_eq = next(d for d in held_all if abs(d["rec"]["R"] - M.REGISTRY[held]["Re"]) < 1e-6)
    vocab = len(train_data[0]["pool"]); dim = std.dim

    cond_model = CondGPTQE(vocab, SEQ, dim, n_embd=NEMB)
    gqe_train(cond_model, train_data, PRE_IT, BATCH, SEQ, BETA, use_cond=True, seed=seed)
    b1_model = CondGPTQE(vocab, SEQ, dim, n_embd=NEMB)
    gqe_train(b1_model, train_data, PRE_IT, BATCH, SEQ, BETA, use_cond=False, seed=seed)

    zc = zeroshot(cond_model, held_eq, use_cond=True, seed=seed)
    zb = zeroshot(b1_model, held_eq, use_cond=False, seed=seed)
    zr = random_zeroshot(held_eq, seed=seed)
    log(f"  zero-shot {held}: COND best={zc['best_mHa']:.2f} mean={zc['mean_mHa']:.2f} | "
        f"B1 best={zb['best_mHa']:.2f} mean={zb['mean_mHa']:.2f} | "
        f"RND best={zr['best_mHa']:.2f} | {time.time()-t0:.0f}s")
    return dict(held=held, seed=seed, train=train_names, vocab=vocab, desc_dim=dim,
                FCI=held_eq["rec"]["e_cas"], HF=held_eq["rec"]["hf_energy"],
                corr_mHa=(held_eq["rec"]["hf_energy"] - held_eq["rec"]["e_cas"]) * 1000,
                COND=zc, B1=zb, RANDOM=zr, seconds=round(time.time() - t0, 1))


def summarize(results):
    """Aggregate per held-out over seeds and apply the pre-registered decision rule."""
    by_held = {}
    for r in results:
        by_held.setdefault(r["held"], []).append(r)
    table = {}
    for held, rs in by_held.items():
        cb = np.array([r["COND"]["best_mHa"] for r in rs])
        bb = np.array([r["B1"]["best_mHa"] for r in rs])
        rb = np.array([r["RANDOM"]["best_mHa"] for r in rs])
        delta = bb - cb                                    # >0 => COND better (lower error)
        noise = float(np.std(np.concatenate([cb, bb])))    # across-seed scale
        table[held] = dict(cond_best=float(cb.mean()), cond_sd=float(cb.std()),
                           b1_best=float(bb.mean()), b1_sd=float(bb.std()),
                           rnd_best=float(rb.mean()),
                           delta_mean=float(delta.mean()), seed_noise=noise,
                           cond_beats_b1_outside_noise=bool(delta.mean() > noise))
    log("\n======== DECISIVE SUMMARY (zero-shot best-mHa, mean over seeds) ========")
    for held, t in table.items():
        tag = "DECISIVE" if held in DECISIVE else ("CONTROL" if held in CONTROL else "")
        log(f"  {held:4s} [{tag:8s}] COND {t['cond_best']:7.2f}  B1 {t['b1_best']:7.2f}  "
            f"RND {t['rnd_best']:7.2f}  | Δ(B1-COND)={t['delta_mean']:+6.2f}  "
            f"noise={t['seed_noise']:.2f}  COND>B1(outside noise)={t['cond_beats_b1_outside_noise']}")
    decisive_win = any(table[h]["cond_beats_b1_outside_noise"] for h in DECISIVE if h in table)
    control_ok = all(table[h]["delta_mean"] >= -table[h]["seed_noise"] for h in CONTROL if h in table)
    verdict = "ENCODER VALIDATED (headline)" if (decisive_win and control_ok) else \
              "ENCODER NOT NECESSARY (drop as headline; use integrated-scaling fallback)"
    log(f"\n  pre-registered verdict: {verdict}")
    log(f"    decisive_win={decisive_win}  control_ok={control_ok}")
    return dict(per_held=table, decisive_win=decisive_win, control_ok=control_ok, verdict=verdict)


def make_figure(results, table):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    helds = list(table.keys()); x = np.arange(len(helds)); w = 0.27
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    for i, (k, c) in enumerate([("rnd_best", "tab:gray"), ("b1_best", "tab:orange"), ("cond_best", "tab:blue")]):
        ax.bar(x + (i - 1) * w, [table[h][k] for h in helds], w,
               label={"rnd_best": "RANDOM", "b1_best": "B1 warm-start", "cond_best": "COND (MP2)"}[c == c and k],
               color=c)
    ax.axhline(1.6, ls="--", c="k", lw=1, label="chem. acc.")
    ax.set_xticks(x); ax.set_xticklabels([f"{h}\n[{'DEC' if h in DECISIVE else 'CTRL'}]" for h in helds])
    ax.set_ylabel("zero-shot best raw GQE error (mHa)")
    ax.set_title("Decisive cross-family transfer (lower = better)")
    ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(OUT, "decisive_transfer.png"), dpi=130)
    log("saved decisive_transfer.png")


def main():
    log(f"\n######## DECISIVE TRANSFER {time.strftime('%Y-%m-%d %H:%M')}  PRE_IT={PRE_IT} ########")
    results = []
    for held in DECISIVE + CONTROL:
        for seed in SEEDS:
            results.append(run_case(held, seed))
            json.dump(dict(config=dict(family=FAMILY, decisive=DECISIVE, control=CONTROL,
                                       factors=FACTORS, ncas=NCAS, seq=SEQ, pre_it=PRE_IT,
                                       batch=BATCH, beta=BETA, zeroshot_n=ZS_N, seeds=SEEDS),
                           results=results),
                      open(os.path.join(OUT, "decisive_transfer_evidence.json"), "w"), indent=2)
    summary = summarize(results)
    json.dump(dict(config=dict(family=FAMILY, decisive=DECISIVE, control=CONTROL, factors=FACTORS,
                               ncas=NCAS, seq=SEQ, pre_it=PRE_IT, batch=BATCH, beta=BETA,
                               zeroshot_n=ZS_N, seeds=SEEDS),
                   results=results, summary=summary),
              open(os.path.join(OUT, "decisive_transfer_evidence.json"), "w"), indent=2)
    make_figure(results, summary["per_held"])
    log("DONE")


if __name__ == "__main__":
    main()
