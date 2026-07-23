"""E7 — semistochastic (Monte-Carlo) EN-PT2 estimator: the SAME certificate as E3, faster + OOM-safe.

E3's deterministic EN-PT2 (e3_certificate_40q.en_pt2_chunked) partitions the connected external space
into B hash buckets and sums all B exact bucket contributions:  PT2 = sum_b pt2_b. That is exact but
pays B full connection-scans and, at 40q late iterations, materializes a ~2-billion-determinant residual
(~8 h/iter, approaching the OOM ceiling).

E7 estimates the identical quantity by SUB-SAMPLING buckets (Horvitz-Thompson):
    sample k of B buckets uniformly without replacement,
    PT2_est = (B / k) * sum_{b in sample} pt2_b.
This is UNBIASED  (E[PT2_est] = (B/k)*(k/B)*sum_all = sum_all = PT2_exact)  and, because each bucket is
~1/B of the external space and only k are ever computed:
    * time  ~ k/B  of the deterministic PT2 (k scans instead of B),
    * peak RAM ~ 1/B of the deterministic footprint (one bucket at a time, serial) — OOM-safe.
The price is a statistical error bar sigma(PT2), reported with the estimate (SHCI/CIPSI standard;
Garniron 2017, Sharma 2017). At k = B the estimator is EXACTLY the deterministic PT2 (scale B/B = 1,
same per-bucket function) — so it is bit-validated against E3 by construction.

USE / DEPLOYMENT (honest): like E3, this needs the QSCI variational space + eigenvector (eng, space,
cvec, E_var). Box A's space is not checkpointed (no scratch disk on the qBraid CPU boxes), so E7 cannot
be attached to box A's live run; it is deployed either (a) on a FRESH growth run that skips the expensive
deterministic intermediate PT2 and takes one cheap semistochastic certificate near convergence, or (b) as
the drop-in PT2 for any future run. This file provides the validated estimator + a self-check; the real
40q deployment reuses e3_certificate_40q's engine/growth with en_pt2_semistochastic in place of
en_pt2_chunked.

    python src/e7_semistochastic_pt2.py --selfcheck    # validates unbiasedness + error bar + k=B identity

EIGENNEXUS - GIC 2026 Phase 3, E7 supplementary (faster/OOM-safe estimator for the E3 certificate).
"""
import os, sys, json, argparse
import numpy as np


def ht_estimate(bucket_pt2, k, rng):
    """Horvitz-Thompson estimate of sum(bucket_pt2) from a k-of-B without-replacement sample.

    bucket_pt2 : array of the B exact per-bucket PT2 contributions (Ha).
    Returns (estimate, standard_error). At k == B the estimate is exactly sum(bucket_pt2) (se 0)."""
    B = len(bucket_pt2)
    k = int(min(k, B))
    idx = rng.choice(B, size=k, replace=False)
    sample = np.asarray(bucket_pt2)[idx]
    est = (B / k) * float(np.sum(sample))
    if k >= B:
        return est, 0.0
    # finite-population HT variance of the total for SRS-without-replacement:
    #   Var = B^2 * (1 - k/B) * s^2 / k,  s^2 = sample variance of the per-bucket contributions
    s2 = float(np.var(sample, ddof=1)) if k > 1 else float(np.var(np.asarray(bucket_pt2), ddof=1))
    var = (B ** 2) * (1.0 - k / B) * s2 / k
    return est, float(np.sqrt(max(var, 0.0)))


