# Cloud Workload Forecasting — Final Report

**Data:** `data-v1` (archive SHA-256 `d04d402a…caeb`, equal to the GitHub release-asset digest).
**Contract revision:** `atomityhq/forecasting-challenge@6e5ac0e` (2026-10-07).
**Code:** `notebooks/01_forecasting.ipynb`, run by `run_notebook.py`.
**Status:** every number below comes from the recorded run in `reports/generated/`. Validation scores are
**development estimates**, because the same three windows chose the model. The real 24-step holdout
evaluation is **deferred**: it has not been opened.

## 1. Executive summary

- **Both targets are forecast with persistence.** `active_vm_count` is exactly 10,000 at all 110
  development timestamps because the release keeps only complete traces; every candidate ties persistence at
  zero error. The CPU forecast is the last development value, 9.1646%, for all 24 timestamps
  (33,000–39,900 s).
- **A challenger scored better pooled, then failed the predeclared stability checks.** Ridge
  autoregression (α=1) cut pooled CPU MAE by 17.6% (0.172 vs 0.208 pp) and passed every improvement gate.
  The gain came from one window: it reversed when that window was left out (−14.8%) and when data arrived
  five minutes late (−0.6%). The rule, fixed before scoring, therefore keeps persistence. SES beat
  persistence in all three windows, but only by 3.1%, below the 5% bar.
- **A stable mean hides hot VMs.** The cohort mean stays within 9.11–9.91%. Yet at every timestamp 108–146
  VMs (median 127) run at 80% CPU or more, and the hottest 10% of VMs supply 43.5% of summed utilization.
  The mean also dips at minute 20 of every relative hour and rebounds at minute 25, in all 9 complete hours.
- **Operational advice.** Do not automate alerts on the forecast cohort mean. In development, the
  forecast-triggered rule did not beat a fixed two-hour review (always-alert) under either assumed cost
  ratio. Hot-spot risk sits in individual VMs, which the required aggregate cannot show. Alert costs are
  illustrative units; no provisioning cost or saving is demonstrated.

## 2. Data understanding and preprocessing

**Integrity.** The archive's SHA-256 equals the release-asset digest. Its four regular files are
byte-identical to `challenge_data/`, and the three content digests match `SHA256SUMS` and digests pinned in
code.

**Isolation, stricter than the assignment requires.** The boundary was fixed from the sorted unique
`timestamp` keys before any VM ID or CPU value was read. The keys form 134 timestamps exactly 300 s apart:
development is 0–32,700 s (110 keys) and the forecast template 33,000–39,900 s (24 keys). The CPU file is then
read in chunks, dropping later rows on their key. Holdout VM counts follow from VM IDs alone, so they are
protected like any target. No development cell counts holdout rows or VMs, inspects holdout quality, or loads
`timestamp_vm_deleted`, since a recorded deletion time reveals holdout presence.

**"Construct the full target series first, then split" (ASSIGNMENT §3B).** Each target at time *t* uses
only readings stamped *t*, under validity rules fixed in advance. The first 110 rows of the full series
therefore equal the series built from development rows alone, which a synthetic self-check confirms.
Full-series construction is quarantined in the disabled final-evaluation cell, which runs only after
predictions are hashed and asserts that equality. The release-wide checks wait there too: holdout quality,
per-VM coverage of all 134 keys, CPU/metadata population equality and deletion times. They have been
exercised on synthetic data only; on `data-v1` they are **deferred**.

**Development facts (measured).** There are 1,100,000 rows: 10,000 VMs at every one of the 110 keys. No value
is missing or non-finite, no (VM, timestamp) key repeats, every CPU value lies in [0,100], and no row has
`min_cpu > avg_cpu` or `avg_cpu > max_cpu`. `avg_cpu` is never exactly 0 (minimum 0.0072%). Every development
VM matches one metadata row, and the category counts (6,180 / 3,091 / 729) reproduce the data card.

**Targets and denominators.** `active_vm_count(t)` counts distinct VMs with a valid reading at *t*, so an idle
0% VM counts. `aggregate_cpu_utilization(t)` is the unweighted mean of one `avg_cpu` per such VM, in percent.

