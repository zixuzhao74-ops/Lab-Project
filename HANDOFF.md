# Handoff: EEG / eye-tracking artifact rejection (Q54–Q59)

Last updated: 2026-11-20. This is a working log of the EEG preprocessing and artifact-rejection review, plus what is still to do. It complements `README.md`, which describes the analysis package. Preprocessing happens outside this package (see "Where things live").

## Goal

Produce a `checked.set` (epoched, artifact-rejected) for each participant, to feed the neural analysis (r-CDA at PO7/PO8, and a fronto-central ROI). The automatic rejection script marks too many epochs for some participants, so each `*_unchecked.set` is reviewed and clearly harmless marks are un-rejected before saving `checked.set`.

**Analysis electrodes:** Fz, FC1, FC2, F3, F4 (fronto-central), PO7, PO8 (parieto-occipital, r-CDA). Cz, CP2, P7 and others are not used. Rejection decisions below are made on these channels plus the gaze channels.

## Where things live

| Item | Location |
|---|---|
| Rejection script `eegreject.m` | In the EEGLAB 2026.1.0 folder, not in this repo. A copy should be added here (see To do). |
| Participant data | `Participants/<ID>/` (not in the repo; raw `.eeg`/`.EDF` are git-ignored) |
| Per-participant files used | `q<N>.vhdr/.vmrk/.eeg`, `<ID>_*.asc` and `_eye.mat`, `q<N>_unchecked.set/.fdt`, `checked.set/.fdt` (when done), `binlist.txt` |
| Analysis scripts | `data_analysis/` (see `README.md`) |

## Setup that was needed

- **MATLAB R2026b** (macOS, Apple silicon), **EEGLAB 2026.1.0**.
- **EEGLAB plugins:** `bva-io` (`pop_loadbv`, reads `.vhdr`), `ERPLAB` (`pop_basicfilter`, `pop_binlister`, `pop_art*`, `pop_syncroartifacts`), `EYE-EEG 1.01` (`parseeyelink`, `pop_importeyetracker`), plus the defaults (ICLabel, clean_rawdata, dipfit, firfilt, EEG-BIDS).
- **MATLAB toolbox:** Signal Processing Toolbox (needed by `pop_basicfilter`; without it the filter step prints an error and the data are left unfiltered).
- **Java:** R2026b no longer bundles Java. ERPLAB's `binlister_smart` needs it. Fix used: install the "MATLAB Support for OpenJDK" add-on (it configures `jenv`); a Temurin 17 JDK was also installed.
- `eegreject.m` calls `clearvars` and `eeglab` at the top, and writes `log.txt` to the current folder.

## What the script does (key settings)

Epochs −250 to 850 ms around image onset; rejection window −200 to 800 ms; baseline −200 to 0 ms; bandpass 0.01–30 Hz; mastoid re-reference (`TP9` only, `0.5 * TP9`); resample to 500 Hz.

| Test | Setting |
|---|---|
| Gaze distance from fixation | `eyeDistThresh` = 1° (about 46 px) |
| Gaze saccade step | `eyeSaccadeThresh` = 0.5° (about 23 px), 80 ms window, 10 ms step |
| EEG absolute value | `eegAbsThresh` = 100 µV |
| EEG moving-window peak-to-peak | `eegNoiseThresh` = 75 µV, 200 ms window, 100 ms step |
| EEG step | `eegStepThresh` = 60 µV, 250 ms window, 20 ms step |
| EEG linear trend | slope 75 µV over the epoch with R² over 0.3 (`pop_rejtrend`) |
| Flatline | gaze or EEG channel at 0 for 200 ms or more (`pop_artflatline`) |

`noisyElectrodes` (line 36) lists channels ignored by all EEG tests. It has been `{'Fp1','Fp2'}` or `{'Fp1','Fp2','F7','F8'}` during these runs, so `Fp1`/`Fp2` were never tested.

## Participant status

Percentages are marked epochs out of 1,920.

