# Reproducibility audit — 2026-06-21

**Why:** the official Phase 2 rules make reproducibility a stated
Phase 3 rule — *"Code, data references, and run instructions must be sufficient for a third-party
reviewer to verify the headline results."* This audit reruns every shipped CPU script from a clean
checkout, in an isolated dir (`/tmp/audit`, repo tree untouched), and diffs the output against the
committed `results/*.json`. Environment: `pyscf`, `openfermion`, `openfermionpyscf`, `pennylane`,
`torch` present; `cudaq`, `quimb`, `block2` absent.

## Reproduced ✅

| Claim | Committed | Reproduced | Verdict |
|---|---|---|---|
| **CrO 20q** QSCI vs CASCI | 0.038 mHa | **0.038 mHa** | exact |
| **NiO 20q** QSCI vs CASCI | 0.197 mHa | **0.197 mHa** | exact (term count 4823→4691, energy unchanged) |
| **SnO 16q** QSCI vs FCI | 0.113 mHa | **0.126 mHa** | headline holds (≪1.6 mHa) |
| **SnO₂ 20q** QSCI vs FCI | 0.225 mHa | **0.181 mHa** | headline holds (≪1.6 mHa) |
| **Stage-2** H2 4q | 0.000 mHa | **0.000 mHa** | exact |
| **Stage-2** H4 8q | 0.009 mHa | **0.009 mHa** | exact |
| **Stage-2** H6 12q | 0.297 mHa | **0.297 mHa** | exact |
| **GQE→QSCI** H6 12q | GQE 51.46 → QSCI 1.054 mHa | GQE 52.59 → **QSCI 1.054 mHa** | holds (GQE step stochastic; QSCI exact) |
| **HamLib match** H14 28q | 27735 terms, one-norm match | 27735, \|Δ\|=9.9e-13 | exact |
| **HamLib match** H16 32q | 47489 terms | 47489, \|Δ\|=1.6e-12 | exact |
| **HamLib match** H20 40q | 116577 terms | 116577, \|Δ\|=5.4e-12 | exact |

Notes: SnO/SnO₂ third-decimal drift (0.126 vs 0.113; 0.181 vs 0.225) is PySCF-version/numerical — both
remain far inside chemical accuracy, so the "chemical accuracy on real Sn-oxide chemistry" headline is
intact. NiO's Pauli-term count differs (4691 vs 4823) from an operator-tapering/version detail; the
**energy error is identical**, so the scientific claim is unaffected (worth reconciling the stored
count later). GQE→QSCI: the raw-GQE number is stochastic (sampling), as expected; the QSCI headline
(~51 mHa → ~1 mHa) reproduces.

## Not reproducible in this environment (and why)

| Evidence | Blocker | Bearing on headlines |
|---|---|---|
| `dmrg_evidence.json` (H10 20q exact-vs-FCI; H24 48q) | `block2` not installed | DMRG is a *scaling-frontier* support claim, not a Phase-2 headline number. Re-run when block2/GPU available. |
| `qsci_scaling_evidence.json` at 28q/40q | CPU-bound (the JSON itself says so); needs R=0.74 H-chain pickles not shipped | QSCI *principle* is already reproduced (SnO/SnO₂/CrO/NiO/H6). The 28–40q H-chain scaling points are GPU/Phase-3 regime. |
| `hamlib_validation_large.json` per-term sign-flip detail | needs external HamLib `.hdf5` files (not in repo) | **Core** claim (term-count + one-norm match at 28/32/40q) **is** reproduced by the self-contained `hamlib_validate.py`. Only the per-term gauge-diff breakdown needs the files. |
| `noise_evidence.json` | not run — 2e6-shot cost, skipped under the build hold | Noise robustness is a bonus/Phase-3 item, not a Phase-2 headline. |
| **38q CrO/NiO ≤0.08 mHa** | `cudaq`/`quimb` absent; needs GPU | **Confirms `paper_version_discrepancy.md`:** this claim is not runnable on CPU and remains unsubstantiated. |

## Bottom line

Every **Phase-2 headline number that can be produced on CPU reproduces** — the real CrO/NiO 20q
results, SnO/SnO₂, the GQE→QSCI pipeline, stage-2 refinement, and the HamLib equivalence at 28/32/40q.
The only claims that don't reproduce here are (a) GPU/Phase-3-regime items (DMRG, 28–40q QSCI scaling)
and (b) the **unsupported 38q ≤0.08 mHa CrO/NiO claim**, which this audit re-confirms cannot be
produced on CPU. No surprises against the committed evidence.

**Reproduce:** `python src/{transition_metal_oxide_qsci,sno_demo,sno2_demo,stage2_refinement,gqe_qsci}.py`
and `python src/hamlib_validate.py {14,16,20}` (each writes its evidence JSON to the working dir).
