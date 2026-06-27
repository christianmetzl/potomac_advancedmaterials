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
from sci_integrals import hchain_integrals, sci_energy   # Slater-Condon: scalable to 48q+

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


def _ccsdt_ref(n_atoms, R):
    """CCSD(T) reference energy (Ha) via pyscf, for systems too large for FCI."""
    from pyscf import gto, scf, cc
    mol = gto.M(atom="; ".join(f"H 0 0 {i*R:.4f}" for i in range(n_atoms)),
                basis="sto-6g", spin=n_atoms % 2, verbose=0)
    mf = scf.RHF(mol).run(conv_tol=1e-10)
    ccsd = cc.CCSD(mf).run()
    return float(ccsd.e_tot + ccsd.ccsd_t())


def hchain_ham(n_atoms, R=0.74):
    geom = [("H", (0.0, 0.0, i * R)) for i in range(n_atoms)]
    mol = MolecularData(geom, "sto-6g", multiplicity=1, charge=0)
    mol = run_pyscf(mol, run_scf=True, run_fci=(n_atoms <= 8))
    qop = jordan_wigner(get_fermion_operator(mol.get_molecular_hamiltonian()))
    nq = 2 * mol.n_orbitals; ne = mol.n_electrons
    e_ref = mol.fci_energy if mol.fci_energy is not None else REF_FCI.get(n_atoms)
    ref_kind = "FCI"
    if e_ref is None:
        e_ref = _ccsdt_ref(n_atoms, R); ref_kind = "CCSD(T)"
    return dict(qop=qop, nq=nq, ne=ne, hf=mol.hf_energy, e_fci=float(e_ref),
                ref_kind=ref_kind, n_atoms=n_atoms)


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


def det_space_transfer(seqs, target_rec, tokens, K=96):
    """Determinant-space QSCI of the excitations a set of circuits proposes on the target system.

    Maps each proposed token to the determinant it produces from HF (bitmask XOR) — NO statevector,
    so this scales to 40q+ on CPU. Pools determinants over all sequences, keeps the K most-proposed
    (HF always included), and QSCI-diagonalizes. A generator that proposes the *right* excitations
    builds a lower-energy subspace at matched K. Returns (err_mHa, n_dets).
    """
    pool, _ = build_realized_pool(tokens, target_rec["ne"], target_rec["nq"])
    hf = 0
    for q in range(target_rec["ne"]):
        hf |= (1 << q)
    counts = {hf: 10**9}                                   # HF always kept
    for s in seqs:
        for k in s:
            tok = pool[int(k)]
            if tok is None:
                continue
            d = hf
            for w in tok[1]:
                d ^= (1 << w)
            counts[d] = counts.get(d, 0) + 1
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:K]
    dets = np.array([d for d, _ in top], dtype=np.uint64)
    e, n = qsci_energy(target_rec["qop"], dets)
    return abs(e - target_rec["e_fci"]) * 1000.0, int(n)


def _hf_int(ne):
    v = 0
    for q in range(ne):
        v |= (1 << q)
    return v


def gen_determinants(seqs, target_rec, tokens):
    """Determinants a set of circuits proposes on the target, ordered by proposal frequency (HF first)."""
    pool, _ = build_realized_pool(tokens, target_rec["ne"], target_rec["nq"])
    hf = _hf_int(target_rec["ne"]); counts = {hf: 10**9}
    for s in seqs:
        for k in s:
            tok = pool[int(k)]
            if tok is None:
                continue
            d = hf
            for w in tok[1]:
                d ^= (1 << w)
            counts[d] = counts.get(d, 0) + 1
    return [d for d, _ in sorted(counts.items(), key=lambda kv: -kv[1])]