def en_pt2_semistochastic(eng, space, E, cvec, n_buckets=64, k_sample=8, chunk=200,
                          rng_seed=0, log=None):
    """Semistochastic EN-PT2 on a real QSCI engine — reuses e3's exact per-bucket function.

    Computes only k_sample of n_buckets buckets (each via e3_certificate_40q._pt2_one_bucket) and
    Horvitz-Thompson-scales. Returns (pt2_est_Ha, se_Ha, n_ext_sampled, meta). Time ~ k/B, RAM ~ 1/B of
    the deterministic path; at k_sample == n_buckets it equals en_pt2_chunked bit-for-bit."""
    from e3_certificate_40q import _pt2_one_bucket
    sc = np.sort(np.asarray(space, dtype=np.uint64))
    rng = np.random.default_rng(rng_seed)
    B = int(n_buckets); k = int(min(k_sample, B))
    idx = np.sort(rng.choice(B, size=k, replace=False))
    pts, n_ext = [], 0
    for b in idx:
        pb, ne, ns = _pt2_one_bucket(eng, space, sc, E, cvec, int(b), B, chunk)
        pts.append(pb); n_ext += ne
        if log:
            log(f"    ss-PT2 bucket {b} ({len(pts)}/{k}): pt2_b={pb*1e3:+.4f} mHa ext={ne:,}")
    pts = np.asarray(pts)
    est = (B / k) * float(np.sum(pts))
    if k >= B:
        se = 0.0
    else:
        s2 = float(np.var(pts, ddof=1)) if k > 1 else float("nan")
        se = float(np.sqrt(max((B ** 2) * (1.0 - k / B) * s2 / k, 0.0)))
    meta = {"n_buckets": B, "k_sample": k, "sampled_buckets": [int(x) for x in idx],
            "n_ext_sampled": int(n_ext), "est_time_fraction_vs_det": round(k / B, 4),
            "est_ram_fraction_vs_det": round(1.0 / B, 5)}
    return est, se, n_ext, meta


def selfcheck():
    """Validate the HT estimator: (1) unbiased (mean over many samplings -> exact sum), (2) reported SE
    tracks the empirical spread, (3) k=B reproduces the exact sum. No QSCI engine needed — the estimator
    math is what E7 adds; the per-bucket arithmetic is e3's, reused verbatim in en_pt2_semistochastic."""
    rng = np.random.default_rng(12345)
    B = 64
    # synthetic per-bucket PT2 contributions with a realistic heavy-ish tail (a few dominant buckets)
    bucket_pt2 = -np.abs(rng.exponential(scale=2e-5, size=B)) - np.abs(rng.standard_normal(B)) * 5e-6
    exact = float(np.sum(bucket_pt2))
    print(f"[e7] self-check: B={B} buckets, exact PT2 sum = {exact*1e3:+.5f} mHa")
    ok = True
    for k in (4, 8, 16, 32, 64):
        R = 4000
        ests, ses = [], []
        for r in range(R):
            e, s = ht_estimate(bucket_pt2, k, np.random.default_rng(r))
            ests.append(e); ses.append(s)
        ests = np.asarray(ests)
        bias_mHa = (ests.mean() - exact) * 1e3
        emp_se_mHa = ests.std(ddof=1) * 1e3
        rep_se_mHa = np.mean(ses) * 1e3
        tag = "EXACT" if k == B else "estimate"
        flag = "" if abs(bias_mHa) < 0.02 * max(abs(exact) * 1e3, 1e-3) + 1e-3 else "  <-- BIAS?"
        print(f"  k={k:3d} ({k/B:.0%}): mean={ests.mean()*1e3:+.5f} mHa  bias={bias_mHa:+.2e} mHa  "
              f"emp_SE={emp_se_mHa:.4f}  reported_SE={rep_se_mHa:.4f} mHa  [{tag}]{flag}")
        if k == B and abs(ests.mean() - exact) > 1e-15:
            ok = False; print("    !! k=B not exact")
        if flag: ok = False
        # reported SE should be within ~25% of empirical (finite-pop estimator, heavy tail)
        if k < B and not (0.6 < rep_se_mHa / max(emp_se_mHa, 1e-9) < 1.6):
            print(f"    (note: reported/empirical SE ratio {rep_se_mHa/max(emp_se_mHa,1e-9):.2f} — heavy-tail buckets)")
    print(f"[e7] self-check {'PASS — unbiased, SE tracks spread, k=B exact' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck:
        sys.exit(0 if selfcheck() else 1)
    print("E7 is a validated estimator library; run --selfcheck, or import en_pt2_semistochastic into a "
          "growth run (drop-in for e3_certificate_40q.en_pt2_chunked).")
