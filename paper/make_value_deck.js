// Builds EIGENNEXUS_MATGENQ_Value_Story.pptx — the business + scientific value story and the
// AI / Quantum / Business / Scientific contributions. Every number traces to a committed evidence
// file (see docs/claims_ledger.md). Run: node paper/make_value_deck.js
const pptxgen = require("pptxgenjs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");

// palette — deep instrument-panel ground; cyan=quantum, violet=AI, amber=classical failure/limits, green=verified
const INK = "0B1220", PANEL = "151E33", PANEL2 = "1B2540", LINE = "2A3654";
const TEXT = "E8EDF7", MUTED = "8B98B4", FAINT = "5D6B8A", WHITE = "FFFFFF";
const CYAN = "4FD1E0", VIOLET = "9A8CFF", AMBER = "E9B84A", GREEN = "3FBF7F", RED = "E86A6A";
const HF = "Cambria", BF = "Calibri";

const p = new pptxgen();
p.defineLayout({ name: "W", width: 13.3, height: 7.5 });
p.layout = "W";
p.author = "Team EIGENNEXUS";

function card(s, x, y, w, h, fill, opts = {}) {
  s.addShape("roundRect", {
    x, y, w, h, rectRadius: 0.08, fill: { color: fill },
    line: opts.line ? { color: opts.line, width: 1 } : { type: "none" },
    shadow: { type: "outer", color: "000000", blur: 10, offset: 3, angle: 90, opacity: 0.35 },
  });
}
function eyebrow(s, t, color) {
  s.addText(t, { x: 0.75, y: 0.42, w: 11.8, h: 0.3, fontFace: BF, color: color || CYAN,
    fontSize: 12, bold: true, charSpacing: 3, margin: 0 });
}
function title(s, t, size) {
  s.addText(t, { x: 0.75, y: 0.82, w: 11.8, h: 1.0, fontFace: HF, color: WHITE,
    fontSize: size || 33, bold: true, margin: 0 });
}
function slide() { const s = p.addSlide(); s.background = { color: INK }; return s; }
function srcline(s, t) {
  s.addText(t, { x: 0.75, y: 6.92, w: 11.8, h: 0.35, fontFace: BF, color: FAINT, fontSize: 10.5, margin: 0 });
}

/* ---------------- 1 · title ---------------- */
let s = slide();
s.addText("Team EIGENNEXUS   ·   GIC 2026 Phase 3   ·   Advanced Materials (Mitsubishi Chemical & AIST)",
  { x: 0.75, y: 0.7, w: 11.8, h: 0.3, fontFace: BF, color: CYAN, fontSize: 12.5, bold: true, charSpacing: 2, margin: 0 });
s.addText("MATGEN-Q", { x: 0.75, y: 1.7, w: 11.8, h: 1.0, fontFace: HF, color: WHITE, fontSize: 54, bold: true, margin: 0 });
s.addText("A bluff-detector for the expensive chemistry decisions.",
  { x: 0.75, y: 2.75, w: 11.8, h: 0.6, fontFace: HF, color: CYAN, fontSize: 26, italic: true, margin: 0 });
s.addText("Generative AI designs the quantum circuits. A quantum-selected solver returns an answer that is always honest about its own error — so a wrong prediction never reaches the lab.",
  { x: 0.75, y: 3.5, w: 9.6, h: 1.0, fontFace: BF, color: TEXT, fontSize: 16, lineSpacing: 24, margin: 0 });
const chips = [["40q", "executed on GPU", CYAN], ["26/26", "re-runnable checks", GREEN], ["p<0.0001", "AI transfer to 56q", VIOLET]];
let cx = 0.75;
chips.forEach(([k, l, c]) => {
  card(s, cx, 5.05, 3.6, 1.35, PANEL);
  s.addText(k, { x: cx + 0.3, y: 5.2, w: 3.0, h: 0.5, fontFace: BF, color: c, fontSize: 26, bold: true, margin: 0 });
  s.addText(l, { x: cx + 0.3, y: 5.75, w: 3.0, h: 0.4, fontFace: BF, color: MUTED, fontSize: 12.5, margin: 0 });
  cx += 3.85;
});

