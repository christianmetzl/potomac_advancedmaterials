# Corrected GPU-day kickoff (attempt 2) — Claude Code on the qBraid GPU Lab instance

Copy everything between the lines into the Claude Code session in the qBraid Lab terminal.
This supersedes `LAB_KICKOFF_PROMPT.md`. It exists because attempt 1's 40q run was **compute-limited,
not method-limited**: the growth schedule was provisioned for ~60k determinants but P2 predicts ~1.1M
are needed for chemical accuracy, and the old engine rebuilt the whole Hamiltonian every iteration
(cost exploded 11s→1678s). Both are now fixed — `qsci_fast` builds the Hamiltonian incrementally and
the growth batches are sized to the P2 budget. Honesty discipline is unchanged: results reported
as-is, no threshold moved.

---

You are running inside a qBraid GPU Lab instance (billed per minute — treat idle time as money).
Repo: this directory (potomac_advancedmaterials, branch claude/wonderful-bohr-rir81t). You are
executing the CORRECTED pre-registered runs for Team EIGENNEXUS's GIC 2026 Phase 3 submission
(Mitsubishi/AIST "Scaling GQE with NVIDIA CUDA-Q"). This is attempt 2 after attempt 1 was
compute-limited; disclose it exactly that way. Never move a threshold; never tune after seeing a result.

CONTEXT (what changed since attempt 1)
- Engine: the run scripts now call `PauliEngine.qsci_fast` (incremental Hamiltonian caching + vectorized
  CIPSI selection + warm-started eigensolver). Validated bit-for-bit vs the original engine and exact
  FCI on CPU (max deviation 1.6e-11 mHa). It reaches FCI at 20q in ~60s (was ~850s) and makes 28q/40q
  determinant budgets tractable.
- Memory: P3 is now judged on real GPU DEVICE memory (nvidia-smi peak via DeviceMemMonitor), not host
  RSS. Both are recorded in the evidence JSON.
- References: `mps_bonddim_evidence.json` holds committed DMRG(chi=400) energies at 20/28/40q, all
  predating access. gpu_run1 auto-selects the right one by qubit count.

DO THIS, IN ORDER (driver runs them in priority order 5 -> 3 -> 1 -> 4)
1. Sanity (~10 min): `pip install -r requirements.txt`, then `python src/run_gpu_phase3.py --dry-run`.
   All runs must print green before any paid step.
2. Run 5 — exact anchor (quick): `CUDAQ_TARGET=nvidia python src/gpu_run1_h20_mps.py --atoms 10
   --shots 100000 --topm 128 --grow-iters 12 --grow-per-iter 4000 --kcap 60000`. Expect ~0.000 mHa
   vs FCI (this reproduces attempt-1 Run 2, the exactness proof). Commit the evidence JSON, push.
3. Run 3 — the new headline: converged 28q vs committed DMRG(chi=400). Use cuStateVec (nvidia):
   at 28q the statevector is 4 GB and fits the 24 GB card, so sampling is EXACT and fast (tensornet-mps
   is reserved for 40q where the statevector is intractable):
   `CUDAQ_TARGET=nvidia python src/gpu_run1_h20_mps.py --atoms 14 --shots 150000 --topm 256
   --grow-iters 8 --grow-per-iter 8000 --kcap 400000`
   - This is the genuine chemical-accuracy PASS ABOVE 20q. CPU pre-validation reached chemical
     accuracy by ~iter 3; the GPU run confirms it with a device-sampled seed. Watch nvidia-smi for P3.
   - Commit + push immediately. STOP here and report before the 40q run (which is ~hours).
4. Run 1 — 40q honest at-scale attempt with the fast engine:
   `CUDAQ_TARGET=tensornet-mps python src/gpu_run1_h20_mps.py --atoms 20 --shots 200000 --topm 256
   --grow-iters 40 --grow-per-iter 50000 --kcap 1500000`
   - This now targets the P2 determinant band ([3e5,4e6]). Report the result AS-IS: if it reaches
     <=1.6 mHa, P1 PASS; if it plateaus above, report the value and determinant count honestly.
     Either way it should be far better than attempt 1's +14.8 mHa (which stopped at 6k dets).
   - P3 note: attempt 1 measured 12 GB device (tensornet-mps sampling workspace) > the 8 GB
     prediction -> P3 FAIL. That is expected to recur; report device memory as measured. It fits the
     24 GB card comfortably; the 8 GB prediction simply omitted sampling workspace. Do NOT move P3.
   - If total instance time approaches ~6 h, checkpoint: commit whatever evidence exists with an
     honest "non-converged at iter N" status, push, and stop.
5. Optional if budget remains (>3000 credits): Run 4 — 38q CrO:
   `python src/gpu_run4_cro38q.py --ncas 19 --grow-iters 40 --grow-per-iter 40000 --kcap 800000`
   (reference already committed as results/cro_cas19_dmrg_reference.json).
6. After EACH run: `git add results/ && git commit` with the printed PASS/FAIL verbatim, then
   `git push origin claude/wonderful-bohr-rir81t`. The instance is ephemeral — push after every run.
7. When done (or at the time/credit limit): print a final summary table (run, result, prereg verdict,
   dets, device-mem, wall-clock, credits), push everything, and tell the user to STOP THE INSTANCE.

RULES
- Zero-defect honesty: numbers in commit messages must match the evidence JSONs exactly.
- Attempt-2 framing is mandatory in commit messages for Run 1 (e.g. "40q attempt 2, fast engine").
- Do not touch the paper (a separate session integrates results); do not modify the pre-registration.
- A run that FAILS its threshold is a reportable result — commit it with the same care as a pass.

---
