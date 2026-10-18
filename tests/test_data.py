import os
from geclens.data import build_subsets, reference_stats


def test_subsets_toy(data):
    sub = build_subsets(os.path.join(data, "ref.m2"), "R:VERB:SVA")
    assert sub.n == 30
    assert len(sub.positive) == 16
    assert len(sub.unedited) == 6
    assert set(sub.positive).isdisjoint(sub.unedited)
    assert set(sub.positive) | set(sub.unedited) | set(sub.other) == set(range(30))


def test_reference_stats(data):
    st = reference_stats(os.path.join(data, "ref.m2"))
    assert st["sentences"] == 30 and st["annotators"] == 2
    assert next(iter(st["types"])) == "R:VERB:SVA"
