# Atomity — Cloud Workload Forecasting

Forecasts `active_vm_count` and `aggregate_cpu_utilization` for the final 24 five-minute timestamps of the
`data-v1` Azure VM release, using only the first 110 timestamps. The analysis is
`notebooks/01_forecasting.ipynb`; the findings are in [`reports/final_report.md`](reports/final_report.md).
Governing contract: [`atomityhq/forecasting-challenge@6e5ac0e`](https://github.com/atomityhq/forecasting-challenge/tree/6e5ac0e4d2f1d81fab0903ce0a974037745db35b)
(`ASSIGNMENT.md`, `DATASET.md`, `SUBMISSION.md`).

For an explanation of the full design and its challenge-specific tradeoffs, read
[`CODE_WALKTHROUGH.md`](CODE_WALKTHROUGH.md), then the XML-tagged comments in the
notebook and Python files. They explain both how each function works and why the
pipeline uses these data, validation, model-selection and evidence rules.

## 1. Environment

Clone the repository and work from its root:

```bash
git clone https://github.com/azharyy/amazonvmforecasting.git
cd amazonvmforecasting
```

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

Optional, to use the notebook in VS Code: install Microsoft's **Python** (`ms-python.python`) and **Jupyter**
(`ms-toolsai.jupyter`) extensions if absent, for example with `code --install-extension ms-python.python` and
`code --install-extension ms-toolsai.jupyter`. Register the environment as a kernel with
`<venv python> -m ipykernel install --user --name atomity-forecasting --display-name "Python (Atomity forecasting)"`.
Open the project folder, open `notebooks/01_forecasting.ipynb`, click **Select Kernel** and choose
**Python (Atomity forecasting)**. The first code cell prints the interpreter it runs, so you can confirm it is
the `.venv` one; then run the cells from top to bottom. The command in section 3 needs no Jupyter server.

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
fresh process, about 30–45 s on the recorded machine. Every single-run self-check runs as part of it. If any
release row, holdout rows included, breaks a validation rule, the run stops before any forecast is written.
Otherwise it develops and freezes, and writes:

- **`predictions.csv`** at the repository root, the submission file. It is copied from the frozen run and
  verified against the SHA-256 recorded in `frozen_run.json`. Never edit it by hand.
- **`reports/generated/`**, the full evidence: `frozen_run.json`, `environment.lock.txt`, validation
  predictions and summaries, selection gates, sensitivity and leakage checks, the alert-policy and headroom
  tables, and the five figures used by the report. Everything here except the figures is git-ignored.
- **`reports/evidence/<manifest digest>/`**, a small tracked snapshot of a data-v1 run: the manifest
  (configuration with the selection, peak and alert-cost rules; initial and final decisions; data, source and
  environment-lock digests; package versions; prediction digest), `environment.lock.txt`, `predictions.csv`
  and the compact model, window, gate, sensitivity, policy, headroom, leakage and workload summaries (about
  26 KB). A snapshot is written once and never replaced. The manifest also records the git state, so a rerun
  after any change, a commit included, gets a new directory. Smoke datasets get none.
- **`reports/generated/frozen_history/<digest>/`**: before a run writes anything, the previous frozen run
  and all of its evidence are archived here. Archived files are never replaced or overwritten by a partial
  copy.

`.\.venv\Scripts\python.exe reports/report_tables.py --check` (`.venv/bin/python` on macOS/Linux) then
confirms that every table in `reports/final_report.md` and the key numbers quoted in its prose equal the
values in the snapshot the report cites, that this snapshot describes both the submitted `predictions.csv`
and its own copy, and that no table sits outside the generated blocks. Without `--check` it rewrites the
tables from that snapshot.

To refresh the report's evidence after a source change:

1. Commit the change, so the manifest records a clean `git_commit`.
2. Freeze with the command above. It prints `Evidence snapshot: reports/evidence/<16 hex>`.
3. Cite that directory in `reports/final_report.md`, in its "tracked snapshot `reports/evidence/<16 hex>/`"
   sentence.
4. Run `.\.venv\Scripts\python.exe reports/report_tables.py` to regenerate the tables, and fix any quoted
   number it lists.
5. Run it again with `--check`.
6. Commit the new snapshot, `predictions.csv` and the report.

Options:

- `--predictions PATH` and `--evidence DIR` write the submission copy and the snapshot elsewhere, for example
  during a smoke test.
- `--evaluate-holdout` evaluates the run already frozen in `--output` (section 5). Leave it off.

Prediction and data digests are of the exact bytes written. Every generated CSV, JSON and text file is written
with LF line endings whatever the operating system, so the same values give the same bytes and digests on
Windows, macOS and Linux; snapshots frozen before this rule keep their original CRLF bytes. `.gitattributes`
keeps git from changing the line endings of `predictions.csv` and `reports/evidence/`, so their recorded
digests hold on every checkout. Source digests ignore line endings, because git may rewrite those of
`run_notebook.py` and `requirements.txt`.

## 4. Main modeling decisions

| Decision | Choice and reason |
|---|---|
| Targets | `active_vm_count(t)` = distinct VMs with a valid `avg_cpu` in [0,100] at *t*; idle 0% VMs count. `aggregate_cpu_utilization(t)` = unweighted mean of those VMs' `avg_cpu`, in percent. Invalid averages leave both numerator and denominator; conflicting duplicates, contradictory min/avg/max and grid gaps stop the run; nothing is imputed. |
| Split | Full target series first, then the chronological split (ASSIGNMENT §3B): development 0–32,700 s (110 keys), forecast template 33,000–39,900 s (24 keys, taken from the timestamp grid). |
| Isolation | Both targets are built for all 134 timestamps with fixed rules, then split 110/24; the 24 holdout values are discarded immediately and never shown, saved, or used for cleaning, diagnostics, fitting or selection. Only the separate evaluation command scores them. A holdout row breaking a validation rule stops the freeze before any forecast is written. Quality, coverage and metadata audits use development rows, whose rebuilt targets must equal the first 110 rows exactly; metadata deletion times are never loaded during development. |
| Candidates | Persistence, simple exponential smoothing, Ridge autoregression (α ∈ {1, 10, 100}), with lags 1–3 and a trailing 6-bin mean. Recursive 24-step forecasts, refit per origin, with no metadata or calendar inputs. |
| Validation | Expanding window, origins after 38/62/86 points, three non-overlapping 24-step blocks. MAE, pooled RMSE, relative improvement (N/A for zero-error baselines), peak and horizon errors. These are development estimates. |
| Selection rule (predeclared) | At least 5% MAE gain, at least 2 of 3 window wins, RMSE not worse and, for CPU (the only target with peaks), peak MAE at most 5% worse on at least 3 peak points; then origin-shift, one-bin-delay and leave-one-window-out checks, falling back to persistence if any fails. The peak guard's CPU-only scope was corrected after the rules were written; nothing changes on data-v1, where the count's persistence forecast is exact. |
| Result | **Persistence for both targets.** Count is constant (exact tie at zero error). Ridge (α=1) had 17.6% lower pooled CPU MAE but lost its advantage with window 62 left out and with a one-bin delay. |
| Operational policy | The prefix-P90 review alert did not beat always-alert in the three development windows (two events). Costs are illustrative units, not demonstrated savings. The 0.7 pp margin that covered every development error is descriptive, not calibrated. The unweighted mean measures no physical capacity, so no provisioning risk or cost is claimed. |

## 5. Final holdout

The final 24 observed targets have **not** been scored. Development builds them with the rest of the series
and discards them at the split (section 4). Evaluation is a separate command that consumes a run frozen
earlier by the section-3 command. Never run it to "see how it does" during development:

```powershell
.\.venv\Scripts\python.exe run_notebook.py --data challenge_data --output reports/generated --evaluate-holdout
```

What it does, in order:

1. Before any cell runs or any directory is created, the runner refuses an output directory without
   `frozen_run.json`, an archived copy (inside `frozen_history/` or the evidence directory), and a missing
   submission copy (`--predictions`) or one that differs from the frozen prediction digest.
2. Before any data row is parsed, it compares four fingerprints with the original
   `reports/generated/frozen_run.json`: the data file digests, the source digests (the notebook code cells
   exactly as the runner executes them, evaluation included, plus `requirements.txt` and `run_notebook.py`,
   line endings ignored), the configuration and the prediction digest. Any difference stops the run, even if
   the predictions would come out identical; so does an opening record written for a different frozen run. It
   never writes a new manifest.
3. It reruns development in a temporary directory, so the output directory's evidence stays as frozen, and
   requires the rerun to reproduce the frozen predictions and every recomputable manifest field: decisions,
   development audit, fit diagnostics, alert threshold and alert.
4. The first evaluation writes `holdout_opened.json` before any holdout value is used: in the output
   directory and, for a data-v1 run, in its tracked evidence snapshot, which every copy of that frozen run
   shares. It then rebuilds the full target series with the same helper as development, asserts that its
   first 110 rows equal the development targets exactly, runs the deferred release-wide audit, and scores the
   frozen `predictions.csv` against persistence (`holdout_*.csv`, `holdout_data_audit.json`).
5. A repeat for the same frozen run, found through either opening record, prints a **REPEAT** notice with
   the first opening time and shows the saved results without rescoring the holdout. If a first evaluation
   stopped before saving its results, the repeat recomputes them, still labelled REPEAT. An opening record is
   never rewritten.

Once the holdout is opened, the output directory is sealed: the development command refuses to run there, so
the frozen run, its evidence and the opening record stay as they were. Develop further only in a new
`--output` directory, and do not present anything evaluated afterwards as a first test of this holdout. These records
cannot stop someone from freezing and evaluating a changed procedure elsewhere; they make the original
evaluation, and any repeat of the same frozen run, identifiable.

Kernels never evaluate. There is no switch to edit, and the notebook refuses evaluation unless
`run_notebook.py` supplies the code it is executing, because a kernel may run edits that were never saved.

## 6. Repository layout

```text
notebooks/01_forecasting.ipynb   analysis, self-checks, frozen forecast, holdout evaluation cell
run_notebook.py                  one-command runner (fresh process, no Jupyter server)
requirements.txt                 exact pins
reports/final_report.md          final report (figures in reports/generated/)
reports/report_tables.py         regenerates/checks the report's tables and quoted numbers
reports/evidence/<digest>/       tracked compact evidence of each frozen data-v1 run
tests/run_synthetic_checks.py    multi-run synthetic checks (constant release, freeze/evaluate protocol)
predictions.csv                  submission file written by the runner
TESTING.md                       what was executed and verified, and what was not
CODE_WALKTHROUGH.md              design walkthrough, from the challenge down to each function
src/                             unused package stub; the analysis lives in the notebook
```

Single-run self-checks are notebook cells, so the reproduction command always runs them. Behaviour that needs
several runs (a constant-CPU smoke release, freezing then evaluating, refused changes, repeats, a release with
an invalid holdout row refused at freeze) is checked on
synthetic data by `.\.venv\Scripts\python.exe tests/run_synthetic_checks.py`, which works on a temporary copy
of the project and uses synthetic releases only, never `challenge_data`. [`TESTING.md`](TESTING.md) lists every check and what was run.
