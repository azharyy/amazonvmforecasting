# Validation record

Every item below was **executed** in this checkout on 2026-10-26 unless it is listed under *Not executed*.
The real final 24 targets were never opened.

## Environments

| Name | Interpreter | Packages | Notes |
|---|---|---|---|
| A: project `.venv` | Python 3.11.9, Windows 11 (`Windows-10-10.0.26200-SP0`) | six exact pins plus unrelated extras, 118 in the lock | `pip check` clean |
| B: fresh venv | same interpreter | `pip install --only-binary=:all: -r requirements.txt`, 46 packages | `pip check` clean; no pin changed |

## Commands and observed outcomes

1. **Documented command, environment A:** `.\.venv\Scripts\python.exe run_notebook.py --data challenge_data --output reports/generated`.
   The final run exited 0 in 25 s. It wrote `predictions.csv` (SHA-256 `ce15e40b…7584`, equal to
   `frozen_run.json`). `reports/generated/frozen_history/` keeps the starter's original manifest `a35c3aaf…`,
   whose predictions are identical, plus two manifests from this session's earlier runs.
2. **Clean copy, environment B.** The copy contained only the source files and `data-v1.tar.gz`, with no
   `challenge_data/`, `predictions.csv` or `reports/`. The same command, on the final code, exited 0 in 23 s. The archive was
   verified and extracted byte-identically, and `predictions.csv` matched run 1 byte for byte. 19 of 21
   generated files matched run 1 byte for byte, including every CSV and figure. The other two were
   `environment.lock.txt` (different package set) and the git fields of `frozen_run.json` (the copy is not a
   repository).
3. **Synthetic smoke release** (3 VMs, grid offset to start at 600 s, one idle 0% VM, no `SHA256SUMS` or
   data card), run with `--data <smoke> --output <scratch> --predictions <scratch>`. It exited 0 and printed
   the unverified / not-data-v1 warnings. The forecast keys are the last 24 smoke keys, and the count is 3,
   including the idle VM.
4. **The same smoke release with `--evaluate-holdout`, twice, on the final code.** Both runs exited 0.
   - The full series was built, and its first 110 rows equalled the development targets.
   - The release-wide audit was written: 402 rows, 3 VMs × 134 keys, metadata 3/3.
   - `holdout_opened.json` was written once; its SHA-256 was unchanged after the second run, which printed
     the "not a fresh test" notice and archived the first evaluation's outputs.
   - This exercised the evaluation code on synthetic data only.

## Checks inside the notebook (run by every command above)

- **Release:** archive digest when extracting; content digests against `SHA256SUMS` and against the pinned
  data-v1 digests.
- **Isolation:** the boundary is derived from timestamp keys only; holdout rows are dropped by key before any
  value is used; the audit covers development rows only.
- **Aggregation fixtures with hand-calculated answers.** The main one gives N=2 and U=40% (zero CPU, unequal
  cores; 64% core-weighted is a different estimand). The others cover: exact versus conflicting duplicates;
  out-of-range and missing averages; each min/max bound checked independently, including with the other
  bound missing; offset and misaligned timestamps; gaps; timestamps with no valid reading; unmatched and
  duplicate metadata; and the equivalence of building the full series then splitting versus building from
  the prefix.
- **Independent aggregation** with the `csv` module and `math.fsum`: it reproduces the hand values and all 110
  development targets (counts exact; CPU within 1.8e-15 pp).
- **EDA:** the metadata left join preserves rows and per-time counts; segment contributions add to the target
  at every timestamp.
- **Metrics:** hand fixture (MAE 1.5, RMSE √2.5, 25% improvement); zero-error baselines give N/A; non-finite
  values are rejected; identical timestamps and the same persistence baseline for every model; pooled
  MAE/RMSE recomputed with plain Python.
- **Leakage.** Each fold is rerun after replacing all later targets, on synthetic and development series, and
  forecasts and fitted state are unchanged. A prefix-only run with later targets set to NaN gives the same
  forecasts. Positive controls (teacher forcing; a globally fitted scaler) are detected. The ridge recursion
  is rebuilt from its recorded coefficients. A corrupted synthetic holdout leaves development loader outputs
  and the audit unchanged, while full-series construction fails.
- **Output contract:** exact columns, 24 rows, timestamps equal to the template, unique and increasing,
  finite values, count ≥ 0, CPU in [0,100]; checked before and after writing.

## One-off checks outside the notebook

- The GitHub release API's asset digest equals the local `data-v1.tar.gz` SHA-256. The archive members are
  byte-identical to `challenge_data/`, and `sha256sum -c SHA256SUMS` passes.
- `ASSIGNMENT.md`, `DATASET.md` and `SUBMISSION.md` were read at `6e5ac0e`; their content equals `main` on
  2026-10-26.
- Before any modelling change, the forecasting outputs of the revised loader were byte-identical to the
  starter's generated CSVs.
- An independent script compared `predictions.csv` with the final 24 keys derived from the release file. All
  contract checks passed.

## Not executed (unverified)

- **Real holdout evaluation: deferred by design.**
- The VS Code notebook interface and kernel picker; Linux and macOS; Python 3.12. The previous version of
  this file recorded a Python 3.12.14/Linux check by the starter's author, which was not reproduced here.
- The dataviz palette validator, because Node.js is not installed. The figures use the documented default
  palette order, with line styles as a second cue.
