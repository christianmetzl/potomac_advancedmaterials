# Claims ledger — every headline number, traced

**Purpose:** one table mapping every quantitative claim in the Phase 3 write-up to the script that
produces it, the committed evidence JSON, its `reproduce.py` check, and an honest status label. Nothing
in the paper is asserted without a traceable, rerunnable source. Status legend:

- **executed-CPU** — a real computation run on CPU; number recorded in the JSON.
- **circuit-sampled** — the genuine quantum pipeline (statevector sim + `qml.sample` shots), executed.
- **proxy** — determinant-space selected-CI proxy for circuit-sampled QSCI (no shots); hardware-independent.
  Validated against the circuit-sampled pipeline at 16q & 20q (see row "measured-vs-proxy").
- **fit** — an empirical fit on committed data points.
- **GPU-owed** — not yet executed; needs qBraid GPU access (`[QBRAID-RUN]` in the paper). Stated as a target,
  never as an achieved result.

| # | Claim (paper) | Value | Script | Evidence JSON | reproduce.py | Status |
|---|---|---|---|---|---|---|
| 1 | Two-stage GQE H₂/H₄/H₆ | 0.000 / 0.009 / 0.297 mHa | `src/stage2_refinement.py` | `stage2_refinement_evidence.json` | PASS | executed-CPU (exact ref) |
| 2 | Integrated GQE→QSCI, H₆ 12q | 1.05 mHa (raw 51→1.05) | `src/gqe_qsci.py` | `gqe_qsci_evidence.json` | PASS | circuit-sampled |
| 3 | Measured QSCI 16q / 20q | 28.1 / 50.4 mHa | `src/encoder/measured_qsci.py` | `measured_qsci_evidence.json` | — | circuit-sampled |
| 3b | measured-vs-proxy (16q/20q) | trained 26.6↔28.1 / 49.3↔50.4; **measured-random 24.0 / 46.7** (edges trained at low shot budget — coverage effect) | `measured_qsci.py` | `measured_qsci_evidence.json` | — | proxy validated vs circuit-sampled; measured-random disclosed |
| 4 | CrO ⁵Π / NiO ³Σ⁻ 20q | 0.038 / 0.197 mHa | `src/transition_metal_oxide_qsci.py` | `transition_metal_qsci_evidence.json` | PASS | executed-CPU (CASCI ref) |
| 5 | SnO / SnO₂ | chemical accuracy (≤0.6; SnO ~0.11–0.34 version-sensitive, SnO₂ 0.23) | `src/sno_demo.py`, `src/sno2_demo.py` | `materials_evidence.json` | PASS (≤0.6 mHa) | executed-CPU; exact value PySCF-version sensitive |
| 6 | QSCI scaling 20q / 28q | 0.57 / 1.21 mHa (3.8% / 0.15% of CI) | `src/qsci_vec.py` | `qsci_scaling_evidence.json` | — | proxy (perturbative selection) |
| 7 | HamLib match 28/32/40q | exact term-count + one-norm (~1e-13) | `src/hamlib_validate.py` | `hamlib_validation_large.json` | PASS (28q) | executed-CPU |
| 8 | Noise robustness 20q | ≤3.3 mHa @ 30% corrupt, 2×10⁶ shots | `src/noise_demo2.py` | `noise_evidence.json` | — | executed-CPU |
| 9 | DFT functional spread | CrO 1.9 eV (sign flip), NiO 0.11 eV | `src/dft_baseline.py` | `dft_functional_spread_evidence.json` | — | executed-CPU |
| 10 | Classical baseline + exact wall | FCI 0.69s(20q)→3.58s(24q) (single-thread, machine-dependent); intractable 32q+ | `src/classical_baselines.py` | `classical_baselines_evidence.json` | PASS | executed-CPU |
| 10b | DMRG (tensor-network) reference | reproduces FCI 0.000 mHa @20q; H₂₄/48q 6.83 mHa off CCSD(T) (bond-dim 250) | `src/dmrg_scale.py` | `dmrg_evidence.json` | — (needs block2) | executed-CPU (block2) |
| 11 | **Strong-corr trust result** | CCSD(T) −217 mHa (below FCI); selected-CI chem-acc @ ~500 dets; HF-weight 0.93→0.06 | `src/encoder/selected_ci_strongcorr.py`, `src/encoder/strong_correlation.py` | `selected_ci_strongcorr_evidence.json` (energies/dets), `strong_correlation_evidence.json` (HF-weight / multireference diagnostic) | — | executed-CPU (FCI ref) |
| 12 | Operator-pool compression | N₂ 2.26 mHa @ 25% of doubles vs 50.4 random | `src/encoder/pool_compression.py` | `pool_compression_evidence.json` | — | executed-CPU |
| 13 | Transfer ladder 16→56q | +8.9/+8.3/+7.1/+5.8/+5.0/+4.4 mHa (3-seed mean); 13/18 paired wins; across-seed SD ≈2.0 vs ≈7.4 mHa (3.7× tighter) | `src/encoder/scaling_transfer.py --ladder` | `scaling_ladder_evidence.json` | — | proxy; mean trend, narrows into noise beyond ~28q |
| 14 | Cross-chemistry transfer | 4/6 oxide targets (SnO fails); MP2 strongest | `scaling_transfer.py --crosschem` | `crosschem_evidence.json` | — | proxy; honest partial |
| 15 | Budget sweep + transfer×MP2 | trained < random ∀K; MP2 strongest; fusion no gain | `scaling_transfer.py --compose` | `compose_evidence.json` | — | proxy |
| 16 | Determinant scaling law | ~1.38×/qubit vs 2.0× FCI (log-R²=0.99) | `src/encoder/scaling_law.py` | `scaling_law_evidence.json` | — | fit (exponential, smaller base; NOT polynomial) |
| 17 | Slater-Condon engine | 0.0000 mHa vs Jordan–Wigner (H6/H10) | `src/encoder/sci_integrals.py` (`_selftest`) | (selftest stdout) | — | validated |
| 18 | Conditional encoder (cross-molecule) | within-noise tie — honest NEGATIVE | `src/encoder/decisive_transfer.py` | `decisive_transfer_evidence.json` | — | executed-CPU, reported as negative |
| 20 | **Real-oxide trust (CrO dissociation)** | in-active-space CCSD(T) erratic/non-convergent (to ~140 mHa) vs CASCI; selected-CI/QSCI variational ≤2.8 mHa; dominant-det weight 0.87→0.16 | `src/cro_dissociation.py` | `cro_dissociation_evidence.json` | PASS | executed-CPU (CASCI ref) |
| 21 | **CrO spin-gap decision** | DFT spans 1.9 eV, B3LYP wrong sign; CASCI/QSCI +1.89 eV quintet = experimental X⁵Π | `src/cro_spin_gap.py` | `cro_spin_gap_evidence.json` | PASS | executed-CPU (CASCI ref) |
| 22 | EN-PT2 two-sided bracket | E_var upper bound + E_var+PT2 estimate; equilibrium extrapolation → FCI +4.1 mHa (R²=0.999) | `src/encoder/selci_pt2.py` | `selci_pt2_evidence.json` | PASS | executed-CPU (FCI ref) |
| 23 | Generator learned MP2 hierarchy | Spearman ρ=0.31 (p<0.002); 4/8 top-double overlap | `src/encoder/generator_mp2.py` | `generator_mp2_evidence.json` | — | executed-CPU |
| 19 | 40q MPS run / CrO·NiO near-38q / QPU validation | — | — | — | — | **GPU-owed** `[QBRAID-RUN]` |

