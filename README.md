# MATGEN-Q

**Scaling a conditional Generative Quantum Eigensolver (GQE) for EUV photoresist discovery with NVIDIA CUDA-Q.**

Team **EIGENNEXUS** — Global Industry Challenge (GIC) 2026, *Advanced Materials* track (Mitsubishi Chemical Group & AIST).
**Phase 1 winner · Phase 3 finalist.**

[![Launch on qBraid](https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png)](https://account.qbraid.com/?gitHubUrl=https://github.com/christianmetzl/potomac_advancedmaterials.git)

> **Phase 3 reviewers:** click **Launch on qBraid**, then follow [Running on qBraid](#running-on-qbraid-phase-3) to reproduce every headline result without modification.

---

## Overview

MATGEN-Q is a generative quantum-chemistry pipeline aimed at the strongly-correlated metal-oxide chemistry of EUV photoresists (Sn/Hf/Zr oxides):

1. A **two-stage GQE** — a GPT-style transformer (GPT-QE) discovers circuit structure, then adjoint-gradient refinement tunes the angles — sidestepping the barren-plateau problem of variational methods.
2. **QSCI** (Quantum-Selected Configuration Interaction) evaluates energies by diagonalizing the Hamiltonian in a compact, measurement-selected determinant subspace, avoiding the expensive full-operator expectation.
3. **Matrix-product-state (MPS) tensor-network simulation** carries the scaling toward the ~40-qubit target on a single high-memory GPU (memory scales with entanglement, not 2ⁿ).
4. **Operator-pool compression** (MP2-amplitude + point-group/spin-symmetry pruning of the O(N⁴) excitation pool) shrinks the transformer vocabulary and circuit depth at scale. *(A chemistry-conditioned encoder for cross-family transfer was also tested; see [Honest scope](#honest-scope) — it proved unnecessary and is not a headline.)*

## Demonstrated results

All numbers are reproducible from the scripts in `src/` and recorded in `results/`.

| Result | Value | Notes |
|---|---|---|
| Two-stage GQE (UCCSD), H₂/H₄/H₆ | 0.000 / 0.009 / 0.297 mHa | chemical accuracy, 4–12 qubits (`stage2_refinement.py`) |
| **Integrated GQE→QSCI, H₆ (12q)** | **1.05 mHa** | GPT-QE generates circuits → QSCI samples determinants *from the generated states* → diagonalizes; refines the raw 51 mHa generative state ~50× |
| QSCI scaling, H₁₄ (28q) | 1.21 mHa | 18,201 determinants = 0.15% of the FCI space |
| QSCI, H₂₀ (40q) | 39 mHa | operational; converging (not yet chemical accuracy — CPU-bound) |
| HamLib validation, 28/32/40q | exact | term counts match (27,735 / 47,489 / 116,577); coefficients agree to ~15 sig figs, differing only by a spectrum-invariant orbital-phase gauge |
| Noise robustness, 20q | ≤3.3 mHa at 30% corrupted measurements | graceful degradation |
| Sn-oxides (EUV target) | SnO chemical accuracy (≤0.5 mHa, 16q; value PySCF-version sensitive), SnO₂ 0.23 mHa (20q) | Sn effective-core-potential CASCI active spaces; construction validated on H₄ to 0.0000 mHa |
| **CrO ⁵Π / NiO ³Σ⁻ (20q)** | **0.038 / 0.197 mHa** | open-shell multireference oxides vs CASCI (`transition_metal_oxide_qsci.py`) |
| **CrO spin-state decision** | DFT spans 1.9 eV, B3LYP flips the sign; CASCI/QSCI **+1.89 eV quintet = experimental X⁵Π** | turns "DFT mis-ranks the candidate" into a worked decision (`cro_spin_gap.py`) |
| **CrO dissociation trust (real oxide)** | in-active-space CCSD(T) erratic / non-convergent (to ~140 mHa vs CASCI); QSCI variational ≤2.8 mHa | the strong-correlation trust story on a real Cr–O bond, not toy H₁₀ (`cro_dissociation.py`) |
| EN-PT2 two-sided bracket | E_var (upper bound) + E_var+PT2 (estimate); equilibrium extrapolation → FCI +4.1 mHa (R²=0.999) | certifies the gap, CIPSI standard (`encoder/selci_pt2.py`) |
| Generator learned MP2 hierarchy | Spearman ρ=0.31 (p<0.002), 4/8 top-double overlap | energy-trained generator (blind to MP2) recovers the MP2 amplitude ordering (`encoder/generator_mp2.py`) |
| **CUDA-Q execution (qpp-cpu)** | H₄ VQE **+0.012 mHa**, QSCI **+0.022 mHa** vs FCI | GQE/QSCI pipeline runs through the CUDA-Q SDK on CPU (`cudaq.observe`/`cudaq.sample`); `src/cudaq_qsci.py` |
| **MPS bond-dim / entanglement (pillar 1)** | χ for chem-acc ≈50/100/400 @20/28/40q; Sₘₐₓ 0.39→4.43 | bond dimension grows slowly with size; area-law near equilibrium → strong correlation; `src/mps_bonddim_study.py` (block2 DMRG) |

## Honest scope

- The **integrated GQE→QSCI loop is demonstrated at 12 qubits**; the larger-scale QSCI results (20–28q) use **perturbative determinant selection as a hardware-independent proxy** for the measurement step, *validated against* the 12q measured pipeline.
- The 40q result is **operational but not yet at chemical accuracy** — the at-scale GPU runs are the Phase 3 deliverable. We *have* executed the supporting evidence on CPU: the GQE/QSCI circuits run through **CUDA-Q's qpp-cpu backend** (H₄ to exact FCI), and a **block2 MPS bond-dimension study** quantifies the χ the 40q GPU run needs (≈400) and the entanglement growth that justifies the tensor-network tier. The owed piece is the GPU `tensornet-mps`/`cuStateVec` run at 40q, not the platform's viability.
- **Train-small, deploy-large (transfer result).** One generator trained only on 8q+12q systems, deployed zero-shot across **16→56 qubits**, proposes lower-energy determinant subspaces than random selection (`src/encoder/scaling_transfer.py --ladder`). The robust signals are statistical: **~3.7× tighter across-seed selection spread** (≈2.0 vs ≈7.4 mHa) and **13/18 size×seed paired wins** (binomial p≈0.05); the per-size mean advantage is all-seeds-positive at 16q and positive in the mean through 28q (+8.9/+8.3/+7.1 mHa), then narrows into noise at 40–56q. That the policy captures real chemistry is corroborated by interpretability (the learned token distribution recovers the MP2 amplitude hierarchy, ρ=0.31, p<0.002). A canonical frontier-relative tokenization makes the small vocabulary a subset of the large one; a determinant-space **selected-CI proxy** (Slater-Condon, validated to 0.0000 mHa vs Jordan–Wigner; no 2ⁿ statevector) makes 56q reachable on CPU. *Honest scope:* a mean trend that narrows into run-to-run noise beyond ~28q (not an every-seed guarantee), a relative advantage at a fixed small budget (not chemical accuracy), and a selected-CI proxy (not circuit-sampled QSCI). Cross-*chemistry* transfer works on 4/6 oxide targets but fails on SnO; target-specific MP2 beats the prior; cross-*molecule* conditioning was a within-noise tie. All reported as negatives where they are negatives.
- Sn-oxide Hamiltonians are **our own ECP-CASCI construction** (not from the HamLib library, which contains no tin oxides).

## Repository structure

```
paper/      Phase 2 submission (PDF + DOCX), the docx-js build script, and the architecture figure
src/        analysis code — GQE, QSCI, integrated GQE→QSCI, noise, DMRG, Sn-oxides, transition-metal
            oxides, HamLib validation, classical baselines, and src/encoder/ (conditional-encoder test)
results/    computational-result JSONs (every headline number traces to one of these)
docs/       project context + Phase 3 strategy: plan_to_win, spec_intake, classical_baselines,
            writeup_draft, reproducibility_audit, novelty_assessment, version-discrepancy resolution
```

## Reproduce (CPU — verified)

Setup (Python 3.11):
```bash
pip install pyscf openfermion openfermionpyscf h5py pennylane pennylane-lightning \
            torch scipy numpy matplotlib
```

**One command** runs the verified CPU suite and checks each headline number against the committed
`results/*.json`, printing a PASS/FAIL table (`--quick` skips the slower scripts):
```bash
python src/reproduce.py     # -> 10/10 PASS (captured transcript: docs/reproduce_transcript.txt)
```
Every quantitative claim is traced to its script + evidence JSON + status (executed / circuit-sampled /
proxy / GPU-owed) in **`docs/claims_ledger.md`**.

Or run each individually — every command below was re-run from a clean checkout on 2026-06-21 and
matches the committed `results/*.json` (see `docs/reproducibility_audit_2026-06-21.md`):

```bash
python src/transition_metal_oxide_qsci.py   # CrO 0.038 / NiO 0.197 mHa (20q, open-shell multireference)
python src/sno_demo.py                       # SnO  ≤0.5 mHa, chem-acc (16q EUV target; value PySCF-version sensitive)
python src/sno2_demo.py                      # SnO₂ 0.23 mHa (20q)
python src/stage2_refinement.py              # two-stage GQE: H2 0.000 / H4 0.009 / H6 0.297 mHa
python src/gqe_qsci.py                        # integrated GQE→QSCI at 12q: 1.05 mHa
python src/hamlib_validate.py 14             # HamLib equivalence at 28q (also: 16→32q, 20→40q)
python src/classical_baselines.py            # timed classical ladder HF/MP2/CCSD(T)/FCI on Hn
python src/encoder/decisive_transfer.py 180  # decisive cross-family conditional-encoder test
```

**Expected inputs/outputs.** Inputs: none external — geometries/active spaces are defined in each
script; Hamiltonians are built in-process (PySCF→OpenFermion). Outputs: one `results/*_evidence.json`
per script (energies, errors in mHa, determinant counts, wall-clock) plus stdout summarizing the
headline value. Runtimes are seconds–minutes on CPU through 28q.

**GPU / data-gated (Phase 3, not in the CPU set above):** `dmrg_scale.py` needs `block2`;
`qsci_vec.py` needs the HamLib pickles; the 40q MPS and near-38q transition-metal runs need
CUDA-Q + an NVIDIA GPU on qBraid (see below).

> Note: exact statevector Hamiltonian expectation is the CPU bottleneck beyond ~12–16 qubits — exactly
the cost the QSCI step and the GPU/MPS backend remove. FCI wall-clock itself jumps ~24× from 20→24
qubits (`results/classical_baselines_evidence.json`).

## Running on qBraid (Phase 3)

The headline scaling runs (40q MPS, near-38q transition-metal oxides, QPU validation) execute on
qBraid with CUDA-Q + GPU credits. Step-by-step:

1. **Launch:** click the **Launch on qBraid** badge above to clone this repo into your qBraid account.
2. **Environment:** select a GPU instance; `pip install -r requirements.txt` then `pip install -r
   requirements-gpu.txt` (the GPU-only `cudaq`, `quimb`, `block2`). On a CPU-only box install only
   `requirements.txt` — the GPU extras will not install without CUDA.
3. **Reproduce CPU results first:** run the commands in [Reproduce](#reproduce-cpu--verified) to confirm
   the verified numbers in the qBraid environment.
4. **GPU scaling runs** *(scripts finalized once access is live — placeholders tracked in
   `docs/phase3_writeup_draft.md` §5c):* 40q MPS GQE/QSCI on H₂₀; near-38q CrO/NiO; quantum-vs-classical
   wall-clock; 10–16q IonQ/IBM QPU validation. Each prints qubit count, circuit depth, shot budget,
   bond dimension, and wall-clock, and writes a `results/*.json`.

*Expected outputs match the values in the write-up; a result that does not reproduce is flagged as
such (Top-Action: be honest about limitations).*

## Paper

The Phase 2 submission is in [`paper/`](paper/). The document is generated programmatically (`paper/build_phase2.js`, docx-js) rather than hand-edited.

## Team

EIGENNEXUS — Christian Metzl, Fares Eldibani, Juan Manuel Aguiar Hualde.

---

*Competition entry — keep this repository private while the challenge is ongoing.*
