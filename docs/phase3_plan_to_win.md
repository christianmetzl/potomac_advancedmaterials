# Phase 3 — evaluation & plan to win (GIC 2026, Advanced Materials)

**Prepared 2026-06-26**, on receipt of the full Phase 3 spec (challenge description + Aqora page) and
the confirmed finalist paper (`EIGENNEXUS__Phase2_VersionAdvancedMaterials1_1`). Decision input for
Christian / Juan / Fares. Every claim below traces to those documents or to our committed
`results/*.json` + the 2026-06-21 reproducibility audit.

---

## 0. The clock and the deliverable

- **Deadline: Sunday 2026-07-26, 11:59 PM EST — ~30 days.** (Aqora, Phase 3 page.)
- **Deliverable:** a single zip `EIGENNEXUS_AdvancedMaterials_Phase3.zip` containing:
  1. **Write-up** — max **5 pages** PDF (was 3), 11pt Times New Roman, single-spaced, excl. references
     + Phase 3 cover page template.
  2. **Source-code folder** — all code to reproduce, well-commented, **executable on qBraid with no
     external configuration**.
  3. **README.md** — team, project title, track; setup/deps; **step-by-step run instructions on
     qBraid**; expected inputs/outputs; known limitations; a **"Launch on qBraid" button**.

## 1. Two spec facts that change our last-round risk picture

- **GPU is available. Risk retired.** Aqora Phase 3: *"the Organizing Committee is creating a team
  account on qBraid with an allocation of credits … credits can be used to access both **classical
  (CPU/GPU) and quantum (QPU)** computing resources."* The GPU-vs-QPU gap I flagged in
  `phase3_spec_intake.md` §2 is resolved — the H100/A100 + CUDA-Q MPS path our paper requests **has
  hardware**. This makes the 40q and 38q GPU runs *executable*, which is the whole game now.
