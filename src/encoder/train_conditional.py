"""GQE energy evaluation + (joint) conditioned GPT-QE training.

Provides the reusable pieces used by transfer_eval.py:
  make_energy_fn   - statevector energy for one molecule (fast sparse matvec, <=12q)
  eval_subseq      - subsequence energies for a batch of generated circuits
  gqe_train        - GPT-QE training loop (single- or multi-molecule / conditioned)
  build_dataset    - assemble {molecule, bond length} training records + descriptors

GQE objective: regress cumulative chosen-token logits onto  -beta*(E - E_HF), so that
lower-energy circuits get higher generation probability (verified to minimize before
any transfer numbers are taken).

EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, time, numpy as np, torch, torch.nn.functional as F
import pennylane as qml
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gqe_scaling import build_pool
import molecules as M
from descriptors import Standardizer
from cond_gptqe import CondGPTQE, expand_cond


def make_energy_fn(rec):
    """Return (energy(idxs), pool, hf_occ). energy = <psi|H|psi> via lightning + sparse matvec."""
    nq, ne = rec["nq"], rec["ne"]
    Hsp = M.hsp(rec)
    pool = build_pool(nq, ne)
    hf_occ = np.zeros(nq, dtype=int); hf_occ[:ne] = 1
    dev = qml.device("lightning.qubit", wires=nq)

    @qml.qnode(dev, diff_method=None)
    def state(idxs):
        for w in np.where(hf_occ)[0]:
            qml.PauliX(int(w))
        for i in idxs:
            typ, wires, t = pool[int(i)]
            qml.SingleExcitation(t, wires=list(wires)) if typ == "s" else qml.DoubleExcitation(t, wires=list(wires))
        return qml.state()

    def energy(idxs):
        psi = np.asarray(state(idxs))
        return float((psi.conj() @ (Hsp @ psi)).real)
    return energy, pool, hf_occ


def eval_subseq(seqs, energy_fn, seq_len):
    B = seqs.shape[0]; sub = np.zeros((B, seq_len))
    for b in range(B):
        for L in range(1, seq_len + 1):
            sub[b, L - 1] = energy_fn(seqs[b, :L])
    return sub


def build_dataset(names, bond_factors, ncas=6, nelec=6, standardizer=None, fit=True):
    """Build records + per-molecule energy fns + descriptors. If fit, fit standardizer here."""
    recs = []
    for nm in names:
        for f in bond_factors:
            recs.append(M.build(nm, R=M.REGISTRY[nm]["Re"] * f, ncas=ncas, nelec=nelec))
    if standardizer is None:
        standardizer = Standardizer()
    if fit:
        standardizer.fit(recs)
    data = []
    for r in recs:
        e_fn, pool, hf_occ = make_energy_fn(r)
        data.append(dict(rec=r, energy=e_fn, pool=pool, hf_occ=hf_occ,
                         cond=standardizer.transform(r), e_ref=r["e_cas"]))
    return data, standardizer


def gqe_train(model, datasets, n_iter, batch=16, seq_len=8, beta=100.0, lr=5e-4,
              use_cond=True, log=None, seed=0, eval_budget_track=True):
    """Train `model` (CondGPTQE) over one or more molecule datasets.

    Cycles molecules across iterations. Returns history with cumulative quantum
    energy-evaluation count and the running best (mHa to FCI) per molecule -- the
    raw material for transfer curves. Energies regressed as -beta*(E - E_HF).
    """
    torch.manual_seed(seed); np.random.seed(seed)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    desc_dim = model.desc_dim
    zero_c = np.zeros(desc_dim, dtype=np.float32)
    hist = {id(d["rec"]): dict(name=d["rec"]["name"], R=d["rec"]["R"],
                               evals=[], best_mHa=[], best_E=[]) for d in datasets}
    best = {id(d["rec"]): d["rec"]["hf_energy"] for d in datasets}
    best_seq = {id(d["rec"]): None for d in datasets}
    cum_evals = 0; t0 = time.time()
    for it in range(n_iter):
        d = datasets[it % len(datasets)]
        rid = id(d["rec"]); hf = d["rec"]["hf_energy"]; e_fci = d["rec"]["e_cas"]
        c_vec = d["cond"] if use_cond else zero_c
        c = expand_cond(c_vec, batch)
        temp = 2.0 + (0.5 - 2.0) * it / max(n_iter - 1, 1)
        seqs = model.generate(batch, seq_len, c, temp)
        sub = eval_subseq(seqs.cpu().numpy(), d["energy"], seq_len)
        cum_evals += batch * seq_len
        bi = int(sub[:, -1].argmin())
        if sub[bi, -1] < best[rid]:
            best[rid] = float(sub[bi, -1]); best_seq[rid] = seqs[bi].cpu().numpy().copy()
        # GQE regression: logit_sum -> -beta*(E - E_HF)
        target = torch.tensor(-beta * (sub - hf), dtype=torch.float32)
        ws = model.logit_sums(seqs, c)
        loss = F.mse_loss(ws, target)
        opt.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
        if eval_budget_track:
            h = hist[rid]; h["evals"].append(cum_evals)
            h["best_E"].append(best[rid]); h["best_mHa"].append(abs(best[rid] - e_fci) * 1000)
        if log is not None and (it % 10 == 0 or it == n_iter - 1):
            log(f"  it{it:3d} {d['rec']['name']:4s} R{d['rec']['R']:.3f} "
                f"best={abs(best[rid]-e_fci)*1000:8.3f} mHa loss={loss.item():.3f} "
                f"evals={cum_evals} t={time.time()-t0:.0f}s")
    return dict(history=hist, best=best, best_seq=best_seq, cum_evals=cum_evals)


if __name__ == "__main__":
    # Standalone smoke: train conditioned on the 3 light monoxides, print per-molecule best.
    def log(s): print(s, flush=True)
    data, std = build_dataset(["CO", "SiO", "GeO"], [0.95, 1.0, 1.05])
    print(f"dataset: {len(data)} (molecule,R) points, desc_dim={std.dim}", flush=True)
    vocab = len(data[0]["pool"])
    model = CondGPTQE(vocab, 8, std.dim, n_embd=96)
    print(f"CondGPTQE params={model.n_params:,}", flush=True)
    out = gqe_train(model, data, n_iter=30, batch=16, seq_len=8, log=log)
    for d in data:
        h = out["history"][id(d["rec"])]
        print(f"{d['rec']['name']:4s} R{d['rec']['R']:.3f} final best {h['best_mHa'][-1]:.3f} mHa")
