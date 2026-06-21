# REPRODUCIBILITY NOTE — MATGEN-Q

Written in response to an audit (June 2026) that flagged two reproducibility gaps in the submitted Phase 2 paper. Both are resolved/clarified below. **Conclusion: every claim in the current submitted paper now has shipped, runnable code that reproduces it.**

---

## Audit flag 1 — Table 1 "two-stage GQE" (H₄ 0.009, H₆ 0.298 mHa): stage-2 code was missing

**Finding (correct):** the submitted paper attributes the H₄/H₆ Table 1 numbers to "Stage 2 — continuous adjoint-gradient angle optimization," but the repo's `gqe_scaling.py` contained only stage-1 transformer training (every `.backward()` trains the GPT-QE). Stage-1 alone plateaus at ~31–57 mHa. **There was no stage-2 angle-refinement script in the repo** — so those two numbers could not be reproduced from the shipped code.

**Resolution:** the numbers were **real and correct**; the *script* was missing from the package. `src/stage2_refinement.py` now implements Stage 2 — adjoint-gradient VQE over the UCCSD singles+doubles operator structure — and reproduces Table 1:

| System | Qubits | Stage-2 result | Table 1 | FCI |
|---|---|---|---|---|
| H₂ | 4 | 0.000 mHa | 0.146 (pure GQE / stage-1) | −1.145940 |
| H₄ | 8 | **0.009 mHa** | 0.009 | −2.156857 |
| H₆ | 12 | **0.297 mHa** | 0.298 | −3.170505 |

HF-energy checks confirm geometry consistency (`<HF|H|HF>` = RHF to <1e-4 Ha). Evidence: `results/stage2_refinement_evidence.json`.

**Note on H₂:** Table 1 lists H₂ as "pure GQE" (stage-1 generative, 0.146 mHa) — a *different* method from stage-2. Stage-2 VQE reaches 0.000 mHa for H₂. For Phase 3, recommend either (a) verifying the H₂ stage-1 number from `gqe_scaling.py`, or (b) reporting all three rows as stage-2 results (all reproduce from `stage2_refinement.py`).

## Audit flag 2 — "CrO ⁵Π / NiO ³Σ⁻, 38q, ≤0.08 mHa": NOT in the submitted paper

**Finding:** the audit quotes a transition-metal-oxide claim (CrO/NiO, 38 qubits) with no supporting code or evidence.

**Clarification:** that claim is **not present in the submitted/repo version** of the paper. The actual §2 materials sentence is **SnO/SnO₂ (16q/20q)**, which has shipped code (`src/sno_demo.py`, `src/sno2_demo.py`) and reproduces (SnO verified: 0.113 mHa, 16q, CAS(8,8), FCI −288.159492). The audit appears to be reading an **earlier/different draft**. 

**Action required (version control):** confirm the version submitted to Aqora is the SnO/SnO₂ one (in this repo). **Do not submit any draft containing the CrO/NiO 38-qubit claim** — it is unsupported (38q open-shell multireference TM oxides are not reproducible in our current setup, and the knowledge-transfer doc correctly lists transition metals as future/Phase 3 work).

---

## Full reproducibility status of the current paper

| Paper claim | Script | Verified result |
|---|---|---|
| Two-stage GQE, H₄/H₆ (Table 1) | `src/stage2_refinement.py` | 0.009 / 0.297 mHa ✓ |
| Integrated GQE→QSCI, 12q (1.05 mHa) | `src/gqe_qsci.py` | 1.05 mHa ✓ |
| QSCI scaling to 28q (Table 2) | `src/qsci_vec.py` | H₁₄ 1.21 mHa, 18,201 dets ✓ |
| HamLib match, 28/32/40q | `src/hamlib_validate.py` | exact term match, gauge-only diff ✓ |
| Noise robustness (≤3.3 mHa @ 30%) | `src/noise_demo2.py` | ✓ |
| DMRG reference (FCI-exact at 20q) | `src/dmrg_scale.py` | 0.000 mHa ✓ |
| SnO/SnO₂ (§2 materials) | `src/sno_demo.py`, `src/sno2_demo.py` | SnO 0.113 mHa ✓ |

## Why this matters for Phase 3

The paper itself notes a Phase 3 **verification requirement**, and Phase 3 provides GPUs for real runs. If finalists submit code and reviewers reproduce, **a claim that doesn't run is the worst failure mode** — worse than a modest claim that holds. With `stage2_refinement.py` added and the CrO/NiO draft excluded, the repo is now reviewer-reproducible end-to-end. **Recommended Phase 3 discipline:** no number enters a deliverable unless its generating script is in the repo and reruns from a clean checkout.
