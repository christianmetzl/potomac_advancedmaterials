"""CrO trust figure: |error vs exact CASCI| as multireference character grows
(x = dominant-determinant weight, decreasing -> stronger correlation). CCSD(T) becomes
erratic/non-convergent; selected-CI/QSCI stays accurate and variational."""
import json, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

d=json.load(open("../results/cro_dissociation_evidence.json"))
g=sorted(d["geometries"], key=lambda r:-r["dominant_det_weight"])
w=[r["dominant_det_weight"] for r in g]
ccsdt=[abs(r["CCSDT_err_mHa"]) if r["CCSDT_err_mHa"] is not None else np.nan for r in g]
conv=[r["CCSDT_converged"] for r in g]
sci=[r["selCI_err_mHa"] for r in g]

fig,ax=plt.subplots(figsize=(5.0,3.2))
ax.axhspan(0,1.6,color="#d9f2d9",zorder=0)
ax.text(0.165,1.65,"chemical accuracy",fontsize=7,color="#2a7a2a",va="bottom")
ax.plot(w,ccsdt,"-",color="#c0392b",lw=1.4,zorder=2)
for wi,ci,cv in zip(w,ccsdt,conv):
    ax.plot(wi,ci,"o" if cv else "X",color="#c0392b",ms=8 if not cv else 6,
            mfc="#c0392b" if cv else "white",mec="#c0392b",mew=1.6,zorder=3)
ax.plot(w,sci,"-s",color="#1f6fb2",lw=1.4,ms=5,zorder=3,label="selected-CI / QSCI (variational)")
ax.plot([],[],"o",color="#c0392b",label="CCSD(T), converged")
ax.plot([],[],"X",color="#c0392b",mfc="white",mec="#c0392b",label="CCSD(T), NOT converged")
ax.plot([],[],"-s",color="#1f6fb2",label="selected-CI / QSCI (variational)")
ax.set_yscale("log"); ax.set_xlim(0.92,0.10)
ax.set_xlabel("dominant-determinant weight  (← stronger multireference)",fontsize=9)
ax.set_ylabel("|error vs exact CASCI|  (mHa)",fontsize=9)
ax.set_title("CrO bond stretch: CCSD(T) breaks down, QSCI stays trustworthy",fontsize=9.5)
ax.tick_params(labelsize=8)
h,l=ax.get_legend_handles_labels()
ax.legend(h[-3:],l[-3:],fontsize=7,loc="center left")
fig.tight_layout()
fig.savefig("../results/cro_dissociation.png",dpi=200)
print("saved results/cro_dissociation.png")
