"""Visualize the neural results: r-CDA (primary question) and FN400 (secondary
question) waveforms and the mixed-model predictions of each from ResMem

Install packages once (recommended terminal command):
    pip install pandas numpy matplotlib
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from memorability_analysis_neural.data_preprocess import (
    RCDA_CHANNELS, RCDA_WINDOW, FN400_CHANNELS, FN400_WINDOW, RESMEM_SCALE)


def _vcov(model):
    """Fixed-effect covariance matrix from lme4; fall back to independent SEs.
    """
    names = model.coefs.index
    try:
        from rpy2.robjects import r
        V = np.array(r("function(m) as.matrix(vcov(m))")(model.model_obj))
    except Exception:
        V = np.diag(model.coefs["SE"].to_numpy() ** 2)
    return pd.DataFrame(V, index=names, columns=names)


def _fixed_line(model, term, x_raw, center):
    """Model prediction and 95% CI along one ResMem predictor, with the other
    predictors at 0 (their mean, or the average over sum-coded factors).
    """
    xc = (x_raw - center) / RESMEM_SCALE
    names = ["(Intercept)", term]
    X = np.column_stack([np.ones_like(xc), xc])
    b = model.coefs.loc[names, "Estimate"].to_numpy()
    V = _vcov(model).loc[names, names].to_numpy()
    fit = X @ b
    se = np.sqrt(np.einsum("ij,jk,ik->i", X, V, X))
    return fit, fit - 1.96 * se, fit + 1.96 * se


def _predict_terms(model, names, X):
    """Model prediction and 95% CI for a design matrix X over the fixed effects
    `names` (all other predictors at 0).
    """
    b = model.coefs.loc[names, "Estimate"].to_numpy()
    V = _vcov(model).loc[names, names].to_numpy()
    fit = X @ b
    se = np.sqrt(np.einsum("ij,jk,ik->i", X, V, X))
    return fit, fit - 1.96 * se, fit + 1.96 * se


def _simple_slope(model, x_term, mod_term, value):
    """Slope of x_term at one level of a moderator (b_x + value * b_interaction),
    with a normal-approximation 95% CI.
    """
    inter = f"{x_term}:{mod_term}"
    names = [x_term, inter]
    b = model.coefs.loc[names, "Estimate"].to_numpy()
    V = _vcov(model).loc[names, names].to_numpy()
    w = np.array([1.0, value])
    slope, se = w @ b, np.sqrt(w @ V @ w)
    return slope, slope - 1.96 * se, slope + 1.96 * se


def _plot_interaction_fit(ax, model, D, x_col, x_term, mod_term, groups, dv,
                          n_bins=6):
    """Draw model lines (95% CI) and observed binned means separately for each
    level of a moderator. groups: list of (label, moderator value, color, mask).
    """
    names = ["(Intercept)", x_term, mod_term, f"{x_term}:{mod_term}"]
    center = D[x_col].mean()
    x = np.linspace(D[x_col].min(), D[x_col].max(), 100)
    xc = (x - center) / RESMEM_SCALE
    for label, value, color, mask in groups:
        v = np.full_like(xc, value)
        fit, lo, hi = _predict_terms(model, names, np.column_stack([np.ones_like(xc), xc, v, xc * v]))
        ax.fill_between(x, lo, hi, color=color, alpha=0.2)
        ax.plot(x, fit, color=color, lw=2.5, label=f"{label}: model prediction (95% CI)")
        sub = D.loc[mask]
        bins = pd.qcut(sub[x_col], n_bins, duplicates="drop")
        obs = sub.groupby(bins, observed=True).agg(
            x=(x_col, "mean"), y=(dv, "mean"), se=(dv, "sem"))
        ax.errorbar(obs["x"], obs["y"], yerr=obs["se"], fmt="o", color=color, ms=4,
                    capsize=3, alpha=0.8, label=f"{label}: observed bin means (± SEM)")


def _effect_text(model, term, label):
    """Text for one ResMem effect: b, 95% CI and p.
    """
    c = model.coefs.loc[term]
    p = c["P-val"]
    p_txt = "p < .001" if p < 0.001 else f"p = {p:.3f}"
    return (f"{label}: b = {c['Estimate']:.3f} µV per 0.1 ResMem, "
            f"95% CI [{c['2.5_ci']:.3f}, {c['97.5_ci']:.3f}], {p_txt}")


def _subject_average_waves(D, wave_col, group_col):
    """Average waveforms within subject x group, then across subjects
    (mean and SEM across subjects).
    """
    per_subj = [(g, np.mean(np.stack(x[wave_col].to_list()), axis=0))
                for (s, g), x in D.groupby(["subject", group_col], observed=True)]
    out = {}
    for g in dict.fromkeys(g for g, _ in per_subj):
        W = np.stack([w for gg, w in per_subj if gg == g])
        sem = W.std(axis=0, ddof=1) / np.sqrt(len(W)) if len(W) > 1 else np.zeros(W.shape[1])
        out[g] = (W.mean(axis=0), sem, len(W))
    return out


def _plot_waves(ax, times, waves, window, colors, ylabel, title):
    """Draw grand-average waveforms (± SEM) with the analysis window shaded.
    """
    ms = times * 1000
    ax.axvspan(window[0] * 1000, window[1] * 1000, color="0.9", zorder=0,
               label="Analysis window")
    ax.axhline(0, color="k", lw=0.8)
    ax.axvline(0, color="k", lw=0.8, ls=":")
    for g, (mean, sem, n) in waves.items():
        ax.plot(ms, mean, color=colors[g], lw=2, label=f"{g} (n = {n} participants)")
        ax.fill_between(ms, mean - sem, mean + sem, color=colors[g], alpha=0.2)
    ax.invert_yaxis()   # ERP convention: negative up
    ax.set(xlabel="Time from image onset (ms)", ylabel=ylabel, title=title)
    ax.legend(frameon=False, fontsize=8)
    ax.grid(alpha=0.2)


def _plot_fit(ax, model, D, x_col, term, dv, color, label, n_bins=8):
    """Draw the model prediction (95% CI) and observed means in equal-count
    ResMem bins (± SEM).
    """
    x = np.linspace(D[x_col].min(), D[x_col].max(), 100)
    fit, lo, hi = _fixed_line(model, term, x, D[x_col].mean())
    ax.fill_between(x, lo, hi, color=color, alpha=0.2)
    ax.plot(x, fit, color=color, lw=2.5, label=f"{label}: model prediction (95% CI)")
    bins = pd.qcut(D[x_col], n_bins, duplicates="drop")
    obs = D.groupby(bins, observed=True).agg(
        x=(x_col, "mean"), y=(dv, "mean"), se=(dv, "sem"))
    ax.errorbar(obs["x"], obs["y"], yerr=obs["se"], fmt="o", color=color, ms=4,
                capsize=3, alpha=0.8, label=f"{label}: observed bin means (± SEM)")


def plot_primary_rcda(models, cat, times, filename="Fig1_primary_rCDA.png"):
    """Figure for the primary question.

    A: grand-average r-CDA during categorization, by old-image role.
    B: model-predicted r-CDA across old-image ResMem, with the ResMem effect.
    C: model-predicted r-CDA across the old-minus-new ResMem difference (drawn
       when the "relative_rcda" model was fitted). The r-CDA is a difference between
       the two images, so a positive slope means a more memorable old image (or a
       less memorable new image) pulls lateralization toward the old image.
    """
    has_rel = "relative_rcda" in models
    fig, axes = plt.subplots(1, 3 if has_rel else 2,
                             figsize=(20 if has_rel else 14, 5.5))
    a, b = axes[0], axes[1]

    D = cat.assign(role=np.where(cat["old_is_target"], "Old image = target",
                                 "Old image = distractor"))
    _plot_waves(a, times, _subject_average_waves(D, "rcda_wave", "role"), RCDA_WINDOW,
                {"Old image = target": "#C0392B", "Old image = distractor": "#2457A7"},
                f"r-CDA, {RCDA_CHANNELS[0]}/{RCDA_CHANNELS[1]} "
                "(µV; contra − ipsi to old image)",
                "A. r-CDA during categorization")

    m = models["primary_rcda"]
    _plot_fit(b, m, cat, "old_ResMem", "OldResMem", "rcda", "#2457A7", "Old image")
    b.axhline(0, color="k", lw=0.8)
    b.invert_yaxis()
    win = f"{int(RCDA_WINDOW[0] * 1000)}–{int(RCDA_WINDOW[1] * 1000)} ms"
    b.set(xlabel="Old-image ResMem", ylabel=f"Mean r-CDA, {win} (µV; negative up)",
          title="B. Old-image memorability and r-CDA")
    b.text(0.02, 0.03, _effect_text(m, "OldResMem", "Old ResMem"),
           transform=b.transAxes, fontsize=9)
    b.legend(frameon=False, fontsize=8, loc="upper right")
    b.grid(alpha=0.2)

    if has_rel:
        c = axes[2]
        mrel = models["relative_rcda"]
        Dr = cat.assign(resmem_diff=cat["old_ResMem"] - cat["new_ResMem"])
        _plot_fit(c, mrel, Dr, "resmem_diff", "DiffResMem", "rcda", "#C0392B",
                  "Old − new")
        c.axhline(0, color="k", lw=0.8)
        c.invert_yaxis()
        c.set(xlabel="Old-image ResMem − new-image ResMem",
              ylabel=f"Mean r-CDA, {win} (µV; negative up)",
              title="C. Relative memorability (old − new) and r-CDA")
        c.text(0.02, 0.03, "\n".join([
            _effect_text(mrel, "DiffResMem", "Old − new ResMem"),
            _effect_text(mrel, "SumResMem", "Sum (asymmetry)")]),
            transform=c.transAxes, fontsize=8.5)
        c.legend(frameon=False, fontsize=8, loc="upper right")
        c.grid(alpha=0.2)

    fig.tight_layout()
    fig.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()
    return fig, tuple(axes)


def plot_role_interaction(models, cat, filename="Fig3_role_interaction.png"):
    """Exploratory figure for the old − new ResMem x Role model.

    Model-predicted r-CDA across the old-minus-new ResMem difference, separately
    for trials where the old image is the categorization target and where it is the
    distractor, with the simple slope for each role. Because the r-CDA is signed to
    the old image, the two roles have opposite expected mean r-CDA. If memorability
    captures attention regardless of the goal, the slopes have the same sign.
    """
    m = models["role_interaction_rcda"]
    D = cat.assign(resmem_diff=cat["old_ResMem"] - cat["new_ResMem"])
    groups = [("Old image = target", 0.5, "#C0392B", D["Role"] > 0),
              ("Old image = distractor", -0.5, "#2457A7", D["Role"] < 0)]

    fig, ax = plt.subplots(figsize=(8, 5.5))
    _plot_interaction_fit(ax, m, D, "resmem_diff", "DiffResMem", "Role", groups, "rcda")
    ax.axhline(0, color="k", lw=0.8)
    ax.invert_yaxis()
    win = f"{int(RCDA_WINDOW[0] * 1000)}–{int(RCDA_WINDOW[1] * 1000)} ms"
    ax.set(xlabel="Old-image ResMem − new-image ResMem",
           ylabel=f"Mean r-CDA, {win} (µV; negative up)",
           title="Old − new ResMem and r-CDA, by old-image role")
    lines = []
    for label, value, _, _ in groups:
        s, lo, hi = _simple_slope(m, "DiffResMem", "Role", value)
        lines.append(f"{label}: slope = {s:.3f} µV per 0.1, 95% CI [{lo:.3f}, {hi:.3f}]")
    lines.append(_effect_text(m, "DiffResMem:Role", "Interaction"))
    ax.text(0.02, 0.03, "\n".join(lines), transform=ax.transAxes, fontsize=8.5)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.grid(alpha=0.2)

    fig.tight_layout()
    fig.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()
    return fig, ax


def plot_recognition_errors(models, rec, times, filename="Fig4_recognition_errors.png"):
    """Exploratory figure for recognition errors (chosen-image-signed r-CDA).

    A: grand-average r-CDA signed to the chosen image, for correct vs error trials.
       Under a familiarity account, errors look confident (a large r-CDA toward the
       chosen foil); under a tag account most errors are guesses (a small r-CDA).
    B: model-predicted chosen-signed r-CDA across old-image ResMem, for correct and
       error trials.
    """
    fig, (a, b) = plt.subplots(1, 2, figsize=(14, 5.5))

    sign = np.where(rec["correct"], 1.0, -1.0)
    D = rec.assign(
        outcome=np.where(rec["correct"], "Correct (chose old)", "Error (chose new)"),
        rcda_chosen_wave=[w * s for w, s in zip(rec["rcda_wave"], sign)])
    _plot_waves(a, times, _subject_average_waves(D, "rcda_chosen_wave", "outcome"),
                RCDA_WINDOW,
                {"Correct (chose old)": "#C0392B", "Error (chose new)": "#2457A7"},
                f"r-CDA, {RCDA_CHANNELS[0]}/{RCDA_CHANNELS[1]} "
                "(µV; contra − ipsi to chosen image)",
                "A. Chosen-locked r-CDA during recognition")

    m = models["recognition_chosen_rcda"]
    groups = [("Correct", 0.5, "#C0392B", D["correct"]),
              ("Error", -0.5, "#2457A7", ~D["correct"])]
    _plot_interaction_fit(b, m, D, "old_ResMem", "OldResMem", "Correct", groups,
                          "rcda_chosen")
    b.axhline(0, color="k", lw=0.8)
    b.invert_yaxis()
    win = f"{int(RCDA_WINDOW[0] * 1000)}–{int(RCDA_WINDOW[1] * 1000)} ms"
    b.set(xlabel="Old-image ResMem",
          ylabel=f"Mean chosen-signed r-CDA, {win} (µV; negative up)",
          title="B. Old-image memorability and r-CDA, correct vs error")
    lines = []
    for label, value, _, _ in groups:
        s, lo, hi = _simple_slope(m, "OldResMem", "Correct", value)
        lines.append(f"{label}: slope = {s:.3f} µV per 0.1, 95% CI [{lo:.3f}, {hi:.3f}]")
    lines.append(_effect_text(m, "OldResMem:Correct", "Interaction"))
    b.text(0.02, 0.03, "\n".join(lines), transform=b.transAxes, fontsize=8.5)
    b.legend(frameon=False, fontsize=8, loc="upper right")
    b.grid(alpha=0.2)

    fig.tight_layout()
    fig.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()
    return fig, (a, b)


def plot_secondary_fn400(models, cat, times, filename="Fig2_secondary_FN400.png"):
    """Figure for the secondary question.

    A: grand-average FN400 for low vs high old-image ResMem (descriptive tertiles).
    B: model-predicted FN400 across old- and new-image ResMem, with both slopes
       and the old - new contrast.
    """
    fig, (a, b) = plt.subplots(1, 2, figsize=(14, 5.5))

    D = cat.copy()
    D["ResMem_group"] = pd.qcut(
        D["old_ResMem"], 3,
        labels=["Low old-image ResMem", "Middle", "High old-image ResMem"]).astype(str)
    D = D.loc[D["ResMem_group"] != "Middle"]
    _plot_waves(a, times, _subject_average_waves(D, "fn400_wave", "ResMem_group"),
                FN400_WINDOW,
                {"Low old-image ResMem": "#7F8C8D", "High old-image ResMem": "#8E44AD"},
                f"Frontal ERP, {'/'.join(FN400_CHANNELS)} (µV)",
                "A. FN400 by old-image ResMem (descriptive tertiles)")

    m = models["secondary_fn400_slopes"]
    _plot_fit(b, m, cat, "old_ResMem", "OldResMem", "fn400", "#8E44AD", "Old image")
    _plot_fit(b, m, cat, "new_ResMem", "NewResMem", "fn400", "#E67E22", "New image")
    b.invert_yaxis()
    win = f"{int(FN400_WINDOW[0] * 1000)}–{int(FN400_WINDOW[1] * 1000)} ms"
    b.set(xlabel="Image ResMem", ylabel=f"Mean FN400, {win} (µV; negative up)",
          title="B. Old- vs new-image memorability and FN400")
    text = "\n".join([
        _effect_text(m, "OldResMem", "Old slope"),
        _effect_text(m, "NewResMem", "New slope"),
        _effect_text(models["secondary_fn400_contrast"], "OldResMem", "Old − new")])
    b.text(0.02, 0.03, text, transform=b.transAxes, fontsize=8.5)
    b.legend(frameon=False, fontsize=8, loc="upper right")
    b.grid(alpha=0.2)

    fig.tight_layout()
    fig.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()
    return fig, (a, b)
