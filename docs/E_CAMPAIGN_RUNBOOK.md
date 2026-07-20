# E-campaign runbook — E2 / E3 / E4 STEP 2 / E5 (+ classical ladder)

**Authorized 2026-07-20** (operator sign-off recorded in `preregistration_v2.json`; rule 3 amended in
`docs/credit_budget.md`). Deadline: **Sunday 2026-07-26 11:59 PM EST** — instances must be productive
by ~Jul 22 for integration by Jul 25. Budget: worst case 27k on top of 16,483 spent → 43.5k < 65k cap.

## Standing rules
- Every run executes its **frozen protocol verbatim** (`preregistration_v2.json`); E5 uses the
  **re-frozen χ=1200 judge**. No parameter improvised on the box.
- Every runner is **CPU-smoke-tested green in the session container BEFORE any instance spins up**
  — instance minutes are production only.
- Evidence JSONs flush incrementally; push checkpoints at every milestone (instance death loses
  nothing but the rung in flight — the B2 lesson).
- `python src/verify_credits.py --live` before spin-up, at each handover, and at shutdown; append
  wallet snapshots to the ledger.
- Abort gate for E5: if not converged by **Jul 25 06:00 UTC**, stop, commit logs, report as
  non-converged per its frozen reporting rule.

## Key fact: no GPU is required
All four runs are CPU-bound QSCI growth / PT2 / DMRG: E2 consumes the **committed** device seed
(`results/p3_sample_dets.json` — frozen rule explicitly allows reuse; sampling cost 0); E3/E5 seed
from MP2 and E4 from HF (classical). **Choose instances by RAM/disk, not GPU.** If qBraid's catalog
has large-RAM CPU instances, they strictly dominate on cost; otherwise fall back to the known-good
A100-sxm class (4.15 cr/min hosts ran B2 fine). The frozen cost estimates assumed GPU-class rates,
so CPU instances only improve the projection.

| Run | Instance floor | Disk | Est. wall |
|---|---|---|---|
| E3 | **≥200 GB RAM (frozen spec)** | ≥100 GB free (state file) | ~20–30 h (kcap 2M + PT2 each iter) |
| E4 STEP 2 | ≥64 GB RAM (B2-class) | ~50 GB | ~18–24 h (kcap 500k, mirrors B2) |
| E2 | ≥128 GB RAM | ~50 GB | ~10–16 h (kcap 450k, matched to committed run) |
| E5 | ≥200 GB RAM | ≥150 GB | ~24–48 h (kcap 3M; the schedule risk) |

## Sequence (two instances, A = big-RAM, B = B2-class)
- **Jul 21:** spin A + B after smoke tests are green.
  A: **E3** start. B: **E4 STEP 2** start.
  (E5 χ=1200 judge reference: built pre-run on the session container if RAM allowed — check
  `results/h22_44q_dmrg_chi1200.json`; if it recorded resource-DNF, build it on A or B **first**,
  ~1–2 h, still committed before any E5 growth.)
- **Jul 22:** B finishes E4 → B starts **E5** (largest box available; if B is too small and A is
  free first, swap). A finishes E3 → A runs **E2**.
- **Jul 23–24:** E5 runs; everything else integrates into the paper as it lands.
- **Jul 25:** E5 terminal or abort-gate; final integration, PDF rebuild, re-zip.
- Shutdown discipline: evidence pushed **before** every instance stop (B2 rule).

## Runners (all in `src/`, smoke-test target = container CPU at toy scale)
| Run | Runner | Status |
|---|---|---|
| E2 | `e2_device_seed_40q.py` — growth from `p3_sample_dets.json`, 150k/iter, kcap 450k; judge: \|E − (−10.290969)\| ≤ 0.5 mHa at matched det count | to write + smoke |
| E3 | `e3_certificate_40q.py` — MP2-seeded, 150k/iter, kcap 2M, chunked EN-PT2 every iteration (committed `selci_pt2` formula); predictions i–iii judged independently | to write + smoke |
| E4 | `e4_sn2o2_38q.py` — HF-seeded, 40k/iter, kcap 500k, integrals via the CrO-validated `sn2o2_integrals` path; judge: committed `sn2o2_cas19_dmrg_reference.json` (±1.6 mHa, ordering disclosure mirrors P4) | to write + smoke |
| E5 | `e5_h22_44q.py` — MP2-seeded, 150k/iter, kcap 3M; judge: re-frozen χ=1200 reference; χ=800 gap reported as ladder diagnostic | to write + smoke |

## Zero-credit work already queued on the session container
1. Stretch sweep (running) — Phase 2 truncation-vs-correlation promise.
2. `dmrg_ladder_ext.py` (auto-starts when the sweep frees the cores): H22 χ400/800/1200 E5
   references + classical ladder H24–H32 (48–64q, χ400/800 + CCSD(T) cross-anchor). **Classical
   headroom evidence only — no QSCI claim; never quote it as a quantum-pipeline result.**

*Same discipline as the whole campaign: frozen first, measured always, reported as-is.*
