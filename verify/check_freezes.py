#!/usr/bin/env python3
"""Check the freeze records and the code copies stored with each batch.

Three questions:
  A. Does every hash written in a freeze record match the file in lab/ today?
     Ten packages keep the record in FREEZE.md; V6 and V7 keep it in section 9 of
     their PREREGISTRATION.md.
  B. Does every code hash that a batch stored in its batch.json match the package
     file, the freeze record, and the copy of that file saved inside the batch?
  C. Are the other files a batch copied (plan, runbook, deviations log) the same
     as the package's files today? Two kinds of difference are expected and are
     listed, not failed: a deviations log that grew after the batch ran, and the
     two plan copies named in EXPECTED_PLAN_DIFFERENCES.

Usage:  python3 verify/check_freezes.py
"""
import glob
import json
import os
import re
import sys

sys.dont_write_bytecode = True  # set before the imports below, so no __pycache__ is left behind
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import LAB, STUDIES, banner, sha256_file, verdict

EXPECTED_PLAN_DIFFERENCES = {
    # V6's plan gained its closing note (in the deviations section, twice) after the batch had run.
    "runs/phase1_v6_frozen_2x2-baseline-real-20260927T011859229841Z/source-PREREGISTRATION.md":
        "V6's plan gained a closing note after this batch ran",
    # This one-run test against a fake model was made in the minute of the freeze, before the record was filled in.
    "runs/phase1_v7_timeout-baseline-fake-20260927T031819735471Z/source-PREREGISTRATION.md":
        "V7's fake-model test run was made before the freeze record was filled in",
}


def freeze_record(pkg):
    """-> (where the record is, {file name: sha256})"""
    path = os.path.join(LAB, pkg, "FREEZE.md")
    if os.path.isfile(path):
        text = open(path, encoding="utf-8").read()
        found = re.findall(r"^\s+(?:= )?([0-9a-f]{64})\s+(\S+)\s*$", text, re.M)
        return "FREEZE.md", {name: digest for digest, name in found}
    text = open(os.path.join(LAB, pkg, "PREREGISTRATION.md"), encoding="utf-8").read()
    found = re.findall(r"^\s+- (\S+\.py): ([0-9a-f]{64})\s*$", text, re.M)
    return "PREREGISTRATION.md, section 9", dict(found)


def main():
    ok = True
    banner("2A. Freeze records: do the recorded hashes match the files?")
    total = bad = 0
    print("%-5s %-30s %-30s %s" % ("study", "package", "record", "hashes"))
    for study, pkg in STUDIES:
        where, hashes = freeze_record(pkg)
        wrong = [n for n, d in hashes.items()
                 if not os.path.isfile(os.path.join(LAB, pkg, n)) or sha256_file(os.path.join(LAB, pkg, n)) != d]
        total += len(hashes)
        bad += len(wrong)
        print("%-5s %-30s %-30s %d of %d match%s" % (study, pkg, where, len(hashes) - len(wrong), len(hashes),
                                                    ("  MISMATCH: " + ", ".join(wrong)) if wrong else ""))
    ok = verdict(bad == 0 and total == 79, "%d of %d recorded freeze hashes match (expected 79)" % (total - bad, total)) and ok

    banner("2B. Code hashes stored by each batch")
    batches = sorted(glob.glob(os.path.join(LAB, "runs", "*", "batch.json")) +
                     glob.glob(os.path.join(LAB, "runs_excluded", "*", "batch.json")))
    stored = problems = 0
    copies = identical = 0
    grown_logs, plan_diffs, unexpected = [], [], []
    for bj_path in batches:
        bdir = os.path.dirname(bj_path)
        rel_b = os.path.relpath(bdir, LAB).replace(os.sep, "/")
        batch = json.load(open(bj_path, encoding="utf-8"))
        pkg = batch["protocol"]
        _, frozen = freeze_record(pkg)
        for name, digest in batch["source_sha256"].items():
            stored += 1
            current = os.path.join(LAB, pkg, name)
            copy = os.path.join(bdir, "source-" + name)
            if (not os.path.isfile(current) or sha256_file(current) != digest
                    or (name in frozen and frozen[name] != digest)
                    or not os.path.isfile(copy) or sha256_file(copy) != digest):
                problems += 1
                print("  PROBLEM %s: %s" % (rel_b, name))
        for copy in sorted(glob.glob(os.path.join(bdir, "source-*"))):
            name = os.path.basename(copy)[len("source-"):]
            current = os.path.join(LAB, pkg, name)
            copies += 1
            if os.path.isfile(current) and sha256_file(current) == sha256_file(copy):
                identical += 1
                continue
            rel = rel_b + "/source-" + name
            if name == "DEVIATIONS.md":
                grown_logs.append(rel)
            elif rel in EXPECTED_PLAN_DIFFERENCES:
                plan_diffs.append(rel)
            else:
                unexpected.append(rel)
    print("%d batches (real, set aside and fake-model)" % len(batches))
    ok = verdict(problems == 0, "%d of %d stored code hashes match the package, the freeze record and the saved copy" % (stored - problems, stored)) and ok

    banner("2C. Other files copied into each batch")
    print("%d copies in all; %d identical to the package's file today" % (copies, identical))
    print("%d are deviations logs that grew after the batch ran (expected)" % len(grown_logs))
    for rel in plan_diffs:
        print("1 plan copy differs as expected: %s\n    (%s)" % (rel, EXPECTED_PLAN_DIFFERENCES[rel]))
    for rel in unexpected:
        print("  UNEXPECTED difference:", rel)
    ok = verdict(not unexpected and len(plan_diffs) == len(EXPECTED_PLAN_DIFFERENCES),
                 "%d copies identical, %d differ in the expected ways, %d unexpected" % (identical, len(grown_logs) + len(plan_diffs), len(unexpected))) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
