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
| **GPU-executed 20q H₁₀ (cuStateVec)** | **+0.000 mHa** vs FCI, 0.44 GB device | exact GPU-execution anchor on real NVIDIA hardware via qBraid |
| **GPU-executed 28q H₁₄ (cuStateVec)** | **+0.395 mHa** vs DMRG(χ=400), 2.82 GB device | device-sampled QSCI grown to 64,212 dets; meets pre-registered P1/P3 |
| **40q H₂₀ flagship (executed)** | **+1.226 mHa** vs DMRG(χ=400), 450,257 dets | P1 PASS; MP2-seeded, seed-independence-validated engine (~16 h, H100 host). Frozen E3 certificate reached terminal it5 (external pod kill during it6 growth): **E_var +0.185 mHa vs χ=400** (prediction ii MET), 750,257 dets (iii MET), \|PT2\| trace to 1.31 mHa; \|PT2\|≤0.5 (i) unreached, as-measured |
| **40q absolute anchor (E6, DMRG extrap.)** | FCI(40q) = **−10.293599 ± 0.022 mHa** (R²=0.997); E3 it5 E_var **+1.59 mHa** → chem-acc | independent DMRG χ=400→2400 truncation-error extrapolation; certifies 40q absolute accuracy (pre-registered; `e6_dmrg_extrap_40q.py`) |
| **38q CrO audit (CAS(18,19), executed)** | **−3.784 mHa BELOW** same-CAS DMRG(χ=400) | reference *corrected*: χ=800/1200 descend toward QSCI from above (+1.06/+0.36 mHa), never cross — truncation-error mechanism at three χ |
| **38q Sn₂O₂ EUV motif (E4, executed)** | **−0.399 mHa BELOW** same-CAS DMRG(χ=400) | a second reference correction, on the real tin-oxo chemistry (524,764 dets, 7.4 h) |
| **EUV-motif trust curve (Sn₂O₂ cleavage)** | in-active-space CCSD(T) 0.14→5.49 mHa (~40×); QSCI ≤0.47 mHa | Sn–O bridge 2.05→3.28 Å; dominant-det weight collapses 0.95→0.53 (`sn2o2_dissociation.py`) |
| **Real trapped-ion QPU (AQT ibex-q1, decoded)** | device-sampled +20.4/+11.1 mHa; device-seeded QSCI → exact FCI | genuine 12q trapped-ion silicon (2,000 shots/job, decoded 2026-07-20); qir-sv sim tier +2.0/+2.4 mHa PASS |
| HamLib validation, 28/32/40q | exact | term counts match (27,735 / 47,489 / 116,577); coefficients agree to ~15 sig figs, differing only by a spectrum-invariant orbital-phase gauge |
| Noise robustness, 20q | ≤3.3 mHa at 30% corrupted measurements | graceful degradation |
| Sn-oxides (EUV target) | SnO (16q) & SnO₂ (20q) chemical accuracy — ≤0.6 mHa asserted by reproduce.py (observed 0.11–0.45 / 0.18–0.23 across environments) | Sn effective-core-potential CASCI active spaces; construction validated on H₄ to 0.0000 mHa |
| **CrO ⁵Π / NiO ³Σ⁻ (20q)** | **0.038 / 0.197 mHa** | open-shell multireference oxides vs CASCI (`transition_metal_oxide_qsci.py`) |
| **CrO spin-state decision** | DFT spans 1.9 eV, B3LYP flips the sign; CASCI/QSCI **+1.89 eV quintet = experimental X⁵Π** | turns "DFT mis-ranks the candidate" into a worked decision (`cro_spin_gap.py`) |
| **CrO dissociation trust (real oxide)** | in-active-space CCSD(T) erratic / non-convergent (to ~140 mHa vs CASCI); QSCI variational ≤2.8 mHa | the strong-correlation trust story on a real Cr–O bond, not toy H₁₀ (`cro_dissociation.py`) |
| EN-PT2 error certificate | E_var (rigorous upper bound) + E_var+PT2 (estimate, converges to FCI from above); equilibrium extrapolation → FCI +4.1 mHa (R²=0.999) | certifies convergence, CIPSI standard (`encoder/selci_pt2.py`) |
| Generator learned MP2 hierarchy | Spearman ρ=0.31 (p<0.002), 4/8 top-double overlap | energy-trained generator (blind to MP2) recovers the MP2 amplitude ordering (`encoder/generator_mp2.py`) |
| **CUDA-Q execution (qpp-cpu)** | H₄ VQE **within 0.02 mHa** of FCI (0.011–0.013 across runs); QSCI within chemical accuracy (sampling-based) | GQE/QSCI pipeline runs through the CUDA-Q SDK on CPU (`cudaq.observe`/`cudaq.sample`); `src/cudaq_qsci.py` |
| **MPS bond-dim / entanglement (pillar 1)** | χ for chem-acc ≈50/100/400 @20/28/40q; Sₘₐₓ 0.39→4.43 | bond dimension grows slowly with size; area-law near equilibrium → strong correlation; `src/mps_bonddim_study.py` (block2 DMRG) |
| **Quantum-vs-classical crossover** | 40q: 16 TB statevector → 195 MB MPS (measured χ=400); FCI 3.4×10¹⁰ dets → ~1.1×10⁶ QSCI (0.003%) | the two classical walls removed, synthesized from measured χ + determinant scaling; `src/crossover_study.py` |
| **Bridged tin-oxo (real EUV motif)** | Sn₂O₂ rhombus (Sn–O–Sn) **0.41 mHa** vs CASCI (16q) | genuine bridged tin-oxo unit, not a diatomic/linear O=Sn=O; `src/tin_oxo_demo.py` |
| **Blind one-shot holdout (VO)** | pre-registered predictions **held**: QSCI 0.167/0.133 mHa; quartet ground = experimental X⁴Σ⁻ | frozen code (SHA pre-committed), untouched molecule, single run reported as-is; `src/blind_holdout_vo.py` |
| **QSCI under real CUDA-Q noise channel** | H₄ holds chemical accuracy to **5% per-gate depolarizing** (density-matrix-cpu) | physical noise channel via the CUDA-Q SDK — hardware-representative QPU stand-in; `src/cudaq_noise.py` |

