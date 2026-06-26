"""Group-14 monoxide registry for the conditional-encoder demonstration.

Builds CAS(ncas,nelec) qubit Hamiltonians for {CO, SiO, GeO, SnO} (and bond-length
variants) via the validated materials_ham.cas_to_qubit path, and extracts the
active-space MP2 features used as the conditioning signal. Everything is cached to
disk so training / transfer runs do not rebuild PySCF objects.

All four monoxides at the same CAS share an identical operator pool and Pauli
structure (verified: 763 terms at CAS(6,6)/12q), so a single generator's tokens
mean the same excitation for every molecule.

EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # src/ on path
from pyscf import gto, scf, mcscf, ao2mo
from openfermion import InteractionOperator, get_fermion_operator, jordan_wigner, get_sparse_operator
from openfermion.chem.molecular_data import spinorb_from_spatial

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".mol_cache")
os.makedirs(CACHE, exist_ok=True)

# Equilibrium bond lengths (Angstrom). All-electron def2-SVP except Sn (def2-SVP ECP).
REGISTRY = {
    "CO":  dict(Re=1.128, Zmetal=6,  atom=lambda R: f"C 0 0 0; O 0 0 {R:.4f}",
                basis={"C": "def2-svp", "O": "def2-svp"}, ecp=None),
    "SiO": dict(Re=1.510, Zmetal=14, atom=lambda R: f"Si 0 0 0; O 0 0 {R:.4f}",
                basis={"Si": "def2-svp", "O": "def2-svp"}, ecp=None),
    "GeO": dict(Re=1.625, Zmetal=32, atom=lambda R: f"Ge 0 0 0; O 0 0 {R:.4f}",
                basis={"Ge": "def2-svp", "O": "def2-svp"}, ecp=None),
    "SnO": dict(Re=1.833, Zmetal=50, atom=lambda R: f"Sn 0 0 0; O 0 0 {R:.4f}",
                basis={"Sn": "def2-svp", "O": "def2-svp"}, ecp={"Sn": "def2-svp"}),
    # --- chemically DIVERSE diatomics (decisive cross-family transfer test, docs/encoder_design.md) ---
    # All closed-shell singlets at CAS(6,6)/12q; deliberately span distinct bonding/correlation
    # regimes so a single un-conditioned policy cannot fit all of them (unlike the monoxide family).
    "N2":  dict(Re=1.098, Zmetal=7,  atom=lambda R: f"N 0 0 0; N 0 0 {R:.4f}",      # homonuclear triple bond, strong covalent correlation
                basis={"N": "def2-svp"}, ecp=None),
    "BF":  dict(Re=1.263, Zmetal=5,  atom=lambda R: f"B 0 0 0; F 0 0 {R:.4f}",      # polar, isoelectronic with CO/N2
                basis={"B": "def2-svp", "F": "def2-svp"}, ecp=None),
    "LiF": dict(Re=1.564, Zmetal=3,  atom=lambda R: f"Li 0 0 0; F 0 0 {R:.4f}",     # ionic closed shell
                basis={"Li": "def2-svp", "F": "def2-svp"}, ecp=None),
    "BeO": dict(Re=1.331, Zmetal=4,  atom=lambda R: f"Be 0 0 0; O 0 0 {R:.4f}",     # ionic metal-oxide, singlet
                basis={"Be": "def2-svp", "O": "def2-svp"}, ecp=None),
}


def _active_mp2(mo_energy, eri_act, nocc):
    """RMP2 doubles amplitudes + correlation energy within the active space.

    eri_act: chemist-notation (pq|rs) active-space MO integrals, shape (n,n,n,n).
    Returns t2 (nocc,nocc,nvir,nvir) and the active-space MP2 correlation energy.
    """
    n = mo_energy.shape[0]; nvir = n - nocc
    eo = mo_energy[:nocc]; ev = mo_energy[nocc:]
    # (ia|jb) integrals: occ-vir-occ-vir block in chemist notation
    iajb = eri_act[:nocc, nocc:, :nocc, nocc:]          # (i,a,j,b)
    denom = (eo[:, None, None, None] + eo[None, None, :, None]
             - ev[None, :, None, None] - ev[None, None, None, :])  # (i,a,j,b)
    t_iajb = iajb / denom
    # MP2 correlation energy: sum (ia|jb)*(2*(ia|jb) - (ib|ja)) / denom
    e_mp2 = np.einsum("iajb,iajb->", t_iajb, 2 * iajb - iajb.transpose(0, 3, 2, 1))
    t2 = t_iajb.transpose(0, 2, 1, 3)                    # -> (i,j,a,b)
    return t2, float(e_mp2)


def build(name, R=None, ncas=6, nelec=6, rebuild=False):
    """Build (or load from cache) the qubit Hamiltonian + conditioning features.

    Returns a dict: qop, e_cas (active-space FCI), nq, ne, and descriptor inputs
    (mo_energy_active, nocc_active, t2, e_mp2_active, homo_lumo_gap, Zmetal, R).
    """
    spec = REGISTRY[name]
    R = spec["Re"] if R is None else R
    key = f"{name}_R{R:.4f}_cas{ncas}_{nelec}.pkl"
    path = os.path.join(CACHE, key)
    if os.path.exists(path) and not rebuild:
        return pickle.load(open(path, "rb"))

    kw = dict(atom=spec["atom"](R), basis=spec["basis"], verbose=0, spin=0, charge=0)
    if spec["ecp"]:
        kw["ecp"] = spec["ecp"]
    mol = gto.M(**kw)
    mf = scf.RHF(mol).run(conv_tol=1e-10)

    mc = mcscf.CASCI(mf, ncas, nelec); mc.verbose = 0
    e_cas = float(mc.kernel()[0])
    ncore = mc.ncore                                     # frozen-core count
    act = slice(ncore, ncore + ncas)
    mo_e_act = mf.mo_energy[act].copy()
    nocc = nelec // 2

    h1e, ecore = mc.get_h1eff()
    h2e = ao2mo.restore(1, mc.get_h2eff(), ncas)         # chemist (pq|rs), active space
    two_body = np.asarray(h2e.transpose(0, 2, 3, 1), order="C")
    one_so, two_so = spinorb_from_spatial(h1e, two_body)
    qop = jordan_wigner(get_fermion_operator(InteractionOperator(ecore, one_so, 0.5 * two_so)))

    t2, e_mp2 = _active_mp2(mo_e_act, h2e, nocc)
    homo_lumo = float(mo_e_act[nocc] - mo_e_act[nocc - 1])

    out = dict(name=name, R=float(R), ncas=ncas, nelec=nelec, nq=2 * ncas, ne=nelec,
               qop=qop, e_cas=e_cas, hf_energy=float(mf.e_tot),
               mo_energy_active=mo_e_act, nocc_active=nocc, t2=t2,
               e_mp2_active=e_mp2, homo_lumo_gap=homo_lumo, Zmetal=spec["Zmetal"])
    pickle.dump(out, open(path, "wb"))
    return out


def hsp(rec):
    """Sparse (CSR) Hamiltonian for fast statevector energies (valid <=12q)."""
    return get_sparse_operator(rec["qop"], n_qubits=rec["nq"]).tocsr()


if __name__ == "__main__":
    # Smoke check: build all four at CAS(6,6) and confirm structure aligns.
    nt = None
    for nm in REGISTRY:
        r = build(nm)
        t = len(r["qop"].terms)
        nt = t if nt is None else nt
        flag = "OK" if t == nt else "POOL MISMATCH"
        print(f"{nm:4s} {r['nq']}q terms={t:5d} CASCI={r['e_cas']:12.6f} "
              f"Emp2(act)={r['e_mp2_active']:9.6f} gap={r['homo_lumo_gap']:.4f} [{flag}]")
