#!/usr/bin/env python3
"""Check the reference pages against the record.

  A. docs/how-a-run-works.md: every labelled quote and every table of quoted texts
     is compared with the code line or the saved request it cites (see _doc_quotes.py).
  B. docs/data-dictionary.md: every top-level field found in the run records,
     batch records and batch logs of the 58 batches is named on the page, and the
     counts of fields and of endings given in its section 5 hold.
  C. Every page outside lab/: each file or folder of this repository that a page
     names in code type (`lab/...`, `results/...`, `verify/...`, `docs/...`,
     `manifest/...`) exists.
  D. README.md and RESULTS.md: the main-result table on each page, the headline
     sentence of README.md and the table of labels in RESULTS.md hold the numbers
     that are in results/tables/ (which checks 6 and 7 rebuild from lab/).

What is NOT checked: the other numbers in the prose of the pages, and the wording
of any page other than docs/how-a-run-works.md.

Nothing is written. No model and no network are used.

Usage:  python3 verify/check_docs.py [--verbose]
"""
import csv
import glob
import json
import os
import re
import sys

sys.dont_write_bytecode = True  # set before the imports below, so no __pycache__ is left behind
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _doc_quotes
from _common import LAB, REPO, banner, verdict

V_PACKAGES = ("phase1_v6_frozen_2x2", "phase1_x1_scope_explicit", "phase1_v7_timeout")
EXPECTED_QUOTES = {"quotes": 57, "tables": 11, "rows": 73}
# What section 5 of the data dictionary states: (V family, C family, both families together).
EXPECTED_FIELDS = {"episode.json": (34, 39, 60), "batch.json": (19, 18, 23), "manifest.jsonl": (7, 7, 11), "ending": (3, 6, 8)}
EXPECTED_WITH_PILOTS = {"episode.json fields": 88, "ending values": 13}


def family(protocol):
    return "V" if protocol in V_PACKAGES else "C"


def field_inventory():
    """Top-level field names per file type and family, over the 58 batches; and over every episode.json under runs/."""
    fields = {name: {"V": set(), "C": set()} for name in ("episode.json", "batch.json", "manifest.jsonl", "ending")}
    batches = 0
    for top in ("runs", "runs_excluded"):
        for bj_path in sorted(glob.glob(os.path.join(LAB, top, "*", "batch.json"))):
            batches += 1
            bdir = os.path.dirname(bj_path)
            batch = json.load(open(bj_path, encoding="utf-8"))
            fam = family(batch["protocol"])
            fields["batch.json"][fam].update(batch)
            manifest = os.path.join(bdir, "manifest.jsonl")
            if os.path.isfile(manifest):
                for line in open(manifest, encoding="utf-8"):
                    if line.strip():
                        fields["manifest.jsonl"][fam].update(json.loads(line))
            for rec_path in glob.glob(os.path.join(bdir, "ep-*", "episode.json")):
                if os.path.getsize(rec_path) == 0:
                    continue
                rec = json.load(open(rec_path, encoding="utf-8"))
                fields["episode.json"][fam].update(rec)
                if "ending" in rec:
                    fields["ending"][fam].add(rec["ending"])
    all_fields, all_endings = set(), set()
    for top in ("runs", "runs_excluded"):
        for d, _dirs, files in os.walk(os.path.join(LAB, top)):
            if "episode.json" in files and os.path.getsize(os.path.join(d, "episode.json")):
                rec = json.load(open(os.path.join(d, "episode.json"), encoding="utf-8"))
                if isinstance(rec, dict):
                    all_fields.update(rec)
                    if isinstance(rec.get("ending"), str):
                        all_endings.add(rec["ending"])
    return batches, fields, all_fields, all_endings


def pages_outside_lab():
    out = []
    for d, dirs, files in os.walk(REPO):
        dirs[:] = sorted(x for x in dirs if not (d == REPO and x in ("lab", ".git")))
        for name in sorted(files):
            if name.endswith(".md"):
                out.append(os.path.join(d, name))
    return out


def section(text, heading):
    """The text of one '## ' section of a Markdown page, without its sub-sections' headings removed."""
    start = text.index("\n" + heading + "\n")
    end = text.find("\n## ", start + 1)
    return text[start:end if end != -1 else len(text)]


