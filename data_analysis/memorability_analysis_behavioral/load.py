"""Load the memorability score file and raw data file
"""

from pathlib import Path
import pandas as pd


def load_data(stim_file, exp_file):
    """Load the stimulus and experiment CSV files.
    """
    stim = pd.read_csv(stim_file)
    raw = pd.read_csv(exp_file, low_memory=False)
    return stim, raw