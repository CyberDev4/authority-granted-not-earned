#!/usr/bin/env python3
"""Re-run every study's analysis on the saved runs and compare the output, byte for byte.

For ten analyses the project saved an output: seven in lab/logs/, and three (C2,
C1M, C3) written when the release snapshot of 1 October was built. This script
runs the same command again, from lab/, and compares what comes out with
  (a) the saved output inside the record (lab/logs/... or the 1 October release
      tarball), and
  (b) the copy of it kept in results/analysis-outputs/ for easy reading.
V6, V7 and X1 have no saved output. Their analyses are run too and compared
with the copies in results/analysis-outputs/, which were generated on
6 October 2026. The file that the audit script writes (authority_review.txt) is
rebuilt the same way.

Nothing is written into lab/. No model and no network are used.

Usage:  python3 verify/reanalyze.py            compare
        python3 verify/reanalyze.py --show C5  print one regenerated output
"""
import glob
import hashlib
import os
import subprocess
import sys
import tarfile
import tempfile

sys.dont_write_bytecode = True  # set before the imports below, so no __pycache__ is left behind
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import LAB, REPO, banner, clean_env, verdict

OUT = os.path.join(REPO, "results", "analysis-outputs")
TARBALL = "release/granted-not-earned-20261001.tar.gz"
TAR_TOP = "granted-not-earned-20261001/"

# name, [script, glob or literal arguments...], where the project saved the output ("" = it did not)
ANALYSES = [
    ("V6", ["phase1_v6_frozen_2x2/analyze.py", "runs/phase1_v6_frozen_2x2-baseline-real-*"], ""),
    ("X1", ["phase1_x1_scope_explicit/analyze_x1.py", "runs/phase1_x1_scope_explicit-scope-real-*"], ""),
    ("V7", ["phase1_v7_timeout/analyze.py", "runs/phase1_v7_timeout-baseline-real-*"], ""),
    ("V7_first_batch_alone", ["phase1_v7_timeout/analyze.py", "runs/phase1_v7_timeout-baseline-real-20260927T031912983853Z"], ""),
    ("V7_second_batch_alone", ["phase1_v7_timeout/analyze.py", "runs/phase1_v7_timeout-baseline-real-20260927T063552038743Z"], ""),
    ("C1", ["analyze_c1_wrapped.py", "runs/gne_core_c1-*-real-*"], "logs/c1_analysis_final.log"),
    ("C2", ["gne_core_c2/analyze_c2.py", "runs/gne_core_c2-*-real-*"], "tar:results/C2_analysis.txt"),
    ("C1M", ["gne_c1m/analyze_c1m.py", "runs/gne_c1m-*-real-*"], "tar:results/C1M_analysis.txt"),
    ("C3", ["gne_c3/analyze_c3.py", "runs/gne_c3-*-real-*"], "tar:results/C3_analysis.txt"),
    ("C4", ["analyze_c4_wrapped.py", "runs/gne_c4-*-real-*"], "logs/c4_analysis_wrapped.txt"),
    ("C4G", ["gne_c4g/analyze_c4g.py", "runs/gne_c4g-*-real-*"], "logs/c4g_analysis.txt"),
    ("C5", ["gne_c5/analyze_c5.py", "runs/gne_c5-*-real-*"], "logs/c5_analysis.txt"),
    ("C6", ["gne_c6/analyze_c6.py", "runs/gne_c6-*-real-*"], "logs/c6_analysis.txt"),
    ("C6_bounds", ["c6_bounds.py"], "logs/c6_bounds.txt"),
    ("C5P", ["gne_c5p/analyze_c5p.py", "runs/gne_c5p-*-real-*"], "logs/c5p_analysis.txt"),
]

# The audit lists flagged runs in the order the batches are given. The saved file was made with the
# batches in the order the lab machine's shell expanded runs/*-main-real-* (en_US sort order).
AUDIT_BATCHES = [
    "runs/gne_c1m-mistral-7b-main-real-20260928T224101229319Z",
    "runs/gne_c3-qwen2.5-14b-main-real-20260929T183311890068Z",
    "runs/gne_c3-qwen2.5-7b-main-real-20260929T153847117893Z",
    "runs/gne_c4-gpt-oss-20b-main-real-20260930T204301620129Z",
    "runs/gne_c4g-gpt-oss-20b-main-real-20261001T035143046468Z",
    "runs/gne_c5p-qwen2.5-7b-main-real-20261002T221859125377Z",
    "runs/gne_c5-qwen2.5-7b-main-real-20261001T080811522442Z",
    "runs/gne_c6-qwen2.5-7b-main-real-20261001T230918321702Z",
    "runs/gne_core_c1-llama3.1-8b-main-real-20260927T191323558301Z",
    "runs/gne_core_c1-qwen2.5-3b-main-real-20260927T165400229910Z",
    "runs/gne_core_c2-qwen2.5-7b-main-real-20260928T194309469194Z",
]
AUDIT_SAVED = "logs/authority_review.txt"


