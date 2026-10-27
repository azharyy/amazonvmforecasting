---
name: forecast-eda
description: Perform training-only exploratory analysis for time-series forecasting notebooks, including VM/timestamp CPU data. Use to profile missingness, invalid values, peaks, distributions, cohort contributions, short-trace limitations, and candidate lag features in the Atomity project. Preserve valid spikes and holdout isolation; do not use for final model selection or causal attribution.
---

# Forecast EDA

Produce reproducible programmatic diagnostics that answer a forecasting question. Preserve valid peaks and the chronological information boundary.

## Establish inputs and scope

1. Read the current data contract and inspect the actual notebook/data. Use forecast-data-contract when target formulas, join cardinality, release provenance, or grain are unresolved. If that skill is unavailable, perform the necessary source checks directly.

2. For Atomity, retain the user's data-v1-only scope, first 110 development timestamps, final 24 reserved timestamps, both required targets, and five-minute output cadence. Revalidate the boundary from current release keys. For another project, obtain its own split and units.

3. Partition before profiling target values. Read holdout timestamp/schema information only as needed to establish coverage; exclude final target values from summaries, plots, outlier thresholds, transformations, feature choices, and examples. Do not derive final per-time VM cardinalities from keys: they reveal the count target. Do not report notebook outputs computed on mixed development/holdout data as valid development evidence.

4. Use existing Python data tools in the project; generate transparent notebook cells or run targeted diagnostics. Avoid installing a profiling framework or changing dependency versions merely for this workflow. Read [diagnostic recipes](#diagnostic-recipes) for edge cases and reporting.

## Profile development observations

- State the row grain and denominator. On raw readings, inspect numeric CPU columns and VM/time coverage; on targets, inspect the correctly aggregated time series. Keep those levels separate.

- Report rows, columns, types, unique IDs/timestamps, cadence, missing cells, missing VM/time rows, duplicate keys, invalid numeric values, and per-time coverage. Validate keys/joins before interpreting summaries.

- Treat CPU range/order violations, infinities, malformed values, and duplicate grain as data problems. Explain a correction or policy before editing; do not silently impute, average duplicates, fill gaps, or change the population.

- Report distributions, quantiles, median/MAD or IQR flags, zeros, near-saturation values, and potential discontinuities. Treat statistical flags as observations to investigate, not deletion instructions. Flag a valid spike separately from a physically invalid CPU value.

- Inspect how the aggregate changes with VM category/core bucket. Distinguish a segment's own mean from its contribution to the overall unweighted mean. Do not replace the required target with a capacity-weighted metric.

## Diagnose predictive structure

- Inspect chronological plots, first differences, persistence residuals, a small lag/ACF view, and whether each target is constant or near-constant. Treat inferential assumptions explicitly: autocorrelated readings are not independent samples.

- Match lag depth to available history and the intended horizon. Do not assert daily or weekly seasonality from an intraday trace. State when a period cannot be identified.

- Propose a small candidate feature set, with a reason and an availability rule for each. Distinguish available values, training parameters, and unknown future quantities. Use correlation as a descriptive check, not proof of usefulness or an automatic fixed-threshold feature filter.

- If exploratory decisions use all 110 development points, acknowledge that those decisions have seen any inner validation targets in that span. For a fair backtest, freeze choices independently of its validation blocks or repeat adaptive diagnostics/selection inside each training prefix. Delegate the comparison and selection rule to forecast-validation.

- Require causal lag and rolling construction. A feature attached to target t cannot include y_t or later unknown values. For batch H-step predictions, derive every horizon from information available at the common origin; do not consume actual observations from inside the forecast block.

## Select a few evidence-bearing plots

Prefer static notebook plots with reproducible data: development target traces, persistence residuals, a small lag diagnostic, and segment contributions when relevant. Label units, time meaning, denominators, and development boundaries. Avoid redundant dashboards, per-VM plot floods, and unsupported causal explanations.

## Deliver

Return:

1. A concise data-quality table with evidence and unresolved issues.

2. A small set of plots/statistics linked to specific questions.

3. A feature-availability table: feature, source, latest permissible time, window, fit scope, rationale.

4. Verified findings, hypotheses to test, and limitations, each clearly distinguished.

5. Minimal notebook edits/cells when requested, with purpose and output interpretation.

Report what was actually run and what was only proposed. Never claim that EDA proves predictive improvement, or that an unexecuted cell constitutes a passed check.

---

## Diagnostic recipes

### Partition and evidence

Determine the split using sorted unique timestamps, not raw row indices. VM-major ordering and interleaved raw rows make a row-count split invalid. Validate duplicate grain first. Derive development keys, filter raw numeric observations to those keys, then aggregate and summarize.

Permit schema and timestamp-grid coverage checks over the complete release when they do not expose final target values. Treat per-time VM cardinalities as target values, even when computed only from keys. Keep final value-dependent and count-revealing validation deferred until the frozen final evaluation.

Separate invalid-data counts, statistical outlier flags, and substantive peaks. Preserve unknown/missing states rather than coercing them to zero.

### Robust flags

For a chosen numeric field, calculate quantiles on development values. IQR bounds or robust median/MAD scores are descriptive flags. If IQR or MAD is zero, report the degenerate scale; do not divide by zero, label every deviation as corrupt, or delete observations.

For a bounded CPU percentage, a 100 percent reading can be valid. A value above 100, an infinity, or an impossible min/avg/max ordering is a different issue. Check the source's units before imposing a numerical bound.

Retain an unmodified training series unless a documented measurement error justifies a correction. Compare any justified correction as a training-only sensitivity check rather than silently changing the required target.

### Constant targets and lags

For a constant training target, report zero first differences and a perfect persistence fit where defined. Correlation/ACF can be undefined because variance is zero; show N/A instead of a fabricated coefficient. Do not add noise to make a statistic compute.

Choose a short lag range from available history and scientific relevance; avoid high-order seasonal decompositions when fewer than two credible cycles exist. Note that two cycles alone do not establish stable seasonality.

For one-step forecasting, lag 1 at target t uses y_(t-1), and a trailing width-w mean uses y_(t-w), ..., y_(t-1). For a forecast issued at o, every batch horizon o+h uses only observed y at or before o, known-future inputs, or recursively predicted values. Shift alone does not make a precomputed full-series validation feature causal for h>1.

### Contributions

For segment g, its contribution to the required mean at time t is sum(avg_cpu for VMs in g at t) / N_t. Contributions add to U_t. A segment mean divides by N_g,t instead; summing segment means is wrong.

Avoid treating VM counts within a timestamp as independent temporal validation windows. Segment differences describe contribution or association; causal explanations need separate evidence that these observations may not contain.

### Notebook presentation

Place markdown before code to state the question and permitted inputs, and after results to explain the finding and limitation. Use current project column names and reuse aggregation helpers. Retain exact underlying values for assertions even if plots/tables are rounded for display.
