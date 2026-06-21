"""Molecular descriptor (the 'encoder' input) from active-space MP2 features.

Per (molecule, bond length): flattened active-space MP2 doubles amplitudes (aligned
index-for-index across the isomorphic active spaces) + HOMO-referenced orbital
energies + a few intensive scalars. Standardization is fit on TRAINING molecules
only and applied unchanged to held-out molecules (no leakage).

EIGENNEXUS - GIC 2026 Phase 3.
"""
import numpy as np


def raw_descriptor(rec):
    """Fixed-length raw feature vector for a molecule record from molecules.build()."""
    t2 = rec["t2"].ravel()                                  # (nocc^2 * nvir^2,)
    mo = rec["mo_energy_active"]
    mo_ref = mo - mo[rec["nocc_active"] - 1]                # HOMO-referenced orbital energies
    scalars = np.array([rec["homo_lumo_gap"], rec["e_mp2_active"],
                        rec["Zmetal"] / 50.0, rec["R"]], dtype=np.float64)
    return np.concatenate([t2, mo_ref, scalars]).astype(np.float64)


class Standardizer:
    """Per-dimension z-score; fit on training records only."""
    def __init__(self, eps=1e-8):
        self.mean = None; self.std = None; self.eps = eps

    def fit(self, recs):
        X = np.stack([raw_descriptor(r) for r in recs])
        self.mean = X.mean(0)
        self.std = X.std(0)
        self.std[self.std < self.eps] = 1.0                # leave zero-variance dims unscaled
        return self

    def transform(self, rec):
        return (raw_descriptor(rec) - self.mean) / self.std

    @property
    def dim(self):
        return None if self.mean is None else self.mean.shape[0]
