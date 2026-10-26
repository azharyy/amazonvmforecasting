# Validation record

The implementation was checked in a separate 64-bit **Python 3.12.14 / Linux** environment
with the six exact direct dependency pins in `requirements.txt`. All six match the supplied
package list. Dependency resolution/imports and `pip check` passed.

## Executed checks

- All 38 notebook cells were validated against the notebook schema; all 19 Python cells compiled.
- The command-line runner executed every Python cell in order on the supplied `data-v1` files.
- The archive digest and all three content checksums matched.
- Training aggregates matched an independent streaming CSV implementation using `math.fsum`.
- Hand-calculated target, duplicate, missing-average, zero-utilization and gap fixtures passed.
- Shifted lag/rolling-mean alignment and constant-target fallback checks passed.
- Metrics covered both zero-error baseline ties and a model worse than an exact baseline.
- Future-value/fitted-parameter checks passed at all three validation origins for all candidates.
- A two-VM fixture tested offset timestamps and a population other than 10,000.
- Changing raw future CPU values and retrospective metadata fields left training data,
  development results/model selection and forecasts unchanged.
- The optional holdout-evaluation branch was exercised on a **synthetic smoke fixture only**.
- Prediction output checks covered columns, timestamps, row count, finiteness and bounds.
- Clean extracted-bundle reproduction was checked against the same release and prediction bytes.

The synthetic fixture is solely a software test. It is not included in the release analysis,
training, selection or operational evidence. The real final 24 target values were not opened
for evaluation during validation of this starter.

## Reproduce

Run the setup commands in `NOTEBOOK_SETUP.md`, then from the project folder:

```bash
python run_notebook.py --data challenge_data --output reports/generated
```

The self-checks are notebook cells, so this command runs them with the analysis. A separate
pytest dependency is unnecessary. The notebook uses ordinary Python cells rather than notebook
magics, allowing the same code to run in a fresh Python process without a Jupyter server.

## Limits

The VS Code graphical interface and Windows/macOS kernels were not exercised here. Your
existing full environment was not reproduced; the notebook checks its selected interpreter
and imports at runtime. A Linux environment snapshot is recorded for each run, while the
direct requirements remain portable and allow pip to resolve platform-specific transitive
dependencies.

This is an executable analysis starter. The final 4–6-page report and any final holdout
interpretation remain your work after running and reviewing the evidence.
