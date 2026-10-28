"""Synthetic end-to-end checks of run_notebook.py; challenge_data and its holdout are never read.

1. A constant-CPU smoke release (134 keys from 600 s, VMs at 0, 20 and 40%) runs to completion and forecasts
   exactly the last 24 keys with count 3 and CPU 20%; so does a release whose CPU is flat until a VM arrives.
2. Freezing and holdout evaluation are separate. A re-freeze archives the previous run. An unchanged frozen run
   evaluates once, writing its opening record before any holdout value is used, and a repeat is labelled and
   returns the saved results. Changed configuration, source, data or prediction bytes, archived copies and a
   changed submission copy are refused before any data row is parsed, and existing records stay byte-identical.
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

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ["run_notebook.py", "requirements.txt", "notebooks/01_forecasting.ipynb"]
KEYS = [600 + 300 * step for step in range(134)]
META = ["vm_id", "subscription_id", "deployment_id", "timestamp_vm_created", "timestamp_vm_deleted",
        "max_cpu", "avg_cpu", "p95_max_cpu", "vm_category", "virtual_core_bucket", "memory_gb_bucket"]
LEVELS = [lambda step: 10 + 3 * math.sin(step / 3), lambda step: 30 + step * 7919 % 13 / 2, lambda step: 50.]


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
                writer.writerow([key, "vm_0", 0, 100, 50])  # a conflicting duplicate: any holdout read fails
    with gzip.open(directory / "vm_metadata.csv.gz", "wt", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(META)
        for vm in range(len(levels)):
            writer.writerow([f"vm_{vm}", "sub", f"dep_{vm}", 0, 999999, 50, 20, 45, "Unknown", "2", "4"])


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


def run(project, data, out, *flags, evidence=None):
    """Run a project's runner in a fresh process; return exit code, output and the last cell started."""
    result = subprocess.run(
        [sys.executable, str(project / "run_notebook.py"), "--data", str(data), "--output", str(out),
         "--predictions", f"{out}_submission.csv", "--evidence", str(evidence or f"{out}_evidence"), *flags],
        cwd=project, capture_output=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    cells = re.findall(r"Running notebook cell (\d+)", result.stdout)
    return result.returncode, result.stdout + result.stderr, int(cells[-1]) if cells else 0


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digests(directory):
    return {path.relative_to(directory).as_posix(): sha256(path) for path in sorted(directory.rglob("*")) if path.is_file()}


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.reader(stream))


def teacher_forcing(out):
    rows = read_csv(out / "leakage_checks.csv")
    column = rows[0].index("control_teacher_forcing")
    return {(row[0], int(row[1])): row[column] for row in rows[1:]}


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


def expect_refusal(project, data, out, reason, *flags):
    before = digests(out)
    code, log, last_cell = run(project, data, out, "--evaluate-holdout", *flags)
    assert code != 0 and reason in log, log[-3000:]
    assert last_cell <= 6, f"refused in cell {last_cell}, after data parsing began"
    assert "Conflicting duplicate" not in log, "the poisoned holdout was read"
    assert digests(out) == before, "a refused evaluation changed existing records"


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

    gain_project = copy_project(tmp / "project_gain", ("MIN_GAIN = .05", "MIN_GAIN = .06"))
    expect_refusal(gain_project, data, out, "configuration")
    code, log, _ = run(gain_project, data, out)
    assert code != 0 and "sealed" in log and digests(out) == opened, log[-3000:]
    print("2b. after opening: a 6% gain rule is refused for evaluation, and re-freezing the opened run is refused")

    sealed, refrozen = tmp / "sealed", tmp / "refrozen"
    assert run(project, poisoned, sealed)[0] == 0
    assert run(project, poisoned, refrozen)[0] == 0
    first = digests(refrozen)
    assert run(gain_project, poisoned, refrozen)[0] == 0
    archive = refrozen / "frozen_history" / first["frozen_run.json"][:16]
    assert sha256(refrozen / "frozen_run.json") != first["frozen_run.json"]
    assert digests(archive) == first, "the re-freeze did not archive the previous run byte for byte"
    assert (refrozen / "predictions.csv").read_bytes() == (sealed / "predictions.csv").read_bytes()
    expect_refusal(project, poisoned, archive, "archived copy")
    expect_refusal(gain_project, poisoned, sealed, "configuration")
    eval_project = copy_project(tmp / "project_eval", ("float(train[target].quantile(PEAK_QUANTILE))",
                                                        "float(train[target].quantile(.95))"))
    expect_refusal(eval_project, poisoned, sealed, "source_sha256")
    print("2c. a re-freeze archives the previous run byte-for-byte; archived copies, a changed configuration and a"
          " changed evaluation definition are refused although the predictions are identical")

    regzipped = tmp / "regzipped"
    shutil.copytree(poisoned, regzipped)
    content = gzip.decompress((poisoned / "vm_cpu_readings.csv.gz").read_bytes())
    (regzipped / "vm_cpu_readings.csv.gz").write_bytes(gzip.compress(content, compresslevel=1))
    expect_refusal(project, regzipped, sealed, "data_sha256")
    edited = tmp / "edited"
    shutil.copytree(sealed, edited)
    shutil.copyfile(f"{sealed}_submission.csv", f"{edited}_submission.csv")
    (edited / "predictions.csv").write_bytes((sealed / "predictions.csv").read_bytes() + b"\n")
    expect_refusal(project, poisoned, edited, "predictions_sha256")
    print("2d. changed data bytes and frozen prediction bytes are refused before any data row is parsed")

    code, log, _ = run(project, poisoned, sealed, "--evaluate-holdout")
    assert code != 0 and "Conflicting duplicate" in log and (sealed / "holdout_opened.json").exists(), log[-3000:]
    record = (sealed / "holdout_opened.json").read_bytes()
    code, log, _ = run(project, poisoned, sealed, "--evaluate-holdout")
    assert "REPEAT" in log and (sealed / "holdout_opened.json").read_bytes() == record, log[-3000:]
    submission = Path(f"{sealed}_submission.csv")
    submission.write_bytes(submission.read_bytes() + b"\n")
    expect_refusal(project, poisoned, sealed, "differs from the frozen predictions")
    print("2e. the opening record exists before the holdout is read and survives repeats; a changed submission"
          " copy is refused")


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
