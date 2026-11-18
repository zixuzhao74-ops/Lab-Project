"""Load the preprocessed EEG (EEGLAB .set), the original BrainVision markers
(.vmrk), the memorability score file and the raw data file
"""

import re
from pathlib import Path
import mne
import pandas as pd
from pymatreader import read_mat


def load_data(stim_file, exp_file):
    """Load the stimulus and experiment CSV files.
    """
    stim = pd.read_csv(stim_file)
    raw = pd.read_csv(exp_file, low_memory=False)
    return stim, raw


def trigger_code(label):
    """Convert a trigger label to an integer ('S  3', '3' and 3.0 all give 3).
    """
    match = re.search(r"\d+", str(label))
    return int(match.group()) if match else None


def load_vmrk_codes(vmrk_file):
    """Read the trigger code of every Stimulus marker in the original
    BrainVision .vmrk file: {marker number: trigger code}.
    """
    codes = {}
    text = Path(vmrk_file).read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        match = re.match(r"Mk(\d+)=Stimulus,([^,]*),", line)
        if match:
            codes[int(match.group(1))] = trigger_code(match.group(2))
    print(f"Stimulus markers in {Path(vmrk_file).name}: {len(codes)}")
    return codes


def load_eeg_structure(set_file):
    """Read the EEGLAB structure of a .set file (the epoch and reject fields
    are needed to match epochs to trials).
    """
    mat = read_mat(str(set_file))
    return mat.get("EEG", mat)


def load_epochs(set_file):
    """Load the epoched EEG data of a .set file with MNE.
    """
    epochs = mne.read_epochs_eeglab(str(set_file), verbose="error")
    print(f"Epochs in {Path(set_file).name}: {len(epochs)}")
    return epochs
