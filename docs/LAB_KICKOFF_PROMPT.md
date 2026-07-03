# Kickoff prompt for the Claude Code session on the qBraid GPU Lab instance

Copy everything between the lines into the Claude Code session running in the qBraid Lab terminal.

---

You are running inside a qBraid GPU Lab instance (billed per minute — treat idle time as money).
Repo: this directory (potomac_advancedmaterials, branch claude/wonderful-bohr-rir81t). You are
executing the pre-registered GPU runs for Team EIGENNEXUS's GIC 2026 Phase 3 submission (Mitsubishi/
AIST "Scaling GQE with NVIDIA CUDA-Q"). Honesty is absolute: results are reported AS-IS, pass or
fail, per results/preregistration_v1.json. Never move a threshold; never tune after seeing a result.

CONTEXT
- src/GPU_RUNLIST.md is the plan; results/preregistration_v1.json holds the pass/fail predictions
  (P1: 40q MPS <=1.6 mHa vs the committed DMRG chi=400 reference; P2: determinant budget in
  [3e5,4e6]; P3: peak memory < 8 GB).
- All scripts are smoke-tested green on CPU; your job is GPU execution + honest reporting.
- The 40q DMRG reference energy is already committed (results/mps_bonddim_evidence.json, H20 chi=400);
  gpu_run1_h20_mps.py reads it automatically.

DO THIS, IN ORDER
1. Sanity (~10 min): `pip install -r requirements.txt` (the default qBraid env has cudaq/pennylane;
   this fills gaps), then `python src/run_gpu_phase3.py --dry-run`. All runs must be green before
   any paid step. If pip conflicts arise in the managed env, prefer `pip install --user` or a venv.
2. Run 2 first (quick win): `CUDAQ_TARGET=nvidia python src/gpu_run1_h20_mps.py --atoms 10
   --shots 100000 --topm 128` — cuStateVec exact-validation point. Commit the evidence JSON.
3. The headline, Run 1: `CUDAQ_TARGET=tensornet-mps python src/gpu_run1_h20_mps.py --atoms 20
   --shots 200000 --topm 256 --grow-iters 60 --grow-per-iter 1000 --kcap 2000000`
   - Log wall-clock per stage (the script does) and watch GPU memory (nvidia-smi).
   - If sampling is unexpectedly slow, you may reduce --shots to 100000 or --topm to 128 — document
     any change and its reason in the commit message; thresholds NEVER change.
   - The QSCI growth phase is CPU-bound; that is expected — do not kill it prematurely, but if
     total instance time approaches 6 hours, checkpoint: commit whatever evidence exists, note the
     state honestly, and stop.
4. Optional if budget remains (>3000 credits): Run 3 QSCI at 38q:
   `python src/gpu_run4_cro38q.py --ncas 19 --grow-iters 80 --kcap 500000` (reference already
   committed as results/cro_cas19_dmrg_reference.json).
5. After each run: `git add results/ && git commit` with a message stating the printed PASS/FAIL
   verbatim, and `git push origin claude/wonderful-bohr-rir81t`. Push after EVERY run, not just at
   the end — the instance is ephemeral.
6. When done (or at the time/credit limit): print a final summary table (run, result, prereg
   verdict, wall-clock, credits estimate), push everything, and tell the user to STOP THE INSTANCE.

RULES
- Zero-defect honesty: numbers in commit messages must match the evidence JSONs exactly.
- Spend discipline: no idle waiting; batch work; if something blocks >15 min, commit state and say so.
- Do not touch the paper (a separate session integrates results); do not modify pre-registration.
- If a run FAILS its prereg threshold, that is a reportable result — commit it with the same care.

---
