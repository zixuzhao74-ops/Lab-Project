# Lab-Project

Pipeline for a recognition-memory experiment (EEG, eye tracking and behavior). The analysis tests whether image memorability, as predicted by the ResMem model, predicts:

- **recognition accuracy** (behavioral): first for a single participant (logistic regression), then across participants (binomial mixed-effects model, GLMM);
- **neural prioritization during categorization** (EEG): whether old-image ResMem predicts the r-CDA (primary question), and whether old-image ResMem predicts the FN400 more strongly than new-image ResMem (secondary question), with linear mixed-effects models (LMM).

## Data source

**Stimuli.** Scene images come from the Konkle et al. scene set (`Places_Konkle_Sample300`: 201 scene categories with 300 images each, from the Places/SUN databases). Images containing people were removed with an OpenCLIP (RN50) filter (`Lab Project Code/Filter_humans.ipynb`), and scenes were labeled indoor/outdoor (`Lab Project Code/Indoor_outdoor.ipynb`).

**Memorability scores.** Every image has a `ResMem` score (predicted memorability; Needell & Bainbridge, 2022) and a `FalseResMem` score, computed with the ResMem neural network. They are stored per participant in `<ID>_allstim.csv`; the full image pool is in `memorability_scores.csv` (columns `filename`, `Folder`, `ResMem_Score`, `FalseResMem_Score`).

**Behavioral and physiological data.** Each participant completes the experiment (a PsychoPy script run with the Hummingbird setup; code in `Lab Project Code/`) with EEG and eye tracking recorded. The task has a study phase, a recognition test in which an old and a new image appear together, and a categorization task in which one old and one new image (always opposite scene categories) appear together. Each participant folder in `Participants/` (`Pilot_1`, `Q54`, `Q55`, `Q56`, `Q57`) contains:

| File | Content | Used by |
|---|---|---|
| `<ID>_Hummingbird_*.csv` | Trial-by-trial behavioral log (phase, session type, old and new image, side of the target, correct/incorrect/no answer) | behavioral and neural `load.py`, `filter.py` |
| `<ID>_allstim.csv` | One row per image: `block`, `scene`, `role` (`old`, `recognition_new`, `categorization_new`), `filename`, `ResMem`, `FalseResMem` | behavioral and neural `load.py`, `filter.py` |
| `*.eeg`, `*.vhdr`, `*.vmrk` | Raw EEG (BrainVision). The `.vmrk` marker file is used to recover the original trial order of each clean epoch | neural `load.py`, `filter.py` |
| `checked.set` / `checked.fdt` | Preprocessed (EEGLAB/ERPLAB), epoched, artifact-rejected EEG | neural `load.py` |
| `*_unchecked.set`, `binlist.txt` | Epoched EEG before artifact rejection; ERPLAB bins (1 = study, 2 = recognition, 3 = categorization) | preprocessing only |
| `*.EDF`, `*.asc`, `*_eye.mat` | Raw and converted eye-tracking data (EyeLink) | preprocessing only |

**EEG triggers (main blocks).** 1 = study image onset, 99 = study image offset, 2 = recognition image onset, 3 = categorization image onset, 199 = response window onset, 21/31 = response, 222/223 = no response, 100/200 = recording start/end. Practice blocks used 255.

## Data pipeline

1. **Procurement.** Run the experiment; collect the behavioral CSV, stimulus CSV, EEG and eye-tracking files.
2. **Storage.** One folder per participant under `Participants/`.
3. **Preprocess EEG** (EEGLAB/ERPLAB, outside this package): epoch from −200 to 800 ms around image onset, reject artifacts (eye tracking/EOG), save `checked.set`.
4. **Load** (`load.py`).
5. **Filter and match** (`filter.py`).
6. **Preprocess** (`data_preprocess.py`).
7. **Analyze** (`statistical_models/`).
8. **Visualize** (`data_visualization.py`).

