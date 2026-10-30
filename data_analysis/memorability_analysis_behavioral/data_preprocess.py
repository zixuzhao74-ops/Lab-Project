"""Test whether old-image ResMem predicts recognition accuracy. This is only
for a single participant using the logistic regression.

Both CSVs and this .py file should be in the same folder
"""

import numpy as np
import pandas as pd


def create_binary_accuracy(D: pd.DataFrame):
    """Create binary recognition accuracy, excluding no-answer ones.
    """
    response = D["CORRECT"].astype("string").str.strip().str.upper()
    
    is_no_answer = response.eq("NO ANSWER") | response.isna()
    print(f"Unanswered trials excluded: {int(is_no_answer.sum())}")
    D = D.loc[~is_no_answer].copy()
    
    response = response.loc[D.index]
    if not response.isin(["CORRECT", "INCORRECT"]).all():
        raise ValueError("Unexpected CORRECT values in recognition trials.")

    D["correct"] = response.eq("CORRECT").astype(int)
    print(
        f"Answered trials: {len(D)}; correct: {D['correct'].sum()}; "
        f"accuracy: {D['correct'].mean() * 100:.2f}%"
    )
    return D


def standardize_predictors(D: pd.DataFrame):
    """Standardize predictors: 1 unit = 1 sample SD (MATLAB zscore default).
    """
    for source, standardized in [
        ("oldResMem", "oldZ"),
        ("foilFalseResMem", "foilFZ"),
        ("foilResMem", "foilRZ"),
    ]:
        D[standardized] = (D[source] - D[source].mean()) / D[source].std(ddof=1)

    D["oldScene"] = D["oldScene"].astype("category")
    return D