| Situation | Effect on N(t) and U(t) |
|---|---|
| `avg_cpu` missing, non-finite or outside [0,100] | VM leaves numerator and denominator; audited |
| Exact duplicate row | Removed and audited; the VM counts once |
| Conflicting duplicate | Error |
| A present `min_cpu`/`max_cpu` violating [0,100] or min ≤ avg ≤ max | Error, each bound checked on its own (the starter skipped both checks when either bound was missing; fixed) |
| Missing timestamp, off-grid reading, or no valid reading at *t* | Error: unknown is not zero; nothing is imputed |
| VM without metadata | Counted and reported; never inner-joined away |

None of these situations occurs in development, so the policy changes no development value. Hand-calculated
fixtures cover every row. In the main fixture, VM *a* reads 0% then 20% and VM *b* 80% then 60%, giving N=2 and
U=40% at both times; a core-weighted mean would give 64% at the first time. An implementation using the `csv`
module and `math.fsum`, without pandas, reproduces the hand values and all 110 development targets: counts
exactly, CPU means within 1.8×10⁻¹⁵ pp.

## 3. Workload analysis (development only)

![Development cohort mean with peak and low periods, hot-VM count, and concentration of CPU across VMs](generated/training_workload.png)

*Finding:* all 11 peak timestamps (≥ P90 = 9.67%) fall in one 4.6–5.7 h episode. Six of the 11 low timestamps
(≤ P10 = 9.18%) sit at minute 20 of a relative hour; the rest lie in the last 1.5 h as the level drifts down.
No five-minute step is a robust outlier (|MAD z| > 3.5), and nothing was deleted. *Limitation:* the quantiles
use all 110 points, overlapping the validation windows, so they are descriptive; 80% is a marker, not an SLA.

**Count and churn.** No VM arrives or leaves, and every creation time equals the first timestamp
(left-censored). The constant count is a property of complete-trace curation and says nothing about fleet
arrivals, departures or lifetimes. **Hot VMs.** Only 1.27% of readings are at 80% or more, yet 437 VMs reach
that level at least once and 99 average it across development; the median VM averages 5.5%.

![Segment own mean versus contribution to the required mean](generated/segment_contribution.png)

*Finding:* Interactive VMs have the highest own mean (11.5%), but Delay-insensitive VMs contribute most to
the required mean (5.10 of 9.41 pp, 54%) because they are 62% of VMs. 2-core VMs contribute 78% and carry 91%
of the mean's level variance. The 24-core bucket has the highest own mean among core buckets (11.4%) but
contributes 0.07 pp: the unweighted mean follows the many small VMs and is not a capacity measure.
*Limitation:* whether labels are known at forecast time is not established; differences are associations,
not causes.

![Autocorrelation of levels and changes, and the within-hour profile](generated/training_acf.png)

*Finding:* five-minute changes have autocorrelation −0.42 at lag 1 (rises tend to reverse), +0.61 at one
hour and +0.58 at two hours. In all 9 complete hours, minute 20 sits below the hour mean (−0.21 pp on
average) and minute 25 above it (+0.14 pp). Hourly scheduled work or a source aggregation artifact are
hypotheses, not findings. *Limitation:* the minute was picked post hoc; nine cycles cannot establish a stable
cycle, and 11.1 hours cannot reveal daily or weekly seasonality.

## 4. Forecasting approach

Candidates, features and rules were frozen before validation scores existed and were not changed afterwards.
**Persistence** repeats the last value. **SES** fits one smoothing coefficient by one-step squared error,
starting from the first observation, and forecasts a flat level. **Ridge autoregression** (α ∈ {1, 10, 100})
uses lags 1–3 and a trailing six-bin mean, standardized with a scaler fitted on the training prefix, and
forecasts 24 steps recursively: each step consumes earlier forecasts, never actual values inside the block.
CPU forecasts are clipped to [0,100] at each step (no clipping occurred). A constant prefix falls back to
persistence, which is why all candidates tie on the count. Metadata, calendar features and holdout values are
never inputs. The hourly pattern was found after the freeze; these features cannot represent a 12-step cycle,
and adding one now would be data-snooping.

## 5. Validation methodology

