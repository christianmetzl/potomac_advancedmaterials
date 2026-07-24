#!/usr/bin/env python3
"""cli.py — prove the whole submission in one line (offline, no credentials).

    python cli.py verify          # full self-check: reproduce.py (26 checks incl. the cost audit)
    python cli.py verify --quick  # faster subset (skips the slow re-executions)
    python cli.py cost            # just the cost audit (published pricing x committed configs)
    python cli.py objections      # print the pre-answered hostile-reviewer red-team

`verify` re-executes the CPU-tier results from a clean state and audits the committed GPU/QPU/cost
artifacts, then prints a single verdict. Everything traces to docs/claims_ledger.md.
"""
import os, sys, subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "src")


def _run(script, *args):
    return subprocess.call([sys.executable, os.path.join(_SRC, script), *args])


def main():
    argv = sys.argv[1:]
    cmd = argv[0] if argv else "verify"
    rest = argv[1:]

    if cmd == "verify":
        print("=" * 78)
        print("MATGEN-Q — full submission self-check (offline, no credentials required)")
        print("=" * 78)
        rc = _run("reproduce.py", *rest)     # 26 checks, incl. cost_audit as check #26
        print("=" * 78)
        print("SUBMISSION VERIFIED — all self-checks green." if rc == 0 else
              "SELF-CHECK REPORTED FAILURES — see the PASS/FAIL table above.")
        print("Every claim traces to docs/claims_ledger.md; the red-team is pre-answered in "
              "results/ANTICIPATED_OBJECTIONS.md.")
        return rc

    if cmd == "cost":
        return _run("cost_audit.py", *rest)

    if cmd == "objections":
        p = os.path.join(_HERE, "results", "ANTICIPATED_OBJECTIONS.md")
        sys.stdout.write(open(p, encoding="utf-8").read())
        return 0

    if cmd in ("-h", "--help", "help"):
        sys.stdout.write(__doc__)
        return 0

    print(f"unknown command: {cmd}\n")
    sys.stdout.write(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
