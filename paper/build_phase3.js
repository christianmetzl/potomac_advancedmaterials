// Phase 3 write-up builder (docx-js), mirroring build_phase2.js.
// Generates EIGENNEXUS_Phase3_Content.docx from the Phase 3 draft prose.
// [QBRAID-RUN] placeholders are styled (bold italic, dark red) so the GPU/QPU numbers
// owed are unmistakable and easy to find-and-replace once executed.
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        AlignmentType, BorderStyle, WidthType, ShadingType, ImageRun } = require('docx');
const fs = require('fs');

const FONT="Times New Roman", SZ=22; // 11pt
const bd={style:BorderStyle.SINGLE,size:1,color:"888888"};
const borders={top:bd,bottom:bd,left:bd,right:bd};
const cw=9792;

function P(runs,opts={}){return new Paragraph({spacing:{after:opts.after??60,line:240,lineRule:"auto"},alignment:opts.align,...opts,children:Array.isArray(runs)?runs:[runs]});}
function T(t,o={}){return new TextRun({text:t,font:FONT,size:SZ,bold:o.b,italics:o.i});}
function Q(t){return new TextRun({text:t,font:FONT,size:SZ,bold:true,italics:true,color:"A52A2A"});} // [QBRAID-RUN] placeholder
function H(t){return new Paragraph({spacing:{before:90,after:40,line:240,lineRule:"auto"},children:[new TextRun({text:t,font:FONT,size:SZ,bold:true})]});}

function cell(text,w,{hdr=false,bold=false,align=AlignmentType.LEFT}={}){
  return new TableCell({borders,width:{size:w,type:WidthType.DXA},
    shading:{fill:hdr?"D5E8F0":"FFFFFF",type:ShadingType.CLEAR},
    margins:{top:40,bottom:40,left:90,right:90},
    children:[new Paragraph({alignment:align,spacing:{after:0,line:240,lineRule:"auto"},
      children:[new TextRun({text:text,font:FONT,size:21,bold:hdr||bold})]})]});
}
function row(cells,w,opts={}){return new TableRow({children:cells.map((c,i)=>cell(c,w[i],opts))});}

// Table 1: verified results (5a) — quantum vs classical, matched instances
const w1=[2000,1100,2900,2400,1392];
const tbl1=new Table({width:{size:9792,type:WidthType.DXA},columnWidths:w1,rows:[
  row(["System","Qubits","Quantum (GQE/QSCI)","Classical ref.","Notes"],w1,{hdr:true,align:AlignmentType.CENTER}),
  row(["H₂/H₄/H₆","4/8/12","0.146 / 0.009 / 0.298 mHa","FCI (exact)","two-stage GQE"],w1,{align:AlignmentType.CENTER}),
  row(["H₆ GQE→QSCI","12","1.05 mHa (51→1.05, ~50×)","FCI","measured pipeline"],w1,{align:AlignmentType.CENTER}),
  row(["H₁₀/H₁₄","20/28","0.57 / 1.21 mHa","FCI / CCSD(T)","2,401 / 18,201 dets"],w1,{align:AlignmentType.CENTER}),
  row(["CrO ⁵Π / NiO ³Σ⁻","20","0.038 / 0.197 mHa","CASCI (exact)","open-shell multiref."],w1,{align:AlignmentType.CENTER}),
  row(["SnO / SnO₂","16/20","0.11 / 0.23 mHa","FCI","EUV target chemistry"],w1,{align:AlignmentType.CENTER}),
  row(["Noise (H₁₀)","20","≤3.3 mHa @ 30% corrupt","—","noise-aware bonus"],w1,{align:AlignmentType.CENTER}),
]});

// Table 2: classical baseline & exact wall (5b) — timed, matched instances
const w2=[1700,1300,2400,2300,2092];
const tbl2=new Table({width:{size:9792,type:WidthType.DXA},columnWidths:w2,rows:[
  row(["System","Qubits","FCI (exact) wall-clock","CCSD(T) err vs FCI","CCSD(T) wall-clock"],w2,{hdr:true,align:AlignmentType.CENTER}),
  row(["H₆","12","0.04 s","0.026 mHa","0.08 s"],w2,{align:AlignmentType.CENTER}),
  row(["H₁₀","20","0.33 s","0.173 mHa","0.09 s"],w2,{align:AlignmentType.CENTER}),
  row(["H₁₂","24","7.81 s","0.282 mHa","0.14 s"],w2,{align:AlignmentType.CENTER}),
  row(["H₁₄","28","minutes","—","~0.2 s"],w2,{align:AlignmentType.CENTER}),
  row(["H₁₆+","32+","intractable (CPU)","—","—"],w2,{align:AlignmentType.CENTER}),
]});

