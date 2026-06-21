"""STAGE 2 - continuous adjoint-gradient angle refinement (the missing reproducibility code).
Optimizes the continuous angles of the UCCSD singles+doubles operator structure by adjoint-gradient
VQE, minimizing <H> for H2/H4/H6 (STO-6G, R=0.74). Hamiltonian + excitations from the same source
(PennyLane qchem); FCI reference from PySCF. HF-energy check confirms geometry consistency."""
import numpy as np, json, time
import pennylane as qml
from pennylane import numpy as pnp
from pyscf import gto, scf, fci

R=0.74; A2B=1.8897259886; GUARD=255; t_start=time.time(); results=[]
for N in [2,4,6]:
    t0=time.time()
    symbols=["H"]*N
    coords=pnp.array([[0.0,0.0,i*R*A2B] for i in range(N)],requires_grad=False)
    H,nq=qml.qchem.molecular_hamiltonian(symbols,coords,basis="sto-6g",method="pyscf")
    ne=N
    singles,doubles=qml.qchem.excitations(ne,nq)
    hf=qml.qchem.hf_state(ne,nq)
    mf=scf.RHF(gto.M(atom=";".join(f"H 0 0 {i*R:.4f}" for i in range(N)),basis="sto6g",verbose=0)).run(conv_tol=1e-11)
    efci=float(fci.FCI(mf).kernel()[0]); ehf=float(mf.e_tot)
    dev=qml.device("lightning.qubit",wires=nq)
    @qml.qnode(dev,diff_method="adjoint")
    def cost(p):
        qml.BasisState(hf,wires=range(nq)); k=0
        for d in doubles: qml.DoubleExcitation(p[k],wires=d); k+=1
        for s in singles: qml.SingleExcitation(p[k],wires=s); k+=1
        return qml.expval(H)
    npar=len(singles)+len(doubles)
    p=pnp.zeros(npar,requires_grad=True)
    e0=float(cost(p))
    print(f"H{N}: HF-check <HF|H|HF>={e0:.6f} vs RHF={ehf:.6f}  (match={abs(e0-ehf)<1e-4})",flush=True)
    opt=qml.AdamOptimizer(0.1); best=e0
    for it in range(250):
        if time.time()-t_start>GUARD: print(f"  H{N}:[guard] it{it}",flush=True); break
        p,e=opt.step_and_cost(cost,p); e=float(e)
        if e<best: best=e
        if it%40==0: print(f"  H{N} it{it}: {e:.6f} ({abs(e-efci)*1000:.3f} mHa)",flush=True)
    err=abs(best-efci)*1000
    print(f"H{N}: {nq}q FCI={efci:.6f} STAGE2={best:.6f} -> {err:.3f} mHa ({npar} params, {time.time()-t0:.0f}s)\n",flush=True)
    results.append({"system":f"H{N}","qubits":nq,"HF":ehf,"FCI":efci,"stage2_energy":best,
                    "err_mHa":round(err,3),"n_params":npar,"method":"stage-2 adjoint-gradient VQE (UCCSD operator structure)"})
    json.dump(results,open("stage2_refinement_evidence.json","w"),indent=2)
print("saved stage2_refinement_evidence.json",flush=True)
