# <module name="frozen-evidence report synchronization">
# <challenge>ASSIGNMENT sections 3F–3G and 7–8 ask for error analysis,
# operational interpretation and reproducible communication.</challenge>
# <how>Read one tracked snapshot, render its five table blocks, and check
# selected prose claims against the same saved evidence.</how>
# <why>Report generation stays separate from training so checking the report
# cannot refit models, change selections or expose the final holdout.</why>
# <tradeoff>The cited evidence is historical. A passing check establishes
# consistency with that run, not that it was produced by today’s source.</tradeoff>
# </module>
"""Regenerate the result tables in final_report.md from its tracked evidence snapshot, and verify its numbers.

usage: python reports/report_tables.py [--check]

The report cites one snapshot ("tracked snapshot `reports/evidence/<16 hex>/`"). Each table sits between
<!-- table:NAME --> and <!-- /table --> markers and is rewritten from the snapshot's CSVs; --check only
compares. Key numbers quoted in the prose (outside the tables) must appear exactly as formatted below, the
snapshot must describe the submitted predictions.csv, its own predictions.csv must match its manifest digest,
and no table may sit outside the markers.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

# <setup>Resolve paths from this file, name the CPU target consistently,
# and define a bounded marker pattern so one table cannot consume the next.</setup>
REPORT = Path(__file__).resolve().parent / "final_report.md"
ROOT = REPORT.parent.parent
CPU = "aggregate_cpu_utilization"
NAMES = {"ses": "SES", "always_alert": "always alert", "never_alert": "never alert"}
WORDS = {1: "one", 2: "two", 3: "three"}
GATES = {"pass_mae_gain": "{gain:.0%} gain", "pass_two_windows": "window wins", "pass_rmse": "RMSE guard",
         "pass_peak": "peak guard"}
BLOCK = r"<!-- table:{name} -->\n(?:(?!<!-- table:).)*?<!-- /table -->"  # never runs into the next table


# <function name="rows">
# <how>Load a snapshot CSV as dictionaries and retain rows matching every named equality
# filter.</how>
# <why>The report renderer reads frozen evidence, rather than rerunning models and silently
# presenting a newer experiment.</why>
# <tradeoff>CSV fields remain strings until their use site converts them, preserving exact labels
# and Boolean encodings.</tradeoff>
# </function>
def rows(snapshot, name, **where):
    with (snapshot / name).open(newline="", encoding="utf-8") as stream:
        return [row for row in csv.DictReader(stream) if all(row[key] == value for key, value in where.items())]


# <function name="signed">
# <how>Format a number with an explicit sign and chosen decimal precision, replacing the ASCII
# hyphen with a typographic minus.</how>
# <why>One formatter keeps prose and tables consistent, making strict quoted-number checks
# predictable.</why>
# </function>
def signed(value, digits=1):
    return f"{value:+.{digits}f}".replace("-", "−")


# <function name="table">
# <how>Build a Markdown header, alignment separator and body from already formatted cells.</how>
# <why>Using the standard library is sufficient for five fixed report tables; the caller controls
# precision, labels and emphasis explicitly.</why>
# <tradeoff>This is a small report-specific renderer, not a general Markdown escaping
# library.</tradeoff>
# </function>
def table(header, right, body):
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---:" if r else "---" for r in right) + "|"]
    return "\n".join(lines + ["| " + " | ".join(row) + " |" for row in body])


# <function name="tables">
# <how>Read the cited run’s configuration and evidence, then render CPU comparison, per-window,
# sensitivity, policy and headroom tables.</how>
# <why>The report must expose baseline comparisons, peak errors, stability and operational costs
# together; a single lowest-MAE value cannot establish the best operational choice.</why>
# <tradeoff>This formatter mirrors the notebook’s recorded gates. It describes the snapshot’s
# initial selection and sensitivity results; it does not select or refit a final model.</tradeoff>
# </function>
def tables(snapshot):
    manifest = json.loads((snapshot / "frozen_run.json").read_text(encoding="utf-8"))
    config = manifest["configuration"]
    models = rows(snapshot, "validation_model_summary.csv", target=CPU)
    gates = {row["candidate"]: row for row in rows(snapshot, "selection_gates.csv", target=CPU)}
    initial = manifest["initial_decisions"][CPU]["candidate"]
    mae = {row["candidate"]: float(row["mae"]) for row in models}
    rmse = {row["candidate"]: float(row["rmse"]) for row in models}
    qualified = [name for name, gate in gates.items() if gate["qualifies"] == "True"]
    best = min(qualified, key=mae.get, default=None)
    body = []
    for row in models:
        name, gate = row["candidate"], gates.get(row["candidate"])
        peak = f"{float(row['peak_mae']):.3f}"
        if gate is None:
            versus, won, status = "—", "—", "baseline"
        else:
            versus, won = signed(-float(gate["mae_gain_pct"])) + "%", f"{gate['windows_won']}/{len(config['origins'])}"
            peak += f" ({signed(float(gate['peak_mae_change_pct']))}%)" if float(gate["peak_mae_change_pct"]) > 0 else ""
            failed = [text.format(gain=config["minimum_mae_gain"]) for column, text in GATES.items() if gate[column] != "True"]
            if failed:
                status = "fails " + ", ".join(failed)
            elif name == initial:
                status = "passes; initial choice"
            elif mae[name] > mae[best] * (1 + config["tie_band"]) + 1e-12:  # the notebook's tie test
                status = f"passes; not within {config['tie_band']:.0%} of {best}"
            else:
                status = f"passes; tie, {initial} preferred"
        body.append([NAMES.get(name, name), *[f"**{v[name]:.3f}**" if v[name] == min(v.values()) else f"{v[name]:.3f}"
                                              for v in (mae, rmse)], versus, won, peak, status])
    results = table([f"CPU, n={models[0]['n']}", "MAE (pp)", "RMSE (pp)", "MAE vs persistence", "Windows won",
                     f"Peak MAE (pp), n={models[0]['peak_n']}", "Gate"], [0, 1, 1, 1, 1, 1, 0], body)

    # <section>Expose each expanding-window error alongside pooled errors;
    # a benefit concentrated in one window is fragile on only 110 training keys.</section>
    window = {(row["candidate"], int(row["origin"])): float(row["mae"])
              for row in rows(snapshot, "validation_window_summary.csv", target=CPU)}
    origins = config["origins"]
    windows = table(["MAE (pp) at origin"] + [str(o) for o in origins], [0] + [1] * len(origins),
                    [[NAMES.get(name, name)] + [f"{window[name, o]:.3f}" for o in origins] for name in mae])

    # <section>Render the fixed sensitivity checks, using extra decimals when
    # normal rounding would hide the candidate/baseline difference.</section>
    labels = {"origins_minus_6": "Origins six bins earlier", "one_bin_delay": "One-bin data delay"}
    results_text = {"True": "holds", "False": "**fails**", "": "n/a (no challenger)"}
    body = []
    for row in rows(snapshot, "sensitivity_summary.csv", target=CPU):
        model, base = float(row["mae"]), float(row["baseline_mae"])
        digits = 3 if f"{model:.3f}" != f"{base:.3f}" else 4
        body.append([labels.get(row["check"], row["check"].replace("leave_out_origin_", "Leave out origin ")),
                     f"{model:.{digits}f}", f"{base:.{digits}f}", results_text[row["mae_advantage_holds"]]])
    sensitivity = table(["Check", f"{initial} MAE (pp)", "persistence MAE (pp)", "Result"], [0, 1, 1, 0], body)

    # <section>Keep trivial always/never-alert rules visible. Group identical
    # forecast-policy outcomes only to reduce repetition, not to drop controls.
    # Costs are illustrative scenario units, not measured cloud savings.</section>
    policies = rows(snapshot, "policy_summary.csv")
    costs = [column for column in policies[0] if column.startswith("cost_miss_")]
    groups = {}
    for row in policies:
        key = tuple(row[c] for c in ["alerts", "misses", "false_alerts", *costs])
        # Forecast-driven policies with identical outcomes share a row; the trivial rules keep their own.
        group = key if row["policy"] not in ("always_alert", "never_alert") else row["policy"]
        label = NAMES.get(row["policy"], row["policy"]) + (" (selected)" if row["selected_model"] == "True" else "")
        groups.setdefault(group, (key, []))[1].append(label)
    lowest = [min(int(key[3 + i]) for key, _ in groups.values()) for i in range(len(costs))]
    policy = table(
        [f"Policy ({policies[0]['windows']} windows, {policies[0]['event_windows']} events)", "Alerts", "Misses",
         "False alerts", *[f"Cost, miss = {c.split('_')[2]}" for c in costs]], [0] + [1] * (3 + len(costs)),
        [[", ".join(names), *key[:3], *[f"**{v}**" if int(v) == low else v for v, low in zip(key[3:], lowest)]]
         for key, names in groups.values()])

    # <section>Show descriptive error magnitudes and buffer coverage in CPU
    # percentage points. This is not a calibrated interval or physical capacity.</section>
    head = {row["statistic"]: row["value"] for row in rows(snapshot, "headroom_summary.csv")}
    headroom = table(
        [f"{head['candidate']}, n={head['n']}", "Median abs. error", "P90 abs. error", "Max abs. error",
         "Largest under-forecast", f"Covered by +{float(head['example_buffer_pp']):g} pp"], [0, 1, 1, 1, 1, 1],
        [["CPU, pp", *[f"{float(head[k]):.2f}" for k in ("median_absolute_error_pp", "p90_absolute_error_pp",
                                                           "max_absolute_error_pp", "max_under_forecast_pp")],
          f"{head['points_within_buffer']} of {head['n']}"]])
    return {"cpu-results": results, "cpu-windows": windows, "sensitivity": sensitivity, "policy": policy,
            "headroom": headroom}


# <function name="claims">
# <how>Load snapshot summaries and build the exact formatted phrases expected in the report’s
# prose, including forecast, workload, error and policy numbers.</how>
# <why>Generated tables alone cannot catch stale narrative claims. Linking the prose to the same
# manifest prevents reporting one run’s tables with another run’s interpretation.</why>
# <tradeoff>This is an explicit phrase checklist, not a semantic audit of every sentence. The
# fixed labels reflect this report and its known candidate set.</tradeoff>
# </function>
def claims(snapshot):
    """Numbers the prose quotes, with their wording, formatted the way the report writes them."""
    manifest = json.loads((snapshot / "frozen_run.json").read_text(encoding="utf-8"))
    tail = {row["statistic"]: float(row["value"]) for row in rows(snapshot, "training_tail_summary.csv")}
    models = {row["candidate"]: row for row in rows(snapshot, "validation_model_summary.csv", target=CPU)}
    window = {(row["candidate"], int(row["origin"])): float(row["mae"])
              for row in rows(snapshot, "validation_window_summary.csv", target=CPU)}
    sensitivity = {row["check"]: float(row["skill"]) for row in rows(snapshot, "sensitivity_summary.csv", target=CPU)}
    acf = {int(row["lag_bins"]): float(row["change_acf"]) for row in rows(snapshot, "training_acf.csv")}
    profile = {int(row["minute"]): row for row in rows(snapshot, "training_hour_profile.csv")}
    bands = {(row["candidate"], row["horizon_band"]): float(row["mae"])
             for row in rows(snapshot, "validation_horizon_bands.csv", target=CPU)}
    segments = {row["segment"]: row for row in rows(snapshot, "training_segments.csv")}
    events = [row for row in rows(snapshot, "policy_events.csv", policy="always_alert") if row["event"] == "True"]
    policy = rows(snapshot, "policy_summary.csv")[0]
    head = {row["statistic"]: row["value"] for row in rows(snapshot, "headroom_summary.csv")}
    forecast = rows(snapshot, "predictions.csv")[0]
    gain = 100 * (1 - float(models["ridge_1"]["mae"]) / float(models["persistence"]["mae"]))
    category = [segments[name] for name in ("Delay-insensitive", "Interactive", "Unknown")]
    covered = int(head["points_within_buffer"]) == int(head["n"])
    return {
        "final count forecast": f"is exactly {float(forecast['active_vm_count']):,.0f} at all "
                                f"{manifest['configuration']['train_size']} development timestamps",
        "final CPU forecast": f"the last development value, {float(forecast[CPU]):.4f}%",
        "ridge_1 pooled gain": f"by {gain:.1f}% ({float(models['ridge_1']['mae']):.3f} vs "
                               f"{float(models['persistence']['mae']):.3f} pp)",
        "leave out origin 62": f"that window left out ({signed(100 * sensitivity['leave_out_origin_62'])}%)",
        "one-bin delay": f"five minutes late ({signed(100 * sensitivity['one_bin_delay'])}%)",
        "SES pooled gain": f"but only by {100 * float(models['ses']['skill']):.1f}%",
        "cohort mean range": f"stays within {tail['cohort_mean_min_pct']:.2f}–{tail['cohort_mean_max_pct']:.2f}%",
        "hot VMs per timestamp": f"{tail['hot_vms_per_timestamp_min']:.0f}–{tail['hot_vms_per_timestamp_max']:.0f} VMs "
                                 f"(median {tail['hot_vms_per_timestamp_median']:.0f})",
        "hottest 10% share": f"supply {tail['cpu_sum_share_of_hottest_10pct_vms']:.1f}% of summed utilization",
        "P90 threshold": f"≥ P90 = {tail['p90_threshold_pct']:.2f}%",
        "P10 threshold": f"≤ P10 = {tail['p10_threshold_pct']:.2f}%",
        "hot readings": f"Only {tail['readings_at_or_above_80_pct']:.2f}% of readings reach 80%, yet "
                        f"{tail['vms_ever_at_or_above_80']:.0f} VMs do so at least once and "
                        f"{tail['vms_with_development_mean_at_or_above_80']:.0f} average it; the median VM averages "
                        f"{tail['median_vm_development_mean_pct']:.1f}%",
        "Interactive own mean": f"Interactive VMs have the highest own mean ({float(segments['Interactive']['mean_cpu']):.1f}%)",
        "Delay-insensitive contribution": f"({float(segments['Delay-insensitive']['contribution_pp']):.2f} of "
                                          f"{sum(float(r['contribution_pp']) for r in category):.2f} pp, "
                                          f"{float(segments['Delay-insensitive']['contribution_share_pct']):.0f}%) because they are "
                                          f"{float(segments['Delay-insensitive']['vm_share_pct']):.0f}% of VMs; 2-core VMs contribute "
                                          f"{float(segments['2']['contribution_share_pct']):.0f}%",
        "24-core bucket": f"({float(segments['24']['mean_cpu']):.1f}%) yet contributes {float(segments['24']['contribution_pp']):.2f} pp",
        "change ACF lags 1, 12, 24": f"{signed(acf[1], 2)} at lag 1 (rises tend to reverse), {signed(acf[12], 2)} at one "
                                     f"hour and {signed(acf[24], 2)} at two hours",
        "minute 20 and 25 deviations": f"minute 20 sits below the hour mean ({signed(float(profile[20]['mean']), 2)} pp "
                                       f"on average) and minute 25 above it ({signed(float(profile[25]['mean']), 2)} pp)",
        "complete hours": f"all {profile[20]['size']} complete hours" if float(profile[20]["max"]) < 0 else "minute 20 not always low",
        "origin 62 window MAE": f"(MAE {window['ridge_1', 62]:.2f} vs {window['persistence', 62]:.2f})",
        "origin 86 window MAE": f"({window['ridge_1', 86]:.2f} vs {window['persistence', 86]:.2f})",
        "largest under-forecast": f"under-forecasts by up to {float(head['max_under_forecast_pp']):.2f} pp",
        "persistence horizon bands": f"Persistence MAE is {bands['persistence', '1-6']:.3f} pp at horizons 1–6, "
                                     f"{bands['persistence', '7-12']:.3f} at 7–12 and {bands['persistence', '13-24']:.3f} at 13–24",
        "first 30 minutes": f"SES ({bands['ses', '1-6']:.3f}) beat ridge_1 ({bands['ridge_1', '1-6']:.3f})",
        "windows and events": f"{WORDS[int(policy['windows'])]} development windows with {WORDS[int(policy['event_windows'])]} events",
        "first crossings": "first crossing " + " and ".join(f"{float(row['first_crossing_minutes']):.0f}" for row in events)
                           + " minutes after the origin",
        "safety margin": f"A {float(head['example_buffer_pp']):g} pp margin above the forecast would have covered "
                         + ("every development observation" if covered else f"{head['points_within_buffer']} of {head['n']}"),
        "margin's worst window": f"came from one window (origin {head['max_under_forecast_origin']})",
        "final alert": f"The final forecast ({float(forecast[CPU]):.2f}%) is "
                       + ("at or above" if manifest["final_alert"] else "below")
                       + f" the development P90 ({manifest['final_alert_threshold']:.2f}%)",
        "predictions digest": f"`{manifest['predictions_sha256'][:8]}…{manifest['predictions_sha256'][-4:]}`",
    }


# <function name="main">
# <how>Resolve the snapshot explicitly cited by the report, verify its prediction digest, render
# each marked table, then check prose phrases and stray tables.</how>
# <why>The challenge requires reproducible communication: every displayed number should point to
# the same frozen submission rather than whichever output directory was most recently run.</why>
# <tradeoff>With --check, a differing table fails without writing. Without it, tables are
# rewritten, but missing prose phrases still fail and must be reviewed manually.</tradeoff>
# </function>
def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="compare only; fail if a table or quoted number differs")
    args = parser.parse_args()
    text = REPORT.read_text(encoding="utf-8")
    cited = re.search(r"tracked snapshot\s+`(reports/evidence/[0-9a-f]{16})/`", text)
    if not cited or not (ROOT / cited.group(1) / "frozen_run.json").is_file():
        sys.exit(f"{REPORT} must cite an existing snapshot as: tracked snapshot `reports/evidence/<16 hex>/`.")
    # <gate>The exact submitted CSV, and the snapshot's own copy that the
    # quoted forecast values come from, must match the cited manifest. Parsed
    # numeric equality is insufficient because the manifest binds file bytes.</gate>
    snapshot = ROOT / cited.group(1)
    manifest = json.loads((snapshot / "frozen_run.json").read_text(encoding="utf-8"))
    if manifest["predictions_sha256"] != hashlib.sha256((ROOT / "predictions.csv").read_bytes()).hexdigest():
        sys.exit(f"{snapshot} does not describe the submitted predictions.csv; cite the snapshot of the frozen run.")
    if manifest["predictions_sha256"] != hashlib.sha256((snapshot / "predictions.csv").read_bytes()).hexdigest():
        sys.exit(f"{snapshot / 'predictions.csv'} does not match its manifest's prediction digest.")
    if text.count("<!-- table:") != text.count("<!-- /table -->"):
        sys.exit("Every <!-- table:NAME --> marker needs its own <!-- /table --> closing marker.")
    # <section>Generate replacements in memory first. The comparison mode is
    # read-only; normal mode may update marked tables after structural checks.</section>
    updated = text
    for name, generated in tables(snapshot).items():
        block = re.compile(BLOCK.format(name=name), re.S)
        if len(block.findall(updated)) != 1:
            sys.exit(f"{REPORT} needs exactly one complete <!-- table:{name} --> block.")
        updated = block.sub(lambda match: f"<!-- table:{name} -->\n{generated}\n<!-- /table -->", updated)
    # <section>Exclude generated tables from narrative checks and collapse
    # whitespace so prose line wrapping does not create false discrepancies.</section>
    prose = re.sub(BLOCK.format(name=r"\S+"), "", updated, flags=re.S)
    if any(line.lstrip().startswith("|") for line in prose.splitlines()):
        sys.exit("A table sits outside the generated blocks; generate it or remove it.")
    prose = " ".join(prose.split())  # quoted numbers may wrap across lines
    missing = [f"  {name}: {quoted}" for name, quoted in claims(snapshot).items() if quoted not in prose]
    if updated != text and args.check:
        sys.exit(f"Report tables differ from {snapshot}; run python reports/report_tables.py to regenerate them.")
    if updated != text:
        REPORT.write_text(updated, encoding="utf-8", newline="\n")
        print(f"Tables regenerated from {snapshot}.")
    if missing:
        sys.exit("Quoted numbers not found in the report's prose:\n" + "\n".join(missing))
    print(f"Every report table and quoted number matches {snapshot}.")


if __name__ == "__main__":
    main()
