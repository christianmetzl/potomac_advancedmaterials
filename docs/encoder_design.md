# Conditional-Encoder Demonstration — Design & Pre-Registered Success Criteria

**MATGEN-Q / Team EIGENNEXUS · GIC 2026 Phase 3 · Priority #1 (novelty lever)**

Status: design pre-registered before results are read. Edit history is the audit trail —
do not retroactively soften the success criteria below to match whatever comes out.

---

## 0. Reproducibility finding (2026-06) — amends §6–§7 *before* any transfer result was read

Diagnostics on the shipped GQE machinery in a clean environment:

- **Random search**, 4000 circuits (len-8) over the fixed UCC/discrete-angle pool: best **53 mHa**
  (H6) / **45 mHa** (CO). The action space *cannot sample chemical accuracy*.
- **GPT-QE stage-1**, proper budget (batch 128, 120 it): mean generated energy **118 → 55 mHa**
  (genuine learning — the distribution shifts), best **31 mHa**. The transformer learns, but the
  discrete-angle ceiling is ~30 mHa.
- **No stage-2** (adjoint-gradient angle refinement) exists in the code — every `.backward()` trains
  the transformer, none refines circuit angles. The standalone "two-stage GQE" numbers in the
  knowledge-transfer doc (H6 0.298 mHa) are **not reproducible from the repo** (and their evidence
  JSON is absent).
- **What is reproducible:** chemical accuracy comes from the **QSCI** step.
  `gqe_qsci_evidence.json`: raw GQE 51 mHa → QSCI **1.05 mHa**.

**Consequence:** the original §7 bar ("conditioned reaches 1.6 mHa in ≤½ the evals") assumed raw GQE
reaches chemical accuracy; it does not. §6–§7 are revised to measure transfer on the quantity where
the learning actually lives (generator quality) plus the QSCI accuracy endpoint. This amendment was
made before any transfer (B0/B1/conditioned) comparison was run.

---

## 1. Why this exists

The Phase-2 honest scoring puts the binding constraint on
**criterion 3 (algorithmic innovation)**: the GQE→QSCI→32q pipeline is the providers' own prior
art (Kemmoku/Gao), and MATGEN-Q's distinguishing claim — a **chemistry-conditioned generator that
transfers across molecules** — is *described but not demonstrated*. This experiment demonstrates it,
or falsifies it. Either outcome is reported honestly.

In the current code (`src/gqe_scaling.py`) the GPT-QE generator has **no molecular input at all**:
`GPTQE.forward()` consumes only token + position embeddings, and `build_pool()` rebuilds the operator
vocabulary per molecule. So "demonstrate the encoder" means two things, in order: (a) build a
conditioning pathway from a molecular representation into the generator; (b) show that conditioning
yields *transfer* — generalization to a molecule held out of training — that beats the obvious
baselines. (a) without (b) is not a novelty result.

## 2. Hypothesis (falsifiable)

> A GPT-QE generator conditioned on a cheap, physically-motivated molecular descriptor (active-space
> MP2 amplitudes + orbital-energy features) and trained jointly across a family of related molecules
> reaches chemical accuracy on a **held-out** molecule in **fewer circuit evaluations** than (B0)
> training from scratch and (B1) a non-conditioned warm-start from the same joint training.

If conditioning does **not** beat both baselines, the encoder is not novel-useful at this scale and
we say so — we do not ship the claim.

## 3. Demonstration system

**Group-14 monoxides: CO, SiO, GeO, SnO**, active space **CAS(6,6) → 12 qubits** (sandbox), built by
the validated `materials_ham.cas_to_qubit` path (def2-SVP; ECP on Sn). Verified (probe, 2026-06):
all four converge; the qubit ground state matches CASCI to ~1e-10 mHa; **all four share an identical
763-term Pauli structure and an identical UCC operator pool** — the action space is isomorphic, so a
single generator's tokens mean the same excitation for every molecule. SnO is the EUV target; the
lighter homologs are cheap training data sharing the same valence (σ,π / σ*,π*) manifold.

- **Train:** {CO, SiO, GeO}, each at bond lengths R ∈ {0.95, 1.00, 1.05} × R_eq → 9 Hamiltonians.
  Bond-length augmentation turns 3 molecules into 9 smoothly-varying training points so the
  descriptor→policy map is learnable (3 points alone is too few) and sets up the optional geometry
  GNN front-end later.
- **Held-out test:** **SnO at R_eq** (primary), plus SnO at R ∈ {0.95, 1.05}×R_eq (extrapolation check).
  SnO is in **no** training point.

**Scale honesty.** 12q is the in-sandbox demonstrated scale (it is where `gqe_qsci.py`'s fast
sparse-matvec energy path is valid; `get_sparse_operator` OOMs at 16q on CPU). The code is
parameterized by `(ncas, nelec)`; CAS(8,8)→16q and CAS(10,10)→20q are a one-line config change for
the Phase-3 GPUs. We report 12q as demonstrated and 16–20q as the GPU target — the same floor/ceiling
honesty as Phase 2 (integrated loop shown at 12q, larger as validated proxy).

## 4. Conditioning signal (the "encoder")

Primary encoder = **active-space MP2 features**, not an equivariant GNN. Rationale: the conditioning
target is "which excitations matter for *this* molecule," and MP2 doubles amplitudes
`t_ijab = <ij||ab>/(ε_i+ε_j−ε_a−ε_b)` live on exactly the excitation indices the pool is built from,
are cheap, and — because the active space is the same size and orbitals are energy-ordered — align
index-for-index across the family. The descriptor per (molecule, R):

