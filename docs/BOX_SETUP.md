# Box setup — E-campaign instances (paste-ready)

Three boxes: **A** = CPU 64 vCPU/256 GB (E3 → E5), **B** = CPU 32 vCPU/128 GB (E4 → E2),
**S** = Subscription Large 8 vCPU/25 GB, free (canonical `reproduce.py` transcript).
Branch everywhere: `claude/wonderful-bohr-rir81t`.

## 1. Common setup (every box, ~5–10 min)

```bash
# --- clone (use a GitHub fine-grained PAT with read/write on this repo) ---
cd ~
git clone -b claude/wonderful-bohr-rir81t \
  https://<YOUR_PAT>@github.com/christianmetzl/potomac_advancedmaterials.git
cd potomac_advancedmaterials
git config user.name  "Christian Metzl"
git config user.email "Christianmetzl@aol.com"

# --- python deps (CPU wheels; cudaq + block2 are in requirements.txt) ---
pip install -r requirements.txt

# --- sanity gates: ALL must pass before spending a single credit-minute on production ---
python - <<'EOF'
import qsci_lib, numpy, pyscf, openfermion
print("qsci_lib import OK (cudaq CPU wheel working)")
EOF
python src/e3_certificate_40q.py --smoke 6        # must end: FORMULA VALIDATED
python src/verify_credits.py --live --append      # wallet snapshot INTO the ledger; commit it
git add results/credit_ledger.json && git commit -m "wallet snapshot at instance start" && git push

# --- threads (per box: A=64, B=32, S=8) ---
export OMP_NUM_THREADS=<N> MKL_NUM_THREADS=<N> OPENBLAS_NUM_THREADS=<N>

# --- disk check (E5 state may reach 150-250 GB; E3 ~100 GB) ---
df -h ~ .
```

## 2. Claude Code install (every box)

```bash
curl -fsSL https://claude.ai/install.sh | bash
export PATH="$HOME/.local/bin:$PATH"      # add to ~/.bashrc too
cd ~/potomac_advancedmaterials && claude  # first run prints a login URL -> open it, authenticate
```

Run Claude inside `tmux` so the session survives browser disconnects:
```bash
tmux new -s campaign   # reattach later: tmux attach -t campaign
```

## 3. Startup prompts (paste into Claude on each box)

### Box A (64 vCPU / 256 GB) — E3, then E5

> You are the run operator on qBraid box A (64 vCPU/256 GB) for the EIGENNEXUS E-campaign.
> Read docs/E_CAMPAIGN_RUNBOOK.md and results/preregistration_v2.json first. Your jobs, in order:
> 1) Launch E3 exactly as frozen: `nohup env OMP_NUM_THREADS=64 MKL_NUM_THREADS=64 python src/e3_certificate_40q.py > e3.log 2>&1 &` — never change GROW_PER_ITER/KCAP/thresholds. (This box has only ~20 GB free disk; E3 v2 runs state-file-free by design — do NOT set STATE_FILE.)
> 2) Babysit it: every ~30 min check e3.log, RAM (`free -g`), disk (`df -h`), and commit+push `results/e3_certificate_evidence.json` + the log at every completed iteration. If the process dies, relaunch the identical command — it restarts from the seed (no state file on this disk; the committed per-iteration certificate points are the durable record).
> 3) When E3 finishes: commit+push everything, then `python src/verify_credits.py --live --append`, commit the ledger.
> 4) Before E5: `git pull`, confirm `results/h22_44q_dmrg_chi1200.json` exists. If it is missing or marked DNF, build the judge FIRST and commit it BEFORE any growth: `python src/dmrg_ladder_ext.py --rung 22 1200 /tmp/r1200.json` then `python -c "import json,sys; sys.path.insert(0,'src'); import dmrg_ladder_ext as lx; lx._write_reference(22,1200,json.load(open('/tmp/r1200.json')),role='E5 JUDGE reference (re-frozen chi=1200)')"` — if block2 fails to load MKL on this image, consult src/e1_env.sh for the documented fix.
> 5) Launch E5: `nohup env OMP_NUM_THREADS=64 MKL_NUM_THREADS=64 STATE_FILE= python src/e5_h22_44q.py > e5.log 2>&1 &` (STATE_FILE empty = checkpointing off: this box's ~20 GB disk cannot hold the state file — disclosed deviation, see runbook; the PARTIAL trace + evidence flushes are the durable record). Same babysit/commit discipline; on death, relaunch restarts from seed.
> 6) HARD ABORT GATE (frozen): if E5 has not converged by 2026-07-25 06:00 UTC, stop it, commit all logs/state trace, and report it as non-converged per its frozen reporting rule. Do not extend.
> 7) Before ANY instance shutdown: push all evidence, take a final `verify_credits.py --live --append` snapshot, commit, push. Evidence must never die with the box.
> Rules: protocols are FROZEN — no parameter tuning, no threshold moves, report outcomes as-is (FAIL is a result). Never edit results/preregistration_v2.json. If anything ambiguous comes up, stop and ask me rather than improvising.

### Box B (32 vCPU / 128 GB) — E4, then E2