def table_rows(text):
    """Markdown table rows -> {first cell: [the other cells]}."""
    rows = {}
    for line in text.split("\n"):
        if line.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows[cells[0]] = cells[1:]
    return rows


def main_tables_against_csv():
    """-> list of problems: places where README.md or RESULTS.md differ from results/tables/."""
    tables = os.path.join(REPO, "results", "tables")
    with open(os.path.join(tables, "main_result_qwen2.5-7b.csv"), encoding="utf-8", newline="") as f:
        main = {r["study"]: r for r in csv.DictReader(f) if r["rules"] == "both rules"}
    with open(os.path.join(tables, "labels_summary.csv"), encoding="utf-8", newline="") as f:
        lab = {r["runs"]: r for r in csv.DictReader(f)}
    total = main["added up (description only)"]
    all0 = lab["standard runs, five studies added up, after agreeing (L0)"]
    all3 = lab["standard runs, five studies added up, after correcting (L3)"]
    problems = []

    def want(page, where, found, expected):
        if found != expected:
            problems.append("%s, %s: the page has %r, the tables give %r" % (page, where, found, expected))

    def of(k, n):
        return "%s of %s" % (k, n)

    def pct(k, n):
        return "%.0f%%" % (100.0 * int(k) / int(n))

    readme = open(os.path.join(REPO, "README.md"), encoding="utf-8").read()
    results = open(os.path.join(REPO, "RESULTS.md"), encoding="utf-8").read()

    # README.md: the table under "What was found"
    rows = table_rows(section(readme, "## What was found"))
    names = {"C2": "C2, pilot", "C3": "C3", "C5": "C5", "C6": "C6", "C5P": 'C5P, "production" prompt'}
    for study, name in names.items():
        m = main[study]
        d0 = lab["%s, standard runs, after agreeing (L0)" % study]
        d3 = lab["%s, standard runs, after correcting (L3)" % study]
        cells = rows.get(name, [""] * 5)
        want("README.md", "row " + name, [cells[0], cells[1], cells[3], cells[4]],
             [of(m["after_agreeing_calls"], m["after_agreeing_scored"]), of(m["after_correcting_calls"], m["after_correcting_scored"]),
              of(d0["call_made_or_written_as_done"], d0["scored"]), of(d3["call_made_or_written_as_done"], d3["scored"])])
    cells = rows.get("Added up (a description, not a test)", [""] * 5)
    want("README.md", "row Added up", [cells[0], cells[1], cells[3], cells[4]],
         [of(total["after_agreeing_calls"], total["after_agreeing_scored"]), of(total["after_correcting_calls"], total["after_correcting_scored"]),
          of(all0["call_made_or_written_as_done"], all0["scored"]), of(all3["call_made_or_written_as_done"], all3["scored"])])
    # README.md: the headline sentence and the smaller gap
    flat = re.sub(r"\s+", " ", readme)
    for phrase in ("%s runs (%s)" % (of(total["after_correcting_calls"], total["after_correcting_scored"]),
                                     pct(total["after_correcting_calls"], total["after_correcting_scored"])),
                   "%s (%s)" % (of(total["after_agreeing_calls"], total["after_agreeing_scored"]),
                                pct(total["after_agreeing_calls"], total["after_agreeing_scored"])),
                   "the gap is %s against %s" % (pct(all0["call_made_or_written_as_done"], all0["scored"]),
                                                 pct(all3["call_made_or_written_as_done"], all3["scored"]))):
        want("README.md", "the phrase %r" % phrase, phrase in flat, True)

    # RESULTS.md: the table under "The main result"
    rows = table_rows(section(results, "## The main result"))
    for study, name in (("C2", "C2, pilot"), ("C3", "C3"), ("C5", "C5"), ("C6", "C6"), ("C5P", "C5P")):
        m = main[study]
        cells = rows.get(name, [""] * 5)
        want("RESULTS.md", "row " + name, [cells[0], cells[1], cells[2], cells[3].split()[0] if cells[3] else ""],
             [m["system_prompt_says"], of(m["after_agreeing_calls"], m["after_agreeing_scored"]),
              of(m["after_correcting_calls"], m["after_correcting_scored"]), m["rise_points"]])
    cells = rows.get("Added up (a description, not a test)", [""] * 5)
    want("RESULTS.md", "row Added up", cells[1:4],
         ["%s (%s)" % (of(total["after_agreeing_calls"], total["after_agreeing_scored"]), pct(total["after_agreeing_calls"], total["after_agreeing_scored"])),
          "%s (%s)" % (of(total["after_correcting_calls"], total["after_correcting_scored"]), pct(total["after_correcting_calls"], total["after_correcting_scored"])),
          total["rise_points"]])
    # RESULTS.md: the table of labels
    rows = table_rows(section(results, "## What the agents wrote (exploratory)"))
    for name, column in (("Runs with a readable outcome", "scored"), ("Forbidden call made", "call_made"),
                         ("No call: says it did it", "no_call_says_it_did_it"), ("No call: writes of it as done", "no_call_writes_of_it_as_done"),
                         ("No call: recommends it", "no_call_recommends_it"), ("No call: none of these", "no_call_none_of_these"),
                         ("No call: holds back", "no_call_holds_back")):
        want("RESULTS.md", "row " + name, rows.get(name), [all0[column], all3[column]])
    return problems


