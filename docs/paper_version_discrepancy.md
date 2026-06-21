# ⚠️ Phase 2 paper — version discrepancy (needs Christian/Aqora confirmation)

**Found 2026-06-21 while verifying the reproducibility artifacts.** This is a high-stakes
version-control issue for Phase 3. It is unresolved until Christian confirms what was actually
submitted to Aqora.

## The discrepancy

Two different versions of the Phase 2 §2 "materials" sentence exist:

- **Repo version** (`paper/EIGENNEXUS_Phase2_Submission.docx`): ends at
  *"SnO 0.11 mHa (16q), SnO₂ 0.23 mHa (20q) — real target chemistry, not only hydrogen."*
  **No CrO/NiO.** Fully reproducible (`src/sno_demo.py`, `src/sno2_demo.py`).

- **Uploaded version** (`EIGENNEXUS_Phase2_VersionAdvancedMaterials1_1.docx/.pdf`, which Christian
  identified as *"the version we submitted for the win and shortlisting"*): adds
  *"…and on third-party HamLib transition-metal oxides … (CrO ⁵Π and NiO ³Σ⁻, **38q**, ~42 mHa
  active-space correlation), reaching **≤0.08 mHa** against exact-FCI / near-exact-DMRG references."*

The earlier `docs/REPRODUCIBILITY_NOTE.md` (prior chat) **assumed the repo (SnO-only) version was the
submitted one** and concluded the CrO/NiO line was from "an earlier draft." That assumption is
**contradicted** by the file Christian uploaded this session.

## Why it matters

- The **38q CrO/NiO ≤0.08 mHa claim is not reproducible** and, per `docs/transition_metal_README.md`,
  cannot be produced on CPU; no such run exists in any verifiable session. What *is* real is **CrO/NiO
  at 20q** (CrO 0.038 mHa, NiO 0.197 mHa — `src/transition_metal_oxide_qsci.py`). The accuracy
  (≤0.08 mHa) and the scale (38q) are **not the same claim** and must not be conflated.
- The paper itself invokes a Phase 3 **verification requirement**. If the 38q version is what the
  judges hold, an unreproducible claim sits in the finalist submission — the worst Phase 3 failure mode.

## Two scenarios — Christian must confirm which

- **(A) The SnO-only (repo) version was submitted to Aqora.** Then there is no liability; the uploaded
  docx is a later/alternate draft and should not be used going forward. The prior note stands.
- **(B) The CrO/NiO (uploaded) version was submitted to Aqora.** Then the unsupported 38q claim is in
  the finalist paper, and Phase 3 strategy must address it: either substantiate on the GPUs (hard, per
  the TM note) or be prepared to correct/walk it back proactively. The honest 20q results do **not**
  match the 38q claim.

**Action:** Christian to verify, against the actual Aqora submission record, which §2 went in. Until
then, treat the 38q CrO/NiO claim as unsupported and do not propagate it into any Phase 3 deliverable.