> You are the run operator on qBraid box B (32 vCPU/128 GB) for the EIGENNEXUS E-campaign.
> Read docs/E_CAMPAIGN_RUNBOOK.md and results/preregistration_v2.json first. Your jobs, in order:
> 1) Launch E4 exactly as frozen: `nohup env OMP_NUM_THREADS=32 MKL_NUM_THREADS=32 STATE_FILE= python src/e4_sn2o2_38q.py > e4.log 2>&1 &` (STATE_FILE empty = checkpointing off: ~20 GB disk, state would need ~29 GB — disclosed deviation, see runbook).
> 2) Babysit: every ~30 min check e4.log, RAM, disk; commit+push `results/e4_sn2o2_38q_evidence.json` (and the PARTIAL checkpoint) at every completed iteration. On process death, relaunch identically — it restarts from the HF seed; the committed PARTIAL trace is the durable record.
> 3) When E4 finishes: commit+push, `python src/verify_credits.py --live --append`, commit the ledger.
> 4) Launch E2: `nohup env OMP_NUM_THREADS=32 MKL_NUM_THREADS=32 STATE_FILE= python src/e2_device_seed_40q.py > e2.log 2>&1 &` (STATE_FILE empty — same disk deviation as E4). Same discipline. E2 consumes the committed seed file verbatim — if `results/p3_sample_dets.json` is missing or fails the runner's assertion, STOP and report; do not substitute a seed.
> 5) Before ANY shutdown: push all evidence + final wallet snapshot.
> Rules: FROZEN protocols — no tuning, no threshold moves, outcomes as-is; a metric FAIL with the below-reference ordering is a valid documented outcome (see the CrO/B2 precedent). Never edit results/preregistration_v2.json. Ask before improvising.

### Box C (64 vCPU / 256 GB, second big box) — E5 judge build + E5 (added 2026-07-21, decouples E5 from E3)

> You are the run operator on qBraid box C (64 vCPU/256 GB) for the EIGENNEXUS E-campaign. E5 is REASSIGNED to this box (box A keeps E3 only; its old Jobs 4–5 are cancelled). Read docs/E_CAMPAIGN_RUNBOOK.md and results/preregistration_v2.json (E5 entry incl. refrozen_2026-07-20) first. Your jobs, in order:
> 1) git pull. Confirm results/h22_44q_dmrg_chi400.json and _chi800.json exist (committed ladder rungs). The JUDGE results/h22_44q_dmrg_chi1200.json is expected MISSING — build it FIRST, before any growth: `python src/dmrg_ladder_ext.py --rung 22 1200 /tmp/r1200.json` then `python -c "import json,sys; sys.path.insert(0,'src'); import dmrg_ladder_ext as lx; lx._write_reference(22,1200,json.load(open('/tmp/r1200.json')),role='E5 JUDGE reference (re-frozen chi=1200)')"` — then COMMIT AND PUSH the judge before proceeding (commit must precede execution). If block2 fails to load MKL on this image, consult src/e1_env.sh for the documented fix. Expect ~1–2 h on 64 threads.
> 2) Launch E5 exactly as frozen: `nohup env OMP_NUM_THREADS=64 MKL_NUM_THREADS=64 STATE_FILE= python src/e5_h22_44q.py > e5.log 2>&1 &` (STATE_FILE empty = checkpointing off on ~20 GB-disk boxes — disclosed deviation, see runbook). The runner refuses to start if the judge file is missing — that refusal means step 1 wasn't completed; never work around it.
> 3) Babysit: every ~30 min check e5.log, RAM (`free -g` — kcap 3M at 44q may push toward this box's limit; an out-of-memory stop is a RESOURCE outcome, reported as-is with the trace, never retried with altered parameters), disk, and commit+push the PARTIAL/evidence per iteration. Also start the unattended backstop loop with label "box C E5 auto-checkpoint" and the pull-rebase-autostash pattern (see box A/B precedent). On process death, relaunch identically — restarts from seed.
> 4) HARD ABORT GATE (frozen): if E5 has not converged by 2026-07-25 06:00 UTC, stop it, commit all logs and the trace, and report non-converged per its frozen reporting rule. Do not extend.
> 5) Before ANY shutdown: push all evidence, `python src/verify_credits.py --live --append`, commit the ledger, and append this instance's settled cost from qBraid console billing to credit_ledger.json attributed_spend_cr.e_campaign_instances (run: "E5").
> Rules: FROZEN protocols — no tuning, no threshold moves, outcomes as-is. Never edit results/preregistration_v2.json. Ask before improvising.

### Box S (Subscription Large, free) — canonical reproduce transcript

> You are on the free subscription box (8 vCPU/25 GB) to produce the canonical full-dependency reproduce transcript for EIGENNEXUS.
> 1) `export OMP_NUM_THREADS=8`, then run `python src/reproduce.py` end-to-end and capture the full stdout to `docs/reproduce_transcript.txt` (replace the committed one).
> 2) Goal: the skip-minimal transcript — cudaq/block2/torch are installed here, so optional checks should EXECUTE rather than skip. If any check fails, do NOT edit checks or thresholds: commit the failing transcript as-is and report it.
> 3) Commit+push the transcript. This box is free (100 subscription CPU-hrs) — no credit ledger entry needed, but note the run in the commit message.

## 4. Handover/shutdown checklist (A and B)
- [ ] evidence JSONs + logs committed and pushed
- [ ] `verify_credits.py --live --append` snapshot committed (start, each handover, shutdown)
- [ ] state files deleted or left per disk budget (they do NOT get committed — 100+ GB)
- [ ] instance STOPPED in the qBraid console (uptime is billing)
