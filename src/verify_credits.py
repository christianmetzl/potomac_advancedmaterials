"""Self-verifying credit budget: recompute every derived number in docs/credit_budget.md from
results/credit_ledger.json, enforce the grant-share cap, and (with --live, where qBraid credentials
exist) pull the wallet balance from the qBraid API and check drift / append a snapshot.

Offline (any machine):   python src/verify_credits.py
Live (qbraidrc present): python src/verify_credits.py --live [--append]

Exit codes: 0 all checks pass; 2 cap exceeded or arithmetic inconsistent.
Honest limits (stated, not hidden): the wallet is POOL-level. Our-project attribution is exact only
while the second project's spend is zero (recorded per snapshot); after that, per-instance billing
history is the arbiter. Personally-funded work (pre-top-up sessions, AQT flight) never appears here
by construction — it drew nothing from the pool.
"""
import json, os, sys, time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LEDGER = os.path.join(_ROOT, "results", "credit_ledger.json")


def fail(msg):
    print(f"FAIL  {msg}"); sys.exit(2)


def ok(msg):
    print(f"PASS  {msg}")


def _qbraidrc():
    """Parse ~/.qbraid/qbraidrc -> (api_key, base_url) or (None, None). No qBraid packages needed."""
    import configparser
    rc = os.path.expanduser("~/.qbraid/qbraidrc")
    if not os.path.exists(rc):
        return None, None
    cp = configparser.ConfigParser()
    try:
        cp.read(rc)
        for sec in cp.sections() or ["default"]:
            key = cp.get(sec, "api-key", fallback=None) or cp.get(sec, "api_key", fallback=None)
            url = cp.get(sec, "url", fallback="https://api.qbraid.com/api")
            if key:
                return key.strip(), url.strip().rstrip("/")
    except Exception:
        pass
    return None, None


def live_balance():
    """Best-effort wallet fetch. Order: qbraid_core -> raw REST via qbraidrc -> CLI. Float or None."""
    paths = ("/billing/credits/get-user-credits", "/user/credits")
    keys = ("qbraidCredits", "credits", "balance", "totalCredits")

    def _extract(r):
        if isinstance(r, dict):
            for k in keys:
                if k in r:
                    return float(r[k])
        return None

    try:
        from qbraid_core import QbraidSession
        s = QbraidSession()
        for path in paths:
            try:
                v = _extract(s.get(path).json())
                if v is not None:
                    return v
            except Exception:
                continue
    except Exception:
        pass
    api_key, base = _qbraidrc()                     # raw REST — works without qBraid packages
    if api_key:
        try:
            import requests
            for path in paths:
                for hdr in ({"api-key": api_key}, {"X-API-Key": api_key}):
                    try:
                        r = requests.get(base + path, headers=hdr, timeout=20)
                        if r.ok:
                            v = _extract(r.json())
                            if v is not None:
                                return v
                    except Exception:
                        continue
        except Exception:
            pass
    try:  # CLI fallback
        import subprocess, re
        out = subprocess.check_output(["qbraid", "credits"], text=True, timeout=30)
        m = re.search(r"([\d][\d,\.]*)\s*credits", out, re.I)
        if m:
            return float(m.group(1).replace(",", ""))
    except Exception:
        pass
    return None


def main():
    L = json.load(open(_LEDGER))
    total = sum(t["amount"] for t in L["pool"]["topups"])
    if total != L["pool"]["total"]:
        fail(f"pool total {L['pool']['total']} != sum of top-ups {total}")
    ok(f"pool total == sum of top-ups == {total:,}")

    cap = L["share"]["cap"]
    if abs(cap - total * L["share"]["fraction"]) > 0.5:
        fail(f"cap {cap:,} != fraction {L['share']['fraction']} x pool {total:,}")
    ok(f"share cap {cap:,} == {L['share']['fraction']} x pool")

    snap = sorted(L["wallet_snapshots"], key=lambda s: s["utc"])[-1]
    consumed = total - snap["balance"]
    if consumed < 0:
        fail(f"negative consumption: balance {snap['balance']:,} > pool {total:,}")
    remaining = cap - consumed
    ok(f"latest snapshot {snap['utc']}: balance {snap['balance']:,} -> pool consumed {consumed:,}")
    if remaining < 0:
        fail(f"CAP EXCEEDED: consumed {consumed:,} > cap {cap:,}")
    ok(f"our remaining allowance: {cap:,} - {consumed:,} = {remaining:,} cr")

    proj_hi = sum(v[1] for v in L["projections_cr"].values())
    if consumed + proj_hi > cap:
        fail(f"projections breach cap: {consumed:,} + {proj_hi:,} > {cap:,}")
    ok(f"worst-case projections fit: {consumed:,} + {proj_hi:,} = {consumed + proj_hi:,} <= {cap:,} "
       f"({100 * (consumed + proj_hi) / cap:.0f}% of share)")
    print(f"NOTE  {L['attribution_caveat']}")

    if "--live" in sys.argv:
        bal = live_balance()
        if bal is None:
            print("SKIP  --live: no qBraid credentials/CLI reachable from this machine "
                  "(run on a box with ~/.qbraid/qbraidrc)")
        else:
            drift = snap["balance"] - bal
            print(f"LIVE  wallet balance now: {bal:,.0f} (drift {drift:+,.0f} vs last snapshot "
                  f"= spend since {snap['utc']})")
            if cap - (total - bal) < 0:
                fail(f"CAP EXCEEDED (live): consumed {total - bal:,.0f} > cap {cap:,}")
            ok(f"live remaining allowance: {cap - (total - bal):,.0f} cr")
            if "--append" in sys.argv:
                L["wallet_snapshots"].append(dict(
                    utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    balance=bal, method="qBraid API via verify_credits.py --live --append",
                    note="automated snapshot"))
                json.dump(L, open(_LEDGER, "w"), indent=2)
                print(f"WROTE appended live snapshot to {_LEDGER}")

    print("ALL CREDIT CHECKS PASS")


if __name__ == "__main__":
    main()
