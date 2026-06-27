# Draft email — qBraid / GPU access request (GIC 2026 Phase 3)

**To:** quantum@connecteddmv.org
**Cc:** (team members)
**From:** Christian Metzl — Team Lead, EIGENNEXUS (connect@christianmetzl.com)
**Subject:** EIGENNEXUS (Advanced Materials, Mitsubishi/AIST) — Phase 3 qBraid GPU + QPU access / credits

---

Dear GIC 2026 Organizing Committee,

Team **EIGENNEXUS** is a Phase 3 finalist in the Advanced Materials challenge (Mitsubishi Chemical & AIST —
"Scaling the Generative Quantum Eigensolver with NVIDIA CUDA-Q"). We are writing to confirm and activate our
**qBraid team account and credit allocation** so we can execute the on-platform results for our Phase 3
submission.

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
reproducible on CPU (a one-command `reproduce.py` passes 7/7), so GPU time goes straight to the at-scale runs.

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
*Notes for the team before sending: (1) confirm the exact device choice recorded on the Phase 2 cover page so
this matches it; (2) confirm whether the TypeForm was already submitted (adjust the wording); (3) add Fares
and Juan to Cc.*
