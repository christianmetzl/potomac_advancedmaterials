# Quantum-vs-classical wall clock — generated, not typed

Regenerate with `python src/make_walltable.py`. Every number is read from the committed
evidence JSON in the last column; '—' = not recorded (never invented).

| Qubits | System | Method / pipeline | Wall | Outcome | Evidence |
|---|---|---|---|---|---|
| 12 | H6 | CCSD(T) (CPU, single-thread) | 0.1 s | exact/deterministic | `classical_baselines_evidence.json` |
| 12 | H6 | FCI (CPU, single-thread) | 0.1 s | exact/deterministic | `classical_baselines_evidence.json` |
| 12 | H6 | QSCI via qBraid cloud runtime (qir-sv tier, 3 pooled jobs) | — | P5 protocol chain PASS (+2.0 mHa) | `qbraid_P5_*_evidence.json` |
| 20 | H10 | CCSD(T) (CPU, single-thread) | 0.2 s | exact/deterministic | `classical_baselines_evidence.json` |
| 20 | H10 | FCI (CPU, single-thread) | 0.7 s | exact/deterministic | `classical_baselines_evidence.json` |
| 20 | H10 | QSCI pipeline (cuStateVec sample 1.0 s + growth) | 3.2 min | err +0.000 mHa vs FCI (exact) | `gpu_run1_h10_nvidia_evidence.json` |
| 24 | H12 | CCSD(T) (CPU, single-thread) | 0.2 s | exact/deterministic | `classical_baselines_evidence.json` |
| 24 | H12 | FCI (CPU, single-thread) | 5.0 s | exact/deterministic | `classical_baselines_evidence.json` |
| 28 | H14 | QSCI pipeline (cuStateVec sample 31.5 s + growth) | 39.8 min | err +0.395 mHa vs block2 DMRG(chi=400) | `gpu_run1_h14_nvidia_evidence.json` |
| 38 | CrO CAS(18,19) | QSCI growth, HF seed (A100 host) | 19.1 h | err -3.784 mHa vs same-CAS DMRG | `gpu_run4_cas19_*.json` |
| 38 | CrO CAS(18,19) | block2 DMRG chi=400 (CPU, reference) | 7.2 min | E = -1118.045626 Ha | `cro_cas19_dmrg_reference.json` |
| 38 | CrO CAS(18,19) | block2 DMRG chi=800 (CPU, E1 counter-audit) | 5.8 min | chi-escalation check | `cro_cas19_dmrg_chi800.json` |
| 40 | H20 | QSCI growth, MP2 seed (CPU-bound eigensolves on H100 host) | ≈16 h* | err +1.226 mHa vs DMRG chi=400 — P1/P2 PASS | `gpu_run1_h20_mp2seed_evidence.json` |
| 40 | H20 | block2 DMRG chi=800 (CPU, E1 counter-audit) | 6.3 min | chi-escalation check | `h20_40q_dmrg_chi800.json` |

\* 40q growth wall reconstructed from the committed per-iteration checkpoint commits
(d834183, 2f8523b: three 150k-determinant growth iterations at ~2.5–5.7 h each on the
H100 host CPUs); the terminal evidence file's own wall_s covers only the finalize step
and is deliberately not quoted as the growth cost.

Context rows the table is judged against: FCI cost doubles per qubit (intractable ≥32q
on CPU — classical_baselines_evidence.json); DMRG chi for chemical accuracy grows
50→100→400 across 20→28→40q (mps_bonddim_evidence.json); the audit tier's decisive-number
cost at 38q was ≈$12 of cloud compute (see the cost-transparency section of the README and `src/cost_audit.py`).
