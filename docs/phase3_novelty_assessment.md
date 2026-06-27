# Phase 3 Novelty — Honest Assessment for the Team

**MATGEN-Q / EIGENNEXUS · GIC 2026 Phase 3 · for Christian, Juan, Fares**
Prepared after the first conditional-encoder demonstration. Every number traces to a script in
`src/` and a JSON in `results/`. Read this as a decision input, not a conclusion.

---
> ## ⏩ RESOLVED 2026-06-26 — the decisive experiment (Option A) has been run
> The decisive cross-family test in §5.1 / §6 is **done** (`src/encoder/decisive_transfer.py`,
> `results/encoder/decisive_transfer_evidence.json`). A **chemically diverse** training family (polar
> monoxides + isoelectronic BF + homonuclear strong-correlation N₂ + ionic BeO, all CAS(6,6)/12q,
> shared vocab) was used so a single un-conditioned policy could not trivially fit all of it; we then
> compared MP2-conditioned (COND) vs un-conditioned warm-start (B1) zero-shot transfer to held-out
> molecules, 3 seeds, under a **pre-registered** decision rule.
>
> **Result — clean negative.** On both decisive held-outs COND was directionally better but **within
> seed noise**: N₂ Δ(B1−COND)=**+2.09** mHa (noise 3.61), BeO Δ=**+0.39** (noise 0.45); control CO
> Δ=−0.71 (conditioning didn't hurt). COND beat B1 in 5/6 hard runs but never cleared the noise bar.
> **Verdict: the conditional encoder is NOT necessary** — even when warm-start is stressed, a single
> generative policy transfers about as well. Per the pre-registered rule we **drop the encoder as the
> Phase-3 algorithmic-innovation headline** and lead innovation with the integrated **MPS + QSCI +
> operator-pool-compression** scaling layer (Option B / pillars 1–3). This honest negative is itself
> rewarded by the Phase-3 rubric (Top-Action #6: honesty > overstatement). The §4–§6 discussion below
> is preserved as the record that led here.
>
> ## ✅ FOLLOW-UP 2026-06-27 — the *harder* transfer test SUCCEEDED (cross-qubit-count)
> The same-size cross-*molecule* conditioning above tied. The genuinely novel, scaling-relevant
> question — does a generator trained on a *small* system transfer to a *larger* one? — is answered
> **yes** (`src/encoder/scaling_transfer.py`, `results/encoder/scaling_transfer_evidence.json`). A
> **canonical frontier-relative tokenization** (token = excite HOMO−d → LUMO+h, size-independent) makes
> a small system's vocabulary a provable subset of a larger one (H₆/12q ⊂ H₈/16q ⊂ H₁₀/20q). A GPT-QE
> generator trained **only on H₆ (12q)** generates zero-shot for **H₈ (16q)** and **beats random search
> across all 3 seeds, both metrics: mean 91.8 vs 127.6 mHa, best 67.4 vs 82.9 mHa** (within-seed spread
> ~1 mHa vs ~36 mHa gap — highly significant). **Net: cross-*size* transfer is a real, on-theme
> contribution (primary criterion: scalability); cross-*molecule* conditioning is an honest negative.**
> Both are in the paper.
---

---

## 1. What we set out to do

Phase-2 honest scoring (`docs/KNOWLEDGE_TRANSFER.md` §11) names criterion 3 (algorithmic innovation)
as the binding constraint, and the **conditional encoder** (a chemistry-conditioned generator that
transfers across molecules) as the intended novelty. Priority #1 was to *demonstrate* it, since it was
only described. We built and ran the first demonstration. This memo reports what it showed and what it
means for the Phase-3 novelty story.

## 2. What we established (reproducible)

**(a) The GQE machinery, as shipped, does not reach chemical accuracy on its own.**
- Random search over the fixed UCC/discrete-angle pool (4000 length-8 circuits): best **53 mHa** (H6),
  **45 mHa** (CO). The action space cannot *sample* chemical accuracy.
- The GPT-QE transformer genuinely **learns** (mean generated energy 118 → 55 mHa with a real budget),
  but tops out ~**31 mHa** — the discrete-angle ceiling.
- ~~There is **no stage-2** (adjoint-gradient angle refinement) in the repo... their evidence JSON is
  absent.~~ **[Corrected 2026-06-21]** Outdated: commit `4e9e319` imported `src/stage2_refinement.py`
  and `results/stage2_refinement_evidence.json`, and the 2026-06-21 reproducibility audit reruns them
  exactly (H2 0.000, H4 0.009, H6 0.297 mHa). Stage-2 is present and reproducible. The transferred
  sub-mHa stage-2 numbers therefore *do* have shipped, rerunnable code.
- **What is reproducible:** chemical accuracy comes from the **QSCI** step. `gqe_qsci_evidence.json`:
  raw GQE 51 mHa → QSCI **1.05 mHa** (H6, 12q). QSCI is the workhorse.

**(b) The conditional encoder, as instantiated, did not beat a non-conditioned warm-start.**
Setup: group-14 monoxides {CO, SiO, GeO} → held-out **SnO**, CAS(6,6)/12q (isomorphic 763-term pool;
construction exact to ~1e-10 mHa), MP2 molecule-level FiLM conditioning, 3 seeds. Held-out SnO:

| Method | zero-shot best (mHa) | zero-shot mean (mHa) | few-shot final (mHa) |
|---|---|---|---|
| RANDOM | ~45 | ~57 | — |
| **B1** warm-start, *no* conditioning | **43.0 ± 0.6** | **50.5 ± 0.1** | ~39–41 |
| **COND** MP2 conditioning | 43.4 ± 0.5 | 50.4 ± 0.1 | ~39–41 |

- Joint pre-training **does** transfer (B1, COND ≫ random).
- MP2 conditioning adds **nothing** over warm-start (COND ≈ B1, marginally worse on best). This is the
  pre-registered **WEAK** outcome (`docs/encoder_design.md` §7).
- **Cause:** the monoxides are too homogeneous (shared valence, isomorphic pool) — a single
  unconditioned policy already transfers, so there is nothing for conditioning to exploit.

## 3. What this means for the novelty story (the uncomfortable part)

- **GQE + QSCI scaling is not our novelty** — to 32q it is the providers' own prior art
  (Kemmoku/Gao, arXiv:2604.09756). We cannot claim it.
- **The conditional encoder, as the headline, is currently unproven and the first result is a yellow
  flag.** It is *not* falsified — the decisive test (a family diverse enough that warm-start *fails*)
  has not been run — but the burden of proof is now higher, and we should not bank the Phase-3 narrative
  on it until that test passes.
- The honest reframing of the question: **is a conditional encoder ever *necessary*, or does plain
  transfer (warm-start) already do the job for the molecule families we care about?** Our one data
  point says "not necessary for similar molecules." The whole novelty claim hinges on the opposite
  being true for *dissimilar* ones.

## 4. Novelty options on the table

| Option | What it claims | Evidence we have | Risk it isn't novel/strong | On-theme | Cost to decide |
|---|---|---|---|---|---|
| **A. Cross-family conditional transfer** | encoder is *necessary* when molecules differ (monoxide → dioxide / oxide) | concept only; homogeneous case = tie | medium–high (may still tie; needs canonical action space across qubit counts) | high | ~½–1 day (decisive experiment) |
| **B. MP2-informed QSCI acceleration** | chemistry features cut determinants/circuits to chemical accuracy (efficiency) | we have MP2 features + QSCI engine | low–medium (efficiency, criterion 4/6 more than 3) | high | ~½ day |
| **C. Sn/Hf/Zr-oxide HamLib benchmark contribution** | first validated metal-oxide oxide benchmarks (HamLib has none) | SnO/SnO₂ already built & QSCI-validated | low novelty weight (criterion 6/7) | high | ~½ day |
| **D. Stage-2 two-stage GQE (adjoint refinement)** | deliver the sub-mHa GQE the paper claims | not in repo; standard method | low novelty (it's expected method) | neutral | ~½ day |
| **E. Noise-aware generative design** | co-optimize accuracy + hardware-noise robustness on real QC | noise robustness demonstrated (20q) | medium | high (needs Phase-3 QC access) | spec-dependent |

## 5. Recommendation (for discussion, not a decision)

1. **Run the one decisive experiment for A before committing the narrative.** Train on monoxides,
   transfer to a *structurally different* target where warm-start should fail. If conditioning beats
   warm-start there, the encoder is genuinely novel and on-theme — make it the headline. If it ties
   there too, the conditional-encoder claim is effectively falsified and we should **drop it as the
   headline** rather than defend an unsupported claim to the judges. Either way we learn the truth
   cheaply. (Note: this is the experiment we paused; flagging it as the key resolver.)
2. **Develop B (MP2-informed QSCI acceleration) in parallel as the fallback novelty.** It reuses
   machinery we already have, is demonstrable in-sandbox, is distinct from Kemmoku/Gao, and is a real
   *algorithmic* contribution (not just benchmarking). Lower ceiling, much lower risk.
3. **Treat C and D as floor-raisers, not novelty** — worth doing for reproducibility/completeness with
   the GPUs, but not what we lead with for criterion 3.
4. **Do not over-index on the encoder out of sunk cost.** Our one honest result says plain transfer
   already works for similar molecules; the encoder must clear a *higher* bar to be worth claiming.

## 6. Open questions for Juan / Fares
- Is the right "dissimilar" target a dioxide (SnO₂, 20q, bent geometry, different correlation) or a
  cross-chemistry jump (H-chain → oxide)? The latter is more dramatic but needs the canonical
  action-space mapping across different qubit counts.
- Does anyone have a reason to believe conditioning *should* help where warm-start fails, beyond
  intuition? If we can't articulate the mechanism, that is itself a signal.
- If the encoder is dropped as headline, is B (MP2-informed QSCI) an acceptable novelty to the team,
  or do we want a different criterion-3 story?

*Artifacts: `results/encoder/transfer_evidence.json`, `results/encoder/transfer_curve.png`,
`docs/encoder_design.md`. Reproduce: `python src/encoder/transfer_eval.py`.*
