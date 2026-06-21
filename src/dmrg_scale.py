"""DMRG (tensor-network/MPS ground state) scaling for hydrogen chains.
Demonstrates the MPS backend (pillar 1) reaches chemical accuracy past 40 qubits.
Energy reference: FCI where available (<=20q), else CCSD(T) at equilibrium (gold standard)."""
import sys, time, numpy as np
from pyscf import gto, scf, cc
log=open("dmrg.log","a")
def L(m): log.write(m+"\n"); log.flush(); print(m,flush=True)

def run(n_atoms, R=0.74, maxM=250, fci_ref=None):
    t0=time.time()
    atom=";".join(f"H 0 0 {i*R:.4f}" for i in range(n_atoms))
    mol=gto.M(atom=atom, basis="sto6g", verbose=0)
    mf=scf.RHF(mol).run(conv_tol=1e-10)
    nq=2*mol.nao
    # CCSD(T) reference (gold standard at equilibrium)
    mycc=cc.CCSD(mf); mycc.verbose=0; mycc.kernel()
    et=mycc.ccsd_t()
    e_ccsdt=mycc.e_tot+et
    L(f"\nH{n_atoms}: {nq} qubits | RHF={mf.e_tot:.6f} | CCSD(T)={e_ccsdt:.6f} | t_setup={time.time()-t0:.0f}s")
    # DMRG via block2
    from pyblock2._pyscf.ao2mo import integrals as itg
    from pyblock2.driver.core import DMRGDriver, SymmetryTypes
    ncas,nelec,spin,ecore,h1e,g2e,orbsym=itg.get_rhf_integrals(mf,ncore=0,ncas=None,g2e_symm=8)
    driver=DMRGDriver(scratch=f"/tmp/dmrg{n_atoms}",symm_type=SymmetryTypes.SU2,n_threads=4)
    driver.initialize_system(n_sites=ncas,n_elec=nelec,spin=spin,orb_sym=orbsym)
    tm=time.time()
    mpo=driver.get_qc_mpo(h1e=h1e,g2e=g2e,ecore=ecore,iprint=0)
    L(f"  MPO built in {time.time()-tm:.0f}s")
    ket=driver.get_random_mps(tag="KET",bond_dim=150,nroots=1)
    bond_dims=[100,150,200,maxM,maxM,maxM]
    noises=[1e-4,1e-5,1e-6,0,0,0]
    thrds=[1e-7]*6
    t1=time.time()
    e_dmrg=driver.dmrg(mpo,ket,n_sweeps=6,bond_dims=bond_dims,noises=noises,thrds=thrds,iprint=0)
    dw=driver.get_bipartite_entanglement() if False else None
    ref=fci_ref if fci_ref is not None else e_ccsdt
    lbl="FCI" if fci_ref is not None else "CCSD(T)"
    L(f"  DMRG(M={maxM})={e_dmrg:.6f} | vs {lbl}={ref:.6f} | diff={abs(e_dmrg-ref)*1000:.3f} mHa | t_dmrg={time.time()-t1:.0f}s")
    return e_dmrg,e_ccsdt

if __name__=="__main__":
    n=int(sys.argv[1]); ref=float(sys.argv[2]) if len(sys.argv)>2 else None
    run(n, fci_ref=ref)
