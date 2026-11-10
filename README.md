# Lab-Project

Pipeline for a recognition-memory experiment (EEG, eye tracking and behavior). The current analysis tests whether image memorability, as predicted by the ResMem model, predicts recognition accuracy: first for a single participant (logistic regression), then across participants (binomial mixed-effects model, GLMM).

## Data source

**Stimuli.** Scene images come from the Konkle et al. scene set (`Places_Konkle_Sample300`: 201 scene categories with 300 images each, from the Places/SUN databases). Images containing people were removed with an OpenCLIP (RN50) filter (`Lab Project Code/Filter_humans.ipynb`), and scenes were labeled indoor/outdoor (`Lab Project Code/Indoor_outdoor.ipynb`).

**Memorability scores.** Every image has a `ResMem` score (predicted memorability; Needell & Bainbridge, 2022) and a `FalseResMem` score, computed with the ResMem neural network. They are stored per participant in `<ID>_allstim.csv`; the full image pool is in `memorability_scores.csv` (columns `filename`, `Folder`, `ResMem_Score`, `FalseResMem_Score`).

**Behavioral and physiological data.** Each participant completes the experiment (a PsychoPy script run with the Hummingbird setup; code in `Lab Project Code/`) with EEG and eye tracking recorded. The task has a study phase, a recognition test in which an old and a new image appear together, and a categorization task. Each participant folder in `Participants/` (`Pilot_1`, `Q54`, `Q55`, `Q56`) contains:

| File | Content | Used by |
|---|---|---|
| `<ID>_Hummingbird_*.csv` | Trial-by-trial behavioral log (phase, session type, old and new image, correct/incorrect/no answer) | `load.py`, `filter.py`, `data_preprocess.py` |
| `<ID>_allstim.csv` | One row per image: `block`, `scene`, `role` (`old`, `recognition_new`, ...), `filename`, `ResMem`, `FalseResMem` | `load.py`, `filter.py` |
| `*.eeg`, `*.vhdr`, `*.vmrk` | Raw EEG (BrainVision) | not analyzed yet |
| `*.EDF` | Raw eye-tracking data (EyeLink) | not analyzed yet |

## Data pipeline

1. **Procurement.** Run the experiment; collect the behavioral CSV, stimulus CSV, EEG and eye-tracking files.
2. **Storage.** One folder per participant under `Participants/`.
3. **Load** (`load.py`).
4. **Filter and match** (`filter.py`).
5. **Preprocess** (`data_preprocess.py`).
6. **Analyze** (`statistical_models/`).
7. **Visualize** (`data_visualization.py`).

EEG and eye-tracking analysis is not implemented yet.

## What each module does

| Module | Input | What it does | Output |
|---|---|---|---|
| `load.py` | Paths to `*_allstim.csv` and `*_Hummingbird_*.csv` | `load_data()` reads both CSVs | `stim` and `raw` DataFrames |
| `filter.py` | `raw`: `PHASE`, `SESSIONTYPE`, `ID`, `OLDITEM`, `NEWITEM`, `CORRECT`; `stim`: `role`, `filename`, `ResMem`, `FalseResMem`, `scene`, `block` | `select_main_recognition_trials()` keeps test-phase trials of the main session (drops practice). `match_stimulus_scores()` joins each trial's old image and new image (foil) to their ResMem scores and raises an error if any trial fails to match | One row per recognition trial with `oldResMem`, `oldScene`, `block`, `foilResMem`, `foilFalseResMem` |
| `data_preprocess.py` | Matched trials with `CORRECT` (`CORRECT`, `INCORRECT` or `NO ANSWER`) | `create_binary_accuracy()` drops unanswered trials and codes `correct` as 0/1. `standardize_predictors()` z-scores ResMem predictors (the Python version of MATLAB `zscore`) | Adds `correct`, `oldZ`, `foilRZ`, `foilFZ` |
| `statistical_models/logistic_regression.py` | One participant's preprocessed trials | Logistic regressions (statsmodels): simple (`correct ~ oldZ`), adjusted (adds foil FalseResMem, scene category and block), extended (adds foil ResMem) | Fitted models and printed summaries; adjusted odds ratio for old-image ResMem |
| `statistical_models/GLLM.py` | List of `(stim_file, exp_file)` pairs, one per participant | `build_dataset()` runs load, filter and preprocess for every participant and stacks them. `fit_recognition_glmm()` fits a binomial mixed model (pymer4/lme4): `correct ~ oldResMem + foilFalseResMem + category + block`, with random intercepts for subject (plus a ResMem slope), old image and new image. ResMem is scaled per 0.1 units | Fitted model, table of log-odds, odds ratios, 95% CIs, z and p, and the trial-level data |
| `data_visualization.py` | Trial data, and the fitted GLMM for the second plot | `visualize_accuracy_by_quartile()` and `plot_resmem_glmm()` (see Figures) | PNG figures |
| `foils_correlation.py` | `memorability_scores.csv` and one participant's behavioral CSV | Checks whether `ResMem` and `FalseResMem` are correlated, across the whole image pool, by category, and for the foils a participant actually saw | Printed Pearson and Spearman correlations |

