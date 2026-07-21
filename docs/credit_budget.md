# GPU/QPU credit budget — grant-share accounting

> **Self-verifying, not self-reported:** every derived number below is recomputed from the
> machine-readable ledger `results/credit_ledger.json` by `python src/verify_credits.py`, which also
> enforces the 65k cap (exit 2 on breach) and checks that worst-case projections still fit. On any
> machine with qBraid credentials, `--live` pulls the wallet balance from the API and reports drift;
> `--live --append` records a fresh timestamped snapshot into the ledger. This document is prose over
> that ledger — if they disagree, the ledger and verifier win. On a credentialed box,
> `python src/generate_credit_ledger.py --write` regenerates the platform-verified sections straight
> from qBraid records — wallet snapshots from the billing API, per-job lines with qBraid job IDs,
> costs, and tags — so those lines are fetched, never typed. Sections the API cannot know (organizer
> top-ups, the 50% share agreement, personally-funded history) stay explicitly labeled as declared,
> with their records held by the organizers / personal billing.
>
> **Honest limit (stated in the ledger too):** the wallet is pool-level. Attribution to this project
> is exact only while the second project's spend is zero (true at the recorded snapshot); once both
> projects draw, the qBraid per-instance billing history is the arbiter, not the balance.

**Constraint (2026-07-19):** organizers topped up 70k credits on top of the earlier 60k → 130k in the
shared pool. Two projects share it; **our hard ceiling is 65k credits total** across all computations.

## Rates (qBraid on-demand, observed)
| Instance | Rate | Role |
|---|---|---|
| gpu-h100-sxm-5eee135b | 8.95 cr/min (537/h) | B1 (40q H₂₀ flagship); P3 attempt blocked (GPU failure) — **RETIRED 2026-07-19, ~17.5 h lifetime ≈ 9,400 cr** |
| gpu-a100-sxm-f38c0cd0 | 4.15 cr/min (249/h) | B2 (38q CrO audit) |

## Committed / projected spend (this campaign phase)
| Item | Estimate (cr) | Status |
|---|---|---|
| H100 uptime through B1 finalize (~16.7 h) | ~8,950 | spent |
| A100 uptime through 12.6 h | ~3,140 | spent |
| P3 device-memory test — moved to A100 post-B2 (H100 GPU failed, a24fe53) | ~750 | authorized |
| B2 to session ceiling (~8–10 h remaining) | ~2,000–2,500 | in flight |
| AQT decode, reproduce.py, paper work (CPU) | ~0 | — |
| **Subtotal, current instances + plan** | **~16–17k** | |

**Measured (wallet, 2026-07-19): 13,422 credits consumed from the pool, 100% attributable to this
project** (the second project has spent nothing yet). Wallet balance 116,578 of the 130,000 pool.
The 13,422 is entirely the two current instances — the ~12.1k table estimate plus running time
accrued between the console snapshot and the wallet check.

**Personally funded (zero draw on the grant share):** all GPU sessions before the first 60k top-up
(20q/28q cuStateVec runs, 38q DMRG reference build, 40q MPS attempt-1) were paid from the team's own
funds, as is the AQT QPU flight (personal OpenQuantum pool). Only the two current instances count
against the 65k.

**CAMPAIGN CLOSED — SETTLED (2026-07-19).** Settlement wallet snapshot (EIGENNEXUS grant org):
**113,517.30** → pool consumed **16,482.70 cr = 25.4% of the 65k share; remaining allowance 48,517**.
The interim 116,342 reading was pre-settlement billing lag (tension stated at the time, now resolved);
the observed-rate model landed within ~3% of the settled figure, validating it as the planning
instrument. Both GPU instances retired; all evidence pushed pre-shutdown. Grant-org subscription also
includes 100 CPU-hrs/mo (0 used, renews in 11 days) — free capacity for any future CPU-tier work.

## Rules of the road
1. **Hard stop at 65k cumulative** attributed to this project; check billing before any new instance.
2. The P5 QPU leg was funded from the personal OpenQuantum pool — it did NOT draw on the grant
   share. **CLOSED 2026-07-20:** all 3 AQT ibex-q1 jobs completed and decoded clean; actual billed
   60 cr (29+29 physics + 2 probe), leaving 102 of 162 personal credits (dashboard-confirmed,
   162−60=102 ✓). No resubmission needed; a grant-funded IonQ replacement is moot. A grant-funded IonQ Forte replacement (~80k) **does not fit** under
   the 65k cap; if AQT stalls permanently, that needs organizer sign-off, not a unilateral spend.
