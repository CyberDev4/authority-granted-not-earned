#!/usr/bin/env python3
"""Run the unit tests that ship inside each study package.

Each package's launcher runs `python -m unittest discover -s PACKAGE -p TESTFILE`
from the project folder; this script does the same for all 14 packages and
compares the number of tests with the number expected. The tests use a fake
model; none of them calls Ollama or the network.

Usage:  python3 verify/run_unit_tests.py
"""
import os
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True  # set before the imports below, so no __pycache__ is left behind
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import LAB, banner, clean_env, verdict

# package, test file, number of tests
PACKAGES = [
    ("phase1_v6_frozen_2x2", "test_v6.py", 30),
    ("phase1_v7_timeout", "test_v7.py", 34),
    ("phase1_x1_scope_explicit", "test_x1.py", 14),
    ("gne_core_c1_superseded_unrun", "test_c1.py", 18),
    ("gne_core_c1", "test_c1.py", 18),
    ("gne_c1m", "test_c1m.py", 23),
    ("gne_c2m", "test_c2m.py", 25),
    ("gne_core_c2", "test_c2.py", 21),
    ("gne_c3", "test_c3.py", 26),
    ("gne_c4", "test_c4.py", 29),
    ("gne_c4g", "test_c4g.py", 34),
    ("gne_c5", "test_c5.py", 16),
    ("gne_c5p", "test_c5p.py", 24),
    ("gne_c6", "test_c6.py", 19),
]


def main():
    banner("3. Unit tests inside the 14 study packages")
    ok = True
    total = 0
    with tempfile.TemporaryDirectory(prefix="gne-tests-") as tmp:
        env = clean_env()
        env["TMPDIR"] = tmp  # anything a test writes goes here, not into lab/
        for pkg, test_file, expected in PACKAGES:
            proc = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", pkg, "-p", test_file],
                                  cwd=LAB, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            ran = re.findall(r"^Ran (\d+) tests? in", proc.stdout, re.M)
            n = int(ran[-1]) if ran else 0
            last = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
            good = proc.returncode == 0 and n == expected and last.startswith("OK")
            total += n
            print("%-30s %-12s ran %3d of %3d   %s" % (pkg, test_file, n, expected, last if good else "FAILED: " + last))
            if not good:
                ok = False
                print(proc.stdout[-2000:])
    ok = verdict(ok and total == 331, "%d unit tests ran and passed (expected 331)" % total) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
