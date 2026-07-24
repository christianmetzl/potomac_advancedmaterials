# Outlook & research roadmap — frozen protocols, not promises

**Reading rule:** every item below that is executable exists as a *frozen pre-registered protocol* in
`results/preregistration_v2.json` (git-timestamped before any execution). Items never executed before
the submission deadline stand unmodified as the research outlook — a reviewer can cost them, audit
their thresholds, and later check whether we ran them as written. This is the same discipline that
governed the completed campaign (preregistration_v1: P1 ✅ P2 ✅ H1 ✅ blind, P4 reported against its
frozen metric, P5 chain validated), applied forward.

## Near term (protocols frozen; execution gated only on compute)

1. **Standing χ-escalation QA (E1 — executing now, personally funded).** Every DMRG reference used to
   judge an audit gets its own audit: recompute at higher χ, report which variational bound is
   tighter. E1 covers the two campaign references (CrO CAS(18,19), H₂₀/40q) at χ=800; the practice
   generalizes to every future reference. The audit layer auditing its own referees is the natural
   fixed point of the method.
2. **Closing the sampling loop at scale (E2).** Device-sampled determinant selection is proven at
   20q/28q; the flagship ran MP2-seeded for documented cost reasons. E2 freezes the equivalence test
   at 40q (device seed vs MP2 seed, matched budgets, ≤0.5 mHa). Pass retires the paper's own
   "quantum-inspired at scale" limitation; fail is a finding. Cost drops to growth-only if the P3
   measurement run commits its sample.
3. **Certificate-complete flagship (E3).** Growth to EN-PT2 certificate convergence (|ΔE_PT2| ≤ 0.5
   mHa) at 40q with the certificate reported every iteration — the "pay compute → becomes truth"
   mechanism demonstrated end-to-end at the headline scale, judged against both the χ=400 and E1's
   χ=800 references.
4. **EUV chemistry at industrial scale (E4).** The bridged Sn–O–Sn motif audited at CAS(18,19)=38q.
   STEP 1 (the same-CAS DMRG reference, committed before any run it will judge) is authorized
   personally-funded pre-work executable on subscription CPU today; STEP 2 mirrors the CrO/P4
   configuration on the materials class the challenge's industrial partners care most about.

## Medium term (framed; would be frozen before any execution)

5. **Reaction-path audits at scale.** The conditional tier (energy differences trusted after each
   endpoint converges) is demonstrated at 20q (CrO dissociation, spin gaps). The industrial decision
   quantity is the barrier height: a 38q bond-stretch audit of CrO (multiple geometries, each
   endpoint individually certified) moves the audit from single points to reaction paths — where
   CCSD(T)'s committed failure (erratic to ~144 mHa, non-convergent) actually bites in catalysis.
6. **Broader oxide trend lines.** NiO at CAS(18,19); FeO/MnO to span the 3d row; ligated tin-oxo
   fragments (methyltin) stepping toward the real resist cage. Same pipeline, same evidence pattern.
7. **44q and beyond (E5, frozen conditionally).** Past the challenge goalpost with the determinant
   budget predicted in advance by the committed scaling law (1.383×/qubit). Gated on E1's verdict
   (reference tightness), funding, and an explicit governance decision — rule 3 of the budget doc
   forbids exploratory >40q spend on the grant share without sign-off.

## Method extensions (research directions; not yet protocolized)

- **Excited states / spectra:** state-averaged selected CI with per-root variational bounds and PT2
  certificates — spin gaps today, optical gaps and photochemistry (EUV exposure pathways) next.
- **Spin adaptation:** CSF-based selection to shrink open-shell determinant budgets and remove
  M_s-resolution as a stated limitation.
- **Forces & geometry:** analytic gradients over the certified subspace → audited geometries, not
  just audited single points.
- **Embedding toward real materials:** DMET/periodic embedding with the certified solver as the
  fragment engine — the path from cluster fragments to the actual lattice.
- **Upstream-assumption quantification:** x2c scalar-relativistic single-points and AVAS-based
  active-space checks as routine companions (first instances executable now on CPU), migrating
  items from "stated assumption" to "measured shift".

## Hardware curve

The expensive step — selecting which determinants matter — is the step a quantum sampler does
natively. Today: CUDA-Q simulators (validated), AQT trapped-ion jobs in flight (P5, personally
funded). As registers grow past ~40 physical qubits with usable fidelities, device sampling replaces
the classical selection heuristics *inside an unchanged certification framework*: the variational
bound and PT2 certificate are sampler-agnostic. That is the strategic bet of the architecture — the
guarantees live in the classical diagonalization layer, so every hardware improvement lowers the cost
of certified truth without ever being trusted blindly.

*EIGENNEXUS — GIC 2026 Phase 3. Companion artifacts: results/preregistration_v2.json (frozen
protocols E1–E5), docs/claims_ledger.md (what is claimed vs executed).*
