"""Regenerate the PLATFORM-VERIFIED sections of results/credit_ledger.json from qBraid records.

Run on a machine with qBraid credentials (~/.qbraid/qbraidrc):
    python src/generate_credit_ledger.py            # fetch + print, no write
    python src/generate_credit_ledger.py --write    # merge into the ledger and save

What becomes platform-verified (traceable to records, not typed):
  * wallet balance        -> appended as a timestamped snapshot (method: qBraid API)
  * quantum job history   -> per-job lines with qBraid job IDs, device, cost, timestamps, tags
What stays DECLARED (facts the API cannot know, labeled as such in the ledger):
  * organizer top-up amounts and the 50% share agreement (organizer email is the record)
  * the personally-funded list (personal-account billing is the record, outside this pool)
  * GPU Lab instance line items, IF the billing API does not expose per-instance usage — then
    instance spend remains bracketed by wallet-snapshot deltas and is labeled so. Every snapshot
    this script appends tightens those brackets.

Honesty rule: this script never invents a number. Anything it cannot fetch it reports as
UNAVAILABLE and leaves the ledger's declared sections untouched.
"""
import json, os, sys, time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LEDGER = os.path.join(_ROOT, "results", "credit_ledger.json")


class _RestSession:
    """Minimal qBraid REST client from ~/.qbraid/qbraidrc — used when qbraid_core is absent."""
    def __init__(self):
        import configparser, requests
        rc = os.path.expanduser("~/.qbraid/qbraidrc")
        cp = configparser.ConfigParser(); cp.read(rc)
        sec = (cp.sections() or ["default"])[0]
        self.key = cp.get(sec, "api-key", fallback=None) or cp.get(sec, "api_key")
        self.base = (cp.get(sec, "url", fallback="https://api.qbraid.com/api")).rstrip("/")
        self._rq = requests
        if not self.key:
            raise RuntimeError("no api-key in qbraidrc")

    def get(self, path, params=None):
        for hdr in ({"api-key": self.key}, {"X-API-Key": self.key}):
            r = self._rq.get(self.base + path, headers=hdr, params=params, timeout=30)
            if r.status_code != 401:
                return r
        return r


def _session():
    try:
        from qbraid_core import QbraidSession
        return QbraidSession()
    except Exception:
        return _RestSession()   # raw REST fallback, no qBraid packages required


def fetch_balance(s):
    for path in ("/billing/credits/get-user-credits", "/user/credits"):
        try:
            r = s.get(path).json()
            for k in ("qbraidCredits", "credits", "balance"):
                if isinstance(r, dict) and k in r:
                    return float(r[k]), path
        except Exception:
            continue
    return None, None


def fetch_jobs(s, max_pages=20):
    """Quantum-job records with IDs/cost/tags. Tries the known endpoint shapes; returns list."""
    jobs = []
    for path in ("/quantum-jobs", "/quantum-jobs/list"):
        try:
            page = 0
            while page < max_pages:
                r = s.get(path, params={"resultsPerPage": 100, "page": page}).json()
                arr = r.get("jobsArray") if isinstance(r, dict) else (r if isinstance(r, list) else None)
                if arr is None and isinstance(r, dict):
                    arr = r.get("jobs") or r.get("data")
                if not arr:
                    break
                for j in arr:
                    jobs.append({
                        "job_id": j.get("qbraidJobId") or j.get("id") or j.get("_id"),
                        "device": j.get("qbraidDeviceId") or j.get("deviceId"),
                        "status": j.get("status"),
                        "cost_credits": j.get("cost") or j.get("costCredits") or j.get("credits"),
                        "created": j.get("createdAt") or j.get("timeStamps", {}).get("createdAt"),
                        "tags": j.get("tags"),
                        "shots": j.get("shots"),
                    })
                page += 1
            if jobs:
                return jobs, path
        except Exception:
            continue
    return jobs, None


def fetch_instance_usage(s):
    """Per-instance Lab billing, if exposed. Returns (records, path) or ([], None) -> UNAVAILABLE."""
    for path in ("/billing/usage", "/lab/instances/usage", "/billing/invoices"):
        try:
            r = s.get(path).json()
            if r:
                return r, path
        except Exception:
            continue
    return [], None


def main():
    try:
        s = _session()
    except Exception as e:
        print(f"SKIP  no qBraid credentials on this machine ({type(e).__name__}); "
              f"run on a box with ~/.qbraid/qbraidrc")
        sys.exit(0)

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    bal, bal_src = fetch_balance(s)
    jobs, jobs_src = fetch_jobs(s)
    usage, usage_src = fetch_instance_usage(s)

    print(f"balance : {bal if bal is not None else 'UNAVAILABLE'}"
          + (f"  (endpoint {bal_src})" if bal_src else ""))
    print(f"jobs    : {len(jobs)} records" + (f"  (endpoint {jobs_src})" if jobs_src else "  UNAVAILABLE"))
    priced = [j for j in jobs if j.get("cost_credits")]
    if priced:
        print(f"          priced jobs total: {sum(float(j['cost_credits']) for j in priced):,.2f} cr")
    print(f"usage   : " + (f"records via {usage_src}" if usage_src else
          "per-instance billing UNAVAILABLE via API -> instance spend stays snapshot-bracketed (labeled)"))

    if "--write" not in sys.argv:
        print("dry run — pass --write to merge into results/credit_ledger.json")
        return

    L = json.load(open(_LEDGER))
    if bal is not None:
        L["wallet_snapshots"].append(dict(
            utc=now, balance=bal, method=f"qBraid API {bal_src} via generate_credit_ledger.py",
            note="platform-verified snapshot"))
    L["platform_records"] = dict(
        generated_utc=now,
        quantum_jobs=jobs,
        quantum_jobs_endpoint=jobs_src,
        instance_usage=usage if usage_src else "UNAVAILABLE via API at generation time",
        instance_usage_endpoint=usage_src,
        note="Everything here is fetched, never typed. Declared sections (top-ups, share, "
             "personally-funded) remain declared and labeled — their records live with the "
             "organizers / personal billing.")
    json.dump(L, open(_LEDGER, "w"), indent=2)
    print(f"WROTE {_LEDGER} — run 'python src/verify_credits.py' next, then commit both.")


if __name__ == "__main__":
    main()
