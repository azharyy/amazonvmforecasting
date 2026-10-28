# <module name="synthetic end-to-end checks">
# <challenge>ASSIGNMENT sections 3B–3F and 7–9 require correct targets,
# leakage-safe evaluation and clean-checkout reproduction.</challenge>
# <how>This file drives the actual runner on isolated synthetic project copies.
# It checks serialized outputs, refusal timing and immutable evidence.</how>
# <why>Known-answer fixtures and deliberate corruption are more decisive than
# checking that a notebook simply exits successfully on one real dataset.</why>
# <tradeoff>These are protocol and edge-case checks, not an accuracy estimate
# or evidence of generalization beyond this short curated trace.</tradeoff>
# </module>
"""Synthetic end-to-end checks of run_notebook.py; they use synthetic releases only, never challenge_data.

1. A constant-CPU smoke release (134 keys from 600 s, VMs at 0, 20 and 40%) runs to completion and forecasts
   exactly the last 24 keys with count 3 and CPU 20%; so does a release whose CPU is flat until a VM arrives.
2. Freezing and holdout evaluation are separate. A re-freeze archives the previous run. An unchanged frozen run
   evaluates once, writing its opening record before holdout scoring, and a repeat is labelled and
   returns the saved results. Changed configuration, source, data or prediction bytes, archived copies and a
   changed submission copy are refused before any data row is parsed, and existing records stay byte-identical.
   A release whose holdout rows break a validation rule is refused at freeze, before any forecast is written.
3. A data-v1 freeze writes its evidence snapshot, which also records the opening for every copy of the run;
   snapshots are written once and never replaced.

Usage, from the repository root: .venv/Scripts/python.exe tests/run_synthetic_checks.py
"""
import csv
import gzip
import hashlib
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

# <setup>Mirror the contract’s 134-key grid while using a nonzero origin and
# a tiny population; smooth, irregular and constant CPUs stress different fits.</setup>
ROOT = Path(__file__).resolve().parents[1]
SOURCES = ["run_notebook.py", "requirements.txt", "notebooks/01_forecasting.ipynb"]
KEYS = [600 + 300 * step for step in range(134)]
META = ["vm_id", "subscription_id", "deployment_id", "timestamp_vm_created", "timestamp_vm_deleted",
        "max_cpu", "avg_cpu", "p95_max_cpu", "vm_category", "virtual_core_bucket", "memory_gb_bucket"]
LEVELS = [lambda step: 10 + 3 * math.sin(step / 3), lambda step: 30 + step * 7919 % 13 / 2, lambda step: 50.]


