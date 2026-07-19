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

**CAMPAIGN CLOSED (2026-07-19 ~22:40 UTC).** Final wallet snapshot: **116,342** → pool consumed
**13,658 cr** (21% of the 65k share; remaining allowance **51,342**). Both GPU instances retired
(H100 ~15:15Z, A100 ~22:35Z); all evidence pushed pre-shutdown. **Stated tension:** the observed-rate
model projected ~17k — the wallet delta since 13:30Z (~236 cr) lags ~3.4k of metered uptime,
consistent with deferred billing posting. Re-check the wallet in 12–24 h and append a settlement
snapshot to the ledger; per-instance billing history is the arbiter. Even at the rate-model's ~17k,
the campaign used ≈26% of the share.

## Rules of the road
1. **Hard stop at 65k cumulative** attributed to this project; check billing before any new instance.
2. The P5 QPU leg is funded from the personal OpenQuantum pool (AQT ibex-q1, ~82 of 162 cr) — it does
   NOT draw on the grant share. A grant-funded IonQ Forte replacement (~80k) **does not fit** under
   the 65k cap; if AQT stalls permanently, that needs organizer sign-off, not a unilateral spend.
3. No exploratory scale pushes (>40q) on the grant share: nothing is pre-registered beyond 40q and
   the evidence campaign is complete. Headroom is contingency reserve, and finishing well under
   budget is itself part of the cost-discipline claim.
4. After B2 terminal evidence + P3 verdict: both instances shut down; all remaining work is CPU-tier.

*EIGENNEXUS — GIC 2026 Phase 3. Same audit trail as the physics: numbers over vibes.*
