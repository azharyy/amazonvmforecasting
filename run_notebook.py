"""Run this Python-only notebook's cells in order in a fresh Python process.

By default the run develops and freezes into --output. With --evaluate-holdout it evaluates the run
already frozen in --output, after verifying its fingerprints; nothing is frozen or overwritten.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

# Compact evidence kept in git for each frozen data-v1 run; bulky outputs stay ignored in --output.
EVIDENCE_FILES = [
    "frozen_run.json", "environment.lock.txt", "predictions.csv", "validation_model_summary.csv",
    "validation_window_summary.csv", "selection_gates.csv", "sensitivity_summary.csv",
    "validation_horizon_bands.csv", "headroom_summary.csv", "policy_summary.csv", "policy_events.csv",
    "leakage_checks.csv", "training_tail_summary.csv", "training_segments.csv", "training_acf.csv",
    "training_hour_profile.csv",
]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot_evidence(output, evidence):
    """Copy the frozen run's compact evidence to evidence/<manifest digest>/, never replacing a file."""
    target = evidence / sha256(output / "frozen_run.json")[:16]
    target.mkdir(parents=True, exist_ok=True)
    for name in EVIDENCE_FILES:
        source, copy = output / name, target / name
        if not source.exists():
            print(f"Evidence file not produced by this run: {name}")
            continue
        if not copy.exists():
            shutil.copyfile(source, copy)
        elif sha256(copy) != sha256(source):
            raise RuntimeError(f"{copy} already exists with different content; evidence is never replaced.")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("challenge_data"))
    parser.add_argument("--output", type=Path, default=Path("reports/generated"))
    parser.add_argument("--predictions", type=Path, default=Path("predictions.csv"),
                        help="submission copy of the frozen predictions")
    parser.add_argument("--evidence", type=Path, default=Path("reports/evidence"),
                        help="where a data-v1 freeze saves its compact evidence snapshot")
    parser.add_argument("--evaluate-holdout", action="store_true",
                        help="evaluate the run already frozen in --output; never freezes")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    manifest = args.output / "frozen_run.json"
    if args.evaluate_holdout:
        # Checked before any cell runs or anything is created: evaluate an original frozen run and its submission.
        output = args.output.resolve()
        if "frozen_history" in output.parts or output.is_relative_to(args.evidence.resolve()):
            raise RuntimeError(f"{args.output} is an archived copy of a frozen run; evaluate its original output directory.")
        if not manifest.is_file():
            raise RuntimeError(f"No frozen run in {args.output}; freeze it first with the development command.")
        if not args.predictions.is_file() or (
                sha256(args.predictions) != json.loads(manifest.read_text(encoding="utf-8"))["predictions_sha256"]):
            raise RuntimeError(f"{args.predictions} is missing or differs from the frozen predictions; evaluation refused.")
    os.environ["CWFC_ROOT"] = str(root)
    os.environ["CWFC_DATA"] = str(args.data.resolve())
    os.environ["CWFC_OUTPUT"] = str(args.output.resolve())
    os.environ["CWFC_EVIDENCE"] = str(args.evidence.resolve())
    os.environ["CWFC_EVALUATE_HOLDOUT"] = "1" if args.evaluate_holdout else "0"
    notebook = json.loads((root / "notebooks/01_forecasting.ipynb").read_text(encoding="utf-8"))
    os.environ["MPLBACKEND"] = "Agg"
    import matplotlib.pyplot as plt
    # Figures are saved by the cells; the command-line run has no inline display.
    plt.show = lambda: plt.close("all")
    cells = [(number, "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"])
             for number, cell in enumerate(notebook["cells"], start=1) if cell["cell_type"] == "code"]
    # The source fingerprint covers exactly the code executed below, not whatever is on disk later.
    namespace = {"__name__": "__main__", "EXECUTED_CODE_CELLS": [source for _, source in cells]}
    for number, source in cells:
        print(f"Running notebook cell {number}", flush=True)
        exec(compile(source, f"notebook-cell-{number}", "exec"), namespace)
    if args.evaluate_holdout:
        return
    shutil.copyfile(args.output / "predictions.csv", args.predictions)
    frozen = json.loads(manifest.read_text(encoding="utf-8"))
    if sha256(args.predictions) != frozen["predictions_sha256"]:
        raise RuntimeError(f"{args.predictions} does not match the frozen predictions.")
    print(f"Created {args.output / 'predictions.csv'} and its frozen copy {args.predictions}")
    if frozen["data_v1_release"]:
        print("Evidence snapshot:", snapshot_evidence(args.output, args.evidence))


if __name__ == "__main__":
    main()
