"""E3 — 40q flagship to certificate convergence (frozen protocol, preregistration_v2.json).

MP2-seeded qsci_fast on H20/40q (IDENTICAL committed engine + seed recipe as the flagship run),
GROW_PER_ITER=150,000, KCAP=2,000,000, with the Epstein-Nesbet PT2 certificate evaluated at EVERY
growth iteration over the COMPLETE connected external space — the same formula as the committed
selci_pt2 validation (numerator sum_i H_ui c_i over ALL subspace sources, denominator E_var - H_uu,
|den| > 1e-6 screen counted and reported), evaluated CHUNKED:

  * source determinants are scanned in vectorized chunks through the committed PauliEngine term
    masks — the exact code shape of qsci_fast's own candidate scan (engine identity, no new physics);
  * the external space is partitioned into hash buckets ((u * golden) >> 32 mod B); each bucket is
    accumulated and reduced independently, bounding peak memory at ~1/B of the full external space.
    The bucket sum equals the full sum exactly (each external det belongs to exactly one bucket).

Driver mechanics: qsci_fast is advanced ONE iteration at a time through its own state-file resume
(bit-exact trajectory per its docstring); after each iteration the state (space in insertion order,
E, eigenvector) is read back and the certificate evaluated on it.

Frozen predictions (judged independently, as-is):
  i  : |dE_PT2| <= 0.5 mHa before kcap (certificate convergence at flagship scale)
  ii : terminal E_var <= +0.9 mHa vs the committed chi=400 reference (-10.292194);
       also reported vs the E1 chi=800 reference
  iii: determinant budget at certificate convergence within half a decade of 1.13e6
       (i.e. [1.13e6/sqrt(10), 1.13e6*sqrt(10)] ~= [357k, 3.57M])

Smoke (container CPU): python src/e3_certificate_40q.py --smoke 6
  (H6 toy: full loop with per-iteration PT2; PT2 cross-validated numerically against the committed
   selci_pt2.Engine.en_pt2 on the identical space/eigenvector, and the bracket checked vs FCI.)
Production:            python src/e3_certificate_40q.py      (env: GROW_ITERS/STATE_FILE/PT2_BUCKETS)
EIGENNEXUS - GIC 2026 Phase 3, extension E3.
"""
import os, sys, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import qsci_lib as L

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
E_CHI400 = -10.292194              # frozen literal (prereg E3 prediction ii)
CERT_MHA = 0.5                     # frozen prediction i
VAR_MHA = 0.9                      # frozen prediction ii
DET_CENTER = 1.13e6                # frozen prediction iii (half a decade each way)
GROW_PER_ITER = 150_000            # frozen
KCAP = 2_000_000                   # frozen
GROW_ITERS = int(os.environ.get("GROW_ITERS", 40))
PT2_BUCKETS = int(os.environ.get("PT2_BUCKETS", 8))
_GOLD = np.uint64(0x9E3779B97F4A7C15)


def en_pt2_chunked(eng, space, E, cvec, n_buckets=8, chunk=200, log=None):
    """EN-PT2 over the complete connected external space; committed selci_pt2 formula, hash-bucketed.
    Returns (pt2_Ha, n_external_dets, n_denominator_screened)."""
    sc = np.sort(np.asarray(space, dtype=np.uint64))
    pt2 = 0.0
    n_ext = 0
    n_scr = 0
    with np.errstate(over="ignore"):
        for b in range(n_buckets):
            cand = np.empty(0, dtype=np.uint64)
            num = np.empty(0, dtype=np.complex128)
            bu, ba, nbuf = [], [], 0

            def _reduce():
                nonlocal cand, num, bu, ba, nbuf
                allu = np.concatenate([cand] + bu)
                alla = np.concatenate([num] + ba)
                cand, inv = np.unique(allu, return_inverse=True)
                num = np.zeros(len(cand), dtype=np.complex128)
                np.add.at(num, inv, alla)
                bu, ba, nbuf = [], [], 0

            for c0 in range(0, len(space), chunk):
                d = np.asarray(space[c0:c0 + chunk], dtype=np.uint64)
                cc = np.asarray(cvec[c0:c0 + chunk])
                new = np.bitwise_xor(d[:, None], eng.XM[None, :])
                par = L._parity((d[:, None] & eng.ZYM[None, :]).reshape(-1)).reshape(new.shape)
                amp = (eng.PH[None, :] * (1 - 2 * par.astype(np.int64))) * cc[:, None]
                u = new.reshape(-1)
                aa = amp.reshape(-1)
                pos = np.clip(np.searchsorted(sc, u), 0, len(sc) - 1)
                ext = sc[pos] != u
                u = u[ext]; aa = aa[ext]
                hb = ((u * _GOLD) >> np.uint64(32)) % np.uint64(n_buckets)
                m = hb == np.uint64(b)
                if m.any():
                    bu.append(u[m]); ba.append(aa[m]); nbuf += int(m.sum())
                if nbuf > 20_000_000:
                    _reduce()
            _reduce()
            if len(cand) == 0:
                continue
            den = E - eng.diag(cand)
            keep = np.abs(den) > 1e-6                      # committed intruder screen, counted
            n_scr += int((~keep).sum())
            n_ext += len(cand)
            pt2 += float(np.sum((np.abs(num[keep]) ** 2) / den[keep]))
            if log:
                log(f"    PT2 bucket {b+1}/{n_buckets}: ext={len(cand):,} cum={pt2*1e3:+.3f} mHa")
    return pt2, n_ext, n_scr


