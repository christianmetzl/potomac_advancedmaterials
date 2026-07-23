"""E6 — independent absolute-accuracy anchor for the 40q flagship via DMRG truncation-error extrapolation.

Supplementary variant to the pre-registered E3 PT2 certificate (box A). E3 certifies 40q absolute
accuracy from the INSIDE (grow the QSCI space, EN-PT2 brackets E_var toward FCI, target |PT2|<=0.5 mHa).
That route is slow and RAM-heavy (billion-determinant residual -> ~8 h/iter, approaching the OOM ceiling).
E6 attacks the *reference half* of the same claim INDEPENDENTLY and cheaply:

  1. run block2 DMRG on the IDENTICAL H20/40q Hamiltonian at a chi-ladder (each chi a rigorous
     variational upper bound to FCI),
  2. extrapolate energy vs discarded weight (dw) to the truncation-free limit dw->0 -> a near-exact
     FCI(40q) estimate with a real uncertainty (textbook DMRG extrapolation; White/Chan std practice),
  3. certify the committed 40q QSCI variational energy E_var (box A, results/e3_certificate_evidence.json)
     against that anchor:  absolute_error = (E_var - E_FCI_extrap) * 1000 mHa.

Why this is legitimate and "equally expressive":
  - Every DMRG energy is variational (>= FCI); the ladder descends monotonically toward FCI.
  - For H20 (quasi-1D, area-law) DMRG is the near-exact method: chi=800 already ran in 375 s / 9.3 GB
    (results/h20_40q_dmrg_chi800.json) with a near-converged final sweep -> high chi is cheap and the
    dw->0 extrapolation is tight. This is exactly the paper's truncation-error thesis, closed on the
    flagship system.
  - It does NOT touch box A, does NOT need box A's un-checkpointable in-RAM space, and cannot OOM the
    way the PT2 residual does (DMRG memory ~ n*chi^2*d, bounded).

PRE-REGISTRATION DISCIPLINE (frozen by committing this file + its prereg entry BEFORE production):
  - chi ladder, DMRG schedule, extrapolation model (linear E vs dw), the fit-quality gate, and the
    reporting rule are all fixed here. The extrapolated number and E_var's absolute error are reported
    AS-MEASURED, pass or fail, with the full ladder in evidence. Supplementary (not the pre-registered
    E3); box A's frozen E3 result stands unchanged and is shown alongside.

DMRG schedule is the frozen make_ref/E1 schedule with the chi plateau raised (n_sweeps=8,
bond_dims=[100,150,200,chi,chi,chi,chi,chi], noises=[1e-4,1e-5,1e-6,1e-7,0,0,0,0], thrds=[1e-8]*8, SU(2)) —
IDENTICAL to e1_chi800_counteraudit.run_dmrg, so the chi=400/800 rungs reproduce the committed references.

Usage:
    python src/e6_dmrg_extrap_40q.py                       # full ladder (needs ~128 GB for chi<=2400)
    CHI_LADDER=400,600,800 python src/e6_dmrg_extrap_40q.py  # low-chi validation ladder (fits <=15 GB up to ~800)
    E6_THREADS=32 python src/e6_dmrg_extrap_40q.py

EIGENNEXUS - GIC 2026 Phase 3, E6 supplementary absolute-accuracy anchor.
"""
import os, sys, json, time
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_RES = os.path.join(os.path.dirname(_HERE), "results")
sys.path.insert(0, _HERE)
from e1_chi800_counteraudit import h20_integrals  # identical integral path as qsci_lib.hchain_problem(20)

# ---- frozen ladder + schedule (pre-registered) ----
CHI_LADDER = [int(x) for x in os.environ.get("CHI_LADDER", "400,800,1200,1600,2400").split(",")]
N_THREADS = int(os.environ.get("E6_THREADS", "8"))
# extrapolation gate (frozen): accept the linear dw->0 fit only if it uses >=3 rungs and R^2 >= this;
# the extrapolation uncertainty is the intercept standard error of that fit.
FIT_MIN_RUNGS = 3
FIT_MIN_R2 = 0.98


