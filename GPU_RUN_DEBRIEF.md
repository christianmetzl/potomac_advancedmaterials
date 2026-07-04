# GPU-day debrief — EIGENNEXUS GIC 2026 Phase 3

**For:** the main Claude Code instance integrating results into the paper.
**From:** the GPU-execution session (branch `claude/wonderful-bohr-rir81t`).
**Date:** 2026-07-04.
**Scope:** honest report of the pre-registered GPU/QPU runs executed on a qBraid RTX 4090 Lab
instance, plus root-caused bugs and prioritized recommendations for a re-run. Numbers here match
the committed evidence JSONs exactly; nothing was tuned after the fact and no pre-registered
threshold was moved.

---

## 1. What was run and what happened (verbatim)

| Run | System / target | Result vs committed reference | Prereg verdict | Wall-clock | Commit |
|---|---|---|---|---|---|
| Sanity | `run_gpu_phase3.py --dry-run` (CPU) | all 4 runs GREEN | — | ~6 min | — |
| **Run 2** | 20q H₁₀, `nvidia` (cuStateVec) | E = −5.202826 vs **FCI** → **+0.000 mHa** (exact) | **PASS** (P1 ✅, exact validation ✅) | 870 s | `e5799b9` |
| **Run 1** ⭐ | 40q H₂₀, `tensornet-mps` | E = −10.277377 vs **DMRG χ=400** (−10.292194) → **+14.8 mHa** at iter 6/60 | **P1 FAIL · P2 FAIL · P3 FAIL** | ~4.5 h (checkpointed) | `cfc5179` |
| **Run 3** | 38q CrO CAS(18,19), CPU QSCI | E = −1118.038598 vs **DMRG χ=400 same-CAS** (−1118.045626) → **+7.03 mHa** at iter 8/80 | **P4 FAIL** | ~38 min (checkpointed) | `747f58c` |

Evidence files (all pushed to the branch):
- `results/gpu_run1_h10_nvidia_evidence.json` — Run 2 (machine-generated, complete run).
- `results/gpu_run1_h20_mps_CHECKPOINT_evidence.json` + `..._rawlog.txt` — Run 1 (hand-built checkpoint).
- `results/gpu_run4_cro38q_CHECKPOINT_evidence.json` + `..._rawlog.txt` — Run 3 (hand-built checkpoint).

Runs 4 (real QPU, P5) and the blind holdout H1 were **not** part of this GPU session (P5 was already
executed on the hosted sim per prior commits; H1 is a CPU one-shot).

### Pre-registered predictions, as judged
- **P1** (40q QSCI within 1.6 mHa of DMRG χ=400): **FAIL** — +14.8 mHa at the stop point,
  converging geometrically to a ~+13 mHa asymptote.
