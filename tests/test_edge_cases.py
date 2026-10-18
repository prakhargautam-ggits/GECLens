"""Hand-built cases: missed, unnecessary and replacement edits, two annotators, two edits of the target type in one
sentence, an unedited sentence and an empty subset. Expected values were worked out by hand."""
import math
import os
import re
import subprocess

import numpy as np

from geclens.score import score_system
from geclens.stats import _vec_metric, approx_randomisation, bootstrap_ci

EDGE = os.path.join(os.path.dirname(__file__), "data", "edge")
SRC, REF, HYP = (os.path.join(EDGE, f) for f in ("src.txt", "ref.m2", "hyp.m2"))


def _score(selector="R:VERB:SVA"):
    return score_system("hyp", SRC, REF, HYP, selector)


def test_counts_equal_errant_with_two_annotators():
    out = subprocess.run(["errant_compare", "-hyp", HYP, "-ref", REF, "-cat", "3"], capture_output=True, text=True,
                         check=True).stdout
    total = tuple(int(x) for x in re.search(r"TP\s+FP\s+FN.*\n(\d+)\s+(\d+)\s+(\d+)", out).groups())
    per = {m.group(1): tuple(int(x) for x in m.groups()[1:])
           for m in re.finditer(r"^([MRU]:[A-Z:]+)\s+(\d+)\s+(\d+)\s+(\d+)", out, re.M)}
    sc = _score()
    m = sc.metrics["overall"]
    assert (m["tp"], m["fp"], m["fn"]) == total
    assert {t: tuple(v) for t, v in sc.per_type.items() if any(v)} == {t: v for t, v in per.items() if any(v)}


def test_sentence_level_measures_by_hand():
    sc = _score().metrics
    # positive sentences: 1 (annotator 1 has an SVA edit), 3 and 5; all three get an SVA edit from the system
    assert (sc["detection"]["tp"], sc["detection"]["fp"], sc["detection"]["fn"]) == (3, 0, 0)
    # sentence 5: annotator 0 needs two SVA edits (only one made), annotator 1 needs one -> success
    assert (sc["success"]["count"], sc["success"]["of"]) == (3, 3)
    # sentence 4 is unedited by both annotators and the system changed it
    assert (sc["overcorrection"]["count"], sc["overcorrection"]["of"]) == (1, 1)
    assert (sc["change_rate"]["count"], sc["change_rate"]["of"]) == (4, 5)


def test_empty_subset_does_not_crash():
    sc = _score("R:CONJ")
    assert sc.metrics["success"]["of"] == 0 and math.isnan(sc.metrics["success"]["rate"])
    assert sc.metrics["type_only"]["F0.5"] == 1.0  # ERRANT convention: no edits expected, none made
    ci = bootstrap_ci(sc, ["success", "type_only"], resamples=50)
    assert math.isnan(ci["success"][0]) and ci["type_only"] == (1.0, 1.0)


def test_resampled_metric_is_recomputed_from_summed_counts():
    sc = _score()
    comp = sc.components["overall"].astype(float)
    rng = np.random.default_rng(0)
    for _ in range(20):
        idx = rng.integers(0, sc.n, sc.n)
        tp, fp, fn = comp[idx].sum(0)
        p = tp / (tp + fp) if tp + fp else 1.0
        r = tp / (tp + fn) if tp + fn else 1.0
        expect = 1.25 * p * r / (0.25 * p + r) if p + r else 0.0
        w = np.bincount(idx, minlength=sc.n).astype(float)[None]
        assert abs(_vec_metric("overall", w @ comp)[0] - expect) < 1e-12


def test_randomisation_swap_equals_explicit_swap():
    a, b = _score(), score_system("ref0", SRC, REF, os.path.join(EDGE, "hyp.m2"), "R:VERB:SVA")
    d, p = approx_randomisation(a, b, "overall", shuffles=99)
    assert d == 0.0 and p == 1.0  # identical systems
    A, B = a.components["type_only"].astype(float), a.components["overall"].astype(float)
    mask = np.array([1, 0, 1, 0, 1], dtype=float)
    swapped = A * (1 - mask[:, None]) + B * mask[:, None]
    assert np.allclose(A.sum(0) - mask @ (A - B), swapped.sum(0))