/* ---------------- 2 · the business stakes ---------------- */
s = slide();
eyebrow(s, "THE BUSINESS PROBLEM");
title(s, "Building one candidate is a months-long bet");
s.addText("Advancing a single photoresist candidate from computer to synthesis and lithographic test costs months of lab time and real money. So the decision of what to build is made by a computer prediction — before anyone touches a flask.",
  { x: 0.75, y: 2.0, w: 7.0, h: 1.4, fontFace: BF, color: TEXT, fontSize: 16, lineSpacing: 25, margin: 0 });
s.addText("The catch: the chemistry that matters most for EUV photoresists — strongly-correlated Sn / Hf / Zr metal-oxides — is exactly the chemistry where the standard prediction is least trustworthy.",
  { x: 0.75, y: 3.5, w: 7.0, h: 1.45, fontFace: BF, color: TEXT, fontSize: 16, lineSpacing: 25, margin: 0 });
card(s, 8.2, 1.95, 4.35, 2.9, PANEL);
s.addText("$800B+", { x: 8.55, y: 2.25, w: 3.7, h: 0.8, fontFace: BF, color: CYAN, fontSize: 42, bold: true, margin: 0 });
s.addText("semiconductor industry riding on photoresist chemistry — where a wrong candidate is paid for in months, not minutes.",
  { x: 8.55, y: 3.15, w: 3.7, h: 1.4, fontFace: BF, color: MUTED, fontSize: 13, lineSpacing: 19, margin: 0 });
card(s, 0.75, 5.05, 11.8, 1.5, PANEL2, { line: LINE });
s.addText([{ text: "The question this deck answers:  ", options: { bold: true, color: WHITE } },
           { text: "what is it worth to know when your computer prediction is wrong — before you build?", options: { color: TEXT, italic: true } }],
  { x: 1.1, y: 5.05, w: 11.1, h: 1.5, fontFace: BF, fontSize: 17, valign: "middle", margin: 0 });

/* ---------------- 3 · the mechanism: the gold standard bluffs ---------------- */
s = slide();
eyebrow(s, "THE MECHANISM  ·  MEASURED, NOT ASSUMED", AMBER);
title(s, "The gold standard doesn't just err — it bluffs");
s.addText("On strongly-correlated bonds, CCSD(T) collapses non-variationally: it returns an energy BELOW the true answer, confidently, with no internal signal that anything is wrong.",
  { x: 0.75, y: 1.9, w: 11.8, h: 0.85, fontFace: BF, color: TEXT, fontSize: 16, lineSpacing: 24, margin: 0 });
const fails = [
  ["217 mHa", "below the exact energy", "H₁₀ stretched to dissociation — an unphysical, confidently-wrong number.", "strong_correlation.py"],
  ["~140 mHa", "and non-convergent", "A real Cr–O bond stretch, in the identical active space as the exact reference.", "cro_dissociation.py"],
  ["40× error growth", "0.14 → 5.49 mHa", "The real Sn₂O₂ EUV motif under bridge cleavage — QSCI stays ≤0.48 mHa.", "sn2o2_dissociation.py"],
];
let fx = 0.75;
fails.forEach(([big, sub, body, src]) => {
  card(s, fx, 2.95, 3.83, 2.75, PANEL);
  s.addText(big, { x: fx + 0.28, y: 3.15, w: 3.3, h: 0.5, fontFace: BF, color: AMBER, fontSize: 24, bold: true, margin: 0 });
  s.addText(sub, { x: fx + 0.28, y: 3.66, w: 3.3, h: 0.3, fontFace: BF, color: WHITE, fontSize: 13, bold: true, margin: 0 });
  s.addText(body, { x: fx + 0.28, y: 4.05, w: 3.3, h: 1.15, fontFace: BF, color: MUTED, fontSize: 12.5, lineSpacing: 18, margin: 0 });
  s.addText(src, { x: fx + 0.28, y: 5.28, w: 3.3, h: 0.28, fontFace: BF, color: FAINT, fontSize: 10, margin: 0 });
  fx += 4.0;
});
s.addText("A screen built on a method that fails silently inherits every one of those failures — and pays for them in the lab.",
  { x: 0.75, y: 5.95, w: 11.8, h: 0.5, fontFace: BF, color: TEXT, fontSize: 15, italic: true, margin: 0 });
