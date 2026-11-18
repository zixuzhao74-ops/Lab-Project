"""Select main recognition and categorization trials, match their old and new
images to the memorability scores, and match each clean EEG epoch to its
behavioral trial

Raises:
    ValueError: when trials cannot match file names after merging old and
        new items, or when the EEG markers and behavioral trials do not line up
"""

import ntpath
import numpy as np
import pandas as pd

from memorability_analysis_neural.load import trigger_code

# Main-block image-onset triggers (practice blocks used 255)
ONSET_CODE = {"recognition": 2, "categorization": 3}


def image_name(path):
    """Keep only the image file name (drops a Windows or Mac folder path).
    """
    return ntpath.basename(str(path)).strip()


def select_main_trials(raw: pd.DataFrame, phase: str):
    """Select main recognition or categorization trials, in presentation order,
    and find the side of the old image and whether it was the target.
    """
    if phase == "categorization":
        keep = (raw["Cate_OLDITEM"].notna()
                & raw["Cate_SESSIONTYPE"].astype("string").str.lower().eq("main"))
        trials = raw.loc[keep].copy()
        trials["old_img"] = trials["Cate_OLDITEM"].map(image_name)
        trials["new_img"] = trials["Cate_NEWITEM"].map(image_name)
        # The old image is the target when its category is the searched category
        target_cat = (trials["Cate_CONDITION"].astype(str)
                      .str.extract(r"find_(\w+)", expand=False).str.lower())
        trials["old_is_target"] = (trials["OLDITEM_CATEGORY"].astype(str)
                                   .str.lower().eq(target_cat))
        target_loc = trials["Cate_TARGET_LOC"].astype(str).str.upper()
        trials["old_side"] = np.where(
            trials["old_is_target"], target_loc,
            np.where(target_loc.eq("LEFT"), "RIGHT", "LEFT"))
        response = trials["Cate_CORRECT"]
    else:
        # Recognition always asks for the OLD image, so the target is the old image
        keep = (raw["OLDITEM"].notna()
                & raw["SESSIONTYPE"].astype("string").str.lower().eq("main"))
        trials = raw.loc[keep].copy()
        trials["old_img"] = trials["OLDITEM"].map(image_name)
        trials["new_img"] = trials["NEWITEM"].map(image_name)
        trials["old_is_target"] = True
        trials["old_side"] = trials["TARGET_LOC"].astype(str).str.upper()
        response = trials["CORRECT"]

    if not trials["old_side"].isin(["LEFT", "RIGHT"]).all():
        raise ValueError(f"Unexpected old-image side values in {phase} trials.")

    trials["correct"] = (response.astype("string").str.strip().str.upper()
                         .eq("CORRECT").fillna(False).astype(bool))
    # Presentation order = order of the onset markers in the EEG recording
    trials["ordinal"] = np.arange(len(trials))
    print(f"Main {phase} trials: {len(trials)}")
    return trials


def match_stimulus_scores(trials: pd.DataFrame, stim: pd.DataFrame, phase: str):
    """Join each trial's old and new image to their memorability scores.
    """
    stim = stim.copy()
    stim["filename"] = stim["filename"].map(image_name)
    stim["role"] = stim["role"].astype(str).str.lower()
    new_role = "categorization_new" if phase == "categorization" else "recognition_new"

    old = (stim.loc[stim["role"].eq("old"), ["filename", "ResMem", "scene", "block"]]
           .rename(columns={
                "filename": "old_img",
                "ResMem": "old_ResMem",
                "scene": "old_scene"}))
    new = (stim.loc[stim["role"].eq(new_role), ["filename", "ResMem", "FalseResMem"]]
           .rename(columns={
                "filename": "new_img",
                "ResMem": "new_ResMem",
                "FalseResMem": "new_FalseResMem"}))

    matched = trials.merge(old, on="old_img", how="inner", validate="many_to_one")
    matched = matched.merge(new, on="new_img", how="inner", validate="many_to_one")
    print(f"Successfully matched {phase} trials: {len(matched)}")
    if len(matched) != len(trials):
        raise ValueError(
            f"Some {phase} trials did not match; check image filenames."
        )

    if phase == "categorization":
        agree = (matched["OLDITEM_CATEGORY"].astype(str).str.lower()
                 .eq(matched["old_scene"].astype(str).str.lower()))
        if not agree.all():
            raise ValueError("OLDITEM_CATEGORY disagrees with the allstim scene.")

    return matched[["ordinal", "block", "old_img", "new_img", "old_is_target",
                    "old_side", "correct", "old_ResMem", "new_ResMem",
                    "new_FalseResMem", "old_scene"]]


def epoch_trial_ordinals(eeg: dict, vmrk_codes: dict, code: int):
    """Find, for every epoch, its position (0, 1, 2, ...) among all `code`
    markers of the original recording, using the BrainVision marker number
    (bvmknum) kept by EEGLAB/ERPLAB. Epochs not time-locked to `code`, or
    still marked as artifacts, get NaN.
    """
    code_markers = sorted(mk for mk, c in vmrk_codes.items() if c == code)
    ordinal_of = {mk: i for i, mk in enumerate(code_markers)}

    epoch = eeg["epoch"]
    if "eventbvmknum" not in epoch:
        raise ValueError("Epochs have no 'eventbvmknum'; cannot recover trial order.")

    n_epochs = len(epoch["eventlatency"])
    rejected = np.zeros(n_epochs, bool)
    rejmanual = np.atleast_1d(eeg.get("reject", {}).get("rejmanual", []))
    if rejmanual.size == n_epochs:
        rejected |= rejmanual.astype(bool)

    ordinals, still_marked = [], 0
    for k in range(n_epochs):
        latency = np.atleast_1d(epoch["eventlatency"][k])
        marker = np.atleast_1d(epoch["eventbvmknum"][k])
        flag = (np.atleast_1d(epoch["eventflag"][k]) if "eventflag" in epoch
                else np.zeros(len(latency)))
        lock = [i for i in range(len(latency)) if abs(float(latency[i])) < 1]
        if not lock:
            ordinals.append(np.nan)
            continue
        i = lock[0]
        mk = int(marker[i])
        # ERPLAB artifact-detection flags are bits 1-8
        artifact = rejected[k] or (int(flag[i]) & 255) != 0
        if vmrk_codes.get(mk) == code and artifact:
            still_marked += 1
        if vmrk_codes.get(mk) != code or artifact:
            ordinals.append(np.nan)
        else:
            ordinals.append(ordinal_of[mk])

    if still_marked:
        print(f"Epochs still marked as artifacts (dropped): {still_marked}")
    return np.asarray(ordinals, float), len(code_markers)


def match_epochs_to_trials(trials: pd.DataFrame, ordinals: np.ndarray,
                           n_markers: int, phase: str):
    """Keep one behavioral trial per clean epoch, in the same order as the
    epochs.
    """
    if n_markers != len(trials):
        raise ValueError(
            f"{n_markers} {phase} markers in the EEG but {len(trials)} behavioral "
            "trials. Do not force-match; check the recording."
        )
    if len(np.unique(ordinals)) != len(ordinals):
        raise ValueError(f"Duplicate {phase} trials among the EEG epochs.")

    matched = trials.set_index("ordinal").loc[ordinals].reset_index()
    print(f"Clean {phase} epochs matched to trials: {len(matched)} of {len(trials)} "
          f"({100 * len(matched) / len(trials):.1f}%)")
    return matched
