"""
Consolidated statistical testing utilities — previously copy-pasted
across run_significance_tests.py, verify_external_claims.py, and
run_tbm_sweep.py independently. Single source of truth now; every future
script imports from here instead of reimplementing.

Every function below is verified against hand-computable known values in
verify_engine.py before being trusted for any real finding.

=== REVISION 1 (this chat) — wilson_ci() ignored its own confidence
parameter ===
Found via a VS Code Copilot shared-engine audit: wilson_ci() accepted a
confidence argument but always used the hardcoded 95% critical value
1.959963985 regardless of what was passed — wilson_ci(k, n,
confidence=0.90) or 0.99 silently returned a 95% interval instead. Fixed
by deriving z from the actual confidence level via
statistics.NormalDist().inv_cdf() (stdlib, no new dependency). Every
existing call site using the 0.95 default is unaffected — the derived z
for confidence=0.95 matches the old hardcoded constant.
"""
import math
import statistics

from scipy import stats


def log_pmf(n: int, k: int, p: float) -> float:
    """log of the binomial probability mass P(X=k) for X~Binomial(n,p).
    Computed via lgamma to stay numerically stable for large n."""
    if k < 0 or k > n:
        return float('-inf')
    log_comb = math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
    return log_comb + k * math.log(p) + (n - k) * math.log(1 - p)


def two_sided_exact_pvalue(k: int, n: int, p: float) -> float:
    """Exact two-sided binomial test p-value: sums P(X=i) for every i
    whose probability is <= P(X=k)."""
    if n == 0:
        return 1.0
    log_pk = log_pmf(n, k, p)
    total = 0.0
    for i in range(n + 1):
        if log_pmf(n, i, p) <= log_pk + 1e-9:
            total += math.exp(log_pmf(n, i, p))
    return min(total, 1.0)


def wilson_ci(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Wilson score confidence interval on a true proportion.

    REVISION 1 fix (see module docstring): z is now derived from the
    actual `confidence` argument via the inverse normal CDF, instead of a
    hardcoded 95% constant that ignored whatever confidence was passed."""
    if n == 0:
        return (0.0, 0.0)
    if not (0.0 < confidence < 1.0):
        raise ValueError(f"confidence must be in (0, 1), got {confidence}")
    z = statistics.NormalDist().inv_cdf(1.0 - (1.0 - confidence) / 2.0)
    phat = k / n
    denom = 1 + z**2 / n
    center = (phat + z**2 / (2 * n)) / denom
    margin = (z * math.sqrt(phat * (1 - phat) / n + z**2 / (4 * n**2))) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def _two_sided_t_pvalue(t_stat: float, df: float) -> float:
    """Two-sided p-value from Student's t with `df` degrees of freedom.

    === CORRECTED 2026-08 (audit finding H1) ===
    Both t-tests below previously computed the t-statistic correctly and then
    converted it with math.erf — the STANDARD NORMAL CDF. For a t-statistic
    the correct reference is Student's t, and the normal approximation always
    returns a SMALLER p-value, i.e. it systematically OVERSTATES significance.
    In a project whose entire acceptance bar is p<0.01 that error ran in the
    worst possible direction.

    WORKED EXAMPLE, and a caution about reading it too quickly. The
    fixed-%-OTM no-stop cell (n=137) was reported as p=0.0094 and treated as
    the best result this project had produced. Three states, all measured:

        wrong lot table + normal approx (as published) : p=0.0094
        wrong lot table + Student's t                  : p=0.0105
        corrected lot table + Student's t (now)        : p=0.0083

    So this fix ALONE would have pushed that cell over the bar, but the
    lot-size correction landed at the same time (audit finding C1), moved the
    underlying P&L, and raised the t-statistic enough to more than offset it.
    The cell now reads MORE significant, not less. An early draft of this
    docstring asserted it "never cleared the bar at all" — that was true only
    of the middle row, and is corrected here rather than left standing.

    None of that changes the verdict: the cell was the best of 10 swept
    configurations, so Bonferroni gives 0.083, and the full-history result
    (391 trades, p=0.1387) supersedes it outright.

    The error scales inversely with sample size, so small sweeps were worst
    affected — at n=5 the reported p was understated by 6.2x, at n=30 by 1.5x.
    Any pre-2026-08 result near the bar with small n should be re-checked.
    """
    if df <= 0:
        return 1.0
    return float(2.0 * stats.t.sf(abs(t_stat), df))


def welch_t_test(sample_a: list[float], sample_b: list[float]) -> tuple[float, float]:
    """Welch's t-test (unequal variance) for whether two sample means differ.
    Returns (t_stat, two_sided_p_value).

    Degrees of freedom use the Welch-Satterthwaite equation, which the old
    normal-approximation version did not compute at all."""
    n_a, n_b = len(sample_a), len(sample_b)
    if n_a < 2 or n_b < 2:
        return (0.0, 1.0)
    mean_a, mean_b = sum(sample_a) / n_a, sum(sample_b) / n_b
    var_a = sum((x - mean_a) ** 2 for x in sample_a) / (n_a - 1)
    var_b = sum((x - mean_b) ** 2 for x in sample_b) / (n_b - 1)
    se_sq = var_a / n_a + var_b / n_b
    if se_sq <= 0:
        return (0.0, 1.0)
    t_stat = (mean_a - mean_b) / math.sqrt(se_sq)
    # Welch-Satterthwaite: the effective df of a difference of two means whose
    # variances are not assumed equal.
    denom = (var_a / n_a) ** 2 / (n_a - 1) + (var_b / n_b) ** 2 / (n_b - 1)
    df = se_sq ** 2 / denom if denom > 0 else (n_a + n_b - 2)
    return (t_stat, _two_sided_t_pvalue(t_stat, df))


def one_sample_t_test(sample: list[float]) -> tuple[float, float]:
    """One-sample t-test: is the sample mean significantly different from 0.
    Returns (t_stat, two_sided_p_value) with df = n - 1."""
    n = len(sample)
    if n < 2:
        return (0.0, 1.0)
    mean = sum(sample) / n
    var = sum((x - mean) ** 2 for x in sample) / (n - 1)
    se = math.sqrt(var / n)
    if se == 0:
        return (0.0, 1.0)
    t_stat = mean / se
    return (t_stat, _two_sided_t_pvalue(t_stat, n - 1))


def two_proportion_z_test(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float]:
    """Two-proportion z-test: are two observed hit rates (k1/n1 vs k2/n2)
    significantly different from each other? Uses pooled proportion under
    the null hypothesis they're equal. Returns (z_stat, two_sided_p)."""
    if n1 == 0 or n2 == 0:
        return (0.0, 1.0)
    p1, p2 = k1 / n1, k2 / n2
    p_pool = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1.0 / n1 + 1.0 / n2))
    if se == 0:
        return (0.0, 1.0)
    z = (p1 - p2) / se
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return (z, p_value)