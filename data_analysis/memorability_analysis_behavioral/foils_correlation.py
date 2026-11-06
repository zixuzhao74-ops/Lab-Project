import pandas as pd, ntpath
from pathlib import Path

INPUTDIR = Path.home() / "Desktop"
DATADIR = Path('Lab Data Collection') / Path('Participants') / Path('Q54')

scores = pd.read_csv(INPUTDIR / "memorability_scores.csv")
data   = pd.read_csv(INPUTDIR / DATADIR / "Q54_Hummingbird_2026-10-28_14h22.52.284.csv")

# 1) Whole pool, and by category
for name, x in [("all", scores)] + list(scores.groupby("Folder")):
    print(name, len(x),
          "Pearson r =", round(x.ResMem_Score.corr(x.FalseResMem_Score), 3),
          "Spearman rho =", round(x.ResMem_Score.corr(x.FalseResMem_Score, method="spearman"), 3))

# 2) The foils this participant actually saw in recognition (main blocks only)
rec = data[data.OLDITEM.notna() & (data.SESSIONTYPE == "main")].copy()
rec["new_file"] = rec.NEWITEM.map(lambda p: ntpath.basename(str(p)))
foils = rec.merge(scores, left_on="new_file", right_on="filename", how="left")
print("matched foils:", foils.ResMem_Score.notna().sum(), "of", len(foils))
print("foil r =", round(foils.ResMem_Score.corr(foils.FalseResMem_Score), 3))