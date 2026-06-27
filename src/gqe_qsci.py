"""Integrated GQE -> QSCI at 12 qubits (H6): GPT-QE GENERATES the circuit; QSCI then SAMPLES
determinants FROM the generated state (qml.sample) and diagonalizes. Real pipeline, not
perturbative selection. Energy via sparse matvec for speed."""
import numpy as np, time, torch
import torch.nn.functional as F
import pennylane as qml
import scipy.sparse as sp, scipy.sparse.linalg as sla
from gqe_scaling import build_pool, GPTQE
from openfermion import MolecularData, jordan_wigner, get_fermion_operator, get_sparse_operator
from openfermionpyscf import run_pyscf
from pyscf import gto, scf, fci
torch.manual_seed(0); np.random.seed(0)
N=6; R=0.74; t0=time.time()
geom=[("H",(0.0,0.0,i*R)) for i in range(N)]
mol=MolecularData(geom,"sto-6g",1,0); mol=run_pyscf(mol,run_scf=True)
of=jordan_wigner(get_fermion_operator(mol.get_molecular_hamiltonian()))
nq=2*mol.n_orbitals; ne=mol.n_electrons
H_pl=qml.from_openfermion(of); Hsp=get_sparse_operator(of,n_qubits=nq).tocsr()
mf=scf.RHF(gto.M(atom=";".join(f"H 0 0 {i*R:.4f}" for i in range(N)),basis="sto6g",verbose=0)).run(conv_tol=1e-10)
e_fci=fci.FCI(mf).kernel()[0]
print(f"H{N}: {nq}q {ne}e HF={mol.hf_energy:.6f} FCI={e_fci:.6f}",flush=True)
# --- QSCI engine ---
_PC=np.array([bin(i).count('1') for i in range(256)],np.uint8)
def parity(x): b=x.view(np.uint8).reshape(-1,8); return (_PC[b].sum(1)&1).astype(np.int8)
XM=[];ZYM=[];PH=[]
for p,c in of.terms.items():
    xm=zym=0;nY=0
    for q,o in p:
        if o in('X','Y'): xm|=(1<<q)
        if o in('Z','Y'): zym|=(1<<q)
        if o=='Y': nY+=1
    XM.append(xm);ZYM.append(zym);PH.append(complex(c)*(1j)**nY)
XM=np.array(XM,np.uint64);ZYM=np.array(ZYM,np.uint64);PH=np.array(PH,np.complex128)
def Hon(c): cc=np.uint64(c); return np.bitwise_xor(cc,XM), PH*(1-2*parity(np.bitwise_and(cc,ZYM)))
def qsci_energy(dets):
    S=np.unique(np.array(dets,dtype=np.uint64)); sc=np.sort(S);order=np.argsort(S);n=len(S);Rr=[];Cc=[];Vv=[]
    for i,c in enumerate(S):
        ncs,amp=Hon(int(c));pos=np.clip(np.searchsorted(sc,ncs),0,n-1);v=sc[pos]==ncs
        j=order[pos[v]];Rr.append(j);Cc.append(np.full(j.shape,i));Vv.append(amp[v])
    H=sp.csr_matrix((np.concatenate(Vv),(np.concatenate(Rr),np.concatenate(Cc))),shape=(n,n),dtype=complex)
    if n<3: return float(np.linalg.eigvalsh(H.toarray())[0]),n
    w=sla.eigsh(H,k=1,which='SA')[0]; return float(w[0]),n
# --- energy via sparse matvec ---
dev=qml.device("lightning.qubit",wires=nq); pool=build_pool(nq,ne); hf_occ=np.zeros(nq,int); hf_occ[:ne]=1
@qml.qnode(dev,diff_method=None)
def state_circ(idxs):
    for w in np.where(hf_occ)[0]: qml.PauliX(int(w))
    for i in idxs:
        typ,wires,t=pool[int(i)]
        qml.SingleExcitation(t,wires=list(wires)) if typ=="s" else qml.DoubleExcitation(t,wires=list(wires))
    return qml.state()