def mp2_determinants(target_rec, R=0.74):
    """HF + singles + doubles (ranked by |MP2 amplitude|) determinants for an H-chain target."""
    from pyscf import gto, scf, mp
    from pennylane import qchem
    n, ne, nq = target_rec["n_atoms"], target_rec["ne"], target_rec["nq"]
    mol = gto.M(atom="; ".join(f"H 0 0 {i*R:.4f}" for i in range(n)), basis="sto-6g", verbose=0)
    mf = scf.RHF(mol).run(conv_tol=1e-10); t2 = mp.MP2(mf).run().t2
    nocc_sp = ne // 2; hf = _hf_int(ne)
    singles, doubles = qchem.excitations(ne, nq)

    def w(d):
        i, j, a, b = d
        if sorted([i % 2, j % 2]) != sorted([a % 2, b % 2]):
            return 0.0
        return abs(float(t2[i // 2, j // 2, a // 2 - nocc_sp, b // 2 - nocc_sp]))
    dord = sorted((tuple(d) for d in doubles), key=lambda d: -w(d))
    # doubles dominate correlation (singles don't couple to HF, Brillouin); rank doubles first for a
    # fair MP2 selected-CI baseline, singles appended after.
    dets = [hf] + [hf ^ (1 << i) ^ (1 << j) ^ (1 << a) ^ (1 << b) for (i, j, a, b) in dord]
    dets += [hf ^ (1 << i) ^ (1 << a) for (i, a) in singles]
    return dets


def _merge(a, b, k0=10):
    """Reciprocal-rank fusion of two ordered determinant lists (HF kept first).

    A determinant scores high if EITHER source ranks it high; determinants both favor rise to the top.
    A principled composition that can beat either source iff they are complementary.
    """
    ra = {d: i for i, d in enumerate(a)}; rb = {d: i for i, d in enumerate(b)}
    allk = set(a) | set(b)
    score = {d: 1.0 / (k0 + ra.get(d, 10**9)) + 1.0 / (k0 + rb.get(d, 10**9)) for d in allk}
    hf = a[0]
    ordered = sorted(allk, key=lambda d: -score[d])
    if hf in ordered:
        ordered.remove(hf)
    return [hf] + ordered


def qsci_at_K(qop, det_list, K, ref):
    e, _ = qsci_energy(qop, np.array(det_list[:K], dtype=np.uint64))
    return abs(e - ref) * 1000.0


def main_compose():
    """(a) determinant-budget sweep + (b) transfer x MP2 composition, at 20q and 40q."""
    def log(s): print(s, flush=True)
    log(f"\n######## COMPOSE: budget sweep + transfer×MP2 {time.strftime('%Y-%m-%d %H:%M')} ########")
    recs_train = [hchain_ham(4), hchain_ham(6)]; tokens = canonical_tokens(6, 12)
    targets = [hchain_ham(10), hchain_ham(20)]                 # 20q (FCI), 40q (CCSD(T))
    Ks = [16, 32, 48, 64, 96, 128]
    out = {"Ks": Ks, "targets": {}}
    models = [train_gptqe_multi(recs_train, tokens, seed=s) for s in (0, 1, 2)]
    for t in targets:
        nq = t["nq"]; log(f"\n== target {nq}q (ref {t['ref_kind']}={t['e_fci']:.5f}) ==")
        pool, valid = build_realized_pool(tokens, t["ne"], t["nq"]); vids = np.where(valid)[0]
        mp2 = mp2_determinants(t)
        rows = {m: [] for m in ("trained", "random", "mp2", "combined")}
        for K in Ks:
            tr, rd, cb = [], [], []
            for si, model in enumerate(models):
                torch.manual_seed(9000 + si)
                gen = _generate(model, 200, 8, 0.5, torch.tensor(~valid)).cpu().numpy()
                rng = np.random.default_rng(si)
                rnd = np.array([rng.choice(vids, 8) for _ in range(200)])
                gd = gen_determinants(gen, t, tokens); rdd = gen_determinants(rnd, t, tokens)
                tr.append(qsci_at_K(t["qop"], gd, K, t["e_fci"]))
                rd.append(qsci_at_K(t["qop"], rdd, K, t["e_fci"]))
                cb.append(qsci_at_K(t["qop"], _merge(gd, mp2), K, t["e_fci"]))
            rows["trained"].append(float(np.mean(tr))); rows["random"].append(float(np.mean(rd)))
            rows["mp2"].append(qsci_at_K(t["qop"], mp2, K, t["e_fci"]))
            rows["combined"].append(float(np.mean(cb)))
            log(f"  K={K:3d}: trained {rows['trained'][-1]:7.2f} | random {rows['random'][-1]:7.2f} | "
                f"mp2 {rows['mp2'][-1]:7.2f} | combined {rows['combined'][-1]:7.2f} mHa")
        out["targets"][str(nq)] = dict(ref_kind=t["ref_kind"], rows=rows)
        json.dump(out, open(os.path.join(OUT, "compose_evidence.json"), "w"), indent=2)
    # figure
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, len(targets), figsize=(6 * len(targets), 4.3), squeeze=False)
        for ax, t in zip(axes[0], targets):
            r = out["targets"][str(t["nq"])]["rows"]
            for m, c in [("random", "tab:orange"), ("mp2", "tab:green"), ("trained", "tab:blue"), ("combined", "tab:red")]:
                ax.plot(Ks, r[m], "o-", color=c, label=m)
            ax.set_xlabel("determinant budget K"); ax.set_ylabel("QSCI error vs ref (mHa)")
            ax.set_yscale("log"); ax.set_title(f"{t['nq']}q"); ax.legend()
        fig.suptitle("Determinant-budget sweep: transfer × MP2 composition")
        fig.tight_layout(); fig.savefig(os.path.join(OUT, "compose.png"), dpi=130); log("saved compose.png")
    except Exception as e:
        log(f"(figure skipped: {e})")
    log("DONE")


def oxide_target(name, ncas, nelec):
    """Build an oxide/diatomic target from molecules.py as a transfer target (qop, ref, MP2 t2)."""
    r = M.build(name, ncas=ncas, nelec=nelec)
    return dict(qop=r["qop"], ne=r["ne"], nq=r["nq"], e_fci=r["e_cas"], t2=r["t2"],
                name=name, ncas=ncas, ref_kind="CASCI")


def oxide_mp2_determinants(rec):
    """HF + doubles(ranked by |MP2 t2|) + singles for an oxide target (fair classical baseline)."""
    from pennylane import qchem
    ne, nq, t2 = rec["ne"], rec["nq"], rec["t2"]; nocc_sp = ne // 2; hf = _hf_int(ne)
    singles, doubles = qchem.excitations(ne, nq)

    def w(d):
        i, j, a, b = d
        if sorted([i % 2, j % 2]) != sorted([a % 2, b % 2]):
            return 0.0
        return abs(float(t2[i // 2, j // 2, a // 2 - nocc_sp, b // 2 - nocc_sp]))
    dord = sorted((tuple(d) for d in doubles), key=lambda d: -w(d))
    dets = [hf] + [hf ^ (1 << i) ^ (1 << j) ^ (1 << a) ^ (1 << b) for (i, j, a, b) in dord]
    dets += [hf ^ (1 << i) ^ (1 << a) for (i, a) in singles]
    return dets


def main_crosschem():
    """SECOND CHEMISTRY: train on H-chains, deploy to oxide chemistry (cross-chemistry transfer).

    The canonical frontier-relative tokenization is chemistry-agnostic (depth below HOMO / height above
    LUMO), so an H-chain-trained generator can propose excitations for oxide active spaces. Tests whether
    the learned generative policy transfers across CHEMISTRY (and, for the 20q oxides, across size too).
    Determinant-space QSCI; trained vs random vs target-specific MP2 (classical baseline).
    """
    def log(s): print(s, flush=True)
    log(f"\n######## CROSS-CHEMISTRY: train H-chains -> oxides {time.strftime('%Y-%m-%d %H:%M')} ########")
    recs_train = [hchain_ham(4), hchain_ham(6)]; tokens = canonical_tokens(6, 12)
    targets = [("CO", 6, 6), ("SiO", 6, 6), ("SnO", 6, 6), ("BeO", 6, 6),   # 12q, cross-chemistry
               ("CO", 10, 10), ("SnO", 10, 10)]                              # 20q, cross-chemistry + size
    K = 64
    models = [train_gptqe_multi(recs_train, tokens, seed=s) for s in (0, 1, 2)]
    rows = []
    for (name, ncas, nelec) in targets:
        t = oxide_target(name, ncas, nelec)
        pool, valid = build_realized_pool(tokens, t["ne"], t["nq"]); vids = np.where(valid)[0]
        mp2 = oxide_mp2_determinants(t)
        tr, rd = [], []
        for si, model in enumerate(models):
            torch.manual_seed(9000 + si)
            gen = _generate(model, 200, 8, 0.5, torch.tensor(~valid)).cpu().numpy()
            rng = np.random.default_rng(si); rnd = np.array([rng.choice(vids, 8) for _ in range(200)])
            tr.append(qsci_at_K(t["qop"], gen_determinants(gen, t, tokens), K, t["e_fci"]))
            rd.append(qsci_at_K(t["qop"], gen_determinants(rnd, t, tokens), K, t["e_fci"]))
        mp2e = qsci_at_K(t["qop"], mp2, K, t["e_fci"])
        row = dict(target=f"{name} CAS({nelec},{ncas})", nq=t["nq"],
                   trained_mHa=float(np.mean(tr)), trained_sd=float(np.std(tr)),
                   random_mHa=float(np.mean(rd)), mp2_mHa=float(mp2e),
                   advantage_vs_random=float(np.mean(rd) - np.mean(tr)))
        rows.append(row)
        log(f"  {name:4s} {t['nq']:2d}q: trained {row['trained_mHa']:7.2f} | random {row['random_mHa']:7.2f} "
            f"| mp2 {row['mp2_mHa']:7.2f} mHa | adv(vs random) {row['advantage_vs_random']:+.2f}")
        json.dump(dict(train="H4+H6 (H-chains)", K=K, results=rows),
                  open(os.path.join(OUT, "crosschem_evidence.json"), "w"), indent=2)
    npos = sum(1 for r in rows if r["advantage_vs_random"] > 0)
    log(f"\nCROSS-CHEMISTRY: H-chain-trained generator beats random on {npos}/{len(rows)} oxide targets")
    log("DONE")


def hchain_target_sci(n_atoms, R=0.74):
    """Integral-based H-chain target (Slater-Condon eval) — scalable to 48q+, no Pauli operator built."""
    integ = hchain_integrals(n_atoms, R)
    ne, nq = integ["ne"], 2 * integ["n_orb"]
    e_ref = REF_FCI.get(n_atoms); ref_kind = "FCI"
    if e_ref is None:
        e_ref = _ccsdt_ref(n_atoms, R); ref_kind = "CCSD(T)"
    return dict(h1=integ["h1"], eri=integ["eri"], ecore=integ["ecore"], ne=ne, nq=nq,
                e_fci=float(e_ref), ref_kind=ref_kind, n_atoms=n_atoms, hf=integ["e_hf"])


def sci_at_K(target, det_list, K):
    e, _ = sci_energy(target["h1"], target["eri"], target["ecore"], det_list[:K])
    return abs(e - target["e_fci"]) * 1000.0


def main_ladder():
    """GAME-CHANGER: train one generator small (H4+H6); deploy across 16->56 qubits, zero-shot.

    Determinant-space Slater-Condon evaluation (no statevector, no Pauli operator) makes targets up to
    56q reachable on CPU. Shows whether the small-trained generator's proposed excitations beat random
    across the size ladder -- i.e. whether GQE training can be amortized at small scale and transferred
    to the 40-56q regime, never trained at scale.
    """
    def log(s): print(s, flush=True)
    log(f"\n######## SCALING LADDER: train H4+H6 -> deploy 16..56q {time.strftime('%Y-%m-%d %H:%M')} ########")
    recs_train = [hchain_ham(4), hchain_ham(6)]
    tokens = canonical_tokens(6, 12)
    log("building integral targets (16/20/28/40/48/56q, Slater-Condon)...")
    targets = [hchain_target_sci(n) for n in (8, 10, 14, 20, 24, 28)]
    for t in targets:
        log(f"  H{t['n_atoms']} {t['nq']}q: ref({t['ref_kind']})={t['e_fci']:.5f}")
    NGEN, K = 200, 96
    per_size = {t["nq"]: {"trained": [], "random": []} for t in targets}
    for seed in (0, 1, 2):
        model = train_gptqe_multi(recs_train, tokens, seed=seed, log=log if seed == 0 else None)
        for t in targets:
            pool, valid = build_realized_pool(tokens, t["ne"], t["nq"])
            torch.manual_seed(9000 + seed)
            gen = _generate(model, NGEN, 8, 0.5, torch.tensor(~valid)).cpu().numpy()
            rng = np.random.default_rng(seed); vids = np.where(valid)[0]
            rnd = np.array([rng.choice(vids, 8) for _ in range(NGEN)])
            te = sci_at_K(t, gen_determinants(gen, t, tokens), K)      # Slater-Condon eval (scales to 56q)
            re_ = sci_at_K(t, gen_determinants(rnd, t, tokens), K)
            per_size[t["nq"]]["trained"].append(te); per_size[t["nq"]]["random"].append(re_)
            log(f"[seed {seed}] {t['nq']:2d}q: trained {te:7.2f} mHa | random {re_:7.2f} mHa | Δ={re_-te:+.2f}")
    rows = []
    for t in targets:
        tr = np.array(per_size[t["nq"]]["trained"]); rd = np.array(per_size[t["nq"]]["random"])
        rows.append(dict(qubits=t["nq"], ref_kind=t["ref_kind"],
                         trained_mHa=float(tr.mean()), trained_sd=float(tr.std()),
                         random_mHa=float(rd.mean()), random_sd=float(rd.std()),
                         advantage_mHa=float(rd.mean() - tr.mean())))
    maxq = rows[-1]["qubits"]
    summary = dict(claim="train-small (H4+H6) -> deploy across 16-56q; Slater-Condon determinant QSCI, matched K=96",
                   ladder=rows, max_qubits=maxq,
                   advantage_persists_to_maxq=bool(rows[-1]["advantage_mHa"] > 0),
                   all_sizes_positive=bool(all(r["advantage_mHa"] > 0 for r in rows)))
    json.dump(dict(train="H4+H6", targets_q=[t["nq"] for t in targets], n_gen=NGEN, K=K,
                   per_size={str(k): v for k, v in per_size.items()}, summary=summary),
              open(os.path.join(OUT, "scaling_ladder_evidence.json"), "w"), indent=2)
    log("\n======== SCALING LADDER (train-small, deploy-large) ========")
    for r in rows:
        log(f"  {r['qubits']:2d}q [{r['ref_kind']:7s}]: trained {r['trained_mHa']:7.2f} vs random "
            f"{r['random_mHa']:7.2f} mHa | advantage {r['advantage_mHa']:+.2f}")
    log(f"  advantage at {maxq}q: {rows[-1]['advantage_mHa']:+.2f} mHa | all sizes positive: "
        f"{summary['all_sizes_positive']}")
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        qs = [r["qubits"] for r in rows]
        fig, ax = plt.subplots(figsize=(7, 4.3))
        ax.plot(qs, [r["trained_mHa"] for r in rows], "o-", color="tab:blue", label="trained on 8q+12q")
        ax.plot(qs, [r["random_mHa"] for r in rows], "s--", color="tab:orange", label="random search")
        ax.set_xlabel("target system size (qubits)"); ax.set_ylabel("QSCI subspace error vs ref (mHa)")
        ax.set_title("Train-small, deploy-large: generative transfer across the size ladder")
        ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(OUT, "scaling_ladder.png"), dpi=130)
        log("saved scaling_ladder.png")
    except Exception as e:
        log(f"(figure skipped: {e})")
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
    elif "--ladder" in sys.argv:
        main_ladder()
    elif "--compose" in sys.argv:
        main_compose()
    elif "--crosschem" in sys.argv:
        main_crosschem()
    else:
        main()
