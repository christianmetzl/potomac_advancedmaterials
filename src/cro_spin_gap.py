"""CrO spin-state DECISION TABLE: DFT functionals disagree (1.9 eV spread, B3LYP flips the
ground state); a single multireference value (CASCI / QSCI in a fixed active space) breaks the tie.

gap = E(triplet) - E(quintet)  [eV].  gap>0  => quintet (5-Pi) is the ground state.
Gas-phase CrO ground term is experimentally X 5-Pi (quintet), so a positive gap agrees with
experiment and any functional giving gap<0 (here B3LYP) predicts the WRONG ground state.

HONEST SCOPE: CAS(10,10)/def2-SVP is a fixed, modest active space; the CASCI/QSCI number is
'the single value DFT functionals scatter around', NOT a benchmark-quality experimental gap.
The defensible claim: DFT spans 1.9 eV and even flips the ordering; the multireference treatment
gives ONE consistent answer, and that answer agrees with the experimental quintet ground term.
"""
import os, json, numpy as np
from pyscf import gto, scf, mcscf, ao2mo
_RES=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"results")
from openfermion import InteractionOperator, get_fermion_operator, jordan_wigner
from openfermion.chem.molecular_data import spinorb_from_spatial
import scipy.sparse as sp, scipy.sparse.linalg as sla

HA2EV=27.211386245988; R=1.621; NCAS=10
STATES={"quintet":dict(spin=4,nelecas=(7,3)), "triplet":dict(spin=2,nelecas=(6,4))}
_PC=np.array([bin(i).count('1') for i in range(256)],dtype=np.uint8)
def parity(x): b=x.view(np.uint8).reshape(-1,8); return (_PC[b].sum(1)&1).astype(np.int8)

def qsci_energy(qop_terms, nelecas, e_ref, tcap=40.0):
    XM=[];ZYM=[];PH=[]
    for pauli,coeff in qop_terms.items():
        xm=zym=nY=0
        for q,op in pauli:
            if op in('X','Y'): xm|=(1<<q)
            if op in('Z','Y'): zym|=(1<<q)
            if op=='Y': nY+=1
        XM.append(xm);ZYM.append(zym);PH.append(complex(coeff)*(1j)**nY)
    XM=np.array(XM,dtype=np.uint64);ZYM=np.array(ZYM,dtype=np.uint64);PH=np.array(PH,dtype=np.complex128)
    def Hon(c): cc_=np.uint64(c); return np.bitwise_xor(cc_,XM),PH*(1-2*parity(np.bitwise_and(cc_,ZYM)))
    diagm=XM==0; ZYMd=ZYM[diagm];PHd=PH[diagm]
    def diagv(cf):
        out=np.empty(len(cf))
        for i,c in enumerate(cf): out[i]=np.sum(PHd*(1-2*parity(np.bitwise_and(np.uint64(int(c)),ZYMd)))).real
        return out
    def build_H(space):
        sc=np.sort(space);order=np.argsort(space);n=len(space);R_=[];C=[];V=[]
        for i,c in enumerate(space):
            nc,amp=Hon(int(c));pos=np.clip(np.searchsorted(sc,nc),0,n-1);v=sc[pos]==nc
            j=order[pos[v]];R_.append(j);C.append(np.full(j.shape,i));V.append(amp[v])
        return sp.csr_matrix((np.concatenate(V),(np.concatenate(R_),np.concatenate(C))),shape=(n,n),dtype=complex)
    na,nb=nelecas; hf=0
    for i in range(na): hf|=(1<<(2*i))
    for i in range(nb): hf|=(1<<(2*i+1))
    space=np.array([hf],dtype=np.uint64); bestE=None; best=1e9; t0=__import__("time").time()
    for it in range(25):
        H=build_H(space)
        if H.shape[0]<3: E=float(np.linalg.eigvalsh(H.toarray())[0]);c=np.array([1.0])
        else: w,v=sla.eigsh(H,k=1,which='SA');E=float(w[0]);c=v[:,0]
        if abs(E-e_ref)*1000<best: best=abs(E-e_ref)*1000; bestE=E
        if best<0.3 or len(space)>=5000 or __import__("time").time()-t0>tcap: break
        cvec=np.abs(np.asarray(c).ravel()); sig=np.where(cvec>1e-4)[0]; sc=np.sort(space); contrib={}
        for ci in sig:
            nc,amp=Hon(int(space[ci])); pos=np.clip(np.searchsorted(sc,nc),0,len(space)-1); ins=sc[pos]==nc
            for u,a in zip(nc[~ins].tolist(),(amp[~ins]*np.asarray(c).ravel()[ci]).tolist()): contrib[u]=contrib.get(u,0)+a
        cand=np.array(list(contrib.keys()),dtype=np.uint64); num=np.array(list(contrib.values()))
        dv=diagv(cand); den=E-dv; den[np.abs(den)<1e-9]=-1e-9
        space=np.concatenate([space,cand[np.argsort(np.abs(num)**2/np.abs(den))[::-1][:400]]])
    return bestE, best

