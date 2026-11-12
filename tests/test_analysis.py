"""Statistics checks on made-up numbers whose answers are known."""
import pytest

from src.analysis.stats import cluster_bootstrap_ci, holm, mcnemar_exact


def test_mcnemar_exact():
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(5, 5) == 1.0
    assert mcnemar_exact(10, 0) == pytest.approx(2 * 0.5**10)  # two-sided binomial tail


def test_cluster_bootstrap_ci_contains_the_mean_and_is_deterministic():
    diffs = [-1, -1, 0, 0, 0, -1, 0, 0, -1, 0] * 10
    clusters = [f"c{i // 2}" for i in range(100)]
    low, high = cluster_bootstrap_ci(diffs, clusters)
    assert low < -0.4 < high and (low, high) == cluster_bootstrap_ci(diffs, clusters)
    assert cluster_bootstrap_ci([0] * 10, list(range(10))) == (0.0, 0.0)


def test_margin_reading_follows_the_protocol_order():
    from src.analysis.primary import reading

    assert reading(-5.0, -0.5) == "change"
    assert reading(0.2, 1.5) == "change"  # excludes 0 comes first, even inside the margin
    assert reading(-1.5, 1.8) == "no change larger than 2 pp"
    assert reading(-4.0, 1.0) == "inconclusive"


def test_holm():
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
