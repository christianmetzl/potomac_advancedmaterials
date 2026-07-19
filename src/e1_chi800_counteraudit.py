"""E1 chi-escalation counter-audit (prereg_v2 E1). block2 DMRG at raised chi.

WORKAROUND CONTEXT: src/qsci_lib.py imports `cudaq` at module top, which is
absent on this personally-funded CPU qBraid box (CUDA-Q intentionally NOT
installed). make_ref / the DMRG reference never needs the qubit-operator
(Jordan-Wigner) part of cas_problem / hchain_problem, so this script replicates
their integral construction directly with pyscf -- the IDENTICAL classical code
path (same ROHF/RHF, same mc.get_h1eff()/get_h2eff(), same ao2mo.restore(1,...))
that qsci_lib uses -- and hands those integrals to block2. Validated by
reproducing the committed chi=400 reference energy through this path before the
chi=800 run.

Systems:
  cro : CrO 5-Pi CAS(18,19)=38q  -- mirrors qsci_lib.cas_problem + gpu_run4 make_ref
  h20 : linear H20 STO-6G R=0.74 40q -- mirrors qsci_lib.hchain_problem(20)

DMRG schedule is the frozen make_ref schedule with the chi plateau raised:
  n_sweeps=8, bond_dims=[100,150,200,chi,chi,chi,chi,chi],
  noises=[1e-4,1e-5,1e-6,1e-7,0,0,0,0], thrds=[1e-8]*8   (SU(2)).
EIGENNEXUS - GIC 2026 Phase 3, extension E1.
"""
import os, sys, json, time, argparse, platform, resource
import numpy as np

_RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

# ---- CrO problem: verbatim replica of qsci_lib.cas_problem's integral path ----
ATOM = "Cr 0 0 0; O 0 0 1.621"          # matches gpu_run4_cro38q.ATOM
SPIN = 4
BASIS = "def2-svp"


def _nelecas_for(ncas):                 # verbatim from gpu_run4_cro38q.nelecas_for
    nel = ncas if ncas % 2 == 0 else ncas - 1
    na = (nel + SPIN) // 2
    return (na, nel - na)


def cro_integrals(ncas=19):
    """Replica of qsci_lib.cas_problem(ATOM,'def2-svp',SPIN,ncas,nelecas) integral half."""
    from pyscf import gto, scf, ao2mo, mcscf
    nelecas = _nelecas_for(ncas)
    mol = gto.M(atom=ATOM, basis=BASIS, ecp={}, spin=SPIN, charge=0, verbose=0)
    mf = scf.ROHF(mol)
    mf.max_cycle = 300; mf.conv_tol = 1e-9; mf.kernel()
    if not mf.converged:
        mf.level_shift = 0.0; mf.init_guess = "atom"; mf.kernel()
    mc = mcscf.CASCI(mf, ncas, nelecas); mc.verbose = 0
    h1e, ecore = mc.get_h1eff(); eri = ao2mo.restore(1, mc.get_h2eff(), ncas)
    na, nb = nelecas
    return dict(h1=h1e, eri=eri, ecore=float(ecore), na=na, nb=nb, n_sites=ncas,
                rohf_converged=bool(mf.converged),
                active_space=f"CAS({na+nb},{ncas})", qubits=2 * ncas, system="CrO 5-Pi")


def h20_integrals(n_atoms=20, R=0.74):
    """Replica of qsci_lib.hchain_problem(20) integral half (RHF STO-6G, R=0.74)."""
    from pyscf import gto, scf, ao2mo
    mol = gto.M(atom="; ".join(f"H 0 0 {i*R:.4f}" for i in range(n_atoms)),
                basis="sto-6g", verbose=0)
    mf = scf.RHF(mol).run(conv_tol=1e-10)
    norb = mf.mo_coeff.shape[1]; ne = mol.nelectron
    h1 = mf.mo_coeff.T @ mf.get_hcore() @ mf.mo_coeff
    eri = ao2mo.restore(1, ao2mo.kernel(mol, mf.mo_coeff), norb)
    ecore = float(mol.energy_nuc())
    na = nb = ne // 2
    return dict(h1=h1, eri=eri, ecore=ecore, na=na, nb=nb, n_sites=norb,
                rhf_converged=bool(mf.converged), e_hf=float(mf.e_tot),
                active_space=f"H{n_atoms} STO-6G R={R}", qubits=2 * norb, system="H20 chain")


