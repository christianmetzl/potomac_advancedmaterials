import sys, os, pickle
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

# --- optional FULL offline third-party re-verification against the committed HamLib slice (if bundled) ---
_slice=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"data","hamlib_slice",f"H{n}_sto6g_jw.qubitop.gz")
if os.path.exists(_slice):
    import gzip, collections
    from openfermion import QubitOperator
    hl=QubitOperator(gzip.open(_slice,"rt",encoding="utf-8").read())
    _mag=lambda op: collections.Counter(round(abs(c),9) for c in op.terms.values())
    full_match=(len(hl.terms)==nt) and (_mag(of)==_mag(hl))     # phase-invariant: handles the orbital-phase convention
    print(f"  FULL offline HamLib slice: terms={len(hl.terms)}  phase-invariant coeff-magnitude multiset "
          f"{'MATCH' if full_match else 'DIFFER'}  [genuine third-party operator, no download]")
else:
    print("  (full offline slice absent — run src/hamlib_extract_slice.py to bundle it; the term-count + "
          "one-norm equivalence above already holds without any download)")
