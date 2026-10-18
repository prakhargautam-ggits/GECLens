"""Type-targeted test subsets and reference statistics.

For an error-type selector, every reference sentence is assigned to sentence-level subsets:

* ``positive``      at least one annotator made an edit of the selected type;
* ``positive_all``  every annotator made an edit of the selected type;
* ``unedited``      no annotator made any edit (reference-supported correct sentence);
* ``unedited_any``  at least one annotator made no edit;
* ``other``         edited by some annotator but with no edit of the selected type.

``positive`` is where a targeted corrector must act; ``unedited`` is where any change is an over-correction.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Dict, List

from .m2 import Sentence, read_m2
from .types import TypeSelector, as_selector


@dataclass
class Subsets:
    selector: str
    n: int
    positive: List[int] = field(default_factory=list)
    positive_all: List[int] = field(default_factory=list)
    unedited: List[int] = field(default_factory=list)
    unedited_any: List[int] = field(default_factory=list)
    other: List[int] = field(default_factory=list)

    def sizes(self) -> Dict[str, int]:
        return {k: len(v) for k, v in asdict(self).items() if isinstance(v, list)}

    def to_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(asdict(self), fh, indent=1)

    @classmethod
    def from_json(cls, path: str) -> "Subsets":
        with open(path, encoding="utf-8") as fh:
            return cls(**json.load(fh))


def build_subsets(ref, selector) -> Subsets:
    """``ref``: path of a reference M2 file or a list of :class:`Sentence`."""
    sents: List[Sentence] = read_m2(ref) if isinstance(ref, str) else ref
    sel: TypeSelector = as_selector(selector)
    sub = Subsets(sel.label, len(sents))
    for i, s in enumerate(sents):
        has = {a: any(sel(e[2]) for e in eds) for a, eds in s.edits.items()}
        if any(has.values()):
            sub.positive.append(i)
        if has and all(has.values()):
            sub.positive_all.append(i)
        if s.is_unedited():
            sub.unedited.append(i)
        if any(len(e) == 0 for e in s.edits.values()):
            sub.unedited_any.append(i)
        if not any(has.values()) and not s.is_unedited():
            sub.other.append(i)
    return sub


def reference_stats(ref, top: int = 25) -> dict:
    """Counts of sentences, annotators and edits per ERRANT type in a reference M2 file."""
    sents: List[Sentence] = read_m2(ref) if isinstance(ref, str) else ref
    by_type: Counter = Counter()
    for s in sents:
        for e in s.all_edits():
            by_type[e[2]] += 1
    total = sum(by_type.values())
    return {
        "sentences": len(sents),
        "annotators": max((len(s.edits) for s in sents), default=0),
        "unedited_sentences": sum(s.is_unedited() for s in sents),
        "edits": total,
        "types": {t: {"edits": c, "share_pct": round(100 * c / total, 2) if total else 0.0}
                  for t, c in by_type.most_common(top)},
    }