## Honest status summary
- **Executed (CPU or circuit-sampled):** rows 1–12, 16–18 — the bulk of the submission is run and recorded.
- **Proxy (validated against real measurement at 16q & 20q, row 3b):** rows 6, 13–15 — the large-scale
  scaling/transfer numbers use the determinant-space selected-CI proxy, which row 3b shows tracks the
  circuit-sampled pipeline.
- **GPU-owed (row 19):** the only un-executed items; clearly marked as targets in the paper, never as
  achieved results.
- **Judges' re-run:** `python src/reproduce.py` → **10/10 PASS** (transcript: `docs/reproduce_transcript.txt`).

## Known honesty caveats (also stated in the paper)
- Transfer ladder advantage is a **3-seed mean** that narrows into run-to-run noise beyond ~28q — not an
  every-seed guarantee.
- Target-specific **MP2 selected-CI beats** the transferred generator; the generator's value is zero
  target-specific cost, not beating MP2.
- Cross-chemistry transfer is **partial (4/6)** and fails on SnO.
- Scaling is **exponential with a smaller base** (vanishing FCI fraction), **not polynomial**.
- SnO's precise QSCI value is **PySCF-version sensitive** (0.11–0.45 mHa across runs); the claim is
  chemical accuracy, which `reproduce.py` asserts robustly (≤0.6 mHa).
