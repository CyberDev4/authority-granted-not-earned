#!/usr/bin/env python3
"""Rebuild every run record from the saved model replies.

Each batch folder holds a copy of the code it ran with, every request that was
sent and every raw reply that came back. This script feeds the saved replies
back through that saved code, batch by batch, and compares what the code then
writes with what the record holds: the requests, the replies, the transcripts,
the run records and the progress manifests. See _replay_batch.py for how.

It covers all 58 batches: the 52 real batches of the twelve studies, the 4
batches that were set aside (lab/runs_excluded) and 2 one-run tests against a
fake model. No model is called and no network is used; a pass shows that the
recorded outcomes follow from the saved replies and the saved code. It cannot
show that the replies came from the named model.

Usage:  python3 verify/replay.py [--keep DIR] [--only TEXT]
          --keep DIR   leave the rebuilt batches in DIR to look at
          --only TEXT  replay only batches whose folder name contains TEXT
"""
import collections
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True  # set before the imports below, so no __pycache__ is left behind
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import HERE, LAB, banner, clean_env, verdict

# What a pass has to reproduce: the counts found when the record was checked on 6 October 2026.
EXPECTED = {
    "real":      {"batches": 52, "records": 3004, "rebuilt": 2999, "aborted": 5},
    "set aside": {"batches": 4,  "records": 45,   "rebuilt": 45,   "aborted": 0},
    "fake":      {"batches": 2,  "records": 2,    "rebuilt": 2,    "aborted": 0},
}


def main(argv):
    keep = argv[argv.index("--keep") + 1] if "--keep" in argv else None
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    banner("5. Rebuilding every run record from the saved replies")
    scratch = keep or tempfile.mkdtemp(prefix="gne-replay-")
    os.makedirs(scratch, exist_ok=True)
    batches = []
    for top in ("runs", "runs_excluded"):
        for bj in sorted(glob.glob(os.path.join(LAB, top, "*", "batch.json"))):
            name = os.path.basename(os.path.dirname(bj))
            if only is None or only in name:
                batches.append((top, name))
    totals = collections.defaultdict(collections.Counter)
    problems = []
    for i, (top, name) in enumerate(batches, 1):
        proc = subprocess.run([sys.executable, "-B", os.path.join(HERE, "_replay_batch.py"), LAB, top, name, scratch],
                              env=clean_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        result_path = os.path.join(scratch, name, "result.json")
        if proc.returncode != 0 or not os.path.isfile(result_path):
            problems.append("%s: the replay itself failed\n%s" % (name, proc.stdout[-1500:]))
            print("[%2d/%d] %-70s REPLAY FAILED" % (i, len(batches), name))
            continue
        r = json.load(open(result_path, encoding="utf-8"))
        kind = "set aside" if top == "runs_excluded" else ("real" if r["mode"] == "real" else "fake")
        t = totals[kind]
        t["batches"] += 1
        t["records"] += r["records_saved"]
        t["rebuilt"] += r["records_equal"]
        t["aborted"] += r["aborted"]
        t["aborted_equal"] += r["aborted_equal"]
        t["requests"] += r["requests"]
        t["requests_equal"] += r["requests_equal"]
        t["other_files"] += r["other_files"]
        t["other_files_equal"] += r["other_files_equal"]
        t["traces"] += r["traces"]
        t["traces_equal"] += r["traces_equal"]
        t["records_with_trace"] += r["records_with_trace"]
        t["stood_in"] += len(r["stood_in"])
        t["manifest_lines"] += r["manifest_lines"]
        t["manifests_equal"] += bool(r["manifest_equal"]) or r["manifest_lines"] == 0
        clean = (r["records_equal"] + r["aborted"] == r["records_saved"] and r["aborted_equal"] == r["aborted"]
                 and r["requests_equal"] == r["requests"] and r["other_files_equal"] == r["other_files"]
                 and r["traces_equal"] == r["traces"] and not r["files_missing_in_replay"] and not r["files_extra_in_replay"]
                 and (r["manifest_equal"] or r["manifest_lines"] == 0))
        note = ""
        if r["halted"]:
            note = "  (stops where the original batch stopped: %s)" % r["halted"]
        print("[%2d/%d] %-70s %4d records  %s%s" % (i, len(batches), name, r["records_saved"], "ok" if clean else "DIFFERS", note))
        if not clean:
            problems.append("%s: records differ %s; files differ %s; missing %s; extra %s; traces differ %s; manifest equal %s" % (
                name, r["records_differ"][:5], r["files_differ"][:5], r["files_missing_in_replay"][:5],
                r["files_extra_in_replay"][:5], r["traces_differ"][:5], r["manifest_equal"]))
    if not keep:
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    print("%-10s %8s %8s %8s %8s %10s %12s %8s %9s" % ("batches", "number", "records", "rebuilt", "cut off", "requests", "other files", "traces", "manifest"))
    ok = not problems
    for kind in ("real", "set aside", "fake"):
        t = totals[kind]
        print("%-10s %8d %8d %8d %8d %5d/%-5d %6d/%-6d %4d/%-4d %5d lines" % (
            kind, t["batches"], t["records"], t["rebuilt"], t["aborted"], t["requests_equal"], t["requests"],
            t["other_files_equal"], t["other_files"], t["traces_equal"], t["traces"], t["manifest_lines"]))
        if only is None:
            e = EXPECTED[kind]
            ok = ok and all(t[k] == e[k] for k in e) and t["aborted_equal"] == t["aborted"]
    print()
    print("'rebuilt' = the record the saved code produces from the saved replies equals the saved record in every field.")
    print("'cut off' = runs that were under way when a batch stopped; recorded as aborted and never run again.")
    print("'traces'  = error traces inside records, compared by error type, message and the runner's code lines.")
    stood = sum(t["stood_in"] for t in totals.values())
    print("In %d requests the original call got no reply (timeout or refused connection); the same error was raised again." % stood)
    for p in problems:
        print("PROBLEM", p)
    if only is None:
        t = totals["real"]
        ok = verdict(ok, "%d of %d run records of the twelve studies rebuild from the saved replies; the other %d are cut-off runs" % (
            t["rebuilt"], t["records"], t["aborted"])) and ok
    else:
        ok = verdict(ok, "selected batches rebuilt") and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
