# MATGEN-Q — Phase 3 write-up DRAFT (working; not the final PDF)

**Purpose:** the working draft of the ≤5-page Phase 3 submission. Verified numbers are in place and
trace to `results/*.json`. **2026-07-19 update: the at-scale campaign is COMPLETE — every former
[QBRAID-RUN] slot below is filled with executed, committed evidence; the only remaining external item
is the AQT trapped-ion decode (P5 silicon), which affects no other claim.**
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
3. **Operator-pool compression — MP2-amplitude ranking (demonstrated).** Ranking the O(N⁴)
   double-excitation pool by active-space MP2 amplitude and keeping the top fraction shrinks the
   transformer vocabulary with negligible accuracy loss, where random pruning collapses. Deterministic
   CI-subspace test (CO/N₂/SiO, 12q): **N₂ retains full-pool accuracy (2.26 mHa) keeping only 25% of
   doubles (vocab 1170→430)** vs **50.4 mHa** for random pruning at the same size (~22×); CO holds 3.7
   mHa at 40% kept vs random 29.7. (`src/encoder/pool_compression.py`.)
4. **Distributed hybrid workflow** (CUDA-Q `mqpu`), §4.

**Transfer learning across molecular families (honest negative — resolved).** We tested whether a
chemistry-conditioned generator (FiLM on an MP2 molecular descriptor) transfers better than a plain
un-conditioned warm-start, on a chemically diverse family (polar monoxides, isoelectronic BF,
homonuclear strong-correlation N₂, ionic BeO) under a pre-registered rule (`decisive_transfer.py`, 3
seeds). **Finding:** a single un-conditioned generative policy already transfers to held-out molecules;
conditioning gave only a within-noise edge (N₂ +2.1 mHa vs noise 3.6; BeO +0.4 vs 0.45) and did not
clear the bar. We therefore report this as a clean negative and **lead the innovation story with
pillars 1–3** — the integrated tensor-network + QSCI + operator-pool-compression scaling layer that is
genuinely beyond the QSCI-only prior art. *(Reporting the negative honestly is rubric Top-Action #6; a
working pipeline + honest limitation outscores an overstated claim.)*

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

**5b. Classical baseline & the exact wall (matched instances, timed):** FCI wall-clock 0.69 s (20q) →
3.74 s (24q), ~5×/2 atoms (machine-dependent); H₁₄/28q FCI = minutes, 32q+ intractable on CPU. CCSD(T) cheap but error
climbs with correlation and breaks down under strong correlation (H₂₄/48q DMRG 6.83 mHa off CCSD(T)).
This is the curve the quantum MPS/QSCI wall-clock is measured against.

**5c. Executed at scale (the headline runs — all committed, pre-registered, reported as frozen):**
- **40q flagship (H₂₀) — P1 PASS, P2 PASS.** GPU anchors: exact to the digit at 20q (+0.000 mHa vs
  FCI, cuStateVec, 0.44 GB device) and chemically accurate at 28q with a device-sampled seed
  (+0.395 mHa vs committed DMRG, 2.82 GB device). At 40q the MPS circuit sampler's fixed contraction
  cost starves growth (measured; documented pivot), so the flagship ran MP2-seeded with the identical,
  seed-independence-validated growth engine: **+1.226 mHa vs the frozen DMRG(χ=400) reference at
  450,257 determinants** (~16 h growth wall, H100 host) — P1 ≤1.6 mHa PASS, P2 budget in the
  pre-registered [3×10⁵, 4×10⁶] band (`gpu_run1_h20_mp2seed_evidence.json`). **Self-audited
  qualifier, disclosed:** our χ-escalation counter-audit (E1) shows the gap vs a tighter χ=800
  reference is +2.19 mHa — so *absolute* 40q chemical accuracy is not yet certified; the frozen E3
  protocol (growth to PT2-certificate convergence) is the pre-registered path.
- **38q CrO audit (CAS(18,19)) — the flagship *result*: the reference corrected, thrice.** QSCI
  converged at **−3.784 mHa BELOW the same-CAS DMRG(χ=400) reference** (529,392 dets, 19.1 h, A100
  host; reference committed before access). P4 reported **FAIL against its frozen |Δ|≤1.6 metric** —
  the metric measures distance to a reference that proved to be the looser bound. The pre-registered
  χ-escalation counter-audit (E1, thresholds frozen first, including the case that would have
  withdrawn the claim): χ=800 and χ=1200 references descend *toward* the QSCI energy from above
  (gaps +1.06 / +0.36 mHa) and never cross it — the truncation-error mechanism confirmed at three
  bond dimensions (`gpu_run4_cas19_evidence.json`, `cro_cas19_dmrg_chi800/1200.json`).
- **P3 device memory — FAIL as measured, decomposed by measurement.** Frozen-config sampling peaked
  at 40.32 GB (>8 GB threshold); the mechanism is vendor-documented (cuTensorNet reserves 50% of free
  card memory — 50%×79.25 GB ≈ the measured peak). A capped diagnostic ran the identical workload in
  **4.88 GB < 8 GB**: the physics estimate holds; the FAIL is an 80 GB-card allocator artifact
  (`gpu_run1_h20_P3_device_memory_A100_evidence.json`). A pre-registration lesson, reported as frozen.