## Honest scope

- The **integrated GQE→QSCI loop is measured at 12q and GPU-executed at 20q/28q** on real NVIDIA hardware (cuStateVec, device-sampled; +0.000 / +0.395 mHa). The at-scale ladder beyond that uses a **hardware-independent determinant-space proxy** for the measurement step, *validated against* the measured 12/16/20q pipeline.
- The 40q flagship is **executed and chemically accurate relative to its pre-registered DMRG(χ=400) reference** (+1.226 mHa, P1 PASS). Absolute 40q certification is the frozen **E3** protocol, terminal at **it5** (ended by an external pod kill during it6 growth, disclosed): prediction ii MET (E_var +0.185 mHa vs χ=400) at 750,257 dets (iii MET), a clean converging \|PT2\| trace to 1.31 mHa; the \|PT2\|≤0.5 mHa point (~it10–11) was unreached, reported as-is. A pre-registered independent DMRG-extrapolation anchor (**E6**) closes the gap the killed PT2 run left: high-χ DMRG (χ=400→2400) extrapolated on discarded weight gives **FCI(40q) = −10.293599 ± 0.022 mHa (R²=0.997)**, placing E3's committed it5 E_var **+1.59 mHa from the near-exact limit — 40q absolute chemical accuracy demonstrated (≤1.6), by a classical route independent of the PT2 certificate**. At 38q the audit *corrects* the DMRG reference on both CrO (−3.784 mHa) and the real Sn₂O₂ EUV motif (E4, −0.399 mHa). The remaining honest gap is the full 40q `tensornet-mps` growth run (the flagship was MP2-seeded — a documented cost pivot, growth seed-independence-validated); the GPU/QPU *platform* is proven, not owed.
- **Train-small, deploy-large (transfer result).** One generator trained only on 8q+12q systems, deployed zero-shot across **16→56 qubits**, proposes lower-energy determinant subspaces than random selection (`src/encoder/scaling_transfer.py --ladder`). The robust signals are statistical: **~3.7× tighter across-seed selection spread** (≈2.0 vs ≈7.4 mHa) and **13/18 size×seed paired wins** (binomial p≈0.05); the per-size mean advantage is all-seeds-positive at 16q and positive in the mean through 28q (+8.9/+8.3/+7.1 mHa), then narrows into noise at 40–56q. That the policy captures real chemistry is corroborated by interpretability (the learned token distribution recovers the MP2 amplitude hierarchy, ρ=0.31, p<0.002). A canonical frontier-relative tokenization makes the small vocabulary a subset of the large one; a determinant-space **selected-CI proxy** (Slater-Condon, validated to 0.0000 mHa vs Jordan–Wigner; no 2ⁿ statevector) makes 56q reachable on CPU. *Honest scope:* a mean trend that narrows into run-to-run noise beyond ~28q (not an every-seed guarantee), a relative advantage at a fixed small budget (not chemical accuracy), and a selected-CI proxy (not circuit-sampled QSCI). Cross-*chemistry* transfer wins clearly on 3/6 oxide targets (BeO a within-noise tie) and fails on SnO; target-specific MP2 beats the prior; cross-*molecule* conditioning was a within-noise tie. All reported as negatives where they are negatives.
- Sn-oxide Hamiltonians are **our own ECP-CASCI construction** (not from the HamLib library, which contains no tin oxides).

