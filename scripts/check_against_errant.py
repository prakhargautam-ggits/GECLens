"""Check that GECLens overall and per-type counts equal `errant_compare -cat 3` on your own data.

Usage: python scripts/check_against_errant.py SRC REF.m2 HYP.txt [HYP2.txt ...]
"""
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
           for m in re.finditer(r"^([MRU]:[A-Z:]+|UNK)\s+(\d+)\s+(\d+)\s+(\d+)", out, re.M)}
    return total, per


def main(src, ref, *hyps):
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for h in hyps:
            sc = score_system(h, src, ref, h, "R:VERB:SVA", cache_dir=tmp)
            total, per = errant_counts(hypothesis_m2(src, h, cache_dir=tmp), ref)
            m = sc.metrics["overall"]
            same_total = (m["tp"], m["fp"], m["fn"]) == total
            ours = {t: tuple(v) for t, v in sc.per_type.items() if any(v)}
            same_types = ours == {t: v for t, v in per.items() if any(v)}
            ok &= same_total and same_types
            print(f"{h}: overall {'OK' if same_total else 'MISMATCH'} {total}; "
                  f"{len(per)} types {'OK' if same_types else 'MISMATCH'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
