"""Assemble the GIC Phase 3 submission zip: EIGENNEXUS_AdvancedMaterials_Phase3.zip.

Per the GIC Phase 3 spec, the zip contains: the write-up PDF (<=5 pages, excl. cover/refs), a source-code
folder (all code to reproduce, runnable on qBraid), and a README.md (with 'Launch on qBraid'). We also
include the evidence JSONs, the claims ledger, and the reproduce.py transcript for full traceability.

NOTE: the official GIC cover page (team template) must be PREPENDED to the write-up PDF as page 1 before
final upload — see SUBMISSION_NOTES.md in the zip. Run: python paper/make_submission_zip.py
"""
import os, shutil, zipfile, fnmatch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGE = os.path.join(REPO, "EIGENNEXUS_AdvancedMaterials_Phase3")
ZIP = os.path.join(REPO, "EIGENNEXUS_AdvancedMaterials_Phase3.zip")
EXCLUDE_DIRS = {"__pycache__", ".mol_cache", "node_modules", ".git", ".ipynb_checkpoints"}
EXCLUDE_GLOB = ["*.pyc", "_img*.png", "_phase3_writeup.html", "*.log"]

NOTES = """# EIGENNEXUS — GIC 2026 Phase 3 submission (Advanced Materials, Mitsubishi/AIST)

## Contents
- `EIGENNEXUS_Phase3_Writeup.pdf` — the write-up (sections 1-8 = 5 pages; references on the last page,
  excluded from the page limit). 11-pt Times New Roman, single-spaced.
- `README.md` — team, project, track; setup; step-by-step run on qBraid; expected I/O; limitations;
  'Launch on qBraid' button.
- `src/` — all source code (CPU-verified + the qBraid GPU run-list scripts).
- `results/` — every committed evidence JSON + figures (each headline number traces here).
- `docs/claims_ledger.md` — per-claim traceability (number -> script -> evidence -> status).
- `docs/reproduce_transcript.txt` — captured `python src/reproduce.py` -> 13/13 PASS (11 core + 2 optional CUDA-Q/MPS).
- `requirements.txt` (CPU) / `requirements-gpu.txt` (cudaq/quimb/block2 for qBraid GPU).

## TWO ACTIONS REQUIRED BEFORE UPLOAD (team)
1. **Prepend the official GIC_2026 cover page** (the provided .docx template, unmodified) as page 1 of the
   final write-up PDF. The cover page is required and is excluded from the 5-page limit. Do NOT recreate or
   modify the template. Final write-up PDF = [cover page] + EIGENNEXUS_Phase3_Writeup.pdf.
2. **Record the device selection on the Phase 3 cover page** = qBraid GPU (CUDA-Q) + IonQ/IBM QPU. It was
   omitted from the Phase 2 cover page; access is gated on this, and it has been raised with the organizers
   (see docs/qbraid_access_email.md). It MUST appear on the Phase 3 cover page.

## Reproducing (judges)
`pip install -r requirements.txt` then `python src/reproduce.py` -> 13/13 PASS on CPU (11 core + 2 optional CUDA-Q/MPS).
GPU/at-scale items (40q MPS, near-38q CrO/NiO, QPU validation) are marked [QBRAID-RUN] in the write-up and
are the qBraid GPU deliverable; everything else is executed and reproducible on CPU.

## Honest status
Executed (CPU/circuit-sampled): two-stage GQE, integrated GQE->QSCI (measured to 20q), CrO/NiO & Sn-oxides
at 20q, the CrO spin-state decision (DFT spans 1.9 eV / B3LYP wrong sign vs CASCI/QSCI +1.89 eV = experimental
X5Pi), the real-oxide CrO dissociation trust curve (CCSD(T) breaks down vs variational QSCI), the EN-PT2
two-sided bracket, generator-MP2 interpretability, HamLib equivalence, noise robustness, DFT functional-spread,
classical baselines, strong-correlation selected-CI, operator-pool compression, scaling law. Proxy (validated vs measurement at 16/20q): the
16->56q transfer ladder, cross-chemistry, budget sweep. Owed (qBraid GPU): the 40q MPS run and QPU
validation. No result is overstated; see docs/claims_ledger.md.
"""


def included(path):
    parts = set(path.split(os.sep))
    if parts & EXCLUDE_DIRS:
        return False
    base = os.path.basename(path)
    return not any(fnmatch.fnmatch(base, g) for g in EXCLUDE_GLOB)


def copytree(src, dst):
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            sp = os.path.join(root, f)
            if not included(sp):
                continue
            rp = os.path.relpath(sp, REPO)
            dp = os.path.join(dst, rp)
            os.makedirs(os.path.dirname(dp), exist_ok=True)
            shutil.copy2(sp, dp)


def main():
    if os.path.exists(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)
    # write-up PDF
    shutil.copy2(os.path.join(REPO, "paper", "EIGENNEXUS_Phase3_Writeup.pdf"),
                 os.path.join(STAGE, "EIGENNEXUS_Phase3_Writeup.pdf"))
    # top-level files
    for f in ("README.md", "requirements.txt", "requirements-gpu.txt"):
        shutil.copy2(os.path.join(REPO, f), os.path.join(STAGE, f))
    # code + evidence + key docs
    copytree(os.path.join(REPO, "src"), STAGE)
    copytree(os.path.join(REPO, "results"), STAGE)
    for d in ("claims_ledger.md", "reproduce_transcript.txt"):
        s = os.path.join(REPO, "docs", d)
        if os.path.exists(s):
            os.makedirs(os.path.join(STAGE, "docs"), exist_ok=True)
            shutil.copy2(s, os.path.join(STAGE, "docs", d))
    open(os.path.join(STAGE, "SUBMISSION_NOTES.md"), "w").write(NOTES)
    # zip
    if os.path.exists(ZIP):
        os.remove(ZIP)
    nfiles = 0
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(STAGE):
            for f in files:
                sp = os.path.join(root, f)
                z.write(sp, os.path.relpath(sp, REPO))
                nfiles += 1
    print(f"built {os.path.basename(ZIP)}: {nfiles} files, {os.path.getsize(ZIP)//1024} KB")


if __name__ == "__main__":
    main()
