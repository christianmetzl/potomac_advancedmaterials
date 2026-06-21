"""REAL CrO and NiO transition-metal-oxide QSCI at a TRACTABLE active space.
Open-shell: CrO quintet (5-Pi), NiO triplet (3-Sigma-). PySCF ROHF + CASCI (all-electron def2-SVP)
builds the active-space qubit Hamiltonian; QSCI (selected-CI) converges to the CASCI reference.

HONEST SCOPE: this is CAS(10,10) = 20 qubits. It is NOT the 38-qubit claim and NOT a sub-0.08 mHa
result. A 38q open-shell multireference TM oxide at <=0.08 mHa is infeasible on CPU and requires the
Phase 3 GPUs (CUDA-Q + MPS). These are honest, reproducible, modest-scale transition-metal results."""
import numpy as np, time, json
from pyscf import gto, scf, mcscf, ao2mo
from openfermion import InteractionOperator, get_fermion_operator, jordan_wigner
from openfermion.chem.molecular_data import spinorb_from_spatial
import scipy.sparse as sp, scipy.sparse.linalg as sla
_PC=np.array([bin(i).count('1') for i in range(256)],dtype=np.uint8)
def parity(x): b=x.view(np.uint8).reshape(-1,8); return (_PC[b].sum(1)&1).astype(np.int8)

SYS=[("CrO","Cr 0 0 0; O 0 0 1.621",4,(7,3),"5-Pi (quintet)"),
     ("NiO","Ni 0 0 0; O 0 0 1.627",2,(6,4),"3-Sigma- (triplet)")]
NCAS=10; results=[]
for name,atom,spin,nelecas,term in SYS:
    t0=time.time()
    mol=gto.M(atom=atom,basis="def2-svp",spin=spin,charge=0,verbose=0)
    mf=scf.ROHF(mol).run(conv_tol=1e-9)
    mc=mcscf.CASCI(mf,NCAS,nelecas); mc.verbose=0
    e_fci=float(mc.kernel()[0])
    h1e,ecore=mc.get_h1eff(); h2e=ao2mo.restore(1,mc.get_h2eff(),NCAS)
    one_so,two_so=spinorb_from_spatial(h1e,np.asarray(h2e.transpose(0,2,3,1),order='C'))
    qop=jordan_wigner(get_fermion_operator(InteractionOperator(ecore,one_so,0.5*two_so)))
    nq=2*NCAS; na,nb=nelecas
    print(f"{name} {term}: ROHF={mf.e_tot:.6f} | CAS({sum(nelecas)},{NCAS})={nq}q, {len(qop.terms)} terms, CASCI={e_fci:.6f} | {time.time()-t0:.0f}s",flush=True)
    XM=[];ZYM=[];PH=[]
    for pauli,coeff in qop.terms.items():
        xm=zym=nY=0
        for q,op in pauli:
            if op in('X','Y'): xm|=(1<<q)
            if op in('Z','Y'): zym|=(1<<q)
            if op=='Y': nY+=1
        XM.append(xm);ZYM.append(zym);PH.append(complex(coeff)*(1j)**nY)
    XM=np.array(XM,dtype=np.uint64);ZYM=np.array(ZYM,dtype=np.uint64);PH=np.array(PH,dtype=np.complex128)
    diagm=XM==0; ZYMd=ZYM[diagm];PHd=PH[diagm]
    def Hon(c): cc=np.uint64(c); return np.bitwise_xor(cc,XM),PH*(1-2*parity(np.bitwise_and(cc,ZYM)))
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
    hf=0
    for i in range(na): hf|=(1<<(2*i))
    for i in range(nb): hf|=(1<<(2*i+1))
    space=np.array([hf],dtype=np.uint64); best=1e9
    for it in range(18):
        H=build_H(space)
        if H.shape[0]<3: E=float(np.linalg.eigvalsh(H.toarray())[0]);c=np.array([1.0])
        else: w,v=sla.eigsh(H,k=1,which='SA');E=float(w[0]);c=v[:,0]
        err=abs(E-e_fci)*1000; best=min(best,err)
        print(f"  {name} |space|={len(space):5d} E={E:.6f} err={err:.3f} mHa",flush=True)
        if err<0.5 or len(space)>=6000 or time.time()-t0>115: break
        cvec=np.abs(np.asarray(c).ravel()); sig=np.where(cvec>1e-4)[0]; sc=np.sort(space); contrib={}
        for ci in sig:
            nc,amp=Hon(int(space[ci])); pos=np.clip(np.searchsorted(sc,nc),0,len(space)-1); ins=sc[pos]==nc
            for u,a in zip(nc[~ins].tolist(),(amp[~ins]*np.asarray(c).ravel()[ci]).tolist()): contrib[u]=contrib.get(u,0)+a
        cand=np.array(list(contrib.keys()),dtype=np.uint64); num=np.array(list(contrib.values()))
        dv=diagv(cand); den=E-dv; den[np.abs(den)<1e-9]=-1e-9
        space=np.concatenate([space,cand[np.argsort(np.abs(num)**2/np.abs(den))[::-1][:400]]])
    print(f"  -> {name} QSCI best error vs CASCI: {best:.3f} mHa ({nq}q) | {time.time()-t0:.0f}s\n",flush=True)
    results.append({"system":name,"term_symbol":term,"qubits":nq,"active_space":f"CAS({sum(nelecas)},{NCAS})",
                    "n_pauli_terms":len(qop.terms),"CASCI_energy_Ha":e_fci,"qsci_best_err_mHa":round(best,3),
                    "NOT_38q":True,"note":"tractable 20-qubit demonstration; not the 38q <=0.08 mHa claim"})
    json.dump(results,open("transition_metal_qsci_evidence.json","w"),indent=2)
print("saved transition_metal_qsci_evidence.json",flush=True)