def mp2_seed_dets(P, exc):
    hf = L.hf_det(P["ne"]); seed = {hf}
    for p, q, r, s in zip(exc["p"], exc["q"], exc["r"], exc["s"]):
        d = (hf & ~((1 << p) | (1 << q))) | (1 << r) | (1 << s)
        if bin(d).count("1") == P["ne"]: seed.add(d)
    return seed


def _load_state(fn):
    z = np.load(fn)
    space = z["space"].astype(np.uint64)      # insertion order == eigenvector order
    E = float(z["E"]); cvec = z["cvec"]; it = int(z["it"])
    z.close()
    return space, E, cvec, it


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", type=int, default=0)
    a = ap.parse_args()
    t0 = time.time()

    if a.smoke:
        P = L.hchain_problem(a.smoke, do_fci=True)
        exc = L.mp2_excitation_lists(P["t2"], P["nocc"], P["nq"], top_m=16)
        seed = mp2_seed_dets(P, exc)
        eng = L.PauliEngine(P["qop"].terms)
        sf = os.path.join(_RES, f"e3_smoke_h{a.smoke}_state.npz")
        if os.path.exists(sf): os.remove(sf)
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "encoder"))
        import selci_pt2 as SP
        ref_eng = SP.Engine(P["qop"].terms)
        ok = True
        for it in range(1, 7):
            E, space = eng.qsci_fast(seed, grow_iters=it, grow_per_iter=30, kcap=10**6,
                                     state_file=sf)
            sp_ins, E_s, cvec, _ = _load_state(sf)
            pt2, ne_, ns_ = en_pt2_chunked(eng, sp_ins, E_s, cvec, n_buckets=4)
            pt2_ref, ne_ref, _ = ref_eng.en_pt2(sp_ins, E_s, cvec)
            d_formula = abs(pt2 - pt2_ref)
            ok &= d_formula < 1e-9 and ne_ == ne_ref
            print(f"E3 SMOKE it{it}: dets={len(sp_ins):4d} E_var-FCI={(E_s-P['e_fci'])*1e3:+8.3f} "
                  f"E_var+PT2-FCI={(E_s+pt2-P['e_fci'])*1e3:+8.3f} mHa | "
                  f"PT2 vs committed formula: |d|={d_formula:.2e} Ha ext {ne_}=={ne_ref} "
                  f"{'OK' if d_formula < 1e-9 else 'MISMATCH'}", flush=True)
        if os.path.exists(sf): os.remove(sf)
        print("E3 SMOKE:", "FORMULA VALIDATED (matches committed selci_pt2 en_pt2 bit-for-bit scale)"
              if ok else "FAILED", flush=True)
        sys.exit(0 if ok else 1)

    P = L.hchain_problem(20, do_fci=False)
    exc = L.mp2_excitation_lists(P["t2"], P["nocc"], P["nq"], top_m=256)
    seed = mp2_seed_dets(P, exc)
    e800 = float(json.load(open(os.path.join(_RES, "h20_40q_dmrg_chi800.json")))["E_dmrg"])
    print(f"E3: H20 40q certificate run | seed MP2 top256 ({len(seed)}) | "
          f"grow {GROW_ITERS}x{GROW_PER_ITER} kcap {KCAP} | PT2 buckets {PT2_BUCKETS}", flush=True)

    eng = L.PauliEngine(P["qop"].terms)
    sf = os.environ.get("STATE_FILE", os.path.join(_RES, "e3_certificate_state.npz"))
    ev_fn = os.path.join(_RES, "e3_certificate_evidence.json")
    points = []
    converged_at = None
    for it in range(1, GROW_ITERS + 1):
        E, space = eng.qsci_fast(seed, grow_iters=it, grow_per_iter=GROW_PER_ITER, kcap=KCAP,
                                 log=lambda m: print(m, flush=True), state_file=sf)
        sp_ins, E_s, cvec, it_s = _load_state(sf)
        tp = time.time()
        pt2, n_ext, n_scr = en_pt2_chunked(eng, sp_ins, E_s, cvec, n_buckets=PT2_BUCKETS,
                                           log=lambda m: print(m, flush=True))
        pt = dict(iter=it_s, dets=int(len(sp_ins)), E_var=E_s, pt2_mHa=round(pt2 * 1e3, 4),
                  E_est=E_s + pt2, n_external=int(n_ext), n_den_screened=int(n_scr),
                  var_err_vs_chi400_mHa=round((E_s - E_CHI400) * 1e3, 3),
                  var_err_vs_chi800_mHa=round((E_s - e800) * 1e3, 3),
                  pt2_wall_s=round(time.time() - tp, 1))
        points.append(pt)
        json.dump(dict(status="IN-PROGRESS (partial, not final)", run="e3_certificate_40q",
                       points=points), open(ev_fn, "w"), indent=2)
        print(f"  E3 it{it_s}: dets={pt['dets']:,} E_var={E_s:.6f} "
              f"(chi400 {pt['var_err_vs_chi400_mHa']:+.3f} / chi800 {pt['var_err_vs_chi800_mHa']:+.3f} mHa) "
              f"| PT2 {pt['pt2_mHa']:+.4f} mHa (ext {n_ext:,}, scr {n_scr}) "
              f"[pt2 {pt['pt2_wall_s']}s]", flush=True)
        if abs(pt2) * 1e3 <= CERT_MHA:
            converged_at = pt
            print(f"  CERTIFICATE CONVERGED: |PT2| <= {CERT_MHA} mHa at {pt['dets']:,} dets", flush=True)
            break
        if len(sp_ins) >= KCAP:
            print("  kcap reached before certificate convergence", flush=True)
            break

    term = points[-1]
    band = (DET_CENTER / 10 ** 0.5, DET_CENTER * 10 ** 0.5)
    p_i = converged_at is not None
    p_ii = term["E_var"] <= E_CHI400 + VAR_MHA * 1e-3
    p_iii = bool(converged_at and band[0] <= converged_at["dets"] <= band[1])
    out = dict(run="e3_certificate_40q", system="H20", qubits=40,
               engine="qsci_fast (identical committed engine); EN-PT2 per committed selci_pt2 "
                      "formula, chunked (hash-bucketed external space), validated in --smoke",
               points=points, terminal=term, certificate_converged_at=converged_at,
               peak_host_rss_gb=round(L.peak_rss_gb(), 2), wall_s=round(time.time() - t0, 1),
               prereg=dict(
                   prediction_i_certificate=dict(hit=bool(p_i), threshold_mHa=CERT_MHA),
                   prediction_ii_var_bound=dict(hit=bool(p_ii), e_chi400=E_CHI400, tol_mHa=VAR_MHA,
                                                also_vs_chi800_mHa=term["var_err_vs_chi800_mHa"]),
                   prediction_iii_det_budget=dict(hit=p_iii, band=[round(band[0]), round(band[1])],
                                                  center=DET_CENTER)))
    json.dump(out, open(ev_fn, "w"), indent=2)
    print(f"\nE3 TERMINAL: dets={term['dets']:,} E_var={term['E_var']:.6f} PT2={term['pt2_mHa']:+.4f} mHa | "
          f"pred_i={'PASS' if p_i else 'FAIL'} pred_ii={'PASS' if p_ii else 'FAIL'} "
          f"pred_iii={'PASS' if p_iii else 'FAIL'} | {out['wall_s']}s", flush=True)
    print(f"saved {os.path.relpath(ev_fn)}", flush=True)


if __name__ == "__main__":
    main()
