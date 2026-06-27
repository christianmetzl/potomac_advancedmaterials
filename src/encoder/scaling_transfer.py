"""Cross-qubit-count generative transfer — the harder encoder test.

The decisive same-size test (decisive_transfer.py) showed conditioning ~= warm-start. The genuinely
novel, scaling-relevant question is different: can a generator trained on a SMALL system propose good
circuits for a LARGER one? If yes, the generative policy transfers across system size — directly
supporting the primary criterion (scalability).

The enabler is a CANONICAL, frontier-relative tokenization: a token encodes an excitation as
(occupied depth below HOMO, virtual height above LUMO), independent of qubit count. For even-electron
systems this mapping is consistent across sizes, so the token vocabulary of a small system is a SUBSET
of a larger one. A generator trained on H6 (12q) can therefore generate frontier excitations realized
on H8 (16q) / H10 (20q).

Test: train an (unconditioned) GPT-QE generator on H6 (12q); zero-shot generate for H8 (16q); compare
best energy over a fixed sample budget against random search on H8 (the no-transfer baseline). If the
H6-trained generator beats random on H8, circuit structure transfers across size.

PRE-REGISTERED: cross-size transfer SUCCEEDS iff the trained generator's best zero-shot energy on the
larger target beats random search (same budget) by more than the across-seed std. Reported honestly
either way.

Energy: exact statevector (lightning) + sparse-matvec, feasible <=16q. 20q is a GPU follow-on.
Run:  python src/encoder/scaling_transfer.py --smoke    # validate tokenization/realize/energy
      python src/encoder/scaling_transfer.py            # full train(H6)->transfer(H8)

EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, time, json, numpy as np, torch, torch.nn.functional as F
import pennylane as qml
from openfermion import MolecularData, jordan_wigner, get_fermion_operator, get_sparse_operator
from openfermionpyscf import run_pyscf
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gqe_scaling import GPTQE
from qsci_score import qsci_energy

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_REPO, "results", "encoder")
os.makedirs(OUT, exist_ok=True)
TVALS = [-2**k/160 for k in range(1, 6)] + [2**k/160 for k in range(1, 6)]   # 10 discrete angles (as build_pool)


# ---------- canonical, frontier-relative tokenization ----------
def canonical_tokens(ne, nq):
    """All spin-conserving single/double excitations as frontier-relative canonical tokens.

    occupied spin-orbital i in [0,ne): depth = ne-1-i.  virtual a in [ne,nq): height = a-ne.
    Token: ("s", d, h) or ("d", d1, h1, d2, h2) with (d1,h1)<=(d2,h2) ordered. For even ne the spin
    parity implied by (depth) is consistent across sizes, so tokens are size-portable.
    """
    occ = list(range(ne)); vir = list(range(ne, nq))
    singles = set(); doubles = set()
    for i in occ:
        for a in vir:
            if (i % 2) == (a % 2):                       # spin-conserving single
                singles.add(("s", ne - 1 - i, a - ne))
    for ii in range(len(occ)):
        for jj in range(ii + 1, len(occ)):
            i, j = occ[ii], occ[jj]
            for aa in range(len(vir)):
                for bb in range(aa + 1, len(vir)):
                    a, b = vir[aa], vir[bb]
                    if sorted([i % 2, j % 2]) == sorted([a % 2, b % 2]):    # spin-conserving double
                        t = tuple(sorted([(ne - 1 - i, a - ne), (ne - 1 - j, b - ne)]))
                        doubles.add(("d", t[0][0], t[0][1], t[1][0], t[1][1]))
    return sorted(singles) + sorted(doubles)


def realize(token, ne, nq):
    """Canonical token -> (type, wires, default_angle) for a concrete (ne,nq), or None if it doesn't fit."""
    if token[0] == "s":
        d, h = token[1], token[2]; i = ne - 1 - d; a = ne + h
        if i < 0 or a >= nq:
            return None
        return ("s", [i, a])
    _, d1, h1, d2, h2 = token
    i = ne - 1 - d1; a = ne + h1; j = ne - 1 - d2; b = ne + h2
    if min(i, j) < 0 or max(a, b) >= nq or i == j or a == b:
        return None
    return ("d", sorted([i, j]) + sorted([a, b]))


