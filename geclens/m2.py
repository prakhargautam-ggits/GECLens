"""Reading and writing M2 files.

An M2 block has one ``S`` line with the tokenised source sentence and one ``A`` line per edit:
``A start end|||type|||correction|||REQUIRED|||-NONE-|||annotator``. A ``noop`` edit (``-1 -1``) records that an annotator
made no change. Blocks are separated by a blank line.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

Edit = Tuple[int, int, str, str]  # (start, end, type, correction)

NOOP_LINE = "A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||{a}"


@dataclass
class Sentence:
    """One M2 block: source tokens and the edits of each annotator (noop edits are dropped, the annotator is kept)."""

    source: List[str]
    edits: Dict[int, List[Edit]] = field(default_factory=dict)
    raw: str = ""

    @property
    def annotators(self) -> List[int]:
        return sorted(self.edits)

    def all_edits(self) -> List[Edit]:
        return [e for eds in self.edits.values() for e in eds]

    def is_unedited(self) -> bool:
        """True when every annotator left the sentence unchanged."""
        return bool(self.edits) and all(len(e) == 0 for e in self.edits.values())


def split_blocks(text: str) -> List[str]:
    text = text.strip("\n")
    return [b for b in text.split("\n\n")] if text.strip() else []


def parse_block(block: str) -> Sentence:
    lines = block.strip("\n").split("\n")
    if not lines or not lines[0].startswith("S"):
        raise ValueError(f"M2 block does not start with an S line: {lines[:1]}")
    src = lines[0][2:].split() if len(lines[0]) > 1 else []
    edits: Dict[int, List[Edit]] = {}
    for ln in lines[1:]:
        if not ln.startswith("A "):
            continue
        span, etype, cor, *_rest = ln[2:].split("|||")
        ann = int(_rest[-1]) if _rest else 0
        s, e = (int(x) for x in span.split())
        edits.setdefault(ann, [])
        if etype == "noop" or s == -1:
            continue
        edits[ann].append((s, e, etype, cor))
    if not edits:
        edits[0] = []
    return Sentence(src, edits, block)


def read_m2(path: str) -> List[Sentence]:
    with open(path, encoding="utf-8") as fh:
        return [parse_block(b) for b in split_blocks(fh.read())]


def read_blocks(path: str) -> List[str]:
    with open(path, encoding="utf-8") as fh:
        return split_blocks(fh.read())


def read_lines(path: str) -> List[str]:
    with open(path, encoding="utf-8") as fh:
        return fh.read().rstrip("\n").split("\n")


def apply_edits(source: List[str], edits: List[Edit]) -> List[str]:
    """Apply one annotator's edits to the source tokens (right to left so offsets stay valid)."""
    out = list(source)
    for s, e, _t, c in sorted(edits, key=lambda x: (x[0], x[1]), reverse=True):
        toks = [] if c in ("", "-NONE-") else c.split()
        out[s:e] = toks
    return out
