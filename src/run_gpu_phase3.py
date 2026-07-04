"""Phase-3 GPU-day driver: executes the pre-registered run-list in priority order, logging everything.

Usage on qBraid GPU (after credits land):
    python src/run_gpu_phase3.py                 # full list, priority order
    python src/run_gpu_phase3.py --only 1 5      # subset
    python src/run_gpu_phase3.py --dry-run       # CPU smoke versions of every run (works today)

Priority order maximizes score-per-GPU-hour: the 40q headline first, then exact validation,
then the 38q reach, then QPU. Each run writes its own results/*_evidence.json and prints its
pre-registered PASS/FAIL (results/preregistration_v1.json).
EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, argparse, subprocess, time

SRC = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

RUNS = {
    # id: (description, production argv, dry-run argv)
    # Corrected run-list (attempt 2): fast incremental engine (qsci_fast) + determinant budgets sized
    # to the P2 scaling law. Priority: exact anchor (5), converged mid-scale PASS (3), 40q headline (1).
    5: ("cuStateVec exact validation, 20q vs FCI (the exactness anchor)",
        [PY, f"{SRC}/gpu_run1_h20_mps.py", "--atoms", "10", "--shots", "100000", "--topm", "128",
         "--grow-iters", "12", "--grow-per-iter", "4000", "--kcap", "60000"],
        [PY, f"{SRC}/gpu_run1_h20_mps.py", "--atoms", "4", "--shots", "10000"]),
    3: ("28q converged QSCI vs committed DMRG(chi=400) — genuine chemical-accuracy PASS above 20q",
        [PY, f"{SRC}/gpu_run1_h20_mps.py", "--atoms", "14", "--shots", "150000", "--topm", "256",
         "--grow-iters", "40", "--grow-per-iter", "8000", "--kcap", "400000"],
        [PY, f"{SRC}/gpu_run1_h20_mps.py", "--atoms", "6", "--shots", "20000",
         "--grow-iters", "20", "--grow-per-iter", "2000", "--kcap", "40000"]),
    1: ("40q H20 MPS QSCI (P1+P2+P3) — headline, honest at-scale attempt with the fast engine",
        [PY, f"{SRC}/gpu_run1_h20_mps.py", "--atoms", "20", "--shots", "200000",
         "--topm", "256", "--grow-iters", "40", "--grow-per-iter", "50000", "--kcap", "1500000"],
        [PY, f"{SRC}/gpu_run1_h20_mps.py", "--atoms", "6", "--shots", "20000"]),
    4: ("CrO CAS(19,19)=38q QSCI vs same-CAS DMRG (P4)",
        [PY, f"{SRC}/gpu_run4_cro38q.py", "--ncas", "19", "--grow-iters", "40",
         "--grow-per-iter", "40000", "--kcap", "800000"],
        [PY, f"{SRC}/gpu_run4_cro38q.py", "--ncas", "10", "--solve-casci",
         "--grow-iters", "15", "--kcap", "6000"]),
    6: ("Real QPU 12q H6 QSCI (P5) — set --target per qBraid device catalogue",
        [PY, f"{SRC}/qpu_run_h6.py", "--shots", "10000"],
        [PY, f"{SRC}/qpu_run_h6.py", "--target", "qpp-cpu", "--shots", "10000"]),
}
ORDER = [5, 3, 1, 4, 6]   # exact anchor -> converged 28q PASS -> 40q honest attempt -> 38q -> QPU

# Backend notes (set BEFORE launching):
#   run 1 at 40q:  CUDAQ_TARGET=tensornet-mps   (single H100/A100; chi target 400 per prereg P1)
#   run 5 <=32q:   CUDAQ_TARGET=nvidia          (cuStateVec exact)
#   run 6 QPU:     --target ionq|quantinuum|... (+ --machine), per qBraid's device names on the day


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int, nargs="*", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ids = a.only if a.only else ORDER
    print(f"Phase-3 driver: runs {ids} | {'DRY-RUN (CPU smoke)' if a.dry_run else 'PRODUCTION'} | "
          f"CUDAQ_TARGET={os.environ.get('CUDAQ_TARGET', '(default qpp-cpu)')}", flush=True)
    results = []
    for i in ids:
        desc, prod, dry = RUNS[i]
        argv = dry if a.dry_run else prod
        print(f"\n=== run {i}: {desc} ===\n$ {' '.join(argv[1:])}", flush=True)
        t0 = time.time()
        rc = subprocess.call(argv)
        results.append((i, rc, time.time() - t0))
    print("\n=== summary ===")
    for i, rc, dt in results:
        print(f"  run {i}: {'OK' if rc == 0 else f'EXIT {rc}'}  [{dt:.0f}s]")
    sys.exit(max((rc for _, rc, _ in results), default=0))


if __name__ == "__main__":
    main()
