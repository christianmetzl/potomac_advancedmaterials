const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, ImageRun } = require('docx');
const fs = require('fs');

const FONT="Times New Roman", SZ=22; // 11pt
const bd={style:BorderStyle.SINGLE,size:1,color:"888888"};
const borders={top:bd,bottom:bd,left:bd,right:bd};
const cw=9792; // content width at ~0.85" margins

function P(runs,opts={}){return new Paragraph({spacing:{after:opts.after??60,line:240,lineRule:"auto"},alignment:opts.align,...opts,children:Array.isArray(runs)?runs:[runs]});}
function T(t,o={}){return new TextRun({text:t,font:FONT,size:SZ,bold:o.b,italics:o.i});}
function H(t){return new Paragraph({spacing:{before:90,after:40,line:240,lineRule:"auto"},children:[new TextRun({text:t,font:FONT,size:SZ,bold:true})]});}

function cell(text,w,{hdr=false,bold=false,align=AlignmentType.LEFT}={}){
  return new TableCell({borders,width:{size:w,type:WidthType.DXA},
    shading:{fill:hdr?"D5E8F0":"FFFFFF",type:ShadingType.CLEAR},
    margins:{top:40,bottom:40,left:90,right:90},
    children:[new Paragraph({alignment:align,spacing:{after:0,line:240,lineRule:"auto"},
      children:[new TextRun({text:text,font:FONT,size:21,bold:hdr||bold})]})]});
}
function row(cells,w,opts={}){return new TableRow({children:cells.map((c,i)=>cell(c,w[i],opts))});}

// Table 1: demonstrated results
const w1=[1500,1200,3492,1500,1100,1000]; // sums 9792 -> adjust
const sum1=w1.reduce((a,b)=>a+b,0); w1[2]+= (9792-sum1);
const tbl1=new Table({width:{size:9792,type:WidthType.DXA},columnWidths:w1,rows:[
  row(["System","Qubits","Method","Error (mHa)","Corr. (%)","Chem. acc."],w1,{hdr:true,align:AlignmentType.CENTER}),
  row(["H\u2082","4","Pure GQE (generative)","0.146","99.3","Yes"],w1,{align:AlignmentType.CENTER}),
  row(["H\u2084","8","Two-stage GQE","0.009","100.0","Yes"],w1,{align:AlignmentType.CENTER}),
  row(["H\u2086","12","Two-stage GQE","0.298","99.5","Yes"],w1,{align:AlignmentType.CENTER}),
]});

// Table 2: QSCI subspace-diagonalization scaling
const w2=[1500,1300,2200,2100,2692];
const tbl2=new Table({width:{size:9792,type:WidthType.DXA},columnWidths:w2,rows:[
  row(["System","Qubits","Determinants","Error (mHa)","Subspace / CI space"],w2,{hdr:true,align:AlignmentType.CENTER}),
  row(["H\u2084","8","27","0.29","75%"],w2,{align:AlignmentType.CENTER}),
  row(["H\u2086","12","148","1.17","37%"],w2,{align:AlignmentType.CENTER}),
  row(["H\u2081\u2080","20","2,401","0.57","3.8%"],w2,{align:AlignmentType.CENTER}),
  row(["H\u2081\u2084","28","18,201","1.21","0.15%"],w2,{align:AlignmentType.CENTER}),
]});

