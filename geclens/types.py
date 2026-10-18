"""Error-type selectors.

GECLens works with ERRANT edit types such as ``R:VERB:SVA``, ``M:DET`` or ``U:PUNCT``. A selector decides which edit types
belong to the error category under study. Selectors accept:

* an exact ERRANT type, e.g. ``R:VERB:SVA``;
* a category without the operation prefix, e.g. ``DET`` or ``VERB:TENSE``. This matches the missing (M), replacement (R)
  and unnecessary (U) variants of that category, as ERRANT does with ``-cat 2``;
* a shell-style pattern, e.g. ``R:VERB*`` or ``*:PREP``;
* a comma-separated list of any of the above, e.g. ``R:VERB:SVA,R:VERB:FORM``.
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Iterable, List

_OPS = ("M:", "R:", "U:")


def _expand(part: str) -> List[str]:
    part = part.strip()
    if not part:
        return []
    if any(ch in part for ch in "*?["):
        return [part]
    if part.startswith(_OPS) or part in ("UNK", "noop"):
        return [part]
    return [op + part for op in _OPS]


@dataclass(frozen=True)
class TypeSelector:
    """Matches ERRANT edit types against one or more patterns."""

    spec: str
    patterns: tuple = field(init=False)

    def __post_init__(self):
        pats: List[str] = []
        for part in self.spec.split(","):
            pats.extend(_expand(part))
        if not pats:
            raise ValueError(f"empty error-type selector: {self.spec!r}")
        object.__setattr__(self, "patterns", tuple(pats))

    def __call__(self, etype: str) -> bool:
        if etype == "noop":
            return False
        return any(fnmatch.fnmatchcase(etype, p) for p in self.patterns)

    def matching(self, types: Iterable[str]) -> List[str]:
        return sorted({t for t in types if self(t)})

    @property
    def label(self) -> str:
        return self.spec


def as_selector(spec) -> TypeSelector:
    return spec if isinstance(spec, TypeSelector) else TypeSelector(str(spec))
