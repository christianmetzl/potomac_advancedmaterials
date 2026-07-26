# ⚠️ Phase 2 paper — version discrepancy → RESOLVED: Scenario B confirmed

**Found 2026-06-21 while verifying the reproducibility artifacts. RESOLVED same day:**
Christian uploaded the actual Aqora submission (`EIGENNEXUS__Phase2_VersionAdvancedMaterials1_1.docx`,
"this is the submitted paper version to aqora"). **It is the CrO/NiO 38q version — Scenario B below.**
The unsupported 38q ≤0.08 mHa transition-metal claim is therefore in the finalist paper, and Phase 3
strategy must address it. See "Resolution & required action" at the bottom.

## The discrepancy

Two different versions of the Phase 2 §2 "materials" sentence exist:

- **Repo version** (the Phase 2 submission — *removed from the repo for privacy; it carried team emails*): ended at
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

## Two scenarios — RESOLVED to (B)

- **(A) The SnO-only (repo) version was submitted to Aqora.** ❌ Not what happened.
- **(B) The CrO/NiO (uploaded) version was submitted to Aqora.** ✅ **Confirmed** by Christian's
  upload of the AdvancedMaterials docx as the submitted file. The unsupported 38q claim is in the
  finalist paper.

## Resolution & required action (Scenario B)

The submitted §2 makes **two distinct claims** about CrO/NiO that the current evidence does not back:
1. **Scale:** 38 qubits. Reality: only **20q** exists (CAS(10,10)); no 38q TM run exists anywhere, and
   it cannot be produced on CPU — it needs the Phase 3 GPUs (CUDA-Q + MPS).
2. **Accuracy:** "≤0.08 mHa" for **both** species. Reality: CrO hits 0.038 mHa ✓ at 20q, but
   **NiO is 0.197 mHa** at 20q — already above 0.08 mHa at the *easy* scale, and the gap only widens
   with size. So even the accuracy figure, as stated for the pair, is not currently met by NiO.

This is the worst Phase 3 failure mode: an unreproducible quantitative claim in the finalist paper,
which itself invokes a verification requirement. Two honest paths for Phase 3, not mutually exclusive:
- **Substantiate on GPUs:** attempt CrO/NiO at (or near) 38q via MPS/QSCI on the requested H100/A100s.
  Hard and uncertain; success would retroactively validate the claim.
- **Correct proactively:** lead Phase 3 with the *real* 20q CrO/NiO results (genuine open-shell
  multireference chemistry — still a strong result) and reframe 38q as the GPU scaling target rather
  than an achieved number. Walking back a single over-reach voluntarily is far cheaper than having a
  judge find it.

**Until a 38q run exists with shipped, rerunnable code, treat the 38q ≤0.08 mHa CrO/NiO claim as
unsupported and do not propagate it into any Phase 3 deliverable.**
