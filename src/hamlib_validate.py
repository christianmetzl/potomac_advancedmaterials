import sys, pickle
from openfermion import MolecularData, jordan_wigner, get_fermion_operator
from openfermionpyscf import run_pyscf
REF={14:(28,27735,151.39933003406185),16:(32,47489,202.27685442967848),20:(40,116577,328.47746113556263)}
n=int(sys.argv[1]); R=0.70; nq_ref,nt_ref,on_ref=REF[n]
geom=[("H",(0.0,0.0,i*R)) for i in range(n)]; mult=1 if n%2==0 else 2
mol=MolecularData(geom,"sto-6g",mult,charge=0); mol=run_pyscf(mol,run_scf=True)
of=jordan_wigner(get_fermion_operator(mol.get_molecular_hamiltonian()))
nq=2*mol.n_orbitals; nt=len(of.terms); on=sum(abs(c) for c in of.terms.values())
print(f"H{n} @ R=0.70:")
print(f"  qubits:    ours={nq}   HamLib={nq_ref}   {'MATCH' if nq==nq_ref else 'DIFFER'}")
print(f"  terms:     ours={nt}   HamLib={nt_ref}   {'MATCH' if nt==nt_ref else 'DIFFER'}")
print(f"  one-norm:  ours={on:.14f}")
print(f"             HamLib={on_ref:.14f}")
print(f"             |diff|={abs(on-on_ref):.3e}  ({'MATCH to '+str(len(str(int(on))))+'+ sig figs' if abs(on-on_ref)<1e-6 else 'DIFFER'})")
pickle.dump({'terms':of.terms,'nq':nq},open(f"h{n}_jw_R0.70.pkl","wb"))
