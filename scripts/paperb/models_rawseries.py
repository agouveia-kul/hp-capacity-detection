"""Raw-series family (iteration 05b, Task 1e): a small 1D-CNN on a substation's chronological daily series, no hand-made features.

Input per substation (feature set `raw`, columns of `substations.raw_daily`): RAW_DAYS daily means of the net load and of the
station temperature (UTC days from the pool's start; a shorter window is padded with NaN), plus the anchor columns of the run
(`Feature Scale_size`, and `Feature Scale_peak` under size_peak). The net-load channel is divided by the size anchor; NaN days take
the median of the training rows of that day; each channel is standardised with its mean / sd over the training rows; the anchors
enter as log values, standardised, joined after pooling. All of these statistics are fitted on the rows passed to `fit` only.
Architecture: `n_blocks` x [Conv1d(kernel, width) -> ReLU -> MaxPool(2)] -> global average pooling -> concat anchors ->
Linear(width) -> ReLU -> Dropout -> Linear(1). Adam with weight decay, batch 64, MSE on the (standardised) target. Early stopping
(patience 20, at most MAX_EPOCHS) on the household-disjoint training fold the caller passes (`train.tune_grouped_cv`: the next
training fold, never the scored one); the final model is refit for the median best epoch count. Deterministic: torch seeded,
deterministic algorithms, a fixed thread count, seeded batch order.
"""
import numpy as np
from hyperopt import hp

RAW_PREFIX, RAW_DAYS, MAX_EPOCHS, PATIENCE, BATCH = "rs_", 365, 200, 20, 64
CNN_SPACE = {"width": hp.choice("width", [8, 16, 32]), "kernel": hp.choice("kernel", [3, 5, 7, 9]),
             "n_blocks": hp.choice("n_blocks", [2, 3]), "dropout": hp.uniform("dropout", 0.0, 0.3),
             "weight_decay": hp.loguniform("weight_decay", np.log(1e-6), np.log(1e-2)),
             "lr": hp.loguniform("lr", np.log(3e-4), np.log(3e-3))}


def raw_columns(n_days=RAW_DAYS):
    return [f"{RAW_PREFIX}y_{i:03d}" for i in range(n_days)] + [f"{RAW_PREFIX}T_{i:03d}" for i in range(n_days)]


class RawSeriesCNN:
    def __init__(self, params, seed, threads=1, device="cpu"):
        self.p, self.seed, self.threads, self.device = dict(params), int(seed), max(1, int(threads)), str(device)

    def _torch(self):
        """torch, seeded and deterministic on self.device (CUDA needs CUBLAS_WORKSPACE_CONFIG for deterministic matmuls)."""
        import os
        if self.device.startswith("cuda"):
            os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        import torch
        torch.manual_seed(self.seed)
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.benchmark = False
        torch.set_num_threads(self.threads)
        return torch

    def _arrays(self, X, fit=False):
        """DataFrame -> (series [n, 2, days], anchors [n, k]) with the training-row statistics."""
        ycol = [c for c in X.columns if c.startswith(f"{RAW_PREFIX}y_")]
        tcol = [c for c in X.columns if c.startswith(f"{RAW_PREFIX}T_")]
        acol = [c for c in X.columns if not c.startswith(RAW_PREFIX)]
        size = X["Feature Scale_size"].to_numpy(float)[:, None]
        S = np.stack([X[ycol].to_numpy(float) / size, X[tcol].to_numpy(float)], axis=1)
        A = np.log(np.maximum(X[acol].to_numpy(float), 1e-6))
        if fit:
            self.med = np.nanmedian(S, axis=0)
            self.med = np.where(np.isfinite(self.med), self.med, 0.0)
        S = np.where(np.isfinite(S), S, self.med[None])
        if fit:
            self.s_mu, self.s_sd = S.mean(axis=(0, 2)), S.std(axis=(0, 2)) + 1e-9
            self.a_mu, self.a_sd = A.mean(0), A.std(0) + 1e-9
        return ((S - self.s_mu[None, :, None]) / self.s_sd[None, :, None]).astype(np.float32), ((A - self.a_mu) / self.a_sd).astype(np.float32)

    def _net(self, n_anchor):
        import torch
        from torch import nn
        w, k = int(self.p["width"]), int(self.p["kernel"])
        layers, c = [], 2
        for _ in range(int(self.p["n_blocks"])):
            layers += [nn.Conv1d(c, w, k, padding=k // 2), nn.ReLU(), nn.MaxPool1d(2)]
            c = w

        class Net(nn.Module):
            def __init__(s):
                super().__init__()
                s.conv, s.head = nn.Sequential(*layers), nn.Sequential(nn.Linear(w + n_anchor, w), nn.ReLU(),
                                                                       nn.Dropout(float(self.p["dropout"])), nn.Linear(w, 1))

            def forward(s, x, a):
                return s.head(torch.cat([s.conv(x).mean(dim=2), a], dim=1)).squeeze(1)
        return Net()

    def fit(self, X, y, n_iter=None, es=None):
        """Train; with `es` = (X_es, y_es) and no n_iter: early-stop and return the best epoch count (the model is then
        refit for that many epochs, deterministically); otherwise train `n_iter` (or MAX_EPOCHS) epochs and return None."""
        torch = self._torch()
        dev = torch.device(self.device)
        S, A = self._arrays(X, fit=True)
        t = [torch.from_numpy(S).to(dev), torch.from_numpy(A).to(dev), torch.from_numpy(np.asarray(y, np.float32)).to(dev)]
        self.net = self._net(A.shape[1]).to(dev)
        self.n_params = int(sum(q.numel() for q in self.net.parameters()))
        opt = torch.optim.Adam(self.net.parameters(), lr=float(self.p["lr"]), weight_decay=float(self.p["weight_decay"]))
        gen = torch.Generator().manual_seed(self.seed)
        if es is not None and n_iter is None:
            Se, Ae = self._arrays(es[0])
            te = (torch.from_numpy(Se).to(dev), torch.from_numpy(Ae).to(dev), torch.from_numpy(np.asarray(es[1], np.float32)).to(dev))
        best, best_ep = np.inf, 1
        for ep in range(1, (n_iter or MAX_EPOCHS) + 1):
            self.net.train()
            for b in torch.randperm(len(t[2]), generator=gen).split(BATCH):     # batch order drawn on the CPU (seeded)
                b = b.to(dev)
                opt.zero_grad()
                torch.mean((self.net(t[0][b], t[1][b]) - t[2][b]) ** 2).backward()
                opt.step()
            if es is not None and n_iter is None:
                self.net.eval()
                with torch.no_grad():
                    loss = float(torch.mean((self.net(te[0], te[1]) - te[2]) ** 2))
                if loss < best - 1e-9:
                    best, best_ep = loss, ep
                elif ep - best_ep >= PATIENCE:
                    break
        if es is not None and n_iter is None:
            self.fit(X, y, n_iter=best_ep)
            return best_ep
        return None

    def predict(self, X):
        import torch
        dev = torch.device(self.device)
        S, A = self._arrays(X)
        self.net.eval()
        with torch.no_grad():
            return self.net(torch.from_numpy(S).to(dev), torch.from_numpy(A).to(dev)).cpu().numpy().astype(float)