## What each module does

### Behavioral analysis (`memorability_analysis_behavioral/`)

| Module | Input | What it does | Output |
|---|---|---|---|
| `load.py` | Paths to `*_allstim.csv` and `*_Hummingbird_*.csv` | `load_data()` reads both CSVs | `stim` and `raw` DataFrames |
| `filter.py` | `raw`: `PHASE`, `SESSIONTYPE`, `ID`, `OLDITEM`, `NEWITEM`, `CORRECT`; `stim`: `role`, `filename`, `ResMem`, `FalseResMem`, `scene`, `block` | `select_main_recognition_trials()` keeps test-phase trials of the main session (drops practice). `match_stimulus_scores()` joins each trial's old image and new image (foil) to their ResMem scores and raises an error if any trial fails to match | One row per recognition trial with `oldResMem`, `oldScene`, `block`, `foilResMem`, `foilFalseResMem` |
| `data_preprocess.py` | Matched trials with `CORRECT` (`CORRECT`, `INCORRECT` or `NO ANSWER`) | `create_binary_accuracy()` drops unanswered trials and codes `correct` as 0/1. `standardize_predictors()` z-scores ResMem predictors (the Python version of MATLAB `zscore`) | Adds `correct`, `oldZ`, `foilRZ`, `foilFZ` |
| `statistical_models/logistic_regression.py` | One participant's preprocessed trials | Logistic regressions (statsmodels): simple (`correct ~ oldZ`), adjusted (adds foil FalseResMem, scene category and block), extended (adds foil ResMem) | Fitted models and printed summaries; adjusted odds ratio for old-image ResMem |
| `statistical_models/GLLM.py` | List of `(stim_file, exp_file)` pairs, one per participant | `build_dataset()` runs load, filter and preprocess for every participant and stacks them. `fit_recognition_glmm()` fits a binomial mixed model (pymer4/lme4): `correct ~ oldResMem + foilFalseResMem + category + block`, with random intercepts for subject (plus a ResMem slope), old image and new image. ResMem is scaled per 0.1 units | Fitted model, table of log-odds, odds ratios, 95% CIs, z and p, and the trial-level data |
| `data_visualization.py` | Trial data, and the fitted GLMM for the second plot | `visualize_accuracy_by_quartile()` and `plot_resmem_glmm()` (see Figures) | PNG figures |
| `foils_correlation.py` | `memorability_scores.csv` and one participant's behavioral CSV | Checks whether `ResMem` and `FalseResMem` are correlated, across the whole image pool, by category, and for the foils a participant actually saw | Printed Pearson and Spearman correlations |

### Neural analysis (`memorability_analysis_neural/`)

