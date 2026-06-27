# Phase 3 submission checklist — EIGENNEXUS (Advanced Materials)

**Deadline:** Sunday 2026-07-26, 11:59 PM EST. Upload `EIGENNEXUS_AdvancedMaterials_Phase3.zip` to Aqora.

## ✅ Done (in the repo / zip)
- [x] **Write-up PDF** — `paper/EIGENNEXUS_Phase3_Writeup.pdf` (§1–8 = 5 pages; references on p.6, excluded
      from the limit; 11-pt Times New Roman, single-spaced). Rebuild: `python paper/build_pdf.py`.
- [x] **Source code** — all CPU-verified scripts + the qBraid GPU run-list scripts (`src/`, `src/encoder/`).
- [x] **README.md** — team/title/track, setup, step-by-step qBraid run, expected I/O, limitations,
      **Launch on qBraid** button.
- [x] **Reproducibility** — `python src/reproduce.py` → **12/12 PASS** (10 core + 2 optional CUDA-Q/MPS; transcript: `docs/reproduce_transcript.txt`).
- [x] **Traceability** — `docs/claims_ledger.md` (every number → script → evidence → status).
- [x] **requirements.txt** (CPU) + **requirements-gpu.txt** (cudaq/quimb/block2).
- [x] **Submission zip** — `python paper/make_submission_zip.py` → `EIGENNEXUS_AdvancedMaterials_Phase3.zip`.
- [x] **Honesty pass** — independent verification GO; no overclaims; GPU items marked as targets.

## ⛔ Team actions required before upload
- [ ] **Prepend the official GIC_2026 cover page** (provided .docx template, unmodified) as page 1 of the
      final write-up PDF. Final = [cover page] + `EIGENNEXUS_Phase3_Writeup.pdf`. (Cover page is required and
      excluded from the 5-page limit; do not recreate/modify it.) Then re-zip (swap the PDF in the zip).
- [ ] **Record the device selection on the Phase 3 cover page** = qBraid GPU (CUDA-Q) + IonQ/IBM QPU.
      ⚠️ It was **omitted from the Phase 2 cover page** — access is gated on this, so it MUST appear now.
- [ ] **Send the qBraid access email** (`docs/qbraid_access_email.md`) to quantum@connecteddmv.org **early** —
      it discloses the omitted device selection and requests the remedy, which may need an organizer reply
      before access is granted. Confirm the qBraid TypeForm POC step.

## 🎯 Highest-impact remaining work (needs qBraid GPU access)
- [ ] Execute the **40q MPS GQE/QSCI** run on H₂₀ (depth, bond dim, shots, GPU wall-clock) → fills the
      primary-criterion `[QBRAID-RUN]` placeholder in §5c.
- [ ] **Near-38q CrO/NiO** on GPU; **quantum-vs-classical wall-clock**; **10–16q IonQ/IBM** validation.
- [ ] Replace the `[QBRAID-RUN]` placeholders in the write-up with the executed numbers, rebuild the PDF, re-zip.

## Notes
- If qBraid access does not arrive in time, the `[QBRAID-RUN]` items remain clearly labeled as targets
  (honest; the rubric rewards this over overstatement). The submission is complete and compliant without
  them — they are upside, not prerequisites.
