# MATGEN-Q — Phase 3 write-up DRAFT (working; not the final PDF)

**Purpose:** the working draft of the ≤5-page Phase 3 submission. Verified numbers are in place and
trace to `results/*.json` (reproduced in `reproducibility_audit_2026-06-21.md`). Cells tagged
**[QBRAID-RUN]** are the executions still owed once qBraid access is live — they are the *only* gaps.
This draft already embeds the honest 38q reframe (`paper_version_discrepancy.md` §5) and the mandated
classical baselines (`classical_baselines.md`). Section 3's innovation headline resolves on the
decisive-encoder verdict (`phase3_novelty_assessment.md`).

Structure follows the 8-criterion Phase 3 rubric and the six "Top Actions." Target: 5 pages, 11pt
Times New Roman, single-spaced, excl. references + cover page.

---

## Title
**MATGEN-Q: Scaling a Two-Stage Generative Quantum Eigensolver to 40 Qubits on NVIDIA CUDA-Q for
EUV Photoresist Chemistry** — Team EIGENNEXUS, Advanced Materials (Mitsubishi Chemical & AIST).

## 1. Focus area & rationale  *(criteria 2, 5; ~0.5 pp)*
Ground-state energy estimation governs the redox and reaction thermodynamics of EUV photoresist
metal-oxides (Sn/Hf/Zr oxides), whose open-shell, multireference character is exactly where classical
DFT incurs 0.3–0.5 eV functional-dependent errors and makes candidate rankings unreliable. GQE
(Nakaji et al. 2024, AIST) replaces variational optimization with a generative transformer that
proposes circuits, sidestepping barren plateaus; QSCI-paired GQE reached 32q only recently
(Kemmoku/Gao 2026, Mitsubishi). **Our contribution: the tensor-network simulation tier + operator-pool
compression that carry this generative pipeline to the ~40-qubit, industrially relevant regime, with
executed, reproducible results.**

## 2. Target system, data & reproducibility  *(criteria 2, 8; ~0.75 pp)*
- **Scaling vehicle:** linear Hₙ chains (n=2…20; 4–40q, STO-6G, Jordan–Wigner) — the canonical
  strong-correlation benchmark; one bond-length knob tunes weak→strong correlation.
- **Target chemistry:** Sn-oxide active spaces (SnO 16q, SnO₂ 20q) and open-shell transition-metal
  oxides (CrO ⁵Π, NiO ³Σ⁻, 20q) — genuine multireference systems.
- **Data integrity (Top-Action: reproducibility):** Hamiltonians built by a HamLib-replicating
  pipeline (PySCF→OpenFermion→JW), **validated against published HamLib files at 28/32/40q**: exact
  term-count match (27,735 / 47,489 / 116,577) and coefficient agreement to ~15 sig figs, differing
  only by a spectrum-invariant orbital-phase gauge. Every Hamiltonian is third-party reproducible.
- **Accuracy anchors / classical references:** FCI (exact, ≤20q), CCSD(T) near equilibrium, DMRG under
  strong correlation (verified = FCI to 0.00 mHa at 20q).

## 3. GQE approach & algorithmic innovation  *(criterion 3 — primary novelty; ~1 pp)*
**Two-stage GQE.** Stage 1: a decoder-only GPT-QE transformer trained by sequence–energy matching
generates circuits as token sequences over a UCC excitation pool. Stage 2: adjoint-gradient continuous
angle refinement → chemical accuracy.

**Four scaling pillars (the innovation):**
1. **MPS (tensornet-mps) simulation — primary scaling enabler.** Memory scales with entanglement, not
   2ⁿ; near-equilibrium area-law bounds bond dimension. Exact cuStateVec validates ≤~32q; MPS carries
   32–40+q. *This tensor-network tier is what we add beyond the QSCI-only 32q prior art.*
2. **QSCI energy evaluation** — diagonalize H in a measurement-selected determinant subspace;
   intrinsically noise-robust (device defines only the subspace).
3. **Operator-pool compression** — MP2-amplitude + point-group/spin symmetry pruning of the O(N⁴)
   double-excitation pool → smaller vocabulary and shallower circuits at scale.
4. **Distributed hybrid workflow** (CUDA-Q `mqpu`), §4.

