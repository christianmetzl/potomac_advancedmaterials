"""Candidate-decision bar chart: spin-gap (high-spin preference) of CrO vs NiO under each method.
Most functionals and the multireference truth rank CrO > NiO; B3LYP INVERTS it (picks NiO) via its
CrO sign-error. Reads committed evidence -> results/candidate_decision.png. The value-case / J2 visual."""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
dec = json.load(open(os.path.join(_RES, "candidate_decision_evidence.json")))
rows = {r["method"]: r for r in dec["decision_table"]}
order = ["PBE", "BP86", "TPSS", "TPSSh", "PBE0", "B3LYP", "CASCI (this work)", "QSCI (this work)"]
labels = ["PBE", "BP86", "TPSS", "TPSSh", "PBE0", "B3LYP", "CASCI", "QSCI"]
cro = [rows[m]["CrO_gap_eV"] for m in order]
nio = [rows[m]["NiO_gap_eV"] for m in order]

x = np.arange(len(order)); w = 0.38
fig, ax = plt.subplots(figsize=(7.4, 4.3))
b1 = ax.bar(x - w/2, cro, w, label="CrO (exp. ground: quintet X⁵Π)", color="#2b6cb0")
b2 = ax.bar(x + w/2, nio, w, label="NiO (exp. ground: triplet X³Σ⁻)", color="#dd6b20")
ax.axhline(0, color="0.4", lw=0.8)

# shade the multireference block
ax.axvspan(5.5, 7.5, color="#2f855a", alpha=0.07, zorder=0)
ax.annotate("multireference\n(this work)", (6.5, ax.get_ylim()[1]*0.02 if False else 1.98), ha="center",
            fontsize=8.5, color="#2f855a")

# flag the B3LYP inversion
bi = order.index("B3LYP")
ax.annotate("B3LYP INVERTS →\nranks NiO above CrO\n(picks the WRONG candidate)",
            (bi, 0.7), ha="center", va="bottom", fontsize=8.5, color="#c53030", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#c53030"), xytext=(bi-0.1, 1.15))

ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel("high-spin preference  =  E(low-spin) − E(high-spin)  [eV]")
ax.set_title("Which candidate to synthesize?  Rank CrO vs NiO by high-spin preference.\n"
             "5/6 functionals + multireference say CrO;  B3LYP alone flips the pick to NiO.",
             fontsize=10)
ax.set_ylim(-0.35, 2.15)
ax.legend(fontsize=8.5, loc="upper left", framealpha=0.95)
ax.grid(True, axis="y", alpha=0.25)
fig.tight_layout()
out = os.path.join(_RES, "candidate_decision.png")
fig.savefig(out, dpi=160)
print(f"wrote {os.path.relpath(out)} | multireference pick: {dec['multireference_pick_to_synthesize']}; "
      f"inverting functionals: {dec['functionals_that_invert_the_ranking']}")
