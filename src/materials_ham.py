"""Build a qubit Hamiltonian from a PySCF active space (CASCI), validated, then apply to SnO.
Bridges our QSCI scaling engine to real EUV-relevant Sn-oxide chemistry."""
import numpy as np, sys, pickle
from pyscf import gto, scf, mcscf, ao2mo
from openfermion import InteractionOperator, get_fermion_operator, jordan_wigner
from openfermion.chem.molecular_data import spinorb_from_spatial

def cas_to_qubit(mf, ncas, nelecas):
    mc = mcscf.CASCI(mf, ncas, nelecas); mc.verbose=0
    e_fci = mc.kernel()[0]                      # CASCI = FCI within the active space
    h1e, ecore = mc.get_h1eff()                 # (ncas,ncas), scalar
    h2e = ao2mo.restore(1, mc.get_h2eff(), ncas)# chemist (pq|rs), full 4-index
    two_body = np.asarray(h2e.transpose(0,2,3,1), order='C')  # openfermionpyscf convention
    one_so, two_so = spinorb_from_spatial(h1e, two_body)
    ham = InteractionOperator(ecore, one_so, 0.5*two_so)
    qop = jordan_wigner(get_fermion_operator(ham))
    return qop, e_fci, 2*ncas, nelecas

# ---- STEP 1: validate construction on H4 CAS(4,4) (should give FCI = -2.156857 @ R0.74) ----
mol = gto.M(atom=";".join(f"H 0 0 {i*0.74:.4f}" for i in range(4)), basis="sto6g", verbose=0)
mf = scf.RHF(mol).run(conv_tol=1e-10)
qop,e_fci,nq,ne = cas_to_qubit(mf, 4, 4)
print(f"[validate] H4 CAS(4,4): qubits={nq}, terms={len(qop.terms)}, CASCI_FCI={e_fci:.6f}  (expect -2.156857)")
# diagonalize the qubit Hamiltonian to confirm it matches CASCI
from openfermion import get_sparse_operator
import scipy.sparse.linalg as sla
E0 = sla.eigsh(get_sparse_operator(qop, n_qubits=nq), k=1, which='SA')[0][0]
print(f"[validate] qubit-Hamiltonian ground state = {E0:.6f}  diff={abs(E0-e_fci)*1000:.4f} mHa  -> {'CONSTRUCTION OK' if abs(E0-e_fci)<1e-6 else 'MISMATCH'}")