def expand(args):
    out = []
    for a in args:
        if "*" in a:
            hits = sorted(glob.glob(os.path.join(LAB, a)))
            if not hits:
                raise SystemExit("no folder matches " + a)
            out += [os.path.relpath(h, LAB).replace(os.sep, "/") for h in hits]
        else:
            out.append(a)
    return out


def run_analysis(args):
    """Run one analysis from lab/ and return its output (stdout and stderr together) as bytes."""
    cmd = [sys.executable, "-B"] + expand(args)
    proc = subprocess.run(cmd, cwd=LAB, env=clean_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout


def saved_bytes(where):
    if where.startswith("tar:"):
        with tarfile.open(os.path.join(LAB, TARBALL)) as t:
            return t.extractfile(TAR_TOP + where[4:]).read()
    return open(os.path.join(LAB, where), "rb").read()


def sha(b):
    return hashlib.sha256(b).hexdigest()[:12]


def main(argv):
    if "--show" in argv:
        name = argv[argv.index("--show") + 1]
        args = dict((n, a) for n, a, _ in ANALYSES)[name]
        sys.stdout.buffer.write(run_analysis(args)[1])
        return 0
    write = "--write" in argv  # used once, when the repository was assembled
    banner("4. Re-running the analyses on the saved runs")
    ok = True
    n_saved = n_saved_ok = 0
    print("%-22s %-7s %-44s %s" % ("analysis", "exit", "saved by the project in", "result"))
    for name, args, where in ANALYSES:
        rc, out = run_analysis(args)
        target = os.path.join(OUT, name + ".txt")
        if write:
            os.makedirs(OUT, exist_ok=True)
            open(target, "wb").write(saved_bytes(where) if where else out)
        kept = open(target, "rb").read() if os.path.isfile(target) else None
        notes = []
        good = rc == 0
        if where:
            n_saved += 1
            original = saved_bytes(where)
            same_saved = out == original
            n_saved_ok += same_saved
            good = good and same_saved and kept == original
            notes.append("identical to the saved output" if same_saved else "DIFFERS from the saved output")
            if kept != original:
                notes.append("copy in results/ DIFFERS from the saved output")
        else:
            good = good and kept == out
            notes.append("no saved output; " + ("identical to the copy in results/" if kept == out else "DIFFERS from the copy in results/"))
        ok = ok and good
        print("%-22s %-7d %-44s %s  [%s]" % (name, rc, where or "-", "; ".join(notes), sha(out)))

    # the file the audit script writes with --review
    with tempfile.TemporaryDirectory(prefix="gne-audit-") as tmp:
        review = os.path.join(tmp, "authority_review.txt")
        cmd = [sys.executable, "-B", "gne_c5p/audit_authority.py"] + AUDIT_BATCHES + ["--review", review]
        proc = subprocess.run(cmd, cwd=LAB, env=clean_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        rebuilt = open(review, "rb").read() if os.path.isfile(review) else b""
        table = proc.stdout
    same = rebuilt == saved_bytes(AUDIT_SAVED)
    target = os.path.join(OUT, "audit_table.txt")
    # the table's last line names the review file's path, which is a temporary one here; leave it out
    body = b"\n".join(table.rstrip(b"\n").split(b"\n")[:-1]) + b"\n"
    if write:
        open(target, "wb").write(body)
    kept_table = open(target, "rb").read() if os.path.isfile(target) else None
    same_table = kept_table == body
    print("%-22s %-7d %-44s %s  [%s]" % ("audit review file", proc.returncode, AUDIT_SAVED,
                                         "identical to the saved file" if same else "DIFFERS from the saved file", sha(rebuilt)))
    print("%-22s %-7s %-44s %s" % ("audit table", "", "-", "no saved output; " + ("identical to the copy in results/" if same_table else "DIFFERS from the copy in results/")))
    ok = ok and same and same_table and proc.returncode == 0
    ok = verdict(ok and n_saved == 10 and n_saved_ok == 10,
                 "%d of %d saved analysis outputs regenerate byte for byte; the audit review file %s" % (
                     n_saved_ok, n_saved, "does too" if same else "does NOT")) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
