"""Confidence intervals and significance tests on per-sentence components.

* Percentile bootstrap confidence intervals (sentence-level resampling).
* Paired approximate randomisation (per-sentence swap of two systems' outputs), the usual significance test for GEC.
* Paired bootstrap intervals of the difference between two systems.
* Holm-Bonferroni adjustment within a family of tests.

All routines work on the additive components stored in :class:`geclens.score.SystemScore`, so any measure (F0.5, F1, rates)
is recomputed exactly from resampled sums. Random generators are seeded for reproducibility.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .score import BETA, MEASURES, SystemScore

CHUNK = 500


def _vec_metric(measure: str, S: np.ndarray, beta: float = BETA) -> np.ndarray:
    """Vectorised measure over summed components S with shape (k, c)."""
    S = S.astype(np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        if measure in ("overall", "type", "type_only"):
            tp, fp, fn = S[:, 0], S[:, 1], S[:, 2]
            p = np.where(tp + fp > 0, tp / np.maximum(tp + fp, 1e-300), 1.0)
            r = np.where(tp + fn > 0, tp / np.maximum(tp + fn, 1e-300), 1.0)
            b2 = beta ** 2
            return np.where(p + r > 0, (1 + b2) * p * r / np.maximum(b2 * p + r, 1e-300), 0.0)
        if measure == "detection":
            tp, fp, fn = S[:, 0], S[:, 1], S[:, 2]
            return np.where(tp > 0, 2 * tp / (2 * tp + fp + fn), 0.0)
        if measure in ("success", "overcorrection", "change_rate"):
            return np.where(S[:, 1] > 0, S[:, 0] / S[:, 1], np.nan)
    raise KeyError(measure)


def point(score: SystemScore, measure: str, beta: float = BETA) -> float:
    return float(_vec_metric(measure, score.components[measure].sum(0, keepdims=True), beta)[0])


def _weights(rng, n: int, k: int) -> np.ndarray:
    return np.stack([np.bincount(rng.integers(0, n, n), minlength=n) for _ in range(k)]).astype(np.float64)


def bootstrap_ci(score: SystemScore, measures: Sequence[str] = MEASURES, resamples: int = 10000, seed: int = 13,
                 level: float = 0.95, beta: float = BETA) -> Dict[str, Tuple[float, float]]:
    """Percentile bootstrap interval for each measure (unadjusted)."""
    rng = np.random.default_rng(seed)
    n = score.n
    vals: Dict[str, list] = {m: [] for m in measures}
    done = 0
    while done < resamples:
        k = min(CHUNK, resamples - done)
        W = _weights(rng, n, k)
        for m in measures:
            vals[m].append(_vec_metric(m, W @ score.components[m].astype(np.float64), beta))
        done += k
    lo, hi = 100 * (1 - level) / 2, 100 * (1 + level) / 2
    return {m: (float(np.nanpercentile(np.concatenate(v), lo)), float(np.nanpercentile(np.concatenate(v), hi)))
            for m, v in vals.items()}


def approx_randomisation(a: SystemScore, b: SystemScore, measure: str, shuffles: int = 10000, seed: int = 13,
                         beta: float = BETA) -> Tuple[float, float]:
    """Two-sided paired approximate randomisation test. Returns (difference a - b, p-value).

    p = (number of shuffles with |d*| >= |d| + 1) / (shuffles + 1).
    """
    if a.n != b.n:
        raise ValueError("systems were scored on different numbers of sentences")
    rng = np.random.default_rng(seed)
    A = a.components[measure].astype(np.float64)
    B = b.components[measure].astype(np.float64)
    SA, SB, D = A.sum(0), B.sum(0), A - B
    obs = float(_vec_metric(measure, SA[None], beta)[0] - _vec_metric(measure, SB[None], beta)[0])
    hits, done = 0, 0
    while done < shuffles:
        k = min(CHUNK, shuffles - done)
        M = (rng.random((k, a.n)) < 0.5).astype(np.float64)
        moved = M @ D
        d = _vec_metric(measure, SA[None] - moved, beta) - _vec_metric(measure, SB[None] + moved, beta)
        hits += int(np.sum(np.abs(np.nan_to_num(d)) >= abs(obs) - 1e-12))
        done += k
    return obs, (hits + 1) / (shuffles + 1)


def paired_bootstrap_ci(a: SystemScore, b: SystemScore, measure: str, resamples: int = 10000, seed: int = 15,
                        level: float = 0.95, beta: float = BETA) -> Tuple[float, float]:
    """Percentile interval of the difference a - b under shared sentence resamples."""
    rng = np.random.default_rng(seed)
    A = a.components[measure].astype(np.float64)
    B = b.components[measure].astype(np.float64)
    out, done = [], 0
    while done < resamples:
        k = min(CHUNK, resamples - done)
        W = _weights(rng, a.n, k)
        out.append(_vec_metric(measure, W @ A, beta) - _vec_metric(measure, W @ B, beta))
        done += k
    d = np.concatenate(out)
    lo, hi = 100 * (1 - level) / 2, 100 * (1 + level) / 2
    return float(np.nanpercentile(d, lo)), float(np.nanpercentile(d, hi))


def holm(pvalues: Sequence[float]) -> List[float]:
    """Holm-Bonferroni adjusted p-values (step-down, monotone)."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adj, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvalues[i]))
        adj[i] = running
    return adj


@dataclass
class Comparison:
    a: str
    b: str
    measure: str
    diff: float
    p: float
    p_holm: float
    ci: Optional[Tuple[float, float]]

    def as_dict(self) -> dict:
        return {"a": self.a, "b": self.b, "measure": self.measure, "diff": self.diff, "p": self.p,
                "p_holm": self.p_holm, "ci_low": None if self.ci is None else self.ci[0],
                "ci_high": None if self.ci is None else self.ci[1]}


def compare_systems(scores: Dict[str, SystemScore], measures: Sequence[str] = ("type_only", "overcorrection"),
                    pairs: Optional[Iterable[Tuple[str, str]]] = None, baseline: Optional[str] = None,
                    shuffles: int = 10000, resamples: int = 2000, seed: int = 13, beta: float = BETA) -> List[Comparison]:
    """Run all requested paired tests as one Holm family.

    ``pairs`` lists (a, b) system names; otherwise every system is compared with ``baseline`` if given, else all pairs.
    """
    names = list(scores)
    if pairs is None:
        pairs = [(s, baseline) for s in names if s != baseline] if baseline else list(combinations(names, 2))
    pairs = list(pairs)
    rows = []
    for a, b in pairs:
        for m in measures:
            d, p = approx_randomisation(scores[a], scores[b], m, shuffles, seed, beta)
            ci = paired_bootstrap_ci(scores[a], scores[b], m, resamples, seed + 2, beta=beta) if resamples else None
            rows.append([a, b, m, d, p, ci])
    adj = holm([r[4] for r in rows])
    return [Comparison(r[0], r[1], r[2], r[3], r[4], q, r[5]) for r, q in zip(rows, adj)]
