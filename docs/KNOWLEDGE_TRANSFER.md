# EIGENNEXUS — MATGEN-Q · GIC/PQIC 2026 — KNOWLEDGE TRANSFER
### Phase 1 WON · Phase 2 submitted · **Phase 3 FINALIST**

**Purpose:** hand this project to a fresh chat. Read this top-to-bottom first — everything needed to continue is here. The accompanying `matgen-q/` folder is the complete codebase + paper (ready to push to GitHub); `matgen-q.bundle` is the same repo as a single clonable git file. Every result below traces to a script in `matgen-q/src/` and a JSON in `matgen-q/results/`.

---

## 0. STATUS & IMMEDIATE PRIORITIES — PHASE 3 (start here)

**We WON Phase 1 and have been SHORTLISTED to the Phase 3 FINAL** (selection email from Kieran Collinson, GIC team, June 2026). The Phase 2 submission described below is **DONE and is what advanced us** — treat it as the established foundation, not something to re-edit.

**Phase 3 logistics:** the Aqora pages are being updated; all Phase 3 requirements, **QC access instructions**, and submission details are due by the end of that week. The organizers' mention of provided "QC access" most likely means **hardware access is provided** — which resolves the long-open question of whether qBraid/IonQ/IBM validation was aspirational. **Phase 3 deadline: 26 July 2026.** GPU compute for Phase 3 is provided by the organizers.

**Phase 3 is decided on NOVELTY (rubric criterion 3) — the one thing capped throughout Phase 2.** Shortlisting validated rigor, scale, and clarity; *winning* requires demonstrating the novel contribution. Priorities, in order:

1. **Demonstrate the conditional encoder across ≥2 molecules** — THE novelty lever, and the only thing that materially raises the winning probability. The equivariant-GNN + transfer-learning encoder is currently *described, not demonstrated*. Show transfer (e.g. trained on one Sn-oxide → generalizing to another, or hydrogen → Sn-oxide with reduced training). It is long-lead and largely spec-independent — **start scoping it now**, before the Aqora spec lands.
2. **Run the real integrated GQE→QSCI→MPS pipeline at 20–40q on the provided GPUs**, with a Sn-oxide endpoint (not hydrogen) — converting the demonstrated 12q loop to target scale, with the wall-clock-vs-VQE and bond-dimension-vs-correlation curves the proposal promised.
3. **Materials benchmarks** — Sn₂O₃ (~28q), HfO₂/ZrO₂, tiered metrics + DLPNO-CCSD(T). This is where the **transition-metals HamLib thread** now belongs (far more valuable in Phase 3, with GPUs and no page limit): a HamLib-validated, strongly-correlated metal-oxide benchmark. If Christian uploads a transition-metal HDF5/zip file, read it (`h5py`), run QSCI (reuse `src/qsci_vec.py` / `src/gqe_qsci.py`), and report chemical accuracy honestly. Sweet spot ≤~24q on CPU; larger on the provided GPUs.
4. **Lock two team decisions** (Juan flagged): which molecule is the 40q endpoint (SnO₂ scaled up, or a specific Sn-oxo cluster)? and confirm hardware/QC access once Aqora updates.

**GitHub:** the codebase is now a git repo, **`matgen-q`** (README, `src/`, `paper/`, `results/`, `docs/`). Christian is connecting the GitHub connector for ongoing Phase 3 work — once available, use it to read and update the repo directly rather than passing files around.

**Do NOT build to exact Phase 3 requirements until the Aqora spec is published** — but priority 1 (the encoder demonstration) is spec-independent, so begin there.

---

## 1. WHO / WHAT / WHEN

- **Team EIGENNEXUS** (three people):
  - **Christian Metzl** — lead, connect@christianmetzl.com. German, based in Munich.
  - **Fares Eldibani** — faresdibany@gmail.com.
  - **Juan Manuel Aguiar Hualde** — PhD physicist; gives detailed scientific review.
