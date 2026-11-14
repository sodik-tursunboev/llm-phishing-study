"""The study's statistical tools, as small functions with tests (tests/test_analysis.py).

The first three are pre-declared (PROTOCOL.md section 5). The paired score interval at the end was
added after the freeze as a descriptive check on the bootstrap (DEVIATIONS.md #24).
"""
import math

import numpy as np
from scipy.stats import binomtest, norm

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


Z95 = float(norm.ppf(0.975))


def wilson_ci(x, n, z=Z95):
    """95% Wilson score interval for the proportion x/n; it never collapses to a point at 0 or n."""
    p, shrink = x / n, 1 + z * z / n
    centre = (p + z * z / (2 * n)) / shrink
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / shrink
    return centre - half, centre + half


def paired_score_ci(both, lost, gained, neither, z=Z95):
    """95% interval for the change in flag rate from condition A to B on the same messages
    (Newcombe 1998, method 10: Wilson intervals of the two rates, combined using their correlation).

    both / neither: flagged under both / neither condition; lost: flagged under A only; gained: under
    B only. With zero or one discordant pair, a percentile bootstrap returns [0, 0] or a one-sided
    interval; this one still has the width that 200 messages allow. It treats messages as
    independent, ignoring template clusters, so it checks the bootstrap and does not replace it.
    """
    n = both + lost + gained + neither
    p_a, p_b = (both + lost) / n, (both + gained) / n
    low_a, high_a = wilson_ci(both + lost, n, z)
    low_b, high_b = wilson_ci(both + gained, n, z)
    cross = both * neither - lost * gained
    if cross > 0:
        cross = max(cross - n / 2, 0)  # Newcombe's continuity correction of the correlation
    margins = (both + lost) * (gained + neither) * (both + gained) * (lost + neither)
    phi = cross / math.sqrt(margins) if margins else 0.0
    change = p_b - p_a
    down = (p_b - low_b) ** 2 - 2 * phi * (p_b - low_b) * (high_a - p_a) + (high_a - p_a) ** 2
    up = (high_b - p_b) ** 2 - 2 * phi * (high_b - p_b) * (p_a - low_a) + (p_a - low_a) ** 2
    return change - math.sqrt(max(down, 0.0)), change + math.sqrt(max(up, 0.0))
