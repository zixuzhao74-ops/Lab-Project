"""Compute single-trial r-CDA and FN400 amplitudes from the clean epochs, keep
correct trials, and center/scale the predictors for the mixed-effects models
"""

import numpy as np
import pandas as pd

BASELINE = (-0.2, 0.0)

# r-CDA: contralateral minus ipsilateral to the OLD image
RCDA_CHANNELS = ("PO7", "PO8")    # (left, right): thesis ROI (as in Utochkin & Vogel)
RCDA_WINDOW = (0.250, 0.450)      # thesis primary window
# Preprint full window (Utochkin & Vogel), reported as a robustness check
RCDA_ROBUSTNESS = {"rcda_PO_250_800": (("PO7", "PO8"), (0.250, 0.800))}

FN400_CHANNELS = ["Fz", "F3", "F4"]
FN400_WINDOW = (0.250, 0.500)

RESMEM_SCALE = 0.1                # model units: per 0.1 ResMem
FALSEMEM_SCALE = 0.01             # model units: per 0.01 FalseResMem

NEEDED_CHANNELS = list(dict.fromkeys(
    [*RCDA_CHANNELS,
     *[ch for chs, _ in RCDA_ROBUSTNESS.values() for ch in chs],
     *FN400_CHANNELS]))


def select_epoch_data(epochs, ordinals: np.ndarray):
    """Keep the clean epochs of one phase, baseline them and return their data
    in microvolts (epochs x NEEDED_CHANNELS x time).
    """
    keep = np.flatnonzero(~np.isnan(ordinals))
    if len(epochs) != len(ordinals):
        raise ValueError(f"MNE read {len(epochs)} epochs, but the file lists {len(ordinals)}.")
    missing = set(NEEDED_CHANNELS) - set(epochs.ch_names)
    if missing:
        raise ValueError(f"Missing channels {sorted(missing)}. Available: {epochs.ch_names}")
    if epochs.times[0] > BASELINE[0] + 1e-6:
        raise ValueError(f"Epochs start after {BASELINE[0]} s; cannot baseline.")

    selected = epochs[keep]
    selected.apply_baseline(BASELINE)
    data = selected.get_data(picks=NEEDED_CHANNELS) * 1e6   # volts -> µV
    return data, selected.times, ordinals[keep].astype(int)


def compute_trial_measures(D: pd.DataFrame, data: np.ndarray, times: np.ndarray):
    """Compute single-trial r-CDA (contralateral minus ipsilateral to the old
    image) and FN400 (frontal mean) amplitudes, and keep their waveforms for the
    figures.
    """
    D = D.copy()
    ch = {name: i for i, name in enumerate(NEEDED_CHANNELS)}
    old_left = D["old_side"].eq("LEFT").to_numpy()[:, None]

    def lateralized(left, right):
        L, R = data[:, ch[left]], data[:, ch[right]]
        return np.where(old_left, R - L, L - R)

    def window_mean(wave, window):
        sel = (times >= window[0] - 1e-9) & (times <= window[1] + 1e-9)
        return wave[:, sel].mean(axis=1)

    rcda_wave = lateralized(*RCDA_CHANNELS)
    fn400_wave = data[:, [ch[c] for c in FN400_CHANNELS]].mean(axis=1)

    D["rcda"] = window_mean(rcda_wave, RCDA_WINDOW)
    for name, (channels, window) in RCDA_ROBUSTNESS.items():
        D[name] = window_mean(lateralized(*channels), window)
    D["fn400"] = window_mean(fn400_wave, FN400_WINDOW)
    D["rcda_wave"] = list(rcda_wave)
    D["fn400_wave"] = list(fn400_wave)
    return D


def select_correct_trials(D: pd.DataFrame):
    """Keep correct trials only (as in Utochkin & Vogel).
    """
    D = D.loc[D["correct"]].copy()
    print(f"Correct trials kept: {len(D)}")
    return D


def select_answered_trials(D: pd.DataFrame):
    """Keep trials with a response (correct or error), dropping timeouts. Used for
    recognition, where errors are analyzed instead of discarded: ResMem predicts
    accuracy, so keeping only correct trials would condition on the outcome.
    """
    D = D.loc[D["answered"]].copy()
    print(f"Answered trials kept: {len(D)} ({int(D['correct'].sum())} correct)")
    return D


def prepare_predictors(D: pd.DataFrame):
    """Center and scale the predictors (per 0.1 ResMem, per 0.01 FalseResMem)
    and sum-code the categorical ones (indoor = +0.5, old image target = +0.5).
    """
    D = D.copy()
    D["OldResMem"] = (D["old_ResMem"] - D["old_ResMem"].mean()) / RESMEM_SCALE
    D["NewResMem"] = (D["new_ResMem"] - D["new_ResMem"].mean()) / RESMEM_SCALE
    D["NewFalseResMem"] = ((D["new_FalseResMem"] - D["new_FalseResMem"].mean())
                           / FALSEMEM_SCALE)

    scene = D["old_scene"].astype(str).str.lower()
    if not scene.isin(["indoor", "outdoor"]).all():
        raise ValueError(f"Unexpected old_scene values: {scene.unique()}")
    D["OldCategory"] = np.where(scene == "indoor", 0.5, -0.5)
    D["Role"] = np.where(D["old_is_target"], 0.5, -0.5)
    D["Block"] = D["block"] - D["block"].mean()
    # With SumResMem in the model, the OldResMem coefficient = old - new slope
    D["SumResMem"] = D["OldResMem"] + D["NewResMem"]
    # The r-CDA is a difference between the two items, so model it with the old - new
    # ResMem difference. DiffResMem slope > 0 means a more memorable old image
    # (or less memorable new image) pulls the lateralization toward the old image;
    # a nonzero SumResMem slope means the old and new effects are asymmetric.
    D["DiffResMem"] = D["OldResMem"] - D["NewResMem"]
    # Recognition error analysis (2AFC: an error means the new image was chosen).
    # rcda is signed to the old image; flip it on errors to sign it to the chosen image.
    D["Correct"] = np.where(D["correct"], 0.5, -0.5)
    chosen_sign = np.where(D["correct"], 1.0, -1.0)
    D["rcda_chosen"] = D["rcda"] * chosen_sign
    for name in RCDA_ROBUSTNESS:
        D[f"{name}_chosen"] = D[name] * chosen_sign
    return D
