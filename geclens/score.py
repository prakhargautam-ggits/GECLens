"""Error-type-targeted scoring of one system against a reference M2 file.

Edit-level scores call ERRANT's own ``compare_m2`` routines, so overall and per-type precision, recall and F0.5 are
identical to ``errant_compare``. For every sentence GECLens keeps the additive components (true/false positives, false
negatives, indicator counts) of each measure, which the statistics module resamples for confidence intervals and tests.

Measures for a selected error type T:

``overall``        ERRANT P/R/F0.5 over all edits.
``type``           ERRANT P/R/F0.5 for edits of type T, read for the annotator that ERRANT selects per sentence (that choice
                   maximises overall F0.5, so it also depends on the system's other edits).
``type_only``      P/R/F0.5 after restricting both hypothesis and reference edits to type T, so the annotator choice depends on
                   T edits only. Use it to compare systems that make different amounts of other edits.
``detection``      sentence-level P/R/F1 for "the sentence contains a T error": gold = some annotator has a T edit,
                   predicted = the system made a T edit.
``success``        share of T-positive sentences in which every T edit of at least one annotator (who made T edits) was
                   produced exactly by the system.
``overcorrection`` share of unedited reference sentences that the system changed (whitespace and quote style ignored).
``change_rate``    share of all sentences that the system changed.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
from errant.commands import compare_m2 as cm

from .align import hypothesis_m2
from .data import Subsets, build_subsets
from .m2 import parse_block, read_blocks, read_lines
from .types import as_selector

BETA = 0.5
MEASURES = ("overall", "type", "type_only", "detection", "success", "overcorrection", "change_rate")


def errant_args(beta: float = BETA, span_detection: bool = False) -> argparse.Namespace:
    return argparse.Namespace(beta=beta, verbose=False, dt=False, ds=span_detection, cs=False, cse=False,
                              single=False, multi=False, filt=[], cat=3)


def prf(tp, fp, fn, beta: float = BETA):
    """Precision, recall and F-beta with ERRANT's conventions (P = R = 1 when undefined)."""
    p = tp / (tp + fp) if tp + fp else 1.0
    r = tp / (tp + fn) if tp + fn else 1.0
    f = (1 + beta ** 2) * p * r / (beta ** 2 * p + r) if p + r else 0.0
    return p, r, f


_QUOTES = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})


def normalise(s: str) -> str:
    """Remove whitespace and unify quote characters, so re-tokenisation alone does not count as a change."""
    return re.sub(r"\s+", "", s.replace("``", '"').replace("''", '"').translate(_QUOTES))


def _restrict(block: str, sel) -> list:
    """ERRANT edit list of one M2 block restricted to the selected type, keeping a noop for annotators left empty."""
    eds = cm.simplify_edits(block)
    coders = sorted({e[4] for e in eds}) or [0]
    keep = [e for e in eds if sel(e[2])]
    for c in coders:
        if not any(e[4] == c for e in keep):
            keep.append([-1, -1, "noop", "-NONE-", c])
    return keep


def errant_counts(hyp_blocks: List[str], ref_blocks: List[str], sel=None, restrict: bool = False,
                  span_detection: bool = False, beta: float = BETA):
    """Per-sentence (tp, fp, fn) overall, for the selected types, and a per-type Counter, following ERRANT exactly.

    With ``restrict=True`` both sides are first restricted to the selected types (``type_only`` scoring).
    """
    if len(hyp_blocks) != len(ref_blocks):
        raise ValueError(f"hypothesis has {len(hyp_blocks)} sentences, reference has {len(ref_blocks)}")
    args = errant_args(beta, span_detection)
    best = Counter({"tp": 0, "fp": 0, "fn": 0})
    per, per_type = [], []
    by_type: Dict[str, np.ndarray] = defaultdict(lambda: np.zeros(3, dtype=np.int64))
    for sid, (h, r) in enumerate(zip(hyp_blocks, ref_blocks)):
        if restrict:
            he, re_ = _restrict(h, sel), _restrict(r, sel)
        else:
            he, re_ = cm.simplify_edits(h), cm.simplify_edits(r)
        hd = cm.process_edits(he, args)
        rd = cm.process_edits(re_, args)
        cd, cat = cm.evaluate_edits(hd, rd, best, sid, "", args)
        best += Counter(cd)
        per.append((cd["tp"], cd["fp"], cd["fn"]))
        t = np.zeros(3, dtype=np.int64)
        for etype, v in cat.items():
            by_type[etype] += np.asarray(v[:3], dtype=np.int64)
            if sel is not None and sel(etype):
                t += np.asarray(v[:3], dtype=np.int64)
        per_type.append(t)
    return np.asarray(per, dtype=np.int64), np.asarray(per_type, dtype=np.int64), dict(by_type)


