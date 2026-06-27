"""CrO spin-gap decision figure: each method's quintet-triplet gap. gap>0 (right of the line) =
correct quintet ground state (agrees with experiment); gap<0 = wrong triplet ground state."""
import json, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

d=json.load(open("../results/cro_spin_gap_evidence.json"))
tbl=d["decision_table"]
# order: DFT functionals (as given), then CASCI, then QSCI at top
labels=[r["method"].split(" (")[0] for r in tbl]
gaps=[r["gap_eV"] for r in tbl]
y=np.arange(len(tbl))[::-1]
colors=["#1f9d55" if r["correct"] else "#c0392b" for r in tbl]
is_ref=["CASCI" in r["method"] or "QSCI" in r["method"] for r in tbl]

fig,ax=plt.subplots(figsize=(5.2,3.3))
ax.axvspan(-1.0,0,color="#fbe4e4",zorder=0); ax.axvspan(0,2.2,color="#e4f5ea",zorder=0)
ax.axvline(0,color="#333",lw=1.2,zorder=2)
ax.barh(y,gaps,color=colors,edgecolor=["black" if r else "none" for r in is_ref],
        linewidth=[1.6 if r else 0 for r in is_ref],height=0.62,zorder=3)
for yi,g in zip(y,gaps):
    ax.text(g+(0.05 if g>=0 else -0.05),yi,f"{g:+.2f}",va="center",
            ha="left" if g>=0 else "right",fontsize=7.5)
ax.set_yticks(y); ax.set_yticklabels(labels,fontsize=8)
ax.set_xlim(-0.6,2.25); ax.set_xlabel("spin gap  E(triplet) − E(quintet)   (eV)",fontsize=9)
ax.text(0.95,len(tbl)-0.4,"→ quintet ground (correct, X⁵Π)",fontsize=7.5,color="#1f6f3f",ha="center")
ax.text(-0.30,len(tbl)-0.4,"wrong",fontsize=7.5,color="#a32020",ha="center")
ax.set_title("CrO ground state: DFT spans 1.9 eV and B3LYP flips it;\nthe multireference value (CASCI/QSCI) agrees with experiment",fontsize=9)
ax.tick_params(labelsize=8)
fig.tight_layout()
fig.savefig("../results/cro_spin_gap.png",dpi=200)
print("saved results/cro_spin_gap.png")