srcline(s, "All three measured in this work and re-runnable via reproduce.py; CCSD(T) uses the identical embedded Hamiltonian as the exact reference (apples-to-apples).");

/* ---------------- 4 · our answer ---------------- */
s = slide();
eyebrow(s, "THE ANSWER", GREEN);
title(s, "Our method cannot bluff — by construction");
s.addText([
  { text: "Variational. ", options: { bold: true, color: GREEN } },
  { text: "QSCI can only ever return an upper bound to the true energy. It cannot sit below the right answer the way CCSD(T) does — the failure mode simply does not exist for it.", options: { color: TEXT } },
], { x: 0.75, y: 1.95, w: 11.8, h: 0.8, fontFace: BF, fontSize: 16, lineSpacing: 24, margin: 0 });
s.addText([
  { text: "Self-certifying. ", options: { bold: true, color: GREEN } },
  { text: "An Epstein–Nesbet PT2 bracket tells you how converged you are. So the answer is either certified-converged, or it tells you it isn't. It never looks confident while being wrong.", options: { color: TEXT } },
], { x: 0.75, y: 2.85, w: 11.8, h: 0.8, fontFace: BF, fontSize: 16, lineSpacing: 24, margin: 0 });
card(s, 0.75, 3.95, 5.75, 2.35, PANEL);
s.addText("Where CCSD(T) fails", { x: 1.05, y: 4.15, w: 5.15, h: 0.4, fontFace: HF, color: AMBER, fontSize: 18, bold: true, margin: 0 });
s.addText("Confidently wrong. Sits 217 mHa below the exact answer with no error signal at all — you cannot tell a good prediction from a bad one.",
  { x: 1.05, y: 4.62, w: 5.15, h: 1.4, fontFace: BF, color: MUTED, fontSize: 13.5, lineSpacing: 20, margin: 0 });
card(s, 6.8, 3.95, 5.75, 2.35, PANEL);
s.addText("Where QSCI stands", { x: 7.1, y: 4.15, w: 5.15, h: 0.4, fontFace: HF, color: GREEN, fontSize: 18, bold: true, margin: 0 });
s.addText("A rigorous bound, with its own error certificate — and on the real oxides it stays within chemical accuracy throughout (≤2.8 mHa on CrO, ≤0.48 mHa on Sn₂O₂).",
  { x: 7.1, y: 4.62, w: 5.15, h: 1.4, fontFace: BF, color: MUTED, fontSize: 13.5, lineSpacing: 20, margin: 0 });
srcline(s, "EN-PT2 certificate: encoder/selci_pt2.py — equilibrium extrapolation reproduces FCI to ~4 mHa, R² = 0.999.");

/* ---------------- 5 · three contributions ---------------- */
s = slide();
eyebrow(s, "WHAT WE CONTRIBUTED", VIOLET);
title(s, "AI  ·  Quantum  ·  Business");
const contrib = [
  [VIOLET, "AI", "Generative circuit design that transfers",
   ["A classical GPT-style transformer writes the quantum circuits — it is not a quantum model.",
    "Trained on 8q+12q only, deployed zero-shot to 56 qubits: 43/48 paired wins, p<0.0001 (8 seeds).",
    "Trained on energy alone, it recovers the MP2 amplitude hierarchy it was never shown (ρ=0.31)."]],
  [CYAN, "QUANTUM", "Executed at scale, on real hardware",
   ["40 qubits, chemically accurate vs its frozen reference (+1.226 mHa, pre-registered pass).",
    "20q / 28q on NVIDIA GPU; trapped-ion QPU silicon decoded and driving the same solver.",
    "Two 38q runs that CORRECT their classical DMRG reference — verified at three bond dimensions."]],
  [GREEN, "BUSINESS", "A pre-synthesis trust gate",
   ["Catch the confidently-wrong classical number before the months-long synthesis commit.",
    "Applies to the strongly-correlated subset — exactly the EUV Sn/Hf/Zr oxide chemistry.",
    "Cost is auditable, not asserted: cost_audit.py re-derives program spend from published pricing."]],
];
let cxx = 0.75;
contrib.forEach(([col, tag, head, bullets]) => {
  card(s, cxx, 1.95, 3.83, 4.45, PANEL);
  s.addText(tag, { x: cxx + 0.28, y: 2.15, w: 3.3, h: 0.35, fontFace: BF, color: col, fontSize: 14, bold: true, charSpacing: 2.5, margin: 0 });
  s.addText(head, { x: cxx + 0.28, y: 2.55, w: 3.3, h: 0.7, fontFace: HF, color: WHITE, fontSize: 17, bold: true, margin: 0 });
  s.addText(bullets.map((b, i) => ({ text: b, options: { bullet: true, breakLine: i < bullets.length - 1 } })),
    { x: cxx + 0.28, y: 3.35, w: 3.3, h: 2.85, fontFace: BF, color: MUTED, fontSize: 12.5, lineSpacing: 17, paraSpaceAfter: 8, margin: 0 });
  cxx += 4.0;
});
srcline(s, "GQE (Nakaji et al. 2024) and QSCI (Kanno et al. 2023) are prior art we build on and cite; the pairing at scale, the transfer generator and the executed results are ours.");

