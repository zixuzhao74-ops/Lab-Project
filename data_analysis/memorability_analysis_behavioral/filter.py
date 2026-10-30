"""Preprocess old resmem scores, its corresponding scene, block #; new  
resmem scores, its corresponding falseresmem scores, scene, block #

Raises:
    ValueError: when trials cannot match file names after merging old and 
        new items from raw data CSV file
"""

import pandas as pd


def select_main_recognition_trials(raw: pd.DataFrame):
    """Select main recognition trials from the raw experiment data."""
    # Only main recognition trials (exclude practice and other phases)
    keep = (
        raw["PHASE"].astype("string").str.lower().eq("test")
        & raw["SESSIONTYPE"].astype("string").str.lower().eq("main")
    )
    # This slices the DataFrame into one containing only the "keep" rows and
    # the columns specified in the list below.
    trials = raw.loc[keep, ["ID", "OLDITEM", "NEWITEM", "CORRECT"]].copy()
    print(f"Main recognition trials: {len(trials)}")
    return trials


def match_stimulus_scores(trials: pd.DataFrame, stim: pd.DataFrame):
    """Join main recognition trials to the stimulus memorability scores."""
    # Match each old and new image to its stimulus-model scores and \
        # convert the column names to more meaningful ones for this memorability analysis.
    old = (stim.loc[stim["role"].str.lower().eq("old"),
            ["filename", "ResMem", "scene", "block"]]
        .rename(columns={
                "filename": "OLDITEM",
                "ResMem": "oldResMem",
                "scene": "oldScene"}))

    foil = (stim.loc[stim["role"].str.lower().eq("recognition_new"),
            ["filename", "ResMem", "FalseResMem"]]
        .rename(columns={
                "filename": "NEWITEM",
                "ResMem": "foilResMem",
                "FalseResMem": "foilFalseResMem"}))

    matched = trials.merge(
        old, on="OLDITEM", how="inner", validate="many_to_one"
    )
    matched = matched.merge(
        foil, on="NEWITEM", how="inner", validate="many_to_one"
    )
    print(f"Successfully matched recognition trials: {len(matched)}")
    if len(matched) != len(trials):
        raise ValueError(
            "Some recognition trials did not match; check image filenames."
        )
    return matched