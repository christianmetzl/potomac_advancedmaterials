"""ONE COMMAND: discover + download the HamLib hydrogen-chain file(s) and bundle the H14/16/20 slice.

The "just do it" wrapper around hamlib_extract_slice.py. Run on a machine WITH internet (the build sandbox
is network-blocked from NERSC). It crawls the public HamLib archive, downloads the electronic-structure
HDF5(s), extracts the three instances we validate against, writes data/hamlib_slice/, and (with --commit)
commits + pushes. Self-validating: it only ever writes genuine HamLib data (matched against committed
term-count + one-norm), so it cannot produce a wrong slice.

    python src/download_and_bundle_hamlib.py            # download + extract
    python src/download_and_bundle_hamlib.py --commit   # ... then git add/commit/push

Only stdlib + h5py/openfermion (the extractor's deps). No API keys. NOTE: the author could not test the live
crawl (this sandbox blocks NERSC), so if HamLib's directory layout differs the script prints exactly what it
found — paste that back and it takes ~2 min to adjust. It won't download a file larger than --max-mb without
--yes. If your own network also blocks NERSC, download manually in a browser and use:
    python src/hamlib_extract_slice.py --dir <folder-of-downloaded-hdf5>
"""
import os, sys, re, argparse, tempfile, subprocess, urllib.request, urllib.parse

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from hamlib_extract_slice import extract, REF, HAMLIB_URL  # reuse the validated, self-checking extractor

ES_HINTS = ("electronicstructure", "electronic_structure", "chemistry", "chem")
HCHAIN_HINTS = ("hydrogen", "hchain", "h_chain", "h-chain", "chain", "_hn", "/h")


def _listing(url):
    try:
        html = urllib.request.urlopen(url, timeout=90).read().decode("utf-8", "ignore")
    except Exception as e:
        print(f"  [crawl] cannot read {url}: {e}")
        return []
    out = []
    for h in re.findall(r'href="([^"?#]+)"', html):
        if h.startswith(("?", "http")) or h in ("../", "/"):
            continue
        out.append(urllib.parse.urljoin(url, h))
    return out


def crawl(base, depth=3):
    """Recursively collect .h5/.hdf5 URLs; rank hydrogen-chain / electronic-structure names first."""
    seen, files = set(), []

    def walk(url, d):
        if d < 0 or url in seen:
            return
        seen.add(url)
        for link in _listing(url):
            low = link.lower()
            if low.endswith((".h5", ".hdf5")):
                files.append(link)
            elif link.endswith("/"):
                walk(link, d - 1)

    walk(base if base.endswith("/") else base + "/", depth)

    def score(u):
        lu = u.lower()
        return (0 if any(h in lu for h in HCHAIN_HINTS) else 1,
                0 if any(h in lu for h in ES_HINTS) else 1, len(u))
    return sorted(set(files), key=score)


def _size_mb(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        n = urllib.request.urlopen(req, timeout=60).headers.get("Content-Length")
        return (int(n) / 1e6) if n else None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description="Auto-download HamLib + bundle the H14/16/20 offline slice.")
    ap.add_argument("--commit", action="store_true", help="git add/commit/push the slice after extraction")
    ap.add_argument("--max-mb", type=float, default=1500.0, help="skip files larger than this unless --yes")
    ap.add_argument("--yes", action="store_true", help="download candidates regardless of size")
    ap.add_argument("--base", default=HAMLIB_URL, help="HamLib archive base URL")
    a = ap.parse_args()

    print(f"[auto] crawling {a.base} for electronic-structure HDF5 files ...", flush=True)
    cands = crawl(a.base)
    if not cands:
        raise SystemExit(f"[auto] no .h5/.hdf5 found under {a.base}. Open it in a browser to confirm it's "
                         f"reachable from THIS machine; if your network also blocks NERSC, download manually "
                         f"and run: python src/hamlib_extract_slice.py --dir <folder>")
    print(f"[auto] {len(cands)} candidate file(s); most-likely hydrogen-chain files first:")
    for u in cands[:10]:
        print("   ", u)

    tmp = tempfile.mkdtemp(prefix="hamlib_")
    got, need = [], set(REF)
    for url in cands:
        if not need:
            break
        mb = _size_mb(url)
        if mb and mb > a.max_mb and not a.yes:
            print(f"  [skip] {os.path.basename(url)} ~{mb:.0f} MB > --max-mb {a.max_mb} (use --yes to force)")
            continue
        dest = os.path.join(tmp, os.path.basename(url))
        print(f"  [dl] {url}{f'  (~{mb:.0f} MB)' if mb else ''} ...", flush=True)
        try:
            urllib.request.urlretrieve(url, dest)
        except Exception as e:
            print(f"  [dl-fail] {e}")
            continue
        got.append(dest)
        try:
            extract(got)          # writes data/hamlib_slice/*, self-validated; returns only if ALL 3 found
            need = set()
            break
        except SystemExit:
            continue              # not all instances present yet — keep downloading candidates
    if need:
        raise SystemExit(f"[auto] downloaded {len(got)} file(s) but couldn't find all of "
                         f"{sorted('H%d' % n for n in REF)}. Paste this output back to adjust the crawl/parser.")
    print("[auto] slice written to data/hamlib_slice/  (self-validated genuine HamLib data).")
    if a.commit:
        subprocess.run(["git", "add", "data/hamlib_slice"], check=True)
        subprocess.run(["git", "commit", "-m", "Bundle HamLib H14/16/20 slice for offline cross-check"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("[auto] committed + pushed.")
    else:
        print("[auto] to commit: git add data/hamlib_slice && git commit -m '...' && git push  (or re-run --commit)")


if __name__ == "__main__":
    main()
