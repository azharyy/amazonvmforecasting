# Atomity forecasting notebook starter

Start with `notebooks/01_forecasting.ipynb`. It contains **39 numbered Markdown/code cells**
(19 executable cells), beginning with requirements and explaining each transformation before
its code. The notebook produces the two required forecasts with the 110/24 chronological split.
It is a working investigation starter, not a finished scientific report.

## 1. Put the files in your project

Clone the assignment, or open the clone you already have:

```bash
git clone https://github.com/atomityhq/forecasting-challenge.git
cd forecasting-challenge
```

Extract this starter bundle's contents into that folder. It adds:

```text
requirements.txt
run_notebook.py
notebooks/01_forecasting.ipynb
reports/final_report.md
reports/report_tables.py
reports/evidence/            (tracked evidence snapshots)
tests/run_synthetic_checks.py
.gitattributes
NOTEBOOK_SETUP.md
TESTING.md
```

The bundle preserves the assignment's existing README. Add these entries to your existing
`.gitignore` before running the notebook; the report's five figures stay tracked:

```gitignore
challenge_data/*.gz
challenge_data/SHA256SUMS
challenge_data/DATA_CARD.md
data-v1.tar.gz
reports/generated/*
!reports/generated/*.png
```

No changes to the `cwfc` starter package are required.
The notebook defines the relevant simple utilities directly so you do not need an editable
package install or the starter splitter's unsuitable defaults.

## 2. Requirements