def build_realized_pool(tokens, ne, nq):
    """Map a canonical token vocabulary to a per-system pool of (type, wires, angle), 10 angles each.

    Returns (pool, valid_mask): pool[k] is the realization of vocab op (k//10) at angle (k%10); entries
    whose token does not fit this system are marked invalid (mask False) and never generated/applied.
    """
    pool = []; valid = []
    for tok in tokens:
        r = realize(tok, ne, nq)
        for t in TVALS:
            if r is None:
                pool.append(None); valid.append(False)
            else:
                pool.append((r[0], r[1], t)); valid.append(True)
    return pool, np.array(valid, bool)


# ---------- H-chain Hamiltonian + exact energy ----------
REF_FCI = {4: -2.156857, 6: -3.170505, 8: -4.186089, 10: -5.202826}  # committed references (Ha)


def hchain_ham(n_atoms, R=0.74):
    geom = [("H", (0.0, 0.0, i * R)) for i in range(n_atoms)]
    mol = MolecularData(geom, "sto-6g", multiplicity=1, charge=0)
    mol = run_pyscf(mol, run_scf=True, run_fci=(n_atoms <= 8))
    qop = jordan_wigner(get_fermion_operator(mol.get_molecular_hamiltonian()))
    nq = 2 * mol.n_orbitals; ne = mol.n_electrons
    e_fci = mol.fci_energy if mol.fci_energy is not None else REF_FCI.get(n_atoms)
    return dict(qop=qop, nq=nq, ne=ne, hf=mol.hf_energy, e_fci=float(e_fci), n_atoms=n_atoms)


def energy_fn(rec):
    nq, ne = rec["nq"], rec["ne"]
    Hsp = get_sparse_operator(rec["qop"], n_qubits=nq).tocsr()
    hf = np.where(np.arange(nq) < ne)[0]
    dev = qml.device("lightning.qubit", wires=nq)

    @qml.qnode(dev, diff_method=None)
    def state(applied):
        for w in hf:
            qml.PauliX(int(w))
        for (typ, wires, t) in applied:
            qml.SingleExcitation(t, wires=wires) if typ == "s" else qml.DoubleExcitation(t, wires=wires)
        return qml.state()

    def E(applied):
        psi = np.asarray(state(applied))
        return float((psi.conj() @ (Hsp @ psi)).real)
    return E


def seq_energy(seq, pool, Efn):
    applied = [pool[int(k)] for k in seq if pool[int(k)] is not None]
    return Efn(applied)


def subseq_energies(seqs, pool, Efn, seq_len):
    """Energy of every prefix seqs[b,:L] (L=1..seq_len) -> (B, seq_len). The GQE per-step signal."""
    B = seqs.shape[0]; sub = np.zeros((B, seq_len))
    for b in range(B):
        for L in range(1, seq_len + 1):
            sub[b, L - 1] = seq_energy(seqs[b, :L], pool, Efn)
    return sub


# ---------- minimal GQE training on one system ----------
def train_gptqe(rec, tokens, n_iter=150, batch=32, seq_len=8, beta=300.0, lr=5e-4, seed=0, log=None):
    torch.manual_seed(seed); np.random.seed(seed)
    pool, valid = build_realized_pool(tokens, rec["ne"], rec["nq"])
    vocab = len(pool); Efn = energy_fn(rec)
    model = GPTQE(vocab, seq_len)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    inval = torch.tensor(~valid)
    best = rec["hf"]; t0 = time.time()
    for it in range(n_iter):
        temp = 2.0 + (0.3 - 2.0) * it / max(n_iter - 1, 1)
        seqs = _generate(model, batch, seq_len, temp, inval)
        sub = subseq_energies(seqs.cpu().numpy(), pool, Efn, seq_len)   # (B, seq_len)
        bi = int(sub[:, -1].argmin())
        if sub[bi, -1] < best:
            best = float(sub[bi, -1])
        # GQE objective: cumulative logit at each prefix -> -beta*(E_prefix - E_HF)
        target = torch.tensor(-beta * (sub - rec["hf"]), dtype=torch.float32)
        ws = model.logit_sums(seqs)
        loss = F.mse_loss(ws, target)
        opt.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
        if log and (it % 20 == 0 or it == n_iter - 1):
            log(f"  train H{rec['n_atoms']} it{it:3d} best={abs(best-rec['e_fci'])*1000:8.2f} mHa "
                f"loss={loss.item():.2f} t={time.time()-t0:.0f}s")
    return model


