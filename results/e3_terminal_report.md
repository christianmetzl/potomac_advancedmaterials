# E3 — 40q flagship certificate run: TERMINAL REPORT (as-is)

**Run:** `src/e3_certificate_40q.py`, MP2-seeded H20/40q, GROW_PER_ITER=150,000, KCAP=2,000,000
(frozen, unchanged). PT2 certificate evaluated every iteration over the complete connected
external space (chunked, hash-bucketed; committed `selci_pt2` EN-PT2 formula).
**Box:** qBraid box A (64 vCPU / 256 GB). **State-file-free** (disclosed deviation — ~20 GB disk).
**PT2 scheduling:** `PT2_PROCS=8` (bucket-parallel; validated **bit-identical** to serial — see below).

## Terminal disposition
E3 **terminated during it6 growth** by an external pod kill (last log write / it5 flush
2026-07-23 22:34 UTC; process confirmed alive growing it6 at 23:25 UTC; found dead 2026-07-24 06:59
UTC). No Python traceback, **no kernel OOM-killer record** (dmesg), RAM ~82 GB at last sighting —
consistent with an external/infrastructure kill, not a reproducible resource fault. Six certificate
points (it0–it5) were flushed, committed, and pushed before termination; the durable per-iteration
record is intact.

**No relaunch.** A from-seed restart (no state file) would re-derive the already-committed it0–it5
(~50 h, ~19–25k cr), breach the 65,000 cr share cap (23,188 cr headroom at decision time; verifier
already reporting projected-cap breach), and could not reach the |dE_PT2| ≤ 0.5 mHa certificate
before the 2026-07-26 submission deadline (it5 = 1.313 mHa; trend ~it10–11). Operator decision
2026-07-24: **report as-is, do not relaunch.** Reported here with the same prominence as a success,
per the frozen discipline.

## Frozen predictions — judged independently, as-is

| # | Prediction (frozen) | Terminal result | Verdict |
|---|---|---|---|
| i | \|dE_PT2\| ≤ 0.5 mHa before kcap (certificate convergence at flagship scale) | Certificate contracted **monotonically 84.234 → 4.643 → 2.589 → 1.951 → 1.571 → 1.313 mHa** (it0→it5); run externally terminated at it6 before reaching 0.5 mHa | **NOT CERTIFIED** (converging, non-terminal; terminated by external kill) |
| ii | terminal E_var ≤ +0.9 mHa vs committed chi=400 reference (−10.292194) | it5 E_var = **−10.292009 → +0.185 mHa** vs chi=400 (also +1.154 mHa vs chi=800) | **MET** |
| iii | det budget at certificate convergence within [357k, 3.57M] (half-decade of 1.13e6) | it5 dets = **750,257** (within band; certificate not yet terminal) | **MET at terminal state** (convergence not reached) |

Prediction i is a genuine, as-is non-certification: the certificate was still contracting and had
not reached the 0.5 mHa threshold when the box was killed. It is **not** a physics/threshold failure
and **not** a kcap-exhaustion failure — it is an interrupted run, reported unmodified.

## Integrity check (free, from the parallelization)
PT2 was parallelized across independent hash-buckets (`PT2_PROCS=8`) between it1 and it2 —
**scheduling only**, per-bucket arithmetic unchanged. Gate evidence:
- `--smoke 6` with PT2_PROCS=8: `parallel==serial: BIT-IDENTICAL` on 7/7 points; PT2 matches the
  committed `selci_pt2.en_pt2` at machine precision (|d| ≤ 2e-19 Ha). `FORMULA VALIDATED`.
- Production reproduction: parallel it0/it1 reproduced the prior **serial** certificate points
  **exactly** — it0 PT2 −84.2340 mHa (ext 3,834,586); it1 PT2 −4.6434 mHa (ext 534,635,459).
  (Marker commit `83e801e`.) Parallel it1 wall 6,103 s vs serial 46,483 s (~7.6×).

## Evidence
- `results/e3_certificate_evidence.json` — measured points it0–it5 (untouched).
- `e3.log` — full per-iteration / per-bucket trace.
- Git history on `claude/wonderful-bohr-rir81t` — tamper-evident timestamps; evidence pushed at
  every completed iteration (auto-checkpoint loop, pull-rebase-autostash).

*Frozen first, measured always, reported as-is.*