- **Solution name: MATGEN-Q** (NO "QUATTRIVA" branding anywhere in the submission).
- **Competition:** GIC / PQIC 2026, **Mitsubishi Chemical Group & AIST**, **Advanced Materials** track, **Phase 2**.
- **Status: Phase 1 WON · Phase 3 FINALIST (shortlisted to the Final).** Phase 2 deadline **31 May 2026, 11:59 PM EST**. Phase 3 deadline **26 July 2026** (organizers provide GPU compute for Phase 3).
- **Submission platform:** Aqora.

## 2. HOW CHRISTIAN WANTS TO WORK (operating principles — important)

- Maximum effort; be **brutally honest**; **NEVER overclaim**; every claim must be **traceable and reproducible**.
- Only **winning or top-3** is an acceptable outcome — frame advice to that bar.
- He **approves changes item-by-item** — propose, wait for his go-ahead, then apply. Verify each external claim scientifically (don't take reviewer notes, including Juan's or Fares's, at face value — confirm or falsify).
- Respond with substance; stay steady and self-respecting (not submissive); **honest over flattering**. Do not inflate scores/probabilities just because he re-asks — hold the line and explain why.
- Keep numbers reproducible; if you state a result, it must come from a real run in the record.

## 3. PHASE 2 CHALLENGE SPEC

- Title of challenge: **"Scaling GQE Using NVIDIA CUDA-Q."** Target ~40 qubits ideal; 20–30q acceptable.
- **Format (hard):** official GIC **cover page** + **max 3 content pages** + **references**. 11pt Times New Roman, US Letter.
- **Rubric, in priority order:** 1. **Scalability (PRIMARY)**, 2. Accuracy (~1.6 mHa = chemical accuracy), 3. Algorithmic innovation, 4. Computational efficiency, 5. Hybrid system design, 6. Benchmarking, 7. Clarity/reproducibility. **Bonuses:** >40q scaling, noise-aware design.
- **Working assumption (drives scoring):** Phase 2 is the **proposal/feasibility** phase; **Phase 3** is where organizers give GPUs to run real CUDA-Q. So "no CUDA-Q runs yet" is expected and not heavily penalized. If this is wrong (Phase 2 expected real GPU runs), scalability/efficiency scores drop.

## 4. CURRENT SUBMISSION — FINAL STATE

**Final deliverables (in the zip and in /mnt/user-data/outputs/):**
- `EIGENNEXUS_Phase2_Submission.pdf` and `.docx` — **THE SUBMISSION**. 5 pages = official GIC cover (banner "PHASE 2 | May 31, 2026") + 3 content pages + references. PDF is the docx rendered (consistent). READY FOR AQORA.

**Title:** "MATGEN-Q: Scaling Conditional GQE for EUV Photoresist Discovery to ~40 Qubits with NVIDIA CUDA-Q." Subtitle: Team EIGENNEXUS — Advanced Materials (Mitsubishi Chemical Group & AIST) — GIC 2026 Phase 2.

**Content map:**
- **§1 Focus & Rationale** — GQE (Nakaji 2024, AIST) replaces variational optimization, sidesteps barren plateaus; statevector GQE stayed small-scale, QSCI-paired GQE only recently reached 32q (Kemmoku/Gao 2026, Mitsubishi); thesis = scaling this generative approach to ~40q. Phase-1 identity (conditional-GQE pipeline: AI proposes metal-oxide molecules → DFT filters → GQE refines → Bayesian optimization). EUV target (Sn/Hf/Zr oxides). Industry framing ($800B+ semis, ~20% CAGR, MFBO 3× cost reduction [Fare 2022]).
- **§2 Target System & Data** — linear Hₙ chains (4–40q, STO-6G, JW) as scaling vehicle. **HamLib validation** (see §6 below). **Reference hierarchy** (CCSD(T)/DMRG — see §5 edits). **SnO/SnO₂ Sn-oxide bridge** (the materials evidence — see §5 edits).
- **§3 GQE Approach** — two-stage GQE (GPT-QE transformer structure discovery + adjoint-gradient refinement) + Phase-1 conditional encoder. **Four scaling pillars:** (1) MPS tensor-network [primary], (2) QSCI evaluation [+ demonstrated noise robustness], (3) operator-pool compression (MP2+symmetry), (4) distributed mqpu. Honestly attributes GQE+QSCI prior art to Kemmoku/Gao.
- **§4 Hybrid Architecture + Figure 1** (`matgenq_arch.png`, embedded at width:372 height:264).
- **§5 Demonstrated Results** — Table 1 (two-stage GQE 4–12q), the **integrated GQE→QSCI 12q result**, Table 2 (QSCI scaling to 28q + 40q operational), Phase 3 plan (3-liner).
- **§6 Platform Justification** — bottlenecks (eval cost via QSCI; 40q memory ~16TB via MPS); request NVIDIA H100/A100 80GB + CUDA-Q, tensornet-mps 24–40q, cuStateVec ≤32q, 4–8 NVLink GPUs for >40q bonus, qBraid 10–16q; ~2 weeks GPU wall-clock.
- **References [1–9]** — all verified (see §10).

## 5. EDITS MADE THIS SESSION (all applied, all in the final files)

1. **Juan item 1** — fixed §1 internal inconsistency: removed blanket "demonstrations stop at ~10–12 qubits"; now "statevector GQE stayed small-scale, QSCI-paired GQE only recently reached 32 qubits (Kemmoku, Gao et al. 2026)"; thesis reframed to "~40-qubit regime." (Verified: Kemmoku/Gao arXiv:2604.09756 reaches 32q on N₂.)
2. **Juan item 2** — ref [7] now "npj Computational Materials 8, **257** (2022)." (Verified via Nature/ADS Bibcode 2022npjCM...8..257F.)
3. **Juan item 3** — ref [5] CUDA-Q now ends "(accessed May 2026)" (no invented version string).
4. **Juan item 7** — captions define terms: Table 1 "Corr. (%) = fraction of correlation energy recovered"; Table 2 "Subspace/CI space = selected determinants ÷ full CI space."
5. **Juan item 8** — Table 2 "40q runs and converges" → "40q operational (converging through 39 mHa)" so it can't be read as a chemical-accuracy claim.
6. **Fares CCSD(T)/DMRG reference-hierarchy fix** — §2 now: "FCI exactly (≤20q), and at larger sizes CCSD(T) near equilibrium where it is reliable, with DMRG — verified to reproduce FCI to 0.000 mHa at 20q — as the reference under strong correlation, where CCSD(T) breaks down. Its H₁₀ error versus FCI grows from 0.17 mHa at equilibrium to 227 mHa at 2.5 Å…" (Precision/wording fix — the science was already correct; scaling demos are at equilibrium R=0.74 where CCSD(T) is accurate.)
7. **Integrated GQE→QSCI 12q result added to §5** (the #1 improvement — closes the GQE-to-QSCI disconnect). NEW experiment this session (see §7).
8. **SnO/SnO₂ added to §2** (the EUV-bridge improvement). Real runs (see §7). Honestly framed as our own ECP-CASCI construction (NOT HamLib-sourced), with "(perturbative QSCI, §5)" caveat.

**Items deliberately NOT done (Christian's calls / page limit):** validation appendix (page-limited); full Phase 3 plan expansion (page-limited). Note: SnO/SnO₂ was declined twice earlier then added in the final round.

## 6. HAMLIB VALIDATION (bulletproof — already in the paper)

Christian uploaded real HamLib R=0.70 files (H14/H16/H20 linear chains). We regenerated ours at R=0.70 via PySCF+OpenFermion JW. **Result: EXACT term-count match (27,735 / 47,489 / 116,577 terms at 28/32/40q); one-norms match to ~15 sig figs; identical Pauli-term sets; ALL coefficient differences are EXACT sign-flips with identical magnitude multiset (max diff ~1e-13) → pure orbital-phase gauge, spectrum-invariant.** Conclusion stated in §2: "our generated Hamiltonians match HamLib exactly in term count and to ~15 significant figures… differing only by a spectrum-invariant orbital-phase convention." Reading HamLib HDF5: `h5py.File(f,'r',libver='latest')['ham_JW'][()].decode()` (scalar bytes, OpenFermion string; H20 uses complex `(x+0j)` coeff format → `.strip('()')` + `complex().real`).

## 7. VERIFIED COMPUTATIONAL RESULTS (every number is from a real run; all in evidence JSONs)

**Scaling ladder (STO-6G, R=0.74):** H2/4q FCI −1.145940 · H4/8q −2.156857 · H6/12q −3.170505 · H8/16q FCI −4.186089 · H10/20q −5.202826 · H14/28q CCSD(T) −7.237790 · H16/32q −8.255886 · H20/40q −10.292650.

**Two-stage GQE (PennyLane lightning.qubit, GPTQE):** H2 0.146 mHa · H4 0.009 mHa · H6 0.298 mHa. (PennyLane needs BOHR coords ×1.8897259886.) → `gqe_scaling.py`, `gqe_scaling_results.json`.

**QSCI / selected-CI (chemical accuracy to 28q):** H4 8q 0.286 mHa · H6 12q 1.166 mHa · H10 20q 0.570 mHa (2,401 dets, 3.8% FCI) · **H14 28q 1.213 mHa (18,201 dets, 0.15% FCI)**. H20 40q: operational, 39.3 mHa at 1,601 dets (CPU-bound by 116,577-term Hamiltonian). → `qsci_vec.py`, `qsci_ck.py`, `qsci_scaling_evidence.json`.

**Integrated GQE→QSCI pipeline at 12q (H6) — THE KEY NEW RESULT:** GPT-QE generates circuits; QSCI samples determinants FROM the generated states via `qml.sample` (real measurement, not perturbative selection); 141 distinct determinants pooled across 161 GQE-generated circuits; diagonalize → **−3.169451 Ha = 1.05 mHa (chemical accuracy)**, refining the raw GQE expectation (−3.119043 = 51 mHa) **~50×**. This is the actual Kemmoku/Gao-style pipeline. → `gqe_qsci.py`, `gqe_qsci_evidence.json`. **NOTE:** 16q+ was infeasible in-sandbox (term-by-term expval too slow AND `get_sparse_operator` OOM at 16q). 12q is the demonstrated integrated scale; larger is Phase 3.

**Noise robustness (demonstrated):** QSCI at 20q, fixed subspace, frequency-based determinant selection. Error: p=0 → 1.51 mHa; p=0.10 → 2.58 mHa; **p=0.30 → 3.30 mHa** (graceful degradation). → `noise_demo2.py`, `noise_evidence.json`.

**DMRG tensor-network (reference validation):** H10 20q DMRG reproduces FCI EXACTLY (0.000 mHa) — justifies DMRG as the strong-correlation reference. H24 48q: runs, 6.83 mHa at bond M=250 (bond-dim-limited; NOT in paper, page-limited). → `dmrg_scale.py` (block2/pyblock2), `dmrg_evidence.json`.

**Materials — SnO/SnO₂ (the EUV bridge, in §2):** PySCF RHF def2-ECP on Sn → CASCI → OpenFermion JW → QSCI; construction validated on H4 to 0.0000 mHa. **SnO CAS(8,8) 16q/2329 terms FCI −288.159492 → QSCI 0.113 mHa (cited 0.11), 901 dets; SnO₂ CAS(10,10) 20q/3151 terms FCI −362.865073 → QSCI 0.225 mHa (cited 0.23), 1201 dets.** Same perturbative-selection proxy as the Hₙ QSCI. → `sno_demo.py`, `sno2_demo.py`, `materials_ham.py`, `materials_evidence.json`. **These are OUR construction, NOT HamLib (HamLib has no tin oxides).**

## 8. HOW TO REBUILD THE PAPER

The paper is generated by a Node script (docx-js), NOT hand-edited docx:
```
node build_phase2.js            # → EIGENNEXUS_Phase2_Content.docx (3 content pages + refs)
python3 /mnt/skills/public/docx/scripts/office/soffice.py --headless --convert-to pdf EIGENNEXUS_Phase2_Content.docx
python3 -c "from pypdf import PdfReader; print(len(PdfReader('EIGENNEXUS_Phase2_Content.pdf').pages))"   # must be 4 (3 content + refs)
# prepend the cover:
python3 -c "from docxcompose.composer import Composer; from docx import Document; m=Document('phase1_cover_v2.docx'); c=Composer(m); c.append(Document('EIGENNEXUS_Phase2_Content.docx')); c.save('EIGENNEXUS_Phase2_Submission.docx')"
python3 /mnt/skills/public/docx/scripts/office/soffice.py --headless --convert-to pdf EIGENNEXUS_Phase2_Submission.docx   # → 5 pages total
```
- `build_phase2.js` text is written as docx-js `T("...")` runs; edit strings there. Em-dash = `\u2014`, en-dash `\u2013`, ≤ `\u2264`, × `\u00d7`, § `\u00a7`, Å `\u00C5`, subscripts like H₁₀ use `\u2081\u2080`.
- `phase1_cover_v2.docx` = the official GIC cover with the "PHASE 2 | May 31, 2026" banner and a trailing page break (the trailing break is what keeps content on page 2 — docxcompose does NOT auto-insert one).
- **Page discipline:** content must stay at **3 pages**. Current build has a comfortable margin (§6 ends ~80% down page 3). Figure is at 372×264 (shrunk to make room for SnO/SnO₂). If you add text, trim verbose passages or shrink the figure slightly; re-check page count every time.

## 9. ENVIRONMENT / GOTCHAS

- Sandbox resets between sessions. Reinstall: `pip install pyscf openfermion openfermionpyscf h5py pennylane pennylane-lightning torch matplotlib quimb block2 python-docx docxcompose scipy --break-system-packages --no-cache-dir`.
- Working versions: pyscf, openfermion 1.7.1, pennylane 0.45, torch, h5py, quimb, block2/pyblock2, numpy 2.4.4 (**NO `np.bit_count`** — use a byte-lookup popcount, see `qsci_vec.py`), python-docx, docxcompose, pypdf.
- **`get_sparse_operator` OOMs at 16q** (use ≤12q for sparse matvec energy). Term-by-term `expval` of a molecular Hamiltonian is the speed wall (this is the paper's whole point — motivates QSCI).
- Tool timeout ~290s; for long runs use file-logging + an internal guard (`time.time()-t0 > 235`) + checkpointing.
- Network for bash allows pypi/files.pythonhosted; the HamLib NERSC portal is NOT in the bash allow-list (download files via the chat upload, or `web_fetch` a direct URL the user pastes).

## 10. REFERENCES (all verified this session)
[1] Nakaji et al., GQE, arXiv:2401.09253 (2024, AIST; N₂ proof-of-concept, small scale).
[2] Sawaya et al., HamLib, Quantum 8, 1559 (2024), arXiv:2306.13126.
[3] Minami/Nakaji, conditional-GQE, Digital Discovery 4(8) 2229–2243 (2025).
[4] Kanno et al., QSCI, arXiv:2302.11320 (2023).
[5] NVIDIA CUDA-Q, https://developer.nvidia.com/cuda-q (accessed May 2026).
[6] Tilly et al., VQE review, Phys. Rep. 986 (2022).
[7] Fare et al., MFBO, **npj Computational Materials 8, 257 (2022)**.
[8] Kharazi et al., EUV photolithography, arXiv:2602.20234 (2026, Xanadu & Mitsubishi).
[9] Kemmoku, Gao, Kanno et al., "Generative Circuit Design for QSCI," arXiv:2604.09756 (2026, Mitsubishi — reaches **32q** on N₂; the providers' own team; the novelty-ceiling source).

## 11. HONEST SCORING (current, /10) & PROBABILITIES

1. Scalability (PRIMARY) **7** — 28q chem acc + 40q operational + real integrated loop at 12q; gap: integrated pipeline shown at 12q, 28q is validated proxy, 40q sub-chemical-accuracy.
2. Accuracy **7.5**.
3. Algorithmic innovation **5.5** — **BINDING CONSTRAINT.** GQE+QSCI→32q is the providers' own (Kemmoku/Gao); MPS + pool compression standard; the novel **conditional encoder (equivariant GNN + transfer) is described, NOT demonstrated**.
4. Computational efficiency **6.5** — logic sound, gains argued not measured (no GPU yet).
5. Hybrid design **7**.
6. Benchmarking **8** — bulletproof HamLib match + now-rigorous reference hierarchy.
7. Clarity/reproducibility **7.5**.
Bonuses: noise-aware **strong** (demonstrated); >40q **partial** (40q operational; 48q DMRG not in paper).
**Weighted ≈ 7.1/10.**

- **Shortlist into Phase 3: ~67–73%.** (Was ~65–72%; SnO/SnO₂ nudged it up — concrete industrial bridge.) If Phase 2 expected real CUDA-Q runs: ~45–55%.
- **Win / top-3: ~12–17%. Capped HARD by novelty (criterion 3).** Only Phase 3 work moves it. Do NOT inflate this on re-ask.

**Two weaknesses that gate everything:** (1) novelty pre-empted + novel encoder undemonstrated; (2) full-scale integration (real loop at 12q; 28–40q is proxy/sub-accuracy). The Sn-oxides and integrated 12q result raised the FLOOR, not the winning CEILING.

## 12. HAMLIB PORTAL

`https://portal.nersc.gov/cfs/m888/dcamps/hamlib/` — folders: `chemistry/` (relevant), `condensedmatter/`, `binaryoptimization/`, `discreteoptimization/`, plus `readme.txt`, `hamlib_snippets.py`. Chemistry = molecular electronic structure (NIST geometries, frozen-core options, multiple qubit counts, `ES_<molecule>_..._ham` HDF5 naming). **HamLib has NO tin oxides / EUV materials.** The `transition_metals` subset (Christian's lead) is the next thing to pull — see §0. For Phase 3: download chemistry/ ES files for benchmark molecules + `readme.txt`/`hamlib_snippets.py` to lock the HDF5 dataset keys + frozen-core conventions; contribute our Sn-oxides in HamLib format for the reproducibility requirement.

## 13. PHASE 3 ROADMAP (if we advance)

- **Run the integrated GQE→QSCI→MPS pipeline at 20–40q on the provided GPUs**, with Sn-oxides (not hydrogen) as the endpoint.
- **Demonstrate the conditional encoder** (NequIP/equivariant GNN + 3-stage transfer) across ≥2 molecules — THE novelty mover (per Fares's workflow diagram and Juan's matgen-q.zip from prior sessions).
- Materials clusters (Sn₂O₃ 28q, HfO₂/ZrO₂) with tiered metrics + DLPNO-CCSD(T); MFBO loop + composite reward.
- Benchmark vs DMRG/CCSD(T) and wall-clock vs VQE; validate selected circuits on IonQ/IBM via qBraid at 10–16q.
- **Open questions Juan needs from Christian:** (a) which molecule is the 40q endpoint (SnO₂ scaled up, or a specific Sn-oxo cluster)? (b) is qBraid/hardware access real or aspirational?

---
*End of knowledge transfer. The zip contains: this file, the final submission (PDF+DOCX), the build script + cover + figure, all evidence JSONs, and all analysis code.*