## Figures

Both figures are made in `data_visualization.py` from the preprocessed trial data (`oldResMem`, `correct`) and are saved by the notebook.

1. **Accuracy by ResMem quartile** (`recognition_resmem_quartiles.png`). Old images are split into four equal-sized groups by ResMem score (Q1 lowest to Q4 highest). Each bar is the percentage of correct recognition trials in that group. It is a descriptive check made from one participant's data.
2. **GLMM prediction plot** (`ResMem_Recognition_GLMM.png`). Uses all participants and the fitted binomial GLMM.
   - x-axis: old-image ResMem score. y-axis: probability of a correct response.
   - Solid line: population-averaged model prediction. Dark band: approximate 95% confidence interval. Optional light band: 95% predictive interval for a new participant and image pair.
   - Black points: observed accuracy in equal-count ResMem bins with 95% intervals. Gray ticks along the bottom (rug): ResMem values of the old images. Dashed line: chance (0.5).
   - Text box: effect of ResMem as log-odds (β), odds ratio per 0.1 ResMem, 95% CI and p. The foil FalseResMem and block are held at their means, and scene category is averaged.

## Repository structure

```
Lab Data Collection/
├── Participants/                      # data storage (one folder per participant)
│   ├── Pilot_1/  Q54/  Q55/  Q56/
│   │   ├── <ID>_Hummingbird_*.csv     # trial-level behavioral data
│   │   ├── <ID>_allstim.csv           # stimulus ResMem / FalseResMem scores
│   │   ├── *.eeg / .vhdr / .vmrk      # raw EEG (BrainVision)
│   │   └── *.EDF                      # raw eye-tracking data (EyeLink)
├── data_analysis/                     # data analysis (installable package)
│   ├── setup.py                       # makes the package installable
│   └── memorability_analysis_behavioral/   # the package
│       ├── __init__.py
│       ├── load.py
│       ├── filter.py
│       ├── data_preprocess.py
│       ├── data_visualization.py
│       ├── foils_correlation.py
│       └── statistical_models/
│           ├── __init__.py
│           ├── logistic_regression.py # single-participant logistic models
│           └── GLLM.py                # multi-participant binomial GLMM
├── Notebook/
│   ├── run_notebook.ipynb             # imports the package, runs both analyses
│   ├── run_memorability.ipynb         # additional notebook
│   └── ResMem_Recognition_GLMM.png    # GLMM output figure
├── analyze_resmem_recognition.m       # original MATLAB analysis (translated to Python)
├── recognition_resmem_quartiles.png   # quartile output figure
└── Lab-Project/                       # git repository (pushed to GitHub)
    ├── README.md
    ├── .gitignore
    ├── data_analysis/                 # copy of the package above
    └── Lab Project Code/              # experiment and stimulus scripts
        ├── Hummingbird_balance.py
        ├── Hummingbird_balance_feedback.py
        ├── SWAN4_4_Tentative.py
        ├── SWAN4_4_Tentative2.py
        ├── Filter_humans.ipynb
        └── Indoor_outdoor.ipynb
```

Raw participant data stays outside the repository because the EEG and eye-tracking files are too large for GitHub.

## Installation

```bash
cd "Lab Data Collection/data_analysis"
pip install -e .
```

Requires Python 3 with `pandas`, `numpy`, `scipy`, `statsmodels` and `matplotlib`. The GLMM (`GLLM.py`) also needs `pymer4`, which requires R with the `lme4` package.

## Usage

Open `Notebook/run_notebook.ipynb`, set the paths to the participants' CSV files, and run all cells.

Cell 1 runs the single-participant analysis (logistic regression and the quartile figure):

```python
from memorability_analysis_behavioral import load as ld
from memorability_analysis_behavioral import filter as ft
from memorability_analysis_behavioral import data_preprocess as dp
from memorability_analysis_behavioral.statistical_models import logistic_regression as logits
from memorability_analysis_behavioral import data_visualization as dv
```

Cell 2 runs the multi-participant analysis (GLMM and its figure):

```python
from memorability_analysis_behavioral.statistical_models import GLLM

d = GLLM.build_dataset(file_lst)              # list of (stim_file, exp_file)
result, table, D = GLLM.fit_recognition_glmm(d)
fig, ax = dv.plot_resmem_glmm(result, D, filename="ResMem_Recognition_GLMM.png")
```

## Notes

- Large raw EEG and eye-tracking files (`*.eeg`, `*.EDF`) exceed GitHub's file size limit and cannot be committed.
- `foils_correlation.py` currently reads hard-coded paths (`~/Desktop/memorability_scores.csv` and one participant's file).
