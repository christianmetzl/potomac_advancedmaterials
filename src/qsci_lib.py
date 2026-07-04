"""Shared library for the Phase-3 GPU/QPU run-list: compressed MP2 circuit (CUDA-Q) + fast QSCI engine.

Everything here is exercised on CPU by the smoke tests (see GPU_RUNLIST.md); on qBraid the ONLY change
is the CUDA-Q target string (tensornet-mps / nvidia / ionq ...). Conventions: interleaved spin-orbitals
(alpha = even qubit, beta = odd), matching OpenFermion spinorb_from_spatial — validated against exact
FCI in cudaq_qsci.py (H4, +0.01 mHa).

Pieces:
  hchain_problem(n)          -> integrals + qubit Hamiltonian terms + FCI ref (<=20q) for Hn chains
  cas_problem(...)           -> same for a CASCI active space (open-shell OK), no FCI solve needed
  mp2_compressed_circuit(..) -> top-M excitations by |MP2 t2| as CUDA-Q wire lists + first-order angles
  compressed_ucc (kernel)    -> HF + those excitations via CUDA-Q single/double excitation sub-kernels
  sample_dets(...)           -> cudaq.sample on the chosen target -> number-conserving determinants
  PauliEngine                -> vectorized bitmask engine: subspace H build, diagonalize, CIPSI growth
EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, time, numpy as np
import cudaq
from cudaq.kernels.uccsd import single_excitation, double_excitation_opt
from pyscf import gto, scf, mp, ao2mo, fci, mcscf
from openfermion import InteractionOperator, get_fermion_operator, jordan_wigner
from openfermion.chem.molecular_data import spinorb_from_spatial
import scipy.sparse as sp, scipy.sparse.linalg as sla

_PC = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)
def _parity(x): b = x.view(np.uint8).reshape(-1, 8); return (_PC[b].sum(1) & 1).astype(np.int8)


# ---------------- problem builders ----------------
def _qop_from_spatial(h1, eri_chem, ecore):
    one_so, two_so = spinorb_from_spatial(h1, np.asarray(eri_chem.transpose(0, 2, 3, 1), order="C"))
    return jordan_wigner(get_fermion_operator(InteractionOperator(ecore, one_so, 0.5 * two_so)))


def hchain_problem(n_atoms, R=0.74, do_fci=None):
    """Hn chain: integrals, MP2 t2, qubit Hamiltonian, and FCI reference where tractable."""
    mol = gto.M(atom="; ".join(f"H 0 0 {i*R:.4f}" for i in range(n_atoms)), basis="sto-6g", verbose=0)
    mf = scf.RHF(mol).run(conv_tol=1e-10)
    norb = mf.mo_coeff.shape[1]; ne = mol.nelectron
    h1 = mf.mo_coeff.T @ mf.get_hcore() @ mf.mo_coeff
    eri = ao2mo.restore(1, ao2mo.kernel(mol, mf.mo_coeff), norb)
    ecore = float(mol.energy_nuc())
    t2 = mp.MP2(mf).run(verbose=0).t2
    if do_fci is None:
        do_fci = n_atoms <= 10
    e_ref = float(fci.FCI(mf).kernel()[0]) if do_fci else None
    qop = _qop_from_spatial(h1, eri, ecore)
    return dict(ne=ne, nq=2 * norb, nocc=ne // 2, t2=t2, qop=qop, e_fci=e_ref,
                e_hf=float(mf.e_tot), h1=h1, eri=eri, ecore=ecore)


def cas_problem(atom, basis, spin, ncas, nelecas, ecp=None, charge=0, solve_casci=False,
                density_fit=False, level_shift=0.0):
    """CASCI active-space problem (open-shell OK). solve_casci=False skips the exact solve
    (mandatory for large CAS, e.g. CAS(19,19)=38q where FCI is impossible)."""
    mol = gto.M(atom=atom, basis=basis, ecp=ecp or {}, spin=spin, charge=charge, verbose=0)
    mf = scf.ROHF(mol)
    if density_fit: mf = mf.density_fit()
    if level_shift: mf.level_shift = level_shift
    mf.max_cycle = 300; mf.conv_tol = 1e-9; mf.kernel()
    if not mf.converged:
        mf.level_shift = 0.0; mf.init_guess = "atom"; mf.kernel()
    mc = mcscf.CASCI(mf, ncas, nelecas); mc.verbose = 0
    e_ref = float(mc.kernel()[0]) if solve_casci else None
    h1e, ecore = mc.get_h1eff(); eri = ao2mo.restore(1, mc.get_h2eff(), ncas)
    qop = _qop_from_spatial(h1e, eri, ecore)
    na, nb = nelecas if isinstance(nelecas, (tuple, list)) else (nelecas // 2, nelecas // 2)
    return dict(ne=na + nb, na=na, nb=nb, nq=2 * ncas, qop=qop, e_ref=e_ref,
                h1=h1e, eri=eri, ecore=float(ecore), rohf_converged=bool(mf.converged), mf=mf, mc=mc)


def hf_det(na, nb=None):
    """Interleaved HF bitstring: alpha on even qubits, beta on odd."""
    if nb is None:                       # closed shell, ne total
        return (1 << na) - 1
    d = 0
    for i in range(na): d |= 1 << (2 * i)
    for i in range(nb): d |= 1 << (2 * i + 1)
    return d


# ---------------- compressed MP2 circuit ----------------
def mp2_excitation_lists(t2, nocc, nq, top_m=64, amp_floor=1e-6):
    """Top-M spin-orbital double excitations by |MP2 amplitude| (interleaved wires) + matching angles.
    Returns dict of parallel int lists for the CUDA-Q kernel. First-order UCC: theta = amplitude."""
    nvirt = nq // 2 - nocc
    cand = []
    for i in range(nocc):
        for j in range(nocc):
            for a in range(nvirt):
                for b in range(nvirt):
                    # mixed spin (i-alpha, j-beta) -> (a-alpha, b-beta): amplitude t2[i,j,a,b]
                    amp = float(t2[i, j, a, b])
                    if abs(amp) > amp_floor:
                        cand.append((abs(amp), amp, 2 * i, 2 * j + 1, 2 * (nocc + a), 2 * (nocc + b) + 1))
    for i in range(nocc):
        for j in range(i + 1, nocc):
            for a in range(nvirt):
                for b in range(a + 1, nvirt):
                    anti = float(t2[i, j, a, b] - t2[i, j, b, a])     # same-spin antisymmetrized
                    if abs(anti) > amp_floor:
                        cand.append((abs(anti), anti, 2 * i, 2 * j, 2 * (nocc + a), 2 * (nocc + b)))          # alpha-alpha
                        cand.append((abs(anti), anti, 2 * i + 1, 2 * j + 1, 2 * (nocc + a) + 1, 2 * (nocc + b) + 1))  # beta-beta
    cand.sort(key=lambda x: -x[0])
    cand = cand[:top_m]
    return dict(p=[c[2] for c in cand], q=[c[3] for c in cand], r=[c[4] for c in cand],
                s=[c[5] for c in cand], th=[c[1] for c in cand])


@cudaq.kernel
def compressed_ucc(n_qubits: int, n_electrons: int,
                   dp: list[int], dq: list[int], dr: list[int], ds: list[int], dth: list[float]):
    """HF reference + top-M double excitations (Givens rotations) — the pool-compressed GQE-style circuit."""
    qubits = cudaq.qvector(n_qubits)
    for i in range(n_electrons):
        x(qubits[i])
    for k in range(len(dth)):
        double_excitation_opt(qubits, dp[k], dq[k], dr[k], ds[k], dth[k])


def sample_dets(nq, ne, exc, shots, target=None, noise_model=None):
    """Sample the compressed circuit on the given CUDA-Q target; return number-conserving determinants
    with counts (dict det->count) and raw distinct-bitstring count."""
    if target:
        cudaq.set_target(target)
    kw = dict(shots_count=shots)
    if noise_model is not None:
        kw["noise_model"] = noise_model
    counts = cudaq.sample(compressed_ucc, nq, ne, exc["p"], exc["q"], exc["r"], exc["s"], exc["th"], **kw)
    dets = {}
    nraw = 0
    for bits, cnt in counts.items():
        nraw += 1
        d = 0
        for qb, ch in enumerate(bits):
            if ch == "1": d |= (1 << qb)
        if bin(d).count("1") == ne:
            dets[d] = dets.get(d, 0) + int(cnt)
    return dets, nraw


# ---------------- fast Pauli bitmask QSCI engine ----------------
class PauliEngine:
    """Vectorized determinant-subspace engine on a JW qubit Hamiltonian (validated 0.0000 mHa vs
    Slater-Condon / Jordan-Wigner cross-checks in the committed pipeline; runs to 56q)."""

    def __init__(self, qop_terms):
        XM = []; ZYM = []; PH = []
        for pauli, coeff in qop_terms.items():
            xm = zym = nY = 0
            for qb, op in pauli:
                if op in ("X", "Y"): xm |= (1 << qb)
                if op in ("Z", "Y"): zym |= (1 << qb)
                if op == "Y": nY += 1
            XM.append(xm); ZYM.append(zym); PH.append(complex(coeff) * (1j) ** nY)
        self.XM = np.array(XM, dtype=np.uint64); self.ZYM = np.array(ZYM, dtype=np.uint64)
        self.PH = np.array(PH, dtype=np.complex128)
        dm = self.XM == 0; self.ZYMd = self.ZYM[dm]; self.PHd = self.PH[dm]

    def Hon(self, c):
        cc = np.uint64(c)
        return np.bitwise_xor(cc, self.XM), self.PH * (1 - 2 * _parity(np.bitwise_and(cc, self.ZYM)))

    def diag(self, dets):
        """Diagonal Hamiltonian energy of each determinant. Vectorized + chunked (identical values to
        the per-det formula) so it scales to 1e6 candidates without a Python loop."""
        d = np.asarray([int(x) for x in dets], dtype=np.uint64)
        if len(d) == 0:
            return np.empty(0)
        phd = self.PHd.real                                    # diagonal coeffs are real
        out = np.empty(len(d))
        step = max(1, 4_000_000 // max(1, len(phd)))           # cap block memory (~few hundred MB)
        for s in range(0, len(d), step):
            blk = d[s:s + step]
            A = np.bitwise_and(blk[:, None], self.ZYMd[None, :])   # (nblk, ndiag) uint64
            par = _parity(A.reshape(-1)).reshape(A.shape)          # 0/1 per entry
            out[s:s + step] = ((1 - 2 * par.astype(np.int64)) * phd[None, :]).sum(axis=1)
        return out

    def build_H(self, space):
        sc = np.sort(space); order = np.argsort(space); n = len(space); R_, C, V = [], [], []
        for i, c in enumerate(space):
            nc, amp = self.Hon(int(c))
            pos = np.clip(np.searchsorted(sc, nc), 0, n - 1); v = sc[pos] == nc
            j = order[pos[v]]; R_.append(j); C.append(np.full(j.shape, i)); V.append(amp[v])
        return sp.csr_matrix((np.concatenate(V), (np.concatenate(R_), np.concatenate(C))),
                             shape=(n, n), dtype=complex)

    def ground(self, space):
        H = self.build_H(space)
        if H.shape[0] < 6:
            w, v = np.linalg.eigh(H.toarray()); return float(w[0]), np.asarray(v[:, 0]).ravel()
        w, v = sla.eigsh(H, k=1, which="SA")
        return float(w[0]), np.asarray(v[:, 0]).ravel()

    def qsci(self, seed_dets, grow_iters=0, grow_per_iter=400, kcap=6000, tcap=1e9, log=None):
        """Diagonalize in the seed subspace; optionally CIPSI-grow (device-seeded selected-CI).
        Returns (E, space). grow_iters=0 = pure sampled-subspace QSCI."""
        space = np.array(sorted(set(int(d) for d in seed_dets)), dtype=np.uint64)
        t0 = time.time(); E, cvec = self.ground(space)
        if log: log(f"  QSCI seed |space|={len(space)}  E={E:.6f}  [{time.time()-t0:.0f}s]")
        for it in range(grow_iters):
            if len(space) >= kcap or time.time() - t0 > tcap: break
            sc = np.sort(space); contrib = {}
            for ci in np.where(np.abs(cvec) > 1e-4)[0]:
                nc, amp = self.Hon(int(space[ci]))
                pos = np.clip(np.searchsorted(sc, nc), 0, len(space) - 1); ins = sc[pos] == nc
                for u, a in zip(nc[~ins].tolist(), (amp[~ins] * cvec[ci]).tolist()):
                    contrib[u] = contrib.get(u, 0) + a
            if not contrib: break
            cand = np.array(list(contrib.keys()), dtype=np.uint64)
            num = np.array(list(contrib.values()))
            den = E - self.diag(cand); den[np.abs(den) < 1e-9] = -1e-9
            keep = cand[np.argsort(np.abs(num) ** 2 / np.abs(den))[::-1][:grow_per_iter]]
            space = np.concatenate([space, np.setdiff1d(keep, space)])
            E, cvec = self.ground(space)
            if log: log(f"  QSCI grow it{it+1} |space|={len(space)}  E={E:.6f}  [{time.time()-t0:.0f}s]")
        return E, space

    # ---- fast incremental path (Option C) -------------------------------------------------------
    # Identical determinant SELECTION as qsci() above (character-for-character), so energies match
    # bit-for-bit; the only change is the Hamiltonian is built INCREMENTALLY (matrix elements for a
    # newly added determinant are computed once and cached, never recomputed) and the eigensolver is
    # warm-started. This turns the O(|space|) per-iteration rebuild (the 40q wall) into O(delta).
    def _cache_reset(self):
        self._id2det = []                 # insertion-order determinant list (id == index)
        self._det2id = {}
        self._Hr, self._Hc, self._Hv = [], [], []   # accumulated COO triplets (never recomputed)

    def _cache_add(self, dets):
        """Append new determinants and emit their Hamiltonian rows (+ transpose into old columns)."""
        first_new = len(self._id2det)
        for d in (int(x) for x in dets):
            if d in self._det2id:
                continue
            self._det2id[d] = len(self._id2det); self._id2det.append(d)
        alld = np.array(self._id2det, dtype=np.uint64)
        order = np.argsort(alld); sd = alld[order]; sid = order.astype(np.int64)
        for k in range(first_new, len(self._id2det)):
            nc, amp = self.Hon(int(self._id2det[k]))
            pos = np.clip(np.searchsorted(sd, nc), 0, len(sd) - 1)
            found = sd[pos] == nc
            cols = sid[pos[found]]; vals = amp[found]
            self._Hr.append(np.full(cols.shape, k, dtype=np.int64)); self._Hc.append(cols); self._Hv.append(vals)
            old = cols < first_new                       # old rows are missing this new column -> add transpose
            if old.any():
                self._Hr.append(cols[old]); self._Hc.append(np.full(int(old.sum()), k, dtype=np.int64))
                self._Hv.append(np.conj(vals[old]))

    def _cache_solve(self, warm=None):
        n = len(self._id2det)
        H = sp.csr_matrix((np.concatenate(self._Hv),
                           (np.concatenate(self._Hr), np.concatenate(self._Hc))),
                          shape=(n, n), dtype=complex)
        if n < 6:
            w, v = np.linalg.eigh(H.toarray()); return float(w[0]), np.asarray(v[:, 0]).ravel()
        v0 = None
        if warm is not None:
            v0 = np.zeros(n, dtype=complex); v0[:len(warm)] = warm
        w, v = sla.eigsh(H, k=1, which="SA", v0=v0)
        return float(w[0]), np.asarray(v[:, 0]).ravel()

    def qsci_fast(self, seed_dets, grow_iters=0, grow_per_iter=400, kcap=6000, tcap=1e9, log=None):
        """Incremental-Hamiltonian equivalent of qsci(); identical energies, O(delta)/iter instead of
        O(|space|). Space/id order mirrors qsci() exactly (sorted seed, then sorted new dets appended),
        so the eigenvector indexing and hence the CIPSI selection are the same at every step."""
        space = np.array(sorted(set(int(d) for d in seed_dets)), dtype=np.uint64)
        self._cache_reset(); self._cache_add(space)
        t0 = time.time(); E, cvec = self._cache_solve()
        if log: log(f"  QSCI* seed |space|={len(space)}  E={E:.6f}  [{time.time()-t0:.0f}s]")
        for it in range(grow_iters):
            if len(space) >= kcap or time.time() - t0 > tcap: break
            sc = np.sort(space)
            sig = np.where(np.abs(cvec) > 1e-4)[0]
            # CIPSI candidate scan, chunked + compacted so memory stays bounded at large scale: the
            # (candidate, amplitude) buffer is unique-reduced after every batch instead of concatenating
            # every connection first (which balloons to GBs at 28q+). Per-candidate sum is identical.
            cand = np.empty(0, dtype=np.uint64); num = np.empty(0, dtype=complex)
            BATCH = 300
            for b0 in range(0, len(sig), BATCH):
                us, as_ = [cand], [num]
                for ci in sig[b0:b0 + BATCH]:
                    nc, amp = self.Hon(int(space[ci]))
                    pos = np.clip(np.searchsorted(sc, nc), 0, len(space) - 1); ext = sc[pos] != nc
                    us.append(nc[ext]); as_.append(amp[ext] * cvec[ci])
                allu = np.concatenate(us); alla = np.concatenate(as_)
                cand, inv = np.unique(allu, return_inverse=True)
                num = np.zeros(len(cand), dtype=complex); np.add.at(num, inv, alla)
            if len(cand) == 0: break
            den = E - self.diag(cand); den[np.abs(den) < 1e-9] = -1e-9
            keep = cand[np.argsort(np.abs(num) ** 2 / np.abs(den))[::-1][:grow_per_iter]]
            newd = np.setdiff1d(keep, space)
            if len(newd) == 0: break
            self._cache_add(newd); space = np.concatenate([space, newd])
            E, cvec = self._cache_solve(warm=cvec)
            if log: log(f"  QSCI* grow it{it+1} |space|={len(space)}  E={E:.6f}  [{time.time()-t0:.0f}s]")
        return E, space


def peak_rss_gb():
    """Peak resident HOST memory of this process (GB). NOT the P3 metric on GPU runs (P3 is DEVICE
    memory); use DeviceMemMonitor for that. Kept for CPU runs and transparency."""
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 ** 2)


class DeviceMemMonitor:
    """Poll nvidia-smi in a background thread and record PEAK GPU device memory (GB) for the P3
    criterion. On a dedicated instance the job is the sole consumer, so device-wide 'used' == our
    peak. On a box without a GPU (CPU smoke), nvidia-smi is absent and .gb() returns None so the
    caller falls back to host RSS with an explicit note. Usage:  with DeviceMemMonitor() as m: ...  """
    def __init__(self, interval=0.5):
        self.interval = interval; self.peak_mb = 0.0; self._stop = False; self._t = None; self._ok = False

    def _poll(self):
        import subprocess
        while not self._stop:
            try:
                out = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                    stderr=subprocess.DEVNULL, timeout=5).decode()
                self.peak_mb = max([self.peak_mb] + [float(x) for x in out.strip().splitlines() if x.strip()])
                self._ok = True
            except Exception:
                pass
            _t0 = time.time()
            while not self._stop and time.time() - _t0 < self.interval:
                time.sleep(0.05)

    def start(self):
        import threading
        self._t = threading.Thread(target=self._poll, daemon=True); self._t.start(); return self

    def stop(self):
        self._stop = True
        if self._t: self._t.join(timeout=2)

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()

    def gb(self):
        """Peak device memory in GB, or None if no GPU was observed (CPU run)."""
        return round(self.peak_mb / 1024.0, 2) if self._ok else None
