# Atomity forecasting notebook starter

Start with `notebooks/01_forecasting.ipynb`. It contains **38 numbered Markdown/code cells**
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
NOTEBOOK_SETUP.md
TESTING.md
```

The bundle preserves the assignment's existing README and `.gitignore`. Add these entries to
your existing `.gitignore` before running the notebook:

```gitignore
challenge_data/*.gz
challenge_data/SHA256SUMS
challenge_data/DATA_CARD.md
data-v1.tar.gz
reports/generated/
```

No changes to the `cwfc` starter package are required.
The notebook defines the relevant simple utilities directly so you do not need an editable
package install or the starter splitter's unsuitable defaults.

## 2. Requirements

Use **64-bit Python 3.12** for the tested profile. Python 3.11+ is required by the assignment;
the pins below were checked together on Python 3.12. All six direct dependencies match your list.

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
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ipykernel install --user --name atomity-forecasting --display-name "Python (Atomity forecasting)"
```

These commands use the environment interpreter explicitly, so PowerShell activation is not needed.
If `py -3.12` is unavailable, install 64-bit Python 3.12 first; do not substitute an unknown
interpreter silently.

### macOS/Linux

```bash
python3.12 -m venv .venv
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
14. Leave the final holdout-evaluation cell disabled until you deliberately open it.

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
validation predictions/metrics, segment/error/sensitivity tables, policy results and figures.
Copy the generated prediction file to the repository root for submission; do not edit its values.

Windows:

```powershell
Copy-Item reports/generated/predictions.csv predictions.csv
```

macOS/Linux:

```bash
cp reports/generated/predictions.csv predictions.csv
```

`frozen_run.json` records development-code digests (excluding notebook outputs and the optional
evaluation cell), the configuration, model decisions, data hashes, package versions, predictions
hash and fit diagnostics. Save the notebook before freezing so these digests describe your code.

## 7. Open the holdout only after freezing

For interactive evaluation, change only the final code cell's `EVALUATE_FROZEN_HOLDOUT` to `True`
and run that cell. The source digest excludes this evaluation cell, so this switch does not
invalidate the development-code digest. Outputs/execution counters are also excluded.

For the command-line equivalent, append `--evaluate-holdout` to the reproduction command.
It recomputes the same predeclared training-only pipeline, freezes predictions, then evaluates
them once. Keep the original opening record. After seeing holdout outcomes, do not tune models,
features or alert thresholds against them. A later run is not a newly untouched test.

## 8. Remaining assignment work

Review the generated evidence and write the required 4–6-page report. Explain constant count
under complete-trace selection, unweighted utilization versus CPU demand, scarce validation
windows, failures, and the bounded operational interpretation. This starter does not claim
that an alert cost scenario establishes resource savings or production readiness.

## Sources

- [Assignment contract](https://github.com/atomityhq/forecasting-challenge/blob/main/ASSIGNMENT.md)
- [Dataset contract](https://github.com/atomityhq/forecasting-challenge/blob/main/DATASET.md)
- [Submission contract](https://github.com/atomityhq/forecasting-challenge/blob/main/SUBMISSION.md)
- [Challenge release](https://github.com/atomityhq/forecasting-challenge/releases/tag/data-v1)
- [Azure V2 semantics](https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetV2.md)
- [VS Code notebook setup](https://code.visualstudio.com/docs/datascience/jupyter-notebooks)
- [scikit-learn installation](https://scikit-learn.org/stable/install.html)
- [SciPy scalar optimization](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize_scalar.html)