| ID | Marked in unchecked | `checked.set` | Main findings |
|---|---|---|---|
| **Q54** | 359 (18.7%) | Done: 1,645 epochs (275 removed, 84 un-rejected) | `Cz` drift in epochs 1521–1560, `CP2` failing from about 1621–1680, `F4` bad in 1671–1674 and 1678. 15 kept epochs still exceed the script's tests; the clearest are 101, 214, 641, 1427, 1431. |
| **Q55** | 274 (14.3%) | Done: 1,772 epochs (148 removed, 126 un-rejected) | Lab says gaze (pupil) drifts are fine to un-reject. `P7` drifts in 117–119. Three kept epochs still fail a test: 55 (distance 1.66×, step 1.22×), 120, 502. |
| **Q56** | 577 (30.1%) after the eye-file fix | Not made yet | First run marked 100%: eye data were all zeros (see Known issues). Remaining marks are mostly a systematic vertical gaze drift present in 92% of epochs (median about −26 px). |
| **Q57** | 645 (33.6%) | Not made yet | Strong occipital alpha triggers the moving-window test (`PO7` 125 failing epochs). Gaze marks are higher in roughly the first 480 epochs (about 32% vs about 10% later); this may relate to right-eye blocks being labelled as left, but the block-to-epoch mapping is approximate and this is unconfirmed. |
| **Q58** | 700 (36.5%) | Not made yet | Gaze noisier than other participants (step test fails in 32% of epochs; 11% have single-sample spikes). 61 epochs have no gaze data. `CP1` drifts in epochs 1–32 (fading). `FC2`/`FC6`/`P4` fail progressively in 1901–1920. |
| **Q59** | 1,095 (57.0%) | Only `q59_unchecked.set` exists | Gaze failures dominate (saccade-size steps, drifts of 1.5° or more, 124 epochs with no gaze data) and blink-sized frontal transients are frequent. |

## Standards used to decide what to un-reject

Applied to marked epochs; the epoch lists below follow these rules.

1. **EEG:** judged on the seven analysis channels only. Absolute value under 100 µV, step under 60 µV, no trend failure. Moving-window peak-to-peak under 100 µV for Q57 (alpha is acceptable per the mentor); the script default of 75 µV otherwise.
2. **Gaze, if the script's gaze tests failed:** a smooth drift under 1.5° from fixation, with the step test passing, no zero (missing) samples, and no single-sample spike above 0.15°.
3. **Strict vs borderline:** strict also requires the largest change in any 30 ms stretch to be under 0.30° (a saccade moves at least 0.5° in that time). Borderline allows 0.30–0.50°.
4. **Blink sign:** `Fp1`/`Fp2` swing under 80 µV (used for Q56–Q58; dropped for the Q59 re-run because those channels are noisy).
5. **Mentor guidance:** "if the drift is not huge, I'd accept such a trial"; alpha oscillations are fine; crossing `GAZE-X`/`GAZE-Y` traces mean nothing because they are independent channels, so judge by how big the drift is.

## Epoch lists ready to un-reject

Epoch numbers are 1-based positions in the unchecked file. These are recommendations from a recomputation, not yet applied.

**Q56 (226 epochs, strict, drift under 1.5°).** Epochs 27 and 39 are clean drifts but just miss the 0.30° rule (0.32° and 0.33°); 1872 is a clean 1.07° drift missed only because of a start-of-window blip.

```
26, 40-41, 45, 47, 52, 58, 68-69, 92, 106, 114, 126, 128, 141, 150, 152, 154, 164, 174, 187, 197, 203, 206, 217, 223, 232, 242, 288, 326-327, 336, 373, 381, 392, 431, 436, 438, 442, 452, 454, 461, 496, 536, 546, 550, 553, 555, 564, 569, 575, 590, 607, 610, 614, 634, 638-639, 655, 657, 663, 674, 678, 692, 722, 744, 748, 755-756, 758-760, 767, 769-771, 773, 791, 796, 799-800, 821, 823, 836, 838, 840, 851, 858, 860-861, 872, 886-887, 896, 908, 916, 918-919, 930, 932, 937-939, 941, 945, 951, 955, 960, 967, 971, 978, 997, 1001, 1009, 1011-1012, 1036, 1039-1040, 1042, 1074, 1079, 1084, 1088, 1090, 1101, 1112, 1120-1121, 1123, 1128, 1136-1139, 1141, 1151, 1153, 1169, 1173-1174, 1176, 1190, 1194, 1196, 1211, 1213, 1219, 1225, 1236, 1240, 1247, 1266, 1278, 1281, 1297, 1332-1335, 1337-1342, 1366, 1383, 1394, 1406, 1416-1417, 1419-1420, 1425, 1429, 1450, 1453, 1458, 1460, 1505, 1510, 1537, 1539-1540, 1544, 1550, 1558, 1564, 1570, 1595, 1600, 1625, 1627, 1640, 1655, 1660, 1680, 1684, 1698, 1700, 1702, 1720-1721, 1753, 1765, 1768, 1775-1776, 1789, 1800, 1810, 1839, 1848, 1851-1852, 1854, 1864-1865, 1868, 1871, 1875, 1900-1902, 1907
```

