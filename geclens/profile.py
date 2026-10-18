"""Error-type profiles: ERRANT P/R/F0.5 per edit type for many systems at once.

One pass of ERRANT's comparison already yields counts for every edit type (for the annotator ERRANT selects), so a profile
over all types costs the same as a single scoring run. Types can be grouped by ERRANT category (operation prefix dropped).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Optional

import numpy as np

from .m2 import read_m2
from .score import BETA, SystemScore, prf


def category(etype: str) -> str:
    """``R:VERB:SVA`` -> ``VERB:SVA``; ``M:DET`` -> ``DET``."""
    return etype.split(":", 1)[1] if etype[:2] in ("M:", "R:", "U:") else etype


def profile_table(scores: Dict[str, SystemScore], group: str = "type", min_ref_edits: int = 0,
                  reference: Optional[str] = None, types: Optional[Iterable[str]] = None,
                  beta: float = BETA) -> Dict[str, Dict[str, dict]]:
    """``{type: {system: {tp, fp, fn, P, R, F}}}``.

    ``group``: ``"type"`` (full ERRANT type) or ``"category"`` (operation prefix merged).
    ``min_ref_edits``: keep only types with at least this many reference edits (needs ``reference``).
    """
    ref_counts: Dict[str, int] = defaultdict(int)
    if reference:
        for s in read_m2(reference):
            for e in s.all_edits():
                ref_counts[e[2] if group == "type" else category(e[2])] += 1
    table: Dict[str, Dict[str, dict]] = defaultdict(dict)
    for name, sc in scores.items():
        agg: Dict[str, np.ndarray] = defaultdict(lambda: np.zeros(3, dtype=np.int64))
        for t, v in sc.per_type.items():
            key = t if group == "type" else category(t)
            agg[key] += np.asarray(v[:3], dtype=np.int64)
        for key, v in agg.items():
            p, r, f = prf(*v, beta=beta)
            table[key][name] = {"tp": int(v[0]), "fp": int(v[1]), "fn": int(v[2]), "P": p, "R": r, "F": f}
    keep = set(types) if types else None
    out = {}
    for key in sorted(table):
        if keep is not None and key not in keep:
            continue
        if reference and ref_counts.get(key, 0) < min_ref_edits:
            continue
        for name in scores:
            table[key].setdefault(name, {"tp": 0, "fp": 0, "fn": 0, "P": 1.0, "R": 1.0, "F": 0.0})
        out[key] = dict(table[key])
    return out


def ranked_types(reference: str, group: str = "type", top: int = 15) -> List[str]:
    """Most frequent edit types (or categories) in a reference M2 file."""
    counts: Dict[str, int] = defaultdict(int)
    for s in read_m2(reference):
        for e in s.all_edits():
            counts[e[2] if group == "type" else category(e[2])] += 1
    return [t for t, _ in sorted(counts.items(), key=lambda x: -x[1])[:top]]