Each fold trains on rows [0, *e*) and forecasts [*e*, *e*+24) from one origin, for *e* = 38, 62, 86 (origins
at 3.08, 5.08 and 7.08 h). That gives three complete, non-overlapping two-hour blocks inside development,
issued the way the final forecast is. All candidates are scored on the same timestamps against the same
persistence forecast. Peak points are actuals at or above the training prefix's 90th percentile.

**Predeclared rule.** A challenger must cut pooled MAE by at least 5%, win at least two of three windows,
not worsen pooled RMSE, and worsen peak MAE by at most 5% (with at least 3 peak points). Among qualifiers
within 1% of the best MAE, SES is preferred, then the strongest penalty. The choice must then keep its MAE
advantage with origins six bins earlier, with a one-bin data delay, and with each window left out; otherwise
the rule falls back to persistence.

**Leakage checks (executed, all passed).** Every fold, rerun from fresh state after all later targets are
replaced, gives identical forecasts and fitted state (SES α, scaler, coefficients) on synthetic and real
development series. A rerun with later targets set to NaN reproduces them exactly. The same detector catches
two deliberately leaky controls: teacher forcing through its forecasts, and a globally fitted scaler through
its fitted state. A ridge path is rebuilt from its recorded coefficients; corrupting a synthetic release's
holdout rows leaves every development output unchanged; and plain-Python recomputation of the pooled metrics
matches. These checks reduce, but cannot rule out, untested leakage paths.

## 6. Results versus baseline (development estimates)

| CPU, n=72 | MAE (pp) | RMSE (pp) | MAE vs persistence | Windows won | Peak MAE, n=16 | Gate |
|---|---:|---:|---:|---:|---:|---|
| persistence | 0.208 | 0.268 | — | — | 0.271 | baseline |
| SES | 0.202 | 0.258 | −3.1% | 3/3 | 0.254 | fails 5% gain |
| ridge_1 | **0.172** | **0.216** | −17.6% | 2/3 | 0.273 (+0.5%) | passes; initial choice |
| ridge_10 | 0.176 | 0.221 | −15.3% | 2/3 | 0.260 | passes; not within 1% of ridge_1 |
| ridge_100 | 0.179 | 0.219 | −14.2% | 2/3 | 0.301 (+10.8%) | fails peak guard |

Window MAE at origins 38 / 62 / 86, in pp:

| Model | 38 | 62 | 86 |
|---|---:|---:|---:|
| persistence | 0.195 | 0.298 | 0.132 |
| ridge_1 | 0.190 | **0.139** | 0.186 |
| SES | 0.190 | 0.286 | 0.129 |

Sensitivity checks for ridge_1 (ridge_1 MAE vs persistence MAE):

| Check | ridge_1 | persistence | Result |
|---|---:|---:|---|
| Origins six bins earlier | 0.166 | 0.189 | holds |
| One-bin data delay | 0.1733 | 0.1724 | **fails** |
| Leave out origin 38 | 0.162 | 0.215 | holds |
| Leave out origin 62 | 0.188 | 0.164 | **fails** |
| Leave out origin 86 | 0.164 | 0.246 | holds |

Both failures trigger the declared fallback, so the decision is **persistence**. **Count:** every candidate
has zero error on 72 points; relative improvement is **N/A** (zero-error baseline): an exact tie, not a gain.

## 7. Error and failure analysis

![Observed versus forecast paths for each development validation window](generated/validation_paths.png)

*Finding:* errors come from level shifts that no candidate anticipates. At origin 62 the forecast is issued
inside the peak episode: persistence (9.79%) and SES (9.78%) carry the peak forward while the level falls,
averaging 0.28 pp below the persistence forecast. Ridge's small coefficients pull its path toward the
training mean, which wins there (MAE 0.14 vs 0.30) but loses at origin 86, where the level keeps drifting
down (0.19 vs 0.13). At origin 38 nothing foresees the episode's onset; persistence under-forecasts by up to
0.54 pp. *Limitation:* three windows from one trace, two shaped by one episode; no band is drawn because no
calibrated uncertainty was produced.

![MAE by validation window and by forecast horizon](generated/validation_errors.png)

