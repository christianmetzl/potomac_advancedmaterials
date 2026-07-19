# E1 chi-escalation counter-audit — execution summary

Prereg: `results/preregistration_v2.json` entry **E1** (committed 4489cca, before execution).
Executed 2026-07-19, personal qBraid `8vCPU_25GB` CPU box, branch `claude/wonderful-bohr-rir81t`.
Interpretation frozen before each run; outcomes reported as-is; nothing tuned to results.

## Environment / workaround (documented for provenance)
- `qsci_lib.py` imports `cudaq` at module top → blocks on this CPU box. CUDA-Q **not** installed
  (per instruction). Integrals rebuilt by a standalone **pyscf replica** of `cas_problem` /
  `hchain_problem` (`src/e1_chi800_counteraudit.py`) — identical classical path (same ROHF/RHF,
  `mc.get_h1eff()/get_h2eff()`, `ao2mo.restore(1,..)`); `make_ref` never needs the JW qubit operator.
- block2 0.5.3 bundled MKL was broken (missing `libmkl_def.so.1`; reduced hashed core/thread).
  Repaired with the self-consistent MKL 2021.4.0 at `~/.local/lib` + `LD_PRELOAD` — see `src/e1_env.sh`.
  Numerically inert; confirmed by the chi=400 reproductions below.

## Chain of custody (standalone integral path validated)
| system | replicated chi=400 | committed chi=400 | Δ (mHa) |
|---|---|---|---|
| CrO CAS(18,19) | −1118.0455968864 | −1118.0456262252 | +0.029 |
| H20 40q | −10.2922357079 | −10.2921941778 | −0.042 |

Both within the frozen 0.2 mHa DMRG-noise tolerance → the standalone path faithfully reproduces
the committed references. (`cro_cas19_dmrg_chi400_VALIDATE.json`, `h20_40q_dmrg_chi400_VALIDATE.json`.)

## Results (block2 SU(2), 8-sweep frozen schedule `[100,150,200,χ×5]`, thrds 1e-8)
| run | E_DMRG (Ha) | Δ vs chi400 (mHa) | wall_s | peak RSS (GB) |
|---|---|---|---|---|
| CrO chi=800 | −1118.0483469495 | −2.721 | 350.3 | 8.02 |
| CrO chi=1200 | −1118.0490535503 | −3.427 | 929.5 | 17.96 |
| H20 chi=800 | −10.2931628791 | −0.969 | 375.7 | 9.26 |

Resource watch: no OOM (ceiling 25 GB; peak 17.96 GB at CrO chi=1200), no ENOSPC
(scratch ≤ ~1.9 GB in `~/dmrg_scratch`; 14 GB floor never approached). All runs flagged
"not converged to 1e-8" — identical to the committed chi=400 runs on this 8-sweep schedule;
per-sweep descent recorded in each evidence JSON, final-sweep Δ inside the 0.2 mHa band.

## Frozen case verdicts (0.2 mHa tolerance)
- **CrO / 38q → CASE A CONFIRMED.** B2's committed terminal `results/gpu_run4_cas19_evidence.json`
  (E_QSCI = −1118.0494099, 529392 dets, iter 14/40, energy converged for verdict) landed on origin
  (commit 943a985) and was pulled in before evaluation — so the comparison is settled, not pending.
  E_DMRG(χ=800) is **+1.063 mHa** and E_DMRG(χ=1200) **+0.356 mHa** *above* the QSCI terminal: both
  raised-χ references stay above QSCI, descending toward it *from above* (gap 1.06 → 0.36 mHa as χ
  grows 800→1200). The truncation-error mechanism is **confirmed with a tighter reference**; the
  reference-correction claim (QSCI landed below the χ=400 DMRG reference due to bond-dimension
  truncation) is **upheld and quantified**. χ=1200 rule was frozen before its run: same case A/B
  logic + 0.2 mHa tolerance, χ=1200 substituted. Convergence caveat: both sides carry sub-mHa
  schedule slack; the χ=800 +1.06 mHa gap is far outside any plausible combined slack, and the sign
  is unchanged even against the QSCI extrapolated asymptote (~−1118.04945).
- **H20 / 40q → case B by the letter, VACUOUS consequence.** E_DMRG(χ=800) is 2.19 mHa below the
  committed QSCI terminal (−10.290969, 7fec4cf). No claim to withdraw: at H20 QSCI was *above* its
  reference (+1.226 mHa, P1 PASS) — the "QSCI-closer-to-exact" claim exists only at CrO/38q. Material
  consequence recorded (`consequence_for_committed_claims`): flagship absolute error ≥2.19 mHa (above
  chem acc); P1 PASS unchanged; χ=400 ref carries ~0.97 mHa slack; absolute cert = frozen E3. E1's
  motivation over-generalized ("references", plural); correct scope is CrO only.

## Cost (personally funded)
Meter (`qbraid compute usage`) counts **weighted vCPU-hours = wall × vCPU**, billed on uptime not
compute: 8-vCPU box, ~6.75 wall-h session → 54/100 compute-hours used, 46 remaining (session
Credits 0.00 = subscription-covered, credit wallet untouched at ~5008 cr). E1 DMRG compute wall
≈ 0.53 h total (all 5 runs) → ≈4 weighted compute-hours attributable to the runs; the session's
54 is uptime-dominated, not run-dominated.

## Overall
E1 CONFIRMS the reference-truncation claim where it lives (CrO/38q, Case A) and, at H20/40q, the
χ=800 reference confirms its own quality while pinning the 40q flagship's absolute error at ≥2.19
mHa. No frozen threshold moved; no reference swapped; no QSCI re-run. Committed χ=400 references
left byte-for-byte untouched (overwrite guard held throughout).
