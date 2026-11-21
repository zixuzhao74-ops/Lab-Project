import numpy as np
import pandas as pd
from pymer4.models import Lmer

from memorability_analysis_behavioral.load import load_data
from memorability_analysis_behavioral.filter import select_main_recognition_trials, match_stimulus_scores
from memorability_analysis_behavioral.data_preprocess import create_binary_accuracy


def build_dataset(file_pairs):
    """Run the existing pipeline for every participant and stack the results.

    file_pairs: list of (stim_file, exp_file) tuples, one per participant,
                e.g. ("Q54_allstim.csv", "Q54_Hummingbird_....csv")
    """
    frames = []
    for stim_file, exp_file in file_pairs:
        stim, raw = load_data(stim_file, exp_file)
        trials = select_main_recognition_trials(raw)
        matched = match_stimulus_scores(trials, stim)
        frames.append(create_binary_accuracy(matched))  # excludes no-answers
    D = pd.concat(frames, ignore_index=True)
    print(f"Participants: {D['ID'].nunique()}, trials: {len(D)}")
    return D


def fit_recognition_glmm(D, random_slope=True):
    """Binomial GLMM (lme4 via pymer4):
    correct ~ old ResMem + foil FalseResMem + old category + block
    random: subject intercept (+ ResMem slope), old-image and new-image intercepts
    """
    D = D.copy()
    D["subject"] = D["ID"].astype(str)
    D["OLDITEM"] = D["OLDITEM"].astype(str)   # grouping factors as strings
    D["NEWITEM"] = D["NEWITEM"].astype(str)
    D["correct"] = D["correct"].astype(int)   # R needs 0/1, not True/False

    # centered + scaled (per 0.1 ResMem, per 0.01 FalseResMem)
    D["oldResMem_c"] = (D["oldResMem"] - D["oldResMem"].mean()) / 0.1
    D["foilFalseResMem_c"] = (D["foilFalseResMem"] - D["foilFalseResMem"].mean()) / 0.01
    D["block_c"] = D["block"] - D["block"].mean()

    scene = D["oldScene"].astype(str).str.lower()
    if not scene.isin(["indoor", "outdoor"]).all():
        raise ValueError(f"Unexpected oldScene values: {scene.unique()}")
    D["category_old"] = np.where(scene == "indoor", 0.5, -0.5)  # indoor = +0.5

    # only pass the columns R needs (faster transfer to R)
    cols = ["correct", "oldResMem_c", "foilFalseResMem_c", "category_old",
            "block_c", "subject", "OLDITEM", "NEWITEM"]
    data = D[cols].dropna()

    subj_re = "(1 + oldResMem_c | subject)" if random_slope else "(1 | subject)"
    formula = ("correct ~ oldResMem_c + foilFalseResMem_c + category_old + block_c"
               f" + {subj_re} + (1 | OLDITEM) + (1 | NEWITEM)")

    m = Lmer(formula, data=data, family="binomial")
    m.fit(control="optimizer='bobyqa', optCtrl=list(maxfun=2e5)", summarize=False)

    coefs = m.coefs  # one row per fixed effect
    table = pd.DataFrame({
        "log_odds": coefs["Estimate"],
        "SE":       coefs["SE"],
        "OR":       np.exp(coefs["Estimate"]),
        "OR_2.5%":  np.exp(coefs["Estimate"] - 1.96 * coefs["SE"]),
        "OR_97.5%": np.exp(coefs["Estimate"] + 1.96 * coefs["SE"]),
        "z":        coefs["Z-stat"],
        "p":        coefs["P-val"],
    })

    print(m.summary())
    print("\nRandom effects:\n", m.ranef_var)
    if m.warnings:
        print("\nWarnings:", m.warnings)
    print(table.round(3))
    return m, table, D