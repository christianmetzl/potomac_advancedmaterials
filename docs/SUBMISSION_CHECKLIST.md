# Phase 3 submission checklist — EIGENNEXUS (Advanced Materials) — VERIFIED AGAINST RULES 2026-07-22

**Deadline:** Sunday **2026-07-26, 11:59 PM EST**. Upload `EIGENNEXUS_AdvancedMaterials_Phase3.zip`
via the Aqora track page → **Submission tab**. One submission per team; ONE teammate uploads;
**re-upload replaces** — so upload early, replace as results land.
(Rules cross-checked against: Phase 3 Challenge Description PDF, Aqora Mitsubishi track page,
GIC main page FAQ, Aqora ToS — captures 2026-07-22.)

## Format requirements (verbatim from the rules)
- [ ] **Official GIC_2026 Cover Page.docx as page 1** — downloaded from the track page link, filled,
      NOT recreated/modified. Must carry the **device selection**: qBraid GPU (NVIDIA CUDA-Q) +
      QPU via qBraid catalog (IonQ/AQT/IQM) — the recorded promise from the access email.
- [ ] **Write-up ≤5 pages** (EXCLUDING references and cover page), **11-pt Times New Roman,
      single-spaced** — `paper/build_pdf.py` enforces the style and prints the page count;
      VERIFY ≤5 after integrating E-campaign results (overflow = disqualification risk).
- [x] **Zip name** `TeamName_Challenge_Phase3.zip` → `EIGENNEXUS_AdvancedMaterials_Phase3.zip` ✓
- [ ] **README.md** with: team/title/track ✓, setup ✓, step-by-step qBraid run ✓, expected I/O,
      limitations, **Launch on qBraid button** ✓ — BUT the results table is PRE-CAMPAIGN STALE
      (still lists 40q as "39 mHa converging"!) → must be refreshed to the executed results.
- [ ] **Source code** executable on qBraid without external configuration ✓ (developed + executed
      there; `requirements.txt`) — keep true after final edits.

## Content requirements (rubric + Top Actions)
- [x] Run on qBraid before submission — all at-scale results executed there (GPU + cloud QPU chain)
- [x] Classical baseline on same instances — FCI/CCSD(T)/DMRG + wall-clock table
- [x] Specific numbers — qubits/dets/χ/shots/wall-clock throughout; sampling-pivot disclosed at 40q
- [x] Honest limitations — §7 + disclosure culture (P3/P4 FAILs reported, χ-qualifier, VQE upgrade)
- [x] Track outcomes — 40q demo ✓, chemical accuracy vs committed refs ✓ (absolute = E3, in flight),
      hybrid workflow ✓, benchmarking vs classical ✓ + VQE (upgraded & disclosed) ✓
- [x] Bonus: noise-aware ✓ (20q corruption study + real trapped-ion P5); >40q ✓ (E5 44q in flight +
      48–64q classical simulation-layer ladder, honestly labeled)
- [ ] **AI-use disclosure** (see risk register): one precise statement in README + write-up using the
      rule's own language — AI used for code support and writing; technical contributions,
      formulations, and results are the team's own (frozen protocols, thresholds, and all governance
      decisions carry operator sign-offs in git history).

## Integration queue (blocking the final PDF/zip)
- [ ] Fold E-campaign results into the write-up as they land: E4 ✅ (done, −0.399 mHa PASS +
      below-reference ordering), E2 (today), E3 certificate (≈Wed), E5 (≈Thu; if non-converged →
      report per frozen rule; unexecuted extensions stand as pre-registered outlook, unmodified)
- [ ] Refresh README results table + wall-clock table (add AQT silicon row)
- [ ] Rebuild PDF (`python paper/build_pdf.py`) → verify page count → re-zip
      (`python paper/make_submission_zip.py`)
- [ ] **UPLOAD EARLY (Thursday), replace later** — never gate first upload on E5's Friday abort gate

## Access & platform
- [ ] **Judges must be able to reach the repo**: the Launch-on-qBraid button points at
      github.com/christianmetzl/potomac_advancedmaterials — make it public (or judge-accessible)
      before the deadline, else the README's reproduce path fails for judges.
- [ ] (Optional, free, strengthens criterion 7) canonical full-dependency `reproduce.py` transcript
      on the subscription CPU box.

## Risk register (assessed 2026-07-22)
1. **"Use of AI may be disqualified and voided"** (track page) vs the description's explicit
   permission ("generative AI permitted for code support and writing; technical contributions,
   formulations, and results must be the team's own"). Posture: we are in the permitted pattern;
   mitigate with the precise disclosure above, not silence. Low–moderate → low with disclosure.
2. **Page-limit creep** after E-result integration — build prints page count; hard gate before zip.
3. **Dirac-3 paragraph** in the description is cross-track boilerplate (the same document's access
   instructions say QCi is "Available for QCi Challenge Only"; our track names CUDA-Q in its title).
   No action; our platform use exceeds the intent (qBraid GPU + real QPU).
4. **Cover page** is the only disqualification-grade item not yet in hand → do first, not last.
5. One team per participant / ≤5 members / registration — satisfied (3 members, Phase-1 registered,
   Phase-3 finalists). IP: participants retain ownership, organizers get evaluation/derivative
   license (ToS) — informational, no action.

*Every claim in the write-up traces to `docs/claims_ledger.md` → script → committed evidence.
Numbers over vibes.*
