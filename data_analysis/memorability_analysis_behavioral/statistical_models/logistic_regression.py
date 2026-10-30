import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf

def fit_simple_model(D: pd.DataFrame):
    """Simple logistic regression, where predictor is old resmem scores.
    """
    simple = smf.glm(
        formula="correct ~ oldZ", data=D, family=sm.families.Binomial()
    ).fit()
    print("\nSIMPLE LOGISTIC REGRESSION")
    print(simple.summary())
    return simple


def fit_adjusted_model(D: pd.DataFrame):
    """Adjusted model: foil falseresmem scores, block #, and old image scene \
        category (categorical: C()) were covariates, while old resmem scores \
        is the predictor.
    """
    adjusted = smf.glm(
        formula="correct ~ oldZ + foilFZ + C(oldScene) + block",
        data=D,
        family=sm.families.Binomial(),
    ).fit()
    print("\nADJUSTED LOGISTIC REGRESSION")
    print(adjusted.summary())

    beta = adjusted.params["oldZ"] # coefficient
    ci_low, ci_high = adjusted.conf_int().loc["oldZ"] # confidence interval
    p = adjusted.pvalues["oldZ"] # statistical significance
    print(
        f"\nAdjusted old-image ResMem: OR = {np.exp(beta):.3f}, "
        f"95% CI [{np.exp(ci_low):.3f}, {np.exp(ci_high):.3f}], "
        f"p = {p:.4f}"
    )
    return adjusted


def fit_extended_model(D: pd.DataFrame):
    """extended model: add foil resmem scores as an additional covariate.
    """
    extended = smf.glm(
        formula="correct ~ oldZ + foilRZ + foilFZ + C(oldScene) + block",
        data=D,
        family=sm.families.Binomial(),
    ).fit()
    print("\nEXTENDED LOGISTIC REGRESSION")
    print(extended.summary())
    return extended