@dataclass
class SystemScore:
    """Scores of one system; ``components`` holds per-sentence additive parts used by :mod:`geclens.stats`."""

    system: str
    selector: str
    n: int
    metrics: Dict[str, dict] = field(default_factory=dict)
    components: Dict[str, np.ndarray] = field(default_factory=dict, repr=False)
    per_type: Dict[str, List[int]] = field(default_factory=dict, repr=False)

    def summary(self) -> dict:
        out = {"system": self.system, "selector": self.selector, "n": self.n}
        out.update(self.metrics)
        return out

    def to_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({**self.summary(), "per_type": self.per_type}, fh, indent=1)

    def save_components(self, path: str) -> None:
        np.savez_compressed(path, **self.components)


def metric_from_totals(measure: str, c: np.ndarray, beta: float = BETA) -> float:
    """Value of a measure from summed components ``c`` (1-D)."""
    if measure in ("overall", "type", "type_only"):
        return prf(*c[:3], beta=beta)[2]
    if measure == "detection":
        tp, fp, fn = c[:3]
        return 2 * tp / (2 * tp + fp + fn) if tp else 0.0
    if measure in ("success", "overcorrection", "change_rate"):
        return float(c[0] / c[1]) if c[1] else float("nan")
    raise KeyError(measure)


def score_system(name: str, source: str, reference: str, hypothesis: str, selector="R:VERB:SVA",
                 subsets: Optional[Subsets] = None, cache_dir: Optional[str] = None, tokenise: bool = False,
                 beta: float = BETA) -> SystemScore:
    """Score one system.

    ``source``: tokenised source sentences, one per line. ``reference``: reference M2 file (ERRANT-typed).
    ``hypothesis``: system output text (one sentence per line) or a ready-made hypothesis ``.m2`` file.
    """
    sel = as_selector(selector)
    ref_blocks = read_blocks(reference)
    ref_sents = [parse_block(b) for b in ref_blocks]
    subsets = subsets or build_subsets(ref_sents, sel)
    hyp_m2 = hypothesis_m2(source, hypothesis, cache_dir=cache_dir, tokenise=tokenise)
    hyp_blocks = read_blocks(hyp_m2)
    n = len(ref_blocks)
    if len(hyp_blocks) != n:
        raise ValueError(f"{name}: {len(hyp_blocks)} hypothesis sentences but {n} reference sentences")

    overall, typ, by_type = errant_counts(hyp_blocks, ref_blocks, sel, beta=beta)
    type_only, _, _ = errant_counts(hyp_blocks, ref_blocks, sel, restrict=True, beta=beta)

    hyp_sents = [parse_block(b) for b in hyp_blocks]
    hyp_edits = [s.all_edits() for s in hyp_sents]

    # sentence-level detection of the selected type
    gold = np.zeros(n, dtype=bool)
    gold[subsets.positive] = True
    pred = np.array([any(sel(e[2]) for e in eds) for eds in hyp_edits], dtype=bool)
    det = np.stack([gold & pred, ~gold & pred, gold & ~pred], 1).astype(np.int64)

    # correction success on positive sentences
    suc = np.zeros((n, 2), dtype=np.int64)
    for i in subsets.positive:
        hs = {(s, e, c) for s, e, _t, c in hyp_edits[i]}
        ok = False
        for eds in ref_sents[i].edits.values():
            gs = {(s, e, c) for s, e, t, c in eds if sel(t)}
            if gs and gs <= hs:
                ok = True
                break
        suc[i] = (int(ok), 1)

    # changed sentences: compare text when the output is text, otherwise use the edits
    if hypothesis.endswith(".m2"):
        changed = np.array([len(eds) > 0 for eds in hyp_edits], dtype=bool)
    else:
        src_lines, hyp_lines = read_lines(source), read_lines(hypothesis)
        changed = np.array([normalise(h) != normalise(s) for h, s in zip(hyp_lines, src_lines)], dtype=bool)
    unedited = np.zeros(n, dtype=bool)
    unedited[subsets.unedited] = True
    oc = np.stack([changed & unedited, unedited], 1).astype(np.int64)
    cr = np.stack([changed, np.ones(n, dtype=bool)], 1).astype(np.int64)

    comps = {"overall": overall, "type": typ, "type_only": type_only, "detection": det, "success": suc,
             "overcorrection": oc, "change_rate": cr}
    metrics = {}
    for m, c in comps.items():
        tot = c.sum(0)
        if m in ("overall", "type", "type_only"):
            p, r, f = prf(*tot, beta=beta)
            metrics[m] = {"tp": int(tot[0]), "fp": int(tot[1]), "fn": int(tot[2]), "P": p, "R": r, f"F{beta:g}": f}
        elif m == "detection":
            p, r, _ = prf(*tot, beta=1.0)
            metrics[m] = {"tp": int(tot[0]), "fp": int(tot[1]), "fn": int(tot[2]), "P": p, "R": r,
                          "F1": metric_from_totals(m, tot)}
        else:
            metrics[m] = {"rate": metric_from_totals(m, tot), "count": int(tot[0]), "of": int(tot[1])}
    per_type = {t: [int(x) for x in v] for t, v in sorted(by_type.items())}
    return SystemScore(name, sel.label, n, metrics, comps, per_type)