- flattened active-space MP2 doubles-amplitude tensor (aligned across molecules),
- active orbital energies referenced to the HOMO (scale-free gaps),
- a few intensive scalars (HOMO–LUMO gap, MP2 correlation energy, metal atomic number, bond length).

All features are standardized (per-dimension z-score over the training set; the same transform is
applied to the held-out molecule — fit on train only, no leakage). A small MLP maps the descriptor to
a conditioning vector injected into the generator via **FiLM** (feature-wise affine modulation of the
token+position embeddings). The equivariant GNN (geometry → descriptor) is an **optional** later
front-end if we want generalization across geometries beyond what MP2 features already give; it is
explicitly out of scope for this first demonstration.

## 5. Baselines (the bar conditioning must clear)

- **B0 — from scratch.** Fresh generator trained only on the held-out molecule. No transfer.
- **B1 — naive warm-start.** Generator pre-trained jointly on {CO,SiO,GeO}×R **without** conditioning,
  then evaluated / fine-tuned on the held-out molecule. Tests "does conditioning add anything over
  simply reusing weights?"
- **Conditioned (ours).** Same joint pre-training **with** the MP2 conditioning, evaluated on the
  held-out molecule by feeding its descriptor: **zero-shot** (no fine-tuning) and **few-shot**
  (a small fine-tune budget).

All three use the identical generator capacity, operator pool, optimizer, and evaluation budget.
The GQE objective (sign/scale of the logit-sum↔energy regression) is fixed and verified to *minimize*
on a single molecule before any transfer numbers are taken (the existing repo code's sign is checked,
not assumed).

## 6. Metrics (revised per §0; all traceable to a JSON in `results/encoder/`)

The encoder conditions the **generator**, so transfer is measured on generator quality (where the
learning lives), with QSCI providing the chemical-accuracy endpoint.

1. **Zero-shot transfer (primary, isolates the encoder)** — after joint pre-training on the light
   monoxides, feed held-out SnO's descriptor and generate circuits with **no SnO training**. Compare
   mean and best raw GQE energy (mHa to FCI) of conditioned vs. B1 (warm-start, no descriptor) vs.
   random. Conditioned − B1 is the pure conditioning effect.
2. **Few-shot transfer curve** — raw GQE best/mean (mHa to FCI) vs. number of SnO circuit evaluations,
   for B0 / B1 / conditioned. Report evaluations to reach a fixed target (the raw-energy level B0
   attains at full budget) per method.
3. **Chemical-accuracy endpoint** — best conditioned circuits → QSCI (sample determinants →
   diagonalize, as in `gqe_qsci.py`) → energy in mHa to FCI on SnO.

## 7. Pre-registered success criteria (revised per §0)

- **PASS (claimable):** on held-out SnO, conditioned beats B1 (warm-start) on **zero-shot** mean/best
  raw energy, **and** reaches the fixed raw-energy target in **fewer** SnO evaluations than both B0
  and B1, with QSCI delivering chemical accuracy on the conditioned circuits.
- **WEAK (report, don't headline):** conditioned beats B0 but is statistically tied with B1 — transfer
  helps but MP2 conditioning adds little over plain weight reuse. We say so and propose the richer
  (token-level MP2 prior / GNN) variant.
- **FAIL (do not claim):** conditioned does not beat B0. Report the negative result and likely cause
  (too few molecules, descriptor uninformative, scale too small for headroom).

Single-seed results are reported with that caveat; multi-seed error bars are added if compute allows.

The criteria are fixed **before** the run. Whatever the outcome, it goes in the results JSON and is
reported to the team verbatim.

## 8. Threats to validity (stated up front)

- **n_molecules is small.** 3 training molecules (×3 bond lengths) is a thin basis for a
  descriptor→policy map; a positive result at 12q is suggestive, not conclusive, and must be repeated
  at 16–20q with more of the family (add CO₂/SiO₂/GeO₂/SnO₂, Hf/Zr oxides) on GPUs.
- **Headroom.** Transfer benefit is only visible where from-scratch has *not* trivially converged; we
  therefore measure at a fixed, deliberately small evaluation budget and report the full curve, not a
  single converged endpoint.
- **Leakage.** Standardization and any model selection use the training molecules only; SnO touches
  nothing until evaluation.
- **GQE sign/scale.** Verified to actually minimize before transfer numbers are taken.

## 9. Repository layout

```
src/encoder/
  molecules.py          # CAS(n,n) Hamiltonian + descriptor registry (reuses materials_ham path); disk cache
  descriptors.py        # MP2 amplitude + orbital-energy features; train-only standardization
  cond_gptqe.py         # GPTQE + FiLM conditioning (reuses gqe_scaling.GPTQE structure)
  qsci_score.py         # bit-packed QSCI energy engine (reuses sno_demo engine) for final integrated number
  train_conditional.py  # joint conditioned pre-training over {CO,SiO,GeO}×R  -> checkpoint
  transfer_eval.py      # held-out SnO: B0 vs B1 vs conditioned -> transfer curves + integrated QSCI
results/encoder/        # one JSON per run + the transfer-curve figure (every number traceable)
docs/encoder_design.md  # this file
```
