# Transition-Metal Oxide QSCI — CrO & NiO (REAL, 20 qubits)

## What these are
Real, reproducible QSCI results for two open-shell transition-metal oxides, run on CPU:

| System | Term | Active space | Qubits | Pauli terms | CASCI (Ha) | QSCI error |
|---|---|---|---|---|---|---|
| CrO | ⁵Π (quintet)   | CAS(10,10) | 20 | 3727 | −1117.891641 | **0.038 mHa** (801 dets) |
| NiO | ³Σ⁻ (triplet)  | CAS(10,10) | 20 | 5915 | −1581.354255 | **0.197 mHa** (1201 dets) |

Both reach chemical accuracy vs the CASCI reference. Reproduce with: `python transition_metal_oxide_qsci.py`
(PySCF ROHF + CASCI, all-electron def2-SVP; open-shell reference built explicitly; QSCI selected-CI).

## What these are NOT — read this
**These are NOT the "CrO ⁵Π / NiO ³Σ⁻, 38 qubits, ≤0.08 mHa" claim from the earlier draft.**
- They are **20 qubits** (CAS(10,10) = 10 active spatial orbitals), **not 38 qubits** (~19 active orbitals).
- **No 38-qubit open-shell multireference TM-oxide result exists in this project.** It was not produced in any session I can verify, is not in the repo, and **cannot be produced on CPU** (`get_sparse_operator` OOMs at 16q; QSCI tops out ~28q on hydrogen). That scale needs the **Phase 3 GPUs** (CUDA-Q + MPS).
- Note the ≤0.08 mHa *accuracy* IS reachable at this tractable 20q scale (CrO hit 0.038 mHa) because the CI space is small. At 38q the space is exponentially larger and far harder. **The accuracy and the qubit count are not the same claim — do not conflate them.**

## Recommendation
- Do **not** put a 38q CrO/NiO claim in any Phase 3 deliverable unless it is produced on the GPUs with shipped code that reruns clean.
- If you want transition-metal evidence now, **these honest 20q results are real and reproducible** and can be added to the repo as such.
- ~~The submitted paper's §2 already uses SnO/SnO₂ (16q/20q)… so the paper does not depend on CrO/NiO at all.~~
  **CORRECTION (2026-06-21):** Christian confirmed the *AdvancedMaterials* version was submitted to Aqora —
  it **does** assert "CrO ⁵Π / NiO ³Σ⁻, 38q, ≤0.08 mHa" in §2. So the finalist paper **does** depend on a
  CrO/NiO claim that is not reproducible (38q does not exist; NiO is 0.197 mHa at 20q). See
  `docs/paper_version_discrepancy.md` for the resolution and Phase 3 options.