## Pre-registered predictions (GPU/QPU) and blind holdout

Every at-scale run was **pre-registered before qBraid access, then executed**: `results/preregistration_v1.json`
(+ `v2.json` for extensions E1–E5) commits quantitative pass/fail predictions (P1–P5) derived *only* from
already-committed measured data — bond-dimension χ=400 at 40q, the determinant-budget band, memory
footprint, and QPU accuracy thresholds — **before** access, with git history as the tamper-evident
timestamp. **Outcomes reported as-is, pass or fail:** P1/P2 PASS (40q flagship), P3 FAIL-as-measured
(allocator artifact, decomposed), P4 FAIL-as-measured (the audit-success case: QSCI below the χ=400
reference, mechanism confirmed at χ=800/1200), P5 executed (sim-chain PASS + trapped-ion silicon decoded).
Frozen extensions E2–E5 executed 2026-07-23: E4 a second reference correction (−0.399 mHa), E3 certificate
terminal at it5 (ii+iii MET, i not certified — external kill), E2 a disclosed resource-DNF, E5 a reported non-convergence. The launch-ready
command list is `src/GPU_RUNLIST.md` (CUDA-Q backends switch via `CUDAQ_TARGET` env vars — no code edits
between the CPU-verified and GPU runs).

The same discipline applied to something executable today: **a blind one-shot holdout** (entry H1) —
`src/blind_holdout_vo.py` was frozen (SHA-256 in the pre-registration) before its first and only
execution, predicting VO's quartet/doublet ordering with untouched code on a molecule appearing
nowhere else in this repository. Result: `results/blind_holdout_vo_result.json`, committed unedited — **both predictions held** (QSCI 0.167/0.133 mHa vs CASCI; quartet 1.09 eV below doublet, matching the experimental X⁴Σ⁻ ground term).

## Third-party HamLib re-verification

`hamlib_validate.py` generates our Hamiltonian in-process and checks it against reference invariants
extracted from the published HamLib files — **committed in the script**, so the term-count + one-norm
equivalence (27,735 / 47,489 / 116,577 terms at 28/32/40q; one-norms to ~1e-13) reproduces **offline, with
no download**. HamLib and our generation differ only by a spectrum-invariant orbital-phase convention, so the
phase-invariant one-norm is the correct quantity to compare.

**Full-operator offline cross-check (optional, bundle-able).** For a coefficient-level third-party check
without any download, `data/hamlib_slice/` can hold the genuine HamLib operators for exactly the three
H14/16/20 instances (not the whole archive). Populate it once from any machine with internet:
`python src/hamlib_extract_slice.py --file <downloaded-hamlib.hdf5>` (it self-validates each extracted
operator against the committed invariants, so it can only emit correct HamLib data), then commit
`data/hamlib_slice/`. `hamlib_validate.py` then prints a **FULL offline HamLib slice … MATCH** line — a
phase-invariant, full coefficient-magnitude comparison — with zero external config. To re-verify against the
whole archive instead, download the chemistry `ES_*_ham` HDF5 files from
`https://portal.nersc.gov/cfs/m888/dcamps/hamlib/` (Sawaya et al., Quantum 8, 1559, 2024).

## Strongest objections, and where they stand

| Objection | Where it stands |
|---|---|
| "No real GPU/QPU execution" | Resolved — executed: 20q/28q on NVIDIA GPU (cuStateVec, +0.000/+0.395 mHa), the 40q flagship (+1.226 mHa vs χ=400), the 38q CrO + Sn₂O₂ audits, and real AQT trapped-ion silicon (decoded 2026-07-20). The remaining owed piece is the full 40q `tensornet-mps` growth run, not platform viability. |
| "Large-scale numbers are a proxy, not circuit-sampled" | True and disclosed; proxy validated against measured QSCI at 12/16/20q, incl. an unflattering measured-random result we published anyway. |
| "CASCI in a modest CAS ≠ physical truth" | Correct — our accuracy claims are vs the in-CAS reference; the spin-state *ordering* claim additionally matches the experimental X⁵Π term (and is hedged to sign, not magnitude). |
| "Transfer statistics are thin (3 seeds, p≈0.05)" | Disclosed verbatim in the paper; the robust claims are the variance reduction and paired-wins count, not the mean curve. |
| "The noise study saturates a small system" | Qualified in the paper as a selection-principle check, not a hardware forecast; real-QPU validation is pre-registered (P5). |