/* ---------------- 5b · the convergence oracle ---------------- */
s = slide();
eyebrow(s, "THE RESULT WE ALMOST FILED AS A FAILURE", GREEN);
title(s, "We caught a silent error in the reference");
s.addText("At 38 qubits our answer came in BELOW the trusted classical reference — on two independent systems. Both are variational upper bounds on the identical Hamiltonian, so the lower energy is strictly more accurate.",
  { x: 0.75, y: 1.9, w: 7.05, h: 1.25, fontFace: BF, color: TEXT, fontSize: 15.5, lineSpacing: 23, margin: 0 });
try {
  s.addImage({ path: path.join(ROOT, "results", "chi_ladder_correction.png"), x: 7.95, y: 1.85, w: 4.6, h: 2.66 });
} catch (e) { /* figure optional */ }
const oracle = [
  ["−3.784 / −0.399 mHa", GREEN, "Two independent corrections", "CrO and the real Sn₂O₂ EUV motif — both below their committed same-CAS DMRG(χ=400) reference."],
  ["χ=400 → 800 → 1200", CYAN, "The mechanism, proven", "Escalating the classical bond dimension walks DMRG down toward our energy (+3.78 → +1.06 → +0.36 mHa) and never crosses it."],
];
let oy = 3.3;
oracle.forEach(([big, col, head, body]) => {
  card(s, 0.75, oy, 7.05, 1.35, PANEL);
  s.addText(big, { x: 1.05, y: oy + 0.13, w: 3.3, h: 0.4, fontFace: BF, color: col, fontSize: 17, bold: true, margin: 0 });
  s.addText(head, { x: 4.4, y: oy + 0.15, w: 3.2, h: 0.35, fontFace: BF, color: WHITE, fontSize: 12.5, bold: true, margin: 0 });
  s.addText(body, { x: 1.05, y: oy + 0.58, w: 6.5, h: 0.7, fontFace: BF, color: MUTED, fontSize: 11.5, lineSpacing: 16, margin: 0 });
  oy += 1.45;
});
card(s, 0.75, 6.2, 11.8, 0.95, PANEL2, { line: LINE });
s.addText([{ text: "Why it matters:  ", options: { bold: true, color: GREEN } },
           { text: "DMRG gives you no signal that your bond dimension is big enough — you stop when it looks converged. An independent variational method coming in lower is proof you hadn't. Useful today, with no quantum-advantage claim.", options: { color: TEXT } }],
  { x: 1.1, y: 6.2, w: 11.1, h: 0.95, fontFace: BF, fontSize: 12.5, valign: "middle", lineSpacing: 17, margin: 0 });
s.addText("Honest limits: not cheaper (19.1 h vs ~15 min to escalate χ classically) — the value is the trigger, not the compute. n = 2: a pattern worth investigating, not a measured rate. Reported as the pre-registered P4 criterion failing as-measured, because P4 assumed DMRG(χ=400) was truth.",
  { x: 7.95, y: 4.62, w: 4.6, h: 1.45, fontFace: BF, color: FAINT, fontSize: 10, lineSpacing: 14, margin: 0 });