# <function name="write_release">
# <how>Create tiny gzip CSVs with the release schema and all 134 five-minute keys. Each callable
# supplies one VM’s CPU; None omits that observation.</how>
# <why>Synthetic values make exact forecasts and failure cases calculable without inspecting real
# holdout targets. The offset grid catches a runner hard-coded to start at zero.</why>
# <tradeoff>A poisoned duplicate appears only after the training boundary. The full target series
# is built before the split, so the freeze must refuse that release in its loader cell.</tradeoff>
# </function>
def write_release(directory, levels, poison_holdout=False):
    """A smoke release without SHA256SUMS: VM i reads levels[i](step) percent at every key (None: absent)."""
    directory.mkdir(parents=True)
    with gzip.open(directory / "vm_cpu_readings.csv.gz", "wt", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["timestamp", "vm_id", "min_cpu", "max_cpu", "avg_cpu"])
        for step, key in enumerate(KEYS):
            for vm, level in enumerate(levels):
                if level(step) is not None:
                    writer.writerow([key, f"vm_{vm}", max(level(step) - 5, 0), min(level(step) + 5, 100), level(step)])
            if poison_holdout and step >= 110:
                writer.writerow([key, "vm_0", 0, 100, 50])  # a conflicting duplicate: the freeze must refuse it in the loader
    with gzip.open(directory / "vm_metadata.csv.gz", "wt", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(META)
        for vm in range(len(levels)):
            writer.writerow([f"vm_{vm}", "sub", f"dep_{vm}", 0, 999999, 50, 20, 45, "Unknown", "2", "4"])


# <function name="copy_project">
# <how>Copy only the runner, pinned requirements and notebook into an isolated test project;
# optionally change one exact notebook fragment.</how>
# <why>Testing temporary copies exercises the real entry point while keeping intentionally broken
# configuration/source edits out of the working checkout.</why>
# <tradeoff>The single-occurrence assertion makes mutation tests fail if a future edit makes their
# replacement ambiguous.</tradeoff>
# </function>
def copy_project(destination, *replacements):
    for name in SOURCES:
        (destination / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination / name)
    notebook = destination / "notebooks/01_forecasting.ipynb"
    text = notebook.read_text(encoding="utf-8")
    for old, new in replacements:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    notebook.write_text(text, encoding="utf-8")
    return destination


# <function name="run">
# <how>Launch the copied runner with this test process’s interpreter, explicit paths, captured
# output and an optional evaluation flag. Return status, log and last started cell.</how>
# <why>A fresh subprocess prevents notebook globals and fitted state leaking between scenarios;
# the same interpreter guarantees the test uses the installed dependencies.</why>
# <tradeoff>Cell-number checks locate early refusal; the unchanged-digest assertions show that
# nothing was rewritten.</tradeoff>
# </function>
def run(project, data, out, *flags, evidence=None):
    """Run a project's runner in a fresh process; return exit code, output and the last cell started."""
    result = subprocess.run(
        [sys.executable, str(project / "run_notebook.py"), "--data", str(data), "--output", str(out),
         "--predictions", f"{out}_submission.csv", "--evidence", str(evidence or f"{out}_evidence"), *flags],
        cwd=project, capture_output=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    cells = re.findall(r"Running notebook cell (\d+)", result.stdout)
    return result.returncode, result.stdout + result.stderr, int(cells[-1]) if cells else 0


# <function name="sha256">
# <how>Hash exact file bytes with SHA-256.</how>
# <why>Byte-level comparison detects rewritten records and newline changes that a parsed numeric
# comparison would miss.</why>
# </function>
def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# <function name="digests">
# <how>Walk all files recursively and map normalized relative names to byte digests.</how>
# <why>Comparing complete directory maps catches both modified contents and added/deleted
# evidence; checking only predictions would miss protocol damage.</why>
# </function>
def digests(directory):
    return {path.relative_to(directory).as_posix(): sha256(path) for path in sorted(directory.rglob("*")) if path.is_file()}


# <function name="read_csv">
# <how>Read CSV rows with the standard library, retaining the header and string fields.</how>
# <why>The assertions inspect the actual serialized output rather than relying on the notebook’s
# own DataFrame validation.</why>
# </function>
def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.reader(stream))


# <function name="teacher_forcing">
# <how>Find the teacher-forcing status column by header name and index its rows by dataset label
# and origin.</how>
# <why>This lets the test distinguish a detected leak from a degenerate control that cannot react
# to future values.</why>
# </function>
def teacher_forcing(out):
    rows = read_csv(out / "leakage_checks.csv")
    column = rows[0].index("control_teacher_forcing")
    return {(row[0], int(row[1])): row[column] for row in rows[1:]}


# <function name="check_constant_releases">
# <how>Run constant and late-arrival populations; check exact output keys/values, submission
# copying and positive-control status.</how>
# <why>The release’s count can be constant, so a zero-error persistence baseline and unresponsive
# leakage control are realistic edge cases. A second population separates constant features from
# constant targets.</why>
# <tradeoff>Three synthetic VMs also show that the code is not restricted to the documented
# 10,000-VM population.</tradeoff>
# </function>
def check_constant_releases(tmp, project):
    data, out = tmp / "constant", tmp / "constant_out"
    write_release(data, [lambda step: 0., lambda step: 20., lambda step: 40.])
    code, log, _ = run(project, data, out)
    assert code == 0, log[-3000:]
    rows = read_csv(out / "predictions.csv")
    assert rows[0] == ["timestamp", "active_vm_count", "aggregate_cpu_utilization"], rows[0]
    assert [int(row[0]) for row in rows[1:]] == KEYS[110:], rows
    assert all(float(row[1]) == 3 and float(row[2]) == 20 for row in rows[1:]), rows
    assert read_csv(Path(f"{out}_submission.csv")) == rows
    status = teacher_forcing(out)
    assert {status["synthetic", o] for o in (38, 62, 86)} == {"detected"}, status
    assert {status["development", o] for o in (38, 62, 86)} == {"not applicable: fitted control cannot respond"}, status
    assert not Path(f"{out}_evidence").exists(), "a smoke run must not write an evidence snapshot"

    # Flat until step 37: at origin 38 the prefix varies but the control's features do not.
    data, out = tmp / "arrival", tmp / "arrival_out"
    write_release(data, [lambda step: 0., lambda step: 20., lambda step: 40., lambda step: None if step < 37 else 50.])
    code, log, _ = run(project, data, out)
    assert code == 0, log[-3000:]
    status = teacher_forcing(out)
    assert status["development", 38] == "not applicable: fitted control cannot respond", status
    assert status["development", 62] == status["development", 86] == "detected", status
    print("1. constant-CPU release: exit 0; last 24 keys, count 3, CPU 20; degenerate controls reported as N/A,"
          " also when only the control's features are constant")


# <function name="expect_refusal">
# <how>Fingerprint existing evidence, request evaluation and require a specific failure before
# data parsing, with every existing output unchanged.</how>
# <why>A nonzero exit alone could hide an unrelated failure. The reason and the cell boundary
# jointly test the intended gate.</why>
# <tradeoff>The bound refers to this notebook’s current cell layout and must change if cells are
# reordered.</tradeoff>
# </function>
def expect_refusal(project, data, out, reason, *flags):
    before = digests(out)
    code, log, last_cell = run(project, data, out, "--evaluate-holdout", *flags)
    assert code != 0 and reason in log, log[-3000:]
    assert last_cell <= 6, f"refused in cell {last_cell}, after full-target construction began"
    assert digests(out) == before, "a refused evaluation changed existing records"


# <function name="check_protocol">
# <how>Freeze, evaluate and repeat synthetic runs; then independently mutate configuration,
# source, archive location, compressed data, predictions and submission bytes.</how>
# <why>The assignment’s public holdout depends on an honest evaluation protocol. These tests show
# that changed procedures cannot silently reuse an old frozen run.</why>
# <tradeoff>Every evaluation here uses fabricated data. These tests do not open or score the real
# final 24 targets.</tradeoff>
# </function>
def check_protocol(tmp, project):
    data, poisoned = tmp / "varying", tmp / "varying_poisoned"
    write_release(data, LEVELS)
    write_release(poisoned, LEVELS, poison_holdout=True)

    out = tmp / "opened"
    assert run(project, data, out)[0] == 0
    frozen = digests(out)
    code, log, _ = run(project, data, out, "--evaluate-holdout")
    assert code == 0 and "Final test evaluated" in log, log[-3000:]
    opened = digests(out)
    assert {name: digest for name, digest in opened.items() if name in frozen} == frozen
    assert "holdout_opened.json" in opened and "holdout_metrics.csv" in opened
    code, log, _ = run(project, data, out, "--evaluate-holdout")
    assert code == 0 and "REPEAT" in log and "Saved results" in log and "Final test evaluated" not in log, log[-3000:]
    assert digests(out) == opened
    print("2a. unchanged frozen run evaluated once; the repeat returned saved results; records unchanged")

    # <scenario>Change the selection policy after evaluation: both evaluating
    # the changed policy and overwriting the opened run must be refused.</scenario>
    gain_project = copy_project(tmp / "project_gain", ("MIN_GAIN = .05", "MIN_GAIN = .06"))
    expect_refusal(gain_project, data, out, "configuration")
    code, log, _ = run(gain_project, data, out)
    assert code != 0 and "sealed" in log and digests(out) == opened, log[-3000:]
    print("2b. after opening: a 6% gain rule is refused for evaluation, and re-freezing the opened run is refused")

    # <scenario>Re-freeze a different policy on the clean release. The old
    # evidence must be archived intact; identical predictions do not excuse
    # changed source or policy.</scenario>
    sealed, refrozen = tmp / "sealed", tmp / "refrozen"
    assert run(project, data, sealed)[0] == 0
    assert run(project, data, refrozen)[0] == 0
    first = digests(refrozen)
    assert run(gain_project, data, refrozen)[0] == 0
    archive = refrozen / "frozen_history" / first["frozen_run.json"][:16]
    assert sha256(refrozen / "frozen_run.json") != first["frozen_run.json"]
    assert digests(archive) == first, "the re-freeze did not archive the previous run byte for byte"
    assert (refrozen / "predictions.csv").read_bytes() == (sealed / "predictions.csv").read_bytes()
    expect_refusal(project, data, archive, "archived copy")
    expect_refusal(gain_project, data, sealed, "configuration")
    eval_project = copy_project(tmp / "project_eval", ("float(train[target].quantile(PEAK_QUANTILE))",
                                                        "float(train[target].quantile(.95))"))
    expect_refusal(eval_project, data, sealed, "source_sha256")
    print("2c. a re-freeze archives the previous run byte-for-byte; archived copies, a changed configuration and a"
          " changed evaluation definition are refused although the predictions are identical")

    # <scenario>Recompression preserves parsed observations but changes bytes;
    # the frozen data fingerprint intentionally notices this provenance change.</scenario>
    regzipped = tmp / "regzipped"
    shutil.copytree(data, regzipped)
    content = gzip.decompress((data / "vm_cpu_readings.csv.gz").read_bytes())
    (regzipped / "vm_cpu_readings.csv.gz").write_bytes(gzip.compress(content, compresslevel=1))
    expect_refusal(project, regzipped, sealed, "data_sha256")
    edited = tmp / "edited"
    shutil.copytree(sealed, edited)
    shutil.copyfile(f"{sealed}_submission.csv", f"{edited}_submission.csv")
    (edited / "predictions.csv").write_bytes((sealed / "predictions.csv").read_bytes() + b"\n")
    expect_refusal(project, data, edited, "predictions_sha256")
    print("2d. changed data bytes and frozen prediction bytes are refused before any data row is parsed")

    # <scenario>The full target series is built before the split, so a holdout
    # row breaking a validation rule stops the freeze in the loader cell: no
    # manifest, predictions or submission copy is written.</scenario>
    refused = tmp / "poisoned_out"
    code, log, last_cell = run(project, poisoned, refused)
    assert code != 0 and "Conflicting duplicate" in log and last_cell == 8, log[-3000:]
    assert not (refused / "frozen_run.json").exists() and not (refused / "predictions.csv").exists()
    assert not Path(f"{refused}_submission.csv").exists()
    # <scenario>On the clean release, an evaluation interrupted right after its
    # opening record (a copied project that divides by zero there, frozen and
    # evaluated with the same code) leaves that record, and the retry is a
    # REPEAT, never a first test.</scenario>
    crash_project = copy_project(tmp / "project_crash", ("= full_target_series(DATA_DIR)", "= 1 / 0 or full_target_series(DATA_DIR)"))
    interrupted = tmp / "interrupted"
    assert run(crash_project, data, interrupted)[0] == 0
    code, log, _ = run(crash_project, data, interrupted, "--evaluate-holdout")
    assert code != 0 and "ZeroDivisionError" in log and (interrupted / "holdout_opened.json").exists(), log[-3000:]
    assert not any((interrupted / name).exists() for name in (
        "holdout_data_audit.json", "holdout_metrics.csv", "holdout_horizon_errors.csv", "holdout_policy.csv")), "evaluation results preceded the opening record"
    record = (interrupted / "holdout_opened.json").read_bytes()
    code, log, _ = run(crash_project, data, interrupted, "--evaluate-holdout")
    assert "REPEAT" in log and (interrupted / "holdout_opened.json").read_bytes() == record, log[-3000:]
    submission = Path(f"{sealed}_submission.csv")
    submission.write_bytes(submission.read_bytes() + b"\n")
    expect_refusal(project, data, sealed, "differs from the frozen predictions")
    print("2e. a release with a conflicting holdout duplicate is refused at freeze (loader cell; no manifest or"
          " predictions); on the clean release the opening record exists before scoring and survives a repeat;"
          " a changed submission copy is refused")


# <function name="check_data_v1_snapshot">
# <how>Create synthetic checksums and temporarily substitute their pinned digests in a copied
# notebook so the genuine-release snapshot branch can be exercised.</how>
# <why>This reaches release-specific evidence behavior without downloading or revealing real
# holdout values; the production notebook’s trust pins remain unchanged.</why>
# <tradeoff>The pseudo-release tests snapshot mechanics, not the authenticity or statistical
# representativeness of data-v1.</tradeoff>
# </function>
def check_data_v1_snapshot(tmp, project, run_notebook):
    data, out = tmp / "pseudo_v1", tmp / "pseudo_v1_out"
    write_release(data, LEVELS)
    (data / "DATA_CARD.md").write_text("Synthetic stand-in for data-v1.\n", encoding="utf-8")
    names = ["vm_cpu_readings.csv.gz", "vm_metadata.csv.gz", "DATA_CARD.md"]
    (data / "SHA256SUMS").write_text("".join(f"{sha256(data / name)}  {name}\n" for name in names), encoding="utf-8")
    pinned = dict(re.findall(r"'(vm_cpu_readings\.csv\.gz|vm_metadata\.csv\.gz|DATA_CARD\.md)': '([0-9a-f]{64})'",
                             (ROOT / SOURCES[2]).read_text(encoding="utf-8")))
    v1_project = copy_project(tmp / "project_v1", *[(pinned[name], sha256(data / name)) for name in names])
    code, log, _ = run(v1_project, data, out)
    assert code == 0 and "Evidence snapshot:" in log, log[-3000:]
    snapshot = Path(f"{out}_evidence") / sha256(out / "frozen_run.json")[:16]
    assert sorted(path.name for path in snapshot.iterdir()) == sorted(run_notebook.EVIDENCE_FILES), snapshot
    assert all(sha256(snapshot / name) == sha256(out / name) for name in run_notebook.EVIDENCE_FILES)

    # A copy made before the first opening is still recognised through the opening record in the snapshot.
    copy = tmp / "pseudo_v1_copy"
    shutil.copytree(out, copy)
    shutil.copyfile(f"{out}_submission.csv", f"{copy}_submission.csv")
    code, log, _ = run(v1_project, data, out, "--evaluate-holdout")
    assert code == 0 and (snapshot / "holdout_opened.json").exists(), log[-3000:]
    record = (snapshot / "holdout_opened.json").read_bytes()
    code, log, _ = run(v1_project, data, copy, "--evaluate-holdout", evidence=Path(f"{out}_evidence"))
    assert code == 0 and "REPEAT" in log and (snapshot / "holdout_opened.json").read_bytes() == record, log[-3000:]
    print("3a. a data-v1 freeze writes its snapshot; its opening record marks a copy's evaluation as a repeat")

    # <scenario>Repeated snapshot writes are idempotent only for identical
    # evidence; a modified existing CSV must be rejected rather than repaired.</scenario>
    first = run_notebook.snapshot_evidence(out, tmp / "evidence")
    files = digests(first)
    assert run_notebook.snapshot_evidence(out, tmp / "evidence") == first and digests(first) == files
    (first / "selection_gates.csv").write_text("tampered", encoding="utf-8")
    try:
        run_notebook.snapshot_evidence(out, tmp / "evidence")
    except RuntimeError:
        pass
    else:
        raise AssertionError("a changed snapshot file was replaced silently")
    print("3b. evidence snapshots are written once per frozen run and never replaced")


# <function name="main">
# <how>Create one temporary workspace, copy the project, then run constant-series, freeze/evaluate
# and snapshot scenarios in order.</how>
# <why>The entry point covers behavior that spans multiple notebook runs; single-run notebook
# assertions cannot prove repeat and tampering behavior.</why>
# <tradeoff>TemporaryDirectory removes fixtures at the end; success is printed only after every
# assertion completes.</tradeoff>
# </function>
def main():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        tmp = Path(directory)
        project = copy_project(tmp / "project")
        sys.path.insert(0, str(project))
        import run_notebook
        check_constant_releases(tmp, project)
        check_protocol(tmp, project)
        check_data_v1_snapshot(tmp, project, run_notebook)
    print("All synthetic checks passed.")


if __name__ == "__main__":
    main()
