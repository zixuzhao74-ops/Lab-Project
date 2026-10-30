"""Visualize recognition accuracy by quartile groups of memorability scores

Install packages once (recommended terminal command):
    pip install pandas numpy statsmodels matplotlib
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


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


def save_analysis_outputs(D: pd.DataFrame, quartile_summary: pd.DataFrame, folder: Path):
    """10. Save the cleaned, matched trial-level dataset.
    """
    D.to_csv(folder / "recognition_resmem_merged.csv", index=False)
    quartile_summary.to_csv(folder / "recognition_resmem_quartiles.csv", index=False)
    print("\nSaved recognition_resmem_merged.csv")
    print("Saved recognition_resmem_quartiles.csv")
    print("Saved recognition_resmem_quartiles.png")