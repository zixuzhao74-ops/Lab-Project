# Lab-Project

Pipeline for a recognition-memory experiment (EEG + behavior). The current
analysis tests whether image memorability, as predicted by the ResMem model,
predicts recognition accuracy for a participant.

## Data pipeline

1. **Procurement.** Each participant completes the experiment (built in PsychoPy/Hummingbird) while EEG is recorded. This yields:
   - a trial-level behavioral CSV (`*_Hummingbird_*.csv`)
   - a stimulus score CSV (`*_allstim.csv`) with `ResMem` and `FalseResMem` scores for every image
   - raw EEG (`.eeg`/`.vhdr`/`.vmrk`, `.EDF`)
2. **Storage.** One folder per participant under `Participants/`.
3. **Load** (`load.py`): read the stimulus and behavioral CSVs.
4. **Filter** (`filter.py`): keep main recognition trials (`PHASE == test`, `SESSIONTYPE == main`) and match each old and new image to its ResMem scores.
5. **Preprocess** (`data_preprocess.py`): exclude unanswered trials, code accuracy as 0/1, and z-score the predictors.
6. **Analyze** (`statistical_models/logistic_regression.py`): simple, adjusted (foil FalseResMem, block, scene) and extended (adds foil ResMem) logistic regressions.
7. **Visualize** (`data_visualization.py`): recognition accuracy by quartile of old-image ResMem.

EEG analysis is not implemented yet.

## Repository structure

```
Lab-Project/
├── README.md
├── .gitignore
├── Participants/                      # data storage (one folder per participant)
│   └── Pilot_1/
│       ├── TEST_1_Hummingbird_*.csv   # trial-level behavioral data
│       ├── TEST_1_allstim.csv         # stimulus ResMem / FalseResMem scores
│       ├── TEST.eeg / .vhdr / .vmrk   # raw EEG (BrainVision)
│       └── TEST_1_*.EDF               # raw EEG (EDF)
└── data_analysis/                     # data analysis
    ├── setup.py                       # makes the package installable
    ├── run_notebook.ipynb             # imports the package and runs the analysis
    └── memorability_analysis_behavioral/   # the package
        ├── __init__.py
        ├── load.py
        ├── filter.py
        ├── data_preprocess.py
        ├── data_visualization.py
        └── statistical_models/
            ├── __init__.py
            └── logistic_regression.py
```

## Installation

```bash
cd data_analysis
pip install -e .
```

Requires Python 3 with `pandas`, `numpy`, `statsmodels` and `matplotlib`.

## Usage

Open `data_analysis/run_notebook.ipynb`, set the paths to a participant's CSV files, and run all cells:

```python
from memorability_analysis_behavioral import load as ld
from memorability_analysis_behavioral import filter as ft
from memorability_analysis_behavioral import data_preprocess as dp
from memorability_analysis_behavioral.statistical_models import logistic_regression as logits
from memorability_analysis_behavioral import data_visualization as dv
```

## Notes

- Large raw EEG files (`*.eeg`, `*.EDF`) exceed GitHub's file size limit and cannot be committed.
