# Validation record

## Current status at 61f174e548bb3a2e72836d52babaaa5386307923, 2026-10-28, Linux / Python 3.12.14

This is the source commit used for the current evidence. The later evidence/documentation commit
contains these results without changing the hashed sources. This session ran in Codex cloud on Linux,
not the Windows / Python 3.11.9 machine described in the historical record. Claude's pasted log was
used to locate unfinished work, not accepted as independent proof of passing checks here.

Both targets are built for all 134 timestamps with fixed rules, then split 110/24; the 24 holdout
values are discarded immediately and never shown, saved, or used for cleaning, diagnostics, fitting
or selection. Only the separate evaluation command scores them. Fatal validation errors stop a freeze;
invalid averages alone are excluded by the unchanged policy. No real holdout evaluation was run.

Commands below ran from the repository root. Notebook/test commands used
`PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/workspace/.onboarding/amazonvmforecasting/matplotlib
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1` (environment assignments on one shell line).

### Executed and observed in this session

1. `.venv/bin/python -m pip check`: exit 0; no broken requirements. All 39 notebook cells and
   `language_info.version = 3.11` were retained. Every code cell parses with Python 3.11 grammar;
   that syntax check is not a Python 3.11 runtime test. All notebook `to_csv` calls explicitly use
   LF terminators and generated-text `write_text` calls use `newline='\n'`.
2. `.venv/bin/python -u tests/run_synthetic_checks.py`: exit 0, **All synthetic checks passed**.
   This includes constant CPU, late arrival, offset keys, freeze/re-freeze archives, changed
   configuration/source/data/prediction/submission refusals before the loader, repeat evaluations,
   synthetic evidence snapshots and a conflicting holdout duplicate refused in loader cell 8 with
   no forecast/manifest/submission. The interruption is injected at the evaluation rebuild itself:
   its opening record must exist, all four evaluation result files must be absent, and retry is REPEAT.
   All evaluation in this suite uses disposable synthetic releases.
3. An isolated synthetic reproduction first demonstrated the pandas rounding defect: a future-only
   VM appended out of time order changed the full/prefix summation path and failed exact equality.
   After the stable timestamp sort, the reproduction passed. The notebook now exercises exact prefix
   equality for appended, reversed, VM-major and shuffled three-VM nontrivial-value fixtures on every
   run. No tolerance was substituted for the required exact assertion.
4. The notebook's selector oracle passed: an exact count challenger qualifies with `pass_peak` N/A;
   a 3% count gain fails; a CPU challenger with worse peaks fails; CPU peak counts of three/two
   respectively pass/fail the sample-size guard. A count-winning reason no longer claims a peak gate.
   Valid synthetic suffix changes also alter release row counts and all three cleaning audit counts
   (duplicate, excluded average, missing bound), while every development artifact remains identical.
5. Scratch real-data freeze (exit 0):

   ```bash
   .venv/bin/python -u run_notebook.py --data challenge_data --output /tmp/atomity-review/scratch/out --predictions /tmp/atomity-review/scratch/predictions.csv --evidence /tmp/atomity-review/scratch/evidence
   ```

   Fixed-rule full-series validation completed without a fatal error. Forecast values equal the
   pre-change submission. SHA-256 is
   `28339ef10688b9bc49535e9aba9426db19ac5d346e20080745824303b0fd1c9a`, also obtained by
   `git show c1e4757:predictions.csv | sha256sum`. Configuration, initial/final decisions,
   development audit, final alert threshold and alert are unchanged. The count reason remains
   **Exact baseline retained.** Leakage checks retain their passing statuses.
6. Historical Windows snapshot comparison: **8 of 14 CSVs match byte-for-byte after CR removal**.
   Six files have only floating-point roundoff: `selection_gates.csv`, `sensitivity_summary.csv`,
   `training_acf.csv`, `validation_horizon_bands.csv`, `validation_model_summary.csv` and
   `validation_window_summary.csv`. Maximum absolute difference is `4.618527782440651e-14`, below
   `1e-12`. Labels, flags, decisions, displayed report values and prediction bytes agree. Exact
   equality of every historical evidence CSV was therefore **not achieved** on this Linux run;
   canonical LF does not promise identical floating-point calculations or platform metadata.
