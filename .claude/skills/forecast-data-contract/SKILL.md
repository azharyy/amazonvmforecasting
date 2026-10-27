---
name: forecast-data-contract
description: Validate forecasting data contracts, target aggregation, metadata joins, provenance, and prediction outputs. Use for data-shape or schema audits, defining active_vm_count and aggregate_cpu_utilization, reconciling assignment requirements, and checking Atomity forecasting submissions. Do not use to select models or certify forecasting accuracy.
---

# Forecast Data Contract

Make every check traceable to a source and an executable assertion. Read the actual inputs; distinguish a described check, implemented code, and an observed passing run.

## Establish the contract

1. Resolve the current project files through the appropriate connected source. Read governing assignment, dataset, and submission documents and their version, plus the release card/checksums when available. Reuse material already verified in this task; do not repeatedly retrieve it.

2. For the Atomity challenge, read [the project profile](#atomity-project-profile). Treat that profile as the user's agreed scope, not independent verification of current repository contents. Keep only supplied data-v1 observations; consult Azure documentation for semantics without retrieving omitted records.

3. Build a compact table: rule, source location/version, status (explicit requirement / user restriction / recommendation / observed property), assertion, and result. Do not turn a release-specific observation into a universal requirement.

4. Resolve conflicting authoritative sources before dependent work. If a source or input cannot be read, mark the corresponding check UNVERIFIED and continue independent checks. Ask only for the specific missing material needed to proceed; never invent schemas or checksum results.

## Audit inputs without exposing holdout targets

- Inspect schema and timestamp keys separately from target-bearing columns. Determine the chronological boundary from the sorted unique timestamp grid. Partition into development and final evaluation before value summaries, cleaning decisions, or feature exploration. Treat held-out VM cardinalities as protected target information: active_vm_count can be derived from VM keys alone. Restrict population/cardinality diagnostics to development until final evaluation.

- Confirm row grain, key types/nullability, duplicate (VM, timestamp) pairs, unique ordered timestamps, units, cadence, gaps, and population coverage. Distinguish absent VM rows from zero CPU readings. Preserve relative trace seconds; do not invent a calendar origin or timezone.

- Verify archive and per-file checksums against the expected release manifest. Record actual digests and file versions. An unavailable manifest yields UNVERIFIED, not a pass.

- On development rows, check numeric finiteness, CPU bounds, and min_cpu <= avg_cpu <= max_cpu where those fields exist. Report missing/invalid values; do not silently drop rows, coerce malformed values, fill zeros, or change the target denominator.

- Check one metadata row per VM and join cardinality (many readings to one metadata row). Compare row counts, key sets, unmatched keys, and per-time populations before/after joining. Duplicate metadata must fail validation before joining.

- Classify metadata by availability at the forecast origin. A field being present in a release does not prove it was available then; exclude full-trace summaries, lifecycle endpoints, and other retrospective fields from predictive inputs unless availability is established.

- Before final evaluation, restrict holdout inspection to permitted schema and timestamp-grid coverage checks. Do not derive its per-time VM counts or inspect CPU summaries, plots, quality-dependent cleaning choices, or target values. Report value-dependent and count-revealing holdout checks as deferred. Hashing release bytes for provenance is permitted; parsing them to expose targets is not.

## Define and verify targets

- Read target formulas from the contract before implementing them. For the agreed Atomity profile, calculate distinct observed VM IDs per timestamp and the unweighted mean of valid VM avg_cpu readings, after enforcing one valid reading per VM/timestamp and documenting invalid-data handling. Keep observed idle VMs in the count.

- Distinguish observation count from demand/provisioning, and mean utilization percentage from total CPU consumption. Bucketed core metadata cannot establish exact used-core totals or unconstrained demand.

- Explain complete-trace selection and any constant VM count as properties of the selected cohort. Never claim Azure-wide representativeness from the selected archive alone.

- Independently verify aggregation on a hand-calculated fixture, including zero utilization, unequal VM sizes, a duplicate key, and missing metadata. Compute expected results before calling the implementation. Use the fixture in the profile.

- If training is constant, record that result and its consequence for the persistence baseline. Do not inspect final target values to decide how to forecast it.

## Check outputs and reproduction

Read the actual submission contract for exact column names/order/types, timestamp representation, required rows, and constraints. Check both target columns, unique exact forecast timestamp coverage, finite predictions, and permitted value ranges. Require integer count predictions only if the governing contract requires them. Do not validate timestamps by row count alone.

When reproduction is requested, use a clean checkout/environment and a fresh notebook kernel or runner. Confirm a clean chronological execution and the expected outputs. Inspect holdout gates before executing a whole notebook; use targeted safe checks during development. Never report clean reproduction from code inspection alone.

## Deliver

Return the requirement/check/result table with file or notebook-cell evidence and status PASS, FAIL, DEFERRED, or UNVERIFIED. Distinguish code present from checks actually executed. For failures, show the smallest corrective change and its validation. When writing notebook cells, explain purpose, inputs, and output interpretation alongside the assertions. Preserve the current project scope and dependency set; introduce a validation framework only if it solves a demonstrated need.

---

## Atomity project profile

Use this profile only for the Atomity cloud workload forecasting project. For other projects, obtain their own targets, origin semantics, splits, and contracts.

### Scope established by the user

- Forecast both active_vm_count and aggregate_cpu_utilization.

- Preserve the first-110 / final-24 chronological timestamp split.

- Produce predictions on every required five-minute timestamp; the final horizon contains 24 steps.

- Use only the supplied data-v1 observations. Consult original Azure documentation for semantics; do not retrieve omitted upstream observations.

- Keep final target values out of development, preprocessing choices, model selection, and operational-policy tuning.

- Keep the effort within 5–7 days. Prefer a small decisive comparison to additional model families.

- Work in a Jupyter notebook in VS Code, with clear markdown and reproducible execution. Add an entry-point script only when needed or requested.

### Governing source locations

Read current versions or the user's pinned checkout:

- https://github.com/atomityhq/forecasting-challenge/blob/main/ASSIGNMENT.md

- https://github.com/atomityhq/forecasting-challenge/blob/main/DATASET.md

- https://github.com/atomityhq/forecasting-challenge/blob/main/SUBMISSION.md

Record exact revision/release identifiers when available. Separate explicit repository requirements from this user's stricter scope and from recommended checks.

### Properties to reverify, not silently assume

Prior project inspection reported a shared complete-trace cohort, constant VM count, 134 timestamps spaced 300 seconds apart, relative trace times, and bucketed resource metadata. Recompute the timestamp grid from release timestamp keys; check population and target-value facts on development rows. Final per-time VM cardinalities reveal the count target and remain deferred until frozen evaluation. Do not hardcode a VM population size, release digest, schema, or benchmark score based on prior summaries.

A fixed cohort makes count forecasting conditional on curation. An arithmetic VM mean gives small and large VMs equal weight. Core buckets, including any open-ended bucket, do not yield exact physical CPU consumption or capacity costs. Release selection using complete traces is not evidence of deployment-time cohort knowledge.

### Hand-calculated aggregation fixture

For each of two observed VMs, use one row at each timestamp:

- time 0: VM a avg_cpu=0; VM b avg_cpu=80.

- time 300: VM a avg_cpu=20; VM b avg_cpu=60.

- metadata: one row for VM a with 2 cores; one row for VM b with 8 cores.

Expect N=2 and U=40 percent at both timestamps. This synthetic exact-core fixture has core-weighted utilization 64 percent at time 0, which is a different estimand. Never infer exact-core totals for the real bucketed metadata.

Add a duplicate (a, 0) row: reject duplicate grain before aggregation; do not silently deduplicate. Add a second metadata row for a: reject the join before it multiplies readings. Remove b's metadata: report an unmatched key; do not inner-join away b and change the target. Set a CPU value outside [0,100] or min_cpu above avg_cpu: report invalid data before calculating target summaries.

### Target and submission checks

Confirm each target's exact definition and the invalid-reading policy from the governing source. On valid unique readings, expect:

- N_t = number of distinct observed VM IDs at t, including idle VMs.

- U_t = arithmetic mean of avg_cpu across those VMs, in percentage points.

Derive final timestamps from actual sorted release keys and the split, then compare exact ordered output keys. Inspect SUBMISSION.md for its schema; do not assume extra fields such as a model-name column are allowed.
