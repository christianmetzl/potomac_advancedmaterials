"""Render the E6 figure: DMRG truncation-error extrapolation → near-exact FCI(40q), with the committed
40q QSCI variational energy marked +1.59 mHa above the dw→0 limit. Reads results/e6_dmrg_extrap_40q_evidence.json
(no recomputation) → results/e6_dmrg_extrapolation.png. The visual capstone of the reference-correction thesis."""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
d = json.load(open(os.path.join(_RES, "e6_dmrg_extrap_40q_evidence.json")))
rungs = d["rungs"]; ext = d["extrapolation"]; cert = d["certification"]
E0 = ext["E_fci_40q_estimate_Ha"]; E0_se = ext["E_fci_uncertainty_mHa"]
E_var = cert["E_var_committed_Ha"]; abs_err = cert["absolute_error_mHa"]; it = cert["E_var_source_iter"]

dw = np.array([r["dw"] for r in rungs]); chi = [r["chi"] for r in rungs]
y = (np.array([r["E_dmrg"] for r in rungs]) - E0) * 1000.0        # mHa above the dw→0 limit
xline = np.linspace(0, dw.max() * 1.05, 100)
slope = np.polyfit(dw, (np.array([r["E_dmrg"] for r in rungs]) - E0) * 1000.0, 1)[0]

fig, ax = plt.subplots(figsize=(6.4, 4.2))
C_DMRG, C_FCI, C_QSCI = "#2b6cb0", "#2f855a", "#c05621"

# DMRG rungs descending toward the truncation-free limit
ax.plot(xline, slope * xline, "-", color=C_DMRG, lw=1.6, alpha=0.7, zorder=1)
ax.scatter(dw, y, s=54, color=C_DMRG, zorder=3, label="block2 DMRG rungs (χ = 400→2400)")
_off = {400: (8, -4), 800: (8, -12), 1200: (-2, 12), 1600: (-6, 14), 2400: (-4, -16)}
for x_, y_, c_ in zip(dw, y, chi):
    ax.annotate(f"χ={c_}", (x_, y_), textcoords="offset points", xytext=_off.get(c_, (6, 6)),
                fontsize=8, color=C_DMRG)

# chemical-accuracy band (±1.6 mHa around the near-exact limit)
ax.axhspan(-1.6, 1.6, color="#2f855a", alpha=0.08, zorder=0)

# dw→0 extrapolated FCI(40q) with its uncertainty
ax.errorbar(0, 0, yerr=E0_se, fmt="D", ms=9, color=C_FCI, capsize=4, zorder=4,
            label=f"FCI(40q) extrapolated (dw→0):  $E_0$ = {E0:.6f} Ha\n"
                  f"± {E0_se:.3f} mHa   (linear fit R² = {ext['R2']:.3f})")

# the committed 40q QSCI variational energy, absolute error above the near-exact limit
ax.axhline(abs_err, color=C_QSCI, ls="--", lw=1.8, zorder=2,
           label=f"40q QSCI $E_{{var}}$ (E3 it{it}):  +{abs_err:.2f} mHa above FCI  →  chemically accurate")
ax.annotate(f"+{abs_err:.2f} mHa", (dw.max() * 0.985, abs_err), textcoords="offset points",
            xytext=(0, 5), ha="right", fontsize=8.5, color=C_QSCI, fontweight="bold")

ax.set_xlabel("DMRG discarded weight  (dw)  —  truncation error → 0")
ax.set_ylabel("energy above extrapolated FCI(40q)   [mHa]")
ax.set_title("E6 — independent absolute-accuracy anchor for the 40-qubit flagship\n"
             "high-χ DMRG truncation-error extrapolation on the identical H₂₀ / 40q Hamiltonian",
             fontsize=10.5)
ax.set_xlim(-dw.max() * 0.05, dw.max() * 1.07)
ax.set_ylim(-0.25, 1.85)
ax.legend(fontsize=8, loc="upper left", framealpha=0.96)
ax.grid(True, alpha=0.22)
fig.tight_layout()
out = os.path.join(_RES, "e6_dmrg_extrapolation.png")
fig.savefig(out, dpi=160)
print(f"wrote {os.path.relpath(out)}  |  E0={E0:.6f} Ha, E_var +{abs_err:.2f} mHa (chem-acc={cert['chemical_accuracy_1p6']})")
