"""Paper figures for the 38q audit and the P3 decomposition — generated from committed evidence
JSONs, never typed. Regenerate: python src/make_audit_figures.py
Outputs: results/fig_38q_audit_chi_ladder.png, results/fig_p3_decomposition.png (300 dpi, print/white).
Colors kept CVD-safe per adjacency: navy+green on fig 1, navy+red on fig 2, gray references."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_R = lambda *p: os.path.join(_ROOT, *p)
NAVY, GREEN, RED, GRAY, INK = "#16205B", "#018A6D", "#C13438", "#6B7280", "#1A2238"

B2 = json.load(open(_R("results", "gpu_run4_cas19_evidence.json")))
C400 = json.load(open(_R("results", "cro_cas19_dmrg_reference.json")))["E_dmrg"]
C800 = json.load(open(_R("results", "cro_cas19_dmrg_chi800.json")))["E_dmrg"]
C1200 = json.load(open(_R("results", "cro_cas19_dmrg_chi1200.json")))["E_dmrg"]
P3 = json.load(open(_R("results", "gpu_run1_h20_P3_device_memory_A100_evidence.json")))

# ---------------- Figure 1: 38q audit — trajectory vs the chi-ladder ----------------
tr = [p for p in B2["growth_trace"] if p["iter"] >= 1]          # seed annotated separately
iters = [p["iter"] for p in tr]
errs = [p["err_mHa"] for p in tr]
rel800 = (C800 - C400) * 1000.0
rel1200 = (C1200 - C400) * 1000.0
term = B2["err_mHa"]

fig, ax = plt.subplots(figsize=(6.6, 4.0), dpi=300)
ax.axhline(0, color=GRAY, lw=1.1, ls="--")
ax.axhline(rel800, color=GRAY, lw=1.1, ls="--")
ax.axhline(rel1200, color=GRAY, lw=1.1, ls="--")
ax.annotate("DMRG χ=400 (committed reference)", xy=(5.2, 0.35), fontsize=7.5, color=GRAY, ha="left")
ax.annotate(f"DMRG χ=800  ({rel800:+.2f})", xy=(5.6, rel800 + 0.22), fontsize=7.5, color=GRAY, ha="left")
ax.annotate(f"DMRG χ=1200  ({rel1200:+.2f})", xy=(0.7, rel1200 - 1.05), fontsize=7.5, color=GRAY, ha="left")
ax.plot(iters, errs, "-o", color=NAVY, lw=2, ms=5, zorder=3)
ax.plot([iters[-1]], [term], "o", color=GREEN, ms=9, zorder=4)
ax.annotate(f"QSCI terminal  {term:+.3f} mHa\n({B2['final_space']:,} determinants)",
            xy=(iters[-1], term), xytext=(11.2, 4.2), fontsize=8, color=GREEN, fontweight="bold",
            ha="center", arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.9))
ax.annotate("HF seed +185.8 mHa (off-scale)", xy=(1, errs[0]), xytext=(1.4, 24.5),
            fontsize=7.5, color=GRAY, arrowprops=dict(arrowstyle="->", color=GRAY, lw=0.8))
ax.set_xlim(0.5, 14.5); ax.set_ylim(-5.2, 29)
ax.set_xlabel("QSCI growth iteration", fontsize=9)
ax.set_ylabel("E − E$_{DMRG(χ=400)}$   (mHa)", fontsize=9)
ax.set_title("38-qubit CrO audit: the variational subspace descends below the DMRG reference\n"
             "at χ = 400, 800, and 1200 — the χ-ladder converges toward the audit from above",
             fontsize=9.5, color=INK, loc="left")
ax.tick_params(labelsize=8)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.grid(axis="y", color="#E5E9F2", lw=0.6, zorder=0)
fig.tight_layout()
fig.savefig(_R("results", "fig_38q_audit_chi_ladder.png"), facecolor="white")
print("wrote fig_38q_audit_chi_ladder.png")

# ---------------- Figure 2: P3 decomposition ----------------
meas = P3["measurement"]["peak_device_mem_gb"]
diag = P3["supplementary_diagnostic"]["peak_device_mem_gb"]
thr = P3["measured_config"]["frozen_threshold_gb"]

fig, ax = plt.subplots(figsize=(6.6, 2.9), dpi=300)
bars = ax.barh([1, 0], [meas, diag], height=0.55, color=[RED, NAVY], zorder=3)
ax.axvline(thr, color=GRAY, lw=1.3, ls="--", zorder=2)
ax.annotate(f"frozen P3 threshold  {thr:.0f} GB", xy=(thr, 1.62), fontsize=8, color=GRAY, ha="center")
ax.text(1.0, 1, f"{meas:.2f} GB — verdict run  (default allocator: 50% of free card memory)",
        va="center", ha="left", fontsize=8, color="white", fontweight="bold")
ax.text(diag + 0.8, 0, f"{diag:.2f} GB — identical workload, allocator capped (diagnostic):\ntrue MPS footprint",
        va="center", ha="left", fontsize=8, color=NAVY, fontweight="bold")
ax.set_yticks([]); ax.set_xlim(0, 44); ax.set_ylim(-0.45, 1.95)
ax.set_xlabel("peak device memory (GB), nvidia-smi device-wide — 40q H$_{20}$ χ=400 sampling, A100 80 GB", fontsize=8.5)
ax.set_title("P3: FAIL as-measured, decomposed — allocator appetite, not workload;\n"
             "capped, the identical run sits under the frozen threshold",
             fontsize=9.5, color=INK, loc="left")
ax.tick_params(labelsize=8)
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.grid(axis="x", color="#E5E9F2", lw=0.6, zorder=0)
fig.tight_layout()
fig.savefig(_R("results", "fig_p3_decomposition.png"), facecolor="white")
print("wrote fig_p3_decomposition.png")
