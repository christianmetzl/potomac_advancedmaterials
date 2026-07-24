"""Bundle the third-party HamLib slice for OFFLINE re-verification (run once, on a machine with internet).

The sandbox that built this repo cannot reach the NERSC HamLib archive (network policy blocks it), so this
one-shot helper is run by the author on any machine that CAN download HamLib. It extracts *only* the three
Hydrogen-chain instances we validate against (H14/H16/H20, STO-6G, 28/32/40 qubits) from the downloaded
HamLib HDF5 into a small committed artifact under data/hamlib_slice/, so a judge can run the full third-party
cross-check with NO external download.

USAGE (on a machine with the HamLib download):
  1. Download the HamLib electronic-structure HDF5 for hydrogen chains from
       https://portal.nersc.gov/cfs/m888/dcamps/hamlib/     (Sawaya et al., Quantum 8, 1559, 2024)
  2. python src/hamlib_extract_slice.py --file <path-to-hamlib.hdf5>
  3. git add data/hamlib_slice && git commit -m "Bundle HamLib H14/16/20 slice for offline cross-check"

SAFETY — this can only ever emit a correct, GENUINE-HamLib slice: it locates each instance by matching the
operator's term count AND one-norm against the committed reference invariants (identical to
src/hamlib_validate.REF). If a file/instance does not match, it errors loudly and prints the file structure
rather than writing anything. It never regenerates the operator itself (that would make the check circular).

EIGENNEXUS - GIC 2026 Phase 3. Companion to hamlib_validate.py (offline third-party equivalence).
"""
import os, sys, json, gzip, hashlib, argparse

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_OUT = os.path.join(_ROOT, "data", "hamlib_slice")

# committed reference invariants — MUST match src/hamlib_validate.REF (the self-validation anchor)
REF = {14: (28, 27735, 151.39933003406185),
       16: (32, 47489, 202.27685442967848),
       20: (40, 116577, 328.47746113556263)}
HAMLIB_URL = "https://portal.nersc.gov/cfs/m888/dcamps/hamlib/"
CITATION = "Sawaya et al., HamLib: A library of Hamiltonians ..., Quantum 8, 1559 (2024)"


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _all_datasets(h5obj, prefix=""):
    """Recursively yield (key_path, dataset) for every dataset in the HDF5 file (schema-agnostic)."""
    import h5py
    for k in h5obj.keys():
        item = h5obj[k]
        path = f"{prefix}/{k}"
        if isinstance(item, h5py.Group):
            yield from _all_datasets(item, path)
        else:
            yield path, item


def _parse_op(dataset):
    """HamLib stores each operator as a UTF-8 string parseable by openfermion.QubitOperator."""
    from openfermion import QubitOperator
    raw = dataset[()]
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    elif hasattr(raw, "tobytes"):
        raw = raw.tobytes().decode("utf-8")
    elif not isinstance(raw, str):
        raw = str(raw)
    return QubitOperator(raw)


def _invariants(op):
    nt = len(op.terms)
    on = sum(abs(c) for c in op.terms.values())
    nq = 1 + max((q for term in op.terms for (q, _) in term), default=-1)
    return nq, nt, float(on)


def extract(h5path):
    import h5py  # imported here so --help works without h5py installed
    os.makedirs(_OUT, exist_ok=True)
    src_sha = _sha256(h5path)
    prov = {"source_url": HAMLIB_URL, "source_file": os.path.basename(h5path),
            "source_sha256": src_sha, "citation": CITATION,
            "note": "Genuine HamLib operators for H14/16/20 (STO-6G), extracted and self-validated against "
                    "committed invariants (term count + one-norm). Bundled so the third-party cross-check in "
                    "hamlib_validate.py runs fully offline.", "instances": {}}
    with h5py.File(h5path, "r") as f:
        datasets = list(_all_datasets(f))
        print(f"[extract] {len(datasets)} datasets in {os.path.basename(h5path)}", flush=True)
        for n, (nq_ref, nt_ref, on_ref) in sorted(REF.items()):
            match = None
            for keypath, ds in datasets:
                try:
                    op = _parse_op(ds)
                except Exception:
                    continue
                nq, nt, on = _invariants(op)
                if nt == nt_ref and abs(on - on_ref) < 1e-6:      # near-unique; schema-agnostic on key naming
                    match = (keypath, op, nq, nt, on)
                    break
            if match is None:
                print(f"[extract] ERROR: no operator in this file matches H{n} "
                      f"(expect terms={nt_ref}, one-norm={on_ref:.6f}).")
                print("[extract] datasets present (first 40):")
                for kp, _ in datasets[:40]:
                    print("   ", kp)
                raise SystemExit(f"H{n} not found — wrong HamLib file? Need the hydrogen-chain "
                                 f"electronic-structure Hamiltonians, STO-6G. See {HAMLIB_URL}")
            keypath, op, nq, nt, on = match
            outp = os.path.join(_OUT, f"H{n}_sto6g_jw.qubitop.gz")
            with gzip.open(outp, "wt", encoding="utf-8") as g:
                g.write(str(op))                                  # the genuine HamLib operator string
            prov["instances"][f"H{n}"] = {"key": keypath, "qubits": nq, "n_terms": nt,
                                          "one_norm": on, "artifact": os.path.relpath(outp, _ROOT)}
            print(f"[extract] H{n}: matched key '{keypath}' -> {os.path.relpath(outp, _ROOT)} "
                  f"(nq={nq}, terms={nt}, one-norm={on:.10f})  [SELF-VALIDATED vs committed REF]")
    json.dump(prov, open(os.path.join(_OUT, "provenance.json"), "w"), indent=2)
    print(f"[extract] wrote {os.path.relpath(os.path.join(_OUT, 'provenance.json'), _ROOT)}")
    print("[extract] DONE. `git add data/hamlib_slice && git commit` — hamlib_validate.py will then run the "
          "FULL offline third-party check automatically.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Extract H14/16/20 HamLib slice for offline cross-check.")
    ap.add_argument("--file", required=True, help="path to the downloaded HamLib electronic-structure HDF5")
    a = ap.parse_args()
    if not os.path.exists(a.file):
        raise SystemExit(f"file not found: {a.file}\nDownload the HamLib HDF5 from {HAMLIB_URL} ({CITATION}).")
    extract(a.file)
