# qBraid GPU/QPU run-list — CODE COMPLETE, smoke-tested, pre-registered

Every run below is a **real, committed script**, smoke-tested end-to-end on CPU (transcripts in the
evidence JSONs); on qBraid the only change is a target flag / env var. Every run is **pre-registered**
in `results/preregistration_v1.json` — quantitative pass/fail thresholds committed before access;
outcomes reported as-is. One driver executes the whole list in priority order:

```bash
python src/run_gpu_phase3.py --dry-run    # CPU smoke of every run (works today; all green)
python src/run_gpu_phase3.py              # PRODUCTION, priority order (GPU day)
```

| Pri | Run (prereg) | Production command | Reference | Pass | Smoke status (CPU, today) |
|---|---|---|---|---|---|
| 1 | 40q H₂₀ MPS QSCI (P1+P2+P3) | `CUDAQ_TARGET=tensornet-mps python src/gpu_run1_h20_mps.py --atoms 20 --shots 200000 --topm 256 --grow-iters 60 --grow-per-iter 1000 --kcap 2000000` | block2 DMRG(χ=400), committed | ≤1.6 mHa; dets ∈ [3e5,4e6]; <8 GB | ✅ H₄/H₆: +0.000 mHa, P1/P3 PASS |
| 2 | cuStateVec validation ≤32q | `CUDAQ_TARGET=nvidia python src/gpu_run1_h20_mps.py --atoms 10 --shots 100000 --topm 128` | FCI (exact) | exact agreement | ✅ same script, FCI recovered |
| 3 | CrO CAS(18,19)=38q (P4) | `python src/gpu_run4_cro38q.py --ncas 19 --grow-iters 80 --kcap 500000` (optional GPU sampling once credits exist) | block2 DMRG **in the identical CAS** — `results/cro_cas19_dmrg_reference.json`, computed on CPU *before* access | ≤1.6 mHa | ✅ CAS(10,10) smoke: −0.000 mHa vs exact CASCI; DMRG ref-maker cross-validated (CAS10 DMRG ≡ CASCI) |
| 4 | Real QPU 12q H₆ QSCI (P5) | `python src/qpu_run_h6.py --target ionq --machine <per qBraid catalogue> --shots 10000` | FCI (exact) | ≤5 mHa; raw counts committed regardless | ✅ flight protocol (3 pooled jobs: MP2 + 2 seeded-random) passes pre-flight at **+1.05 mHa noiseless**; single-job design measured at ~16 mHa and **rejected before hardware** |
| 5 | Quantum-vs-classical wall-clock | timings logged automatically by runs 1–2; compare `classical_baselines.py` / DMRG walls | — | reported as measured |  ✅ per-stage wall-clock in every evidence JSON |

## What is already DONE before access (no GPU needed)
- All five scripts written, argument-complete, and smoke-tested green (`--dry-run` driver).
- The **38q DMRG reference** (P4's judge) is computed on CPU and committed — the GPU run will be scored
  against a reference that provably predates it.
- The **QPU flight protocol** was tuned and frozen on simulators (incl. a density-matrix noisy
  rehearsal); the P5 threshold was never moved (see `protocol_amendments` in the pre-registration).
- Shared engine (`src/qsci_lib.py`): compressed MP2 circuit via CUDA-Q's own excitation sub-kernels
  (interleaved convention validated against exact FCI), sampling → number-conserving post-selection,
  vectorized bitmask QSCI with device-seeded CIPSI growth, peak-memory logging for P3.

## GPU-day sequence (score-per-hour ordered)
1. `--dry-run` once on the GPU box (sanity, ~1 min).
2. Run 1 (the headline). 3. Run 2 (exact validation). 4. Run 3 QSCI at 38q. 5. Run 4 QPU submission.
6. Paste each printed PASS/FAIL + evidence JSON into the paper's `[QBRAID-RUN]` slots; every number
   already has a pre-registered prediction to be judged against.