- **P2** (converged determinant budget in [3×10⁵, 4×10⁶]): **FAIL** — the run's growth schedule
  caps at ~6×10⁴ determinants, an order of magnitude below the band (see §3, bug #2).
- **P3** (peak **device** memory < 8 GB): **FAIL** — peak device memory 12.06 GB (nvidia-smi).
  (The script's built-in metric measures host RSS and would have mislabeled this PASS — see bug #1.)
- **P4** (38q CrO QSCI within 1.6 mHa of same-CAS DMRG): **FAIL** — +7.03 mHa, converging to
  ~+3.7 mHa. P4 was pre-registered as the lowest-confidence prediction; it failed as flagged.

---

## 2. The honest bottom line

**The QSCI engine is correct; the at-scale failures are about cost, not method validity.**
H₄/H₆/H₁₀ all reproduce FCI to +0.000 mHa (Run 2 is the exact-validation point and it PASSED).
Everything that failed did so because the pre-registered growth schedules cannot reach the
determinant counts needed for chemical accuracy within feasible compute — and the QSCI growth phase
is implemented in a way that makes reaching those counts infeasible on this hardware (§3).

This is a legitimate, publishable *negative* result: the pipeline is validated exact at small scale,
and the honest finding is that the pre-registered 40q/38q configurations under-provision
determinants and the current growth implementation does not scale to close the gap in a GPU day.
The pre-registration is what makes the negative result credible — thresholds were fixed in advance
and none were moved.

---

## 3. Confirmed bugs

### Bug #1 — P3 measures host RSS, not device memory (verdict-affecting)
`src/qsci_lib.py:211` `peak_rss_gb()` returns `resource.getrusage().ru_maxrss` = **host** peak RSS,
but the runner labels it "P3 device memory < 8 GB", and P3 is pre-registered explicitly as *device*
memory. This mislabels in **both** directions:

| Run | host RSS (script) | true device (nvidia-smi) | script verdict | correct verdict |
|---|---|---|---|---|
| Run 1 (40q MPS) | 7.87 GB | **12.06 GB** | would say PASS | **FAIL** |
| Run 2 (20q cuStateVec) | 9.09 GB | ~0.45 GB | says FAIL | **PASS** |

**Fix:** instrument real device memory (`pynvml.nvmlDeviceGetMemoryInfo`, or `cudaq`/`cupy` mempool
peak, or shell out to `nvidia-smi`) and score P3 against that. My commits already score against the
true device figure and note the discrepancy in each JSON, but the script must be fixed before a re-run.

### Bug #2 — the pre-registered command cannot reach the pre-registered P2 band (design bug)
Determinant ceiling = `grow_per_iter × grow_iters`:
- Run 1: 1000 × 60 ≈ **6×10⁴**
- Run 3: 600 × 80 ≈ **4.8×10⁴**

P2's own band is **[3×10⁵, 4×10⁶]**, point estimate **1.13×10⁶**. The command tops out ~5–20×
*below* the determinant count P2 says chemical accuracy needs. That is exactly why P1/P4 plateau
high. P1 and P2 were unreachable *by construction*, independent of the physics.

---

## 4. Root cause of the growth-phase slowdown (code-level)

The QSCI growth phase is **O(N²·n_terms)** because the Hamiltonian is rebuilt from scratch every
iteration. In `src/qsci_lib.py`:

- `qsci()` (line 186) calls `ground(space)` (line 206) each iteration → `build_H(space)` (line 170),
  which loops over **all** determinants in the current space (line 172) and applies `Hon` over
  **all** Pauli terms for each. Per-iteration cost ∝ |space| × n_terms; repeated ~N/grow_per_iter
  times → **O(N²·n_terms)**. (CrO has n_terms = 48 890.)
- **No eigensolver warm-start:** `sla.eigsh(H, k=1, which="SA")` (line 183) runs cold every
  iteration; the previous `cvec` is discarded instead of passed as `v0=`.
- **Python-level CIPSI candidate loop** (lines 195–199) builds a dict with nested `for` loops
  instead of vectorized numpy.
- **100% CPU / numpy / scipy** — the RTX 4090 was idle through every multi-hour growth phase. The
  "GPU day" was CPU-bound.

Observed per-iteration wall-clock (confirms the O(N²) blowup):
- Run 1 growth deltas: 11 → 515 → 760 → 981 → 1329 → 1678 s (at only 1k–6k dets).
- Run 3 growth deltas: 2 → 102 → 181 → 253 → 331 → 398 → 451 → 517 s.

At these rates, reaching iter 60/80 is 30+ hours; the script writes its evidence JSON only at the
end, so neither run produced a machine artifact — all three checkpoints were hand-built from the
live log + `/proc` + `nvidia-smi`.

**Additional waste (Run 1 sampling):** `tensornet-mps` drew 200 000 shots in 9549 s (2.65 h) but
yielded only **108 unique** number-conserving determinants. The seed subspace is tiny and growth
does all the work, so the shot budget is largely wasted.

---

## 5. Prioritized recommendations for a re-run

1. **Incremental `build_H`** — cache the sparse H and compute only the new rows/columns for
   determinants added that iteration. Turns O(N²·n_terms) → ~O(N·n_terms). This is the single change
   that moves the run from "infeasible" to "finishes." *(Prerequisite for everything below.)*
2. **Warm-start `eigsh` with `v0=`** the previous (zero-padded) ground vector — cheap, cuts Lanczos
   iterations materially.
3. **Fix the P3 device-memory metric** (bug #1) so the reported P3 verdict is the pre-registered one.
4. **Reconcile the schedule with P2** — only meaningful after #1: an honest attempt at P1/P2 needs a
   schedule that can actually reach ~10⁶ dets (e.g. `grow_per_iter ≈ 5000` with a scalable build).
5. **Move the diagonalization to GPU** (cupy sparse + GPU Lanczos/LOBPCG) to use the 4090 — highest
   leverage if the goal is to finish inside a GPU day.
6. **Cut Run 1 sampling** to 100k shots or seed directly from MP2 determinants — negligible accuracy
   cost because growth dominates.
7. **Emit intermediate evidence JSON every K iterations** so a killed/checkpointed run still yields a
   machine-generated artifact (and to survive the ephemeral instance).

---

## 6. Honest caveat to carry into the paper

Even with #1–#6 implemented, **P1 passing at 40q is not guaranteed.** It is an open question whether
QSCI/selected-CI reaches DMRG(χ=400) within 1.6 mHa at ~10⁶ determinants. The re-run makes the
attempt *feasible*; it does not promise a pass. Report the current outcome as the honest at-scale
result (validated exact at ≤20q; under-provisioned and CPU-bound at 38–40q), and treat any improved
re-run as a follow-up with its own pre-registered prediction.

---

## 7. Reproducibility pointers

- Branch: `claude/wonderful-bohr-rir81t`; commits `e5799b9` (Run 2), `cfc5179` (Run 1),
  `747f58c` (Run 3).
- Committed references (predate access): `results/mps_bonddim_evidence.json` (DMRG χ=400 for H₂₀),
  `results/cro_cas19_dmrg_reference.json` (DMRG χ=400 same-CAS for CrO), pre-registration in
  `results/preregistration_v1.json`.
- Exact commands executed (verbatim from `src/GPU_RUNLIST.md`):
  - Run 2: `CUDAQ_TARGET=nvidia python src/gpu_run1_h20_mps.py --atoms 10 --shots 100000 --topm 128`
  - Run 1: `CUDAQ_TARGET=tensornet-mps python src/gpu_run1_h20_mps.py --atoms 20 --shots 200000 --topm 256 --grow-iters 60 --grow-per-iter 1000 --kcap 2000000`
  - Run 3: `python src/gpu_run4_cro38q.py --ncas 19 --grow-iters 80 --kcap 500000`
- Engine under discussion: `src/qsci_lib.py` (class methods `build_H`, `ground`, `qsci`, and
  `peak_rss_gb`).
