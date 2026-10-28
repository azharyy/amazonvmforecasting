# Validation record

Every item below was **executed** in this checkout on 2026-10-27/28 unless it is dated otherwise or listed
under *Not executed*. The real final 24 targets were never opened: no `holdout_opened.json` exists anywhere
under `reports/`, and `--evaluate-holdout` was only ever run on synthetic releases.

## Environments

| Name | Interpreter | Packages | Notes |
|---|---|---|---|
| A: project `.venv` | Python 3.11.9, Windows 11 (`Windows-10-10.0.26200-SP0`) | six exact pins plus unrelated extras, 118 in the lock | `pip check` clean |
| B: fresh venv | same base interpreter, created 2026-10-27 outside the repository | `pip install --only-binary=:all: -r requirements.txt`, 44 in the lock | `pip check` clean; no pin changed |

## Commands and observed outcomes

1. **Synthetic multi-run checks, environment A:** `.venv\Scripts\python.exe tests\run_synthetic_checks.py`
   exited 0 in 3 min 01 s. It works on a temporary copy of the project and never reads `challenge_data`:
   - The constant-CPU release (134 keys from 600 s; VMs at 0, 20 and 40%) runs to completion and forecasts
     exactly the last 24 keys (33,600–40,500 s) with count 3 and CPU 20%. Teacher forcing is detected on the
     synthetic series and reported "not applicable: fitted control cannot respond" on the constant one.
   - A release whose CPU is flat until a VM arrives at step 37 also runs: not applicable at origin 38,
     detected at 62 and 86.
   - Freeze then evaluate: the first evaluation succeeds; a repeat prints REPEAT and returns the saved
     results; every file is byte-identical afterwards.
   - Refused, each before any data row is parsed (last cell started ≤ 6), with every existing file
     byte-identical: a 6% gain rule (before and after opening), an edit to the evaluation cell's peak rule,
     re-gzipped data, changed frozen prediction bytes, an archived copy in `frozen_history/`, and a changed
     submission copy. A re-freeze with the 6% rule writes byte-identical predictions, so these refusals do not
     depend on the predictions changing. Re-freezing an opened directory is refused.
   - A re-freeze archives the previous run byte-for-byte.
   - On a holdout poisoned with conflicting duplicates, the first evaluation fails while reading the holdout,
     and `holdout_opened.json` already exists. The next attempt is labelled REPEAT and leaves the record
     byte-identical.
   - A pseudo data-v1 release writes its evidence snapshot with all 16 files. After the original run is
     evaluated, a copy of it made beforehand is recognised as a REPEAT through the snapshot's opening record.
   - Snapshots are never replaced: a tampered file makes `snapshot_evidence` raise.
2. **Synthetic multi-run checks, environment B:** the same script run with the fresh environment's
   interpreter exited 0 in 2 min 43 s, with the same eight outcomes.
