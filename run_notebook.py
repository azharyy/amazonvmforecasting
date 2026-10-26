"""Run this Python-only notebook's cells in order in a fresh Python process."""
import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("challenge_data"))
    parser.add_argument("--output", type=Path, default=Path("reports/generated"))
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
    print(f"Created {args.output / 'predictions.csv'}")


if __name__ == "__main__":
    main()
