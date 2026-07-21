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
    import subprocess, re
    for cmd in (["qbraid", "account", "credits"], ["qbraid", "credits"]):   # CLI fallback, both eras
        try:
            out = subprocess.check_output(cmd, text=True, timeout=30, stderr=subprocess.DEVNULL)
            m = (re.search(r"credits?[^0-9]*([0-9][0-9,\.]*)", out, re.I)
                 or re.search(r"([0-9][0-9,\.]*)\s*credits", out, re.I))
            if m:
                return float(m.group(1).rstrip(".").replace(",", ""))
        except Exception:
            continue
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
    ok(f"latest snapshot {snap['utc']}: balance {snap['balance']:,} -> POOL consumed {consumed:,.1f}")

    # ---- attribution-aware accounting (2026-07-21): the pool is shared; the cap governs OUR spend.
    # OUR spend = settled campaign figure + per-instance E-campaign lines (qBraid console billing,
    # appended by the box operators at each shutdown). Pool-minus-ours = the second project's draw.
    att = L.get("attributed_spend_cr", {})
    our_spent = float(att.get("settled_campaign_2026-07-19", consumed))
    inst = att.get("e_campaign_instances", [])
    our_spent += sum(float(x.get("cr", 0)) for x in inst if isinstance(x, dict))
    other_draw = max(0.0, consumed - our_spent)
    remaining = cap - our_spent
    ok(f"OUR attributed spend: {our_spent:,.1f} cr ({len(inst)} E-campaign instance lines); "
       f"second project's draw: {other_draw:,.1f} cr")
    if remaining < 0:
        fail(f"CAP EXCEEDED: OUR attributed spend {our_spent:,.1f} > cap {cap:,}")
    ok(f"our remaining allowance: {cap:,} - {our_spent:,.1f} = {remaining:,.1f} cr")

    def _proj_hi(v):
        """Worst-case credits from a projection entry: plain [lo, hi] lists, or authorization
        dicts (uses their 'total' [lo, hi] when present to avoid double-counting per-run lines,
        else sums nested entries; strings/metadata contribute 0)."""
        if isinstance(v, (list, tuple)) and len(v) >= 2 and all(isinstance(x, (int, float)) for x in v[:2]):
            return v[1]
        if isinstance(v, dict):
            t = v.get("total")
            if isinstance(t, (list, tuple)) and len(t) >= 2:
                return t[1]
            return sum(_proj_hi(x) for x in v.values())
        return 0

    proj_hi = sum(_proj_hi(v) for v in L["projections_cr"].values())
    if our_spent + proj_hi > cap:
        fail(f"projections breach cap: OUR {our_spent:,.1f} + {proj_hi:,} > {cap:,}")
    ok(f"worst-case projections fit OUR cap: {our_spent:,.1f} + {proj_hi:,} = "
       f"{our_spent + proj_hi:,.1f} <= {cap:,} ({100 * (our_spent + proj_hi) / cap:.0f}% of share)")

    # ---- pool RUNWAY: entitlement is not availability. The pool is first-come-first-served;
    # if the other project drains it, our unspent allowance becomes unusable regardless of the cap.
    if snap["balance"] < proj_hi:
        fail(f"POOL RUNWAY EXHAUSTED: balance {snap['balance']:,} < our remaining worst-case "
             f"projection {proj_hi:,} — escalate to organizers (per-project accounting)")
    elif snap["balance"] < 1.5 * proj_hi:
        print(f"WARN  pool runway tight: balance {snap['balance']:,} vs our remaining worst-case "
              f"{proj_hi:,} ({snap['balance'] / proj_hi:.1f}x). The second project's continued draw "
              f"could strand our allowance — prioritize launches, re-check at every handover.")
    else:
        ok(f"pool runway: balance {snap['balance']:,} covers our remaining worst-case {proj_hi:,} "
           f"({snap['balance'] / max(proj_hi, 1):.1f}x)")
    print(f"NOTE  {L['attribution_caveat']}")

    if "--live" in sys.argv:
        bal = live_balance()
        if bal is None:
            print("SKIP  --live: no qBraid credentials/CLI reachable from this machine "
                  "(run on a box with ~/.qbraid/qbraidrc)")
        elif bal < 0.06 * total:
            # A grant-pool wallet reading this low is either the WRONG ORG's wallet (the personal
            # org sits ~5k) or a pool nearly drained by the other project — both demand a human
            # look before anything is auto-appended.
            print(f"WARN  --live: fetched balance {bal:,.0f} is <6% of the {total:,} pool. Either "
                  f"this machine's qBraid credentials point at a DIFFERENT org's wallet (personal "
                  f"vs EIGENNEXUS grant), or the pool is nearly exhausted. NOT appending; verify "
                  f"the org (qbraid account credits vs the grant console) and record a labeled "
                  f"manual snapshot if this reading is intentional.")
        else:
            drift = snap["balance"] - bal
            print(f"LIVE  wallet balance now: {bal:,.0f} (drift {drift:+,.0f} vs last snapshot "
                  f"{snap['utc']} — pool-level, includes the second project's draw)")
            if bal < proj_hi:
                fail(f"POOL RUNWAY EXHAUSTED (live): balance {bal:,.0f} < our remaining "
                     f"worst-case projection {proj_hi:,}")
            elif bal < 1.5 * proj_hi:
                print(f"WARN  pool runway tight (live): {bal:,.0f} vs our remaining worst-case "
                      f"{proj_hi:,} ({bal / proj_hi:.1f}x)")
            else:
                ok(f"pool runway (live): {bal:,.0f} covers our remaining worst-case {proj_hi:,}")
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
