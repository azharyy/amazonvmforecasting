---
name: forecast-validation
description: Audit or implement leakage-safe multi-step time-series backtests, persistence comparisons, model-selection rules, and final evaluation. Use for Atomity forecasting notebooks, expanding-window splits, 24-step horizons, zero-error baselines, peak errors, future-value perturbation tests, and forecast-based alert policies. Do not use to tune on the final holdout or expand model scope without justification.
---

# Forecast Validation

Test whether a forecast improves on persistence using only information available at each origin. Match evaluation to how the final 24-step forecast is issued.

## Establish the experiment

1. Read the actual notebook/code, governing contracts, target definitions, and feature-availability record. Distinguish code inspection, historical saved output, and fresh execution. Check the data contract before trusting metrics.

2. For Atomity, use only supplied data-v1 observations, first 110 development timestamps, final 24 reserved timestamps, both targets, and five-minute predictions. Do not retrieve omitted upstream records. For other projects, obtain their own scope.

3. Define the origin, forecast horizon, update/refit cadence, primary metric, practical improvement criterion, tie rule, and peak threshold rule before comparing outcomes. If unspecified, recommend MAE per target as primary, RMSE as secondary, and the simplest model on a tie. Label recommendations as such.

4. Keep the final 24 target values outside all development decisions, transformations, thresholds, model/feature selection, uncertainty calibration, and policy tuning. Treat final per-time VM cardinalities derived from keys as count targets, not harmless structural metadata. If final target values were already used, disclose contamination; do not describe the holdout as untouched.