## Repository structure

```
paper/      Phase 3 write-up (PDF + DOCX build scripts) + Phase 2 submission retained; architecture figure
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

**Pinned environment:** `requirements-lock.txt` records the exact package versions behind the committed evidence and transcript (numerics like SnO drift across PySCF versions — disclosed in the ledger; the pins reproduce the committed values most closely).

**One command** runs the verified CPU suite and checks each headline number against the committed
`results/*.json`, printing a PASS/FAIL table (`--quick` skips the slower scripts):
```bash
python src/reproduce.py     # -> 26/26 PASS (17 re-execution + 9 evidence audits; captured: docs/reproduce_transcript.txt)
python src/cost_audit.py    # re-derives the ENTIRE program cost from published pricing × committed shot/uptime configs
```
Every quantitative claim is traced to its script + evidence JSON + status (executed / circuit-sampled /
proxy / GPU-owed) in **`docs/claims_ledger.md`**.

**Cost transparency is executable, not self-reported.** `src/cost_audit.py` re-derives the whole
program's spend from **published per-unit pricing** (qBraid rate card; OpenQuantum AQT invoice) × **committed
configs** — QPU shot counts read straight from `qpu_aqt_evidence.json`, instance uptimes from the console
snapshot in `credit_ledger.json` — and reconciles it against the recorded ledger (QPU 60 cr re-derived from
committed shots; the personal **OpenQuantum pool reconciles 162 → 102 cr remaining**, matching the dashboard;
grant-attributed 75,219.7 cr; every re-derivable line matches). A judge re-checks the money the same way they
re-check the physics.

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
the cost the QSCI step and the GPU/MPS backend remove. FCI wall-clock itself jumps ~6× from 20→24
qubits (`results/classical_baselines_evidence.json`).

## Running on qBraid (Phase 3)

The headline scaling runs (40q flagship, 38q transition-metal + Sn₂O₂ oxide audits, QPU validation) were
**executed** on qBraid with CUDA-Q + GPU credits and are re-runnable there. Step-by-step:

1. **Launch:** click the **Launch on qBraid** badge above to clone this repo into your qBraid account.
2. **Environment:** select a GPU instance; `pip install -r requirements.txt` then `pip install -r
   requirements-gpu.txt` (the GPU-only `cudaq`, `quimb`, `block2`). On a CPU-only box install only
   `requirements.txt` — the GPU extras will not install without CUDA.
3. **Reproduce CPU results first:** run the commands in [Reproduce](#reproduce-cpu--verified) to confirm
   the verified numbers in the qBraid environment.
4. **GPU/QPU scaling runs (executed; re-runnable):** 40q GQE/QSCI on H₂₀; 38q CrO + Sn₂O₂ audits;
   quantum-vs-classical wall-clock; trapped-ion QPU validation (AQT via OpenQuantum, decoded). Each
   prints qubit count, circuit depth, shot budget, bond dimension, and wall-clock, and writes a
   `results/*.json`. Evidence and per-run commands: `docs/phase3_writeup_draft.md` §5 and the E-campaign
   scripts (`e3_certificate_40q.py`, `e4_sn2o2_38q.py`, `sn2o2_dissociation.py`).

*Expected outputs match the values in the write-up; a result that does not reproduce is flagged as
such (Top-Action: be honest about limitations).*

## Paper

The **Phase 3 write-up** is in [`paper/`](paper/) (`EIGENNEXUS_Phase3_Writeup.pdf`, ≤5 pages excl. references),
generated programmatically (`paper/build_phase3.js` → docx → `paper/build_pdf.py`, no hand-editing so the
PDF never drifts from the source). The Phase 2 submission is retained alongside it for reference.

## AI-use disclosure

Consistent with the challenge's stated policy (generative AI permitted for code support and writing):
AI assisted with code and prose. **All technical contributions, formulations, and results are the team's
own** — every judged claim is pre-registered with frozen protocols and thresholds (`results/preregistration_*.json`),
each traces to a committed script + evidence file (`docs/claims_ledger.md`), and all governance decisions
carry operator sign-offs in the git history.

## Team

EIGENNEXUS — Christian Metzl, Fares Eldibani, Juan Manuel Aguiar Hualde.

---

*Competition entry — Team EIGENNEXUS · GIC 2026 Phase 3 · Advanced Materials (Mitsubishi Chemical Group & AIST).*