Use **64-bit Python 3.11 or newer** (the assignment's minimum). The recorded runs used Python 3.11.9
on Windows with the exact pins below; see `TESTING.md`. The starter bundle reported an earlier check on
Python 3.12/Linux that was not repeated here.

| Dependency | Pin | Purpose |
|---|---:|---|
| numpy | 2.4.6 | Numerical arrays, metrics and checks |
| pandas | 3.1.0 | CSV processing, aggregation, time ordering and features |
| scipy | 1.17.1 | Single-parameter exponential smoothing optimization |
| scikit-learn | 1.9.1 | StandardScaler and Ridge |
| matplotlib | 3.11.2 | Training and error figures |
| ipykernel | 7.4.0 | The VS Code notebook kernel |

LightGBM, XGBoost, seaborn, Plotly and statsmodels are not needed. Keep them in your existing
environment if other projects need them. `nbformat`/`nbclient` are also not required by this
starter's command-line runner: it executes this Python-only notebook's code cells in order
using the selected Python interpreter, without launching a Jupyter server.

Your complete existing environment was not available for inspection. The first notebook cell
runs `pip check`, prints the actual kernel/interpreter and versions, and exercises NumPy/SciPy/
scikit-learn together. A separate environment avoids conflicts with unrelated packages.

### Windows PowerShell

Run these in the **terminal**, not in an ordinary Python cell:

```powershell
python -m venv .venv    # any 64-bit Python 3.11+; check with: python --version
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ipykernel install --user --name atomity-forecasting --display-name "Python (Atomity forecasting)"
```

These commands use the environment interpreter explicitly, so PowerShell activation is not needed.
If `python --version` reports anything older than 3.11, install a 64-bit Python 3.11+ first; do not
substitute an unknown interpreter silently.

### macOS/Linux

```bash
python3 -m venv .venv   # any 64-bit Python 3.11+
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install --only-binary=:all: -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m ipykernel install --user --name atomity-forecasting --display-name "Python (Atomity forecasting)"
```

### Reusing your current environment

If you prefer the environment from your package list, check it first:

```bash
python --version
python -m pip check
python -m pip install --only-binary=:all: -r requirements.txt
python -m ipykernel install --user --name atomity-forecasting --display-name "Python (Atomity forecasting)"
```

Already installed matching pins are reused. If `pip check` reports a conflict, use the separate
environment rather than changing unrelated project dependencies. When installing from a
notebook, `%pip install -r requirements.txt` targets its kernel; restart the kernel after any
numerical-library changes. The tested workflow installs in the terminal before opening the notebook.

## 3. VS Code

Install Microsoft's Python and Jupyter extensions if absent. If the `code` command is available:

```bash
code --install-extension ms-python.python
code --install-extension ms-toolsai.jupyter
```

Open the project folder, open `notebooks/01_forecasting.ipynb`, click **Select Kernel**, and
choose **Python (Atomity forecasting)**. Confirm that the first code cell prints the `.venv`
interpreter you intended. Run cells from top to bottom. Markdown cells explain the methods,
assumptions, acceptance rules and limitations; code cells perform the work.

## 4. Dataset

If you already extracted `data-v1`, keep its four files under `challenge_data/`. The notebook
verifies all content checksums. If none of the four files exist, it downloads only the challenge
archive, verifies its pinned SHA-256, and extracts the named files. An incomplete data directory
fails with a useful message instead of silently overwriting existing files.

Manual option:

```bash
curl -L --fail https://github.com/atomityhq/forecasting-challenge/releases/download/data-v1/data-v1.tar.gz -o data-v1.tar.gz
mkdir challenge_data
tar -xzf data-v1.tar.gz -C challenge_data
```

On PowerShell, use `curl.exe` if `curl` is an alias. Skip `mkdir` when the directory already exists.
The notebook verifies the hashes in either case. It never downloads omitted Azure records.

## 5. What the notebook does

1. Check the environment and freeze split/features/model-selection rules.
2. Verify release provenance and inspect the actual data card.
3. Audit schema, keys, duplicates, gaps, CPU bounds and metadata coverage.
4. Construct both targets; keep only the first 110 target rows in development variables.
5. Independently recalculate training aggregates and test hand-calculated fixtures.
6. Describe training utilization, VM tails, category/core segments and short-lag dependence.
7. Document availability; construct shifted lags and a past-only rolling mean.
8. Compare persistence, SES and three Ridge penalties on 24-step expanding-window folds.
9. Evaluate MAE/RMSE, zero-error baselines, horizons and peaks.
10. Check origin, latency, peak-threshold and leave-one-window sensitivity.
11. Compare a utilization-review alert with persistence and trivial alert policies.
12. Test future-value perturbations and a two-VM, offset-timestamp fixture.
13. Freeze the configuration and generate 24 predictions with output-contract checks.
14. Evaluate the holdout only through `run_notebook.py --evaluate-holdout`, against a run frozen earlier.

The feature set and acceptance rule are fixed recommendations, not assignment requirements.
Automatic feature selection is deliberately omitted because 110 time points and three validation
windows do not support a large feature search. SES uses an explicit level recursion and SciPy;
Ridge uses a scaler fitted only on each training prefix. Recursive forecasts feed predictions
back into later features rather than substituting future observations.

## 6. One-command reproduction

From the project root, Windows:

```powershell
.\.venv\Scripts\python.exe run_notebook.py --data challenge_data --output reports/generated
```

macOS/Linux:

```bash
.venv/bin/python run_notebook.py --data challenge_data --output reports/generated
```

The runner executes the notebook's Python code cells in a fresh process; inline displays become
terminal output and saved figures/CSVs remain available. It intentionally does not create an
executed `.ipynb`. Use VS Code for the interactive notebook experience.

The output directory contains `predictions.csv`, `frozen_run.json`, a runtime dependency snapshot,
validation predictions/metrics, segment/error/sensitivity/leakage tables, policy and headroom results and
figures. The runner also writes the submission copy `predictions.csv` at the repository root and verifies
it against the frozen hash, so no manual copy or edit is needed. A data-v1 run also saves a compact,
tracked snapshot under `reports/evidence/<manifest digest>/`. `--predictions PATH` and `--evidence DIR`
write those elsewhere, for example for a smoke test.

`frozen_run.json` records the source digests (every notebook code cell, outputs excluded, plus
`requirements.txt` and `run_notebook.py`), the configuration with its selection and alert-cost rules, the
initial and final model decisions, data hashes, package versions, the predictions hash and fit
diagnostics. Save the notebook before freezing so these digests describe your code. Before a run writes
anything, the previous `frozen_run.json` and all of its evidence are archived under `frozen_history/`.

## 7. Open the holdout only after freezing

Evaluation is a separate command run in a fresh process after freezing: append `--evaluate-holdout` to the
reproduction command, with the same `--data` and `--output`. There is no switch inside the notebook, and
a kernel cannot evaluate: the notebook refuses unless `run_notebook.py` supplies the code it executes, since
a kernel may run unsaved edits. In VS Code the last cell only reports that the holdout is unopened.

The evaluation consumes the frozen run. Before parsing any data row it compares the data, source (the
executed code cells, `requirements.txt`, `run_notebook.py`; line endings ignored), configuration and
prediction fingerprints with the original `frozen_run.json` and refuses any change, even one that leaves
the predictions identical. It also refuses archived copies and a missing or changed submission copy. It
reruns development in a temporary directory, requires the frozen predictions and every recomputable
manifest field to be reproduced, writes `holdout_opened.json` before any holdout value is used (also in the
run's tracked evidence snapshot), and then scores the frozen `predictions.csv`. A repeat for the same frozen
run is labelled as such and shows the saved results. After opening, the output directory is sealed against
further development runs. After seeing holdout outcomes, do not tune models, features or alert thresholds
against them; a later run is not a newly untouched test.

## 8. Report

The 4–6-page report is `reports/final_report.md`. Its tables are generated from the tracked evidence
snapshot it cites by `reports/report_tables.py`; `--check` also verifies the key numbers in the text. It
covers constant count under complete-trace selection, unweighted utilization versus CPU demand, scarce
validation windows, failures, and the bounded operational interpretation. Neither the alert cost scenario
nor the descriptive safety margin establishes capacity, provisioning risk, resource savings or production
readiness. The final holdout evaluation remains unopened.

## Sources

- [Assignment contract](https://github.com/atomityhq/forecasting-challenge/blob/main/ASSIGNMENT.md)
- [Dataset contract](https://github.com/atomityhq/forecasting-challenge/blob/main/DATASET.md)
- [Submission contract](https://github.com/atomityhq/forecasting-challenge/blob/main/SUBMISSION.md)
- [Challenge release](https://github.com/atomityhq/forecasting-challenge/releases/tag/data-v1)
- [Azure V2 semantics](https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetV2.md)
- [VS Code notebook setup](https://code.visualstudio.com/docs/datascience/jupyter-notebooks)
- [scikit-learn installation](https://scikit-learn.org/stable/install.html)
- [SciPy scalar optimization](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize_scalar.html)
