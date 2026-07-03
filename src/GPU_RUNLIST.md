# qBraid GPU/QPU run-list (Phase 3, owed runs) — launch-ready, pre-registered

Every run below is **pre-registered** in `results/preregistration_v1.json` (quantitative pass/fail
thresholds committed *before* access; outcomes will be reported as-is). The CUDA-Q scripts are
backend-parameterized — the same code that passes `reproduce.py` on CPU dispatches to GPU via an
environment variable. Estimated total: ~2 weeks single H100/A100 (80 GB) wall-clock; degrades
gracefully to a smaller allocation.

| # | Run (prereg ID) | Command on qBraid GPU | Reference | Pass threshold |
|---|---|---|---|---|
| 1 | 40q MPS GQE/QSCI on H₂₀ (P1) | `CUDAQ_TARGET=tensornet-mps python src/cudaq_qsci.py` (extend `run()` to H₂₀; χ=400 per measured target) | block2 DMRG(χ=400), same basis/geometry | ≤1.6 mHa |
| 2 | 40q determinant budget (P2) | GPU-sampled QSCI at 40q (`src/qsci_vec.py` path, device-sampled selection) | scaling-law band | 3×10⁵–4×10⁶ dets |
| 3 | Memory footprint check (P3) | log peak device memory during run 1 | crossover model (195 MB + margin) | <8 GB |
| 4 | CrO/NiO near-38q (P4) | `transition_metal_oxide_qsci.py` lifted to CAS(19,19) with GPU-MPS evaluation | block2 DMRG in same CAS | ≤1.6 mHa (extrapolated prediction — lowest confidence, labeled) |
| 5 | cuStateVec exact validation ≤32q | `CUDAQ_TARGET=nvidia python src/cudaq_qsci.py` | FCI/DMRG | exact-method agreement |
| 6 | Real QPU 12q H₆ QSCI (P5) | IonQ/IBM via qBraid, ≥10⁴ shots; determinants → classical diagonalization | FCI | ≤5 mHa; raw counts committed regardless |
| 7 | Quantum-vs-classical wall-clock | runs 1+5 timed vs `classical_baselines.py` / DMRG on same instances | — | reported as measured |

Notes:
- `CUDAQ_TARGET` / `CUDAQ_TARGET_SV` / `CUDAQ_TARGET_DM` env vars switch backends without code edits
  (`qpp-cpu` and `density-matrix-cpu` defaults are what `reproduce.py` verifies on CPU today).
- Failures are reported with the same prominence as passes — see `results/preregistration_v1.json`.
