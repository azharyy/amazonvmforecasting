"""Run this Python-only notebook's cells in order in a fresh Python process.

By default the run develops and freezes into --output. With --evaluate-holdout it evaluates the run
already frozen in --output, after verifying its fingerprints; nothing is frozen or overwritten.
"""
# <module name="notebook_runner">
# <challenge>ASSIGNMENT sections 7 and 9 require one reproducible prediction
# command and protection of the final 24 target values. This file orchestrates
# execution; target construction, models and tests live in the notebook.</challenge>
# <how>CLI paths -> optional evaluation preflight -> shared notebook namespace ->
# ordered code cells -> verified submission copy -> compact evidence snapshot.</how>
# <why>The notebook is the single implementation used by both an interactive
# reader and this fresh-process runner; maintaining a second training pipeline
# would let the analysis and the submitted predictions drift apart.</why>
# <tradeoff>This runner supports ordinary Python cells, not arbitrary notebook
# magics or asynchronous widgets; no Jupyter server is needed for these cells.</tradeoff>
# </module>
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

# <evidence_contract>
# This explicit allowlist captures the small tables needed to audit the model
# decision. It avoids copying the raw Azure data, all figures, or a growing output
# directory into every tracked snapshot (SUBMISSION repository hygiene).
# </evidence_contract>
# Compact evidence kept in git for each frozen data-v1 run; bulky outputs stay ignored in --output.
EVIDENCE_FILES = [
    "frozen_run.json", "environment.lock.txt", "predictions.csv", "validation_model_summary.csv",
    "validation_window_summary.csv", "selection_gates.csv", "sensitivity_summary.csv",
    "validation_horizon_bands.csv", "headroom_summary.csv", "policy_summary.csv", "policy_events.csv",
    "leakage_checks.csv", "training_tail_summary.csv", "training_segments.csv", "training_acf.csv",
    "training_hour_profile.csv",
]


# <function name="sha256">
# <how>Read the exact file bytes, hash them with SHA-256, return hexadecimal text.</how>
# <why>Digest equality detects changes that a filename or modification time misses;
# the same primitive checks frozen predictions and write-once evidence.</why>
# <tradeoff>read_bytes loads the whole file; these are small manifests and tables.
# The notebook uses a streaming hash for the much larger release archive.</tradeoff>
# </function>
def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# <function name="snapshot_evidence">
# <how>Use the first 16 characters of the complete manifest's digest as a directory
# key, copy each allowed evidence file if absent, and reject different existing
# bytes. Return the directory so the CLI can identify the resulting snapshot.</how>
# <why>Content-addressing separates freezes even when forecasts happen to match;
# write-once checks preserve the evidence underlying a report or evaluation.</why>
# <tradeoff>The shortened directory key is convenient, not a mathematical guarantee
# against collisions. Existing-file digest checks catch conflicting copied files;
# the full manifest and prediction digests remain the provenance records.</tradeoff>
# </function>
def snapshot_evidence(output, evidence):
    """Copy the frozen run's compact evidence to evidence/<manifest digest>/, never replacing a file."""
    target = evidence / sha256(output / "frozen_run.json")[:16]
    target.mkdir(parents=True, exist_ok=True)
    for name in EVIDENCE_FILES:
        source, copy = output / name, target / name
        # <why>A historical or smoke run can omit an optional summary. Report
        # that omission rather than inventing evidence or copying a stale file.</why>
        if not source.exists():
            print(f"Evidence file not produced by this run: {name}")
            continue
        # <how>Identical repeat calls are harmless; mismatched files stop the
        # copy rather than silently rewriting evidence for an earlier freeze.</how>
        if not copy.exists():
            shutil.copyfile(source, copy)
        elif sha256(copy) != sha256(source):
            raise RuntimeError(f"{copy} already exists with different content; evidence is never replaced.")
    return target