7. After committing the fixes as `61f174e`, `.venv/bin/python -u run_notebook.py --data challenge_data
   --output reports/generated` exited 0. It produced snapshot
   `reports/evidence/0a6fdea759245cba/`, recording the full source commit above and
   `git_uncommitted_sources: false`. A second identical command also exited 0, archived the first
   freeze byte-for-byte under `reports/generated/frozen_history/0a6fdea759245cba/`, and reproduced
   the same manifest, prediction digest and snapshot. The checkout had no earlier generated manifest;
   its older tracked evidence snapshots were preserved, not fabricated as a prior local freeze.
8. `.venv/bin/python reports/report_tables.py`, then `.venv/bin/python reports/report_tables.py --check`:
   both exit 0 against `0a6fdea759245cba`, covering five tables, 29 quoted prose claims, the submitted
   prediction digest and the snapshot's own prediction digest. An isolated copy accepted intact
   historical evidence and rejected a changed snapshot CSV even when the root submission was intact.
9. Final report rendering (exit 0):

   ```bash
   pandoc reports/final_report.md --from=gfm --standalone --resource-path=reports --pdf-engine=xelatex -V mainfont='Liberation Serif' -V fontsize=11pt -V geometry:margin=1in -V papersize:letter -o /tmp/atomity-review/final-report.pdf
   pdfinfo /tmp/atomity-review/final-report.pdf
   pdftotext -layout /tmp/atomity-review/final-report.pdf /tmp/atomity-review/final-report.txt
   ```

   **6 pages including the appendix**, which begins on page 6; Letter (612×792 pt), one-inch margins,
   11 pt body, Liberation Serif. No missing-glyph warnings. Rendered pages 3 and 6 were inspected for
   legibility and layout. The PDF stays outside the checkout. This validates this specified rendering,
   not every Markdown viewer or font. An earlier Noto Serif trial had missing math glyphs and was not
   accepted; the final Liberation Serif render uses plain wording for the unsupported set-membership glyph.
10. `git diff --check`: exit 0. A name-only recursive search found **no `holdout_opened.json` under
    `/workspace` or `/tmp`** (the available checkout, data, archived outputs and task scratch locations).
    Successful synthetic tests remove their temporary opening records. No claim is made about the
    inaccessible Windows temp folders mentioned in Claude's pasted log.

### Not executed or not established in this session

- Real `--evaluate-holdout`: deferred by design; no real final scores or targets were inspected.
- Windows / Python 3.11.9, macOS, or a second operating-system run. Linux / Python 3.12.14 **was** run.
- VS Code's UI/kernel picker; Python 3.11 runtime compatibility beyond the grammar check.
- Bitwise equality of all evidence/figures across systems. Six historical CSVs differ only at rounding
  precision as quantified above; figures were regenerated on this platform and are committed with the report.
- Headless Edge and the historical Georgia-font pagination. A separately specified Linux render is used.
- The optional palette-validator tool and any checks not listed as executed above.

## Historical record: uncommitted tree on c1e4757, committed as 641f051

The following is retained historical evidence, not a claim about the current checkout.
Superseded statements include “Nothing was committed”, the dirty root prediction file, unrun Linux /
Python 3.12, and CRLF-only differences from the then-HEAD file. The old assertion that source digests
match its manifest applies to that historical tree; the new manifest above identifies the current code.
The old corruption/holdout wording describes the development-first loader, which has been replaced by
full-series construction before splitting. The opening record now precedes scoring and the evaluation
rebuild; deterministic full-target construction already occurs during development. The old holdout target
values were never displayed or scored, and no new real scoring has been performed.

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
