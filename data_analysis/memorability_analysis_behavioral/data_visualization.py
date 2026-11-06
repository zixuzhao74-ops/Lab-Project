"""Visualize recognition accuracy by quartile groups of memorability scores

Install packages once (recommended terminal command):
    pip install pandas numpy statsmodels matplotlib
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from scipy.special import expit


def visualize_accuracy_by_quartile(D: pd.DataFrame, folder: Path):
    """Recognition accuracy by quartile of old-image ResMem.
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
    """Look up a random-effect SD from pymer4's ranef_var table."""
    rv = result.ranef_var.reset_index()
    rv = rv.rename(columns={rv.columns[0]: "group"})
    row = rv[(rv["group"] == group) & (rv["Name"] == term)]
    return float(row["Std"].iloc[0]) if len(row) else 0.0


def _ranef_corr(result, group="subject"):
    """Intercept-slope correlation for a group (0 if not estimated)."""
    rc = getattr(result, "ranef_corr", None)
    if rc is None or len(rc) == 0:
        return 0.0
    rc = rc.reset_index()
    rc = rc.rename(columns={rc.columns[0]: "group"})
    row = rc[rc["group"] == group]
    return float(row["Corr"].iloc[0]) if len(row) else 0.0


def _fixef_draws(result, n_samples, rng):
    """Draw fixed effects jointly from N(estimate, vcov); fall back to independent SEs."""
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
                     n_samples=1200, n_random=40, seed=42):
    """Plot marginal GLMM predictions with fixed-effect and random-effect uncertainty."""

    rng = np.random.default_rng(seed)

    # ResMem grid on the original scale, converted to model units
    x = np.linspace(D["oldResMem"].min(), D["oldResMem"].max(), 160)
    x_c = (x - D["oldResMem"].mean()) / 0.1

    # Fixed effects: sampled jointly from their sampling distribution
    fe = _fixef_draws(result, n_samples, rng)
    b0 = fe["(Intercept)"].to_numpy()
    b1 = fe["oldResMem_c"].to_numpy()
    # foil FalseResMem, category, block held at their centered value (0)
    eta_fixed = b0[:, None] + b1[:, None] * x_c[None, :]

    # Random-effect SDs (lme4 gives point estimates only)
    sd_subj = _ranef_sd(result, "subject", "(Intercept)")
    sd_slope = _ranef_sd(result, "subject", "oldResMem_c")
    sd_old = _ranef_sd(result, "OLDITEM")
    sd_new = _ranef_sd(result, "NEWITEM")
    rho = _ranef_corr(result, "subject")

    # Subject intercept + slope, drawn jointly (keeps their correlation)
    cov = np.array([[sd_subj**2,              rho * sd_subj * sd_slope],
                    [rho * sd_subj * sd_slope, sd_slope**2]])
    z = rng.multivariate_normal([0, 0], cov, size=(n_samples, n_random))
    subj, slope = z[..., 0:1], z[..., 1:2]

    shape = (n_samples, n_random, 1)
    old_img = rng.normal(size=shape) * sd_old
    new_img = rng.normal(size=shape) * sd_new

    # Linear predictor: fixed + random intercepts + random slope
    eta = (eta_fixed[:, None, :] + subj + old_img + new_img
           + slope * x_c[None, None, :])

    # Population-averaged (marginal) probability for each fixed-effect draw
    marginal_samples = expit(eta).mean(axis=1)
    predicted = marginal_samples.mean(axis=0)
    lower, upper = np.percentile(marginal_samples, [2.5, 97.5], axis=0)

    # Interval for a new subject x image combination
    individual = expit(eta[:, 0, :])
    pred_low, pred_high = np.percentile(individual, [2.5, 97.5], axis=0)

    # Plot
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.fill_between(x, pred_low, pred_high, color="#2457A7",
                    alpha=0.10, label="95% predictive interval")
    ax.fill_between(x, lower, upper, color="#2457A7",
                    alpha=0.25, label="Approx. 95% confidence interval")
    ax.plot(x, predicted, color="#2457A7", lw=2.5,
            label="Population-averaged prediction")

    beta = result.coefs.loc["oldResMem_c", "Estimate"]
    ax.set(xlabel="Old-image ResMem",
           ylabel="Predicted recognition accuracy",
           title="ResMem and Recognition Performance",
           ylim=(0, 1))
    ax.text(0.04, 0.05, f"β = {beta:.3f} (per 0.1 ResMem), OR = {np.exp(beta):.2f}",
            transform=ax.transAxes, fontsize=11)

    ax.grid(alpha=0.2)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()

    return fig, ax


def save_analysis_outputs(D: pd.DataFrame, quartile_summary: pd.DataFrame, folder: Path):
    """10. Save the cleaned, matched trial-level dataset.
    """
    D.to_csv(folder / "recognition_resmem_merged.csv", index=False)
    quartile_summary.to_csv(folder / "recognition_resmem_quartiles.csv", index=False)
    print("\nSaved recognition_resmem_merged.csv")
    print("Saved recognition_resmem_quartiles.csv")
    print("Saved recognition_resmem_quartiles.png")