**Q57 (250 epochs, analysis channels, moving-window limit 100 µV).** The limit changes the size of the list: 153 epochs at 75 µV, 234 at 90 µV, 250 at 100 µV; confirm 100 µV with the mentor.

```
32, 39, 53, 63, 122, 144, 180-181, 183, 204, 207, 215, 448, 472, 493, 496, 498, 516, 519, 527-528, 542, 553, 555-556, 559, 561-568, 570-573, 575-576, 578-579, 581-592, 595-599, 616, 633, 638, 657, 669, 677, 679, 698, 710, 719, 734, 759, 766, 770, 781-782, 789, 791, 798, 815, 824, 826, 830, 833, 841-842, 844, 869, 871, 896, 907-908, 912, 915, 918, 931, 934, 938, 956, 962, 975, 984, 990, 995, 1011, 1023, 1031, 1035, 1038, 1049, 1052, 1060, 1082-1083, 1087, 1091, 1094, 1096, 1115, 1136, 1142-1143, 1146, 1149, 1151, 1155-1156, 1158, 1163, 1180, 1184, 1186-1188, 1193, 1202, 1204, 1206, 1213, 1233, 1239, 1249, 1260, 1265-1266, 1269, 1288, 1291, 1297, 1310, 1314-1315, 1327-1328, 1333, 1336, 1354, 1359, 1363, 1373, 1375, 1378-1379, 1382, 1385, 1393, 1415, 1426, 1433, 1437, 1446-1447, 1450, 1457, 1465, 1470, 1473, 1475, 1477, 1486-1488, 1490-1491, 1497, 1500, 1502, 1504-1505, 1507, 1509-1510, 1513, 1517, 1525, 1529, 1535-1536, 1554, 1558, 1564, 1569, 1572, 1574, 1576, 1578, 1586, 1601, 1610, 1637, 1654, 1661, 1665, 1677, 1683, 1686-1687, 1691, 1705, 1711, 1719, 1726, 1728, 1731-1732, 1743, 1762, 1778, 1781, 1786, 1788-1790, 1793, 1795, 1806, 1810-1811, 1813, 1835, 1850-1851, 1858, 1861, 1866-1867, 1873, 1878, 1880, 1898, 1913
```

**Q58 (43 epochs: 22 strict + 21 borderline).** Epochs 1901–1920 stay rejected (`FC2`, an analysis channel, drifts there).

```
1-5, 7-12, 14-15, 17, 22-29, 31, 349, 407, 1266, 1520-1521, 1524, 1536, 1538, 1545, 1548-1549, 1551, 1563, 1655, 1778, 1780, 1841, 1847, 1861-1862
```

**Q59 (23 epochs, `Fp1`/`Fp2` ignored; this does not bring Q59 under 30%).**

```
73, 200-201, 261-262, 288, 420, 475-476, 531, 631, 686, 857, 925, 931, 1056, 1095, 1202, 1237, 1360, 1705, 1850, 1910
```

## Known issues and caveats

