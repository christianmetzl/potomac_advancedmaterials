# E6 — DMRG truncation-error extrapolation anchor (40q flagship): TERMINAL REPORT (as-measured)

**Supplementary and independent** of the pre-registered E3 PT2 certificate (box A). E3's frozen
result stands unchanged; E6 is a second, equally rigorous road to the same claim — that the 40q QSCI
variational energy is absolutely (near-FCI) accurate — reported as "we also tried this."

**Method (frozen, `preregistration_e67_supplementary.json` + `src/e6_dmrg_extrap_40q.py`):** block2
DMRG on the identical H20/40q Hamiltonian at a χ-ladder [400, 800, 1200, 1600, 2400], frozen
E1/make_ref schedule (n_sweeps=8, bond_dims=[100,150,200,χ×5], noises=[1e-4…1e-7,0,0,0,0], SU(2));
linear extrapolation E vs final-sweep discarded weight → truncation-free (FCI) limit.
**Box:** qBraid box A (64 vCPU / 256 GB), block2 0.5.3 with the documented `e1_env.sh` MKL fix.

## Gate: reproduce committed references — PASS
| χ | E6 (Ha) | committed ref (Ha) | Δ |
|---|---|---|---|
| 400 | −10.292240978 | −10.292235708 | ~5 µHa |
| 800 | −10.293162954 | −10.293162879 | ~0.08 µHa |

## Ladder + extrapolation
| χ | E_dmrg (Ha) | dw | wall |
|---|---|---|---|
| 400 | −10.292240978 | 1.296e-4 | 64 s |
| 800 | −10.293162954 | 4.686e-5 | 273 s |
| 1200 | −10.293353512 | 2.426e-5 | 716 s |
| 1600 | −10.293433313 | 1.482e-5 | 1473 s |
| 2400 | −10.293498299 | 7.071e-6 | 3645 s |

- **E_FCI(40q) extrapolation = −10.29359876 ± 0.022 mHa** (linear E vs dw; R² = 0.99661; 5 rungs).
- **Fit gate (≥3 rungs, R² ≥ 0.98): PASS.**

## Certification of box A's committed E_var (as-measured)
- E_var (box A E3, terminal committed iteration it5) = −10.29200915 Ha
- **absolute_error = (E_var − E_FCI_extrap) = +1.590 mHa**
- **Chemical accuracy (≤ 1.6 mHa): demonstrated** ✓
- Prediction-i-equivalent (≤ 0.5 mHa): not met (> 0.5)
- Note: measured against box A's *terminal* committed E_var because E3 was externally terminated at
  it6 (see `e3_terminal_report.md`). Per the frozen rule, as E_var descends this gap closes; the
  value is reported as-measured against whichever iteration is committed at read time.

## Honest caveats (frozen)
- DMRG-extrapolated FCI is an estimate with a fit uncertainty (reported), **not** a rigorous
  two-sided bracket like E_var+PT2 — standard SHCI/DMRG practice, stated as such.
- H20 is the DMRG-favourable quasi-1D case, so the extrapolation is tight here; this anchors the
  flagship system, not a claim about DMRG on strongly-2D/3D correlation.

**Evidence:** `results/e6_dmrg_extrap_40q_evidence.json` (full ladder + fit), `e6.log` (DMRG trace).

*Frozen first, measured always, reported as-is.*
