"""Check GECLens against ERRANT on your own data.

For every system output this script checks that
1. the hypothesis M2 written by GECLens is byte-identical to the one written by `errant_parallel`, and
2. the overall and per-type TP/FP/FN counts of GECLens equal those of `errant_compare -cat 3`, and
3. for every sentence, the TP/FP/FN that GECLens stores equal the local counts of the hypothesis-reference pair that
   `errant_compare -v` reports as chosen for that sentence. With several annotators this checks the annotator choice
   sentence by sentence, not only through the totals.

Usage: python scripts/check_against_errant.py SRC REF.m2 HYP.txt [HYP2.txt ...]
Exit code 0 if every check passes, 1 otherwise.
"""
import os
import re
import subprocess
import sys
import tempfile

from geclens.align import hypothesis_m2
from geclens.score import score_system


def errant_counts(hyp_m2, ref_m2):
    out = subprocess.run(["errant_compare", "-hyp", hyp_m2, "-ref", ref_m2, "-cat", "3"],
                         capture_output=True, text=True, check=True).stdout
    total = tuple(int(x) for x in re.search(r"TP\s+FP\s+FN.*\n(\d+)\s+(\d+)\s+(\d+)", out).groups())
    per = {m.group(1): tuple(int(x) for x in m.groups()[1:4])
           for m in re.finditer(r"^(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+[\d.]+\s+[\d.]+\s+[\d.]+\s*$", out, re.M)}
    return total, per


def errant_chosen(hyp_m2, ref_m2):
    """Per-sentence (tp, fp, fn) of the annotator ERRANT chooses, and the chosen reference id."""
    out = subprocess.run(["errant_compare", "-hyp", hyp_m2, "-ref", ref_m2, "-v"],
                         capture_output=True, text=True, check=True).stdout
    local, chosen = {}, {}
    cur = None
    for line in out.splitlines():
        m = re.match(r"SENTENCE (\d+) - HYP (\d+) - REF (\d+)", line)
        if m:
            cur = tuple(int(x) for x in m.groups())
            continue
        m = re.match(r"Local TP/FP/FN\s*:\s*(\d+) (\d+) (\d+)", line)
        if m and cur is not None:
            local[cur] = tuple(int(x) for x in m.groups())
            continue
        m = re.match(r"\^\^ HYP (\d+), REF (\d+) chosen for sentence (\d+)", line)
        if m:
            h, r, sid = (int(x) for x in m.groups())
            chosen[sid] = (r, local[(sid, h, r)])
    return [chosen[i] for i in sorted(chosen)]


def main(src, ref, *hyps):
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for h in hyps:
            sc = score_system(h, src, ref, h, "R:VERB:SVA", cache_dir=tmp)
            ours_m2 = hypothesis_m2(src, h, cache_dir=tmp)
            theirs_m2 = os.path.join(tmp, "errant_parallel.m2")
            subprocess.run(["errant_parallel", "-orig", src, "-cor", h, "-out", theirs_m2], check=True,
                           capture_output=True)
            same_m2 = open(ours_m2, "rb").read() == open(theirs_m2, "rb").read()
            total, per = errant_counts(theirs_m2, ref)
            m = sc.metrics["overall"]
            same_total = (m["tp"], m["fp"], m["fn"]) == total
            ours = {t: tuple(v) for t, v in sc.per_type.items() if any(v)}
            same_types = ours == {t: v for t, v in per.items() if any(v)}
            per_sent = errant_chosen(theirs_m2, ref)
            comps = [tuple(int(x) for x in row) for row in sc.components["overall"]]
            same_sent = len(per_sent) == len(comps) and all(c == e[1] for c, e in zip(comps, per_sent))
            n_ref = len({e[0] for e in per_sent})
            ok &= same_m2 and same_total and same_types and same_sent
            print(f"{os.path.basename(h)}: M2 {'identical' if same_m2 else 'DIFFERENT'}; "
                  f"overall {'OK' if same_total else 'MISMATCH'} {total}; "
                  f"{len(per)} types {'OK' if same_types else 'MISMATCH'}; "
                  f"{len(comps)} sentences {'OK' if same_sent else 'MISMATCH'} ({n_ref} annotator(s) chosen)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
