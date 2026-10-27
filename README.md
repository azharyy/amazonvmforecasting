# Atomity — Cloud Workload Forecasting

Forecasts `active_vm_count` and `aggregate_cpu_utilization` for the final 24 five-minute timestamps of the
`data-v1` Azure VM release, using only the first 110 timestamps. The analysis is
`notebooks/01_forecasting.ipynb`; the findings are in [`reports/final_report.md`](reports/final_report.md).
Governing contract: [`atomityhq/forecasting-challenge@6e5ac0e`](https://github.com/atomityhq/forecasting-challenge/tree/6e5ac0e4d2f1d81fab0903ce0a974037745db35b)
(`ASSIGNMENT.md`, `DATASET.md`, `SUBMISSION.md`).

## 1. Environment

Use 64-bit Python 3.11 or newer. The recorded runs used Python 3.11.9 on Windows. `requirements.txt` pins the
six direct dependencies exactly: numpy, pandas, scipy, scikit-learn, matplotlib and ipykernel.

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

```bash
# macOS / Linux
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install --only-binary=:all: -r requirements.txt
.venv/bin/python -m pip check
```

Optional, to use the notebook in VS Code: run
`<venv python> -m ipykernel install --user --name atomity-forecasting --display-name "Python (Atomity forecasting)"`,
then pick that kernel. The command below needs no Jupyter server.

## 2. Dataset location

Put the `data-v1` release in `challenge_data/`:

```text
challenge_data/
├── vm_cpu_readings.csv.gz
├── vm_metadata.csv.gz
├── DATA_CARD.md
└── SHA256SUMS
```

To fetch it manually, run `curl -L --fail -o data-v1.tar.gz https://github.com/atomityhq/forecasting-challenge/releases/download/data-v1/data-v1.tar.gz`
and then `mkdir challenge_data && tar -xzf data-v1.tar.gz -C challenge_data`. On PowerShell use `curl.exe`.

If `challenge_data/` is empty, the run extracts `data-v1.tar.gz` from the repository root, downloading it
first if it is missing. It verifies the archive SHA-256 (`d04d402a…caeb`) before extracting. Every run checks
the files against `SHA256SUMS` and against data-v1 digests pinned in the notebook. A directory without
`SHA256SUMS`, such as a reviewer's smoke dataset, still runs, with a printed **unverified / not data-v1**
warning recorded in `frozen_run.json`. Any dataset must have the release grid: 134 timestamps, 300 s apart.
Any number of VMs works.

## 3. Generate `predictions.csv` and the evidence (one command)

From the repository root:

```powershell
.\.venv\Scripts\python.exe run_notebook.py --data challenge_data --output reports/generated
```

On macOS/Linux, use `.venv/bin/python` instead. The runner executes the notebook's code cells in order in a
fresh process, about 30 s on the recorded machine. Every self-check runs as part of it. It writes:

- **`predictions.csv`** at the repository root, the submission file. It is copied from the frozen run and
  verified against the SHA-256 recorded in `reports/generated/frozen_run.json`. Never edit it by hand.
- **`reports/generated/`**, the supporting evidence:
  - `frozen_run.json` (configuration, decisions, data/source digests, versions, development-only audit)
  - `environment.lock.txt`
  - validation predictions and summaries, `selection_gates.csv`, sensitivity and leakage checks
  - the alert-policy tables
  - five figures used by the report

  Everything here except the figures is git-ignored.
- **`reports/generated/frozen_history/<digest>/`** holds every earlier frozen run, archived before it would be
  overwritten. Archived files are never replaced.

Options:
- `--predictions PATH` writes the submission copy elsewhere, for example during a smoke test.
- `--evaluate-holdout` opens the final holdout once, after freezing. Leave it off.

## 4. Main modeling decisions

| Decision | Choice and reason |
|---|---|
| Targets | `active_vm_count(t)` = distinct VMs with a valid `avg_cpu` in [0,100] at *t*; idle 0% VMs count. `aggregate_cpu_utilization(t)` = unweighted mean of those VMs' `avg_cpu`, in percent. Invalid averages leave both numerator and denominator; conflicting duplicates, contradictory min/avg/max and grid gaps stop the run; nothing is imputed. |
| Split | Boundary fixed from timestamp keys alone: development 0–32,700 s (110 keys), forecast template 33,000–39,900 s (24 keys). |
| Isolation (stricter than required) | No development step reads holdout targets, quality or per-time VM counts, or metadata deletion times. Full-series construction and the release-wide audit run only in the disabled final-evaluation cell, after freezing. |
| Candidates | Persistence, simple exponential smoothing, Ridge autoregression (α ∈ {1, 10, 100}), with lags 1–3 and a trailing 6-bin mean. Recursive 24-step forecasts, refit per origin, with no metadata or calendar inputs. |
| Validation | Expanding window, origins after 38/62/86 points, three non-overlapping 24-step blocks. MAE, pooled RMSE, relative improvement (N/A for zero-error baselines), peak and horizon errors. These are development estimates. |
| Selection rule (predeclared) | At least 5% MAE gain, at least 2 of 3 window wins, RMSE not worse, peak MAE at most 5% worse; then origin-shift, one-bin-delay and leave-one-window-out checks, falling back to persistence if any fails. |
| Result | **Persistence for both targets.** Count is constant (exact tie at zero error). Ridge (α=1) had 17.6% lower pooled CPU MAE but lost its advantage with window 62 left out and with a one-bin delay. |
| Operational policy | The prefix-P90 review alert did not beat always-alert in the three development windows. Costs are illustrative units, not demonstrated savings. |

## 5. Final holdout

The final 24 observed targets have **not** been opened. Evaluate them only after the notebook, data and
predictions are frozen:

```powershell
.\.venv\Scripts\python.exe run_notebook.py --data challenge_data --output reports/generated --evaluate-holdout
```

The evaluation checks the frozen prediction, data and source hashes, and writes `holdout_opened.json` once,
never overwriting it. It then builds the full target series, asserts that its first 110 rows equal the
development targets, runs the deferred release-wide audit, and scores the frozen predictions against
persistence. Do not tune anything afterwards; a rerun after changes is not an untouched test.

## 6. Repository layout

```text
notebooks/01_forecasting.ipynb   analysis, self-checks, frozen forecast, disabled holdout cell
run_notebook.py                  one-command runner (fresh process, no Jupyter server)
requirements.txt                 exact pins
reports/final_report.md          final report (figures in reports/generated/)
predictions.csv                  submission file written by the runner
TESTING.md                       what was executed and verified, and what was not
NOTEBOOK_SETUP.md                VS Code notebook setup details
src/                             unused package stub; the analysis lives in the notebook
```

Self-checks are notebook cells rather than a separate `tests/` suite, so the reproduction command always runs
them; [`TESTING.md`](TESTING.md) lists them.