3. **Documented command, environment A:**
   `.\.venv\Scripts\python.exe run_notebook.py --data challenge_data --output reports/generated`
   (run from Git Bash with the same interpreter and arguments) exited 0 in 44 s.
   - The previous run (manifest `e87c877f…`, the code of commit `c1e4757`) was archived in
     `frozen_history/e87c877f9b04d5cc/`. All 32 files fingerprinted before any change in this session
     survive byte-for-byte, archived or in place, including the earlier histories `a35c3aaf…` (the
     starter's original), `b491783b…` and `a0f6475b…`.
   - `predictions.csv` is unchanged: SHA-256 `ce15e40b…7584`, the same bytes as the previous run and the
     starter's original.
   - Snapshot `reports/evidence/d21d137c7ebf7bd1/` (16 files, 25,899 bytes). Its evidence CSVs are
     byte-identical to the previous run's except `leakage_checks.csv` (new status columns) and
     `training_tail_summary.csv` (two added rows). Three CSVs are new: headroom, ACF and hour profile.
   - Leakage: every fold is unchanged under the alternating shift and the prefix-only run, and both controls
     are detected at all three origins, on the synthetic and on the data-v1 series.
   - The working tree's source digests equal the manifest's (recomputed read-only).
4. **Clean copy, environment B.** The copy held only `run_notebook.py`, `requirements.txt`, the notebook and
   `data-v1.tar.gz`. The same command exited 0 in 41 s, verifying and extracting the archive itself.
   - The extracted files equal `challenge_data/` byte-for-byte, and `predictions.csv` equals run 3's.
   - 22 of 24 generated files are byte-identical, including every CSV and all five figures. The two others
     differ as expected: `environment.lock.txt` (different package set) and three manifest fields
     (environment-lock digest, `git_commit`, `git_uncommitted_sources`; the copy is not a repository).
5. **Independent output check** (a script that uses no notebook code and reads only the release's
   `timestamp` column):
   - exact columns; 24 rows; timestamps equal to the last 24 of the 134 sorted release keys
     (33,000–39,900 s);
   - finite values, count 10,000 (≥ 0) and CPU 9.16455617499 (in [0, 100]);
   - values identical to the previous run, the starter's original and `git HEAD`. The bytes differ from
     `HEAD` only by CRLF vs LF line endings.
6. **Report:** `.venv\Scripts\python.exe reports/report_tables.py --check` exited 0 against the cited
   snapshot. It checks five generated tables, 29 quoted numbers in the prose, that the snapshot's prediction
   digest equals the root `predictions.csv`, and that no table sits outside the generated blocks. A mutation
   test on scratch copies made 15 single edits (prose numbers, a table cell, a removed marker, an unmarked
   table, the prediction digest); `--check` failed on all 15 and passed on the unchanged report.
7. **Pagination:** the report was rendered with headless Edge (Chromium print) on US Letter: 1-inch margins,
   11 pt Georgia body, 9 pt tables, figures at the 6.5-inch text width. That gives **6 pages**, appendix
   included, with about 0.4 inch to spare. All five figures are 6.5 in wide at 200 dpi, so their 7–8.5 pt
   text prints at true size; the rendered pages were inspected visually. Other page sizes, fonts or
   renderers give other counts. GitHub's Markdown view is not paginated.
8. **Kernel refusal:** the notebook's cells, executed without the runner but with
   `CWFC_EVALUATE_HOLDOUT=1` (as a kernel would, on a synthetic release), stopped in cell 4. No data was read
   and no record changed.
9. **Independent review.** Four reviewers worked on scratch copies with synthetic data only, plus
   freeze-only data-v1 runs. They tried to break the protocol, the leakage redesign, the report and the
   code. Their findings were fixed, and items 1–8 were run afterwards on the fixed code.

## Checks inside the notebook (run by every development command)

- **Release:** archive digest when extracting; content digests against `SHA256SUMS` and against the pinned
  data-v1 digests.
- **Isolation:** the boundary is derived from timestamp keys only; holdout rows are dropped by key before any
  value is used; the audit covers development rows only.
- **Aggregation fixtures with hand-calculated answers.** The main one gives N=2 and U=40% (zero CPU, unequal
  cores; 64% core-weighted is a different estimand). The others cover:
  - exact versus conflicting duplicates;
  - out-of-range and missing averages;
  - each min/max bound checked on its own, including with the other bound missing;
  - offset and misaligned timestamps, gaps, and timestamps with no valid reading;
  - unmatched and duplicate metadata;
  - building the full series and then splitting gives the same result as building from the prefix.
- **Independent aggregation** with the `csv` module and `math.fsum` reproduces the hand values and all 110
  development targets (counts exact, CPU within the asserted 1e-10 pp).
- **EDA:** the metadata left join preserves rows and per-time counts; segment contributions add to the target
  at every timestamp.
- **Metrics:**
  - hand fixture: MAE 1.5, RMSE √2.5, 25% improvement;
  - zero-error baselines give N/A, and non-finite values are rejected;
  - every model has identical timestamps and the same persistence baseline;
  - pooled MAE/RMSE are recomputed with plain Python.
- **Leakage.** Each fold is rerun with every later target shifted (CPU alternately +50 and +60 pp, count +7
  and +8) and with later targets set to NaN; forecasts and fitted state must not change.
  - Both positive controls (teacher forcing; a globally fitted scaler) must be detected at every origin of
    the nonconstant synthetic series.
  - On the supplied series a control may go undetected only if its fitted model cannot respond (zero input
    response); this is reported as "not applicable". Any other miss fails the run.
  - The ridge recursion is rebuilt from its recorded coefficients.
  - A corrupted synthetic holdout leaves the development loader outputs and the audit unchanged, while
    full-series construction fails.
- **Output contract:** exact columns, 24 rows, timestamps equal to the template, unique and increasing,
  finite values, count ≥ 0, CPU in [0,100]; checked before and after writing.
- **Freeze record:** before anything is written, the previous run is archived in full (temporary file, then
  rename; differing archived files are refused). A directory with an opening record is refused.
  `frozen_run.json` is written last and includes the environment-lock digest.
- **Evaluation gate** (evaluation mode only):
  - refused unless the runner supplies the executed code;
  - data, source (line endings ignored), configuration and prediction fingerprints are compared with the
    original manifest before any data row is parsed;
  - the scratch rerun must reproduce the predictions and every recomputable manifest field;
  - the opening record is created atomically and exclusively before any holdout value is used;
  - a repeat returns the saved results.

## Earlier checks (2026-10-26, not repeated in this session)

- The GitHub release API's asset digest equals the local `data-v1.tar.gz` SHA-256. The archive members are
  byte-identical to `challenge_data/`, and `sha256sum -c SHA256SUMS` passes.
- `ASSIGNMENT.md`, `DATASET.md` and `SUBMISSION.md` were read at `6e5ac0e`; their content equals `main` on
  2026-10-26.

## Not executed (unverified)

- **Real holdout evaluation: deferred by design.**
- **A commit and a fresh clone.** Nothing was committed. `.gitattributes` should store `predictions.csv` and
  `reports/evidence/` byte-exact once committed. `git status` already shows `predictions.csv` as modified,
  but only in its line endings: no content change once CR is ignored. A clone was not tested here.
- **macOS/Linux and Python 3.12.** There, the CSV and JSON files are written with LF, so digests differ while
  the values do not. Cross-platform evaluation is designed to work (source digests and the recomputed
  predictions ignore line endings) but was not run.
- **The VS Code notebook interface and kernel picker.** Kernel refusal was simulated (item 8), not run in
  VS Code.
- **The dataviz palette validator**, because Node.js is not installed. The figures keep the documented
  palette colors for persistence (slot 1) and ridge α=1 (slot 3), with line styles as a second cue; the
  other candidates are grey.
