# The value case — what a wrong candidate costs, and where a quantum-accurate check intercepts it

*One-slide framework. The **mechanism** and the **mis-rank evidence** below are measured in this work; the
**dollar figures are illustrative placeholders** you replace with your own pipeline's numbers. This is the
shape of the value, not a claimed Mitsubishi ROI.*

---

## The mechanism (measured here, not assumed)
DFT's *functional choice* can flip **the spin state you would carry into synthesis**:
- On CrO, six functionals span **1.9 eV** and **B3LYP assigns the wrong ground state** — a triplet, where
  CASCI/QSCI and 5 of the 6 functionals give the **quintet (⁵Π) that matches the experimental X⁵Π term**
  (`cro_spin_gap.py`). This **sign error is robust to active-space size** (holds across CAS(10,10)/12/14;
  `candidate_decision_larger_cas.py`) — it is the defensible decision-value result.

*What we do **not** claim:* a two-candidate CrO-vs-NiO *ranking*. We tested it and it is **not robust** — the
multireference ranking inverts between CAS(10,10) and CAS(12,12)/(14,14), so we withdrew it (see the README
honesty note). The value case below rests only on the CAS-robust **single-molecule sign** error.

A quantum-accurate check gives the **right spin state** exactly where the classical filter is unreliable.

## The three factors
| Factor | Meaning | Grounding |
|---|---|---|
| **C** — cost of a false lead | fully-loaded cost of carrying one candidate from computation into **multi-month synthesis + lithographic evaluation** | *illustrative* — plug your own; EUV-resist candidate synthesis + test is widely months and high-cost |
| **p** — DFT mis-assignment rate | fraction of **multireference** candidates where a common functional gets the ground state (spin state) wrong | *measured here:* B3LYP gave a wrong ground-state **sign** on CrO (robust to CAS size); DFT spin-state errors of 0.3–1+ eV are well documented (small measured sample — see caveats) |
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
                        the interception point: catch the wrong spin state
                        BEFORE the months-long synthesis commit
```

## Bottom line
The value is **not a speedup** — at ≤40 qubits classical methods still solve these instances. The value is
**not carrying a wrong answer into synthesis**: our demonstrated contribution is exactly this interception —
catching where the classical filter silently gets a multireference candidate's spin state wrong, before the
expensive synthesis decision.

## Honest caveats (non-negotiable)
- The **dollar numbers are illustrative placeholders**, not measured Mitsubishi costs.
- The **measured sample is small** (a handful of oxide centers); the robust, committed facts are the
  1.9 eV DFT spread and the B3LYP ground-state **sign error on CrO** (robust across CAS(10–14)) — not a specific rate.
- The two-candidate **CrO-vs-NiO ranking was tested and withdrawn** (not robust to active-space size); the
  claim is the **single-molecule sign** (which spin state), not a candidate ranking or a benchmark gap magnitude.
- `f_mr`, `p`, `C`, `N` are your pipeline's to measure; this page supplies the **framework and the mechanism**,
  verifiably, and leaves the economics to your data.