| Module | Input | What it does | Output |
|---|---|---|---|
| `load.py` | Paths to `*_allstim.csv`, `*_Hummingbird_*.csv`, `checked.set` and the `.vmrk` file | `load_data()` reads both CSVs. `load_vmrk_codes()` reads the trigger code of every original BrainVision marker. `load_eeg_structure()` reads the EEGLAB epoch and reject fields. `load_epochs()` reads the epoched EEG with MNE | `stim` and `raw` DataFrames, `{marker number: code}`, EEGLAB structure, MNE epochs |
| `filter.py` | `raw`: `OLDITEM`/`NEWITEM`, `Cate_OLDITEM`/`Cate_NEWITEM`, `TARGET_LOC`/`Cate_TARGET_LOC`, `Cate_CONDITION`, `OLDITEM_CATEGORY`, `CORRECT`/`Cate_CORRECT`; `stim`; EEG structure and markers | `select_main_trials()` keeps main recognition or categorization trials in presentation order and finds the old image's side and role (target or distractor). `match_stimulus_scores()` joins old and new images to their scores (new images: `recognition_new` or `categorization_new`). `epoch_trial_ordinals()` uses each epoch's BrainVision marker number (`bvmknum`) to find which original trial it is, and drops epochs still marked as artifacts. `match_epochs_to_trials()` keeps one trial per clean epoch and raises an error if the EEG markers and behavioral trials do not line up | One row per clean epoch with `old_side`, `old_is_target`, `correct`, `old_ResMem`, `new_ResMem`, `new_FalseResMem`, `old_scene`, `block` |
| `data_preprocess.py` | Matched trials and clean epochs | `select_epoch_data()` baselines (−200–0 ms) and extracts µV data. `compute_trial_measures()` computes single-trial r-CDA (contralateral − ipsilateral to the old image; PO7/PO8, 250–450 ms; robustness: PO7/PO8, 250–800 ms, the preprint's full window) and FN400 (Fz/F3/F4, 250–500 ms). `select_correct_trials()` keeps correct trials. `prepare_predictors()` centers and scales ResMem (per 0.1) and FalseResMem (per 0.01), centers block, and sum-codes category (indoor = +0.5) and role (target = +0.5) | Adds `rcda`, `rcda_PO_250_800`, `fn400`, waveforms, `OldResMem`, `NewResMem`, `NewFalseResMem`, `OldCategory`, `Role`, `Block`, `SumResMem` |
| `statistical_models/LMM.py` | `{subject: dict(set, vmrk, behavior, allstim)}` | `build_dataset()` runs load, filter and preprocess for every participant and phase. `fit_neural_models()` fits LMMs (pymer4/lme4, REML, Satterthwaite df) with random intercepts for subject (plus a ResMem slope), old image and new image | Fitted models, fixed-effect tables (CSV) and trial-level data |
| `data_visualization.py` | Fitted models, categorization trials and the epoch time axis | `plot_primary_rcda()` and `plot_secondary_fn400()` (see Figures) | PNG figures |

**Neural models** (categorization trials unless noted; covariates: new-image FalseResMem, old-image category, block):

| Question | Model |
|---|---|
| Primary | `rcda ~ OldResMem + NewFalseResMem + OldCategory + Block + Role + (1 + OldResMem \| subject) + (1 \| old_img) + (1 \| new_img)` |
| Secondary (slopes) | `fn400 ~ OldResMem + NewResMem + NewFalseResMem + OldCategory + Block + Role + random effects` |
| Secondary (test) | `fn400 ~ OldResMem + SumResMem + ...`: the `OldResMem` coefficient is the old − new slope difference |
| Positive control | `rcda ~ OldResMem + NewFalseResMem + OldCategory + Block + random effects` (recognition) |
| Robustness | Primary model with the preprint's full window, PO7/PO8 250–800 ms (`rcda_PO_250_800`) |

## Figures

Both behavioral figures are made in `memorability_analysis_behavioral/data_visualization.py` from the preprocessed trial data (`oldResMem`, `correct`) and are saved by the notebook.

1. **Accuracy by ResMem quartile** (`recognition_resmem_quartiles.png`). Old images are split into four equal-sized groups by ResMem score (Q1 lowest to Q4 highest). Each bar is the percentage of correct recognition trials in that group. It is a descriptive check made from one participant's data.
2. **GLMM prediction plot** (`ResMem_Recognition_GLMM.png`). Uses all participants and the fitted binomial GLMM.
   - x-axis: old-image ResMem score. y-axis: probability of a correct response.
   - Solid line: population-averaged model prediction. Dark band: approximate 95% confidence interval. Optional light band: 95% predictive interval for a new participant and image pair.
   - Black points: observed accuracy in equal-count ResMem bins with 95% intervals.
   - Gray ticks (rug), labeled in the legend: each tick is one raw trial placed at its old image's ResMem score. Ticks along the top ("Correct trials") are correct responses (y = 1), and ticks along the bottom ("Incorrect trials") are incorrect responses (y = 0). Where the top ticks are denser than the bottom ticks, accuracy is higher, which is what the fitted curve summarizes.
   - Text box: effect of ResMem as log-odds (β), odds ratio per 0.1 ResMem, 95% CI and p. The foil FalseResMem and block are held at their means, and scene category is averaged.

Both neural figures are made in `memorability_analysis_neural/data_visualization.py` from the correct categorization trials and the fitted LMMs. ERP amplitude axes are plotted negative up.

3. **Primary question** (`Fig1_primary_rCDA.png`).
   - Panel A: grand-average r-CDA (PO7/PO8, contralateral − ipsilateral to the old image) over time, separately for trials where the old image was the target or the distractor. Lines are averaged within participant first, then across participants (band: ± SEM across participants). The gray area is the analysis window (250–450 ms).
   - Panel B: model-predicted mean r-CDA across old-image ResMem (line, 95% CI band), with observed means in equal-count ResMem bins (± SEM). Text: ResMem effect (b per 0.1 ResMem, 95% CI, p). Other predictors are held at 0 (their mean, or averaged over category and role).
4. **Secondary question** (`Fig2_secondary_FN400.png`).
   - Panel A: grand-average frontal ERP (Fz/F3/F4) for the lowest and highest thirds of old-image ResMem. This split is descriptive only; the model uses continuous ResMem. The gray area is the FN400 window (250–500 ms).
   - Panel B: model-predicted FN400 across old-image ResMem and across new-image ResMem (two lines, 95% CI bands), with observed bin means. Text: old slope, new slope and the old − new contrast (b, 95% CI, p).

### How `plot_resmem_glmm` creates the GLMM figure

```python
fig, ax = dv.plot_resmem_glmm(result, D, filename="ResMem_Recognition_GLMM.png")
```

**Inputs:** `result` is the fitted GLMM and `D` is the trial-level data, both returned by `GLLM.fit_recognition_glmm()`. Optional arguments: `n_samples` (fixed-effect draws, default 1000), `n_random` (random-effect draws, default 1000), `n_bins` (observed-data bins, default 8), `show_predictive` (draw the predictive interval, default `False`), `ylim`, and `seed`.

**Steps:**

1. **Prediction grid.** Build 160 evenly spaced old-image ResMem values from the minimum to the maximum in `D`, and convert them to the model's units (centered, per 0.1 ResMem).
2. **Fixed-effect uncertainty.** Draw 1,000 sets of fixed effects (intercept and ResMem slope) from a multivariate normal using the model's estimates and covariance matrix. Each draw gives one logit curve across the grid, with foil FalseResMem, block and scene category held at their average value.
3. **Random effects.** Read the estimated standard deviations for subject (intercept and ResMem slope, with their correlation), old image and new image. Draw one shared set of random effects from them.
4. **Population-averaged curve.** For each fixed-effect draw, add the random effects, apply the inverse logit to get probabilities, and average over the random-effect draws. The mean across fixed-effect draws is the solid line, and the 2.5th–97.5th percentiles form the approximate 95% confidence band. The optional predictive interval is the same calculation for a single subject and image pair, without averaging.
5. **Observed data.** Split the trials into 8 equal-count ResMem bins and compute the proportion correct in each, with a 95% Wilson interval (black points).
6. **Effect text.** Take the ResMem coefficient from the model and report β, the odds ratio per 0.1 ResMem, its 95% CI and the p-value.
7. **Draw and save.** Plot the band, curve, observed points, the correct/incorrect rug and the effect text. Save the figure at 300 dpi to `filename` and return `(fig, ax)`.

## Repository structure

```
Lab Data Collection/
├── Participants/                      # data storage (one folder per participant)
│   ├── Pilot_1/  Q54/  Q55/  Q56/  Q57/
│   │   ├── <ID>_Hummingbird_*.csv     # trial-level behavioral data
│   │   ├── <ID>_allstim.csv           # stimulus ResMem / FalseResMem scores
│   │   ├── *.eeg / .vhdr / .vmrk      # raw EEG (BrainVision)
│   │   ├── checked.set / .fdt         # preprocessed, artifact-rejected epochs
│   │   ├── *_unchecked.set, binlist.txt
│   │   └── *.EDF / .asc / *_eye.mat   # eye-tracking data (EyeLink)
├── data_analysis/                     # data analysis (installable package)
│   ├── setup.py                       # makes the package installable
│   ├── memorability_analysis_behavioral/   # behavioral package
│   │   ├── __init__.py
│   │   ├── load.py
│   │   ├── filter.py
│   │   ├── data_preprocess.py
│   │   ├── data_visualization.py
│   │   ├── foils_correlation.py
│   │   └── statistical_models/
│   │       ├── __init__.py
│   │       ├── logistic_regression.py # single-participant logistic models
│   │       └── GLLM.py                # multi-participant binomial GLMM
│   └── memorability_analysis_neural/       # neural (EEG) package
│       ├── __init__.py
│       ├── load.py
│       ├── filter.py
│       ├── data_preprocess.py
│       ├── data_visualization.py
│       └── statistical_models/
│           ├── __init__.py
│           └── LMM.py                 # r-CDA and FN400 linear mixed models
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

Requires Python 3 with `pandas`, `numpy`, `scipy`, `statsmodels` and `matplotlib`. The GLMM (`GLLM.py`) and the LMMs (`LMM.py`) also need `pymer4`, which requires R with the `lme4` and `lmerTest` packages. The neural package also needs `mne` and `pymatreader`.

## Usage

Open `Notebook/run_notebook.ipynb`, set the paths to the participants' files, and run all cells.

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

Cell 3 runs the neural analysis (LMMs and both figures):

```python
from pathlib import Path
from memorability_analysis_neural.statistical_models import LMM
from memorability_analysis_neural import data_visualization as ndv

P = Path.home() / "Desktop" / "Lab Data Collection" / "Participants"
subject_files = {
    "Q54": dict(set=P / "Q54/checked.set", vmrk=P / "Q54/q54.vmrk",
                behavior=P / "Q54/Q54_Hummingbird_2026-10-28_14h22.52.284.csv",
                allstim=P / "Q54/Q54_allstim.csv"),
    "Q55": dict(set=P / "Q55/checked.set", vmrk=P / "Q55/q55.vmrk",
                behavior=P / "Q55/Q55_Hummingbird_2026-11-01_14h21.38.686_1.csv",
                allstim=P / "Q55/Q55_allstim.csv"),
}

cat, rec, times = LMM.build_dataset(subject_files)
models = LMM.fit_neural_models(cat, rec, random_slope=True, out_dir="Neural_results")
fig1, _ = ndv.plot_primary_rcda(models, cat, times, filename="Fig1_primary_rCDA.png")
fig2, _ = ndv.plot_secondary_fn400(models, cat, times, filename="Fig2_secondary_FN400.png")
```

## Notes

- Large raw EEG and eye-tracking files (`*.eeg`, `*.EDF`) exceed GitHub's file size limit and cannot be committed.
- `foils_correlation.py` currently reads hard-coded paths (`~/Desktop/memorability_scores.csv` and one participant's file).
- The neural pipeline matches epochs to trials through the BrainVision marker number (`bvmknum`) kept in `checked.set`, and stops with an error if the number of onset markers in the `.vmrk` (640 per phase in Q54 and Q55) does not equal the number of behavioral trials.
- Q54 has two behavioral CSVs with the same number of rows (`..._284.csv` and `..._284_1.csv`); the usage example uses the first one. Confirm they are identical.
- With fewer than five participants, subject random effects cannot be estimated reliably; treat neural model fits as a pipeline check. If a model does not converge, use `random_slope=False`.
- The raw EEG includes a photodiode channel (`StimTrak`) that can be used to check the delay between trigger and screen onset.
