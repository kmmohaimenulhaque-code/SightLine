"""Cramer-Rao lower bound for parameters of an image model with independent per-pixel noise (DERIVED theory).

For pixel means mu_i(theta) and independent noise of variance v_i (Gaussian approximation of Poisson shot noise plus
read noise, v_i = mu_i + read^2 in electrons), the Fisher information matrix is

    I = J^T diag(1 / v) J,      J_ij = d mu_i / d theta_j

and any unbiased estimator has covariance >= I^-1. The bound on a subset of parameters with the others unknown
("nuisance") is the corresponding block of I^-1; with the others known it is the inverse of that block of I.

The bound concerns *precision* (scatter of an unbiased estimator). It says nothing about *accuracy*: bias from a wrong
model, calibration or print errors is outside it.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def numerical_jacobian(mean_fn: Callable[[np.ndarray], np.ndarray], theta0: np.ndarray, steps: np.ndarray) -> np.ndarray:
    """Central-difference Jacobian of ``mean_fn`` (returns a flat array) at ``theta0``; one step size per parameter."""
    theta0, steps = np.asarray(theta0, float), np.asarray(steps, float)
    cols = []
    for j, h in enumerate(steps):
        d = np.zeros_like(theta0)
        d[j] = h
        cols.append((np.ravel(mean_fn(theta0 + d)) - np.ravel(mean_fn(theta0 - d))) / (2.0 * h))
    return np.column_stack(cols)


def fisher_information(jacobian: np.ndarray, variance: np.ndarray) -> np.ndarray:
    j = np.asarray(jacobian, float)
    v = np.ravel(np.asarray(variance, float))
    if np.any(v <= 0):
        raise ValueError("pixel variances must be positive")
    return j.T @ (j / v[:, None])


def crlb_covariance(fisher: np.ndarray, subset: slice | list[int] | None = None, nuisance_known: bool = False) -> np.ndarray:
    """Lower-bound covariance for ``subset`` of the parameters (all by default). Inversion is done on the
    diagonally-scaled matrix; a (numerically) non-identifiable nuisance direction is handled by the pseudo-inverse."""
    f = np.asarray(fisher, float)
    idx = np.arange(f.shape[0])[subset] if subset is not None else np.arange(f.shape[0])
    if nuisance_known:
        f = f[np.ix_(idx, idx)]
        idx = np.arange(f.shape[0])
    scale = np.sqrt(np.clip(np.diag(f), 1e-300, None))
    cov = np.linalg.pinv(f / np.outer(scale, scale), rcond=1e-10, hermitian=True) / np.outer(scale, scale)
    return cov[np.ix_(idx, idx)]
