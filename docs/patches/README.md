# Held patches

`qsci_lib_hardening.patch` — two fixes surfaced by the B1 disk incident: (1) close the np.load
handle in the qsci_fast resume path (an open NpzFile pins the replaced state file's blocks on disk);
(2) wrap _save_state in try/except so a failed checkpoint write (e.g. ENOSPC) degrades to a warning
instead of killing the run before its terminal evidence.

**Deliberately NOT applied while any campaign run is live** (B2 executes this module). Apply after
B2's terminal evidence: `git apply docs/patches/qsci_lib_hardening.patch`, then rerun the engine
equivalence check before committing.