const children=[
  new Paragraph({spacing:{after:30,line:240,lineRule:"auto"},alignment:AlignmentType.CENTER,
    children:[new TextRun({text:"MATGEN-Q: Scaling Conditional GQE for EUV Photoresist Discovery to ~40 Qubits with NVIDIA CUDA-Q",font:FONT,size:24,bold:true})]}),
  new Paragraph({spacing:{after:80,line:240,lineRule:"auto"},alignment:AlignmentType.CENTER,
    children:[new TextRun({text:"Team EIGENNEXUS  \u2014  Advanced Materials (Mitsubishi Chemical Group & AIST)  \u2014  GIC 2026 Phase 2",font:FONT,size:21,italics:true})]}),

  H("1. Focus Area and Rationale"),
  P([T("Ground-state energy estimation governs reaction thermodynamics, redox behavior, and excited-state properties across materials chemistry, yet classical methods scale exponentially with electron correlation and the gold-standard CCSD(T) costs O(N\u2077). The Generative Quantum Eigensolver (GQE; Nakaji et al. 2024, with AIST) replaces variational circuit optimization with a classical generative transformer that proposes quantum circuits, side-stepping the barren-plateau problem \u2014 but statevector GQE stayed small-scale, and QSCI-paired GQE only recently reached 32 qubits (Kemmoku, Gao et al. 2026). "),T("Scaling this generative approach to the ~40-qubit, industrially relevant regime is the problem we address.",{b:true})]),
  P([T("In Phase 1 we proposed ",{}),T("MATGEN-Q",{b:true}),T(", a conditional-GQE pipeline for EUV semiconductor photoresist discovery: AI proposes candidate metal-oxide molecules \u2192 DFT filters \u2192 GQE refines with quantum accuracy \u2192 Bayesian optimization selects the next candidate. EUV photoresists (tin-oxo clusters; Sn, Hf, Zr oxides) are an apt target because their open-shell, multi-reference character is where DFT's 0.3\u20130.5 eV functional-dependent errors make candidate rankings unreliable, and because they are the focus of an active quantum-simulation program by one of this challenge's providers (Kharazi et al., Xanadu & Mitsubishi Chemical, 2026). "),T("Here we develop the scalable prototype that makes this pipeline tractable",{b:true}),T(", reframing MATGEN-Q around the engineering required to reach ~40 qubits. MATGEN-Q's scalable ground-state engine is complementary to that program's excited-state absorption work, and the same pipeline generalizes beyond photoresists to battery electrolytes, catalysts, and functional polymers central to Mitsubishi Chemical's materials portfolio and AIST's computational-materials mission. The stakes are commercial and scientific: EUV photoresists grow at ~20% CAGR within an $800B+ semiconductor industry, and multi-fidelity Bayesian screening has shown up to 3\u00d7 cost reduction (Fare et al., 2022) \u2014 acceleration MATGEN-Q targets through quantum-accurate pre-selection.")]),

  H("2. Target System and Data Modeling Strategy"),
  P([T("Target system. ",{b:true}),T("Our scaling vehicle is the linear hydrogen-chain series H\u2099 (n = 2\u202620; 4\u201340 qubits in the STO-6G basis with Jordan\u2013Wigner mapping) \u2014 the canonical strong-correlation benchmark. Varying a single bond-length parameter tunes the system continuously from weak (area-law) to strong (volume-law) correlation, directly stressing the simulation layer that underpins any scaling claim. EUV tin-oxide fragments are the target: the same QSCI engine already reaches chemical accuracy on Sn-oxide active spaces (Sn effective-core-potential CASCI, validated on H\u2084 to 0.0000 mHa) \u2014 SnO 0.11 mHa (16q), SnO\u2082 0.23 mHa (20q) \u2014 real target chemistry, not only hydrogen (perturbative QSCI, \u00a75).")]),
  P([T("Data. ",{b:true}),T("We adopt HamLib (Sawaya et al., Quantum 2024) \u2014 a public, peer-reviewed library of qubit-mapped Hamiltonians co-developed by Sandia, NASA Ames, NERSC, Oxford and Intel \u2014 as our benchmark; choosing it signals advancement beyond the small molecules on which GQE was originally demonstrated. Because HamLib's large instances ship only Hartree\u2013Fock energies, we built a generation pipeline replicating HamLib's exact methodology (PySCF \u2192 OpenFermion \u2192 Jordan\u2013Wigner, STO-6G) that reproduces its QubitOperator/HDF5 format and extends to any size. "),T("We validated our Hamiltonians against the published HamLib files: diagonalizing HamLib's operators reproduces our independent FCI to 0.00000 mHa (H\u2082\u2013H\u2086), and at 28, 32 and 40 qubits our generated Hamiltonians match HamLib exactly in term count and to ~15 significant figures in coefficient magnitude (differing only by a spectrum-invariant orbital-phase convention).",{b:true}),T(" Every Hamiltonian is therefore reproducible by a third-party reviewer, satisfying the Phase 3 verification requirement.")]),
  P([T("Accuracy anchors. ",{b:true}),T("HamLib stores no reference energies, so we compute our own: FCI exactly (\u226420q), and at larger sizes CCSD(T) near equilibrium where it is reliable, with DMRG \u2014 verified to reproduce FCI to 0.000 mHa at 20q \u2014 as the reference under strong correlation, where CCSD(T) breaks down. Its H\u2081\u2080 error versus FCI grows from 0.17 mHa at equilibrium to 227 mHa at 2.5 \u00C5, exactly where MPS bond dimension grows: a regime we study, not avoid.")]),

  H("3. GQE-Based Approach and Algorithmic Innovation"),
  P([T("MATGEN-Q uses a two-stage GQE. Stage 1 (generative structure discovery): ",{b:true}),T("a decoder-only GPT-style transformer, trained by sequence\u2013energy matching (Nakaji et al.), generates circuits as token sequences over an operator pool of UCC single/double excitations with discrete time steps, learning which excitations compose low-energy states. "),T("Stage 2 (continuous refinement): ",{b:true}),T("the discovered operator structure is refined by continuous, adjoint-gradient angle optimization, converging to chemical accuracy. This division \u2014 generative discovery of structure, gradient refinement of parameters \u2014 is what reliably reaches chemical accuracy, and it incorporates our Phase 1 chemistry-conditioned encoder (an equivariant GNN conditioning generation on molecular graph and target properties) to enable transfer across molecular families. Four innovations make it scalable:")]),
  P([T("(1) Tensor-network (MPS) simulation \u2014 primary scaling enabler. ",{b:true}),T("We replace exact statevector simulation with CUDA-Q's tensornet-mps backend, whose memory scales with circuit entanglement rather than 2\u207F. Molecular ground states near equilibrium obey an entanglement area law, bounding MPS bond dimension; UCC excitations are decomposed into \u22642-qubit gates as the backend requires. Exact cuStateVec validates \u2264~32 qubits; MPS carries 32\u201340+.")],{after:30}),
  P([T("(2) QSCI energy evaluation \u2014 accuracy and noise-aware bonus. ",{b:true}),T("We adopt Quantum Selected Configuration Interaction (Kanno et al. 2023): dominant configurations are sampled from the generated circuit and the Hamiltonian is classically diagonalized in that subspace \u2014 scalable and intrinsically noise-robust, since the quantum device defines only the subspace. We verify this robustness directly at 20 qubits: QSCI reaches chemical accuracy and degrades gracefully under depolarizing noise (\u22643.3 mHa even with 30% of measurements corrupted to random determinants), as frequency-based selection filters the spurious configurations. GQE paired with QSCI was very recently validated to 32 qubits (Kemmoku, Gao, Kanno et al. 2026, Mitsubishi Chemical); we build directly on this, contributing the tensor-network simulation layer (pillar 1) and operator-pool compression that together target the 40-qubit regime.")],{after:30}),
  P([T("(3) Operator-pool compression \u2014 efficiency. ",{b:true}),T("The O(N\u2074) double-excitation pool is pruned via MP2 amplitudes and symmetry-adaptation (point-group, spin), shrinking transformer vocabulary and circuit depth at scale.")],{after:30}),
  P([T("(4) Distributed hybrid workflow. ",{b:true}),T("Detailed in \u00A74.")]),

  H("4. Hybrid Architecture"),
  P([T("The classical transformer trains on GPU (PyTorch); circuit evaluations are dispatched across GPUs via CUDA-Q's mqpu in an asynchronous generate\u2192evaluate\u2192update loop. Quantum resources handle state preparation and energy estimation (MPS / QSCI); classical resources handle generation, optimization, and active-space selection that keeps the qubit count focused on chemically relevant orbitals. The two-stage design maps naturally onto this split: Stage 1 is sampling-bound and parallelizable, Stage 2 is gradient-bound and efficient via adjoint differentiation.")]),
  new Paragraph({spacing:{before:60,after:20,line:240,lineRule:"auto"},alignment:AlignmentType.CENTER,
    children:[new ImageRun({type:"png",data:fs.readFileSync("matgenq_arch.png"),transformation:{width:372,height:264}})]}),
  new Paragraph({spacing:{before:0,after:60,line:240,lineRule:"auto"},alignment:AlignmentType.CENTER,
    children:[new TextRun({text:"Figure 1. MATGEN-Q hybrid architecture: a classical generative transformer (Stage 1) and GPU-accelerated quantum simulation (MPS/QSCI) form an asynchronous loop that discovers circuit structure; Stage 2 refines angles to chemical accuracy. Bracketed labels mark the four scaling pillars.",font:FONT,size:18,italics:true})]}),

  H("5. Demonstrated Results and Benchmarking"),
  P([T("Two-stage GQE \u2014 chemical accuracy at 4\u201312 qubits. ",{b:true}),T("On verified HamLib-format Hamiltonians, our two-stage GQE reaches chemical accuracy across a real scaling sweep (Table 1), benchmarked against HF, DFT, CCSD(T)/FCI and VQE. The H\u2084 value (0.009 mHa) reflects the continuous-refinement stage; the H\u2082 result (0.146 mHa) is from the generative model alone. Crucially, we also run the pipeline end-to-end at 12 qubits: the GPT-QE transformer generates the circuits, QSCI then samples determinants directly from the generated states (141 pooled across 161 generated circuits) and diagonalizes, reaching chemical accuracy (1.05 mHa) and refining the raw generative expectation (51 mHa) ~50\u00d7 \u2014 measurement-based QSCI on genuine GQE output, not perturbative selection.")],{after:50}),
  tbl1,
  new Paragraph({spacing:{before:30,after:50,line:240,lineRule:"auto"},children:[new TextRun({text:"Table 1. Demonstrated two-stage GQE accuracy on validated HamLib hydrogen chains (CPU, lightning.qubit); Corr. (%) = fraction of correlation energy recovered.",font:FONT,size:19,italics:true})]}),
  P([T("QSCI \u2014 chemical accuracy extended to 28 qubits. ",{b:true}),T("Beyond 12 qubits the bottleneck is the Hamiltonian-expectation cost (H\u2081\u2080's 7,151-term operator: 88.5 s per exact-statevector evaluation), so energies are evaluated by QSCI \u2014 diagonalizing the Hamiltonian in a compact selected subspace rather than measuring it in full. This reaches chemical accuracy at 20 qubits with 2,401 determinants and at 28 qubits with 18,201 (Table 2): respectively 3.8% and 0.15% of the spin-conserving FCI space \u2014 a vanishing fraction as size grows, quantifying QSCI scalability. The method also runs at the 40-qubit ideal target (converging through 39 mHa), where the 116,000-term Hamiltonian makes further CPU iterations prohibitive \u2014 precisely the bottleneck the GPU request resolves. At larger scale the subspace is selected perturbatively as a hardware-independent proxy for this measured sampling, validated against it at 12 qubits above.")],{after:50}),
  tbl2,
  new Paragraph({spacing:{before:30,after:50,line:240,lineRule:"auto"},children:[new TextRun({text:"Table 2. QSCI subspace diagonalization: chemical accuracy (\u22641.6 mHa) to 28 qubits; 40q operational (converging through 39 mHa). Subspace/CI space = selected determinants \u00f7 full CI space. Perturbative selection is a hardware-independent proxy for circuit-sampled QSCI.",font:FONT,size:19,italics:true})]}),
  P([T("Phase 3 benchmarking plan. ",{b:true}),T("Extend the demonstrated ladder on GPU via MPS to 24\u201340 qubits; report energy error versus CCSD(T)/DMRG, truncation error versus correlation, and wall-clock versus VQE; validate selected circuits on qBraid hardware (IonQ/IBM) at 10\u201316 qubits.")]),

  H("6. Platform Justification and Resource Needs"),
  P([T("Two bottlenecks set our requirements: the Hamiltonian-expectation cost (addressed by QSCI, \u00A75) and, at 40 qubits, statevector memory \u2014 exact simulation needs ~16 TB and is infeasible \u2014 addressed by tensor-network simulation. We therefore request "),T("NVIDIA H100 or A100 (80 GB) GPUs with the CUDA-Q SDK",{b:true}),T(", using the tensornet-mps backend for the 24\u201340 qubit tier and cuStateVec for exact validation to ~32 qubits. One high-memory GPU suffices for the MPS runs; "),T("4\u20138 GPUs with NVLink",{b:true}),T(" enable distributed circuit evaluation (innovation 4) and the >40-qubit bonus attempt. We additionally request "),T("qBraid access",{b:true}),T(" for hardware validation at 10\u201316 qubits. Estimated need ~2 weeks of GPU wall-clock; backend-agnostic and flexible to the allocation.")]),
  new Paragraph({spacing:{before:120,after:40,line:240,lineRule:"auto"},pageBreakBefore:true,children:[new TextRun({text:"References",font:FONT,size:SZ,bold:true})]}),
];
function refP(n,txt){return new Paragraph({spacing:{after:30,line:240,lineRule:"auto"},indent:{left:360,hanging:360},children:[new TextRun({text:"["+n+"] ",font:FONT,size:20,bold:true}),new TextRun({text:txt,font:FONT,size:20})]});}
const refs=[
 refP(1,"K. Nakaji, et al. \u201CThe generative quantum eigensolver (GQE) and its application for ground state search.\u201D arXiv:2401.09253 (2024). [Research Center for Emerging Computing Technologies, AIST]"),
 refP(2,"N. P. D. Sawaya, et al. \u201CHamLib: A library of Hamiltonians for benchmarking quantum algorithms and hardware.\u201D Quantum 8, 1559 (2024). arXiv:2306.13126."),
 refP(3,"S. Minami, K. Nakaji, et al. \u201CGenerative quantum combinatorial optimization by means of a novel conditional generative quantum eigensolver.\u201D Digital Discovery 4(8), 2229\u20132243 (2025)."),
 refP(4,"K. Kanno, et al. \u201CQuantum-selected configuration interaction: classical diagonalization of Hamiltonians in subspaces selected by quantum computers.\u201D arXiv:2302.11320 (2023)."),
 refP(5,"NVIDIA Corporation. CUDA-Q and cuQuantum SDK (cuStateVec and tensornet / tensornet-mps backends). https://developer.nvidia.com/cuda-q (accessed May 2026)."),
 refP(6,"J. Tilly, et al. \u201CThe Variational Quantum Eigensolver: A review of methods and best practices.\u201D Physics Reports 986, 1\u201364 (2022)."),
 refP(7,"P. Fare, et al. \u201CA multi-fidelity machine learning approach to high-throughput materials screening.\u201D npj Computational Materials 8, 257 (2022)."),
 refP(8,"T. D. Kharazi, S. Fomichev, S. Kanno, T. Kobayashi, J. M. Arrazola, Q. Gao, T. F. Stetina. \u201CQuantum Simulations for Extreme Ultraviolet Photolithography.\u201D arXiv:2602.20234 (2026). [Xanadu & Mitsubishi Chemical]"),
 refP(9,"R. Kemmoku, Q. Gao, S. Kanno, K. Keithley, I. Hamamura, N. Yamamoto, K. Nakaji. \u201CGenerative Circuit Design for Quantum-Selected Configuration Interaction.\u201D arXiv:2604.09756 (2026). [Mitsubishi Chemical]"),
];
children.push(...refs);


const doc=new Document({
  styles:{default:{document:{run:{font:FONT,size:SZ}}}},
  sections:[{properties:{page:{size:{width:12240,height:15840},margin:{top:1224,right:1224,bottom:1224,left:1224}}},children}]
});
Packer.toBuffer(doc).then(b=>{fs.writeFileSync("EIGENNEXUS_Phase2_Content.docx",b);console.log("Created:",b.length,"bytes");});

// ===== Append References (excluded from 3-page limit) =====