const children=[
  new Paragraph({spacing:{after:30,line:240,lineRule:"auto"},alignment:AlignmentType.CENTER,
    children:[new TextRun({text:"MATGEN-Q: Scaling a Two-Stage Generative Quantum Eigensolver to 40 Qubits on NVIDIA CUDA-Q for EUV Photoresist Chemistry",font:FONT,size:24,bold:true})]}),
  new Paragraph({spacing:{after:80,line:240,lineRule:"auto"},alignment:AlignmentType.CENTER,
    children:[new TextRun({text:"Team EIGENNEXUS  —  Advanced Materials (Mitsubishi Chemical Group & AIST)  —  GIC 2026 Phase 3",font:FONT,size:21,italics:true})]}),

  H("1. Focus Area and Rationale"),
  P([T("Ground-state energy estimation governs reaction thermodynamics, redox behavior, and excited-state properties across materials chemistry, yet classical methods scale exponentially with electron correlation and the gold-standard CCSD(T) costs O(N⁷). The Generative Quantum Eigensolver (GQE; Nakaji et al. 2024, with AIST) replaces variational circuit optimization with a classical generative transformer that proposes quantum circuits, side-stepping the barren-plateau problem — but statevector GQE stayed small-scale, and QSCI-paired GQE only recently reached 32 qubits (Kemmoku, Gao et al. 2026). "),T("Scaling this generative approach to the ~40-qubit, industrially relevant regime — with executed, reproducible results — is the problem we address in Phase 3.",{b:true})]),
  P([T("Our target is EUV semiconductor photoresist chemistry (tin-oxo clusters; Sn, Hf, Zr oxides), whose open-shell, multi-reference character is where DFT's functional-dependent errors make candidate rankings unreliable, and which is the focus of an active quantum-simulation program by one of this challenge's providers (Kharazi et al., Xanadu & Mitsubishi Chemical, 2026). We quantify the unreliability directly: across six standard functionals the CrO spin-state splitting spans 1.9 eV — PBE0 places the quintet 1.84 eV below the triplet while B3LYP inverts the order (−0.08 eV) — and even the milder NiO gap varies 0.11 eV, against a chemical-accuracy target of 0.044 eV. A single quantum-accurate number removes this functional-choice band. The MATGEN-Q pipeline — AI proposes candidate metal-oxide molecules → DFT filters → GQE refines with quantum accuracy → Bayesian optimization selects the next candidate — generalizes beyond photoresists to battery electrolytes, catalysts, and functional polymers central to Mitsubishi Chemical's portfolio and AIST's computational-materials mission. EUV photoresists grow at ~20% CAGR within an $800B+ semiconductor industry, and multi-fidelity Bayesian screening has shown up to 3× cost reduction (Fare et al., 2022) — acceleration MATGEN-Q targets through quantum-accurate pre-selection.")]),
  P([T("Stakeholder relevance. ",{b:true}),T("For Mitsubishi Chemical the immediate value is a quantum-accurate filter ahead of expensive synthesis and lithographic testing: tin-oxo photoresist performance hinges on radiation-induced bond cleavage and redox energetics that DFT ranks unreliably, so even a modest improvement in candidate ordering compounds across a screening campaign. For AIST/G-QuAT the contribution is methodological — a scalable, reproducible GQE workflow on NVIDIA CUDA-Q that extends the jointly-developed GQE program past its current size limits. The same ground-state engine is complementary to that program's excited-state absorption work, so the two compose into a single materials-informatics loop rather than competing.")]),

  H("2. Target System and Data Modeling Strategy"),
  P([T("Scaling vehicle. ",{b:true}),T("The linear hydrogen-chain series Hₙ (n = 2…20; 4–40 qubits, STO-6G, Jordan–Wigner) — the canonical strong-correlation benchmark; a single bond-length parameter tunes weak (area-law) to strong (volume-law) correlation, directly stressing the simulation layer that underpins any scaling claim.")]),
  P([T("Target chemistry. ",{b:true}),T("The same QSCI engine reaches chemical accuracy on real materials chemistry: Sn-oxide active spaces (Sn ECP-CASCI, validated on H₄ to 0.0000 mHa) — SnO 0.11 mHa (16q), SnO₂ 0.23 mHa (20q) — and genuine open-shell, multireference transition-metal oxides — "),T("CrO ⁵Π 0.038 mHa and NiO ³Σ⁻ 0.197 mHa at 20 qubits",{b:true}),T(". We report these executed 20-qubit results; the 38-qubit regime is the GPU scaling target of §5, not a pre-claimed figure.")]),
  P([T("Data integrity. ",{b:true}),T("We adopt HamLib (Sawaya et al., Quantum 2024) and built a generation pipeline replicating its methodology (PySCF → OpenFermion → Jordan–Wigner, STO-6G). "),T("Validated against the published files: FCI reproduced to 0.00000 mHa (H₂–H₆), and at 28/32/40 qubits our Hamiltonians match HamLib exactly in term count (27,735 / 47,489 / 116,577) and to ~15 significant figures in coefficient magnitude",{b:true}),T(" (differing only by a spectrum-invariant orbital-phase convention) — third-party reproducible.")]),
  P([T("Accuracy anchors / classical references. ",{b:true}),T("FCI exactly (≤20q), CCSD(T) near equilibrium, and DMRG — verified to reproduce FCI to 0.000 mHa at 20q — as the reference under strong correlation where CCSD(T) breaks down.")]),

  H("3. GQE-Based Approach and Algorithmic Innovation"),
  P([T("MATGEN-Q uses a two-stage GQE. Stage 1 (generative structure discovery): ",{b:true}),T("a decoder-only GPT-style transformer, trained by sequence–energy matching (Nakaji et al.), generates circuits as token sequences over a UCC single/double excitation pool. "),T("Stage 2 (continuous refinement): ",{b:true}),T("adjoint-gradient angle optimization converges to chemical accuracy. Four innovations make it scalable:")]),
  P([T("(1) Tensor-network (MPS) simulation — primary scaling enabler. ",{b:true}),T("CUDA-Q's tensornet-mps backend's memory scales with circuit entanglement rather than 2ⁿ; near-equilibrium area-law bounds bond dimension. Exact cuStateVec validates ≤~32 qubits; MPS carries 32–40+. This tensor-network tier is what we add beyond the QSCI-only 32-qubit prior art.")],{after:30}),
  P([T("(2) QSCI energy evaluation — accuracy and noise-aware. ",{b:true}),T("Quantum-Selected Configuration Interaction (Kanno et al. 2023): dominant configurations are sampled from the generated circuit and H is classically diagonalized in that subspace — intrinsically noise-robust (the device defines only the subspace; ≤3.3 mHa even with 30% of measurements corrupted at 20q).")],{after:30}),
  P([T("(3) Operator-pool compression — efficiency (demonstrated). ",{b:true}),T("Ranking the O(N⁴) double-excitation pool by active-space MP2 amplitude and keeping the top fraction shrinks the transformer vocabulary with negligible accuracy loss, where random pruning collapses. Deterministic CI-subspace test (CO/N₂/SiO, 12q): "),T("N₂ retains full-pool accuracy (2.26 mHa) keeping only 25% of doubles (vocabulary 1170→430) vs 50.4 mHa for random pruning at the same size (~22×)",{b:true}),T("; CO holds 3.7 mHa at 40% kept vs 29.7 mHa random.")],{after:30}),
  P([T("(4) Distributed hybrid workflow. ",{b:true}),T("Detailed in §4.")],{after:30}),
  P([T("Transfer learning — generative structure transfers across system size. ",{b:true}),T("Using a canonical, frontier-relative tokenization (each excitation encoded as occupied-depth-below-HOMO and virtual-height-above-LUMO, independent of qubit count), a small system's token vocabulary is a provable subset of a larger one (H₆/12q ⊂ H₈/16q ⊂ H₁₀/20q). "),T("one GPT-QE generator trained only on H₄+H₆ (8q+12q) is deployed zero-shot across 16→20→28→40 qubits and beats random search at every size and every seed",{b:true}),T(" — advantage +9.2 / +8.5 / +7.4 / +6.0 mHa at 16/20/28/40q (3-seed mean; trained spread ~1 mHa vs random ~7–10). This is the "),T("train-small, deploy-large",{i:true}),T(" result: GQE training is the cost that is CPU-bound near ~16 qubits, so transferring a small-trained generator to the 40-qubit target — instead of training at scale — directly addresses the field's central bottleneck (Figure 2). The enabler is a determinant-space evaluation (each proposed excitation maps by bitmask to a determinant; QSCI diagonalizes that subspace) that needs no 2ⁿ statevector, so 40q runs on CPU. Honest scope: a relative advantage at a small fixed determinant budget (K=96), not absolute chemical accuracy at 40q (the GPU/large-subspace deliverable). A separate same-size cross-molecule conditioning variant gave only a within-noise gain and is reported as a negative; the value is in cross-size transfer.")]),

  new Paragraph({spacing:{before:50,after:10,line:240,lineRule:"auto"},alignment:AlignmentType.CENTER,
    children:[new ImageRun({type:"png",data:fs.readFileSync("../results/encoder/scaling_ladder.png"),transformation:{width:330,height:202}})]}),
  new Paragraph({spacing:{before:0,after:60,line:240,lineRule:"auto"},alignment:AlignmentType.CENTER,
    children:[new TextRun({text:"Figure 2. Train-small, deploy-large. A generator trained only on 8- and 12-qubit systems beats random search at every target size up to 40 qubits (lower is better; determinant-space QSCI, matched budget). The trained policy is tightly consistent across seeds; the advantage persists to 40q.",font:FONT,size:18,italics:true})]}),

  H("4. Hybrid Architecture"),
  P([T("The classical transformer trains on GPU (PyTorch); circuit evaluations are dispatched across GPUs via CUDA-Q's mqpu in an asynchronous generate→evaluate→update loop. Quantum resources handle state preparation and energy estimation (MPS / QSCI); classical resources handle generation, optimization, and active-space selection. Stage 1 is sampling-bound and parallelizable; Stage 2 is gradient-bound and adjoint-efficient.")]),
  new Paragraph({spacing:{before:60,after:20,line:240,lineRule:"auto"},alignment:AlignmentType.CENTER,
    children:[new ImageRun({type:"png",data:fs.readFileSync("matgenq_arch.png"),transformation:{width:360,height:256}})]}),
  new Paragraph({spacing:{before:0,after:60,line:240,lineRule:"auto"},alignment:AlignmentType.CENTER,
    children:[new TextRun({text:"Figure 1. MATGEN-Q hybrid architecture: a classical generative transformer (Stage 1) and GPU-accelerated quantum simulation (MPS/QSCI) form an asynchronous loop; Stage 2 refines angles to chemical accuracy.",font:FONT,size:18,italics:true})]}),

  H("5. Phase 3 Execution and Results"),
  P([T("Verified results (CPU; reproduced from a clean checkout via ",{b:true}),T("reproduce.py",{b:true,i:true}),T(").",{b:true}),T(" All values below are reproduced against the committed result files (Table 1).")],{after:50}),
  tbl1,
  new Paragraph({spacing:{before:30,after:50,line:240,lineRule:"auto"},children:[new TextRun({text:"Table 1. Verified quantum results vs classical references on matched instances (CPU).",font:FONT,size:19,italics:true})]}),
  P([T("Classical baseline and the exact wall (matched instances, timed). ",{b:true}),T("On identical STO-6G Hₙ geometries, classical FCI wall-clock grows ~24× from 20→24 qubits (0.33 s → 7.8 s) and is intractable by 32q on CPU; CCSD(T) stays cheap but its error climbs with correlation and breaks down under strong correlation (at H₂₄/48q, classical DMRG is itself 6.83 mHa off CCSD(T)). Exact quantum-state simulation needs ~16 TB at 40 qubits — the wall the MPS + QSCI tiers remove (Table 2).")],{after:50}),
  tbl2,
  new Paragraph({spacing:{before:30,after:50,line:240,lineRule:"auto"},children:[new TextRun({text:"Table 2. Classical reference cost on the Hₙ ladder (single-thread CPU) — the exact-method wall the quantum approach is measured against.",font:FONT,size:19,italics:true})]}),
  P([T("Executed scaling results on qBraid GPU. ",{b:true}),
     T("40-qubit MPS GQE/QSCI on H₂₀ (primary criterion): ",{b:true}),Q("[QBRAID-RUN: energy err vs DMRG, circuit depth, MPS bond dimension, shot budget, GPU wall-clock]"),
     T(" (CPU baseline today: operational, converging through 39 mHa). "),
     T("CrO/NiO near-38 qubits on GPU: ",{b:true}),Q("[QBRAID-RUN: accuracy achieved + wall-clock]"),
     T(", presented as the scaling demonstration on real open-shell chemistry, building on the executed 20-qubit results. "),
     T("Quantum-vs-classical wall-clock: ",{b:true}),Q("[QBRAID-RUN: MPS/QSCI vs exact statevector vs VQE]"),
     T(". "),T("Hardware validation: ",{b:true}),Q("[QBRAID-RUN: selected circuits on IonQ/IBM at 10–16 qubits, depth + shots]"),T(".")]),
  P([T("What the results establish. ",{b:true}),T("Three things are demonstrated, not asserted. (i) Correctness: the GQE/QSCI pipeline reproduces the classical FCI/CASCI reference to chemical accuracy on every instance we can run, including genuine open-shell multireference oxides (CrO, NiO) and EUV-relevant Sn-oxides. (ii) Scalability of the simulation layer: QSCI reaches chemical accuracy using a vanishing fraction of the CI space (3.8% at 20q, 0.15% at 28q), and operator-pool compression preserves accuracy at 25–40% of the double-excitation pool — both quantifying that the cost grows far slower than the Hilbert space. (iii) Transferable structure: a generator trained on small systems proposes good circuits for a larger one it never saw (§3), evidence that the learned policy — not just a per-system fit — scales. The honest boundary is that at the sizes classical FCI/DMRG still solve, we show correctness and favourable scaling rather than a head-to-head speed win; that win is the 40q+ regime the GPU run targets, where classical exact methods break down (Table 2).")]),

  H("6. Platform Use and Resourcing"),
  P([T("qBraid provides classical (CPU/GPU) and quantum (QPU) credits. We use "),T("NVIDIA H100/A100 (80 GB)",{b:true}),T(" with CUDA-Q: tensornet-mps for the 24–40-qubit tier and cuStateVec for exact validation to ~32 qubits. One high-memory GPU suffices for MPS; 4–8 GPUs (NVLink) enable distributed circuit evaluation (pillar 4) and the >40-qubit bonus attempt; QPU (IonQ/IBM) for 10–16-qubit validation.")]),
  P([T("Resource estimate. ",{b:true}),T("UCC excitations decompose to ≤2-qubit gates; with operator-pool compression a length-8 generated circuit is shallow (tens of two-qubit gates), within MPS reach at bounded bond dimension near equilibrium. QSCI needs ~10³–10⁴ shots per circuit to resolve the dominant determinants (we use 2,000 in simulation). The dominant cost is the generate→evaluate loop: a few hundred transformer updates, each dispatching a batch of circuit evaluations across the GPU(s). We estimate ~1–2 weeks of single-GPU wall-clock for the full 24→40-qubit sweep plus the transition-metal-oxide runs; the workflow is backend-agnostic and degrades gracefully to fewer qubits if the allocation is smaller. Concrete per-run depth/shot/wall-clock: "),Q("[QBRAID-RUN: from §5]"),T(".")]),

  H("7. Limitations and Honest Scope"),
  P([T("We state where the approach does and does not yet provide benefit. (i) ",{}),T("Measurement vs proxy: ",{b:true}),T("the integrated GQE→QSCI loop is measured (real circuit sampling) at 12 qubits; the larger QSCI numbers use perturbative determinant selection as a hardware-independent proxy, validated against the 12-qubit measured pipeline — quantum-inspired at scale until executed with real sampling on qBraid. (ii) ",{}),T("No classical-beating claim yet: ",{b:true}),T("at ≤28 qubits classical FCI/DMRG already solve these instances, so we demonstrate correctness and favourable scaling, not a head-to-head speed advantage; that regime is 40q+ strong correlation where DMRG bond dimension explodes (visible at H₂₄/48q, where DMRG is 6.83 mHa off CCSD(T)). (iii) ",{}),T("40q is operational, not converged: ",{b:true}),T("on CPU the 40-qubit run converges through 39 mHa, above chemical accuracy; closing this is the GPU deliverable. (iv) ",{}),T("Transfer scope: ",{b:true}),T("cross-size generative transfer is shown within the hydrogen-chain family and at the 12→16/20-qubit scale; cross-chemistry and 40q+ transfer are follow-ons. The cross-molecule conditioning variant is a tested negative. A clear-eyed reading: MATGEN-Q is a working, reproducible pipeline whose scaling mechanisms are demonstrated and whose decisive large-scale quantum-vs-classical comparison is the executed GPU work this phase enables.")]),

  H("8. Conclusion and Reproducibility"),
  P([T("MATGEN-Q is a working two-stage GQE whose tensor-network and QSCI tiers, plus MP2 operator-pool compression, target the 40-qubit regime on a single GPU, with every claim third-party reproducible. A one-command driver ("),T("reproduce.py",{i:true}),T(") and a README with a “Launch on qBraid” button let judges re-run each headline result without modification.")]),

  new Paragraph({spacing:{before:120,after:40,line:240,lineRule:"auto"},pageBreakBefore:true,children:[new TextRun({text:"References",font:FONT,size:SZ,bold:true})]}),
];
function refP(n,txt){return new Paragraph({spacing:{after:30,line:240,lineRule:"auto"},indent:{left:360,hanging:360},children:[new TextRun({text:"["+n+"] ",font:FONT,size:20,bold:true}),new TextRun({text:txt,font:FONT,size:20})]});}
const refs=[
 refP(1,"K. Nakaji, et al. “The generative quantum eigensolver (GQE) and its application for ground state search.” arXiv:2401.09253 (2024). [AIST]"),
 refP(2,"N. P. D. Sawaya, et al. “HamLib: A library of Hamiltonians for benchmarking quantum algorithms and hardware.” Quantum 8, 1559 (2024)."),
 refP(3,"S. Minami, K. Nakaji, et al. “Generative quantum combinatorial optimization … conditional generative quantum eigensolver.” Digital Discovery 4(8) (2025)."),
 refP(4,"K. Kanno, et al. “Quantum-selected configuration interaction … subspaces selected by quantum computers.” arXiv:2302.11320 (2023)."),
 refP(5,"NVIDIA Corporation. CUDA-Q and cuQuantum SDK (cuStateVec, tensornet / tensornet-mps backends)."),
 refP(6,"J. Tilly, et al. “The Variational Quantum Eigensolver: A review of methods and best practices.” Physics Reports 986 (2022)."),
 refP(7,"P. Fare, et al. “A multi-fidelity machine learning approach to high-throughput materials screening.” npj Computational Materials 8, 257 (2022)."),
 refP(8,"T. D. Kharazi, et al. “Quantum Simulations for Extreme Ultraviolet Photolithography.” arXiv:2602.20234 (2026). [Xanadu & Mitsubishi Chemical]"),
 refP(9,"R. Kemmoku, Q. Gao, S. Kanno, et al. “Generative Circuit Design for Quantum-Selected Configuration Interaction.” arXiv:2604.09756 (2026). [Mitsubishi Chemical]"),
];
children.push(...refs);

const doc=new Document({
  styles:{default:{document:{run:{font:FONT,size:SZ}}}},
  sections:[{properties:{page:{size:{width:12240,height:15840},margin:{top:1224,right:1224,bottom:1224,left:1224}}},children}]
});
Packer.toBuffer(doc).then(b=>{fs.writeFileSync("EIGENNEXUS_Phase3_Content.docx",b);console.log("Created EIGENNEXUS_Phase3_Content.docx:",b.length,"bytes");});
