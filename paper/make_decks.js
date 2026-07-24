// Builds two decks: (1) professional J2 showcase, (2) ELI5-but-professional. Centered on the
// candidate-decision figure (results/candidate_decision.png). Run: node paper/make_decks.js
const pptxgen = require("pptxgenjs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
const FIG = path.join(ROOT, "results", "candidate_decision.png");

// palette (quantum-chemistry: deep indigo + the figure's CrO-blue / NiO-orange + warning red / correct green)
const NAVY = "1E2761", DARK = "151B3A", INK = "1F2937", SLATE = "64748B", LINE = "E2E8F0";
const BLUE = "2B6CB0", ORANGE = "DD6B20", RED = "C53030", GREEN = "2F855A", ICE = "CADCFC", WHITE = "FFFFFF";
const HFONT = "Cambria", BFONT = "Calibri";

function card(s, x, y, w, h, fill, opts = {}) {
  s.addShape("roundRect", { x, y, w, h, rectRadius: 0.09, fill: { color: fill },
    line: opts.line ? { color: opts.line, width: 1 } : { type: "none" },
    shadow: { type: "outer", color: "9AA5B1", blur: 6, offset: 2, angle: 90, opacity: 0.35 } });
}
function tb(s, text, o) { s.addText(text, Object.assign({ fontFace: BFONT, color: INK, align: "left", valign: "top", margin: 0 }, o)); }

// ------- shared content slides (deckKind: 'pro' | 'eli5') -------
function build(kind, outfile, done) {
  const p = new pptxgen();
  p.defineLayout({ name: "W", width: 13.3, height: 7.5 });
  p.layout = "W";
  const eli5 = kind === "eli5";

  // ---------- Slide 1 — title (dark) ----------
  let s = p.addSlide(); s.background = { color: DARK };
  s.addText("Team EIGENNEXUS", { x: 0.7, y: 0.55, w: 6, h: 0.35, fontFace: BFONT, color: ICE, fontSize: 13, charSpacing: 2 });
  s.addText(eli5 ? "Picking the Right Molecule to Build"
                 : "When DFT Picks the Wrong Molecule",
    { x: 0.7, y: 2.0, w: 11.9, h: 1.7, fontFace: HFONT, color: WHITE, fontSize: 46, bold: true, lineSpacing: 48 });
  s.addText(eli5
    ? "Why the popular computational shortcut sometimes picks the wrong candidate — and how a quantum-accurate check catches it first."
    : "A quantum-accurate candidate decision that inverts a widely-used DFT ranking — and matches the experiment.",
    { x: 0.7, y: 3.75, w: 11.4, h: 1.0, fontFace: BFONT, color: ICE, fontSize: 19, lineSpacing: 26 });
  // two candidate chips as the motif
  card(s, 0.7, 5.3, 2.7, 1.15, NAVY); s.addText([{ text: "Candidate A\n", options: { bold: true, color: WHITE, fontSize: 16 } }, { text: "CrO", options: { color: ICE, fontSize: 22, bold: true } }], { x: 0.7, y: 5.3, w: 2.7, h: 1.15, align: "center", valign: "middle", fontFace: BFONT });
  s.addText("vs", { x: 3.5, y: 5.3, w: 0.7, h: 1.15, align: "center", valign: "middle", fontFace: HFONT, color: ICE, fontSize: 20, italic: true });
  card(s, 4.3, 5.3, 2.7, 1.15, NAVY); s.addText([{ text: "Candidate B\n", options: { bold: true, color: WHITE, fontSize: 16 } }, { text: "NiO", options: { color: ICE, fontSize: 22, bold: true } }], { x: 4.3, y: 5.3, w: 2.7, h: 1.15, align: "center", valign: "middle", fontFace: BFONT });
  s.addText("GIC 2026 · Phase 3 · Advanced Materials (Mitsubishi Chemical & AIST)",
    { x: 7.4, y: 5.75, w: 5.2, h: 0.6, align: "right", valign: "middle", fontFace: BFONT, color: SLATE, fontSize: 12 });

  // ---------- Slide 2 — the problem (light) ----------
  s = p.addSlide(); s.background = { color: WHITE };
  s.addText(eli5 ? "You can only afford to build one" : "Which candidate do you synthesize?",
    { x: 0.7, y: 0.5, w: 12, h: 0.8, fontFace: HFONT, color: NAVY, fontSize: 34, bold: true });
  tb(s, eli5
    ? "Advancing one molecule to synthesis and lab testing costs months and real money. Computers screen candidates first to pick the best one — usually with a method called DFT."
    : "DFT is the standard pre-synthesis filter. But its functional choice can flip the answer exactly where it matters most — strongly-correlated (multireference) metal-oxide chemistry, the heart of EUV resists.",
    { x: 0.7, y: 1.45, w: 8.0, h: 1.5, fontSize: 17, color: INK, lineSpacing: 25 });
  // two stat callouts
  card(s, 9.0, 1.5, 3.6, 2.0, "F1F5FB");
  s.addText([{ text: "1.9 eV\n", options: { fontSize: 44, bold: true, color: BLUE } },
             { text: eli5 ? "how much the DFT answer swings\ndepending on the 'flavor' chosen" : "spread across six DFT functionals\non one molecule's spin-state gap", options: { fontSize: 13, color: SLATE } }],
    { x: 9.2, y: 1.7, w: 3.2, h: 1.6, align: "left", valign: "top", fontFace: BFONT, lineSpacing: 16 });
  card(s, 0.7, 3.4, 11.9, 2.9, "FBFBFD", { line: LINE });
  s.addText(eli5 ? "The catch" : "Why it bites here", { x: 1.0, y: 3.6, w: 11, h: 0.5, fontFace: HFONT, color: RED, fontSize: 20, bold: true });
  tb(s, eli5
    ? [{ text: "The most popular 'flavor' of DFT (called B3LYP) can get the answer backwards on these tricky molecules. If it does, the whole ranking flips — and you'd build the wrong one.", options: {} }]
    : [{ text: "On CrO, one of the six functionals — B3LYP, the single most-used functional — assigns the ", options: {} },
       { text: "wrong ground state", options: { bold: true, color: RED } },
       { text: " (spin-gap −0.08 eV vs the true +1.89 eV). A screen built on it inherits that error and mis-ranks the candidate.", options: {} }],
    { x: 1.0, y: 4.2, w: 11.3, h: 1.9, fontSize: 17, color: INK, lineSpacing: 26 });

  // ---------- Slide 3 — the decision (light) ----------
  s = p.addSlide(); s.background = { color: WHITE };
  s.addText(eli5 ? "The test: which is the stronger magnet?" : "A frozen, testable decision",
    { x: 0.7, y: 0.5, w: 12, h: 0.8, fontFace: HFONT, color: NAVY, fontSize: 34, bold: true });
  // candidate A card
  card(s, 0.7, 1.55, 5.7, 2.5, "F1F5FB");
  s.addText("Candidate A — CrO", { x: 1.0, y: 1.75, w: 5.1, h: 0.5, fontFace: HFONT, color: BLUE, fontSize: 20, bold: true });
  tb(s, [{ text: eli5 ? "Real-world answer: strong high-spin (a good magnet)." : "Experimental ground state: X⁵Π (quintet, S = 2).", options: { breakLine: true } },
         { text: eli5 ? "This is the correct pick." : "A robust high-spin center.", options: { color: SLATE } }],
     { x: 1.0, y: 2.4, w: 5.1, h: 1.4, fontSize: 15, lineSpacing: 22 });
  // candidate B card
  card(s, 6.9, 1.55, 5.7, 2.5, "F1F5FB");
  s.addText("Candidate B — NiO", { x: 7.2, y: 1.75, w: 5.1, h: 0.5, fontFace: HFONT, color: ORANGE, fontSize: 20, bold: true });
  tb(s, [{ text: eli5 ? "Real-world answer: weaker high-spin than CrO." : "Experimental ground state: X³Σ⁻ (triplet, S = 1).", options: { breakLine: true } },
         { text: eli5 ? "The runner-up." : "A weaker high-spin preference than CrO.", options: { color: SLATE } }],
     { x: 7.2, y: 2.4, w: 5.1, h: 1.4, fontSize: 15, lineSpacing: 22 });
  card(s, 0.7, 4.35, 11.9, 2.0, "FBFBFD", { line: LINE });
  s.addText(eli5 ? "How we decide" : "The rule (pre-registered)", { x: 1.0, y: 4.55, w: 11, h: 0.5, fontFace: HFONT, color: NAVY, fontSize: 19, bold: true });
  tb(s, eli5
    ? "Rank the two by how strongly they prefer the high-spin state, using six DFT flavors AND a quantum-accurate method. We wrote the rule down before computing the quantum answer — no moving the goalposts."
    : "Rank both candidates by high-spin preference (spin-gap = E(low-spin) − E(high-spin)), computed by six DFT functionals and by a fixed CAS(10,10) CASCI/QSCI treatment. The decision rule was committed before the multireference numbers were computed.",
    { x: 1.0, y: 5.15, w: 11.3, h: 1.1, fontSize: 15.5, color: INK, lineSpacing: 22 });

  // ---------- Slide 4 — the result (figure) ----------
  s = p.addSlide(); s.background = { color: WHITE };
  s.addText(eli5 ? "The quantum-accurate check picks the right one"
                 : "The multireference selector is right — B3LYP inverts it",
    { x: 0.7, y: 0.45, w: 12, h: 0.75, fontFace: HFONT, color: NAVY, fontSize: 30, bold: true });
  s.addImage({ path: FIG, x: 0.55, y: 1.25, w: 8.7, h: 5.05 });
  // right rail callout
  card(s, 9.45, 1.4, 3.25, 2.5, "F1F5FB");
  s.addText([{ text: "Synthesize CrO\n", options: { fontSize: 22, bold: true, color: GREEN } },
             { text: eli5 ? "The quantum-accurate method — and 5 of 6 DFT flavors — agree." : "5 of 6 functionals + CASCI/QSCI agree; matches CrO's experimental X⁵Π.", options: { fontSize: 14, color: INK } }],
    { x: 9.65, y: 1.6, w: 2.85, h: 2.2, align: "left", valign: "top", fontFace: BFONT, lineSpacing: 18 });
  card(s, 9.45, 4.05, 3.25, 2.25, "FDECEC");
  s.addText([{ text: "B3LYP → NiO\n", options: { fontSize: 20, bold: true, color: RED } },
             { text: eli5 ? "The popular flavor picks the wrong molecule." : "The most-used functional inverts the ranking — advances the wrong candidate.", options: { fontSize: 14, color: INK } }],
    { x: 9.65, y: 4.25, w: 2.85, h: 2.0, align: "left", valign: "top", fontFace: BFONT, lineSpacing: 18 });

  // ---------- Slide 5 — value (light) ----------
  s = p.addSlide(); s.background = { color: WHITE };
  s.addText(eli5 ? "Why it matters" : "Where a quantum-accurate check pays off",
    { x: 0.7, y: 0.5, w: 12, h: 0.8, fontFace: HFONT, color: NAVY, fontSize: 34, bold: true });
  // funnel steps
  const steps = eli5
    ? ["AI suggests molecules", "DFT quick-screens", "Quantum check on the tricky ones", "Build the winner"]
    : ["AI proposes", "DFT filters", "QSCI-accurate check on multireference candidates", "Bayesian selects → synthesize"];
  let fx = 0.7; const fw = [2.2, 2.2, 3.95, 3.35];
  steps.forEach((t, i) => {
    const hot = i === 2;
    card(s, fx, 1.5, fw[i], 1.15, hot ? NAVY : "F1F5FB");
    s.addText(t, { x: fx + 0.12, y: 1.5, w: fw[i] - 0.24, h: 1.15, align: "center", valign: "middle", fontFace: BFONT, fontSize: hot ? 14 : 13, bold: hot, color: hot ? WHITE : INK, lineSpacing: 16 });
    if (i < 3) s.addText("→", { x: fx + fw[i] - 0.02, y: 1.5, w: 0.24, h: 1.15, align: "center", valign: "middle", fontFace: BFONT, color: SLATE, fontSize: 18 });
    fx += fw[i] + 0.12;
  });
  s.addText(eli5 ? "The quantum-accurate check sits right where DFT is unreliable — catching a wrong pick before the months-long build."
                 : "The interception point: catch the flipped ranking before the months-long synthesis commit.",
    { x: 0.7, y: 2.85, w: 11.9, h: 0.6, fontFace: BFONT, italic: true, color: SLATE, fontSize: 14 });
  // value formula card
  card(s, 0.7, 3.7, 11.9, 2.55, "FBFBFD", { line: LINE });
  s.addText(eli5 ? "The rough cost of picking wrong" : "Avoidable waste (illustrative framework — plug your own numbers)",
    { x: 1.0, y: 3.9, w: 11.3, h: 0.5, fontFace: HFONT, color: NAVY, fontSize: 19, bold: true });
  s.addText([{ text: "Waste ≈ N · f", options: { fontSize: 22, bold: true, color: INK } },
             { text: "mr", options: { fontSize: 13, bold: true, color: INK } },
             { text: " · p · C", options: { fontSize: 22, bold: true, color: INK } }],
    { x: 1.0, y: 4.5, w: 6.0, h: 0.6, fontFace: BFONT });
  tb(s, eli5
    ? "N candidates screened × how many are 'tricky' × how often the shortcut mis-picks × cost per wrong build. Every number is yours to fill in — the point is the mechanism is real and measured."
    : "N screened × f_mr (multireference fraction) × p (mis-rank rate) × C (cost per false lead). Dollar inputs are placeholders; the measured facts are the 1.9 eV spread, the B3LYP sign-error, and the ranking inversion. Multi-fidelity screening shows up to 3× cost reduction (Fare 2022).",
    { x: 1.0, y: 5.15, w: 11.3, h: 1.0, fontSize: 14, color: INK, lineSpacing: 20 });

  // ---------- Slide 6 — conclusion (dark) ----------
  s = p.addSlide(); s.background = { color: DARK };
  s.addText(eli5 ? "Honest, and you can check it yourself" : "Decision-robust. Verifiable. Honest.",
    { x: 0.7, y: 0.7, w: 12, h: 0.9, fontFace: HFONT, color: WHITE, fontSize: 34, bold: true });
  const pts = eli5
    ? [["Real result", "A popular method picks the wrong molecule; the quantum-accurate one picks the right one — matching experiment."],
       ["Small print, stated", "One small test, a simplified model — the pattern is real, not the exact dollar figure."],
       ["Re-runnable", "Anyone can reproduce it: one script, committed data, no special access."]]
    : [["Decision-robust", "5/6 functionals + CASCI/QSCI pick CrO; B3LYP alone inverts. The multireference selector doesn't flip."],
       ["Honest scope", "Fixed modest CAS(10,10)/def2-SVP; the claim is the ranking/sign (which candidate), not a benchmark gap magnitude."],
       ["Verifiable", "python src/candidate_decision.py → results/candidate_decision_evidence.json. Frozen rule, committed evidence."]];
  let cy = 1.9;
  pts.forEach(([h, b]) => {
    s.addShape("roundRect", { x: 0.7, y: cy, w: 0.5, h: 0.5, rectRadius: 0.25, fill: { color: NAVY }, line: { type: "none" } });
    s.addText("✓", { x: 0.7, y: cy, w: 0.5, h: 0.5, align: "center", valign: "middle", fontFace: BFONT, color: ICE, fontSize: 18, bold: true });
    s.addText(h, { x: 1.4, y: cy - 0.05, w: 11, h: 0.5, fontFace: HFONT, color: ICE, fontSize: 20, bold: true });
    s.addText(b, { x: 1.4, y: cy + 0.42, w: 11.0, h: 0.9, fontFace: BFONT, color: "C7CEDB", fontSize: 15, lineSpacing: 20 });
    cy += 1.55;
  });

  p.writeFile({ fileName: outfile }).then(() => { console.log("wrote", outfile); done && done(); });
}

build("pro", path.join(ROOT, "paper", "EIGENNEXUS_J2_Decision_Professional.pptx"),
  () => build("eli5", path.join(ROOT, "paper", "EIGENNEXUS_J2_Decision_ELI5.pptx")));
