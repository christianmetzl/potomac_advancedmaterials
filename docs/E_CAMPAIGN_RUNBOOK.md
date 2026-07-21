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
  wallet snapshots to the ledger. **Attribution duty (since the 2026-07-21 second-project draw):**
  at each instance shutdown, read that instance's settled cost from the qBraid console billing and
  append a line to `credit_ledger.json` → `attributed_spend_cr.e_campaign_instances`
  (`{"instance": ..., "cr": ..., "utc": ..., "run": "E3|E4|E2|E5"}`) — that list, not the pool
  balance, is what the 65k cap governs. Watch the verifier's pool-RUNWAY line at every handover.
- Abort gate for E5: if not converged by **Jul 25 06:00 UTC**, stop, commit logs, report as
  non-converged per its frozen reporting rule.

## Key fact: no GPU is required
All four runs are CPU-bound QSCI growth / PT2 / DMRG: E2 consumes the **committed** device seed
(`results/p3_sample_dets.json` — frozen rule explicitly allows reuse; sampling cost 0); E3/E5 seed
from MP2 and E4 from HF (classical). **Choose instances by RAM/disk, not GPU.** If qBraid's catalog
has large-RAM CPU instances, they strictly dominate on cost; otherwise fall back to the known-good
A100-sxm class (4.15 cr/min hosts ran B2 fine). The frozen cost estimates assumed GPU-class rates,
so CPU instances only improve the projection.

**Instance selection (from the live On-Demand catalog, 2026-07-21):**
| Run | LAUNCH THIS | Rate | Est. wall | Est. cost (cr) |
|---|---|---|---|---|
| E3 | **CPU · 64 vCPU / 256 GB** (meets the frozen ≥200 GB spec) | 6.40/min | ~20–30 h | 7.7–11.5k |
| E4 STEP 2 | **CPU · 32 vCPU / 128 GB** | 3.20/min | ~18–24 h | 3.5–4.6k |
| E2 | same 32/128 box, after E4 | 3.20/min | ~10–16 h | 1.9–3.1k |
| E5 | same 64/256 box, after E3 (upgrade to NanoAcademic Medium 96/384 @9.60 only if the E3 state-file footprint shows 256 GB is tight — decision at handover) | 6.40/min | ~24–48 h | 9.2–18.4k |

**Rate-based re-projection: 22.3–37.6k total → worst case 16,483 + 37.6k = 54.1k < 65k cap ✓**
(tighter than the original 27k worst case — the E5 tail is the driver; its Jul 25 06:00 UTC abort
gate and `verify_credits.py` remain the guards.)

**DISK REALITY (measured 2026-07-21): the catalog CPU boxes expose ~20 GB free on a 49 GB root, no
scratch volume.** State-file checkpointing (frozen E3 spec wanted ≥100 GB) is therefore DISABLED on
these boxes — a disclosed operational deviation (recorded in each runner header/evidence; the same
ceiling forced B1's early stop). Consequences: crash = restart from seed; per-iteration evidence
traces (tiny, flushed every iteration, checkpoint-committed) are the durable record; all runner
checkpoint flushes are disk-full-immune. Launch E2/E4/E5 with `STATE_FILE=` (empty) as shown in
BOX_SETUP; E3 v2 needs no state file at all (it observes the engine's live caches through the
sanctioned ckpt callback — smoke-validated at 1e-16 Ha vs the committed PT2 formula). Physics,
engine, schedule, thresholds: unchanged.
**Bonus, zero credits:** the Subscription tier (100 free CPU-hrs, renews in 10 days) **Large
(8 vCPU / 25 GB)** box is exactly right for the full-dependency `reproduce.py` canonical transcript
— the outstanding Phase-1 leftover. Launch it anytime; it draws nothing.

**Per-instance setup (5 min):**
```bash
git clone -b claude/wonderful-bohr-rir81t <repo-url> && cd potomac_advancedmaterials
pip install -r requirements.txt && pip install cudaq     # CPU wheel suffices (validated)
python src/e3_certificate_40q.py --smoke 6                # sanity: must print FORMULA VALIDATED
nohup python src/<runner>.py > run.log 2>&1 &             # production; then commit/push evidence
```

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

## Runners (all in `src/`) — ALL SMOKE-TESTED GREEN in the session container, 2026-07-21
| Run | Runner | Smoke result |
|---|---|---|
| E2 | `e2_device_seed_40q.py` — growth from `p3_sample_dets.json`, 150k/iter, kcap 450k; judge: \|E − (−10.290969)\| ≤ 0.5 mHa at matched det count | ✅ H₆: 0.0000 mHa vs FCI |
| E3 | `e3_certificate_40q.py` — MP2-seeded, 150k/iter, kcap 2M, chunked hash-bucketed EN-PT2 every iteration; predictions i–iii judged independently | ✅ PT2 ≡ committed `selci_pt2.en_pt2` **exactly** (\|Δ\|=0.0 Ha, identical external counts, 6/6 iters); bracket vs FCI converges |
| E4 | `e4_sn2o2_38q.py` — HF-seeded, 40k/iter, kcap 500k, integrals via the reference's exact `sn2o2_integrals` path; judge: committed `sn2o2_cas19_dmrg_reference.json` (±1.6 mHa, ordering disclosure mirrors P4) | ✅ Sn₂O₂ CAS(6,6): 0.0000 mHa vs exact diag |
| E5 | `e5_h22_44q.py` — MP2-seeded, 150k/iter, kcap 3M; judge: re-frozen χ=1200 reference (runner REFUSES to start without the committed file); χ=800/400 gaps reported as ladder diagnostic | ✅ H₆: 0.0000 mHa vs FCI |

Instance setup note: the plain `pip install cudaq` CPU wheel suffices for `qsci_lib` on CPU-only
instances — validated in this container (H₄ qsci_fast: 0.0000 mHa vs FCI). No GPU image required.
Production env knobs per runner: `GROW_ITERS`, `STATE_FILE` (E3 also `PT2_BUCKETS`, default 8).

## Zero-credit work already queued on the session container
1. Stretch sweep (running) — Phase 2 truncation-vs-correlation promise.
2. `dmrg_ladder_ext.py` (auto-starts when the sweep frees the cores): H22 χ400/800/1200 E5
   references + classical ladder H24–H32 (48–64q, χ400/800 + CCSD(T) cross-anchor). **Classical
   headroom evidence only — no QSCI claim; never quote it as a quantum-pipeline result.**

*Same discipline as the whole campaign: frozen first, measured always, reported as-is.*