5. Read [verification recipes](#verification-recipes) for split boundaries, score fixtures, leakage tests, and the final-evaluation gate.

## Use the smallest decisive comparison

- Compare persistence, simple exponential smoothing, and a regularized autoregression unless the current contract or evidence warrants a different small set. Avoid adding model families just to improve the narrative.

- Evaluate each target separately. Preserve a constant-count persistence baseline when training supports it; explain curation rather than forcing artificial dynamics.

- Use complete H-step expanding-window backtests entirely within development. Generate splits over unique aggregated timestamps. Use explicit exclusive slice boundaries and check every fold.

- For the 110/24 profile, a recommended small primary schedule is training lengths 62 and 86, with validation slices [62:86] and [86:110]. These are two complete non-overlapping validation blocks, not two guaranteed independent experiments. Verify model feasibility after lags/target shifts; reduce complexity if samples are insufficient.

- Fit imputers, scalers, clipping rules, selected lags/features, and hyperparameters only on the fold's training prefix. Fit direct-horizon models only on examples whose target times are also inside that prefix. Freeze a tiny candidate grid in advance or use feasible time-aware inner validation; otherwise label the same-window comparison as model development, not unbiased performance estimation.

- Use a single origin per H-step batch. Recursive autoregression must feed its own predictions after the origin; direct models must use origin-available features. Actual validation y can score predictions, but cannot update features, smoothing state, or model fits within that batch.

- Include dense overlapping origins only as a labeled sensitivity analysis. Report training lengths, forecast origins, validation ranges, and window counts. Do not treat overlapping errors, horizons, or VM rows as independent replications.

## Score and select honestly

- Report MAE and RMSE per target/model/window; provide aggregate scores with the pooling rule. Compare identical timestamps and horizons against the same persistence forecasts. Report absolute error differences and baseline-relative improvement.

- If baseline error is zero, report relative improvement N/A. State whether the candidate ties at zero or is worse. Never add epsilon to fabricate a percentage gain.

- Report errors by horizon and during peaks, plus peak sample counts. Define peak thresholds from the training prefix (for example its 90th percentile), then use validation outcomes only for scoring. Do not tune peak definitions on final outcomes.

- Add a small sensitivity check for training start/length, rolling-origin spacing, or a justified preprocessing choice. Freeze its scope; do not search many variants until a gain appears.

- Select a more complex model only if it clears the predeclared practical criterion, behaves consistently across the available windows, and has no unacceptable secondary-metric/peak degradation under that criterion. Otherwise retain persistence or report insufficient evidence. Do not claim statistical significance from the very small number of temporal windows.

- When selection and reported backtest performance reuse the same windows, label results as development estimates. Reserve the frozen final evaluation for the final performance claim.

## Verify causality and reproduce

- Build independent hand-calculated aggregation, score, and split fixtures. Use expected values calculated before invoking the implementation.

- Rebuild each fold from fresh state after perturbing values later than its origin while retaining keys. Predictions, fold-fitted artifacts, and origin features must remain unchanged within declared tolerance. Permit resulting scores to change; fail a forecast that changes. Run a complementary prefix-only comparison to detect hidden global preprocessing and caches.

- Audit negative shifts, centered windows, backward filling, interpolation across future observations, globally fit scalers, retrospective metadata, teacher forcing, and label overlap in direct models.

- Validate forecast timestamp/column contracts before scoring. Only after the pipeline, features, parameters, clipping, and any policy are frozen may final target values be revealed for one evaluation. Do not tune again on its results.

- For clean reproduction, start a fresh kernel/environment, run in order, and verify recorded dependencies, seeds where applicable, exact forecast keys, and outputs. Do not claim success from an unexecuted notebook.

## Evaluate an operational policy only when requested

Compare a simple utilization alert/headroom rule using each frozen forecast against the same rule using persistence. State threshold, decision timing, lead time, false-positive/false-negative costs, and how costs were chosen before evaluation. Choose/tune only inside development. Keep this a utilization-based scenario; bucketed resources and a selected cohort do not establish exact capacity savings, Azure-wide cost, or unconstrained demand.

## Deliver

Return the fold table, per-target baseline comparison, horizon/peak evidence, leakage-check results, and a short model decision with its limitations. State whether evidence is implemented, executed, or still proposed. For notebook edits, explain each cell's purpose and interpret its outputs. Report failed or unverified tests explicitly; passing one perturbation fixture does not prove that all leakage paths are absent.

---

## Verification recipes

### Split boundaries

Treat end as the number of timestamps available for training (exclusive boundary). For development length T and horizon H:

- train = values[0:end]

- validation = values[end:end+H]

- origin = timestamp[end-1]

- require end > 0 and end + H <= T.

Require positive integer horizon/stride/minimum training length; never silently shorten the last validation block. For T=110, H=24, minimum training length 62, stride 24, expect exactly (end=62, validation 62:86) and (end=86, validation 86:110). The final holdout is outside this development array.

A direct horizon-h training example using features at index i is eligible only if i+h < end. A recursive H-step model predicts the whole block before seeing any actual validation target. One-step walk-forward scores with actual observations after each prediction answer a different question.

### Metric fixture

For actual=[1,3] and prediction=[2,1]:

- absolute errors=[1,2], MAE=1.5.

- squared errors=[1,4], RMSE=sqrt(2.5), about 1.58113883.

For candidate error C and baseline error B > 0:

- absolute improvement = B - C.

- relative improvement percent = 100 * (B - C) / B.

For B=0:

- C=0: tie; relative improvement N/A.

- C>0: candidate worse; relative improvement N/A.
Reject negative or nonfinite error values. Do not calculate percentage gains by adding epsilon. A constant series with correct persistence provides a useful zero-error fixture.

For pooling windows, declare whether each window has equal weight or each prediction has equal weight. Pooled RMSE is sqrt(pooled squared-error mean), not the arithmetic mean of window RMSEs. Keep target units separate.

### Leakage tests

Use an independent copy of source data and fresh model/preprocessing state. Hold keys and past values fixed; perturb all unknown future numeric values after one origin, including the inner validation block. Compare the fold's actual input features, preprocessing parameters, model state, and H-step predictions. Require equality or a small predeclared floating-point tolerance.

Also call the forecast pipeline with only the available prefix plus permitted known-future inputs. It should produce the same forecast as the full-source input. This complements perturbation tests that could miss cached or separately loaded future values.

Test the boundary after an extreme synthetic future spike and with a column whose values summarize the complete trace. Synthetic fixtures may contain arbitrary values; never expose real final targets to develop the test.

Demonstrate that intentionally faulty centered rolling, global scaling, or feeding validation observations is detected. A failing test should identify the contaminated stage; merely declaring all features shifted is insufficient.

### Final evaluation gate

Before accessing final target values, record/freeze:

- data/release revision and contract, feature definitions, permitted metadata, training interval;

- model family and hyperparameters, preprocessing, prediction strategy, and bounds;

- selection and metric/peak/policy definitions, reproduction command/kernel, output timestamp keys.

Fit the selected procedure on all development observations, save predictions, and validate their output contract. Reveal final target values only for the frozen evaluation. Report metrics and limitations without revising the model on that holdout.

If asked to improve a model after final results were used to guide changes, describe the former holdout as development data and require genuinely new evaluation evidence for a new unbiased claim; do not silently reuse it as a fresh test.
