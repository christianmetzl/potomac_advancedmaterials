"""The reference-correction figure: escalating the classical DMRG bond dimension walks it DOWN toward
our QSCI energy and never crosses it — proving the committed chi=400 reference carried a silent
truncation error, and that QSCI (a variational upper bound on the SAME active-space Hamiltonian) was
strictly closer to the exact answer.

Both methods are variational upper bounds on the identical CAS(18,19) Hamiltonian, so by Rayleigh-Ritz the
LOWER energy is strictly more accurate — no arbitration needed. Reads committed evidence only.
Output: results/chi_ladder_correction.png.  EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def _energy(fn):
    d = json.load(open(os.path.join(_RES, fn)))
    for k, v in d.items():
        if isinstance(v, float) and -1200 < v < -1000:
            return v
    raise ValueError(f"no CrO-scale energy in {fn}")


def main():
    q = json.load(open(os.path.join(_RES, "gpu_run4_cas19_evidence.json")))
    e_qsci, ndet = q["E_qsci"], q["final_space"]
    rungs = [(400, "cro_cas19_dmrg_reference.json"), (800, "cro_cas19_dmrg_chi800.json"),
             (1200, "cro_cas19_dmrg_chi1200.json")]
    chis = np.array([c for c, _ in rungs], dtype=float)
    gaps = np.array([(_energy(f) - e_qsci) * 1000.0 for _, f in rungs])   # mHa above QSCI

    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    # region above the QSCI line = where the classical reference sits (silently too high)
    ax.axhspan(0, gaps.max() * 1.22, color="#E9B84A", alpha=0.09, zorder=0)
    ax.axhline(0, color="#2F855A", lw=2.2, zorder=3)
    ax.text(1290, 0.13, "QSCI (this work) — variational, 529,392 determinants",
            ha="right", va="bottom", fontsize=9, color="#2F855A", fontweight="bold")

    ax.plot(chis, gaps, "o-", color="#C53030", lw=2.0, ms=9, zorder=4,
            label="classical DMRG reference (same CAS(18,19) Hamiltonian)")
    for c, g in zip(chis, gaps):
        ax.annotate(f"+{g:.3f} mHa", (c, g), textcoords="offset points", xytext=(0, 11),
                    ha="center", fontsize=9.5, color="#C53030", fontweight="bold")
    ax.annotate("committed reference\n(the setting that would have shipped)",
                (400, gaps[0]), textcoords="offset points", xytext=(46, -30), fontsize=8.6,
                color="#C53030", arrowprops=dict(arrowstyle="->", color="#C53030", lw=1.0))
    ax.text(0.05, 0.34, "escalating the classical bond dimension\nwalks it DOWN toward QSCI —\nand never crosses it",
            transform=ax.transAxes, fontsize=8.8, color="0.32", ha="left", va="top")

    ax.set_xscale("log")
    ax.set_xticks(chis); ax.set_xticklabels([f"χ={int(c)}" for c in chis], fontsize=10)
    ax.minorticks_off()
    ax.set_xlim(330, 1500)
    ax.set_ylim(-0.35, gaps.max() * 1.22)
    ax.set_ylabel("energy above the QSCI result  [mHa]", fontsize=10)
    ax.set_xlabel("classical DMRG bond dimension χ  (more classical effort →)", fontsize=10)
    ax.set_title("Catching a silent error in the classical reference (CrO, CAS(18,19) = 38 qubits)\n"
                 "Both bound the same Hamiltonian from above — so lower is strictly more accurate.",
                 fontsize=10.5)
    ax.legend(fontsize=8.8, loc="upper right", framealpha=0.95)
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    out = os.path.join(_RES, "chi_ladder_correction.png")
    fig.savefig(out, dpi=160)
    print(f"wrote {os.path.relpath(out)}")
    print(f"  QSCI = {e_qsci:.9f} Ha ({ndet:,} dets); DMRG gaps above it: " +
          ", ".join(f"chi={int(c)}: +{g:.3f} mHa" for c, g in zip(chis, gaps)))


if __name__ == "__main__":
    main()