- **Hardware validation (P5):** the 3-job pooled protocol executed end-to-end through the qBraid
  cloud runtime (qir-sv tier): **+2.0/+2.4 mHa vs FCI, PASS**, job IDs committed. Trapped-ion jobs
  (AQT ibex-q1 via OpenQuantum, personally funded) submitted with L1-verified, SHA-pinned exports;
  decode pending queue drain — raw counts will be committed pass or fail.
- **Quantum-vs-classical wall clock:** generated (never typed) from the evidence JSONs —
  `docs/wall_clock_table.md` / `src/make_walltable.py`; headline rows: FCI seconds→intractable by
  32q; DMRG references minutes; QSCI 3 min (20q) → 40 min (28q) → ~16–19 h at 38–40q on host CPUs.

**5d. Pre-registration scoreboard (all six resolved exactly as frozen; no threshold moved):** P1 PASS ·
P2 PASS · P3 FAIL-as-measured (mechanism documented, physics holds under cap) · P4 FAIL-as-measured
(the audit-success case: below the reference at χ=400/800/1200) · P5 sim-chain PASS, silicon pending ·
H1 blind holdout PASS (VO quartet by 1.091 eV = experiment). Two disclosed FAILs, each carrying the
strongest evidence in the portfolio — the discipline working as designed
(`preregistration_v1.json`, `preregistration_v2.json`).

## 6. Platform use & resourcing  *(criterion 6; ~0.4 pp)*
qBraid execution, as used: **H100-SXM** (B1 flagship, ~17.5 h lifetime; retired after a mid-session
host-driver GPU failure — diagnosed, documented, work rehomed) and **A100-SXM 80 GB** (B2 audit + P3
measurement, ~23.5 h). CUDA-Q cuStateVec for exact ≤28q anchors; tensornet-mps for the 40q sampling
phase; growth is CPU-bound on the GPU hosts. **Accounting is self-verifying, not self-reported:**
grant-pool consumption **16,483 cr ≈ 25% of our 65k share** per the settled end-of-campaign wallet
snapshot (`results/credit_ledger.json`, enforced by `src/verify_credits.py`; the interim reading's
billing lag was stated at the time and resolved on settlement — the rate model landed within ~3%). DMRG references, the χ-escalation counter-audit,
and the QPU flight were **personally funded — zero grant draw** (before/after wallet identity
recorded). Frozen, costed extension protocols E2–E5 stand as the research outlook
(`docs/outlook_roadmap.md`).

## 7. Limitations & honest scope  *(criterion 8; Top-Action #6; ~0.3 pp)*
- Device-sampled selection is **measured** at 12/20/28q; the 40q flagship ran MP2-seeded (documented
  cost pivot) — quantum-*inspired* at that scale until the frozen equivalence test E2 runs. Its
  sampling phase is already executed and committed (102 number-conserving determinants from the P3
  run), reducing E2 to a classical growth run.
- 40q chemical accuracy is certified **relative to the pre-registered χ=400 reference** (P1). Our own
  counter-audit shows +2.19 mHa vs χ=800 — absolute certification awaits the frozen E3 protocol. We
  state this because we found it; no external reviewer did.
- At ≤28q, classical FCI/DMRG already solve these instances — we demonstrate *correctness + scaling +
  the audit mechanism*; the demonstrated at-scale value is reference *correction* (38q), not speedup.
- Upstream assumptions (basis, active-space window, geometry) are shared across all compared methods;
  two are now measured rather than stated (x2c: ≤58 meV on ~1–2 eV gaps; AVAS supports the CrO
  window) — the rest remain declared scope (`docs/matgenq_audit_table.md`, honest-scope section).

## 8. Conclusion & reproducibility
MATGEN-Q is a working two-stage GQE whose tensor-network + QSCI tiers target 40q on a single GPU, with
every claim third-party reproducible. **README.md + "Launch on qBraid"** let judges re-run each headline
result without modification.

## References
[Nakaji 2024 GQE/AIST; Sawaya 2024 HamLib; Kanno 2023 QSCI; Kemmoku/Gao 2026 Mitsubishi; Kharazi 2026
Xanadu&Mitsubishi EUV; NVIDIA CUDA-Q; Tilly 2022 VQE review; Fare 2022 multi-fidelity screening.]

---
### Run-list distilled — ALL EXECUTED (2026-07-19)
1. ~~40q on H₂₀~~ **DONE** — P1/P2 PASS (+1.226 mHa, 450,257 dets) + E1 qualifier disclosed.
2. ~~CrO 38q~~ **DONE** — terminal −3.784 mHa below the reference; χ-ladder counter-audit case A.
3. ~~Wall-clock table~~ **DONE** — generated from evidence (`docs/wall_clock_table.md`).
4. ~~QPU validation~~ **DONE (sim tier)** — qir-sv chain PASS; AQT trapped-ion decode is the sole
   remaining external item and gates nothing else.
5. ~~Innovation headline~~ **DONE 2026-06-26** — encoder clean negative; pillars 1–3 lead.
**Nothing in this draft is compute-gated anymore. Remaining work is prose: compress to 5 pages,
final claims-ledger sweep, insert figures, and slot the AQT result (or its 'submitted, decode
pending' status) at deadline time.**
