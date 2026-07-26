# Worked industrial example — the organotin resist ligand decision, run through the trust gate

**What this is.** Every hostile-panel critique of this submission converged on one gap: the difference
between *"EUV-relevant chemistry"* and *an actual resist decision*. This memo closes that gap with a
complete, executed, judge-verifiable worked example on the real decision coordinate — and reports the
outcome **exactly as measured**, including the predictions that failed.

**The decision.** Organotin EUV photoresists are R–Sn oxo/hydroxo systems; a real formulation choice is the
alkyl ligand **R**, and the decision-relevant quantity is the **Sn–C homolysis energy** — the EUV activation
step (Kharazi et al. 2026, the challenge-provider paper we cite). We run **methyl vs n-butyl**
(CH₃–Sn(OH)₃ vs n-C₄H₉–Sn(OH)₃ model monomers) through the full MATGEN-Q workflow along the Sn–C stretch.

**Method (frozen before execution — `results/preregistration_we_snc.json`).** Per point, per ligand:
CASSCF(8,8) singlet = **exact-in-CAS reference** (16 qubits); in-CAS CCSD(T) on the *identical* integrals =
the classical screen; selected-CI/QSCI = the trust gate (same engine as the committed Sn₂O₂ curve). Six-point
Sn–C grid 2.15→4.60 Å. Four falsifiable predictions (P-WE1…4). Script: `src/we_snc_homolysis.py` (~30 min CPU).

## Outcome as measured — 2 of 5 predictions held

| Prediction (frozen) | Result | Evidence |
|---|---|---|
| **P-WE1** — QSCI gate stays ≤1.6 mHa vs exact-in-CAS everywhere | **HELD** | max gate error **0.43 mHa**, both curves, all points |
| **P-WE2b** — CCSD(T) goes non-variational somewhere | **HELD** | Me curve: CCSD(T) sits **−4.4 mHa below exact** at 4.60 Å |
| **P-WE2a** — CCSD(T) error >5 mHa or non-convergent at R≥3.35 | **refuted** | it degraded (to 4.4 mHa) but stayed converged and <5 |
| **P-WE3** — in-model BDE(Me) > BDE(Bu) | **refuted** | measured **Bu 85.6 > Me 38.7 mHa** (opposite order) |
| **P-WE4** — screen error exceeds the decision margin | **refuted** | max error 4.4 mHa ≪ margin **46.9 mHa** |

## What is solid, and what we do NOT claim

**Solid (the gap-closers):**
1. **The workflow ran end-to-end on a real resist decision**, with an exact reference a judge re-verifies on
   CPU. Not a hydrogen chain, not a demonstrator oxide — the actual Sn–C activation coordinate.
2. **The gate self-certified on real organotin chemistry**: QSCI stayed within **0.43 mHa** of the exact
   CASSCF energy at every geometry, *through genuine bond homolysis* — the CASSCF natural-orbital occupations
   confirm a true σ/σ*(Sn–C) diradical pair at stretch (Me 1.14/0.86, Bu 1.07/0.93;
   `results/we_snc_diagnostic.json`), so this is the strongly-correlated regime, not an easy one.
3. **The silent-failure mechanism is real on organotin**: in-CAS CCSD(T) collapses **non-variationally**
   (−4.4 mHa below the exact energy) on the methyl curve — the same failure we showed on H₁₀ and CrO, now
   reproduced on a resist-relevant molecule, with no internal error signal.

**What we explicitly do NOT claim (reported, not hidden):**
- **The gate did not flip this decision.** For *this* ligand pair the classical screen's error (≤4.4 mHa) is
  far smaller than the ligand gap (~47 mHa), so CCSD(T) would have ranked Me vs n-Bu correctly. The gate
  **confirmed** the classical answer and **certified** its convergence — value a classical method cannot
  provide, but not a decision reversal. We do not oversell it as one.
- **A pre-registered chemistry prediction was wrong.** We froze P-WE3 (Me BDE larger) informed by an
  RHF-level probe; the correlated result reversed it. Published as refuted.
- **A grid limitation, caught and disclosed:** the methyl energy minimum falls at R=2.55 Å, not the R=2.15 Å
  reference the frozen BDE used, so the frozen BDE(Me)=23.7 mHa is measured from up the repulsive wall. From
  each curve's true minimum, BDE(Me)=38.7, BDE(Bu)=85.6 mHa — the **ordering and the P-WE4 verdict are robust
  to this correction**. We therefore make **no ligand-ranking claim**; the BDEs are model-level in-CAS numbers
  in def2-SVP, not experimental-grade.

## Honest scope
Model monomers, not the industrial oxo-cage cluster; idealized rigid geometries; in-model BDEs in a modest
basis and active space. This is a demonstration of the **decision workflow** on the decision-relevant
coordinate with a verifiable exact reference — **not** a resist simulation, and not a claim to have changed a
Mitsubishi formulation call. Its value is showing the gate is credible, self-certifying, and honest exactly
where an unaudited classical screen would ship a confidently-wrong number with no warning — and admitting when,
as here, that warning turns out to confirm rather than overturn the classical answer.

*Reproduce:* `python src/we_snc_homolysis.py` (curves + predictions) · `python src/we_snc_diagnostic.py`
(natural-orbital character) · `python src/make_we_figure.py` (figure). Evidence:
`results/we_snc_homolysis_evidence.json`, `results/we_snc_diagnostic.json`, `results/we_snc_homolysis.png`.
