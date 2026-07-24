# Phase 3 submission checklist — EIGENNEXUS (Advanced Materials) — REFRESHED 2026-07-24

**Deadline:** Sunday **2026-07-26, 11:59 PM EST**. Upload `EIGENNEXUS_AdvancedMaterials_Phase3.zip`
via the Aqora track page → **Submission tab**. One submission per team; ONE teammate uploads;
**re-upload replaces** — so upload early, replace if anything changes.
(Rules cross-checked against: Phase 3 Challenge Description PDF, Aqora Mitsubishi track page, GIC FAQ,
Aqora ToS — captured 2026-07-22.)

## STATUS: package complete — 3 user-side actions remain
The write-up, code, evidence, and zip are **done, committed, and consistent**; `main` is current so the
Launch-on-qBraid button serves the full submission. What's left is **cover page → make repo public →
upload** (+ a 30-second incognito button check). Nothing compute or code remains.

---

## ✅ COMPLETE
**Format**
- [x] **Write-up ≤5 pages** (excl. references + cover), 11-pt Times New Roman, single-spaced —
      `paper/build_pdf.py` prints the count; **verified 5 content pages** after every edit.
- [x] **Zip name** `EIGENNEXUS_AdvancedMaterials_Phase3.zip` (203 files) — `paper/make_submission_zip.py`.
- [x] **README.md** — team/title/track, setup, step-by-step qBraid run, expected I/O, limitations,
      Launch-on-qBraid button; **results table refreshed to executed results** (was pre-campaign stale).
- [x] **Source code** executable on qBraid without external config (`requirements.txt`; `reproduce.py`
      needs no downloads for the CPU set).
- [x] **AI-use disclosure** — precise statement in README **and** write-up (per the rule's own language:
      AI for code/writing; technical contributions, formulations, results are the team's own; frozen
      protocols/thresholds + operator sign-offs in git history).

**Content (rubric + Top Actions)**
- [x] Executed on qBraid — 20/28q cuStateVec, 40q flagship, 38q CrO + Sn₂O₂ (E4), real AQT trapped-ion QPU.
- [x] Classical baselines on matched instances — FCI/CCSD(T)/DMRG + wall-clock table.
- [x] Specific numbers — qubits/dets/χ/shots/wall-clock throughout; 40q sampling-pivot disclosed.
- [x] Honest limitations — §7 + disclosure culture (P3/P4 FAILs, χ-qualifier, VQE→classical upgrade).
- [x] Track outcomes — 40q demo; chemical accuracy vs committed refs; **absolute accuracy demonstrated
      independently by E6 DMRG-extrapolation (+1.59 mHa)** after E3's pre-registered PT2 certificate ran
      to a terminal it5 (external pod kill, ii+iii MET, i not certified — reported as-is); hybrid workflow;
      classical benchmarking + VQE (disclosed).
- [x] Bonus — noise-aware (20q corruption + real trapped-ion P5); >40q (E5 44q non-converged, reported;
      48–64q classical simulation-layer ladder, labeled).

**Integration & verification**
- [x] E-campaign folded into the write-up: E4 −0.399 (2nd reference correction), Sn₂O₂ EUV trust curve,
      E3 terminal certificate, E2 resource-DNF, E5 non-converged, E6 absolute-accuracy anchor.
- [x] PDF rebuilt → page-count gate PASS → zip regenerated.
- [x] `reproduce.py` = **26 checks** (17 re-execution + 9 audits incl. AQT decode + cost audit).
- [x] **`cost_audit.py`** — program cost re-derived from published pricing × committed configs; OpenQuantum
      pool reconciled (162→102). Executable cost transparency.
- [x] **`main` branch fast-forwarded** to the submission (the button clones `main`).
- [x] Full-dependency `reproduce.py` transcript captured → `docs/reproduce_transcript.txt`.

---

## ⏳ OPEN — required (all user-side)
- [ ] **Official GIC_2026 Cover Page.docx as page 1** — download from the track-page link, fill in (team,
      title, track, **device selection**: qBraid GPU / NVIDIA CUDA-Q + QPU via the qBraid catalog), do NOT
      recreate/modify the template. *The only disqualification-grade item still open.* (`phase1_cover_v2.docx`
      in the repo is the Phase-1 cover — not this.)
- [ ] **Make the repo public** — `github.com/christianmetzl/potomac_advancedmaterials` → Settings → Danger
      Zone → Change visibility → Public. The Launch-on-qBraid button + judge access fail until this.
- [ ] **Verify the button** from an incognito window once public (repo loads logged-out ⇒ button works).
- [ ] **Upload the zip** to the Aqora Submission tab — upload early; re-upload replaces.

## 🔵 OPTIONAL — nothing depends on these
- [ ] HamLib raw-operator slice (`src/hamlib_extract_slice.py` / `download_and_bundle_hamlib.py`) — the
      offline term-count + one-norm cross-check already works from committed constants; the slice only
      upgrades it to a full-operator check. NERSC portal currently unreachable; add later or skip.

## Risk register (still current)
1. **AI-use policy** — permitted for code/writing; results must be the team's own. Mitigated by the
      committed disclosure (above) + pre-registration/git provenance. Low with disclosure.
2. **Page-limit creep** — hard gate before every zip; currently 5 pages.
3. **Dirac-3 paragraph** in the description is cross-track boilerplate; our track names CUDA-Q. No action.
4. **Cover page** — the one disqualification-grade item still in hand → do first.
5. Team/registration/IP — satisfied (3 members, Phase-1 registered, Phase-3 finalists).

*Every claim in the write-up traces to `docs/claims_ledger.md` → script → committed evidence, and the
program cost re-derives via `src/cost_audit.py`. Numbers over vibes.*