/* ---------------- 6 · scientific value ---------------- */
s = slide();
eyebrow(s, "THE SCIENTIFIC VALUE", GREEN);
title(s, "Built so a skeptic can check every number");
const sci = [
  ["Pre-registered", "Every judged claim's threshold was git-timestamped BEFORE the run. Outcomes reported as measured — passes, a resource-DNF, a non-convergence.", GREEN],
  ["Re-runnable", "One command re-executes 17 headline scripts and audits 9 GPU/QPU artifacts: 26/26 PASS, no modification needed.", CYAN],
  ["Self-corrected", "Two claims we tested and WITHDREW: an active-space-fragile candidate ranking, and a DFT sign-flip that proved to be an SCF artifact.", AMBER],
  ["Reference-correcting", "At 38q our solver drops BELOW the classical DMRG reference — and χ=800/1200 confirm it is the reference that was truncated, not us.", VIOLET],
];
let sy = 1.95;
sci.forEach(([h, b, col]) => {
  card(s, 0.75, sy, 11.8, 1.1, PANEL);
  s.addText(h, { x: 1.1, y: sy + 0.16, w: 2.9, h: 0.4, fontFace: HF, color: col, fontSize: 17, bold: true, margin: 0 });
  s.addText(b, { x: 4.1, y: sy + 0.14, w: 8.15, h: 0.85, fontFace: BF, color: MUTED, fontSize: 13, lineSpacing: 18, margin: 0 });
  sy += 1.22;
});
s.addText("We publish the negatives. That is why the positives should be believed.",
  { x: 0.75, y: 6.85, w: 11.8, h: 0.4, fontFace: BF, color: TEXT, fontSize: 15, italic: true, margin: 0 });

/* ---------------- 7 · executed results ---------------- */
s = slide();
eyebrow(s, "EXECUTED — EVERY NUMBER TRACES TO A COMMITTED FILE");
title(s, "What actually ran");
const res = [
  ["+1.226 mHa", CYAN, "40q flagship on GPU", "Chemically accurate vs its frozen DMRG(χ=400) reference at 450,257 determinants — pre-registered criterion met."],
  ["+1.59 mHa", GREEN, "40q absolute anchor", "Independent DMRG extrapolation to the near-exact limit; robust to ±0.05 mHa under a leave-one-out jackknife."],
  ["−3.784 / −0.399", VIOLET, "38q reference corrections", "CrO and the real Sn₂O₂ EUV motif land below their same-CAS DMRG references — mechanism confirmed at three χ."],
  ["0.038 / 0.197 mHa", GREEN, "Open-shell oxides (20q)", "CrO ⁵Π and NiO ³Σ⁻ to chemical accuracy against exact diagonalization."],
  ["real QPU", CYAN, "Trapped-ion silicon", "AQT ibex-q1 decoded; device-sampled determinants seed a QSCI growth that recovers exact FCI."],
  ["16 TB → 195 MB", AMBER, "The memory wall removed", "Tensor-network representation at the measured bond dimension — what makes 40 qubits fit on one GPU."],
];
let rx = 0.75, ry = 1.95;
res.forEach(([big, col, head, body], i) => {
  card(s, rx, ry, 3.83, 2.2, PANEL);
  s.addText(big, { x: rx + 0.26, y: ry + 0.16, w: 3.35, h: 0.45, fontFace: BF, color: col, fontSize: 20, bold: true, margin: 0 });
  s.addText(head, { x: rx + 0.26, y: ry + 0.62, w: 3.35, h: 0.3, fontFace: BF, color: WHITE, fontSize: 13, bold: true, margin: 0 });
  s.addText(body, { x: rx + 0.26, y: ry + 0.96, w: 3.35, h: 1.1, fontFace: BF, color: MUTED, fontSize: 11.5, lineSpacing: 16, margin: 0 });
  rx += 4.0;
  if (i === 2) { rx = 0.75; ry = 4.35; }
});
srcline(s, "Full traceability: docs/claims_ledger.md maps every number → script → evidence file → status.");