def run_dmrg_dw(P, chi, tag, n_threads=N_THREADS):
    """Frozen E1/make_ref schedule at raised chi; returns E AND the final-sweep discarded weight (dw).

    Numerically identical to e1_chi800_counteraudit.run_dmrg (same bond_dims/noises/thrds/SU2); the only
    addition is capturing the discarded weight, which block2 exposes after the sweep. dw is the abscissa
    for the truncation-free extrapolation."""
    from pyblock2.driver.core import DMRGDriver, SymmetryTypes
    scratch = os.path.join(os.path.expanduser("~"), "dmrg_scratch", tag)
    os.makedirs(scratch, exist_ok=True)
    na, nb = P["na"], P["nb"]; ns = P["n_sites"]
    bond_dims = [100, 150, 200, chi, chi, chi, chi, chi]
    noises = [1e-4, 1e-5, 1e-6, 1e-7, 0, 0, 0, 0]
    thrds = [1e-8] * 8
    # runtime resource pool ONLY (numerically inert; identical schedule/thresholds to e1.run_dmrg).
    # chi>=1200 needs a raised stack_mem on a large-RAM box; defaults reproduce block2's originals.
    stack_mem = int(float(os.environ.get("STACK_MEM_GB", "1")) * (1024 ** 3))
    n_mkl = int(os.environ.get("DMRG_MKL_THREADS", "1"))
    n_threads = int(os.environ.get("DMRG_N_THREADS", str(n_threads)))
    driver = DMRGDriver(scratch=scratch, symm_type=SymmetryTypes.SU2, n_threads=n_threads,
                        stack_mem=stack_mem, n_mkl_threads=n_mkl)
    driver.initialize_system(n_sites=ns, n_elec=na + nb, spin=na - nb, orb_sym=None)
    mpo = driver.get_qc_mpo(h1e=P["h1"], g2e=P["eri"], ecore=P["ecore"], iprint=0)
    ket = driver.get_random_mps(tag=tag.upper(), bond_dim=min(chi, 100), nroots=1)
    t0 = time.time()
    e = driver.dmrg(mpo, ket, n_sweeps=8, bond_dims=bond_dims, noises=noises,
                    thrds=thrds, iprint=2)   # iprint=2 -> per-sweep energy + discarded weight to stdout
    wall = time.time() - t0
    # discarded weight: block2 stores per-sweep discarded weights; take the last (converged-plateau) value.
    dw = None
    for attr in ("discarded_weights", "sweep_discarded_weights"):
        v = getattr(driver, attr, None)
        if v is not None and len(v):
            dw = float(np.asarray(v).ravel()[-1]); break
    if dw is None:
        # fallback: many block2 builds expose it on the internal dmrg object
        dm = getattr(driver, "_dmrg", None) or getattr(driver, "dmrg_obj", None)
        for attr in ("discarded_weights", "sweep_max_discarded_weight"):
            v = getattr(dm, attr, None) if dm is not None else None
            if v is not None:
                try: dw = float(np.asarray(v).ravel()[-1])
                except Exception: dw = float(v)
                break
    return dict(E_dmrg=float(e), chi=int(chi), dw=(float(dw) if dw is not None else None),
                wall_s=round(wall, 1), bond_dims=bond_dims)


