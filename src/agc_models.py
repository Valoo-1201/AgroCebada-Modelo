"""agc_models.py: código de modelado compartido del Reto AgroCebada 2026 (lo escribe el cuaderno 06)."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.linalg import cho_factor, cho_solve


# ----------------------------------------------------------------------------------------------
# Selección de variables dentro de un pliegue de entrenamiento
# ----------------------------------------------------------------------------------------------
def within_muni_rho(X, y, muni):
    """|rho de Spearman| entre cada columna y y, después de centrar ambas en la media de su municipio."""
    df = X.copy()
    df["_y"] = np.asarray(y, float)
    dm = df.sub(df.groupby(np.asarray(muni)).transform("mean"))
    return dm[X.columns].corrwith(dm["_y"], method="spearman").abs().fillna(0)


def select_features(tr, y, muni, candidates, clusters, k):
    """Las k variables con mayor |rho| dentro de municipio, calculado SOLO en el pliegue de entrenamiento,
    con a lo más una variable por grupo de redundancia (casi duplicados, |rho| >= 0.9)."""
    if k <= 0:
        return []
    X = tr[candidates].astype(float)
    X = X.fillna(X.median())
    rho = within_muni_rho(X, y, muni).sort_values(ascending=False)
    chosen, used = [], set()
    for f in rho.index:
        c = clusters.get(f, f)
        if c in used:
            continue
        chosen.append(f)
        used.add(c)
        if len(chosen) == k:
            break
    return chosen


def prep(tr, te, cols):
    """Imputación por mediana y estandarización con estadísticas del pliegue de ENTRENAMIENTO."""
    if not cols:
        return np.zeros((len(tr), 0)), np.zeros((len(te), 0))
    med = tr[cols].astype(float).median()
    A, B = tr[cols].astype(float).fillna(med), te[cols].astype(float).fillna(med)
    mu, sd = A.mean(), A.std().replace(0, 1).fillna(1)
    return ((A - mu) / sd).to_numpy(), ((B - mu) / sd).to_numpy()


def muni_prior(tr_muni, tr_y, te_muni):
    """Media municipal del pliegue de entrenamiento (media general para municipios no vistos)."""
    s = pd.Series(np.asarray(tr_y, float)).groupby(np.asarray(tr_muni)).mean()
    g = float(np.mean(tr_y))
    return (pd.Series(np.asarray(tr_muni)).map(s).to_numpy(),
            pd.Series(np.asarray(te_muni)).map(s).fillna(g).to_numpy())


# ----------------------------------------------------------------------------------------------
# Proceso gaussiano jerárquico (propio)
# ----------------------------------------------------------------------------------------------
def _matern32(d, l):
    a = np.sqrt(3.0) * d / l
    return (1 + a) * np.exp(-a)


class HierGP:
    """Rendimiento = media general
             + efecto de municipio              (efecto aleatorio: s_muni · 1[mismo municipio])
             + efecto espacial a escala de finca (s_spatial · Matérn-3/2(distancia / l_spatial))
             + efecto de variables satelitales, climáticas o de suelo (opcional; lineal: s_feat · <x_i, x_j> / n_variables)
             + ruido                            (error de reporte o redondeo, variación no explicada)
    Todas las varianzas y escalas de longitud se aprenden maximizando la verosimilitud marginal (evidencia bayesiana)."""

    def __init__(self, use_features=True, restarts=3, seed=0, feat_kernel="linear"):
        # feat_kernel = "linear" (una sola varianza compartida: robusto con ~110 parcelas) o "ard" (una escala por variable;
        # se probó durante el desarrollo y se descartó: la evidencia elegía 10 variables en todos los pliegues y el error de VC subía 0.04 t/ha)
        self.use_features, self.restarts, self.seed, self.fk = use_features, restarts, seed, feat_kernel

    def _K(self, p, A, B, same):
        s_m, s_s, l_s = np.exp(p[0]), np.exp(p[1]), np.exp(p[2])
        D = np.sqrt(((A["xy"][:, None] - B["xy"][None]) ** 2).sum(-1))
        K = s_m * same + s_s * _matern32(D, l_s)
        if self.nf:
            if self.fk == "linear":
                K = K + np.exp(p[3]) * (A["f"] @ B["f"].T) / self.nf
            else:
                Z = (A["f"][:, None, :] - B["f"][None]) / np.exp(p[4:-1])
                K = K + np.exp(p[3]) * np.exp(-0.5 * (Z ** 2).sum(-1))
        return K

    def _nll(self, p):
        K = self._K(p, self.A, self.A, self.same) + (np.exp(p[-1]) + 1e-6) * np.eye(len(self.r))
        try:
            c = cho_factor(K, lower=True)
        except np.linalg.LinAlgError:
            return 1e10
        a = cho_solve(c, self.r)
        return 0.5 * self.r @ a + np.log(np.diag(c[0])).sum() + 0.5 * len(self.r) * np.log(2 * np.pi)

    def fit(self, xy_km, muni, f, y):
        y = np.asarray(y, float)
        self.mu = y.mean()
        self.r = y - self.mu
        self.nf = f.shape[1] if self.use_features else 0
        self.A = {"xy": np.asarray(xy_km, float), "f": np.asarray(f, float)}
        self.muni = np.asarray(muni, dtype=object)
        self.same = (self.muni[:, None] == self.muni[None]).astype(float)
        v = self.r.var()
        nl = self.nf if self.fk == "ard" else 0
        x0 = [np.log(v * .5), np.log(v * .2), np.log(.3)] + ([np.log(v * .1)] + [np.log(1.5)] * nl if self.nf else []) + [np.log(v * .3)]
        lo = [np.log(1e-4), np.log(1e-4), np.log(.03)] + ([np.log(1e-4)] + [np.log(.3)] * nl if self.nf else []) + [np.log(1e-3)]
        hi = [np.log(5), np.log(5), np.log(20)] + ([np.log(5)] + [np.log(50)] * nl if self.nf else []) + [np.log(5)]
        rng = np.random.default_rng(self.seed)
        best = None
        for k in range(self.restarts):
            start = np.clip(np.array(x0) + (rng.normal(0, .5, len(x0)) if k else 0), lo, hi)
            res = minimize(self._nll, start, method="L-BFGS-B", bounds=list(zip(lo, hi)))
            if best is None or res.fun < best.fun:
                best = res
        self.p, self.nll = best.x, float(best.fun)
        K = self._K(self.p, self.A, self.A, self.same) + (np.exp(self.p[-1]) + 1e-6) * np.eye(len(self.r))
        self.c = cho_factor(K, lower=True)
        self.alpha = cho_solve(self.c, self.r)
        return self

    def predict(self, xy_km, muni, f, return_std=False):
        B = {"xy": np.asarray(xy_km, float), "f": np.asarray(f, float)}
        m = np.asarray(muni, dtype=object)
        same = (m[:, None] == self.muni[None]).astype(float)
        Ks = self._K(self.p, B, self.A, same)
        mean = self.mu + Ks @ self.alpha
        if not return_std:
            return mean
        prior = np.exp(self.p[0]) + np.exp(self.p[1]) + (np.exp(self.p[3]) if self.nf else 0)
        v = cho_solve(self.c, Ks.T)
        var_f = np.clip(prior - (Ks * v.T).sum(1), 0, None)
        return mean, np.sqrt(var_f + np.exp(self.p[-1]))      # DE predictiva para una observación nueva

    def params(self):
        e = np.exp(self.p)
        out = {"s_muni": e[0], "s_spatial": e[1], "l_spatial_km": e[2], "noise": e[-1]}
        if self.nf:
            out["s_feat"] = e[3]
            out.update({f"l_feat_{i}": v for i, v in enumerate(e[4:-1])})
        return out
