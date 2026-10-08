"""Read-only wrapper for the frozen C4 analysis (logged in gne_c4/DEVIATIONS.md).

The frozen analyze_c4.py divides by zero when a main-stage cell has no known outcomes (gpt-oss:20b in C4:
113 of 120 runs unknown). This wrapper changes nothing in the package: it catches that one error, reports
the model as NOT TESTABLE, and lets the rest of the frozen analysis (other models, Holm, H5) run as written.

Usage, from the project root: python analyze_c4_wrapped.py runs/gne_c4-*-real-*
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "gne_c4"))
import analyze_c4 as A  # noqa: E402

_report = A.model_report


def model_report(model, rows):
    try:
        return _report(model, rows)
    except ZeroDivisionError:
        print("  NOT TESTABLE: a main-stage cell has no known outcomes, so H4 and the reading are not computed."
              " (Read-only wrapper; see gne_c4/DEVIATIONS.md.)")
        return {"model": model, "controls": None, "instrument": None, "scope_l0": (0, 0), "scope_l3": (0, 0),
                "tech_l0": (0, 0), "tech_l3": (0, 0), "reading": "NOT TESTABLE (empty cell)", "p_h1": None}


A.model_report = model_report

if __name__ == "__main__":
    A.main()