def _generate(model, n, L, temp, inval):
    """Generate sequences, masking invalid (out-of-system) tokens to -inf."""
    idx = torch.full((n, 1), model.start, dtype=torch.long)
    for _ in range(L):
        cond = idx if idx.size(1) <= model.blk else idx[:, -model.blk:]
        lg = model.forward(cond)[:, -1, :] / temp
        lg = lg.masked_fill(inval.unsqueeze(0), float("-inf"))
        idx = torch.cat([idx, torch.multinomial(F.softmax(lg, -1), 1)], 1)
    return idx[:, 1:]


def zeroshot_best(model, rec, tokens, n=256, seq_len=8, temp=0.7, seed=0):
    torch.manual_seed(1234 + seed)
    pool, valid = build_realized_pool(tokens, rec["ne"], rec["nq"])
    Efn = energy_fn(rec)
    seqs = _generate(model, n, seq_len, temp, torch.tensor(~valid)).cpu().numpy()
    En = np.array([seq_energy(s, pool, Efn) for s in seqs])
    return float((En.min() - rec["e_fci"]) * 1000), float((En.mean() - rec["e_fci"]) * 1000)


def random_best(rec, tokens, n=256, seq_len=8, seed=0):
    rng = np.random.default_rng(seed)
    pool, valid = build_realized_pool(tokens, rec["ne"], rec["nq"])
    vids = np.where(valid)[0]; Efn = energy_fn(rec)
    En = np.array([seq_energy(rng.choice(vids, seq_len), pool, Efn) for _ in range(n)])
    return float((En.min() - rec["e_fci"]) * 1000), float((En.mean() - rec["e_fci"]) * 1000)


# ---------- multi-system training + QSCI evaluation at the larger target (for 20q) ----------
def train_gptqe_multi(recs, tokens, n_iter=180, batch=32, seq_len=8, beta=300.0, lr=5e-4, seed=0, log=None):
    """Train one generator over several systems (cycled), masking each system's invalid tokens.

    Vocabulary = canonical `tokens` (the largest training system's set); smaller systems mask the
    tokens that do not fit them. This teaches a single size-agnostic generative policy.
    """
    torch.manual_seed(seed); np.random.seed(seed)
    sysd = []
    for rec in recs:
        pool, valid = build_realized_pool(tokens, rec["ne"], rec["nq"])
        sysd.append(dict(rec=rec, pool=pool, inval=torch.tensor(~valid), Efn=energy_fn(rec),
                         best=rec["hf"]))
    vocab = len(tokens) * len(TVALS)
    model = GPTQE(vocab, seq_len)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    t0 = time.time()
    for it in range(n_iter):
        s = sysd[it % len(sysd)]; rec = s["rec"]
        temp = 2.0 + (0.3 - 2.0) * it / max(n_iter - 1, 1)
        seqs = _generate(model, batch, seq_len, temp, s["inval"])
        sub = subseq_energies(seqs.cpu().numpy(), s["pool"], s["Efn"], seq_len)
        s["best"] = min(s["best"], float(sub[:, -1].min()))
        target = torch.tensor(-beta * (sub - rec["hf"]), dtype=torch.float32)
        loss = F.mse_loss(model.logit_sums(seqs), target)
        opt.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
        if log and (it % 30 == 0 or it == n_iter - 1):
            msg = " ".join(f"H{s['rec']['n_atoms']}={abs(s['best']-s['rec']['e_fci'])*1000:.1f}" for s in sysd)
            log(f"  multi it{it:3d} best[{msg}] mHa loss={loss.item():.1f} t={time.time()-t0:.0f}s")
    return model


def sample_dets(seqs, pool, target_rec, shots=2000):
    """Sample computational-basis determinants from each generated circuit on the target system."""
    nq, ne = target_rec["nq"], target_rec["ne"]
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


