"""Estimate the number of participants needed to detect an old-image ResMem
effect on the r-CDA (or FN400), using the trial-level noise, trial counts and
ResMem values observed in the pilot participants

The effect size (smallest effect of interest) and the between-participant SD
of the ResMem slope cannot be estimated from a few participants; they are
assumptions and should be reported as such.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

RESMEM_SCALE = 0.1      # model units: per 0.1 ResMem (as in the neural LMMs)


def residual_sd(model):
    """Read the residual (trial-level) SD in µV from a fitted pymer4 Lmer model.
    """
    rv = model.ranef_var.reset_index()
    rv = rv.rename(columns={rv.columns[0]: "group"})
    row = rv[rv["group"] == "Residual"]
    return float(row["Std"].iloc[0])


def trials_per_participant(D: pd.DataFrame):
    """Average number of clean, correct trials per participant.
    """
    return int(round(D.groupby("subject").size().mean()))


def analytic_sample_size(sigma, effect, n_trials, tau_slope=0.05, x_sd=1.0,
                         alpha=0.05, power=0.80):
    """Participants needed for the ResMem slope (normal approximation).

    The SE of the average slope is sqrt((tau_slope^2 + sigma^2 / (n_trials * x_sd^2)) / N),
    where x_sd is the SD of ResMem within category in model units (about 1 = 0.1 ResMem).
    """
    z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    v = tau_slope ** 2 + sigma ** 2 / (n_trials * x_sd ** 2)
    return int(np.ceil(z ** 2 * v / effect ** 2)) + 2     # +2: t instead of normal


def simulate_power(D: pd.DataFrame, sigma, effect, n_list=(20, 30, 40, 50, 60, 80),
                   n_trials=None, tau_slope=0.05, item_sd=0.0, n_sims=1000,
                   alpha=0.05, seed=1):
    """Simulated power for the old-image ResMem slope (µV per 0.1 ResMem).

    Each simulated participant sees n_trials old images drawn from the observed
    images (ResMem centered within category, equivalent to the category
    covariate). Trial r-CDA = participant slope x ResMem + image effect + noise.
    Each participant's slope is fitted, and the average slope is tested against 0
    (a fast two-stage stand-in for the mixed model).
    """
    rng = np.random.default_rng(seed)
    n_trials = n_trials or trials_per_participant(D)

    pool = (D.drop_duplicates("old_img")[["old_img", "old_ResMem", "old_scene"]]
            .reset_index(drop=True))
    x_all = ((pool["old_ResMem"] - pool.groupby("old_scene")["old_ResMem"].transform("mean"))
             / RESMEM_SCALE).to_numpy()
    print(f"Simulating from {len(pool)} observed images, {n_trials} trials per participant, "
          f"sigma = {sigma:.2f} µV, effect = {effect} µV per 0.1 ResMem")

    rows = []
    for N in n_list:
        hits = 0
        for _ in range(n_sims):
            item = rng.normal(0, item_sd, len(pool))   # shared image effects
            slopes = np.empty(N)
            for s in range(N):
                idx = rng.choice(len(pool), n_trials, replace=len(pool) < n_trials)
                x = x_all[idx]
                b_s = effect + rng.normal(0, tau_slope)
                y = b_s * x + item[idx] + rng.normal(0, sigma, n_trials)
                slopes[s] = np.polyfit(x, y, 1)[0]
            hits += stats.ttest_1samp(slopes, 0).pvalue < alpha
        rows.append({"N": N, "power": hits / n_sims})
        print(f"N = {N}: power = {hits / n_sims:.2f}")
    return pd.DataFrame(rows)


def plot_power_curve(results: dict, filename="Power_curve.png", target=0.80):
    """Plot power against the number of participants.

    results: {label: DataFrame returned by simulate_power()}
    """
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for label, df in results.items():
        ax.plot(df["N"], df["power"], marker="o", lw=2, label=label)
    ax.axhline(target, color="gray", ls="--", lw=1, label=f"{int(target * 100)}% power")
    ax.set(xlabel="Number of participants", ylabel="Power (α = .05, two-sided)",
           title="Power to detect the old-image ResMem effect", ylim=(0, 1.02))
    ax.grid(alpha=0.2)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()
    return fig, ax