def main(argv):
    verbose = "--verbose" in argv
    banner("9. The reference pages against the record")
    ok = True

    # A. quotes
    page = os.path.join(REPO, "docs", "how-a-run-works.md")
    failed, lines, counts = _doc_quotes.run(REPO, page, verbose=verbose)
    for line in lines:
        print("  " + line)
    ok = verdict(failed == 0 and all(counts[k] == v for k, v in EXPECTED_QUOTES.items()),
                 "docs/how-a-run-works.md: %d quotes and %d tables (%d rows) match the files they cite" % (
                     counts["quotes"], counts["tables"], counts["rows"])) and ok

    # B. data dictionary
    text = open(os.path.join(REPO, "docs", "data-dictionary.md"), encoding="utf-8").read()
    named = set(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)", text))            # the first word inside any code span
    batches, fields, all_fields, all_endings = field_inventory()
    missing = []
    counts_ok = True
    for name, expected in EXPECTED_FIELDS.items():
        v, c = fields[name]["V"], fields[name]["C"]
        found = (len(v), len(c), len(v | c))
        counts_ok = counts_ok and found == expected
        print("  %-15s V family %2d, C family %2d, both %2d%s" % (name, found[0], found[1], found[2],
                                                                "" if found == expected else "   EXPECTED %s" % (expected,)))
        missing += sorted("%s: %s" % (name, x) for x in (v | c) if x not in named)
    with_pilots = {"episode.json fields": len(all_fields), "ending values": len(all_endings)}
    print("  counting the early pilot folders too: %d fields in run records, %d values of ending" % (
        with_pilots["episode.json fields"], with_pilots["ending values"]))
    for m in missing:
        print("  NOT NAMED ON THE PAGE:", m)
    ok = verdict(batches == 58 and not missing and counts_ok and with_pilots == EXPECTED_WITH_PILOTS,
                 "docs/data-dictionary.md: every top-level field and every ending found in the %d batches is named on the page; the counts in its section 5 hold" % batches) and ok

    # C. paths named on the pages
    checked, problems = 0, []
    for path in pages_outside_lab():
        rel = os.path.relpath(path, REPO).replace(os.sep, "/")
        body = open(path, encoding="utf-8").read()
        for token in sorted(set(re.findall(r"`((?:lab|results|verify|docs|manifest)/[^`\s]*)`", body))):
            if any(ch in token for ch in "<>*{}$") or "..." in token:
                continue                                  # a pattern or a placeholder, not one path
            target = re.sub(r":\d+(-\d+)?$", "", token).rstrip("/")
            checked += 1
            if not os.path.exists(os.path.join(REPO, *target.split("/"))):
                problems.append("%s names %s" % (rel, token))
    for p in problems:
        print("  MISSING:", p)
    ok = verdict(not problems, "%d paths named on the pages outside lab/ exist (%d pages)" % (checked, len(pages_outside_lab()))) and ok

    # D. the main tables on the two front pages
    problems = main_tables_against_csv()
    for p in problems:
        print("  DIFFERS:", p)
    ok = verdict(not problems, "README.md and RESULTS.md: the main-result tables, the headline sentence and the table of labels "
                 "hold the numbers in results/tables/") and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
