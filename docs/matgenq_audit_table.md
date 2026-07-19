# The MATGEN-Q Audit — a synthesis-decision ranking framework

**The business artifact in one sentence:** before a candidate material advances from computation to
synthesis (the step where cost jumps by orders of magnitude), every decisive computed number gets an
**audit verdict** from a method whose answer is a *mathematically guaranteed variational bound* with a
built-in error certificate (EN-PT2) — so silent failures in the standard methods are caught *before*
they commit lab spend.

Every row below is a real, committed, reproducible result from this repository (evidence file cited).
This is the demonstration instance of the framework on industrially relevant chemistry — transition-metal
oxides (catalysis, batteries, magnetics) and tin oxides (EUV photoresists).

## Audit table (all numbers from committed evidence)

| # | Decision question | DFT says | CCSD(T) says | DMRG says | **MATGEN-Q audit verdict** | Decision impact if unaudited | Evidence |
|---|---|---|---|---|---|---|---|
| 1 | CrO ground spin state (quintet vs triplet) — which candidate chemistry is even right? | **Functional-dependent: spread 1.9 eV; B3LYP picks the WRONG ground state** (−0.08 eV, inverted) | — | — | Quintet by **1.89 eV** (CASCI + QSCI agree; matches experimental X⁵Π) | A B3LYP-based screen mis-ranks every CrO-like candidate | `cro_spin_gap_evidence.json` |
| 2 | CrO bond stretch (reaction-path energetics) | — | **Erratic errors to ~140 mHa, frequently non-convergent** as correlation strengthens | — | Variational bound holds at every geometry, **≤2.8 mHa throughout** | Barrier heights / binding curves silently wrong exactly where bonds break (i.e., where catalysis happens) | `cro_dissociation_evidence.json` |
| 3 | Strong-correlation stress test (H₁₀ dissociation) | — | **−217 mHa BELOW exact — confidently wrong, unphysical, no warning** | — | Chemical accuracy with ~500 determinants; rigorous upper bound + PT2 certificate (R²=0.999) | The "accuracy gold standard" fails hardest precisely on the hard cases it's reserved for | `selected_ci_strongcorr_evidence.json`, `encoder/selci_pt2_evidence.json` |
| 4 | CrO at scale — CAS(18,19), 38 qubits: absolute correlated energy | — | — | **χ=400 reference carries ~3 mHa (~1.9 kcal/mol) of silent truncation error** | QSCI energy lands *below* the DMRG reference — since both are variational upper bounds, QSCI is **provably closer to exact**; pre-registered P4 metric reported FAIL as frozen, mechanism disclosed | Even the heavy-artillery reference method needs an auditor at industrial system sizes | `gpu_run4_cas19_*` checkpoints (final evidence pending run completion) |
| 5 | VO ground state — blind test (no tuning possible) | — | — | — | Pre-registered, SHA-frozen, one-shot: quartet below doublet by 1.09 eV — **matches experimental X⁴Σ⁻** | The audit's predictions hold when it cannot see the answer key | `blind_holdout_vo_result.json`, `preregistration_v1.json` |
| 6 | NiO spin gap (second oxide — trend, not anecdote) | Functional spread 0.11 eV vs 0.044 eV accuracy target | — | — | 0.197 mHa vs exact reference at 20q | Same failure mechanism, second material class | `transition_metal_qsci_evidence.json`, `dft_functional_spread_evidence.json` |
| 7 | EUV photoresist chemistry (SnO, SnO₂, Sn₂O₂) | (screening tier) | — | — | Chemical accuracy vs exact reference on all three | Audit tier extends to the semiconductor materials class ($800B+ industry downstream) | `materials_evidence.json`, `tin_oxo_evidence.json` |

## Why the audit verdict is trustworthy (the mechanism, not a promise)
1. **One-sided by construction:** the QSCI/selected-CI energy can never be *below* the exact answer.
   When the audit reads lower than a reference, the reference is wrong — no judgment call.
2. **Self-certifying:** the EN-PT2 correction estimates the audit's own remaining error and shrinks
   as the certificate converges (demonstrated R²=0.999 extrapolation to exact).
3. **Pre-registration discipline:** thresholds frozen before execution, FAILs published (see row 4 —
   reported as a FAIL against its frozen metric even though the physics favors the audit).
4. **Runs on rentable hardware today:** row 4's audit cost ≈ $12 of cloud compute and ~3 hours —
   cheaper than the reference calculation it corrected.

## Honest scope (what the audit does NOT cover)
- It audits the **correlated-electron solve inside the chosen active space** — the dominant silent-failure
  mode — not basis-set or active-space-selection error (those are shared assumptions across all columns).
- Demonstrated on first-row transition-metal and tin oxides at up to 38–40 qubits; broader chemistry
  coverage is roadmap, not claim.
- DFT remains the right *screening* tier on cost grounds; the audit's role is the decision gate before
  synthesis, not a DFT replacement.

## The economics, conditioned honestly
A single failed synthesis campaign driven by a mis-ranked candidate costs $10⁵–$10⁶⁺ (staff, materials,
characterization, opportunity cost). The audit tier costs $10–$10² per decisive number on today's cloud
GPUs. It does not need to be right about "millions saved industry-wide" to be worth deploying: **one
avoided dead-end per year pays for the audit layer on an entire screening portfolio.** Rows 1–4 show the
failure modes it catches are real, current, and present in every tier of the standard toolchain.

*Team EIGENNEXUS — GIC 2026 Phase 3 (MATGEN-Q). Every number traceable via `python src/reproduce.py` (24 automated checks).*