def run_dmrg(P, chi, tag, n_threads=8):
    """Frozen make_ref schedule with chi plateau raised. Scratch in ~/dmrg_scratch/<tag>."""
    from pyblock2.driver.core import DMRGDriver, SymmetryTypes
    scratch = os.path.join(os.path.expanduser("~"), "dmrg_scratch", tag)
    os.makedirs(scratch, exist_ok=True)
    na, nb = P["na"], P["nb"]; ns = P["n_sites"]
    bond_dims = [100, 150, 200, chi, chi, chi, chi, chi]
    noises = [1e-4, 1e-5, 1e-6, 1e-7, 0, 0, 0, 0]
    thrds = [1e-8] * 8
    driver = DMRGDriver(scratch=scratch, symm_type=SymmetryTypes.SU2, n_threads=n_threads)
    driver.initialize_system(n_sites=ns, n_elec=na + nb, spin=na - nb, orb_sym=None)
    mpo = driver.get_qc_mpo(h1e=P["h1"], g2e=P["eri"], ecore=P["ecore"], iprint=1)
    ket = driver.get_random_mps(tag=tag.upper(), bond_dim=min(chi, 100), nroots=1)
    print(f"[e1] DMRG start system={P['system']} sites={ns} chi={chi} "
          f"schedule bond_dims={bond_dims} n_threads={n_threads}", flush=True)
    t0 = time.time()
    e = driver.dmrg(mpo, ket, n_sweeps=8, bond_dims=bond_dims, noises=noises,
                    thrds=thrds, iprint=2)   # iprint=2 -> per-sweep energy+DW+time to stdout
    wall = time.time() - t0
    print(f"[e1] DMRG done E={e:.10f} wall_s={wall:.1f}", flush=True)
    return dict(E_dmrg=float(e), chi=chi, wall_s=round(wall, 1),
                sweep_schedule=dict(n_sweeps=8, bond_dims=bond_dims, noises=noises,
                                    thrds=thrds, symmetry="SU2"),
                scratch=scratch)


def machine_specs(n_threads):
    return dict(platform=platform.platform(), python=platform.python_version(),
                cpu_count=os.cpu_count(), n_threads=n_threads,
                omp_num_threads=os.environ.get("OMP_NUM_THREADS"),
                mem_total_gb=round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9, 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", choices=["cro", "h20"], required=True)
    ap.add_argument("--chi", type=int, default=800)
    ap.add_argument("--ncas", type=int, default=19)
    ap.add_argument("--n-threads", type=int, default=8)
    ap.add_argument("--out", type=str, default=None, help="output json filename (in results/)")
    ap.add_argument("--validate-note", type=str, default=None)
    a = ap.parse_args()

    t_all = time.time()
    if a.system == "cro":
        P = cro_integrals(a.ncas); tag = f"cro{a.ncas}_chi{a.chi}"
        conv_key = "rohf_converged"
    else:
        P = h20_integrals(20); tag = f"h20_chi{a.chi}"
        conv_key = "rhf_converged"
    print(f"[e1] integrals ready: {P['active_space']} {P['qubits']}q "
          f"{conv_key}={P[conv_key]} [{time.time()-t_all:.0f}s]", flush=True)

    R = run_dmrg(P, a.chi, tag, n_threads=a.n_threads)
    peak_rss_gb = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 ** 2), 2)

    out = dict(
        system=P["system"], active_space=P["active_space"], qubits=P["qubits"],
        dmrg_chi=a.chi, E_dmrg=R["E_dmrg"], wall_s=R["wall_s"],
        sweep_schedule=R["sweep_schedule"], thresholds=R["sweep_schedule"]["thrds"],
        peak_host_rss_gb=peak_rss_gb, scratch_dir=R["scratch"],
        machine=machine_specs(a.n_threads),
        code_path_note=("block2 DMRG via pyscf-replicated integral construction "
                        "(qsci_lib cas_problem/hchain_problem integral half; cudaq import "
                        "bypassed on this CPU box -- make_ref never uses the JW qubit operator). "
                        "Same ROHF/RHF + mc.get_h1eff()/get_h2eff() + ao2mo.restore(1,..) path."),
        prereg="E1 chi-escalation counter-audit (results/preregistration_v2.json)",
    )
    out[conv_key] = P[conv_key]
    if a.validate_note:
        out["validate_note"] = a.validate_note
    fn = a.out or f"{a.system}_{P['qubits']}q_dmrg_chi{a.chi}.json"
    path = os.path.join(_RES, fn)
    json.dump(out, open(path, "w"), indent=2)
    print(f"[e1] wrote results/{fn}  E={R['E_dmrg']:.10f} chi={a.chi} "
          f"wall_s={R['wall_s']} peak_rss_gb={peak_rss_gb}", flush=True)


if __name__ == "__main__":
    main()
