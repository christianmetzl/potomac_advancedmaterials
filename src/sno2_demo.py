"""SnO2 (16 qubits) via CASCI(8,8) with def2-ECP on Sn -> qubit Hamiltonian -> QSCI.
Demonstrates the QSCI engine on REAL EUV-relevant Sn-oxide chemistry (not just H chains)."""
import numpy as np, time, pickle
from pyscf import gto, scf, mcscf, ao2mo
from openfermion import InteractionOperator, get_fermion_operator, jordan_wigner
from openfermion.chem.molecular_data import spinorb_from_spatial
import scipy.sparse as sp, scipy.sparse.linalg as sla
_PC=np.array([bin(i).count('1') for i in range(256)],dtype=np.uint8)
def parity(x): b=x.view(np.uint8).reshape(-1,8); return (_PC[b].sum(1)&1).astype(np.int8)

t0=time.time()
# --- Build SnO2 with effective core potential on Sn ---
R=1.88
mol=gto.M(atom=f"O 0 0 {-R}; Sn 0 0 0; O 0 0 {R}", basis={'Sn':'def2-svp','O':'def2-svp'},
          ecp={'Sn':'def2-svp'}, verbose=0, spin=0, charge=0)
mf=scf.RHF(mol).run(conv_tol=1e-10)
print(f"SnO2: RHF={mf.e_tot:.6f} | {mol.nao} orbitals, {mol.nelectron} electrons (Sn ECP applied) | {time.time()-t0:.0f}s")

# --- CAS(8,8) active space -> qubit Hamiltonian + FCI reference ---
ncas,nelecas=10,10
mc=mcscf.CASCI(mf,ncas,nelecas); mc.verbose=0
e_fci=mc.kernel()[0]
h1e,ecore=mc.get_h1eff(); h2e=ao2mo.restore(1,mc.get_h2eff(),ncas)
two_body=np.asarray(h2e.transpose(0,2,3,1),order='C')
one_so,two_so=spinorb_from_spatial(h1e,two_body)
qop=jordan_wigner(get_fermion_operator(InteractionOperator(ecore,one_so,0.5*two_so)))
nq=2*ncas; ne=nelecas
print(f"SnO2 CAS(8,8): {nq} qubits, {len(qop.terms)} Pauli terms, FCI(CASCI)={e_fci:.6f}")

# --- QSCI (selected-CI) on the SnO2 Hamiltonian ---
XM=[];ZYM=[];PH=[]
for pauli,coeff in qop.terms.items():
    xm=0;zym=0;nY=0
    for q,op in pauli:
        if op in('X','Y'): xm|=(1<<q)
        if op in('Z','Y'): zym|=(1<<q)
        if op=='Y': nY+=1
    XM.append(xm);ZYM.append(zym);PH.append(complex(coeff)*(1j)**nY)
XM=np.array(XM,dtype=np.uint64);ZYM=np.array(ZYM,dtype=np.uint64);PH=np.array(PH,dtype=np.complex128)
diagm=XM==0; ZYMd=ZYM[diagm];PHd=PH[diagm]
def Hon(c): cc=np.uint64(c); return np.bitwise_xor(cc,XM), PH*(1-2*parity(np.bitwise_and(cc,ZYM)))
def build_H(space):
    sc=np.sort(space);order=np.argsort(space);n=len(space);R_=[];C=[];V=[]
    for i,c in enumerate(space):
        nc,amp=Hon(int(c));pos=np.clip(np.searchsorted(sc,nc),0,n-1);v=sc[pos]==nc
        j=order[pos[v]];R_.append(j);C.append(np.full(j.shape,i));V.append(amp[v])
    return sp.csr_matrix((np.concatenate(V),(np.concatenate(R_),np.concatenate(C))),shape=(n,n),dtype=complex)
def diagv(cf):
    out=np.empty(len(cf))
    for i,c in enumerate(cf): out[i]=np.sum(PHd*(1-2*parity(np.bitwise_and(np.uint64(int(c)),ZYMd)))).real
    return out
hf=(1<<ne)-1; space=np.array([hf],dtype=np.uint64)
print("QSCI on SnO2:")
for it in range(10):
    H=build_H(space)
    if H.shape[0]<3: E=float(np.linalg.eigvalsh(H.toarray())[0]);c=np.array([1.0])
    else: w,v=sla.eigsh(H,k=1,which='SA');E=float(w[0]);c=v[:,0]
    err=abs(E-e_fci)*1000
    print(f"  |space|={len(space):4d}  E={E:.6f}  err={err:.3f} mHa")
    if err<0.5 or len(space)>=3500: break
    cvec=np.abs(np.asarray(c).ravel()); sig=np.where(cvec>1e-4)[0]; sc=np.sort(space); contrib={}
    for ci in sig:
        nc,amp=Hon(int(space[ci])); pos=np.clip(np.searchsorted(sc,nc),0,len(space)-1); ins=sc[pos]==nc
        for u,a in zip(nc[~ins].tolist(),(amp[~ins]*np.asarray(c).ravel()[ci]).tolist()): contrib[u]=contrib.get(u,0)+a
    cand=np.array(list(contrib.keys()),dtype=np.uint64); num=np.array(list(contrib.values()))
    dv=diagv(cand); den=E-dv; den[np.abs(den)<1e-9]=-1e-9
    space=np.concatenate([space,cand[np.argsort(np.abs(num)**2/np.abs(den))[::-1][:400]]])
print(f"\nSnO2 QSCI final error vs FCI: {abs(E-e_fci)*1000:.3f} mHa | total {time.time()-t0:.0f}s")
