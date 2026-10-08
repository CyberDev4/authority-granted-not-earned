"""Read-only wrapper around the frozen gne_core_c1/analyze_c1.py (logged in DEVIATIONS.md).
The frozen run.py writes resume-aborted episodes without 'family'/'target_outcome', which the frozen
analyzer cannot read. This fills those two fields IN MEMORY ONLY (family from run.ITEMS, outcome = unknown).
No data file or frozen code is changed. Usage: python analyze_c1_wrapped.py runs/gne_core_c1-*-real-*
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "gne_core_c1"))
import analyze_c1, run

_load = analyze_c1.load
def load(folders):
    batches, rows = _load(folders)
    for r in rows:
        if r["_stage"] == "main" and "family" not in r:
            r["family"] = run.ITEMS[r["item"]]["family"]
            r["target_outcome"] = None
            print("WRAPPER: %s %s %s -> family=%s, outcome=unknown (%s)" % (
                r["_model"], r["_stage"], r["_id"], r["family"], r.get("ending")))
    return batches, rows
analyze_c1.load = load

if __name__ == "__main__":
    analyze_c1.main()