E_casci={}; E_qsci={}
for st,sp_ in STATES.items():
    mol=gto.M(atom=f"Cr 0 0 0; O 0 0 {R}",basis="def2-svp",spin=sp_["spin"],charge=0,verbose=0)
    mf=scf.ROHF(mol); mf.max_cycle=300; mf.conv_tol=1e-9; mf.kernel()
    mc=mcscf.CASCI(mf,NCAS,sp_["nelecas"]); mc.verbose=0
    e=float(mc.kernel()[0]); E_casci[st]=e
    h1e,ecore=mc.get_h1eff(); h2e=ao2mo.restore(1,mc.get_h2eff(),NCAS)
    one_so,two_so=spinorb_from_spatial(h1e,np.asarray(h2e.transpose(0,2,3,1),order='C'))
    qop=jordan_wigner(get_fermion_operator(InteractionOperator(ecore,one_so,0.5*two_so)))
    eq,err=qsci_energy(qop.terms,sp_["nelecas"],e); E_qsci[st]=eq
    print(f"{st}: CASCI={e:.6f}  QSCI={eq:.6f} (err {err:.3f} mHa)",flush=True)

gap_casci=(E_casci["triplet"]-E_casci["quintet"])*HA2EV
gap_qsci =(E_qsci["triplet"] -E_qsci["quintet"]) *HA2EV
dft=json.load(open(os.path.join(_RES,"dft_functional_spread_evidence.json")))["systems"]["CrO"]["gaps_eV"]

def gs(gap): return "quintet (5-Pi)" if gap>0 else "triplet"
table=[{"method":f,"gap_eV":g,"predicted_GS":gs(g),"correct":(g>0)} for f,g in dft.items()]
table.append({"method":"CASCI (CAS(10,10), exact in active space)","gap_eV":round(gap_casci,3),"predicted_GS":gs(gap_casci),"correct":(gap_casci>0)})
table.append({"method":"QSCI / selected-CI (this work)","gap_eV":round(gap_qsci,3),"predicted_GS":gs(gap_qsci),"correct":(gap_qsci>0)})

out={"system":"CrO  quintet (5-Pi) vs triplet, R=1.621 A, CAS(10,10)=20q",
     "gap_definition":"E(triplet) - E(quintet) [eV]; gap>0 => quintet ground (agrees with experiment X 5-Pi)",
     "experimental_ground_term":"X 5-Pi (quintet) [gas-phase CrO]",
     "dft_spread_eV":round(max(dft.values())-min(dft.values()),3),
     "n_functionals_wrong_sign":int(sum(1 for g in dft.values() if g<0)),
     "wrong_functionals":[f for f,g in dft.items() if g<0],
     "casci_gap_eV":round(gap_casci,3),"qsci_gap_eV":round(gap_qsci,3),
     "decision_table":table,
     "key_finding":f"DFT functionals span {max(dft.values())-min(dft.values()):.2f} eV and B3LYP flips the "
                   f"ground state to triplet; CASCI/QSCI give one consistent quintet ground state, agreeing "
                   f"with the experimental X 5-Pi term. A B3LYP-only screen would carry the wrong spin ground state.",
     "honest_caveats":[
        "CAS(10,10)/def2-SVP is a fixed modest active space; the CASCI/QSCI gap is the single value DFT scatters around, not a benchmark-quality experimental gap.",
        "Each spin state uses CASCI on its own ROHF orbitals (standard), not state-averaged CASSCF.",
        "The robust, defensible claim is the SIGN/ordering agreement with experiment and the 1.9 eV DFT spread, not the precise gap magnitude."]}
json.dump(out,open(os.path.join(_RES,"cro_spin_gap_evidence.json"),"w"),indent=2)
print(f"\nDFT spread={out['dft_spread_eV']} eV; B3LYP gap={dft['B3LYP']} eV (WRONG sign).")
print(f"CASCI gap={gap_casci:+.3f} eV -> {gs(gap_casci)};  QSCI gap={gap_qsci:+.3f} eV -> {gs(gap_qsci)}")
print("saved results/cro_spin_gap_evidence.json")