# <function name="main">
# <how>Resolve input/output paths, reject invalid evaluation requests before
# executing cells, then execute the saved notebook from top to bottom. A normal
# run copies its frozen predictions and optionally snapshots genuine data-v1.</how>
# <why>The two modes deliberately have different lifecycles: development creates
# a decision; evaluation consumes the decision already frozen. Combining fitting
# and final scoring in one implicit mode would weaken holdout discipline.</why>
# <tradeoff>The command can overwrite its chosen submission path in development;
# use --predictions and --evidence overrides for exploratory runs. It does not
# enforce a repository sandbox or prevent someone bypassing the runner.</tradeoff>
# </function>
def main():
    # <interface>The defaults reproduce README's submission workflow. Separate
    # paths also allow the synthetic suite to run in isolated temporary projects
    # without touching the real release or tracked submission.</interface>
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
        # <evaluation_gate>
        # Refuse archived copies, missing manifests and a missing/changed submission
        # before any notebook code runs. Notebook gates then compare data, source,
        # configuration and predictions before parsing target-bearing data rows.
        # Archives are evidence, not new opportunities to evaluate a revised model.
        # </evaluation_gate>
        # Checked before any cell runs or anything is created: evaluate an original frozen run and its submission.
        output = args.output.resolve()
        if "frozen_history" in output.parts or output.is_relative_to(args.evidence.resolve()):
            raise RuntimeError(f"{args.output} is an archived copy of a frozen run; evaluate its original output directory.")
        if not manifest.is_file():
            raise RuntimeError(f"No frozen run in {args.output}; freeze it first with the development command.")
        if not args.predictions.is_file() or (
                sha256(args.predictions) != json.loads(manifest.read_text(encoding="utf-8"))["predictions_sha256"]):
            raise RuntimeError(f"{args.predictions} is missing or differs from the frozen predictions; evaluation refused.")
    # <configuration>Pass explicit absolute paths through the same environment
    # interface used by interactive cells. The notebook can locate sources from a
    # different working directory without changing data-dependent model choices.</configuration>
    os.environ["CWFC_ROOT"] = str(root)
    os.environ["CWFC_DATA"] = str(args.data.resolve())
    os.environ["CWFC_OUTPUT"] = str(args.output.resolve())
    os.environ["CWFC_EVIDENCE"] = str(args.evidence.resolve())
    os.environ["CWFC_EVALUATE_HOLDOUT"] = "1" if args.evaluate_holdout else "0"
    notebook = json.loads((root / "notebooks/01_forecasting.ipynb").read_text(encoding="utf-8"))
    # <why>A noninteractive backend writes the report figures on a cloud machine
    # with no display; closing each shown figure prevents many open figures.</why>
    os.environ["MPLBACKEND"] = "Agg"
    import matplotlib.pyplot as plt
    # Figures are saved by the cells; the command-line run has no inline display.
    plt.show = lambda: plt.close("all")
    # <how>Keep original cell numbers for failure messages, skip markdown, and
    # share one namespace so later cells receive earlier variables and functions.
    # This mirrors an ordered fresh-kernel run rather than hidden notebook state.</how>
    cells = [(number, "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"])
             for number, cell in enumerate(notebook["cells"], start=1) if cell["cell_type"] == "code"]
    # The source fingerprint covers exactly the code executed below, not whatever is on disk later.
    # <provenance>The notebook hashes EXECUTED_CODE_CELLS, including comments,
    # rather than rereading potentially edited code after execution has started.
    # Comment-only edits therefore require a new freeze before final evaluation;
    # unchanged mathematics does not imply an unchanged source fingerprint.</provenance>
    namespace = {"__name__": "__main__", "EXECUTED_CODE_CELLS": [source for _, source in cells]}
    for number, source in cells:
        print(f"Running notebook cell {number}", flush=True)
        exec(compile(source, f"notebook-cell-{number}", "exec"), namespace)
    if args.evaluate_holdout:
        # <why>Evaluation must never replace the original submission or mint a
        # new freeze; the notebook has already saved or returned evaluation results.</why>
        return
    # <submission>Publish only the notebook's validated frozen predictions and
    # recheck the copied bytes against its manifest. The submission is a product
    # of the frozen procedure, not a second calculation or a hand-edited CSV.</submission>
    shutil.copyfile(args.output / "predictions.csv", args.predictions)
    frozen = json.loads(manifest.read_text(encoding="utf-8"))
    if sha256(args.predictions) != frozen["predictions_sha256"]:
        raise RuntimeError(f"{args.predictions} does not match the frozen predictions.")
    print(f"Created {args.output / 'predictions.csv'} and its frozen copy {args.predictions}")
    # <why>Only exact data-v1 runs become release evidence. Tiny reviewer smoke
    # datasets remain useful tests but must not be presented as release results.</why>
    if frozen["data_v1_release"]:
        print("Evidence snapshot:", snapshot_evidence(args.output, args.evidence))


# <entrypoint>Importing snapshot_evidence in synthetic tests has no training
# side effect; only an explicit script invocation dispatches the CLI.</entrypoint>
if __name__ == "__main__":
    main()
