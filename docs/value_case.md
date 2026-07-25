# The value case — not paying for a confidently-wrong classical prediction

*One-page framework. The **mechanism** below is measured and committed in this work; the **dollar figures
are illustrative placeholders** you replace with your own pipeline's numbers. This is the shape of the value,
not a claimed Mitsubishi ROI.*

---

## The asset, in one sentence
**A quantum-accurate, self-certifying check that catches when the industry's gold-standard classical method
is *confidently wrong* on strongly-correlated materials — before that wrong number commits a multi-month
synthesis campaign to a dead end.**

## The mechanism (measured here, not assumed)
In EUV-photoresist and transition-metal-oxide chemistry the bonds are **strongly correlated (multireference)**.
There, the gold standard **CCSD(T) does not merely lose precision — it collapses *non-variationally***: it
returns an energy *below* the exact answer, confidently, **with no internal signal that it is wrong**.

- **Real oxide (CrO bond stretch, CAS(10,10)=20q):** in-active-space CCSD(T) error grows to **~162 mHa and
  goes non-convergent** as multireference character turns on, while the determinant-subspace method
  (selected-CI / QSCI) stays a **rigorous variational bound within chemical accuracy (≤2.8 mHa) throughout**
  (`cro_dissociation.py`, in the 26/26 reproduce suite).
- **Real EUV motif (Sn₂O₂ bridge cleavage):** in-active-space CCSD(T) error grows **0.14 → 5.49 mHa (~40×)**,
  crossing chemical accuracy, while the identical selected-CI/QSCI stays **≤0.48 mHa everywhere**
  (`sn2o2_dissociation.py`).
- **Textbook illustration (H₁₀ dissociation):** CCSD(T) sits **217 mHa *below* exact FCI** — an unphysical,
  confidently-wrong number with no error flag (`strong_correlation.py`).

**Why QSCI is the trustworthy check:** it is **variational** (it can only ever be an *upper bound* to the true
energy) and it carries **its own error certificate** — an Epstein–Nesbet PT2 bracket that tightens toward FCI
and tells you how converged you are (`encoder/selci_pt2.py`; equilibrium extrapolation → FCI, R²=0.999). So it
**never returns a confidently-wrong answer**: it is either certified-converged, or it tells you it is not. We
have executed this pipeline on the real chemistry up to **40 qubits on GPU/QPU hardware**.

## The three factors
| Factor | Meaning | Grounding |
|---|---|---|
| **C** — cost of a false lead | fully-loaded cost of carrying one candidate from computation into **multi-month synthesis + lithographic evaluation** | *illustrative* — plug your own; EUV-resist candidate synthesis + test is widely months and high-cost |
| **p** — silent-failure rate | fraction of **multireference** candidates where the classical gold standard is confidently wrong with no warning | *measured mechanism here:* CCSD(T) non-variational collapse (to ~162 mHa on CrO; below FCI on H₁₀); the rate over your library is yours to measure |
| **N** — candidates screened / yr | throughput of the classical filter feeding synthesis | your pipeline's number |

## The arithmetic (plug your own numbers)
> **Waste ≈ N · f_mr · p · C** — where `f_mr` = fraction of screened candidates with multireference character
> (the regime where the classical gold standard silently fails and QSCI is decisive), and the quantum-accurate,
> self-certifying check **intercepts that term** at the pre-synthesis gate.

*Illustrative:* screen `N = 1,000`/yr; `f_mr = 20%` multireference; the classical method is confidently wrong on
`p = 1 in 5` of those; a false lead costs `C = $250k`. Then `1,000 · 0.20 · 0.20 · $250k = $10M/yr` committed to
wrong leads a self-certifying quantum-accurate check on the flagged subset would catch. **Every input is a
placeholder — swap in yours.** Multi-fidelity screening economics independently show up to **3× cost reduction**
from a better filter (Fare et al., *npj Comput. Mater.* 2022).

## Where our method sits in the funnel
```
AI proposes → classical screens → [ multireference candidates: QSCI-accurate, self-certifying check ] → SYNTHESIZE
                                              ↑
                        catch the confidently-wrong classical number
                        BEFORE the months-long synthesis commit
```

## Bottom line
The value is **not a speedup** and **not "our method is always more accurate."** It is **trust**: the classical
gold standard can be confidently wrong on exactly the strongly-correlated chemistry that matters, with no warning;
the quantum-accurate selector is a rigorous, self-certifying bound that never blindsides you and is systematically
improvable to exact. You stop paying for confidently-wrong predictions.

## Honest caveats (non-negotiable)
- **No quantum *advantage* at ≤40q:** classical DMRG can still solve these instances; the value is
  **trust/certifiability, not speed**. The advantage regime is 40q+ strong correlation, which the executed 40q
  run targets.
- **QSCI is not universally more accurate at a fixed small budget:** at *extreme* dissociation on a CPU proxy
  budget its *absolute* error can exceed |CCSD(T) error| (`strong_correlation.py` note). The claim is that it is
  **variational and self-certifying** (never confidently wrong, always improvable), not that it beats CCSD(T)'s
  number everywhere. On the real oxides at equilibrium-to-cleavage it *is* both variational and accurate (≤2.8 mHa).
- **The dollar numbers are illustrative placeholders**, not measured Mitsubishi costs.
- **Not a DFT claim.** An earlier version of this page rested on DFT spin-state errors; those turned out to be
  SCF-/active-space-convergence artifacts and were withdrawn. This value case rests only on the CCSD(T)
  non-variational collapse — a textbook failure mode independent of functional, SCF guess, or active space.
- `f_mr`, `p`, `C`, `N` are your pipeline's to measure; this page supplies the **framework and the mechanism**,
  verifiably, and leaves the economics to your data.
