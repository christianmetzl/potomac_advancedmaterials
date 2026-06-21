"""Memory-efficient, resumable selected-CI/QSCI. Chunked candidate generation + checkpointing."""
import numpy as np, time, sys, pickle, os
import scipy.sparse as sp, scipy.sparse.linalg as sla
N=int(sys.argv[1]); CKPT=f"qsci_space_{N}.npy"
LOG=open(f"qck{N}.log","a")
def L(m): LOG.write(m+"\n"); LOG.flush(); print(m,flush=True)
_PC=np.array([bin(i).count('1') for i in range(256)],dtype=np.uint8)
def parity(x): b=x.view(np.uint8).reshape(-1,8); return (_PC[b].sum(1)&1).astype(np.int8)
REF={4:-2.156857,6:-3.170505,8:-4.186089,10:-5.202826,14:-7.237790,20:-10.292650}

d=pickle.load(open(f"h{N}_jw_R0.74.pkl","rb")); terms=d['terms']; nq=d['nq']; ne=d['ne']; hf=d['hf']
XM=[];ZYM=[];PH=[]
for pauli,coeff in terms.items():
    xm=0;zym=0;nY=0
    for q,op in pauli:
        if op in('X','Y'): xm|=(1<<q)
        if op in('Z','Y'): zym|=(1<<q)
        if op=='Y': nY+=1
    XM.append(xm);ZYM.append(zym);PH.append(complex(coeff)*(1j)**nY)
XM=np.array(XM,dtype=np.uint64);ZYM=np.array(ZYM,dtype=np.uint64);PH=np.array(PH,dtype=np.complex128)
diagmask=(XM==0); XMd=XM[diagmask];ZYMd=ZYM[diagmask];PHd=PH[diagmask]
ref=REF.get(N,hf)

def Hon(c):
    cc=np.uint64(c); newc=np.bitwise_xor(cc,XM); par=parity(np.bitwise_and(cc,ZYM)); return newc,PH*(1-2*par)
def diag_chunk(configs):  # vectorized-ish diagonal energies
    out=np.empty(len(configs))
    for i,c in enumerate(configs):
        par=parity(np.bitwise_and(np.uint64(int(c)),ZYMd)); out[i]=np.sum(PHd*(1-2*par)).real
    return out
def build_Hsub(space):
    sc=np.sort(space); order=np.argsort(space); n=len(space)
    R=[];C=[];V=[]
    for i,c in enumerate(space):
        newc,amp=Hon(int(c)); pos=np.clip(np.searchsorted(sc,newc),0,n-1); val=sc[pos]==newc
        j=order[pos[val]]; R.append(j);C.append(np.full(j.shape,i));V.append(amp[val])
    return sp.csr_matrix((np.concatenate(V),(np.concatenate(R),np.concatenate(C))),shape=(n,n),dtype=complex)

if os.path.exists(CKPT): space=np.load(CKPT); L(f"[resume] H{N} |space|={len(space)}")
else: space=np.array([(1<<ne)-1],dtype=np.uint64); L(f"[start] H{N}: {nq}q {len(terms)} terms ref={ref}")

t0=time.time(); GUARD=240; GROW=2600; CHUNK=120
for it in range(40):
    H=build_Hsub(space)
    if H.shape[0]<3: E=float(np.linalg.eigvalsh(H.toarray())[0]); c=np.array([1.0])
    else: w,v=sla.eigsh(H,k=1,which='SA'); E=float(w[0]); c=v[:,0]
    err=abs(E-ref)*1000
    L(f"  |space|={len(space):5d}  E={E:.6f}  err={err:.3f} mHa  t={time.time()-t0:.0f}s")
    np.save(CKPT,space)
    if err<0.8 or time.time()-t0>GUARD: 
        L(f"[stop] err={err:.3f} mHa, |space|={len(space)}"); break
    cvec=np.asarray(c).ravel(); sig=np.argsort(np.abs(cvec))[::-1][:1500]
    sc=np.sort(space); contrib={}
    for s in range(0,len(sig),CHUNK):
        batch=sig[s:s+CHUNK]; cs=[];ws=[]
        for ci in batch:
            newc,amp=Hon(int(space[ci])); cs.append(newc); ws.append(amp*cvec[ci])
        cs=np.concatenate(cs); ws=np.concatenate(ws)
        pos=np.clip(np.searchsorted(sc,cs),0,len(space)-1); ins=sc[pos]==cs
        cs=cs[~ins]; ws=ws[~ins]
        if len(cs)==0: continue
        uq,inv=np.unique(cs,return_inverse=True); num=np.zeros(len(uq),dtype=complex); np.add.at(num,inv,ws)
        for u,nm in zip(uq.tolist(),num.tolist()): contrib[u]=contrib.get(u,0)+nm
    if not contrib: L("[converged: no new configs]"); break
    cand=np.array(list(contrib.keys()),dtype=np.uint64); numv=np.array(list(contrib.values()),dtype=complex)
    dv=diag_chunk(cand); den=E-dv; den[np.abs(den)<1e-9]=-1e-9
    score=np.abs(numv)**2/np.abs(den); top=np.argsort(score)[::-1][:GROW]
    space=np.concatenate([space,cand[top]])
L(f"RESULT H{N}: E={E:.6f} err={abs(E-ref)*1000:.3f} mHa |space|={len(space)}")
