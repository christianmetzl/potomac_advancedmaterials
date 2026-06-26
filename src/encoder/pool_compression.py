"""Operator-pool compression — MP2-amplitude + symmetry pruning (innovation pillar 3).

With the conditional encoder dropped (decisive_transfer.py: clean negative), operator-pool
compression becomes a load-bearing algorithmic-innovation pillar. This DEMONSTRATES it, rather than
just asserting it.

Claim: the O(N^4) double-excitation pool can be pruned by (a) spin/point-group symmetry — excitations
whose MP2 amplitude is exactly zero by spin selection are removed for free — and (b) MP2-amplitude
ranking — keeping only the chemically important doubles. The test is whether MP2-ranked pruning
preserves the correlation a pool can capture FAR better than random pruning at the same pool size.

Deterministic pool-quality metric (no GQE/sampling noise): each pruned pool defines a determinant
subspace = {HF} u {singly-excited dets from all singles} u {doubly-excited dets from the KEPT
doubles}. We diagonalize H in that subspace (QSCI engine) and report the energy error vs the
active-space CASCI/FCI reference. A better pool captures more correlation (lower error) per kept
operator. We compare, at matched pool size: MP2-ranked pruning vs random pruning (several seeds).

Systems: CAS(6,6)/12q molecules from the registry (CO, N2, SiO) — qop, e_cas, and the active-space
MP2 t2 all come straight from molecules.build(). Writes results/encoder/pool_compression_evidence.json
and pool_compression.png.

EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, json, numpy as np
from pennylane import qchem
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import molecules as M
from qsci_score import qsci_energy

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_REPO, "results", "encoder")
os.makedirs(OUT, exist_ok=True)

MOLS = ["CO", "N2", "SiO"]
FRACTIONS = [1.0, 0.6, 0.4, 0.25, 0.15, 0.08]
RANDOM_SEEDS = [0, 1, 2]
NCAS, NELEC = 6, 6


def det_int(occ_bits):
    v = np.uint64(0)
    for q in occ_bits:
        v |= np.uint64(1) << np.uint64(int(q))
    return v


def excitation_det(hf_occ, removed, added):
    s = set(hf_occ) - set(removed) | set(added)
    return det_int(sorted(s))


def double_weight(d, t2, nocc_spin):
    """|MP2 amplitude| for double [i,j,a,b] (spin-orbitals), or 0 if spin-forbidden (symmetry prune).

    Interleaved spin-orbitals: spatial = p//2, spin = p%2. Virtual t2 index = spatial - nocc_spatial.
    """
    i, j, a, b = d
    nocc_sp = nocc_spin // 2
    # spin conservation (multiset of spins must match)
    if sorted([i % 2, j % 2]) != sorted([a % 2, b % 2]):
        return 0.0
    io, jo = i // 2, j // 2
    av, bv = a // 2 - nocc_sp, b // 2 - nocc_sp
    return abs(float(t2[io, jo, av, bv]))


def subspace_error(qop, e_cas, hf_occ, singles, kept_doubles):
    dets = [det_int(hf_occ)]
    for (i, a) in singles:
        dets.append(excitation_det(hf_occ, [i], [a]))
    for (i, j, a, b) in kept_doubles:
        dets.append(excitation_det(hf_occ, [i, j], [a, b]))
    e, n = qsci_energy(qop, np.array(dets, dtype=np.uint64))
    return abs(e - e_cas) * 1000.0, n


def run_mol(name):
    rec = M.build(name, ncas=NCAS, nelec=NELEC)
    nq, ne, qop, e_cas, t2 = rec["nq"], rec["ne"], rec["qop"], rec["e_cas"], rec["t2"]
    hf_occ = list(range(ne))
    singles, doubles = qchem.excitations(ne, nq)
    singles = [tuple(s) for s in singles]; doubles = [tuple(d) for d in doubles]
    w = np.array([double_weight(d, t2, ne) for d in doubles])
    n_sym0 = int((w == 0).sum())                       # spin-forbidden doubles (free symmetry prune)
    order = np.argsort(-w)                              # MP2 ranking, descending
    nd = len(doubles)

    levels = []
    for f in FRACTIONS:
        k = max(1, int(round(f * nd)))
        mp2_keep = [doubles[idx] for idx in order[:k]]
        mp2_err, mp2_n = subspace_error(qop, e_cas, hf_occ, singles, mp2_keep)
        rnd_errs = []
        for s in RANDOM_SEEDS:
            rng = np.random.default_rng(1000 + s)
            ridx = rng.choice(nd, size=k, replace=False)
            rnd_keep = [doubles[i] for i in ridx]
            rerr, _ = subspace_error(qop, e_cas, hf_occ, singles, rnd_keep)
            rnd_errs.append(rerr)
        vocab = (len(singles) + k) * 10
        levels.append(dict(fraction=f, n_doubles_kept=k, vocab=vocab,
                           mp2_err_mHa=round(mp2_err, 3), mp2_dets=mp2_n,
                           rnd_err_mHa_mean=round(float(np.mean(rnd_errs)), 3),
                           rnd_err_mHa_std=round(float(np.std(rnd_errs)), 3)))
        print(f"  {name} f={f:.2f} keep={k:3d}/{nd} vocab={vocab:4d} | "
              f"MP2 {mp2_err:7.3f} mHa | random {np.mean(rnd_errs):7.3f}±{np.std(rnd_errs):.3f} mHa",
              flush=True)
    return dict(molecule=name, nq=nq, ne=ne, n_singles=len(singles), n_doubles=nd,
                n_spin_forbidden_doubles=n_sym0, e_cas=e_cas, levels=levels)


def make_figure(results):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, len(results), figsize=(5 * len(results), 4.2), squeeze=False)
    for ax, r in zip(axes[0], results):
        fr = [l["fraction"] for l in r["levels"]]
        ax.plot(fr, [l["mp2_err_mHa"] for l in r["levels"]], "o-", color="tab:blue", label="MP2-ranked prune")
        ax.errorbar(fr, [l["rnd_err_mHa_mean"] for l in r["levels"]],
                    yerr=[l["rnd_err_mHa_std"] for l in r["levels"]], fmt="s--", color="tab:orange",
                    label="random prune")
        ax.axhline(1.6, ls=":", c="k", lw=1, label="chem. acc.")
        ax.set_xlabel("fraction of doubles kept"); ax.set_ylabel("CI-subspace error vs CASCI (mHa)")
        ax.set_yscale("log"); ax.set_title(f"{r['molecule']} ({r['nq']}q)"); ax.invert_xaxis(); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "pool_compression.png"), dpi=130)
    print("saved pool_compression.png", flush=True)


def main():
    print("Operator-pool compression: MP2-ranked vs random pruning (deterministic CI-subspace metric)")
    results = []
    for nm in MOLS:
        results.append(run_mol(nm))
        json.dump(dict(config=dict(mols=MOLS, fractions=FRACTIONS, random_seeds=RANDOM_SEEDS,
                                   ncas=NCAS, nelec=NELEC,
                                   metric="HF + all singles + kept doubles -> QSCI diagonalization"),
                       results=results),
                  open(os.path.join(OUT, "pool_compression_evidence.json"), "w"), indent=2)
    make_figure(results)
    print("DONE")


if __name__ == "__main__":
    main()
