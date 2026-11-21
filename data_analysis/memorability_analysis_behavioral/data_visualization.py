"""Visualize recognition accuracy by quartile groups of memorability scores

Install packages once (recommended terminal command):
    pip install pandas numpy statsmodels matplotlib
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from scipy.special import expit
from statsmodels.stats.proportion import proportion_confint

# ResMem units per model unit: oldResMem_c = (oldResMem - mean) / 0.1 (see GLLM.py)
RESMEM_SCALE = 0.1


def visualize_accuracy_by_quartile(D: pd.DataFrame, folder: Path):
    """
    Recognition accuracy by quartile of old-image ResMem.
    """
    D["quartile"] = pd.qcut(D["oldResMem"], q=4, labels=[1, 2, 3, 4])
    quartile_summary = (
        D.groupby("quartile", observed=True)
        .agg(TrialCount=("correct", "size"),
             AccuracyPercent=("correct", lambda v: 100 * v.mean()))
        .reset_index()
        .rename(columns={"quartile": "ResMemQuartile"})
    )

    print("\nACCURACY BY OLD-IMAGE RESMEM QUARTILE")
    print(quartile_summary.to_string(index=False, float_format="%.2f"))

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar([1, 2, 3, 4], quartile_summary["AccuracyPercent"])
    ax.set_xticks([1, 2, 3, 4], ["Q1: Lowest", "Q2", "Q3", "Q4: Highest"])
    ax.set_ylabel("Recognition accuracy (%)")
    ax.set_xlabel("Old-image ResMem quartile")
    ax.set_title("Recognition accuracy by model-predicted memorability")
    ax.set_ylim(0, 100)
    fig.tight_layout()
    fig.savefig(folder / "recognition_resmem_quartiles.png", dpi=200)
    plt.show()

    return quartile_summary


def _ranef_sd(result, group, term="(Intercept)"):
    """
    Look up a random-effect SD from pymer4's ranef_var table.
    """
    rv = result.ranef_var.reset_index()
    rv = rv.rename(columns={rv.columns[0]: "group"})
    row = rv[(rv["group"] == group) & (rv["Name"] == term)]
    return float(row["Std"].iloc[0]) if len(row) else 0.0


def _ranef_corr(result, group="subject"):
    """
    Intercept-slope correlation for a group (0 if not estimated).
    """
    rc = getattr(result, "ranef_corr", None)
    if rc is None or len(rc) == 0:
        return 0.0
    rc = rc.reset_index()
    rc = rc.rename(columns={rc.columns[0]: "group"})
    row = rc[rc["group"] == group]
    return float(row["Corr"].iloc[0]) if len(row) else 0.0


def _fixef_draws(result, n_samples, rng):
    """
    Draw fixed effects jointly from N(estimate, vcov); fall back to 
    independent SEs.
    """
    est = result.coefs["Estimate"]
    try:
        from rpy2.robjects import r
        V = np.array(r("function(m) as.matrix(vcov(m))")(result.model_obj))
        draws = rng.multivariate_normal(est.to_numpy(), V, n_samples)
    except Exception:
        se = result.coefs["SE"].to_numpy()
        draws = rng.normal(est.to_numpy(), se, (n_samples, len(est)))
    return pd.DataFrame(draws, columns=est.index)


def plot_resmem_glmm(result, D, filename="ResMem_GLMM.png",
                     n_samples=1000, n_random=1000, seed=42,
                     n_bins=8, show_predictive=False, ylim=(0, 1)):
    """Plot marginal (population-averaged) GLMM predictions of recognition 
    accuracy.

    Shows the fitted curve with an approximate 95% confidence band, the observed
    accuracy in equal-count ResMem bins (95% Wilson intervals), the ResMem
    raw correct (top) and incorrect (bottom) trials as a rug, and the ResMem effect
    (OR, 95% CI, p). The wide 95% predictive interval (a new subject x image
    pair) is optional (show_predictive=True).
    """

    rng = np.random.default_rng(seed)

    # ResMem grid on the original scale, converted to model units
    x = np.linspace(D["oldResMem"].min(), D["oldResMem"].max(), 160)
    x_c = (x - D["oldResMem"].mean()) / RESMEM_SCALE

    # Fixed effects: sampled jointly from their sampling distribution
    fe = _fixef_draws(result, n_samples, rng)
    b0 = fe["(Intercept)"].to_numpy()
    b1 = fe["oldResMem_c"].to_numpy()
    # foil FalseResMem, category, block held at their centered value (0)
    eta_fixed = b0[:, None] + b1[:, None] * x_c[None, :] # (n_samples, 160)

    # Random-effect SDs (lme4 gives point estimates only)
    sd_subj = _ranef_sd(result, "subject", "(Intercept)")
    sd_slope = _ranef_sd(result, "subject", "oldResMem_c")
    sd_old = _ranef_sd(result, "OLDITEM")
    sd_new = _ranef_sd(result, "NEWITEM")
    rho = _ranef_corr(result, "subject")

    # One shared set of random-effect draws (subject intercept + slope drawn
    # jointly, plus old/new image intercepts). Reusing it for every
    # fixed-effect draw keeps the band smooth: it varies only with the
    # fixed-effect uncertainty, not with Monte Carlo noise.
    cov = np.array([[sd_subj**2, rho * sd_subj * sd_slope],
                    [rho * sd_subj * sd_slope, sd_slope**2]])
    z = rng.multivariate_normal([0, 0], cov, size=n_random)
    subj, slope = z[:, 0:1], z[:, 1:2]
    old_img = rng.normal(size=(n_random, 1)) * sd_old
    new_img = rng.normal(size=(n_random, 1)) * sd_new
    R = subj + old_img + new_img + slope * x_c[None, :] # (n_random, 160)

    # Population-averaged (marginal) probability for each fixed-effect draw
    marginal_samples = np.empty((n_samples, x.size))
    for s in range(n_samples):
        marginal_samples[s] = expit(eta_fixed[s][None, :] + R).mean(axis=0)
    predicted = marginal_samples.mean(axis=0)
    lower, upper = np.percentile(marginal_samples, [2.5, 97.5], axis=0)

    # Interval for a new subject x image combination
    individual = expit(eta_fixed + R[np.arange(n_samples) % n_random])
    pred_low, pred_high = np.percentile(individual, [2.5, 97.5], axis=0)

    # Observed accuracy in equal-count ResMem bins (trials pooled across subjects)
    bins = pd.qcut(D["oldResMem"], q=n_bins, duplicates="drop")
    obs = D.groupby(bins, observed=True).agg(
        x=("oldResMem", "mean"), k=("correct", "sum"), n=("correct", "size"))
    obs_p = (obs["k"] / obs["n"]).to_numpy()
    obs_lo, obs_hi = proportion_confint(obs["k"], obs["n"],
                                        alpha=0.05, method="wilson")
    obs_err = [obs_p - np.asarray(obs_lo), np.asarray(obs_hi) - obs_p]

    # Effect of ResMem (log-odds scale -> odds ratio per 0.1 ResMem)
    est = result.coefs.loc["oldResMem_c", "Estimate"]
    se = result.coefs.loc["oldResMem_c", "SE"]
    p_val = result.coefs.loc["oldResMem_c", "P-val"]
    p_txt = "p < .001" if p_val < 0.001 else f"p = {p_val:.3f}"
    effect_txt = (f"β = {est:.3f}, OR = {np.exp(est):.2f} per 0.1 ResMem\n"
                  f"95% CI [{np.exp(est - 1.96 * se):.2f}, "
                  f"{np.exp(est + 1.96 * se):.2f}], {p_txt}")

    # Plot
    fig, ax = plt.subplots(figsize=(8, 5.5))
    if show_predictive:
        ax.fill_between(x, pred_low, pred_high, color="#2457A7",
                        alpha=0.10, label="95% predictive interval")
    ax.fill_between(x, lower, upper, color="#2457A7",
                    alpha=0.25, label="Approx. 95% confidence interval")
    ax.plot(x, predicted, color="#2457A7", lw=2.5,
            label="Population-averaged prediction")
    ax.errorbar(obs["x"], obs_p, yerr=obs_err, fmt="o", color="black",
                capsize=3, ms=5, label=f"Observed ({len(obs)} bins, 95% CI)")
    # Two-sided rug of the raw binary outcomes: ticks at the top = correct
    # trials, ticks at the bottom = incorrect trials, placed at their ResMem
    h = 0.03 * (ylim[1] - ylim[0])
    ax.vlines(D.loc[D["correct"] == 1, "oldResMem"], ylim[1] - h, ylim[1],
              color="gray", alpha=0.25, lw=0.8,
              label="Correct trials (top ticks)")
    ax.vlines(D.loc[D["correct"] == 0, "oldResMem"], ylim[0], ylim[0] + h,
              color="gray", alpha=0.25, lw=0.8,
              label="Incorrect trials (bottom ticks)")

    ax.set(xlabel="Old-image ResMem",
           ylabel="Probability of correct recognition",
           title="ResMem and Recognition Performance",
           ylim=ylim)
    ax.text(0.04, 0.12, effect_txt, transform=ax.transAxes, fontsize=11)

    ax.grid(alpha=0.2)
    ax.legend(frameon=False, loc="lower right", fontsize=9)
    fig.tight_layout()
    fig.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()

    return fig, ax


def save_analysis_outputs(D: pd.DataFrame, quartile_summary: pd.DataFrame, folder: Path):
    """
    10. Save the cleaned, matched trial-level dataset.
    """
    D.to_csv(folder / "recognition_resmem_merged.csv", index=False)
    quartile_summary.to_csv(folder / "recognition_resmem_quartiles.csv", index=False)
    print("\nSaved recognition_resmem_merged.csv")
    print("Saved recognition_resmem_quartiles.csv")
    print("Saved recognition_resmem_quartiles.png")