- **`parseeyelink` fails on mixed layouts.** It reads the column layout from the first `SAMPLES` header and silently deletes every sample line with a different column count (EYE-EEG `parseeyelink.m`, lines 86 and 160–165). Q56's `.asc` starts with 60 empty binocular/left-eye blocks and then 2,160 right-eye blocks, so only the empty 14,212 samples were parsed and every epoch was rejected as flatline. Fix: a repaired copy of the `.asc` (setup blocks' sample lines dropped, headers set to the right-eye format). The original was kept as `Q56_..._.asc.orig`. After the fix: 1.74 million samples, 96.6% valid gaze, same 5,322 sync events. `eyeRecorded` needs no change for single-eye files (columns 2 and 3 are read either way).
- **Mixed left/right eye blocks** also occur in Q57 (120 left, 660 right, 1,440 left blocks) and Q58 (1,800 left, 360 right). The parser labels everything by the first header, so right-eye data are tagged as left. This may inflate gaze marks in those stretches; not yet confirmed.
- **Epochs are baseline-corrected on −200 to 0 ms, including the gaze channels**, so every epoch's gaze baseline is exactly 0. Slow tracker drift across the session cannot be seen in the epoched data; the raw `_eye.mat` is needed.
- **Possible bug in `eegreject.m`** (line 303, the no-eye-tracking branch): `strcmp(noisyElectrodes,{EEG.chanlocs.labels})` should probably be `ismember(...)`, as on lines 270 and 293. Not changed.
- **Recomputed numbers are approximate.** All per-epoch ratios and lists here come from a Python recomputation of the script's tests (reading `.set`/`.fdt` directly), not from ERPLAB's own output. They reproduced every marked epoch for Q54 but also flag some epochs the script did not mark, so treat borderline ratios (within about 10% of a limit) as uncertain.
- **Trend-only marks have no per-channel highlight.** `pop_rejtrend` sets only the epoch flag, so such epochs look yellow with no red channel in the scroll plot.
- **Blinks.** `HEOG`/`VEOG` carry no signal in these recordings (about 0.2 µV), so blinks must be judged from `Fp1`/`Fp2`, zero or wild gaze samples, or missing pupil area.

## To do

1. **Apply the un-reject lists** and save `checked.set` for Q56, Q57, Q58 (and Q59 only if the lab decides to keep it). Untested sketch for scripting this:
   ```matlab
   EEG = pop_loadset('filename','q57_unchecked.set','filepath','<participant folder>');
   EEG.reject.rejmanual(unreject)    = 0;
   EEG.reject.rejmanualE(:,unreject) = 0;
   EEG = pop_rejepoch(EEG, EEG.reject.rejmanual, 0);
   EEG = pop_saveset(EEG, 'filename','checked.set','filepath','<participant folder>');
   ```
   Check that the resulting epoch count matches expectations and that the `.vmrk` marker numbers still map to the behavioral data.
2. **Q57:** rerun with the settings recommended after the analysis-channel review (`noisyElectrodes` = every channel except the seven analysis ones, `eegNoiseThresh = 100`), once the mentor confirms 100 µV. The last rerun used `{'Fp1','Fp2','F7','F8'}` and 75 µV.
3. **Q55 follow-up:** reconsider epochs 55, 120, 502 (kept but still failing). **Q54:** reconsider 101, 214, 641, 1427, 1431.
4. **Q57 sensitivity check:** compute the contralateral-minus-ipsilateral r-CDA with and without the 250 un-rejected epochs. The un-rejected set had about 3.4 µV more positive mean amplitude at PO7/PO8 (400–800 ms) and more alpha than the never-marked epochs. This needs the left/right target side from the behavioral log.
5. **Q59:** decide with the lab whether to exclude it. Under any defensible standard it stays about 55% rejected (needs 519 un-rejects to reach 30%).
6. **Add safeguards to `eegreject.m`:** after `parseeyelink`, warn or stop if the parsed sample count is far below the recording length or valid gaze is under about 80%; warn if the `.asc` mixes eye layouts. Fix the line 303 `strcmp`.
7. **Put `eegreject.m` and the review scripts in this repo.** The review used throwaway Python scripts (loading `.set`/`.fdt`, recomputing tests, building lists) that were not saved; turn them into a documented script so the lists can be regenerated.
8. **Back up repaired inputs** (the Q56 repaired `.asc`) alongside the originals.

## Open questions for the lab or mentor

- What is the cutoff for a drift that counts as "huge"? Epoch lists above assume 1.5°.
- Is a 100 µV moving-window limit acceptable for alpha, or should it be 90 µV?
- Should epochs with small quick gaze movements (0.3–0.5° within 30 ms, but under the step threshold) be kept (the "borderline" group)?
- Is there a maximum acceptable rejection rate per participant (30% has been used as a reference), and what happens to participants above it (Q58, Q59, possibly Q57)?
- Are single-sample gaze spikes treated as tracker glitches or as eye movements?
- Should the eye recorded be fixed to one eye in future sessions (mixed left/right blocks break the parser)?