**[VERDICT-DEPENDENT] Chemistry-conditioned encoder.** A FiLM-conditioned generator (MP2 molecular
descriptor) for cross-family transfer. *Decisive cross-family test in progress
(`decisive_transfer.py`, pre-registered rule).* → If validated: headline this as transfer-learning
innovation. → If not (warm-start already transfers): report the **honest negative** — "a single
generative policy already transfers across these families; conditioning is unnecessary" — a genuine
finding that supports leading the innovation story with pillars 1–3. *(Either way, reported honestly —
Top-Action #6.)*

## 4. Hybrid architecture  *(criterion 5; ~0.5 pp)*
Classical transformer trains on GPU (PyTorch); circuit evaluations dispatched across GPUs via CUDA-Q
`mqpu` in an asynchronous generate→evaluate→update loop. Quantum side: state prep + energy estimation
(MPS/QSCI). Classical side: generation, optimization, active-space selection. Stage 1 is
sampling-bound/parallelizable; Stage 2 is gradient-bound/adjoint-efficient. *(Figure 1: architecture.)*

## 5. Phase 3 execution & results  *(criterion 7 — NEW, "critical"; criteria 1, 4, 6; ~1.5 pp)*
*This is the section the Phase 3 rubric weights hardest: concrete, executed, reproducible numbers with
qubit count, circuit depth, shot budget, and wall-clock.*

**5a. Verified today (CPU, reproduced in audit):**

| Result | Qubits | Quantum (GQE/QSCI) | Classical ref | Status |
|---|---|---|---|---|
| Two-stage GQE H₂/H₄/H₆ | 4/8/12 | 0.146 / 0.009 / 0.298 mHa | FCI (exact) | ✓ chem acc |
| Integrated GQE→QSCI H₆ | 12 | 1.05 mHa (raw 51→1.05, ~50×) | FCI | ✓ measured pipeline |
| QSCI scaling H₁₀/H₁₄ | 20/28 | 0.57 / 1.21 mHa | FCI / CCSD(T) | ✓ (2401 / 18,201 dets) |
| CrO ⁵Π / NiO ³Σ⁻ | 20 | 0.038 / 0.197 mHa | CASCI (exact) | ✓ open-shell multireference |
| SnO / SnO₂ | 16/20 | 0.11 / 0.23 mHa | FCI | ✓ EUV target chemistry |
| Noise robustness H₁₀ | 20 | ≤3.3 mHa @ 30% corrupt | — | ✓ noise-aware bonus |

**5b. Classical baseline & the exact wall (matched instances, timed):** FCI wall-clock 0.33 s (20q) →
7.8 s (24q), ~24×/2 atoms; H₁₄/28q FCI = minutes, 32q+ intractable on CPU. CCSD(T) cheap but error
climbs with correlation and breaks down under strong correlation (H₂₄/48q DMRG 6.83 mHa off CCSD(T)).
This is the curve the quantum MPS/QSCI wall-clock is measured against.

**5c. To execute on qBraid GPU (the headline runs):**
- **[QBRAID-RUN] 40q scalability (primary criterion):** MPS GQE/QSCI on H₂₀ → energy error vs DMRG,
  **circuit depth, bond dimension, shot budget, GPU wall-clock**. Target: chemical accuracy (or the
  closest credible approach) at 40q — the win condition. (CPU today: operational, converging @ 39 mHa.)
- **[QBRAID-RUN] CrO/NiO near-38q on GPU:** report the accuracy **actually achieved** + wall-clock.
  *Honest reframe:* lead with executed 20q (CrO 0.038 / NiO 0.197 mHa) and present 38q as the GPU
  **scaling demonstration**, not a pre-claimed number — the prior "≤0.08 mHa @ 38q" is kept only if a
  run earns it (`paper_version_discrepancy.md` §5).
- **[QBRAID-RUN] Hardware validation:** selected circuits on IonQ/IBM QPU at 10–16q (depth/shots).
- **[QBRAID-RUN] Quantum-vs-classical wall-clock table:** MPS/QSCI vs exact statevector vs VQE on
  matched instances.

## 6. Platform use & resourcing  *(criterion 6; ~0.4 pp)*
qBraid: classical (CPU/GPU) + quantum (QPU) credits. **NVIDIA H100/A100 (80 GB)** + CUDA-Q;
`tensornet-mps` for 24–40q, cuStateVec for exact ≤32q validation; 1 GPU for MPS, 4–8 (NVLink) for
distributed eval + >40q bonus. QPU (IonQ/IBM) for 10–16q validation. Per-run estimates:
**[QBRAID-RUN]** qubit/depth/shot/wall-clock filled from §5c.

## 7. Limitations & honest scope  *(criterion 8; Top-Action #6; ~0.3 pp)*
- Integrated GQE→QSCI **measured** at 12q; larger QSCI uses **perturbative selection as a
  hardware-independent proxy**, validated against the 12q measured pipeline — quantum-*inspired* at
  scale until run with real sampling.
- At ≤28q, classical FCI/DMRG already solve these instances — we demonstrate *correctness + scaling*,
  not yet a regime where quantum beats classical. The genuine-advantage target is 40q+ strong
  correlation where DMRG bond dimension explodes.
- 40q is operational, not yet at chemical accuracy on CPU; the GPU run is the deliverable.

## 8. Conclusion & reproducibility
MATGEN-Q is a working two-stage GQE whose tensor-network + QSCI tiers target 40q on a single GPU, with
every claim third-party reproducible. **README.md + "Launch on qBraid"** let judges re-run each headline
result without modification.

## References
[Nakaji 2024 GQE/AIST; Sawaya 2024 HamLib; Kanno 2023 QSCI; Kemmoku/Gao 2026 Mitsubishi; Kharazi 2026
Xanadu&Mitsubishi EUV; NVIDIA CUDA-Q; Tilly 2022 VQE review; Fare 2022 multi-fidelity screening.]

---
### Run-list distilled (what unblocks the final PDF)
1. 40q MPS GQE/QSCI on H₂₀ (depth, χ, shots, wall-clock, err vs DMRG) — **primary**.
2. CrO/NiO near-38q on GPU (accuracy achieved + wall-clock) — honest reframe.
3. Quantum-vs-classical wall-clock table (MPS/QSCI vs statevector vs VQE).
4. 10–16q IonQ/IBM QPU validation.
5. Final innovation headline per encoder verdict.
All are GPU/qBraid-gated; everything else in this draft is done.
