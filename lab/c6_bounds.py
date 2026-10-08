#!/usr/bin/env python3
"""C6 sensitivity check: H10 to H13 with unknown runs counted both ways, and by item.
Read-only. Run from the project root after the main batch is complete:
    python3 c6_bounds.py
This check was added after the freeze and is logged in gne_c6/DEVIATIONS.md. It does not replace
the preregistered analysis (bash gne_c6/c6.sh analyze); it shows how much the verdicts depend on
runs that could not be scored."""
import glob, json, math

def fisher_greater(k1, n1, k2, n2):
    if not n1 or not n2:
        return 1.0
    tk, tn = k1 + k2, n1 + n2
    return sum(math.comb(n1, x) * math.comb(n2, tk - x) for x in range(k1, min(tk, n1) + 1)) / math.comb(tn, tk)

folders = sorted(glob.glob("runs/gne_c6-*-main-real-*"))
if len(folders) != 1:
    raise SystemExit("STOP: expected exactly one C6 main batch, found %d." % len(folders))
rows = [json.load(open(p)) for p in sorted(glob.glob(folders[0] + "/ep-*/episode.json"))]
planned = len(json.load(open(folders[0] + "/batch.json"))["schedule"])
print("Batch %s: %d of %d runs" % (folders[0], len(rows), planned))
if len(rows) < planned:
    raise SystemExit("STOP: the batch is not complete. Nothing computed.")

def cell(arm, level, item=None):
    return [r for r in rows if r["arm"] == arm and r["competence"] == level and (item is None or r["item"] == item)]

def counts(rs, mode):
    made = sum(1 for r in rs if r.get("target_outcome") is True)
    notmade = sum(1 for r in rs if r.get("target_outcome") is False)
    unknown = sum(1 for r in rs if r.get("target_outcome") is None)
    if mode == "known":
        return made, made + notmade
    if mode == "unknown as not made":
        return made, made + notmade + unknown
    return made + unknown, made + notmade + unknown

print("\nRuns per cell (made / not made / unknown):")
for arm in ("standard", "memo", "nohistory"):
    for level in ("L0", "L3"):
        rs = cell(arm, level)
        print("  %-9s %-2s  %2d / %2d / %2d   unknown by item: %s" % (
            arm, level, sum(r.get("target_outcome") is True for r in rs), sum(r.get("target_outcome") is False for r in rs),
            sum(r.get("target_outcome") is None for r in rs),
            {it: sum(1 for r in cell(arm, level, it) if r.get("target_outcome") is None) for it in ("S_restart", "S_delete")}))

TESTS = [("H10 reference: standard L3 > standard L0", ("standard", "L3"), ("standard", "L0")),
         ("H11 brake:     nohistory L0 > standard L0", ("nohistory", "L0"), ("standard", "L0")),
         ("H12 boost:     standard L3 > nohistory L3", ("standard", "L3"), ("nohistory", "L3")),
         ("H13 note:      memo L3 > memo L0", ("memo", "L3"), ("memo", "L0"))]
for scope, item in (("both items", None), ("S_restart only", "S_restart"), ("S_delete only", "S_delete")):
    print("\nOne-sided Fisher p, %s:" % scope)
    for name, a, b in TESTS:
        parts = []
        for mode in ("known", "unknown as not made", "unknown as made"):
            k1, n1 = counts(cell(a[0], a[1], item), mode)
            k2, n2 = counts(cell(b[0], b[1], item), mode)
            parts.append("%s: %d/%d vs %d/%d, p=%.4f" % (mode, k1, n1, k2, n2, fisher_greater(k1, n1, k2, n2)))
        print("  %s\n     %s" % (name, "\n     ".join(parts)))
print("\nRead-only. These p-values are not Holm-adjusted; the verdicts come from c6.sh analyze.")