/* ---------------- 8 · honest limits ---------------- */
s = slide();
eyebrow(s, "HONEST LIMITS — NON-NEGOTIABLE", AMBER);
title(s, "What we do not claim");
const lims = [
  "No quantum ADVANTAGE at these sizes. At ≤40 qubits classical methods still solve these instances. The value is trust and correctness, not speed — the advantage regime is beyond, which the 40q run targets.",
  "The value case is a framework, not a Mitsubishi ROI. The mechanism is measured here; the dollar inputs are placeholders for your pipeline's own numbers.",
  "Large-ladder results beyond 20q use a determinant-space proxy for the measurement step — validated against real circuit-sampled shots at 12 / 16 / 20 qubits.",
  "The 40q absolute result sits AT the chemical-accuracy threshold, not comfortably inside it. The full 40q tensor-network growth run remains owed.",
  "Two decision claims were tested and withdrawn rather than defended. The value story above depends on neither.",
];
let ly = 1.95;
lims.forEach((t) => {
  card(s, 0.75, ly, 11.8, 0.92, PANEL2, { line: LINE });
  s.addText("⚑", { x: 1.05, y: ly + 0.12, w: 0.4, h: 0.6, fontFace: BF, color: AMBER, fontSize: 16, valign: "middle", margin: 0 });
  s.addText(t, { x: 1.55, y: ly + 0.08, w: 10.7, h: 0.78, fontFace: BF, color: TEXT, fontSize: 13, lineSpacing: 18, valign: "middle", margin: 0 });
  ly += 1.0;
});

/* ---------------- 9 · bottom line ---------------- */
s = slide();
eyebrow(s, "BOTTOM LINE");
title(s, "Where MATGEN-Q sits in the pipeline", 31);
const steps = [["AI proposes", MUTED], ["Classical screens", MUTED], ["MATGEN-Q trust gate", CYAN], ["Synthesize", MUTED]];
let sx = 0.75; const sw = [2.6, 2.9, 3.9, 2.4];
steps.forEach((st, i) => {
  const hot = i === 2;
  card(s, sx, 2.05, sw[i], 1.25, hot ? "1E3A52" : PANEL);
  s.addText(st[0], { x: sx + 0.15, y: 2.05, w: sw[i] - 0.3, h: 1.25, align: "center", valign: "middle",
    fontFace: BF, fontSize: hot ? 15 : 13.5, bold: hot, color: hot ? CYAN : TEXT, margin: 0 });
  if (i < 3) s.addText("→", { x: sx + sw[i] - 0.02, y: 2.05, w: 0.3, h: 1.25, align: "center", valign: "middle", fontFace: BF, color: FAINT, fontSize: 17, margin: 0 });
  sx += sw[i] + 0.22;
});
s.addText("Applied only to the strongly-correlated candidates — the subset where the classical screen is unreliable.",
  { x: 0.75, y: 3.45, w: 11.8, h: 0.4, fontFace: BF, color: MUTED, fontSize: 13.5, italic: true, margin: 0 });
card(s, 0.75, 4.05, 11.8, 2.15, PANEL);
s.addText("You stop paying for confidently-wrong predictions.",
  { x: 1.15, y: 4.35, w: 11.0, h: 0.55, fontFace: HF, color: WHITE, fontSize: 27, bold: true, margin: 0 });
s.addText("The classical gold standard can be confidently wrong on exactly the chemistry that matters, with no warning. MATGEN-Q is variational and self-certifying — it never blindsides you, and it is systematically improvable to the exact answer. Executed to 40 qubits on real hardware, and re-runnable end-to-end in one command.",
  { x: 1.15, y: 5.0, w: 11.0, h: 1.1, fontFace: BF, color: MUTED, fontSize: 14, lineSpacing: 21, margin: 0 });
s.addText("Team EIGENNEXUS  ·  MATGEN-Q  ·  GIC 2026 Phase 3",
  { x: 0.75, y: 6.85, w: 11.8, h: 0.35, fontFace: BF, color: FAINT, fontSize: 11, margin: 0 });

p.writeFile({ fileName: path.join(ROOT, "paper", "EIGENNEXUS_MATGENQ_Value_Story.pptx") })
  .then((f) => console.log("wrote", f));
