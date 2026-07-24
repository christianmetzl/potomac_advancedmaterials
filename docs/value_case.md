# The value case — what a wrong candidate costs, and where a quantum-accurate check intercepts it

*One-slide framework. The **mechanism** and the **mis-rank evidence** below are measured in this work; the
**dollar figures are illustrative placeholders** you replace with your own pipeline's numbers. This is the
shape of the value, not a claimed Mitsubishi ROI.*

---

## The mechanism (measured here, not assumed)
DFT's *functional choice* can flip **which candidate you would synthesize**:
- On CrO, six functionals span **1.9 eV** and **B3LYP assigns the wrong ground state** (`cro_spin_gap.py`).
- In a two-candidate decision (**CrO vs NiO**), **B3LYP inverts the ranking** and would advance the **wrong**
  candidate; the multireference (QSCI/CASCI) selector picks CrO, agreeing with CrO's experimental X⁵Π ground
  term (`candidate_decision.py`, `results/candidate_decision.png`).

A quantum-accurate check gives **one consistent answer** exactly where the classical filter is unreliable.

## The three factors
| Factor | Meaning | Grounding |
|---|---|---|
| **C** — cost of a false lead | fully-loaded cost of carrying one candidate from computation into **multi-month synthesis + lithographic evaluation** | *illustrative* — plug your own; EUV-resist candidate synthesis + test is widely months and high-cost |
| **p** — DFT mis-rank rate | fraction of **multireference** candidates where a common functional flips the ground state / ranking | *measured here:* B3LYP gave a wrong ground-state sign on CrO **and** inverted the CrO↔NiO ranking; DFT spin-state errors of 0.3–1+ eV are well documented (small measured sample — see caveats) |
| **N** — candidates screened / yr | throughput of the DFT filter feeding synthesis | your pipeline's number |

## The arithmetic (plug your own numbers)
Expected avoidable waste per year from mis-ranked **multireference** candidates:

> **Waste ≈ N · f_mr · p · C**  — where `f_mr` = fraction of screened candidates with multireference
> character (the regime where DFT is unreliable and QSCI is decisive), and the quantum-accurate check
> **intercepts that term** at the pre-synthesis gate.

*Illustrative:* screen `N = 1,000` candidates/yr; `f_mr = 20%` are multireference; a common functional
mis-ranks `p = 1 in 5` of those; a false lead costs `C = $250k` (synthesis + litho eval). Then
`1,000 · 0.20 · 0.20 · $250k = $10M/yr` of spend committed to wrong leads that a quantum-accurate check on
the flagged multireference subset would catch. **Every input here is a placeholder — swap in yours.**
Multi-fidelity screening economics independently show up to **3× cost reduction** from a better filter
(Fare et al., *npj Comput. Mater.* 2022).

## Where our method sits in the funnel
```
AI proposes → DFT filters → [ multireference candidates: QSCI-accurate check ] → Bayesian selects → SYNTHESIZE
                                         ↑
                        the interception point: catch the flipped ranking
                        BEFORE the months-long synthesis commit
```

## Bottom line
The value is **not a speedup** — at ≤40 qubits classical methods still solve these instances. The value is
**not paying for the wrong candidate**: our demonstrated at-scale contribution is exactly this interception —
catching where the classical filter silently mis-ranks a multireference candidate, before the expensive
synthesis decision.

## Honest caveats (non-negotiable)
- The **dollar numbers are illustrative placeholders**, not measured Mitsubishi costs.
- The **measured mis-rank sample is small** (a handful of oxide centers); the robust, committed facts are the
  1.9 eV DFT spread, the B3LYP ground-state **sign error**, and the **ranking inversion** — not a specific rate.
- Fixed modest active space (CAS(10,10)/def2-SVP): the claim is the **ranking/sign** (which candidate), not a
  benchmark-quality gap magnitude.
- `f_mr`, `p`, `C`, `N` are your pipeline's to measure; this page supplies the **framework and the mechanism**,
  verifiably, and leaves the economics to your data.