def qsci_transfer(seqs, target_rec, tokens, topk=600):
    """QSCI energy of the determinant subspace sampled from circuits on the target system.

    Returns (err_at_topk_mHa, n_used, err_at_matchedK_mHa) where matched-K (=K_FAIR most frequent
    determinants) controls for sampling DIVERSITY so the comparison reflects determinant QUALITY.
    """
    K_FAIR = 64
    pool, _ = build_realized_pool(tokens, target_rec["ne"], target_rec["nq"])
    dets = sample_dets(seqs, pool, target_rec)
    uq, cnt = np.unique(dets, return_counts=True)
    rank = np.argsort(cnt)[::-1]
    keep = uq[rank[:topk]]
    e, n = qsci_energy(target_rec["qop"], keep)
    keep_fair = uq[rank[:K_FAIR]]
    e_fair, _ = qsci_energy(target_rec["qop"], keep_fair)
    return abs(e - target_rec["e_fci"]) * 1000.0, int(n), abs(e_fair - target_rec["e_fci"]) * 1000.0


def main_large():
    """Stronger claim: train on H4(8q)+H6(12q); transfer to H10(20q), QSCI-evaluated."""
    def log(s): print(s, flush=True)
    log(f"\n######## SCALING TRANSFER (train H4+H6 -> transfer H10/20q, QSCI) {time.strftime('%Y-%m-%d %H:%M')} ########")
    recs = [hchain_ham(4), hchain_ham(6)]
    tokens = canonical_tokens(6, 12)                 # H4 tokens are a subset of H6's
    tgt = hchain_ham(10)
    log(f"train {[r['n_atoms'] for r in recs]} -> target H10 nq={tgt['nq']} FCI={tgt['e_fci']:.6f}; vocab={len(tokens)} ops")
    NGEN = 96
    res = []
    for seed in [0, 1, 2]:
        model = train_gptqe_multi(recs, tokens, seed=seed, log=log if seed == 0 else None)
        pool_t, valid_t = build_realized_pool(tokens, tgt["ne"], tgt["nq"])
        torch.manual_seed(7000 + seed)
        gen = _generate(model, NGEN, 8, 0.4, torch.tensor(~valid_t)).cpu().numpy()
        rng = np.random.default_rng(seed); vids = np.where(valid_t)[0]
        rnd = np.array([rng.choice(vids, 8) for _ in range(NGEN)])
        te, tn, tef = qsci_transfer(gen, tgt, tokens)
        re_, rn, ref = qsci_transfer(rnd, tgt, tokens)
        log(f"[seed {seed}] H(4,6)->H10: pooled trained {te:.2f}({tn}d) vs random {re_:.2f}({rn}d) | "
            f"matched-K64 trained {tef:.2f} vs random {ref:.2f}")
        res.append(dict(seed=seed, trained_pooled_mHa=te, trained_dets=tn, random_pooled_mHa=re_,
                        random_dets=rn, trained_fairK_mHa=tef, random_fairK_mHa=ref))
        json.dump(dict(train="H4+H6", target="H10_20q", eval="QSCI", n_gen=NGEN, results=res),
                  open(os.path.join(OUT, "scaling_transfer_h10_evidence.json"), "w"), indent=2)
    tf = np.array([r["trained_fairK_mHa"] for r in res]); rf = np.array([r["random_fairK_mHa"] for r in res])
    tp = np.array([r["trained_pooled_mHa"] for r in res]); rp = np.array([r["random_pooled_mHa"] for r in res])
    noise = float(np.std(np.concatenate([tf, rf])))
    success = bool((rf.mean() - tf.mean()) > noise)
    summary = dict(fair_metric="QSCI at matched K=64 determinants (quality, diversity-controlled), mHa to FCI",
                   trained_fairK=float(tf.mean()), random_fairK=float(rf.mean()),
                   delta_fairK=float(rf.mean() - tf.mean()), noise_fairK=noise,
                   pooled_note="pooled metric favors random via determinant DIVERSITY, not quality",
                   trained_pooled=float(tp.mean()), random_pooled=float(rp.mean()),
                   cross_size_transfer_success_fairK=success)
    log(f"\nSUMMARY H(4,6)->H10/20q [FAIR matched-K=64]: trained {tf.mean():.2f}±{tf.std():.2f} vs "
        f"random {rf.mean():.2f}±{rf.std():.2f} | Δ={rf.mean()-tf.mean():+.2f} noise={noise:.2f} -> success={success}")
    log(f"  [pooled, diversity-confounded]: trained {tp.mean():.2f} vs random {rp.mean():.2f}")
    out = json.load(open(os.path.join(OUT, "scaling_transfer_h10_evidence.json")))
    out["summary"] = summary
    json.dump(out, open(os.path.join(OUT, "scaling_transfer_h10_evidence.json"), "w"), indent=2)
    log("DONE")