- **Boilerplate contamination — do not be misled.** Phase 3 description p5 says *"working
  implementations run on **QCi's Dirac-3** … executed on a concrete **grid instance**."* That is
  copy-paste from the **energy/grid-optimization track** (QCi Dirac-3 is *"Available for QCi Challenge
  Only"*; "grid instance / siting / grid topology" is not our domain). **Our track** is GQE on
  **NVIDIA CUDA-Q via qBraid GPU** (+ optional IonQ/IBM QPU validation), per the challenge title and
  the authoritative Aqora page. → **Action:** one-line confirmation email to
  quantum@connecteddmv.org so there is no ambiguity at judging.

## 2. The rubric moved from "design" to "executed results"

| # | Phase 2 criterion | Phase 3 criterion | What changed |
|---|---|---|---|
| 1 | Scalability (primary) | Scalability (primary) | unchanged — still the #1 weight |
| 2 | Accuracy | Accuracy & scientific validity | — |
| 3 | Algorithmic innovation | Algorithmic innovation | — |
| 4 | Computational efficiency | Computational efficiency | — |
| 5 | Hybrid system design | Hybrid system design | — |
| 6 | Benchmarking | **Platform Use** | now: qubit/depth/shot estimates, integration appropriateness |
| 7 | — | **Phase 3 Execution (NEW, "critical")** | *"detailed write-up of concrete results, observations, conclusions"* |
| 8 | Clarity | Clarity & reproducibility | judges **re-run your code**; unreproducible ⇒ no credit |

**The six "Top Actions" the judges spelled out (these are the scoring key):**
1. **Run code on qBraid before submission** — judges re-run exactly as submitted; *a result that cannot
   be reproduced will not receive credit.*
2. **Report a classical baseline on the same instance** — *"the single most common gap in Phase 2."*
   Mandatory, every result.
3. **Demonstrate & explain quantum advantage** — concrete results, qubit/depth/shot, integration.
4. **Be specific about numbers** — qubit count, circuit depth, shot budget, **wall-clock**, key metric
   values must appear. Qualitative is not sufficient.
5. **Complete README.md** — *"the first thing judges read."*
6. **Be honest about limitations** — *"honest limitations + a working implementation will OUTSCORE an
   overstated claim + a partial one."*

## 3. Where we stand vs. what Phase 3 rewards (gap analysis)

| Asset we have (verified) | Phase 3 status | Gap to close |
|---|---|---|
| Two-stage GQE chem-acc 4–12q; GQE→QSCI 12q (1.05 mHa) | strong, but **CPU/local only** | re-run on qBraid; capture depth/shots/wall-clock |
| QSCI chem-acc to 28q; **40q operational @ 39 mHa** | scalability story, **not yet at chem acc @ 40q, not on GPU** | **execute the GPU MPS path → real 40q number** (primary criterion) |
| CrO/NiO **20q** (0.038 / 0.197 mHa) reproducible | real open-shell multireference chemistry | run on qBraid; **classical baseline + wall-clock** |
| HamLib equivalence 28/32/40q (exact) | reproducibility win | keep; cite as third-party-verifiable |
| Noise robustness 20q | noise-aware **bonus** | re-run on qBraid; tie to a real QPU if time permits |
| ~~Conditional encoder~~ cross-*molecule* (criterion 3) | **RESOLVED → negative** (within-noise tie vs warm-start) | reported honestly |
| **Cross-*size* transfer** (criteria 1, 3) | **DEMONSTRATED ✅ at 16q AND 20q** — H₆→H₈ beats random (mean 91.8 vs 127.6 mHa); H₄+H₆→H₁₀/20q beats random at matched determinant budget (QSCI 58.7 vs 73.9 mHa), all seeds | genuine scaling-transfer result; in paper |
| **Operator-pool compression** (criterion 3/4) | **DEMONSTRATED** — MP2 ranking keeps full-pool accuracy at 25–40% of doubles vs random collapse (~22×) | done; cite in write-up |
| **38q CrO/NiO ≤0.08 mHa claim (in finalist paper)** | **unsubstantiated, CPU-infeasible** | **substantiate on GPU OR correct — see §5** |
| Classical baselines presented as such | partial (have FCI/CCSD(T)/DMRG refs) | **package as explicit quantum-vs-classical + wall-clock** |
| qBraid-runnable repo + README + Launch button | **does not exist yet** | build it (criteria 7 & 8) |

**Bottom line:** our *science* is largely in hand and verified; the *Phase-3-shaped* work — **executing
on qBraid, producing a real 40q result, explicit classical baselines, and a re-runnable package** — is
mostly still ahead. That is exactly where criteria 1, 6, 7, 8 and all six Top Actions concentrate.

## 4. Recommended winning shape (five pillars, mapped to criteria)

1. **[Scalability — primary] Execute the 40q GQE/QSCI on qBraid GPU.** Take the CUDA-Q `tensornet-mps`
   path from "operational @ 39 mHa" to an **actually-run 40q result with wall-clock and resource
   numbers**. This is the headline and the primary criterion. Reaching (or credibly approaching)
   chemical accuracy at 40q on GPU is the win condition.
2. **[Accuracy + honesty] Real metal-oxide chemistry, executed + claim corrected.** Run CrO/NiO 20q on
   qBraid (reproducible today); **attempt 38q on GPU** and report the number we actually get. Convert
   the §5 exposure into a strength via Top-Action 6.
3. **[Mandatory] Classical baseline on every instance.** Present quantum-vs-classical (FCI/CCSD(T)/DMRG)
   with wall-clock, explicitly framed. Closes the "single most common gap."
4. **[Algorithmic innovation] Decide encoder vs. integration — early.** Run the decisive cross-family
   encoder experiment in week 1. If conditioning beats warm-start on a *dissimilar* target → headline
   it. If it ties again → drop it and lead innovation with the **integrated MPS + QSCI + operator-pool
   compression** scaling layer (genuinely beyond Kemmoku/Gao's QSCI-only 32q prior art — we add the
   tensor-network simulation tier).
5. **[Execution + Reproducibility] qBraid-runnable repo + README + Launch button.** Judges re-run with
   zero modification. This is criteria 7 & 8 and three of the six Top Actions.

## 5. The 38q ≤0.08 mHa claim — recommended resolution

The finalist paper §2 states CrO/NiO at **38q, ≤0.08 mHa**. Reality (audited): only **20q** exists
(CrO 0.038 ✓, **NiO 0.197 ✗** already above 0.08 at the easy scale); no 38q run exists; it is
CPU-infeasible. Phase 3 judges **re-run code** and reward **honesty over overstatement** (Top-Action 6),
and unreproducible claims get **zero credit**. Leaving "≤0.08 mHa @ 38q" as a headline is therefore the
single highest-risk item in the submission.

**Recommendation (needs team sign-off — it edits a finalist claim):**
- **Attempt** CrO/NiO at (or near) 38q on the qBraid GPU via MPS/QSCI. Report **whatever accuracy we
  actually achieve**, with wall-clock and resource numbers.
- **Reframe the headline** to *executed* results: real 20q CrO/NiO (genuine multireference chemistry) +
  the 38q GPU attempt as the **scaling demonstration**, not a pre-claimed ≤0.08 number. If the GPU run
  does reach ≤0.08, the claim becomes *substantiated* and we keep it — earned, not asserted.

## 6. Decisions that gate execution (need Christian/team)

1. **qBraid access — is the team account + credits live yet?** This is the critical path; GPU MPS runs
   take real wall-clock and we have 30 days. Everything in §4 depends on it.
2. **38q claim direction** (§5): attempt-on-GPU + reframe honestly (recommended) vs. defend as-is.
3. **Encoder:** authorize the week-1 decisive experiment to settle headline-or-drop.
4. **Cover page device selection:** select **qBraid (CPU/GPU + QPU)** for Phase 3. Confirm POC TypeForm
   done so credits actually land.

## 7. Suggested 30-day sequence (compresses if qBraid access slips)

- **Days 1–3:** confirm qBraid access; "Launch on qBraid" smoke test; port the QSCI/MPS scripts to run
  on qBraid GPU; run the decisive encoder experiment.
- **Days 4–12:** execute the scalability ladder on GPU (20 → 28 → 32 → 40q) with MPS; capture
  depth/shots/wall-clock; CrO/NiO 20q + 38q attempt.
- **Days 13–18:** classical baselines + quantum-vs-classical tables; optional IonQ/IBM QPU validation at
  10–16q; noise-aware run.
- **Days 19–25:** write the 5-page paper (numbers-first, honest limitations); build README + repo;
  judge dry-run reproducibility test.
- **Days 26–30:** buffer, internal review, package + submit zip well before the deadline.

## 8. Cross-references
- `paper_version_discrepancy.md` — the 38q exposure (§5 here is its resolution path).
- `phase3_spec_intake.md` — §1 here retires its GPU-vs-QPU risk.
- `reproducibility_audit_2026-06-21.md` — what is verified-reproducible today (our floor).
- `phase3_novelty_assessment.md` — encoder options A–E (pillar 4).