3. ~~No exploratory scale pushes (>40q) on the grant share~~ **AMENDED 2026-07-20 by explicit
   operator sign-off** (recorded in `preregistration_v2.json` → E5.governance_signoff): E2, E3,
   E4 STEP 2, and E5 (44q, re-frozen against χ=1200) are authorized on the grant share. E5 runs
   exactly as re-frozen — 44q H₂₂, nothing beyond; "max-q" pushes remain out of scope (assessed and
   declined 2026-07-20: no audit-grade reference exists past ~44q).
4. After B2 terminal evidence + P3 verdict: both instances shut down; all remaining work is CPU-tier.
   **Superseded 2026-07-20 by the E-campaign authorization:** new instance spend is governed by the
   projection below and the 65k cap; `verify_credits.py` remains the enforcement gate.

## ATTRIBUTION EVENT (2026-07-21) — the pool is now genuinely shared
At E-campaign instance start the grant wallet read **84,611** — down 28,906 from the 07-19
settlement with ~zero spend of ours: **the second project has begun drawing, heavily.** As the
ledger always said, pool balance stopped being our meter the moment that happened. Consequences,
implemented in `verify_credits.py` + `credit_ledger.json`:
- **Cap accounting is now attribution-based:** `attributed_spend_cr` (settled 16,482.7 + one line
  per E-campaign instance from console billing, appended at each shutdown) is what the 65k cap
  governs. qBraid per-instance billing is the arbiter, as pre-declared.
- **New runway check:** entitlement ≠ availability — the pool is first-come-first-served. The
  verifier FAILs if pool balance < our remaining worst-case projection (37.6k), WARNs below 1.5×.

**RUNWAY ESCALATION (2026-07-21 ~19:20Z):** live wallet **41,952** — the second project burned a
further ~42.7k in under a day; its cumulative draw (~70k+) now **exceeds a 50% share of the 130k
pool on its own**. Runway vs our remaining worst case ≈ **1.1× — below the WARN threshold; the
escalation trigger above has FIRED.** Response: (a) organizer escalation drafted for immediate
send (`docs/pool_runway_escalation_email.md`) requesting per-project accounting / ring-fencing of
our documented remaining share; (b) campaign re-prioritized to bank evidence early (E2 running,
E3 certificate acceleration proposed, E5 launch decision deferred pending organizer reply or
Wednesday-morning runway re-check); (c) all runners already tolerate a mid-run pool freeze —
evidence flushes and is pushed per iteration, so a freeze strands future compute, never completed
results. Our own conduct stays inside the cap: attributed spend to date ≈ 16.5k settled + E-runs
in flight; per-instance billing remains the arbiter.

## E-campaign authorization (2026-07-20)
| Run | Frozen spec | Est. (cr) |
|---|---|---|
| E3 — 40q certificate convergence | kcap 2M, EN-PT2 every iter, ≥200 GB RAM instance | 4,000–8,000 |
| E4 STEP 2 — Sn₂O₂ 38q QSCI | HF seed, 40k/iter, kcap 500k, vs committed STEP 1 reference | 2,500–5,000 |
| E2 — device-seeded 40q equivalence | committed `p3_sample_dets.json` seed (sampling cost 0), kcap 450k | 2,000–4,000 |
| E5 — 44q H₂₂ frontier | MP2 seed, 150k/iter, kcap 3M, vs re-frozen χ=1200 reference (built pre-run, CPU) | 6,000–10,000 |
| **Total projection** | | **14,500–27,000** |

Worst case: 16,483 (spent) + 27,000 = **43,483 < 65,000 cap** ✓ (remaining buffer ≥21.5k). The
DMRG-only classical ladder (H22 refs + 48–64q headroom study) runs on the session container CPU at
zero credits. Deadline gate: instances must be productive by ~Jul 22 to integrate by Jul 26;
unexecuted entries revert to pre-registered-outlook status, unmodified.

*EIGENNEXUS — GIC 2026 Phase 3. Same audit trail as the physics: numbers over vibes.*
