# qBraid access email — FINAL SENT VERSION (2026-07-06, rev 3 — as sent by C. Metzl)

Facts verified at send time: 24/24 reproduce checks; GPU runs 20q +0.000 / 28q +0.395 mHa executed
self-funded on qBraid RTX 4090; H100-sxm 8.95 cr/min and QPU rates per docs.qbraid.com/v2/home/pricing;
QPU catalog = IonQ Forte-1 / AQT IBEX Q1 / IQM (not IBM); deadline Sun 26 July 2026 11:59 PM EST.

---

To: quantum@connecteddmv.org
Subject: EIGENNEXUS (Advanced Materials — Mitsubishi/AIST): Phase 3 qBraid GPU/QPU access + device selection

Dear GIC 2026 Organizing Committee,

Team EIGENNEXUS is a Phase 3 finalist in the Advanced Materials challenge (Mitsubishi Chemical & AIST
— "Harnessing the Generative Quantum Eigensolver for Next-Generation Materials Design"). I'm writing to activate our qBraid
team credit allocation and to put our device selection clearly on record, so we can complete the
at-scale on-platform results for our Phase 3 submission.

Device selection. To remove any ambiguity at judging: our selection was not captured on our Phase 2
cover page, so I'm setting it on record now, well ahead of the Phase 3 deadline (Sunday, 26 July 2026,
11:59 PM EST). Our selection is: qBraid GPU compute (NVIDIA CUDA-Q) as the primary platform, plus QPU
access via qBraid (IonQ Forte-1 / AQT / IQM, per the current qBraid device catalog) for small-scale
hardware validation. This is exactly what our Phase 2 write-up justifies (NVIDIA H100/A100 (80 GB) +
CUDA-Q, and qBraid hardware validation at 10-16 qubits). We will record this selection on our Phase 3
cover page; please let me know if you also need a corrected Phase 2 cover page or any other step to
release access.

Progress to date. We did not wait for credits to progress our work. Our qBraid team account is already active: we self-funded initial
GPU runs on a qBraid RTX 4090 instance and executed our GQE->QSCI pipeline on NVIDIA hardware with
CUDA-Q (cuStateVec), reproducing exact full CI at 20 qubits (+0.000 mHa) and reaching chemical accuracy
at 28 qubits (+0.395 mHa vs a DMRG reference committed before access), plus an honest, converging
40-qubit frontier. The full pipeline is validated end-to-end through the qBraid cloud runtime,
including the QPU submission chain. Organizer credits therefore go directly to the remaining at-scale
runs, not to setup.

What we are requesting (matching our Phase 2 §6, "Platform Justification and Resource Needs"):

- qBraid GPU compute — NVIDIA H100 or A100 (80 GB) with the CUDA-Q SDK: the tensornet-mps backend for
  the 24-40-qubit tier (one high-memory GPU is sufficient for the core runs), and cuStateVec for exact
  validation to ~32 qubits.
- Multi-GPU (4-8 GPUs, NVLink), where available — for distributed circuit evaluation and our >40-qubit
  bonus attempt. The workflow degrades gracefully to a single GPU, so this is additive, not a blocker.
- qBraid classical (CPU/GPU) credits to run and reproduce the full pipeline.
- QPU credits (IonQ / AQT / IQM via qBraid) for hardware validation at 10-16 qubits — our verified
  12-qubit circuits are already submission-ready (SHA-pinned, export-verified against the native
  statevector).

What we plan to run: completion of the 40-qubit MPS GQE/QSCI scalability result on H20 (energy vs DMRG to
chemical accuracy, circuit depth, bond dimension, shot budget, wall-clock); near-38-qubit CrO
open-shell transition-metal oxide on GPU; a quantum-vs-classical wall-clock comparison; 10-16-qubit
validation on real QPU hardware; and, with multi-GPU, the >40-qubit bonus attempt. Everything else in
our submission is already executed and reproducible — a one-command reproduce.py passes 24/24
automated checks (16 clean-checkout re-executions + 8 committed-evidence audits) — so platform credits
go straight to the at-scale runs.

Estimated allocation (rates per docs.qbraid.com/v2/home/pricing): our core program needs ~50,000
qBraid credits — the 40-qubit completion, the 38-qubit CrO run, and the wall-clock comparison on
gpu-h100-sxm (8.95 credits/min), including realistic retry margins calibrated from our self-funded
runs, plus trapped-ion QPU validation (AQT/IonQ) with one resubmission cycle. The full program —
adding the >40-qubit multi-GPU bonus attempt (4x H100) and our pre-registered 10,000-shot QPU
protocol — comes to ~100,000-150,000 credits. These figures use the overhead multiplier we measured
on our own self-funded qBraid GPU runs rather than ideal-path estimates; failed QPU jobs bill
nothing on the platform, every run checkpoints durable evidence, and the workflow degrades
gracefully — a smaller allocation reduces scope rather than blocking results.

A few quick logistics:

- Could you confirm our qBraid team credit allocation is provisioned and loaded?
- I am completing the qBraid request form (https://qbraid.typeform.com/to/vTxsKddw) alongside this
  note — please let me know if anything further is needed from us to release access.
- We are ready to launch from our Aqora submission as soon as credits are live.

Thank you — we're looking forward to running the final at-scale results on the platform.

Best regards,
Christian Metzl
Team EIGENNEXUS (C. Metzl, F. Eldibani, J. M. Aguiar Hualde)
connect@christianmetzl.com · https://aqora.io/christianmetzl · https://aqora.io/eigennexus
