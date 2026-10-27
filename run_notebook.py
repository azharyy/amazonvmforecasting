"""Run this Python-only notebook's cells in order in a fresh Python process."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("challenge_data"))
    parser.add_argument("--output", type=Path, default=Path("reports/generated"))
    parser.add_argument("--predictions", type=Path, default=Path("predictions.csv"),
                        help="submission copy of the frozen predictions")
    parser.add_argument("--evaluate-holdout", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    os.environ["CWFC_ROOT"] = str(root)
    os.environ["CWFC_DATA"] = str(args.data.resolve())
    os.environ["CWFC_OUTPUT"] = str(args.output.resolve())
    os.environ["CWFC_EVALUATE_HOLDOUT"] = "1" if args.evaluate_holdout else "0"
    notebook = json.loads((root / "notebooks/01_forecasting.ipynb").read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    os.environ["MPLBACKEND"] = "Agg"
    import matplotlib.pyplot as plt
    # Figures are saved by the cells; the command-line run has no inline display.
    plt.show = lambda: plt.close("all")
    namespace = {"__name__": "__main__"}
    for number, cell in enumerate(notebook["cells"], start=1):
        if cell["cell_type"] == "code":
            source = cell["source"]
            if isinstance(source, list):
                source = "".join(source)
            print(f"Running notebook cell {number}", flush=True)
            exec(compile(source, f"notebook-cell-{number}", "exec"), namespace)
    shutil.copyfile(args.output / "predictions.csv", args.predictions)
    frozen = json.loads((args.output / "frozen_run.json").read_text(encoding="utf-8"))
    if hashlib.sha256(args.predictions.read_bytes()).hexdigest() != frozen["predictions_sha256"]:
        raise RuntimeError(f"{args.predictions} does not match the frozen predictions.")
    print(f"Created {args.output / 'predictions.csv'} and its frozen copy {args.predictions}")


if __name__ == "__main__":
    main()
