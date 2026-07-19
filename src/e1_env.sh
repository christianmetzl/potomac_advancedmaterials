# E1 runtime environment (source before any block2 run on this qBraid CPU box).
#
# MKL WORKAROUND (documented for provenance):
# block2 0.5.3's bundled MKL subset in site-packages/block2.libs/ is missing the
# runtime CPU-dispatch kernel libmkl_def.so.1 (and avx/mc), and its bundled
# hashed core/gnu_thread/intel_lp64 are a reduced build whose def-resolved
# threaded-sparse symbols (e.g. mkl_sparse_optimize_bsr_trsm_i8) are absent.
# The full, self-consistent MKL 2021.4.0 that is block2's own runtime dependency
# is installed at ~/.local/lib (verified: `mkl_get_version_string` -> 2021.4).
# Fix applied once (see git log / e1 notes):
#   - copied libmkl_def/avx/mc/mc3/avx512_mic.so.1 into block2.libs
#   - replaced block2.libs hashed core/gnu_thread/intel_lp64 + avx2/avx512 with
#     the self-consistent ~/.local/lib 2021.4.0 builds (same DT_NEEDED names)
# Plus, at runtime, LD_PRELOAD the single dynamic interface libmkl_rt so all MKL
# symbols are globally resolved before block2 dlopens the dispatch kernel.
# This changes NOTHING numerically: it only lets the (already classical, CPU)
# block2 DMRG load its BLAS. Correctness is confirmed by reproducing the
# committed chi=400 reference energy through this exact path before chi=800.
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
export OPENBLAS_NUM_THREADS=8
export MKL_THREADING_LAYER=GNU
export LD_LIBRARY_PATH="/home/jovyan/.local/lib:${LD_LIBRARY_PATH}"
export LD_PRELOAD="/home/jovyan/.local/lib/libmkl_rt.so.1"