def _linfit(x, y):
    """Least-squares y = a + b x; return (a, b, R2, a_stderr)."""
    x = np.asarray(x, float); y = np.asarray(y, float); n = len(x)
    A = np.vstack([np.ones(n), x]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    a, b = float(coef[0]), float(coef[1])
    yhat = a + b * x
    ss_res = float(np.sum((y - yhat) ** 2)); ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    # standard error of the intercept
    dof = max(n - 2, 1); s2 = ss_res / dof
    sxx = float(np.sum((x - x.mean()) ** 2))
    a_se = float(np.sqrt(s2 * (1.0 / n + x.mean() ** 2 / sxx))) if sxx > 0 else float("nan")
    return a, b, r2, a_se


def _committed_evar():
    """Box A's latest committed 40q QSCI variational energy (rigorous upper bound) + iter label."""
    fp = os.path.join(_RES, "e3_certificate_evidence.json")
    if not os.path.exists(fp):
        return None, None
    d = json.load(open(fp))
    pts = d.get("points", [])
    if not pts:
        return None, None
    p = pts[-1]
    return float(p["E_var"]), int(p.get("iter", -1))


def main():
    P = h20_integrals(20)
    print(f"[e6] H20 40q integrals ready: {P['active_space']} {P['qubits']}q | ladder chi={CHI_LADDER} "
          f"| threads={N_THREADS}", flush=True)
    rungs = []
    for chi in CHI_LADDER:
        R = run_dmrg_dw(P, chi, tag=f"h20_e6_chi{chi}")
        rungs.append(R)
        print(f"[e6] chi={chi:5d}  E={R['E_dmrg']:.10f}  dw={R['dw']}  {R['wall_s']}s", flush=True)

    # extrapolate E vs discarded weight dw -> dw=0 (truncation-free). Fall back to E vs 1/chi^2 if dw
    # unavailable from this block2 build.
    have_dw = all(r["dw"] is not None for r in rungs)
    if have_dw and len(rungs) >= FIT_MIN_RUNGS:
        xs = [r["dw"] for r in rungs]; abscissa = "discarded_weight"
    else:
        xs = [1.0 / r["chi"] ** 2 for r in rungs]; abscissa = "inv_chi_squared (dw unavailable)"
    ys = [r["E_dmrg"] for r in rungs]
    E0, slope, r2, E0_se = _linfit(xs, ys)

    fit_ok = (len(rungs) >= FIT_MIN_RUNGS) and (r2 >= FIT_MIN_R2)
    E_var, evar_iter = _committed_evar()
    abs_err_mHa = round((E_var - E0) * 1000, 4) if E_var is not None else None

    out = {
        "run": "e6_dmrg_extrap_40q",
        "role": "SUPPLEMENTARY independent absolute-accuracy anchor for the 40q flagship (NOT the "
                "pre-registered E3; box A's frozen E3 PT2 certificate stands unchanged and is reported alongside)",
        "system": "H20 chain STO-6G R=0.74, 40 qubits (identical to qsci_lib.hchain_problem(20))",
        "dmrg_schedule": "frozen E1/make_ref: n_sweeps=8, bond_dims=[100,150,200,chi*5], "
                         "noises=[1e-4,1e-5,1e-6,1e-7,0,0,0,0], thrds=[1e-8]*8, SU(2) — identical to "
                         "e1_chi800_counteraudit.run_dmrg (chi=400/800 rungs reproduce committed refs)",
        "chi_ladder": CHI_LADDER,
        "rungs": rungs,
        "extrapolation": {
            "model": "linear E = E0 + slope * x", "abscissa": abscissa,
            "E_fci_40q_estimate_Ha": E0, "E_fci_uncertainty_mHa": round(E0_se * 1000, 4),
            "slope": slope, "R2": round(r2, 6),
            "fit_gate": f">= {FIT_MIN_RUNGS} rungs and R2 >= {FIT_MIN_R2}", "fit_gate_pass": bool(fit_ok),
        },
        "certification": {
            "E_var_committed_Ha": E_var, "E_var_source_iter": evar_iter,
            "E_var_source": "results/e3_certificate_evidence.json (box A committed, latest iteration)",
            "absolute_error_mHa": abs_err_mHa,
            "chemical_accuracy_1p6": (abs_err_mHa is not None and abs(abs_err_mHa) <= 1.6),
            "prediction_i_equiv_0p5": (abs_err_mHa is not None and abs(abs_err_mHa) <= 0.5),
            "note": "absolute_error is E_var measured against an INDEPENDENT near-exact DMRG-extrapolated "
                    "reference (not the self-consistent PT2 estimate). As box A grows, E_var descends and "
                    "this gap closes; reported as-measured against whichever E_var is committed at read time.",
        },
        "honest_caveats": [
            "DMRG-extrapolated FCI is an estimate with a fit uncertainty (reported), not a rigorous "
            "two-sided bracket like E_var+PT2; standard practice (SHCI/DMRG literature) but stated as such.",
            "H20 is the DMRG-favourable quasi-1D case, so the extrapolation is tight here; this anchors the "
            "flagship system, it is not a claim about DMRG on strongly-2D/3D correlation.",
            "Supplementary and independent — box A's pre-registered E3 PT2 certificate is the primary "
            "route and is reported unchanged whatever its terminal (convergence / OOM / deadline).",
        ],
    }
    fn = os.path.join(_RES, "e6_dmrg_extrap_40q_evidence.json")
    json.dump(out, open(fn, "w"), indent=2)
    print(f"\n[e6] E_FCI(40q) extrap = {E0:.8f} +/- {E0_se*1000:.3f} mHa (R2={r2:.5f}, {abscissa}, "
          f"gate {'PASS' if fit_ok else 'FAIL'})", flush=True)
    if E_var is not None:
        print(f"[e6] E_var (box A it{evar_iter}) = {E_var:.8f}  ->  absolute error = {abs_err_mHa:+.3f} mHa "
              f"({'chem-acc' if abs(abs_err_mHa)<=1.6 else 'above 1.6'}"
              f"{'; <=0.5 (pred-i equiv)' if abs(abs_err_mHa)<=0.5 else ''})", flush=True)
    print(f"[e6] wrote {os.path.relpath(fn)}", flush=True)


if __name__ == "__main__":
    main()
