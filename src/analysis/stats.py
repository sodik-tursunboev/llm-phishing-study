"""The study's three statistical tools, as small functions with tests (tests/test_analysis.py)."""
import numpy as np
from scipy.stats import binomtest

SEED, RESAMPLES = 2026, 10_000


def mcnemar_exact(lost, gained):
    """Exact McNemar test: under "no change", each discordant pair is lost or gained with p = 1/2."""
    n = lost + gained
    return 1.0 if n == 0 else binomtest(lost, n, 0.5).pvalue


def cluster_bootstrap_ci(diffs, clusters, seed=SEED, resamples=RESAMPLES):
    """95% percentile CI of the mean paired difference, resampling whole template clusters.

    Messages from one campaign template are not independent, so whole clusters are drawn with
    replacement; each resample's mean is its total difference over its total message count.
    """
    diffs, clusters = np.asarray(diffs, float), np.asarray(clusters)
    ids, index = np.unique(clusters, return_inverse=True)
    sums, counts = np.bincount(index, weights=diffs), np.bincount(index)
    draw = np.random.default_rng(seed).integers(0, len(ids), size=(resamples, len(ids)))
    means = sums[draw].sum(axis=1) / counts[draw].sum(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def holm(pvalues):
    """Holm-adjusted p-values (same order as given): controls the chance of any false positive."""
    order = np.argsort(pvalues)
    adjusted, running = np.empty(len(pvalues)), 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(pvalues) - rank) * pvalues[i])
        adjusted[i] = min(1.0, running)
    return adjusted.tolist()
