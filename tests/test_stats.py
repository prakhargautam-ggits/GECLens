from geclens.stats import approx_randomisation, bootstrap_ci, compare_systems, holm, point


def test_holm_known_values():
    assert holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]
    assert holm([0.5]) == [0.5]


def test_identical_systems_not_significant(toy_scores):
    a = toy_scores["careful"]
    d, p = approx_randomisation(a, a, "type_only", shuffles=500, seed=1)
    assert d == 0.0 and p == 1.0


def test_large_difference_significant(toy_scores):
    d, p = approx_randomisation(toy_scores["careful"], toy_scores["cautious"], "type_only", shuffles=2000, seed=1)
    assert d > 0.4 and p < 0.01


def test_bootstrap_contains_point(toy_scores):
    sc = toy_scores["careful"]
    ci = bootstrap_ci(sc, measures=["overall", "success"], resamples=500, seed=1)
    for m in ("overall", "success"):
        assert ci[m][0] <= point(sc, m) <= ci[m][1]


def test_compare_family_is_holm_adjusted(toy_scores):
    comps = compare_systems(toy_scores, ["type_only"], baseline="cautious", shuffles=500, resamples=0)
    assert len(comps) == 2
    assert all(c.p_holm >= c.p for c in comps)
