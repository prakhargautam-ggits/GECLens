"""Check GECLens against ERRANT on your own data.

For every system output this script checks that
1. the hypothesis M2 written by GECLens is byte-identical to the one written by `errant_parallel`, and
2. the overall and per-type TP/FP/FN counts of GECLens equal those of `errant_compare -cat 3`
   (with several reference annotators, ERRANT's choice of annotator is reproduced as well).

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
            ok &= same_m2 and same_total and same_types
            print(f"{os.path.basename(h)}: M2 {'identical' if same_m2 else 'DIFFERENT'}; "
                  f"overall {'OK' if same_total else 'MISMATCH'} {total}; "
                  f"{len(per)} types {'OK' if same_types else 'MISMATCH'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
