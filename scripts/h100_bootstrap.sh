#!/usr/bin/env bash
# One-command setup for a paid qBraid GPU instance (H100/A100). Every minute here is billed —
# this script front-loads everything so the physics starts within ~2-3 minutes of boot.
#   bash scripts/h100_bootstrap.sh          # setup + dry-run smoke, prints the run menu
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== $(date -u +%H:%M:%S) deps =="
pip install --user -q -r requirements.txt 2>&1 | tail -1 || pip install -q -r requirements.txt 2>&1 | tail -1

echo "== $(date -u +%H:%M:%S) environment =="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "(no GPU visible)"
free -g | head -2
python3 -c "import cudaq, qsci_lib" 2>/dev/null && echo "imports OK" || python3 - <<'EOF'
import sys; sys.path.insert(0, 'src'); import cudaq, qsci_lib; print("imports OK")
EOF
export OMP_NUM_THREADS=$(nproc)   # the growth eigensolver is BLAS-bound; use all cores

echo "== $(date -u +%H:%M:%S) smoke (CPU, ~1 min) =="
python3 src/gpu_run1_h20_mps.py --atoms 4 --shots 5000 2>&1 | tail -2

cat <<'MENU'
== READY. Production menu (run + push after each; STOP THE INSTANCE when done) ==
# B1  40q flagship (big batch, exact resume enabled — rerun same command after any crash):
GROW_PER_ITER=150000 KCAP=550000 GROW_ITERS=12 python3 src/gpu_run1_h20_mp2seed.py

# B2  38q CrO oxide:
python3 src/gpu_run4_cro38q.py --ncas 19 --grow-iters 40 --grow-per-iter 40000 --kcap 800000

# B3  40q genuine tensornet-mps GPU sampling + wall-clock:
CUDAQ_TARGET=tensornet-mps python3 src/gpu_run1_h20_mps.py --atoms 20 --shots 20000 --topm 256 \
  --grow-iters 6 --grow-per-iter 30000 --kcap 200000

# After each:  git add results/ && git commit -m "<verbatim PASS/FAIL line>" && git push
MENU
