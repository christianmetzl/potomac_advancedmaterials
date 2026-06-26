# Classical baselines — quantum-vs-classical on matched instances

**Why this doc:** Phase 3 Top-Action #2 names a classical baseline *"the single most common gap in
Phase 2 submissions"* — every result must be compared to a non-quantum method on the **same problem
instance**. This assembles that comparison from our verified results (`results/*.json`, reproduced in
the 2026-06-21 audit) and states honestly where the quantum approach does and does not yet beat
classical. Cells marked **[run on qBraid]** are the timed/GPU executions to add during Phase 3.

## 1. Accuracy — quantum pipeline vs classical reference, same instance

The classical references are **FCI** (exact, ≤20q), **CCSD(T)** (classical gold standard near
equilibrium), and **DMRG** (classical tensor-network, the reference under strong correlation). Our
quantum pipeline is **GQE** (generative circuit discovery) + **QSCI** (quantum-selected CI). Error =
|E_method − E_FCI/CASCI| in mHa; chemical accuracy = 1.6 mHa.

| Instance | Qubits | Classical ref (energy, Ha) | Classical CCSD(T)/DMRG | **Quantum (GQE/QSCI) error** | Verdict |
|---|---|---|---|---|---|
| H₂ | 4 | FCI −1.145940 | exact | GQE 0.146 mHa | ✓ chem acc |
| H₄ | 8 | FCI −2.156857 | exact | GQE+refine 0.009 mHa; QSCI(27 det) 0.29 | ✓ |
| H₆ | 12 | FCI −3.170505 | exact | GQE+refine 0.298; **GQE→QSCI 1.05** | ✓ |
| H₁₀ | 20 | FCI −5.202826 | **DMRG 0.00 mHa (=FCI)** | QSCI(2401 det) 0.57 | ✓ |
| H₁₄ | 28 | CCSD(T) ref | — | QSCI(18201 det) 1.21 | ✓ |
| H₂₀ | 40 | — | DMRG (bond-dim limited) | QSCI converging 39 mHa | **[run on qBraid]** → target ≤1.6 |
| H₂₄ | 48 | CCSD(T) −12.329874 | **DMRG −12.323043 (6.83 mHa, M=250)** | — | classical itself strained here |
| SnO | 16 | FCI −288.159492 | — | QSCI 0.11 mHa | ✓ real Sn-oxide |
| SnO₂ | 20 | FCI −362.865073 | — | QSCI 0.23 mHa | ✓ |
| CrO ⁵Π | 20 | CASCI −1117.891641 | — | QSCI 0.038 mHa | ✓ open-shell multireference |
| NiO ³Σ⁻ | 20 | CASCI −1581.354256 | — | QSCI 0.197 mHa | ✓ (above 0.08; honest) |
| CrO/NiO | ~38 | — | DMRG/FCI ref | — | **[run on qBraid]** — the §5 reframed claim |

**Reading:** at every scale we can currently run, the quantum pipeline reproduces the classical
reference **to chemical accuracy** — establishing *correctness*. It does not yet *beat* classical here
(see §3).

## 2. Cost & scaling — where classical exact simulation breaks

The honest quantum-advantage argument is about **scaling of the simulation layer**, not accuracy at
small size. Exact classical statevector simulation of the quantum state cost (measured,
`lightning.qubit`, single Hamiltonian-expectation eval):

| Instance | Qubits | H terms | ms / exact eval | Classical exact status |
|---|---|---|---|---|
| H₆ | 12 | 919 | 42 | feasible |
| H₈ | 16 | 2,913 | 1,347 | edge of feasibility |
| H₁₀ | 20 | 7,151 | 88,500 | **CPU-prohibitive** (~2100× the 12q cost) |
| H₂₀ | 40 | 116,577 | — | exact statevector ≈ **16 TB RAM — infeasible** |

→ Exact classical statevector GQE training is wall-bound at ~16 qubits. The MPS (tensornet-mps) +
QSCI approach replaces 2ⁿ memory with entanglement-bounded cost, which is the mechanism that carries
24→40q. **[run on qBraid]**: report MPS bond-dimension vs error, and MPS/QSCI wall-clock vs the exact
statevector and vs VQE, on matched instances.

## 3. Honest quantum-vs-classical delineation (rubric Top-Action #6)

- **What is genuinely quantum:** GQE's generative circuit discovery (sidesteps VQE barren plateaus —
  an optimization-landscape advantage), and QSCI's determinant selection from circuit sampling (the
  device defines the subspace; intrinsically noise-robust, demonstrated at 20q).
- **What is still classical in our pipeline:** the QSCI energy is a *classical* diagonalization in the
  selected subspace, and at scale we currently select determinants **perturbatively** (a
  hardware-independent proxy), validated against true circuit-sampling at 12q. Until run with real
  sampling on qBraid, the large-scale QSCI numbers are quantum-*inspired*, not quantum-*executed*.
- **Where classical still wins today:** at ≤28q, classical FCI/DMRG solve these instances outright
  (DMRG reproduces H₁₀ to 0.00 mHa). We have **not** shown a regime where quantum beats classical —
  we have shown the pipeline is *correct* and its simulation layer *scales*.
- **Where the genuine-advantage regime is:** 40q+ strong correlation (stretched chains, open-shell
  oxides) where DMRG bond dimension explodes — visible already at H₂₄/48q, where classical DMRG itself
  is 6.83 mHa off CCSD(T) at M=250. Demonstrating the MPS+QSCI pipeline holding chemical accuracy
  there, on GPU, is the Phase 3 win condition. **[run on qBraid]**.

## 4. Baselines still to compute/time (access-independent, short CPU runs)

A `src/classical_baselines.py` pass can fill these from the same geometries, all quick on CPU:
- Per instance: HF, MP2, CISD, CCSD, CCSD(T), FCI/CASCI energies **with wall-clock**, tabled beside the
  quantum error — so every quantum cell has a matched, timed classical cell.
- DFT (B3LYP/PBE0) energies on the oxides, to quantify the *"0.3–0.5 eV functional-dependent error"*
  the paper cites as the motivation for quantum accuracy on open-shell oxides.

These need neither qBraid nor the encoder verdict and can run as soon as the CPU is free (the encoder
sweep is using it now).

## 5. Cross-references
- `reproducibility_audit_2026-06-21.md` — every quantum number above is reproduced there.
- `phase3_plan_to_win.md` §4 pillar 3 — this doc is that pillar's substance.
- `paper_version_discrepancy.md` §5 — the 38q CrO/NiO row here is the reframed claim.