*Finding:* error grows beyond about an hour. Persistence MAE is 0.108 pp at horizons 1–6, 0.099 at 7–12 and
0.313 at 13–24; in the first 30 minutes persistence and SES (0.110) beat ridge_1 (0.120). Minutes 20 and 25
carry 16.3–16.7% of absolute error across models, close to their 16.7% share of time, so the hourly dip is not
the main error source. *Limitation:* three errors per horizon point, and every origin, including the final one
at 9.08 h, falls at minute 5 of an hour, so horizon and within-hour phase are confounded.

## 8. Capacity-planning recommendation

**Evaluated policy.** At each origin, alert for operator review if any forecast in the next two hours reaches
the training prefix's 90th percentile. An event is any actual value crossing it within the window. Costs, fixed
before scoring, are 1 per unnecessary alert and 3 or 10 per miss: illustrative units, not dollars or
provisioning savings.

| Policy (3 windows, 2 events) | Alerts | Misses | False alerts | Cost, miss = 3 | Cost, miss = 10 |
|---|---:|---:|---:|---:|---:|
| persistence (selected), SES, ridge_1, ridge_10 | 1 | 1 | 0 | 3 | 10 |
| ridge_100 | 0 | 2 | 0 | 6 | 20 |
| always alert | 3 | 0 | 1 | **1** | **1** |
| never alert | 0 | 2 | 0 | 6 | 20 |

**Why always-alert wins here.** Events are common: two windows cross the threshold, 20 and 5 minutes after
the origin, because one five-minute reading above P90 is enough. Flat forecasts can only alert when the level
is already above the threshold (origin 62). Ridge paths revert toward a prefix mean below P90, so they rarely
alert. The one miss is the onset of the 4.6–5.7 h episode, which no candidate predicted. With three windows
this ranking is fragile.

**Recommendation.**
1. **Count:** treat it as fixed for this curated cohort. A live fleet would need arrival and departure data,
   which this release lacks.
2. **Aggregate CPU:** use persistence as the two-hour point forecast and review on a fixed two-hour cadence
   rather than on forecast-triggered alerts. That cadence was the cheapest evaluated policy under both cost
   assumptions.
3. **Headroom:** persistence's absolute error over the 72 development points had median 0.16 pp,
   90th percentile 0.47 pp and maximum 0.64 pp. A 0.7 pp buffer above the forecast would have covered every
   development point; that describes three windows and is not a calibrated interval. At a ~9.4% mean, aggregate
   under-provisioning risk is small and the cost of over-provisioning by such a margin is low. The material
   risk is the ~127 VMs at 80% or more at any moment, which need per-VM rules; those were not evaluated here.

The final forecast (9.16%) is below the development P90 (9.67%), so the frozen run issues no review alert.

## 9. Limitations and future work

- **Evidence:** 110 points and three windows that also chose the model, so every score is a development
  estimate. The holdout evaluation is implemented and tested on synthetic data, but deferred on `data-v1`.
- **Cohort and target:** curation fixes the count and limits generalization to Azure. The unweighted mean is
  not demand or capacity; sizes are bucketed, and memory utilization is absent.
- **Time:** no wall-clock mapping; the hourly pattern was found post hoc and is confounded with horizon.
- **Future work:** a pre-registered hour-phase or seasonal-naive-12 candidate judged on new data,
  sustained-crossing alerts, and VM-level hot-spot rules.
- **Engineering:** verified on Windows with Python 3.11.9 in two environments. The VS Code interface,
  Linux/macOS and an automated colour-vision check of the figures were not exercised.

## Appendix: reproduction and provenance

```bash
python run_notebook.py --data challenge_data --output reports/generated
```

Run from the repository root with the `README.md` environment. The command took about 25 s and writes
`reports/generated/` and the root `predictions.csv` (SHA-256 `ce15e40b…7584`).
- `frozen_run.json` records the configuration, decisions, data and source digests, versions and the
  development-only audit.
- `frozen_history/` keeps earlier frozen runs byte-for-byte, including the starter's original manifest
  (`a35c3aaf…`, identical predictions).
- A clean copy with a freshly installed, pinned environment reproduced every CSV and figure byte for byte.
- A 3-VM synthetic smoke release without checksums runs with an "unverified / not data-v1" warning.

`TESTING.md` lists every executed check.
