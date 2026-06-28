# Draft email — qBraid / GPU access request (GIC 2026 Phase 3)

**To:** quantum@connecteddmv.org
**Cc:** (team members)
**From:** Christian Metzl — Team Lead, EIGENNEXUS (connect@christianmetzl.com)
**Subject:** EIGENNEXUS (Advanced Materials, Mitsubishi/AIST) — Phase 3 qBraid GPU/QPU access + device-selection correction

---

Dear GIC 2026 Organizing Committee,

Team **EIGENNEXUS** is a Phase 3 finalist in the Advanced Materials challenge (Mitsubishi Chemical & AIST —
"Scaling the Generative Quantum Eigensolver with NVIDIA CUDA-Q"). We are writing to confirm and activate our
**qBraid team account and credit allocation** so we can execute the on-platform results for our Phase 3
submission.

**Important — device selection (please advise on remedy).** We need to flag, transparently, that our
platform/device selection was **inadvertently omitted from our Phase 2 cover page**. We understand the rule
that the selection must be recorded on the cover page for usage to be granted, so we want to correct this
now, well ahead of the Phase 3 deadline. **Our intended platform selection is: qBraid GPU compute (NVIDIA
CUDA-Q) as the primary platform, plus IonQ/IBM QPU access (via qBraid) for small-scale hardware validation.**
Could you please advise how we can formally record this so access can be granted — e.g., confirm it via this
email and the qBraid TypeForm, submit an updated/corrected cover page, or note it on our Phase 3 cover page?
We are happy to follow whatever process you prefer and to provide anything you need. The selection is fully
consistent with our Phase 2 write-up, which explicitly requests NVIDIA H100/A100 + CUDA-Q and qBraid hardware
validation (IonQ/IBM).

**What we need (per our Phase 2 cover-page platform selection):**

1. **qBraid GPU compute** — NVIDIA **H100 or A100 (80 GB)** instances with the **CUDA-Q SDK** (tensornet-mps
   and cuStateVec backends). This is the core requirement: our scaling tier runs GQE circuit simulation via
   CUDA-Q's MPS backend, whose memory scales with entanglement rather than 2ⁿ.
2. **qBraid classical (CPU/GPU) credits** to run and reproduce the full pipeline.
3. **QPU access** (IonQ / IBM via qBraid) for small-scale hardware validation at 10–16 qubits.

**What we will run with it (our Phase 3 execution list):**
- 40-qubit MPS GQE/QSCI on H₂₀ — energy error vs DMRG, circuit depth, bond dimension, shot budget, GPU
  wall-clock (our primary scalability result).
- Near-38-qubit CrO/NiO open-shell transition-metal oxides via MPS/QSCI on GPU.
- Quantum-vs-classical wall-clock comparison (MPS/QSCI vs exact statevector vs VQE).
- 10–16-qubit circuit validation on IonQ/IBM QPU.

Estimated need: ~1–2 weeks of single high-memory GPU wall-clock (the workflow is backend-agnostic and
degrades gracefully to a smaller allocation). Everything else in our submission is already executed and
reproducible on CPU (a one-command `reproduce.py` passes 13/13, incl. CUDA-Q qpp-cpu + MPS checks), so GPU time goes straight to the at-scale runs.

**Logistics:**
- Could you confirm our team account is provisioned and credits are loaded, and point us to the device-request
  status from our Phase 2 down-select?
- Our POC (Christian Metzl) completed / will complete the qBraid TypeForm (https://qbraid.typeform.com/to/vTxsKddw).
  Please let us know if anything further is required from us to release access.
- We are ready to click **Launch on qBraid** from our Aqora submission the moment credits are live.

Thank you very much — we are excited to execute the final at-scale results on the platform.

Best regards,
Christian Metzl
Team Lead, EIGENNEXUS
connect@christianmetzl.com · https://aqora.io/eigennexus

---
*Notes for the team before sending: (1) device selection was omitted from the Phase 2 cover page — this email
discloses that and proposes the correction (qBraid GPU/CUDA-Q + IonQ/IBM); make sure the Phase 3 cover page
DOES record this selection; (2) confirm whether the qBraid TypeForm was already submitted and adjust the
wording; (3) add Fares and Juan to Cc; (4) send early — the remedy may need an organizer reply before access
is granted, so the sooner the better.*
