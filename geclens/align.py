"""Convert system output text into hypothesis M2 with ERRANT.

The loop follows ``errant_parallel`` line by line, so the resulting M2 is identical to the command-line tool. The ERRANT
annotator (spaCy model) is loaded once and reused for every system, and results are cached on disk by content hash.
"""
from __future__ import annotations

import hashlib
import os
from typing import List, Optional

from .m2 import NOOP_LINE, read_lines

_ANNOTATOR = None


def get_annotator(lang: str = "en"):
    global _ANNOTATOR
    if _ANNOTATOR is None:
        import errant  # imported lazily: loading spaCy takes a few seconds

        _ANNOTATOR = errant.load(lang)
    return _ANNOTATOR


def align_lines(src: List[str], hyp: List[str], tokenise: bool = False, lev: bool = False,
                merge: str = "rules", annotator=None) -> str:
    """Return the M2 text for one system (one annotator, id 0)."""
    if len(src) != len(hyp):
        raise ValueError(f"source has {len(src)} lines but the system output has {len(hyp)}")
    ann = annotator or get_annotator()
    out = []
    for i, (o, c) in enumerate(zip(src, hyp)):
        o, c = o.strip(), c.strip()
        if not o:
            raise ValueError(f"empty source line {i + 1}: ERRANT would skip it and misalign the files")
        if not tokenise:
            orig = ann.parse(o, False)
            lines = ["S " + " ".join(t.text for t in orig)]
            if orig.text.strip() == c:
                lines.append(NOOP_LINE.format(a=0))
            else:
                cor = ann.parse(c, False)
                for edit in ann.annotate(orig, cor, lev, merge):
                    lines.append(edit.to_m2(0))
        else:
            # The source must keep the tokens of the reference M2, so only the system output is tokenised.
            orig = ann.parse(o, False)
            cor = ann.parse(c, True)
            lines = ["S " + " ".join(t.text for t in orig)]
            edits = [] if orig.text.strip() == cor.text.strip() else ann.annotate(orig, cor, lev, merge)
            lines.extend(e.to_m2(0) for e in edits)
            if not edits:
                lines.append(NOOP_LINE.format(a=0))
        out.append("\n".join(lines))
    return "".join(block + "\n\n" for block in out)  # byte-identical to errant_parallel


def _digest(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()[:20]


def hypothesis_m2(src_path: str, hyp_path: str, cache_dir: Optional[str] = None, tokenise: bool = False) -> str:
    """Path of the hypothesis M2 for ``hyp_path``; built with ERRANT (and cached) if needed.

    If ``hyp_path`` already ends in ``.m2`` it is returned unchanged.
    """
    if hyp_path.endswith(".m2"):
        return hyp_path
    src, hyp = read_lines(src_path), read_lines(hyp_path)
    cache_dir = cache_dir or os.path.join(os.path.dirname(os.path.abspath(hyp_path)), ".geclens_cache")
    os.makedirs(cache_dir, exist_ok=True)
    key = _digest("align-v3", "\n".join(src), "\n".join(hyp), str(tokenise))
    out = os.path.join(cache_dir, f"{os.path.splitext(os.path.basename(hyp_path))[0]}.{key}.m2")
    if not os.path.exists(out):
        text = align_lines(src, hyp, tokenise=tokenise)
        tmp = out + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, out)
    return out
