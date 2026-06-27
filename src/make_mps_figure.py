"""MPS pillar figure (2 panels): (A) energy error vs bond dimension chi across system size;
(B) entanglement entropy + chi-for-chemical-accuracy vs bond length (area law -> strong correlation)."""
import json, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

d = json.load(open("../results/mps_bonddim_evidence.json"))
fig, (axA, axB) = plt.subplots(1, 2, figsize=(8.2, 3.2))

# Panel A: |error| vs chi
colors = {"H10": "#1f6fb2", "H14": "#e08a1e", "H20": "#c0392b"}
for s in d["study_A_error_vs_chi"]:
    chis = [p["chi"] for p in s["points"] if abs(p["err_mHa"]) > 1e-3]
    errs = [abs(p["err_mHa"]) for p in s["points"] if abs(p["err_mHa"]) > 1e-3]
    axA.plot(chis, errs, "-o", ms=4, color=colors.get(s["system"], "k"),
             label=f"{s['system']} ({s['qubits']}q, vs {s['ref_kind'].split('(')[0]})")
axA.axhspan(0, 1.6, color="#d9f2d9", zorder=0)
axA.text(20, 1.7, "chemical accuracy", fontsize=6.5, color="#2a7a2a")
axA.set_xscale("log"); axA.set_yscale("log"); axA.set_xlabel("MPS bond dimension χ", fontsize=9)
axA.set_ylabel("|error| (mHa)", fontsize=9)
axA.set_title("(A) χ for chemical accuracy grows slowly with size", fontsize=8.5)
axA.legend(fontsize=6.5, loc="upper right"); axA.tick_params(labelsize=8)

# Panel B: entanglement entropy + chi-for-chem-acc vs R
B = d["study_B_entanglement_vs_R"]
R = [b["R"] for b in B]; S = [b["Smax"] for b in B]; chi = [b["chi_for_chem_acc"] for b in B]
axB.plot(R, S, "-s", color="#7b3fa0", ms=5, label="max entanglement entropy")
axB.set_xlabel("H–H bond length R (Å)  →  stronger correlation", fontsize=9)
axB.set_ylabel("max bipartite entropy  Sₘₐₓ", fontsize=9, color="#7b3fa0")
axB.tick_params(axis="y", labelcolor="#7b3fa0", labelsize=8); axB.tick_params(axis="x", labelsize=8)
ax2 = axB.twinx()
ax2.plot(R, chi, "--^", color="#1f9d55", ms=5, label="χ for chemical accuracy")
ax2.set_ylabel("χ for chemical accuracy", fontsize=9, color="#1f9d55")
ax2.tick_params(axis="y", labelcolor="#1f9d55", labelsize=8)
axB.set_title("(B) H₁₀: area-law near equilibrium → strong correlation", fontsize=8.5)
h1, l1 = axB.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
axB.legend(h1 + h2, l1 + l2, fontsize=6.5, loc="upper left")

fig.tight_layout()
fig.savefig("../results/mps_bonddim.png", dpi=200)
print("saved results/mps_bonddim.png")
