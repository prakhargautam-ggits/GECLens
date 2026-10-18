import os
import re
import subprocess

import pytest

from geclens.align import hypothesis_m2
from geclens.score import prf


def _errant_compare(hyp_m2, ref_m2, cat=None):
    cmd = ["errant_compare", "-hyp", hyp_m2, "-ref", ref_m2]
    if cat:
        cmd += ["-cat", str(cat)]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


@pytest.mark.parametrize("system", ["careful", "eager", "cautious"])
def test_overall_and_type_match_errant(toy_scores, data, tmp_path, system):
    sc = toy_scores[system]
    hyp = hypothesis_m2(os.path.join(data, "src.txt"), os.path.join(data, f"{system}.txt"), cache_dir=str(tmp_path))
    out = _errant_compare(hyp, os.path.join(data, "ref.m2"), cat=3)
    tp, fp, fn = (int(x) for x in re.search(r"TP\s+FP\s+FN.*\n(\d+)\s+(\d+)\s+(\d+)", out).groups())
    m = sc.metrics["overall"]
    assert (m["tp"], m["fp"], m["fn"]) == (tp, fp, fn)
    row = re.search(r"^R:VERB:SVA\s+(\d+)\s+(\d+)\s+(\d+)", out, re.M)
    t = sc.metrics["type"]
    if row:
        assert (t["tp"], t["fp"], t["fn"]) == tuple(int(x) for x in row.groups())
    else:
        assert (t["tp"], t["fp"], t["fn"]) == (0, 0, 0)


def test_behaviour_on_toy(toy_scores):
    careful, eager, cautious = (toy_scores[k].metrics for k in ("careful", "eager", "cautious"))
    assert careful["overcorrection"]["rate"] == 0.0
    assert eager["overcorrection"]["rate"] == 1.0
    assert eager["overall"]["F0.5"] < careful["overall"]["F0.5"]
    assert cautious["success"]["rate"] < careful["success"]["rate"]


def test_prf_conventions():
    assert prf(0, 0, 0) == (1.0, 1.0, 1.0)
    assert prf(0, 0, 5)[2] == 0.0
    p, r, f = prf(3, 1, 2)
    assert abs(p - .75) < 1e-12 and abs(r - .6) < 1e-12 and abs(f - (1.25 * .75 * .6 / (.25 * .75 + .6))) < 1e-12


def test_hypothesis_m2_byte_identical_to_errant_parallel(data, tmp_path):
    src, hyp = os.path.join(data, "src.txt"), os.path.join(data, "eager.txt")
    ours = hypothesis_m2(src, hyp, cache_dir=str(tmp_path / "c"))
    ref = tmp_path / "errant.m2"
    subprocess.run(["errant_parallel", "-orig", src, "-cor", hyp, "-out", str(ref)], check=True, capture_output=True)
    assert open(ours, encoding="utf-8").read() == ref.read_text(encoding="utf-8")


def test_tokenise_plain_text_output(data, tmp_path):
    """A detokenised copy of a system output, scored with tokenise=True, gives the same counts as the original."""
    import re as _re
    from geclens.score import score_system
    src, ref = os.path.join(data, "src.txt"), os.path.join(data, "ref.m2")
    plain = tmp_path / "plain.txt"
    lines = open(os.path.join(data, "careful.txt"), encoding="utf-8").read().splitlines()
    plain.write_text("\n".join(_re.sub(r" ([.,!?;:])", r"\1", l) for l in lines) + "\n", encoding="utf-8")
    a = score_system("tok", src, ref, os.path.join(data, "careful.txt"), cache_dir=str(tmp_path / "a"))
    b = score_system("plain", src, ref, str(plain), cache_dir=str(tmp_path / "b"), tokenise=True)
    for m in ("overall", "type", "type_only", "detection"):
        assert (a.metrics[m]["tp"], a.metrics[m]["fp"], a.metrics[m]["fn"]) == \
               (b.metrics[m]["tp"], b.metrics[m]["fp"], b.metrics[m]["fn"])
    assert a.metrics["overcorrection"] == b.metrics["overcorrection"]
