# GPU/QPU credit budget — grant-share accounting

**Constraint (2026-07-19):** organizers topped up 70k credits on top of the earlier 60k → 130k in the
shared pool. Two projects share it; **our hard ceiling is 65k credits total** across all computations.

## Rates (qBraid on-demand, observed)
| Instance | Rate | Role |
|---|---|---|
| gpu-h100-sxm-5eee135b | 8.95 cr/min (537/h) | B1 (40q H₂₀ flagship) + P3 memory test |
| gpu-a100-sxm-f38c0cd0 | 4.15 cr/min (249/h) | B2 (38q CrO audit) |

## Committed / projected spend (this campaign phase)
| Item | Estimate (cr) | Status |
|---|---|---|
| H100 uptime through B1 finalize (~16.7 h) | ~8,950 | spent |
| A100 uptime through 12.6 h | ~3,140 | spent |
| P3 device-memory test on H100 (~3 h, 4 h cap) | ~1,600–2,150 | authorized |
| B2 to session ceiling (~8–10 h remaining) | ~2,000–2,500 | in flight |
| AQT decode, reproduce.py, paper work (CPU) | ~0 | — |
| **Subtotal, current instances + plan** | **~16–17k** | |

**Unquantified prior spend (TBD from qBraid billing page):** earlier GPU sessions on the first 60k
top-up — 20q/28q cuStateVec runs, 38q DMRG reference build, 40q MPS attempt-1. Expected low
thousands (the 38q class cost ≈ $12/run), but must be read off per-instance usage history, not
assumed. **Action: pull the billing breakdown and replace this line with numbers.**

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
