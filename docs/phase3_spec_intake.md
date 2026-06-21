# Phase 3 spec intake — what the official docs confirm (and what's still pending)

**Source:** the two official documents Christian provided 2026-06-21 —
*Mitsubishi Chemical & AIST Phase 2 Challenge Description* (the rubric/rules PDF) and the
*Aqora competition page* (gic-2026-Mitsubishi-AIST). These are the **Phase 2** spec plus the
Aqora finalist-access notes. **Full Phase 3 spec is still pending** — nothing below should be read
as the complete Phase 3 brief. This note records only what is now *officially confirmed* and the
action items it creates.

Hold on sizable build work remains in effect (per Christian). This is documentation intake, not build.

---

## 1. Requirements now officially confirmed (bear directly on Phase 3)

- **Reproducibility is a stated rule, verbatim:** *"Solutions must be reproducible. Code, data
  references, and run instructions must be sufficient for a third-party reviewer to verify the
  headline results in Phase 3."* → This is exactly the failure mode flagged in
  `paper_version_discrepancy.md`. The 38q CrO/NiO ≤0.08 mHa headline must be third-party
  verifiable or it must not be a headline.
- **Phase 3 = applied execution on real hardware.** Aqora: Phases 2→3 go "conceptual design →
  applied execution." Phase 3 expects functional prototypes / circuit designs run on the granted
  platforms.
- **Targets (reconfirmed):** ~40 qubits ideal, 20–30 acceptable; **chemical accuracy ~1.6 mHa**
  where possible. Bonus: **>40-qubit scaling** and **noise-aware design**.
- **Rubric, in priority order:** (1) **Scalability — primary**, (2) Accuracy, (3) Algorithmic
  innovation, (4) Computational efficiency, (5) Hybrid system design, (6) Benchmarking, (7) Clarity.
- **Timeline:** Phase 2 deadline was 2026-05-31 (past — consistent with finalist status);
  competition runs through Sep 2026; Phase 3 deadline / winners-notified dates were truncated in the
  Aqora capture and remain to be confirmed.

## 2. New action items / risks these docs create

- **[RISK] GPU vs. QPU gap in finalist hardware.** The Aqora finalist device list is **QPUs** —
  IonQ AQT, Cepheus-1-108Q, IQM Emerald, IBEX Q — plus IBM Open Plan / D-Wave / QCi. Our entire
  38q-substantiation path needs **NVIDIA H100/A100 + CUDA-Q tensornet-mps** (a GPU, not a QPU). Our
  submitted paper requests this, but it is **not** in the enumerated finalist list. **Must confirm
  qBraid grants GPU instances/credits to finalists**, or the "substantiate 38q on GPU" path has no
  hardware. (Verification on a real QPU — IonQ/IBM at 10–16q — is separately fine and already
  scoped in the paper.)
- **[ACTION] Cover-page device gate.** Aqora: *"The selection of that device must be made on the
  Cover Page, or usage will not be granted."* Plus the qBraid request form
  (https://qbraid.typeform.com/to/vTxsKddw) and *"you must still include your choice and
  justification in your Phase 2 write-up."* Our paper **body** requests qBraid GPU + IonQ/IBM, but
  the gate is the **cover page**, which is **not in the repo** (only `paper/phase1_cover_v2.docx`).
  → Christian to confirm the submitted *AdvancedMaterials* cover page named a device and that GPU
  access is covered by it.
- **[STRATEGY] Accuracy bar (~1.6 mHa) << our exposed claim (≤0.08 mHa).** Scalability is the
  *primary* criterion; ~1.6 mHa is the accuracy target. Our honest **20q CrO 0.038 / NiO 0.197 mHa**
  already meets or beats chemical accuracy. We are risking a reproducibility flag to defend a number
  ~20× tighter than the rubric asks for. This *strengthens* the "correct proactively" option in
  `paper_version_discrepancy.md`: lead Phase 3 with real 20q results + 38q as the GPU **scaling
  target**, not an achieved figure.
- **[OPPORTUNITY] Noise-aware design is an explicit bonus** and Phase 3 runs on real hardware.
  Maps to Option E in `phase3_novelty_assessment.md`; our QSCI step is already argued to be
  intrinsically noise-robust (demonstrated at 20q).

## 3. Still pending (do not plan against as if known)

- The full Phase 3 challenge description (exact deliverables, scoring weights, page/format limits).
- Confirmed Phase 3 deadline and winners-notified dates.
- Which platforms/credits *we specifically* are granted as a finalist (esp. GPU — see §2 risk).

## 4. Cross-references

- `paper_version_discrepancy.md` — the 38q ≤0.08 mHa exposure these rules make load-bearing.
- `phase3_novelty_assessment.md` — novelty options A–E; §2 here reweights toward proactive correction.
- `transition_metal_README.md` — why 38q cannot be produced on CPU (needs the §2 GPU path).