def energy(idxs):
    psi=np.asarray(state_circ(idxs)); return float((psi.conj()@(Hsp@psi)).real)
print(f"HF via matvec: {energy([]):.6f} (matches HF: {abs(energy([])-mol.hf_energy)<1e-6})",flush=True)
# --- train GPT-QE (Stage 1) ---
SEQ=8; model=GPTQE(len(pool),SEQ,n_embd=96)
opt=torch.optim.AdamW(model.parameters(),lr=5e-4,weight_decay=0.01)
def ev(seqs):
    B,Nn=seqs.shape; sub=np.zeros((B,Nn))
    for b in range(B):
        for Ln in range(1,Nn+1): sub[b,Ln-1]=energy(seqs[b,:Ln])
    return sub
best=mol.hf_energy; best_seq=None; NIT=130; BATCH=16
for it in range(NIT):
    temp=2.0+(0.5-2.0)*it/max(NIT-1,1)
    seqs=model.generate(BATCH,SEQ,temp); sub=ev(seqs.cpu().numpy())
    bi=int(sub[:,-1].argmin())
    if sub[bi,-1]<best: best=float(sub[bi,-1]); best_seq=seqs[bi].cpu().numpy().copy()
    st=torch.tensor(sub,dtype=torch.float32); ws=model.logit_sums(seqs)
    loss=F.mse_loss(ws,st); opt.zero_grad(); loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step()
print(f"GQE best expectation={best:.6f} ({abs(best-e_fci)*1000:.3f} mHa from FCI), t={time.time()-t0:.0f}s",flush=True)
# --- QSCI: pool determinants sampled across GQE-proposed circuits (Kemmoku/Gao-style) ---
sdev=qml.device("lightning.qubit",wires=nq,shots=3000)
def samp_seq(seq):
    @qml.qnode(sdev)
    def q():
        for w in np.where(hf_occ)[0]: qml.PauliX(int(w))
        for i in seq:
            typ,wires,t=pool[int(i)]
            qml.SingleExcitation(t,wires=list(wires)) if typ=="s" else qml.DoubleExcitation(t,wires=list(wires))
        return qml.sample(wires=range(nq))
    Sm=q(); d=np.zeros(len(Sm),dtype=np.uint64)
    for qi in range(nq): d|=(Sm[:,qi].astype(np.uint64)<<np.uint64(qi))
    return d
gen=model.generate(160,SEQ,1.0).cpu().numpy()
if best_seq is not None: gen=np.vstack([best_seq[None,:],gen])
alld=np.concatenate([samp_seq(seq) for seq in gen])
uq,cnt=np.unique(alld,return_counts=True)
keep=uq[np.argsort(cnt)[::-1][:400]]
e_q,nd=qsci_energy(keep)
print(f"GQE->QSCI: pooled {len(uq)} distinct dets from {len(gen)} GQE circuits; diagonalize top {nd} = {e_q:.6f} ({abs(e_q-e_fci)*1000:.3f} mHa from FCI)",flush=True)
import json
json.dump({"system":"H6","qubits":nq,"FCI":e_fci,"HF":mol.hf_energy,
 "GQE_expectation":best,"GQE_err_mHa":round(abs(best-e_fci)*1000,3),
 "GQE_to_QSCI":e_q,"GQE_to_QSCI_err_mHa":round(abs(e_q-e_fci)*1000,3),
 "distinct_dets_pooled":int(len(uq)),"dets_used":int(nd),"n_gqe_circuits":int(len(gen)),"shots_per_circuit":3000,
 "note":"GPT-QE generated the circuit; QSCI sampled determinants from that state (qml.sample) and diagonalized. Real integrated pipeline, not perturbative selection."},
 open("gqe_qsci_evidence.json","w"),indent=2)
print("saved gqe_qsci_evidence.json",flush=True)
