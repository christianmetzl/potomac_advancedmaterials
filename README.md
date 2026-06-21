# MATGEN-Q

**Scaling a conditional Generative Quantum Eigensolver (GQE) for EUV photoresist discovery with NVIDIA CUDA-Q.**

Team **EIGENNEXUS** — Global Industry Challenge (PQIC) 2026, *Advanced Materials* track (Mitsubishi Chemical Group & AIST).
**Phase 1 winner · Phase 3 finalist.**

---

## Overview

MATGEN-Q is a generative quantum-chemistry pipeline aimed at the strongly-correlated metal-oxide chemistry of EUV photoresists (Sn/Hf/Zr oxides):

1. A **two-stage GQE** — a GPT-style transformer (GPT-QE) discovers circuit structure, then adjoint-gradient refinement tunes the angles — sidestepping the barren-plateau problem of variational methods.
2. **QSCI** (Quantum-Selected Configuration Interaction) evaluates energies by diagonalizing the Hamiltonian in a compact, measurement-selected determinant subspace, avoiding the expensive full-operator expectation.
3. **Matrix-product-state (MPS) tensor-network simulation** carries the scaling toward the ~40-qubit target on a single high-memory GPU (memory scales with entanglement, not 2ⁿ).
4. A **chemistry-conditioned encoder** (equivariant GNN + transfer learning) is designed to generalize the generator across molecular families *(Phase 3 demonstration)*.

## Demonstrated results

All numbers are reproducible from the scripts in `src/` and recorded in `results/`.

| Result | Value | Notes |
|---|---|---|
| Two-stage GQE, H₂/H₄/H₆ | 0.146 / 0.009 / 0.298 mHa | chemical accuracy, 4–12 qubits |
| **Integrated GQE→QSCI, H₆ (12q)** | **1.05 mHa** | GPT-QE generates circuits → QSCI samples determinants *from the generated states* → diagonalizes; refines the raw 51 mHa generative state ~50× |
| QSCI scaling, H₁₄ (28q) | 1.21 mHa | 18,201 determinants = 0.15% of the FCI space |
| QSCI, H₂₀ (40q) | 39 mHa | operational; converging (not yet chemical accuracy — CPU-bound) |
| HamLib validation, 28/32/40q | exact | term counts match (27,735 / 47,489 / 116,577); coefficients agree to ~15 sig figs, differing only by a spectrum-invariant orbital-phase gauge |
| Noise robustness, 20q | ≤3.3 mHa at 30% corrupted measurements | graceful degradation |
| Sn-oxides (EUV target) | SnO 0.11 mHa (16q), SnO₂ 0.23 mHa (20q) | Sn effective-core-potential CASCI active spaces; construction validated on H₄ to 0.0000 mHa |

## Honest scope

- The **integrated GQE→QSCI loop is demonstrated at 12 qubits**; the larger-scale QSCI results (20–28q) use **perturbative determinant selection as a hardware-independent proxy** for the measurement step, *validated against* the 12q measured pipeline.
- The 40q result is **operational but not yet at chemical accuracy** — the GPU runs are the Phase 3 deliverable.
- The **conditional encoder is specified but not yet demonstrated** — cross-molecule transfer is the headline Phase 3 experiment.
- Sn-oxide Hamiltonians are **our own ECP-CASCI construction** (not from the HamLib library, which contains no tin oxides).

## Repository structure

```
paper/      Phase 2 submission (PDF + DOCX), the docx-js build script, and the architecture figure
src/        analysis code — GQE, QSCI, integrated GQE→QSCI, noise, DMRG, Sn-oxides, HamLib validation
results/    computational-result JSONs (every figure in the paper traces to one of these)
docs/       knowledge-transfer document (full project context and Phase 3 roadmap)
```

## Reproduce

```bash
pip install pyscf openfermion openfermionpyscf h5py pennylane pennylane-lightning \
            torch quimb block2 scipy numpy --break-system-packages

python src/gqe_scaling.py     # two-stage GQE on hydrogen chains
python src/gqe_qsci.py        # integrated GQE→QSCI pipeline at 12 qubits
python src/qsci_vec.py        # QSCI scaling on validated HamLib Hamiltonians
python src/noise_demo2.py     # QSCI noise robustness
python src/dmrg_scale.py      # DMRG reference validation
python src/sno_demo.py        # SnO active-space QSCI
python src/sno2_demo.py       # SnO₂ active-space QSCI
```

> Note: term-by-term Hamiltonian expectation becomes the speed bottleneck beyond ~12–16 qubits on CPU — this is precisely the cost QSCI and the GPU/MPS backend are designed to remove. `openfermion.get_sparse_operator` is memory-heavy past ~14 qubits.

## Paper

The Phase 2 submission is in [`paper/`](paper/). The document is generated programmatically (`paper/build_phase2.js`, docx-js) rather than hand-edited.

## Team

EIGENNEXUS — Christian Metzl, Fares Eldibani, Juan Manuel Aguiar Hualde.

---

*Competition entry — keep this repository private while the challenge is ongoing.*
