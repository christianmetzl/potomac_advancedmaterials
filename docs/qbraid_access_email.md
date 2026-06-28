# qBraid / GPU access request email (GIC 2026 Phase 3) — send-ready

> Copy everything between the rules below into your mail client. Fill the three bracketed fields
> ([…]) with your real addresses, and actually submit the qBraid form (link in the body) before/with
> sending. Nothing else needs changing — every claim in the body is verified true.

---

**To:** quantum@connecteddmv.org
**Cc:** [your EIGENNEXUS teammates]
**From:** [your registered EIGENNEXUS team contact email]
**Subject:** EIGENNEXUS (Advanced Materials — Mitsubishi/AIST): Phase 3 qBraid GPU/QPU access + device selection

Dear GIC 2026 Organizing Committee,

Team **EIGENNEXUS** is a Phase 3 finalist in the Advanced Materials challenge (Mitsubishi Chemical & AIST —
"Scaling the Generative Quantum Eigensolver with NVIDIA CUDA-Q"). I'm writing to activate our qBraid team
account and credit allocation, and to put our device selection clearly on record, so we can run the
on-platform results for our Phase 3 submission.

**Device selection.** To remove any ambiguity at judging, I want to confirm our platform/device selection in
writing: our selection was not captured on our Phase 2 cover page, so I'm setting it on record now, well ahead
of the Phase 3 deadline (Sunday, 26 July 2026, 11:59 PM EST). **Our selection is: qBraid GPU compute (NVIDIA
CUDA-Q) as the primary platform, plus IonQ/IBM QPU access via qBraid for small-scale hardware validation.**
This is exactly what our Phase 2 write-up justifies (it requests NVIDIA H100/A100 (80 GB) + CUDA-Q and qBraid
hardware validation at 10–16 qubits). We will record this selection on our Phase 3 cover page; please let me
know if you also need a corrected Phase 2 cover page or any other step to release access.

**What we are requesting (matching our Phase 2 §6, "Platform Justification and Resource Needs"):**

1. **qBraid GPU compute** — NVIDIA H100 or A100 (80 GB) with the CUDA-Q SDK: the **tensornet-mps** backend for
   the 24–40-qubit tier (one high-memory GPU is sufficient for the core runs), and **cuStateVec** for exact
   validation to ~32 qubits.
2. **Multi-GPU (4–8 GPUs, NVLink), where available** — for distributed circuit evaluation and our >40-qubit
   bonus attempt. The workflow degrades gracefully to a single GPU, so this is additive, not a blocker.
3. **qBraid classical (CPU/GPU) credits** to run and reproduce the full pipeline.
4. **QPU access** (IonQ/IBM via qBraid) for hardware validation at 10–16 qubits.

**What we will run:** the 40-qubit MPS GQE/QSCI scalability result on H₂₀ (energy vs DMRG, circuit depth, bond
dimension, shot budget, wall-clock); near-38-qubit CrO/NiO open-shell transition-metal oxides on GPU; a
quantum-vs-classical wall-clock comparison; 10–16-qubit circuit validation on QPU; and, with multi-GPU, the
>40-qubit bonus attempt. Estimated need ~2 weeks of GPU wall-clock; the workflow is backend-agnostic and
flexible to whatever allocation you provide. Everything else in our submission is already executed and
reproducible on CPU — a one-command `reproduce.py` passes 13/13 — so GPU time goes straight to the at-scale runs.

**A few quick logistics:**
- Could you confirm our qBraid team account is provisioned and our credits are loaded?
- I am completing the qBraid request form (https://qbraid.typeform.com/to/vTxsKddw) alongside this note —
  please let me know if anything further is needed from us to release access.
- We are ready to launch on qBraid from our Aqora submission as soon as credits are live.

Thank you — we're looking forward to running the final at-scale results on the platform.

Best regards,
Christian Metzl
Team Lead, EIGENNEXUS
[your registered EIGENNEXUS team contact email] · https://aqora.io/eigennexus

---

## Before you hit send (3 things — none change the body wording)
1. **From / signature email:** use the address the organizers have on file for your team (your Aqora/
   registration contact). Replace both `[…]` email fields with it.
2. **Cc:** add your teammates' addresses (or delete the Cc line if you'd rather send solo).
3. **qBraid form:** actually submit https://qbraid.typeform.com/to/vTxsKddw — the body says you're doing it
   "alongside this note," so do it the same day to keep that true.

## Why this is credibility-safe
- Every factual claim is verified: recipient address, the deadline, the cover-page rule, the §6 resource list,
  the TypeForm URL, and the 13/13 `reproduce.py` result all match the committed spec and our submission.
- The device-selection note is framed as a proactive correction ("setting it on record now"), not an apology —
  honest and constructive, which strengthens rather than weakens standing. (It is also required: per the rule,
  access is not granted unless the device is selected on the cover page.)
- No over-claims: GPU/QPU at-scale results are described as what we *will run*, never as done.