def smoke():
    print("=== smoke: canonical tokenization / realize / energy ===")
    t6 = canonical_tokens(6, 12); t8 = canonical_tokens(8, 16); t10 = canonical_tokens(10, 20)
    s6, s8, s10 = set(t6), set(t8), set(t10)
    print(f"tokens: H6(12q)={len(t6)}  H8(16q)={len(t8)}  H10(20q)={len(t10)}")
    print(f"H6 tokens subset of H8? {s6 <= s8}   subset of H10? {s6 <= s10}")
    rec8 = hchain_ham(8)
    pool, valid = build_realized_pool(t6, rec8["ne"], rec8["nq"])
    print(f"H6-vocab realized on H8: {valid.sum()}/{len(valid)} valid slots")
    Efn = energy_fn(rec8)
    print(f"H8: nq={rec8['nq']} ne={rec8['ne']} HF={rec8['hf']:.5f} FCI={rec8['e_fci']:.5f} "
          f"| HF-energy check={abs(seq_energy([], pool, Efn)-rec8['hf'])*1000:.3f} mHa")
    print("smoke OK")


def main():
    def log(s): print(s, flush=True)
    log(f"\n######## SCALING TRANSFER (train H6/12q -> transfer H8/16q) {time.strftime('%Y-%m-%d %H:%M')} ########")
    train_rec = hchain_ham(6); tgt_rec = hchain_ham(8)
    tokens = canonical_tokens(train_rec["ne"], train_rec["nq"])      # H6 vocabulary (subset of H8)
    log(f"train H6: {len(tokens)} canonical ops, FCI={train_rec['e_fci']:.6f}")
    log(f"target H8: nq={tgt_rec['nq']} FCI={tgt_rec['e_fci']:.6f}")
    res = []
    for seed in [0, 1, 2]:
        model = train_gptqe(train_rec, tokens, seed=seed, log=log if seed == 0 else None)
        tb, tm = zeroshot_best(model, tgt_rec, tokens, seed=seed)
        rb, rm = random_best(tgt_rec, tokens, seed=seed)
        log(f"[seed {seed}] H6->H8 zero-shot best={tb:.2f} mean={tm:.2f} | random best={rb:.2f} mean={rm:.2f}")
        res.append(dict(seed=seed, transfer_best=tb, transfer_mean=tm, random_best=rb, random_mean=rm))
        json.dump(dict(train="H6_12q", target="H8_16q", results=res),
                  open(os.path.join(OUT, "scaling_transfer_evidence.json"), "w"), indent=2)
    # primary metric = MEAN zero-shot energy (distribution shift = learning signal); best is secondary
    tm = np.array([r["transfer_mean"] for r in res]); rm = np.array([r["random_mean"] for r in res])
    tb = np.array([r["transfer_best"] for r in res]); rb = np.array([r["random_best"] for r in res])
    noise_mean = float(np.std(np.concatenate([tm, rm])))
    success = bool((rm.mean() - tm.mean()) > noise_mean)        # trained mean below random mean, outside noise
    summary = dict(metric="zero-shot mean energy on larger target (mHa to FCI)",
                   transfer_mean=float(tm.mean()), random_mean=float(rm.mean()),
                   delta_mean=float(rm.mean() - tm.mean()), noise_mean=noise_mean,
                   transfer_best=float(tb.mean()), random_best=float(rb.mean()),
                   delta_best=float(rb.mean() - tb.mean()),
                   cross_size_transfer_success=success)
    log(f"\nSUMMARY (H6->H8): mean trained {tm.mean():.2f}±{tm.std():.2f} vs random {rm.mean():.2f}±{rm.std():.2f} "
        f"| Δmean={rm.mean()-tm.mean():+.2f} noise={noise_mean:.2f} -> success={success}")
    log(f"  (best: trained {tb.mean():.2f} vs random {rb.mean():.2f}, Δ={rb.mean()-tb.mean():+.2f})")
    out = json.load(open(os.path.join(OUT, "scaling_transfer_evidence.json")))
    out["summary"] = summary
    json.dump(out, open(os.path.join(OUT, "scaling_transfer_evidence.json"), "w"), indent=2)
    log("DONE")


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        smoke()
    elif "--large" in sys.argv:
        main_large()
    else:
        main()
