"""Reusable A/B-test functions shared by the notebook and the Streamlit app."""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

DATA = Path(__file__).resolve().parents[1] / "data" / "raw" / "hillstrom.csv"
CONTROL = "No E-Mail"
ARMS = ["Mens E-Mail", "Womens E-Mail"]


def load(path=DATA):
    return pd.read_csv(path)


# ---------- design checks ----------
def sample_ratio_check(df, col="segment"):
    """Chi-square of arm sizes against an equal split."""
    counts = df[col].value_counts()
    chi2, p = stats.chisquare(counts.values)
    return counts, chi2, p


def smd(df, covariates, arm, col="segment", control=CONTROL):
    """Standardized mean difference of each covariate, arm vs. control."""
    a, c = df[df[col] == arm], df[df[col] == control]
    out = {}
    for v in covariates:
        pooled = np.sqrt((a[v].var() + c[v].var()) / 2)
        out[v] = (a[v].mean() - c[v].mean()) / pooled
    return pd.Series(out)


# ---------- effect estimates ----------
def diff_in_means(treat, ctrl, n_boot=5000, seed=0):
    """Mean difference with Welch t p-value and a bootstrap percentile 95% CI.

    Bootstrap is used because spend is mostly zeros with a long right tail.
    """
    rng = np.random.default_rng(seed)
    t, c = np.asarray(treat, float), np.asarray(ctrl, float)
    est = t.mean() - c.mean()
    boots = np.empty(n_boot)
    for i in range(n_boot):
        boots[i] = (rng.choice(t, t.size).mean() - rng.choice(c, c.size).mean())
    lo, hi = np.percentile(boots, [2.5, 97.5])
    p = stats.ttest_ind(t, c, equal_var=False).pvalue
    return {"diff": est, "lo": lo, "hi": hi, "p": p, "boots": boots}


def diff_in_props(treat, ctrl):
    """Difference in proportions: two-sided z-test, Wald 95% CI."""
    t, c = np.asarray(treat, float), np.asarray(ctrl, float)
    pt, pc = t.mean(), c.mean()
    se = np.sqrt(pt * (1 - pt) / t.size + pc * (1 - pc) / c.size)
    pool = (t.sum() + c.sum()) / (t.size + c.size)
    se0 = np.sqrt(pool * (1 - pool) * (1 / t.size + 1 / c.size))
    z = (pt - pc) / se0
    return {"diff": pt - pc, "lo": pt - pc - 1.96 * se, "hi": pt - pc + 1.96 * se,
            "p": 2 * stats.norm.sf(abs(z))}


def holm(pvals):
    return multipletests(pvals, method="holm")[1]


def cuped(df, outcome, covariate, arm, col="segment", control=CONTROL):
    """Regression-adjusted (CUPED) difference in means using a pre-period covariate.

    theta = cov(Y, X)/var(X) is estimated on the two arms pooled; Y_adj = Y - theta (X - mean X).
    Valid because X is measured before assignment, so it cannot be affected by treatment.
    """
    d = df[df[col].isin([arm, control])]
    x, y = d[covariate].to_numpy(float), d[outcome].to_numpy(float)
    theta = np.cov(x, y)[0, 1] / x.var(ddof=1)
    y_adj = y - theta * (x - x.mean())
    is_t = (d[col] == arm).to_numpy()
    r = diff_in_means(y_adj[is_t], y_adj[~is_t], n_boot=2000)
    r["theta"] = theta
    r["var_reduction"] = 1 - y_adj.var(ddof=1) / y.var(ddof=1)
    return r


def interaction_test(df, outcome, subgroup, arm, col="segment", control=CONTROL):
    """F-test: does the arm effect differ across levels of `subgroup`?"""
    import statsmodels.formula.api as smf
    d = df[df[col].isin([arm, control])].copy()
    d["treated"] = (d[col] == arm).astype(int)
    d = d.rename(columns={outcome: "y"})
    full = smf.ols(f"y ~ treated * C({subgroup})", d).fit()
    reduced = smf.ols(f"y ~ treated + C({subgroup})", d).fit()
    f, p, _ = full.compare_f_test(reduced)
    return f, p


# ---------- business translation ----------
def incremental_profit(spend_diff, margin, cost_per_email):
    return margin * spend_diff - cost_per_email


# ---------- planning ----------
def n_per_arm(baseline, mde_abs, alpha=0.05, power=0.8):
    """Sample size per arm to detect an absolute lift in a proportion."""
    es = proportion_effectsize(baseline + mde_abs, baseline)
    return int(np.ceil(NormalIndPower().solve_power(es, alpha=alpha, power=power, ratio=1)))


def n_per_arm_mean(sd, mde_abs, alpha=0.05, power=0.8):
    """Sample size per arm to detect an absolute lift in a mean with std dev `sd`."""
    return int(np.ceil(NormalIndPower().solve_power(mde_abs / sd, alpha=alpha, power=power, ratio=1)))


def peeking_simulation(n_per_day=1000, days=14, base_rate=0.1, n_sims=2000, alpha=0.05, seed=0):
    """A/A test (no true effect) checked every day; stop at first p < alpha.

    Returns (false-positive rate if you peek daily, rate if you test once at the end).
    """
    rng = np.random.default_rng(seed)
    a = rng.binomial(n_per_day, base_rate, (n_sims, days)).cumsum(axis=1)
    b = rng.binomial(n_per_day, base_rate, (n_sims, days)).cumsum(axis=1)
    n = n_per_day * np.arange(1, days + 1)
    pool = (a + b) / (2 * n)
    se = np.sqrt(pool * (1 - pool) * 2 / n)
    z = np.abs((a - b) / n) / se
    p = 2 * stats.norm.sf(z)
    return (p < alpha).any(axis=1).mean(), (p[:, -1] < alpha).mean()
