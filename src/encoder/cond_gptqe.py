"""Conditioned GPT-QE generator: GPTQE + FiLM modulation from a molecular descriptor.

A small MLP maps the (standardized) molecular descriptor to feature-wise affine
parameters (gamma, beta) that modulate the token+position embeddings, so one
generator produces molecule-specific circuit distributions. With a zero descriptor
the conditioning is inert (1+gamma=1, beta=0 at init-friendly scaling), which makes
the non-conditioned baseline architecturally identical.

Reuses the transformer structure of gqe_scaling.GPTQE.

EIGENNEXUS - GIC 2026 Phase 3.
"""
import os, sys, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gqe_scaling import GPTQE


class CondGPTQE(GPTQE):
    def __init__(self, vocab, blk, desc_dim, n_layer=4, n_head=4, n_embd=128, cond_hidden=128):
        super().__init__(vocab, blk, n_layer, n_head, n_embd)
        self.desc_dim = desc_dim
        self.cond = nn.Sequential(
            nn.Linear(desc_dim, cond_hidden), nn.GELU(),
            nn.Linear(cond_hidden, 2 * n_embd))
        # init last layer to ~0 so conditioning starts inert (gamma=0, beta=0)
        nn.init.zeros_(self.cond[-1].weight); nn.init.zeros_(self.cond[-1].bias)
        self.n_embd = n_embd
        self.n_params = sum(p.numel() for p in self.parameters())

    def _film(self, c):
        """c: (B, desc_dim) -> gamma,beta each (B,1,n_embd)."""
        gb = self.cond(c)
        g, b = gb[:, :self.n_embd], gb[:, self.n_embd:]
        return g.unsqueeze(1), b.unsqueeze(1)

    def forward(self, idx, c):
        T = idx.size(1)
        mask = torch.triu(torch.ones(T, T, device=idx.device) * float("-inf"), diagonal=1)
        x = self.tok(idx) + self.pos(torch.arange(T, device=idx.device))
        g, b = self._film(c)
        x = (1.0 + g) * x + b
        for blk in self.blocks:
            x = blk(x, src_mask=mask)
        return self.head(self.ln(x))

    def logit_sums(self, seqs, c):
        B, N = seqs.size()
        start = torch.full((B, 1), self.start, dtype=torch.long, device=seqs.device)
        inp = torch.cat([start, seqs[:, :-1]], 1)
        lg = self.forward(inp, c)
        chosen = lg.gather(2, seqs.unsqueeze(2)).squeeze(2)
        return torch.cumsum(chosen, 1)

    @torch.no_grad()
    def generate(self, n, L, c, temp=1.0, device="cpu"):
        idx = torch.full((n, 1), self.start, dtype=torch.long, device=device)
        for _ in range(L):
            cond = idx if idx.size(1) <= self.blk else idx[:, -self.blk:]
            lg = self.forward(cond, c)[:, -1, :] / temp
            idx = torch.cat([idx, torch.multinomial(F.softmax(lg, -1), 1)], 1)
        return idx[:, 1:]


def expand_cond(c_vec, B, device="cpu"):
    """Broadcast a single descriptor vector to a batch tensor (B, desc_dim)."""
    t = torch.as_tensor(np.asarray(c_vec, dtype=np.float32), device=device)
    return t.unsqueeze(0).expand(B, -1)
