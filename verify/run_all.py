#!/usr/bin/env python3
"""Run every check in this repository, in order, and print one summary.

    python3 verify/run_all.py           run everything
    python3 verify/run_all.py --quiet   print only the summary (full output on a failure)
    python3 verify/run_all.py 4 6       run only checks 4 and 6

Needs Python 3.10 or later and nothing else: no packages, no model, no network.
Nothing is written into lab/. Each check can also be run alone; see README.md.

What a pass shows, check by check:
  1  the files under lab/ are the files listed in manifest/MANIFEST.tsv, byte for byte
  2  every hash in a freeze record matches, and each batch ran the frozen code
  3  the unit tests inside the study packages pass
  4  each study's own analysis, run again, gives the output the project saved, byte for byte
  5  the saved replies, fed back through the code saved with each batch, rebuild the run records
  6  separate code, reading the raw replies of the C studies, arrives at the same counts and p-values,
     and recounts the exploratory counts quoted on the pages
  7  the label tables rebuild from the saved labels, and every quoted phrase is in the reading sheet
     for its run
  8  the tables of batch times, long waits and overlaps rebuild
  9  the texts quoted in docs/how-a-run-works.md match the code and the saved requests, the data
     dictionary names every top-level field, and the main tables on README.md and RESULTS.md match
     results/tables/
  F  the figure in results/figures/ is the one its script draws from the tables

What no check here can show: that the saved replies came from the named models, or that
every sentence on the pages is right. See README.md, "Check it yourself".
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

CHECKS = [
    ("1", "Files", ["verify/check_manifest.py"]),
    ("2", "Freezes", ["verify/check_freezes.py"]),
    ("3", "Unit tests", ["verify/run_unit_tests.py"]),
    ("4", "Analyses", ["verify/reanalyze.py"]),
    ("5", "Replay", ["verify/replay.py"]),
    ("6", "Recount", ["verify/recount.py"]),
    ("7", "Labels", ["verify/label_tables.py"]),
    ("8", "Timeline", ["verify/timeline.py"]),
    ("9", "Pages", ["verify/check_docs.py"]),
    ("F", "Figure", ["results/figures/make_figure.py", "--check"]),
]


def main(argv):
    quiet = "--quiet" in argv
    wanted = [a.upper() for a in argv if not a.startswith("--")]
    unknown = [w for w in wanted if w not in [c[0] for c in CHECKS]]
    if unknown:
        print("unknown check: %s (choose from %s)" % (", ".join(unknown), " ".join(c[0] for c in CHECKS)))
        return 2
    if sys.version_info < (3, 10):
        print("Python 3.10 or later is needed; this is %s" % sys.version.split()[0])
        return 2

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"   # never leave __pycache__ folders next to the record
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONUTF8"] = "1"                # the same text encoding on every system
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("PYTHONPATH", None)

    results = []
    started = time.time()
    for key, name, args in CHECKS:
        if wanted and key not in wanted:
            continue
        cmd = [sys.executable, "-B"] + args
        t0 = time.time()
        if quiet:
            proc = subprocess.run(cmd, cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if proc.returncode != 0:
                sys.stdout.write(proc.stdout.decode("utf-8", "replace"))
        else:
            sys.stdout.flush()
            proc = subprocess.run(cmd, cwd=REPO, env=env)
        results.append((key, name, " ".join(["python3"] + args), proc.returncode, time.time() - t0))
        sys.stdout.flush()

    print()
    print("=" * 78)
    print("Summary (Python %s)" % sys.version.split()[0])
    print("=" * 78)
    for key, name, shown, code, seconds in results:
        print("%-4s  %s  %-11s %5.0f s   %s" % ("PASS" if code == 0 else "FAIL", key, name, seconds, shown))
    failed = [r for r in results if r[3] != 0]
    print()
    if failed:
        print("FAIL  %d of %d checks failed: %s" % (len(failed), len(results), ", ".join(r[1] for r in failed)))
    else:
        if len(results) == len(CHECKS):
            print("PASS  all nine checks and the figure check passed in %.0f seconds" % (time.time() - started))
        else:
            print("PASS  %s passed in %.0f seconds" % (
                "the selected check" if len(results) == 1 else "the %d selected checks" % len(results), time.time() - started))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
