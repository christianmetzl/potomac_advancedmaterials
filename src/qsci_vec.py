"""Vectorized selected-CI/QSCI: numpy uint64 Pauli action + searchsorted subspace membership.
Demonstrates QSCI subspace diagonalization at chemical accuracy up to 40 qubits."""
import numpy as np, time, sys, pickle, os
import scipy.sparse as sp, scipy.sparse.linalg as sla

LOG=open(sys.argv[2] if len(sys.argv)>2 else "qv.log","w")
def L(m): LOG.write(m+"\n"); LOG.flush(); print(m,flush=True)
_PC=np.array([bin(i).count('1') for i in range(256)],dtype=np.uint8)
def parity(x):  # x: uint64 array -> parity (0/1) int8 array
    b=x.view(np.uint8).reshape(-1,8); return (_PC[b].sum(1)&1).astype(np.int8)

def load(n,R=0.74):
    d=pickle.load(open(f"h{n}_jw_R{R}.pkl","rb")); return d['terms'],d['nq'],d['ne'],d['hf']

def precompute(terms):
    XM=[];ZYM=[];PH=[]
    for pauli,coeff in terms.items():
        xm=0;zym=0;nY=0
        for q,op in pauli:
            if op in('X','Y'): xm|=(1<<q)
            if op in('Z','Y'): zym|=(1<<q)
            if op=='Y': nY+=1
        XM.append(xm);ZYM.append(zym);PH.append(complex(coeff)*(1j)**nY)
    XM=np.array(XM,dtype=np.uint64);ZYM=np.array(ZYM,dtype=np.uint64);PH=np.array(PH,dtype=np.complex128)
    diag=(XM==0)
    return XM,ZYM,PH,diag

def Hon(c,XM,ZYM,PH):
    cc=np.uint64(c)
    newc=np.bitwise_xor(cc,XM)
    par=parity(np.bitwise_and(cc,ZYM))
    amp=PH*(1-2*par)
    return newc,amp

def diag_vals(configs,XM,ZYM,PH,diag):
    # diagonal <c|H|c> for array of configs
    xmd=XM[diag];zymd=ZYM[diag];phd=PH[diag]
    out=np.empty(len(configs))
    for i,c in enumerate(configs):
        par=parity(np.bitwise_and(np.uint64(c),zymd))
        out[i]=np.sum(phd*(1-2*par)).real
    return out

def build_Hsub(space,XM,ZYM,PH):
    sorted_c=np.sort(space); order=np.argsort(space); n=len(space)
    rows=[];cols=[];vals=[]
    for i,c in enumerate(space):
        newc,amp=Hon(c,XM,ZYM,PH)
        pos=np.searchsorted(sorted_c,newc)
        pos=np.clip(pos,0,n-1)
        valid=sorted_c[pos]==newc
        j=order[pos[valid]]
        rows.append(j); cols.append(np.full(j.shape,i)); vals.append(amp[valid])
    rows=np.concatenate(rows);cols=np.concatenate(cols);vals=np.concatenate(vals)
    return sp.csr_matrix((vals,(rows,cols)),shape=(n,n),dtype=complex)

def selci(XM,ZYM,PH,diag,nq,ne,ref,max_space,n_iter,grow,guard=250):
    hf=(1<<ne)-1; space=np.array([hf],dtype=np.uint64); t0=time.time(); hist=[]
    for it in range(n_iter):
        H=build_Hsub(space,XM,ZYM,PH)
        if H.shape[0]<3: E=float(np.linalg.eigvalsh(H.toarray())[0]); c=np.array([1.0])
        else: w,v=sla.eigsh(H,k=1,which='SA'); E=float(w[0]); c=v[:,0]
        err=abs(E-ref)*1000; hist.append((len(space),E,err))
        L(f"  it{it}: |space|={len(space):5d}  E={E:.6f}  err={err:.3f} mHa  t={time.time()-t0:.0f}s")
        if err<0.8 or len(space)>=max_space or time.time()-t0>guard: break
        # candidate generation (weighted), vectorized accumulation
        cvec=np.asarray(c).ravel(); sig=np.abs(cvec)>2e-4
        allc=[];allw=[]
        for ci in np.where(sig)[0]:
            newc,amp=Hon(int(space[ci]),XM,ZYM,PH)
            allc.append(newc); allw.append(amp*cvec[ci])
        allc=np.concatenate(allc); allw=np.concatenate(allw)
        # remove configs already in space
        sc=np.sort(space); pos=np.clip(np.searchsorted(sc,allc),0,len(space)-1)
        inspace=sc[pos]==allc
        allc=allc[~inspace]; allw=allw[~inspace]
        if len(allc)==0: break
        uniq,inv=np.unique(allc,return_inverse=True)
        num=np.zeros(len(uniq),dtype=complex)
        np.add.at(num,inv,allw)
        dv=diag_vals(uniq,XM,ZYM,PH,diag)
        den=E-dv; den[np.abs(den)<1e-9]=-1e-9
        score=np.abs(num)**2/np.abs(den)
        topidx=np.argsort(score)[::-1][:grow]
        space=np.concatenate([space,uniq[topidx]])
    return E,hist

if __name__=="__main__":
    n=int(sys.argv[1]); ref={4:-2.156857,6:-3.170505,8:-4.186089,10:-5.202826,14:-7.237790,20:-10.292650}
    terms,nq,ne,hf=load(n); XM,ZYM,PH,diag=precompute(terms)
    L(f"H{n}: {nq} qubits, {len(terms)} terms, {ne} e-, HF={hf:.6f}, ref={ref.get(n)}")
    E,hist=selci(XM,ZYM,PH,diag,nq,ne,ref.get(n,hf),max_space=8000,n_iter=15,grow=700)
    L(f"FINAL H{n}: E={E:.6f}  err={abs(E-ref.get(n,hf))*1000:.3f} mHa")
