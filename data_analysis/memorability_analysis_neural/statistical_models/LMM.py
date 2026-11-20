"""Linear mixed-effects models (lme4 via pymer4) for the neural questions:
primary: old-image ResMem -> r-CDA during categorization;
secondary: old- vs new-image ResMem -> FN400 during categorization;
control: old-image ResMem -> r-CDA during recognition.
"""

import re
from pathlib import Path
import numpy as np
import pandas as pd
from pymer4.models import Lmer

from memorability_analysis_neural.load import (
    load_data, load_vmrk_codes, load_eeg_structure, load_epochs)
from memorability_analysis_neural.filter import (
    ONSET_CODE, select_main_trials, match_stimulus_scores,
    epoch_trial_ordinals, match_epochs_to_trials)
from memorability_analysis_neural.data_preprocess import (
    RCDA_ROBUSTNESS, select_epoch_data, compute_trial_measures,
    select_correct_trials, select_answered_trials, prepare_predictors)

LMM_CONTROL = "optimizer='bobyqa', optCtrl=list(maxfun=2e5)"
COVARIATES = " + NewFalseResMem + OldCategory + Block"


def build_phase_dataset(subject, files, phase):
    """Run load, filter and preprocess for one participant and one phase.

    files: dict with the paths "set", "vmrk", "behavior" and "allstim"
    """
    stim, raw = load_data(files["allstim"], files["behavior"])
    trials = select_main_trials(raw, phase)
    trials = match_stimulus_scores(trials, stim, phase)

    eeg = load_eeg_structure(files["set"])
    vmrk_codes = load_vmrk_codes(files["vmrk"])
    ordinals, n_markers = epoch_trial_ordinals(eeg, vmrk_codes, ONSET_CODE[phase])
    data, times, kept = select_epoch_data(load_epochs(files["set"]), ordinals)

    matched = match_epochs_to_trials(trials, kept, n_markers, phase)
    matched = compute_trial_measures(matched, data, times)
    matched["subject"] = str(subject)
    return matched, times


def build_dataset(subject_files):
    """Run the pipeline for every participant and stack the results.

    subject_files: {subject ID: dict(set=..., vmrk=..., behavior=..., allstim=...)}
    Returns categorization trials (correct only; accuracy is near ceiling),
    recognition trials (all answered trials, errors kept, with Correct and the
    chosen-signed r-CDA) and the epoch time axis.
    """
    frames = {"categorization": [], "recognition": []}
    times = None
    for subject, files in subject_files.items():
        print(f"\n--- {subject} ---")
        for phase in frames:
            D, t = build_phase_dataset(subject, files, phase)
            if times is not None and not np.allclose(times, t):
                raise ValueError("Epoch time axes differ across files.")
            times = t
            frames[phase].append(D)

    cat = prepare_predictors(select_correct_trials(
        pd.concat(frames["categorization"], ignore_index=True)))
    rec = prepare_predictors(select_answered_trials(
        pd.concat(frames["recognition"], ignore_index=True)))
    print(f"\nParticipants: {cat['subject'].nunique()}, categorization trials: "
          f"{len(cat)}, recognition trials: {len(rec)}")
    return cat, rec, times


def random_effects(random_slope=True):
    """Crossed random effects: subject (+ ResMem slope), old and new image.
    """
    subj = "(1 + OldResMem | subject)" if random_slope else "(1 | subject)"
    return f" + {subj} + (1 | old_img) + (1 | new_img)"


def fit_lmm(formula, D, label):
    """Fit one linear mixed model (REML; Satterthwaite df via lmerTest).
    """
    names = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", formula))
    data = D[[c for c in D.columns if c in names]].dropna().copy()
    for group in ["subject", "old_img", "new_img"]:
        data[group] = data[group].astype(str)   # grouping factors as strings

    m = Lmer(formula, data=data)
    m.fit(REML=True, control=LMM_CONTROL, summarize=False)

    print(f"\n{label.upper()}\n{formula}\nN trials = {len(data)}")
    print(m.coefs.round(4))
    print("\nRandom effects:\n", m.ranef_var)
    if m.warnings:
        print("\nWarnings:", m.warnings)
    return m


def fit_neural_models(cat, rec, random_slope=True, out_dir=None):
    """Fit the primary, secondary, control and robustness models.

    Primary:   rcda ~ OldResMem + covariates + Role      (categorization)
    Secondary: fn400 ~ OldResMem + NewResMem + ...        (separate slopes)
               fn400 ~ OldResMem + SumResMem + ...        (OldResMem = old - new)
    Control:   rcda ~ OldResMem + covariates              (recognition)
    Relative:  rcda ~ DiffResMem + SumResMem + ...        (categorization)
    Exploratory: DiffResMem x Role; recognition errors (chosen-signed r-CDA)
    """
    if cat["subject"].nunique() < 5:
        print("\nNOTE: fewer than 5 participants. Subject random effects cannot be "
              "estimated reliably; treat these fits as a pipeline check, not results.")

    RE = random_effects(random_slope)
    models = {
        "primary_rcda": fit_lmm(
            "rcda ~ OldResMem" + COVARIATES + " + Role" + RE, cat,
            "Primary: r-CDA ~ old ResMem (categorization)"),
        "secondary_fn400_slopes": fit_lmm(
            "fn400 ~ OldResMem + NewResMem" + COVARIATES + " + Role" + RE, cat,
            "Secondary: FN400 old and new slopes"),
        "secondary_fn400_contrast": fit_lmm(
            "fn400 ~ OldResMem + SumResMem" + COVARIATES + " + Role" + RE, cat,
            "Secondary: FN400 old - new contrast (OldResMem term)"),
    }
    # Recognition keeps errors, so the control model gets Correct as a covariate and
    # is refit on correct trials only to match the earlier version.
    models["control_recognition_rcda"] = fit_lmm(
        "rcda ~ OldResMem + Correct" + COVARIATES + RE, rec,
        "Control: r-CDA ~ old ResMem (recognition, all answered trials)")
    models["control_recognition_rcda_correct_only"] = fit_lmm(
        "rcda ~ OldResMem" + COVARIATES + RE, rec[rec["correct"]],
        "Control: r-CDA ~ old ResMem (recognition, correct trials only)")
    models["recognition_chosen_rcda"] = fit_lmm(
        "rcda_chosen ~ OldResMem * Correct" + COVARIATES + RE, rec,
        "Exploratory: chosen-signed r-CDA, correct vs error (recognition)")
    # Relative (old - new) ResMem and its interaction with Role (categorization)
    models["relative_rcda"] = fit_lmm(
        "rcda ~ DiffResMem + SumResMem" + COVARIATES + " + Role" + RE, cat,
        "Relative: r-CDA ~ old-minus-new ResMem (categorization)")
    models["role_interaction_rcda"] = fit_lmm(
        "rcda ~ DiffResMem * Role + SumResMem" + COVARIATES + RE, cat,
        "Exploratory: r-CDA ~ ResMem difference x Role (categorization)")
    for name in RCDA_ROBUSTNESS:
        models[f"robust_{name}"] = fit_lmm(
            f"{name} ~ OldResMem" + COVARIATES + " + Role" + RE, cat,
            f"Robustness: {name}")

    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, m in models.items():
            m.coefs.to_csv(out_dir / f"{name}_fixed_effects.csv")
        waves = ["rcda_wave", "fn400_wave"]
        cat.drop(columns=waves).to_csv(out_dir / "categorization_trials.csv", index=False)
        rec.drop(columns=waves).to_csv(out_dir / "recognition_trials.csv", index=False)
        print(f"\nSaved model tables and trial data to {out_dir}")
    return models
