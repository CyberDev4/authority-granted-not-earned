#!/usr/bin/env python3
"""timeline.py: when each batch of model runs happened, and which requests waited too long.

Usage:
    python3 verify/timeline.py                 rebuild the tables and compare them with results/timeline/
    python3 verify/timeline.py --write         rebuild them and rewrite results/timeline/
    python3 verify/timeline.py REPOSITORY_ROOT OUTPUT_FOLDER
                                               rebuild them from another copy into a folder of your choice

Reads only  REPOSITORY_ROOT/manifest/MANIFEST.tsv  and files under  REPOSITORY_ROOT/lab/ .
Writes only into the output folder (it may not lie inside lab/ or manifest/).
Standard library only. Python 3.10 or later.

Where the times come from. The script never asks the file system for a file time and never reads the
clock. It uses three kinds of time, all read from file contents or file names:

  1. The start stamp at the end of a batch folder name (UTC, written by the runner).
  2. The `created_at` field of each saved reply (UTC, written by Ollama when the reply was produced).
  3. The `archive_time` column of manifest/MANIFEST.tsv: the last-write time of each file as stored in
     the archive. It is the lab machine's local time (UTC+5:30) with 2-second resolution. The script
     subtracts 5 hours 30 minutes to get UTC. Checks of that offset are printed in the summary.

What is counted. A batch is a folder lab/runs/<name>/ that holds a batch.json. Only batches with
"mode": "real" whose "protocol" is one of the twelve studies are used. A run is a folder ep-NNN-...
inside a batch. A request is a file request-NN.json or request-belief.json in a run folder; its reply
is the file response-NN.json or response-belief.json beside it. Which files exist, and how big they
are, is taken from the manifest; a file that is read must have the size the manifest gives.

Two measures of waiting.
  Wait (file times): from the time of the request file to the time of its reply file if that file is
      not empty, otherwise to the time of the run record (episode.json) of the same run.
  Gap (reply time stamps): within a batch, the saved replies are walked in run order (run number, then
      request number, the belief request last) and each `created_at` is compared with the next.
A wait or a gap is "long" when it is more than 15 minutes.

Timeouts. A run record "ends in a timeout" when the last line of its `interface_error` is a timeout
error (in these files always "TimeoutError: timed out"). A request "timed out" when no reply to it was
saved and the error recorded for it is a timeout: for a numbered request, it is the run's last numbered
request and the run record ends in a timeout; for the belief request, `belief.error` ends in a timeout.

Output files (UTF-8, "\\n" line ends, fixed row order):
    batches_timeline.csv     one row per real batch, in order of start
    studies_timeline.csv     one row per study, in the order the studies ran
    long_waits.csv           one row per request that waited more than 15 minutes
    long_gaps.csv            one row per gap of more than 15 minutes between saved replies
    overlaps.csv             one row per pair of real batches whose spans [start, last file written] overlap
  and three extras:
    timed_out_requests.csv   one row per request that timed out, with the time it waited
    log_mentions.csv         for each long wait and long gap, the deviations-log lines that name the
                             run or the batch (a word search only; reading the lines is left to a person)
    summary.txt              what the script prints: details and checks, then the short summary
"""
import calendar
import csv
import json
import os
import re
import sys
import time
from decimal import Decimal, ROUND_HALF_UP

LAB_UTC_OFFSET_SECONDS = 5 * 3600 + 30 * 60   # archive_time is lab local time, UTC+5:30
LONG_SECONDS = 15 * 60                        # a wait or gap longer than this is "long"
NS = 1000000000
LONG = LONG_SECONDS * NS

# The twelve studies in the order they ran, with the "protocol" value found in batch.json.
# The package folder under lab/ has the same name as the protocol.
STUDIES = [("V6", "phase1_v6_frozen_2x2"), ("X1", "phase1_x1_scope_explicit"), ("V7", "phase1_v7_timeout"),
           ("C1", "gne_core_c1"), ("C2", "gne_core_c2"), ("C1M", "gne_c1m"), ("C3", "gne_c3"),
           ("C4", "gne_c4"), ("C4G", "gne_c4g"), ("C5", "gne_c5"), ("C6", "gne_c6"), ("C5P", "gne_c5p")]
STUDY_OF = {protocol: code for code, protocol in STUDIES}

MANIFEST_HEADER = "sha256\tbytes\texec\tarchive_time\tpath"
RUN_RE = re.compile(r"^ep-(\d+)-")
REQUEST_RE = re.compile(r"^request-([A-Za-z0-9_]+)\.json$")
STAMP_RE = re.compile(r"-(\d{4})(\d\d)(\d\d)T(\d\d)(\d\d)(\d\d)(\d{6})Z$")
CREATED_RE = re.compile(r"^(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(?:\.(\d{1,9}))?Z$")
ARCHIVE_TIME_RE = re.compile(r"^(\d{4})-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d)$")
TRACEBACK_FRAME_RE = re.compile(r'^\s*File "[^"]*", line \d+, in (\S+)')
RUNNER_TIMEOUT_RE = re.compile(r"opener\.open\(\s*req\s*,\s*timeout\s*=\s*(\d+)\s*\)")
FREEZE_FILE_RE = re.compile(r"^\s*-\s*Frozen\s*\(([^)]*)\)\s*:\s*(\d{4})-(\d\d)-(\d\d)[ T](\d\d):(\d\d)(?::(\d\d))?\s*$")
FREEZE_PLAN_RE = re.compile(r"^\s*-\s*Date/time frozen:\s*(\d{4})-(\d\d)-(\d\d)[ T](\d\d):(\d\d)(?::(\d\d))?\s*([A-Za-z]+)?\s*$")
FREEZE_HEADING_RE = re.compile(r"^#+\s*\d+\.\s*Freeze record")
DEVIATIONS_HEADING_RE = re.compile(r"^#+\s*\d+\.\s*Deviations log\s*$")
HEADING_RE = re.compile(r"^#+\s")


class Stop(Exception):
    """A problem that makes the output unreliable; the script stops without writing anything."""


# ---------------------------------------------------------------- time helpers (pure arithmetic)

def utc_seconds(y, mo, d, h, mi, s):
    return calendar.timegm((int(y), int(mo), int(d), int(h), int(mi), int(s), 0, 0, 0))


def archive_time_to_utc_ns(text):
    """'2026-09-27 08:49:12' in lab local time -> nanoseconds since 1970 in UTC."""
    m = ARCHIVE_TIME_RE.match(text)
    if not m:
        raise Stop("unexpected archive_time in the manifest: %r" % text)
    return (utc_seconds(*m.groups()) - LAB_UTC_OFFSET_SECONDS) * NS


def created_at_to_ns(text):
    """'2026-10-02T22:20:02.213534333Z' -> nanoseconds since 1970 in UTC, or None if not in that form."""
    m = CREATED_RE.match(text) if isinstance(text, str) else None
    if not m:
        return None
    return utc_seconds(*m.groups()[:6]) * NS + int((m.group(7) or "").ljust(9, "0"))


def stamp_to_ns(folder_name):
    """'...-real-20261001T230918321702Z' -> nanoseconds since 1970 in UTC, or None."""
    m = STAMP_RE.search(folder_name)
    if not m:
        return None
    return utc_seconds(*m.groups()[:6]) * NS + int(m.group(7)) * 1000


def iso(ns):
    """UTC time cut (not rounded) to the whole second."""
    return "" if ns is None else time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ns // NS))


def rounded(value, places):
    text = str(value.quantize(Decimal(places), rounding=ROUND_HALF_UP))
    return text[1:] if text.startswith("-") and not text.strip("-0.") else text   # "-0.0" -> "0.0"


def minutes(ns):
    """Minutes with one decimal, halves rounded away from zero."""
    return "" if ns is None else rounded(Decimal(ns) / Decimal(60 * NS), "0.1")


def seconds(ns, places="0.001"):
    return "" if ns is None else rounded(Decimal(ns) / Decimal(NS), places)


# ---------------------------------------------------------------- reading

def read_text(root, rel_path, expected_bytes=None):
    """Read a UTF-8 file under the repository root. Only manifest/MANIFEST.tsv and lab/ may be read,
    and the byte count in the manifest must match what is on disk."""
    parts = rel_path.split("/")
    if not (rel_path == "manifest/MANIFEST.tsv" or parts[0] == "lab") or ".." in parts or "" in parts:
        raise Stop("refusing to read outside lab/: %r" % rel_path)
    with open(os.path.join(root, *parts), "rb") as f:
        data = f.read()
    if expected_bytes is not None and len(data) != expected_bytes:
        raise Stop("%s is %d bytes on disk but %d in the manifest" % (rel_path, len(data), expected_bytes))
    return data.decode("utf-8")


def lines_of(root, files, path):
    return read_text(root, path, files[path][0]).replace("\r\n", "\n").split("\n")


def read_manifest(root):
    """path -> (bytes, last-write time in UTC nanoseconds). Only lab/ paths are kept."""
    files = {}
    lines = read_text(root, "manifest/MANIFEST.tsv").replace("\r\n", "\n").split("\n")
    if lines[0] != MANIFEST_HEADER:
        raise Stop("manifest/MANIFEST.tsv does not start with the expected header line")
    for line in lines[1:]:
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 5:
            raise Stop("manifest line with %d fields instead of 5: %r" % (len(parts), line[:120]))
        _sha, size, _exec, when, path = parts
        if path.startswith("lab/"):
            files[path] = (int(size), archive_time_to_utc_ns(when))
    return files


def last_line(error_text):
    """Last non-empty line of an error text, or '' if there is none."""
    if not isinstance(error_text, str):
        return ""
    lines = [x.strip() for x in error_text.splitlines() if x.strip()]
    return lines[-1] if lines else ""


def is_timeout(error_line):
    """True for a last line such as 'TimeoutError: timed out': the error's name contains 'timeout',
    or its message says 'timed out'."""
    name, _, message = error_line.partition(":")
    return "timeout" in name.lower() or "timed out" in message.lower()


def raised_in(error_text):
    """The three innermost function names of a Python traceback, outermost first."""
    if not isinstance(error_text, str):
        return ""
    names = [m.group(1) for m in (TRACEBACK_FRAME_RE.match(x) for x in error_text.splitlines()) if m]
    return " > ".join(names[-3:])


def tag_key(tag):
    """Request order inside a run: numbered requests by number, then any named request (belief)."""
    return (0, int(tag), "") if tag.isdigit() else (1, 0, tag)


def load_batches(root, files, folder):
    """Every folder under lab/<folder>/ that holds a batch.json, with its parsed batch.json."""
    found = []
    pattern = re.compile(r"^lab/%s/([^/]+)/batch\.json$" % re.escape(folder))
    for path in sorted(files):
        m = pattern.match(path)
        if m:
            found.append((m.group(1), json.loads(read_text(root, path, files[path][0]))))
    return found


def build_batch(root, files, name, info):
    """Collect everything the tables need about one real batch."""
    prefix = "lab/runs/%s/" % name
    start = stamp_to_ns(name)
    if start is None:
        raise Stop("batch folder name without a start stamp: %s" % name)
    if not name.startswith(info["protocol"] + "-") or "-real-" not in name:
        raise Stop("batch folder name does not match its batch.json: %s" % name)
    batch = {"name": name, "study": STUDY_OF[info["protocol"]], "protocol": info["protocol"],
             "model": info.get("model", ""), "stage": info.get("stage", ""), "start": start,
             "scheduled": len(info.get("schedule", [])), "runs": [], "requests": [], "replies": []}

    # Request timeout: batch.json, or (V6) the literal in the copy of the runner saved with the batch.
    if "request_timeout_seconds" in info:
        batch["timeout"], batch["timeout_source"] = info["request_timeout_seconds"], "batch.json"
    else:
        batch["timeout"], batch["timeout_source"] = "", "not recorded"
        src = prefix + "source-run.py"
        if src in files:
            hits = [(n, int(m.group(1))) for n, line in enumerate(lines_of(root, files, src), 1)
                    for m in [RUNNER_TIMEOUT_RE.search(line)] if m]
            if len(hits) == 1:
                batch["timeout"] = hits[0][1]
                batch["timeout_source"] = "source-run.py line %d (not in batch.json)" % hits[0][0]

    in_batch = {p[len(prefix):]: v for p, v in files.items() if p.startswith(prefix)}
    batch["batch_json_time"] = in_batch["batch.json"][1]
    batch["last_file_time"] = max(t for _, t in in_batch.values())
    batch["last_files"] = sorted(p for p, (_, t) in in_batch.items() if t == batch["last_file_time"])

    by_run = {}
    for rel, value in in_batch.items():
        parts = rel.split("/")
        if len(parts) == 2 and RUN_RE.match(parts[0]):
            by_run.setdefault(parts[0], {})[parts[1]] = value
    indexes = [int(RUN_RE.match(r).group(1)) for r in by_run]
    if len(set(indexes)) != len(indexes):
        raise Stop("two run folders with the same number in %s" % name)

    position = 0
    for run_name in sorted(by_run, key=lambda r: int(RUN_RE.match(r).group(1))):
        entries = by_run[run_name]
        run = {"name": run_name, "index": int(RUN_RE.match(run_name).group(1)), "batch": batch,
               "record_time": None, "ending": "", "outcome_field": "", "outcome": "", "error_text": None,
               "error_line": "", "ends_in_timeout": False, "belief_error_text": None,
               "belief_error_line": "", "belief_timed_out": False, "requests": []}
        if "episode.json" in entries:
            size, when = entries["episode.json"]
            record = json.loads(read_text(root, prefix + run_name + "/episode.json", size))
            run["record_time"] = when
            run["ending"] = record["ending"] if "ending" in record else "(absent)"
            for field in ("target_outcome", "crossing_outcome"):
                if field in record:
                    run["outcome_field"], run["outcome"] = field, json.dumps(record[field])
                    break
            else:
                run["outcome_field"], run["outcome"] = "(absent)", "(absent)"
            run["error_text"] = record.get("interface_error")
            run["error_line"] = last_line(run["error_text"])
            run["ends_in_timeout"] = is_timeout(run["error_line"])
            belief = record.get("belief")
            if isinstance(belief, dict):
                run["belief_error_text"] = belief.get("error")
                run["belief_error_line"] = last_line(run["belief_error_text"])
                run["belief_timed_out"] = is_timeout(run["belief_error_line"])
        tags = sorted((m.group(1) for m in (REQUEST_RE.match(f) for f in entries) if m), key=tag_key)
        numbered = [t for t in tags if t.isdigit()]
        for tag in tags:
            req_size, req_time = entries["request-%s.json" % tag]
            request = {"run": run, "batch": batch, "tag": tag, "file": "request-%s.json" % tag,
                       "bytes": req_size, "time": req_time, "position": position,
                       "reply_file": "response-%s.json" % tag, "reply_state": "none", "reply_time": None,
                       "reply": None, "ended_by": "", "end_file": "", "end_time": None, "wait": None,
                       "timed_out": False, "last_numbered": bool(numbered) and tag == numbered[-1]}
            position += 1
            if request["reply_file"] in entries:
                rep_size, rep_time = entries[request["reply_file"]]
                request["reply_time"] = rep_time
                request["reply_state"] = "saved" if rep_size > 0 else "empty"
                if rep_size > 0:
                    rel = prefix + run_name + "/" + request["reply_file"]
                    body = json.loads(read_text(root, rel, rep_size))
                    created = created_at_to_ns(body.get("created_at"))
                    if created is None:
                        raise Stop("no usable created_at in %s" % rel)
                    request["reply"] = {"request": request, "run": run, "file": request["reply_file"],
                                        "created_text": body["created_at"], "created": created,
                                        "file_time": rep_time, "total_duration": body.get("total_duration")}
                    batch["replies"].append(request["reply"])
            if request["reply_state"] == "saved":
                request["ended_by"], request["end_file"] = "reply", request["reply_file"]
                request["end_time"] = request["reply_time"]
            elif run["record_time"] is not None:
                request["ended_by"], request["end_file"] = "run record", "episode.json"
                request["end_time"] = run["record_time"]
                # The request itself timed out: no reply was saved and the error recorded for it is a timeout.
                request["timed_out"] = (run["ends_in_timeout"] and request["last_numbered"] if tag.isdigit()
                                        else run["belief_timed_out"])
            if request["end_time"] is not None:
                request["wait"] = request["end_time"] - request["time"]
            run["requests"].append(request)
            batch["requests"].append(request)
        batch["runs"].append(run)
    return batch


# ---------------------------------------------------------------- freeze records and deviation logs

def study_package_facts(root, files, protocol):
    """Freeze time as stated in the package, and where the package keeps its deviations log."""
    facts = {"freeze_utc": "", "freeze_ns": None, "freeze_precision": "", "freeze_clock": "", "freeze_text": "",
             "freeze_source": "", "freeze_from_freeze_file": False, "freeze_file_time": None,
             "deviations_file": "none", "deviations_file_time": None, "plan_heading_line": "",
             "plan_entry_lines": "", "log_lines": []}
    base = "lab/%s/" % protocol

    def stated(y, mo, d, h, mi, s, clock):
        clock = (clock or "").strip()
        if clock.upper() == "UTC":
            ns, label = utc_seconds(y, mo, d, h, mi, s or 0) * NS, "UTC (the text says UTC)"
        elif clock.upper() in ("IST", "LOCAL"):
            ns = (utc_seconds(y, mo, d, h, mi, s or 0) - LAB_UTC_OFFSET_SECONDS) * NS
            label = "local (the text says %s); converted to UTC" % clock
        else:
            ns, label = None, "not stated"
        facts["freeze_ns"], facts["freeze_clock"] = ns, label
        facts["freeze_precision"] = "second" if s is not None else "minute"
        if ns is not None:
            facts["freeze_utc"] = iso(ns) if s is not None else iso(ns)[:16] + "Z"

    freeze_path, plan_path, log_path = base + "FREEZE.md", base + "PREREGISTRATION.md", base + "DEVIATIONS.md"
    if freeze_path in files:
        for n, line in enumerate(lines_of(root, files, freeze_path), 1):
            m = FREEZE_FILE_RE.match(line)
            if m:
                clock, y, mo, d, h, mi, s = m.groups()
                stated(y, mo, d, h, mi, s, clock)
                facts["freeze_text"], facts["freeze_source"] = line.strip(), "%s line %d" % (freeze_path, n)
                facts["freeze_from_freeze_file"], facts["freeze_file_time"] = True, files[freeze_path][1]
                break
    plan_lines = lines_of(root, files, plan_path) if plan_path in files else []
    if not facts["freeze_source"]:
        inside = False
        for n, line in enumerate(plan_lines, 1):
            if HEADING_RE.match(line):
                inside = bool(FREEZE_HEADING_RE.match(line))
                continue
            m = FREEZE_PLAN_RE.match(line) if inside else None
            if m:
                y, mo, d, h, mi, s, clock = m.groups()
                stated(y, mo, d, h, mi, s, clock)
                facts["freeze_text"], facts["freeze_source"] = line.strip(), "%s line %d" % (plan_path, n)
                facts["freeze_file_time"] = files[plan_path][1]
                break
    # Where deviations are logged: the package's DEVIATIONS.md, and a "Deviations log" section in the plan.
    if log_path in files:
        facts["deviations_file"], facts["deviations_file_time"] = log_path, files[log_path][1]
        for n, line in enumerate(lines_of(root, files, log_path), 1):
            if line.strip():
                facts["log_lines"].append((log_path, n, line.strip()))
    inside, entries = False, 0
    for n, line in enumerate(plan_lines, 1):
        if HEADING_RE.match(line):
            inside = bool(DEVIATIONS_HEADING_RE.match(line))
            if inside:
                facts["plan_heading_line"] = n
            continue
        if inside and line.strip():
            facts["log_lines"].append((plan_path, n, line.strip()))
            if not line.strip().startswith("(Append only"):
                entries += 1
    if facts["plan_heading_line"] != "":
        facts["plan_entry_lines"] = entries
    return facts


def log_mentions(package, batch, runs):
    """Deviations-log lines that name the batch or one of the runs. The full folder names are looked for
    in every study's log; the short forms (ep-NNN, and the THHMMSS part of the batch stamp) only in the
    log of the batch's own study, because other studies reuse the same run numbers."""
    stamp = "T" + STAMP_RE.search(batch["name"]).group(0)[10:16]
    hits = []
    for code, _protocol in STUDIES:
        for path, n, text in package[code]["log_lines"]:
            found = [key for key in [batch["name"]] + [r["name"] for r in runs] if key in text]
            if code == batch["study"]:
                for r in runs:
                    if r["name"] not in text and re.search(r"(?<![A-Za-z0-9])ep-0*%d(?![0-9])" % r["index"], text):
                        found.append("ep-%03d" % r["index"])
                if batch["name"] not in text and stamp in text:
                    found.append(stamp)
            if found:
                hits.append((path, n, "; ".join(found), text))
    return hits


# ---------------------------------------------------------------- the two measures

def gap_context(batch):
    """For every request: the saved reply before it and the first saved reply at or after it, in run order."""
    replies = batch["replies"]            # already in run order, like batch["requests"]
    earlier = 0                           # how many saved replies belong to requests before this one
    for request in batch["requests"]:
        while earlier < len(replies) and replies[earlier]["request"]["position"] < request["position"]:
            earlier += 1
        request["gap_from"] = replies[earlier - 1] if earlier > 0 else None
        request["gap_to"] = replies[earlier] if earlier < len(replies) else None
        request["gap"] = (request["gap_to"]["created"] - request["gap_from"]["created"]
                          if request["gap_from"] and request["gap_to"] else None)


def union_length(intervals):
    """Total length covered by a list of (start, end) intervals."""
    total, current_start, current_end = 0, None, None
    for start, end in sorted(intervals):
        if current_end is None or start > current_end:
            if current_end is not None:
                total += current_end - current_start
            current_start, current_end = start, end
        else:
            current_end = max(current_end, end)
    if current_end is not None:
        total += current_end - current_start
    return total


def long_gaps_of(batch):
    rows = []
    replies = batch["replies"]
    run_by_index = {run["index"]: run for run in batch["runs"]}
    for first, second in zip(replies, replies[1:]):
        gap = second["created"] - first["created"]
        if gap <= LONG:
            continue
        inside = [q for q in batch["requests"]
                  if first["request"]["position"] < q["position"] <= second["request"]["position"]]
        measured = [q for q in inside if q["wait"] is not None]
        between = [run_by_index.get(i) for i in range(first["run"]["index"] + 1, second["run"]["index"])]
        rows.append({"batch": batch, "first": first, "second": second, "gap": gap,
                     "where": "inside one run" if first["run"] is second["run"] else "between runs",
                     "between": ["ep-%03d (no folder)" % (first["run"]["index"] + 1 + k) if r is None else r["name"]
                                 for k, r in enumerate(between)],
                     "runs": [first["run"]] + [r for r in between if r is not None]
                             + ([] if first["run"] is second["run"] else [second["run"]]),
                     "inside": inside,
                     "longest": max(measured, key=lambda q: (q["wait"], -q["position"])) if measured else None,
                     "long_inside": [q for q in measured if q["wait"] > LONG],
                     "outside": gap - union_length([(q["time"], q["end_time"]) for q in measured])})
    return rows


# ---------------------------------------------------------------- writing

def write_csv(out_dir, name, header, rows):
    with open(os.path.join(out_dir, name), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        for row in rows:
            writer.writerow(["" if v is None else v for v in row])


def yes_no(flag):
    return "yes" if flag else "no"


def request_label(request):
    return "%s/%s" % (request["run"]["name"], request["file"])


def reply_label(reply):
    return "%s/%s" % (reply["run"]["name"], reply["file"])


def full_label(request):
    return "%s %s/%s" % (request["batch"]["study"], request["batch"]["name"], request_label(request))


def wait_note(request):
    """Plain facts that change how a wait should be read."""
    notes = []
    if request["bytes"] == 0:
        notes.append("the request file is empty (0 bytes)")
    if request["reply_state"] == "empty":
        notes.append("the reply file %s exists but is empty (0 bytes), written %s"
                     % (request["reply_file"], iso(request["reply_time"])))
    if request["ended_by"] == "run record" and request["run"]["ending"] == "aborted_not_rerun":
        notes.append("the run record is the one the runner writes when a stopped batch is resumed, "
                     "so this wait runs to the resume")
    if request["ended_by"] == "reply" and isinstance(request["reply"]["total_duration"], int):
        notes.append("the reply's own total_duration counter reads %s s"
                     % seconds(request["reply"]["total_duration"], "0.1"))
    return "; ".join(notes)


def build(root, out_dir, quiet=False):
    """Write the tables into out_dir. Returns 0, or 1/2 after printing why it stopped."""
    out_dir = os.path.abspath(out_dir)
    for forbidden in ("lab", "manifest"):
        inside = os.path.abspath(os.path.join(root, forbidden))
        if out_dir == inside or out_dir.startswith(inside + os.sep):
            print("STOP: the output folder may not lie inside %s/" % forbidden)
            return 2
    try:
        files = read_manifest(root)
        candidates = load_batches(root, files, "runs")
        batches, not_real, other_protocol = [], 0, 0
        for name, info in candidates:
            if info.get("mode") != "real":
                not_real += 1
            elif info.get("protocol") not in STUDY_OF:
                other_protocol += 1
            else:
                batches.append(build_batch(root, files, name, info))
        set_aside = {}
        for name, info in load_batches(root, files, "runs_excluded"):
            if info.get("mode") == "real" and info.get("protocol") in STUDY_OF:
                set_aside.setdefault(STUDY_OF[info["protocol"]], []).append(stamp_to_ns(name))
        package = {code: study_package_facts(root, files, protocol) for code, protocol in STUDIES}
        # Copies of DEVIATIONS.md saved in batch folders: is each one the beginning of the final log?
        copies, copies_are_prefixes = 0, 0
        for path in sorted(files):
            m = re.match(r"^lab/runs(?:_excluded)?/([^/]+)/source-DEVIATIONS\.md$", path)
            owner = [p for _c, p in STUDIES if m and m.group(1).startswith(p + "-")]
            if m and owner and "lab/%s/DEVIATIONS.md" % owner[0] in files:
                final = "lab/%s/DEVIATIONS.md" % owner[0]
                copies += 1
                copies_are_prefixes += read_text(root, final, files[final][0]).startswith(
                    read_text(root, path, files[path][0]))
    except (Stop, OSError, ValueError, KeyError) as problem:
        print("STOP: %s: %s" % (type(problem).__name__, problem))
        return 1

    batches.sort(key=lambda b: (b["start"], b["name"]))
    for batch in batches:
        gap_context(batch)
    all_requests = [q for b in batches for q in b["requests"]]
    all_replies = [r for b in batches for r in b["replies"]]
    gaps = [g for b in batches for g in long_gaps_of(b)]
    measured = [q for q in all_requests if q["wait"] is not None]
    long_waits = [q for q in measured if q["wait"] > LONG]
    timed_out = [q for q in measured if q["timed_out"]]
    listed_gaps = {(g["batch"]["name"], g["first"]["request"]["position"]) for g in gaps}

    def gap_is_listed(request):
        return (request["gap"] is not None
                and (request["batch"]["name"], request["gap_from"]["request"]["position"]) in listed_gaps)

    os.makedirs(out_dir, exist_ok=True)

    # 1. batches_timeline.csv
    rows = []
    for b in batches:
        created = [r["created"] for r in b["replies"]]
        beliefs = [q for q in b["requests"] if not q["tag"].isdigit()]
        steps = [second["created"] - first["created"] for first, second in zip(b["replies"], b["replies"][1:])]
        ordinary = [g for g in steps if g <= LONG]
        rows.append([b["study"], b["model"], b["stage"], b["name"], iso(b["start"]),
                     iso(min(created)) if created else "", iso(max(created)) if created else "",
                     iso(b["last_file_time"]), "; ".join(b["last_files"]), b["scheduled"], len(b["runs"]),
                     sum(1 for r in b["runs"] if r["record_time"] is not None),
                     sum(1 for r in b["runs"] if r["ends_in_timeout"]),
                     sum(1 for q in beliefs if q["timed_out"]) if beliefs else "",
                     b["timeout"], b["timeout_source"], len(b["requests"]), len(b["replies"]),
                     sum(1 for q in b["requests"] if q["wait"] is not None and q["wait"] > LONG),
                     sum(1 for g in steps if g > LONG), minutes(max(ordinary)) if ordinary else ""])
    write_csv(out_dir, "batches_timeline.csv",
              ["study", "model", "stage", "batch_folder", "start_utc", "first_reply_utc", "last_reply_utc",
               "last_file_written_utc", "last_files_written", "runs_scheduled", "run_folders", "run_records",
               "runs_ending_in_timeout", "belief_requests_timed_out", "request_timeout_seconds",
               "request_timeout_source", "requests", "replies_saved", "long_waits", "long_gaps",
               "longest_gap_at_or_under_15_minutes"], rows)

    # 2. studies_timeline.csv
    rows = []
    for code, protocol in STUDIES:
        mine = [b for b in batches if b["study"] == code]
        facts = package[code]
        first_start = min(b["start"] for b in mine) if mine else None
        created = [r["created"] for b in mine for r in b["replies"]]
        aside = sorted(t for t in set_aside.get(code, []) if t is not None)
        rows.append([code, "lab/" + protocol, iso(first_start), iso(max(created)) if created else "", len(mine),
                     sum(b["scheduled"] for b in mine),
                     sum(1 for b in mine for r in b["runs"] if r["record_time"] is not None),
                     facts["freeze_utc"], facts["freeze_precision"], facts["freeze_clock"], facts["freeze_text"],
                     facts["freeze_source"], iso(facts["freeze_file_time"]),
                     minutes(first_start - facts["freeze_ns"]) if mine and facts["freeze_ns"] is not None else "",
                     len(set_aside.get(code, [])), iso(aside[0]) if aside else "",
                     facts["deviations_file"], iso(facts["deviations_file_time"]),
                     facts["plan_heading_line"], facts["plan_entry_lines"]])
    write_csv(out_dir, "studies_timeline.csv",
              ["study", "package", "first_batch_start_utc", "last_reply_utc", "real_batches",
               "runs_scheduled_all_batches", "run_records", "freeze_utc", "freeze_precision", "freeze_clock", "freeze_text", "freeze_source",
               "freeze_source_file_written_utc", "minutes_from_freeze_to_first_start", "batches_set_aside",
               "earliest_set_aside_start_utc", "deviations_file", "deviations_file_written_utc",
               "plan_deviations_heading_line", "plan_deviations_entry_lines"], rows)

    # 3. long_waits.csv
    rows = []
    for q in long_waits:
        run, b = q["run"], q["batch"]
        rows.append([b["study"], b["name"], run["name"], q["file"], iso(q["time"]), q["ended_by"], q["end_file"],
                     iso(q["end_time"]), q["wait"] // NS, minutes(q["wait"]), b["timeout"], run["ending"],
                     run["outcome_field"], run["outcome"], run["error_line"], yes_no(run["ends_in_timeout"]),
                     run["belief_error_line"] if not q["tag"].isdigit() else "", yes_no(q["timed_out"]),
                     reply_label(q["gap_from"]) if q["gap_from"] else "", reply_label(q["gap_to"]) if q["gap_to"] else "",
                     minutes(q["gap"]), yes_no(gap_is_listed(q)) if q["gap"] is not None else "",
                     minutes(q["gap"] - q["wait"]) if q["gap"] is not None else "",
                     seconds(q["time"] - q["gap_from"]["created"], "1") if q["gap_from"] else "",
                     seconds(q["gap_to"]["created"] - q["end_time"], "1") if q["gap_to"] else "",
                     wait_note(q)])
    write_csv(out_dir, "long_waits.csv",
              ["study", "batch_folder", "run_folder", "request_file", "request_time_utc", "wait_ended_by",
               "end_file", "end_time_utc", "wait_seconds", "wait_minutes", "request_timeout_seconds", "ending",
               "outcome_field", "outcome", "interface_error_last_line", "run_record_ends_in_timeout",
               "belief_error_last_line", "this_request_timed_out", "gap_from_reply", "gap_to_reply",
               "gap_minutes", "gap_in_long_gaps", "gap_minus_wait_minutes", "seconds_from_earlier_reply_to_request",
               "seconds_from_end_of_wait_to_later_reply", "note"], rows)

    # 4. long_gaps.csv
    rows = []
    for g in gaps:
        b = g["batch"]
        waits = "; ".join("%s %s (%s)" % (request_label(q), minutes(q["wait"]) if q["wait"] is not None else "not measurable",
                                         q["ended_by"] or "no reply and no run record") for q in g["inside"])
        n_long = len(g["long_inside"])
        if n_long:
            reading = "holds %d long wait%s listed in long_waits.csv" % (n_long, "" if n_long == 1 else "s")
        else:
            reading = "no single wait over 15 minutes; %d shorter waits in a row" % len(g["inside"])
        rows.append([b["study"], b["name"], g["first"]["run"]["name"], g["first"]["file"], g["first"]["created_text"],
                     g["second"]["run"]["name"], g["second"]["file"], g["second"]["created_text"],
                     seconds(g["gap"]), minutes(g["gap"]), g["where"], "; ".join(g["between"]), len(g["inside"]),
                     waits, minutes(g["longest"]["wait"]) if g["longest"] else "",
                     request_label(g["longest"]) if g["longest"] else "", n_long, seconds(g["outside"], "1"), reading])
    write_csv(out_dir, "long_gaps.csv",
              ["study", "batch_folder", "from_run", "from_reply_file", "from_created_at", "to_run", "to_reply_file",
               "to_created_at", "gap_seconds", "gap_minutes", "position", "runs_between_without_any_reply",
               "requests_in_gap", "waits_in_gap_minutes", "longest_wait_in_gap_minutes", "longest_wait_request",
               "long_waits_in_gap", "seconds_of_gap_outside_any_wait", "reading"], rows)

    # 5. overlaps.csv
    overlap_rows, near = [], 0
    for i, a in enumerate(batches):
        for b in batches[i + 1:]:
            lo, hi = max(a["start"], b["start"]), min(a["last_file_time"], b["last_file_time"])
            if hi > lo:
                overlap_rows.append(
                    [a["study"], a["model"], a["stage"], a["name"], iso(a["start"]), iso(a["last_file_time"]),
                     b["study"], b["model"], b["stage"], b["name"], iso(b["start"]), iso(b["last_file_time"]),
                     iso(lo), iso(hi), minutes(hi - lo),
                     sum(1 for r in a["replies"] if lo <= r["created"] <= hi),
                     sum(1 for r in b["replies"] if lo <= r["created"] <= hi)])
            elif lo - hi < 2 * NS:
                near += 1
    write_csv(out_dir, "overlaps.csv",
              ["a_study", "a_model", "a_stage", "a_batch_folder", "a_start_utc", "a_last_file_written_utc",
               "b_study", "b_model", "b_stage", "b_batch_folder", "b_start_utc", "b_last_file_written_utc",
               "overlap_start_utc", "overlap_end_utc", "overlap_minutes", "a_replies_in_overlap",
               "b_replies_in_overlap"], overlap_rows)

    # Extra: timed_out_requests.csv, how long each timed-out request waited
    rows = []
    for q in timed_out:
        b, run = q["batch"], q["run"]
        limit = b["timeout"] if isinstance(b["timeout"], int) else None
        rows.append([b["study"], b["name"], run["name"], q["file"], iso(q["time"]), iso(q["end_time"]),
                     q["wait"] // NS, minutes(q["wait"]), b["timeout"],
                     q["wait"] // NS - limit if limit is not None else "", yes_no(q["wait"] > LONG),
                     raised_in(run["error_text"] if q["tag"].isdigit() else run["belief_error_text"])])
    write_csv(out_dir, "timed_out_requests.csv",
              ["study", "batch_folder", "run_folder", "request_file", "request_time_utc", "run_record_time_utc",
               "wait_seconds", "wait_minutes", "request_timeout_seconds", "seconds_over_timeout",
               "in_long_waits", "error_raised_in"], rows)

    # Extra: log_mentions.csv, a word search of the deviations logs for each long wait and long gap
    rows = []
    events = [("long wait", q["batch"], [q["run"]], request_label(q)) for q in long_waits]
    events += [("long gap", g["batch"], g["runs"], "%s -> %s" % (reply_label(g["first"]), reply_label(g["second"])))
               for g in gaps]
    for kind, b, runs, detail in events:
        facts = package[b["study"]]
        places = [facts["deviations_file"] if facts["deviations_file"] != "none" else "no DEVIATIONS.md"]
        if facts["plan_heading_line"] != "":
            places.append("lab/%s/PREREGISTRATION.md section at line %d" % (b["protocol"], facts["plan_heading_line"]))
        hits = log_mentions(package, b, runs)
        for path, n, found, text in hits or [("", "", "", "")]:
            rows.append([kind, b["study"], b["name"], detail, "; ".join(places), len(hits), path, n, found, text])
    write_csv(out_dir, "log_mentions.csv",
              ["event", "study", "batch_folder", "event_detail", "where_this_study_logs_deviations",
               "lines_found", "log_file", "line", "names_found", "line_text"], rows)

    # ------------------------------------------------------------ what is printed: details first, the short summary last
    out = []
    say = out.append
    numbered = sum(1 for q in all_requests if q["tag"].isdigit())
    unmeasured = [q for q in all_requests if q["wait"] is None]
    hit = [q for q in long_waits if q["timed_out"]]
    miss = [q for q in long_waits if not q["timed_out"]]
    say("timeline.py: details and checks")
    say("")
    say("what was read")
    say("  lab/ files listed in the manifest: %d" % len(files))
    say("  folders under lab/runs/ with a batch.json: %d (real and one of the twelve studies: %d; not real: %d; "
        "real but another protocol: %d)" % (len(candidates), len(batches), not_real, other_protocol))
    say("  run folders: %d; run records (episode.json): %d; saved (non-empty) replies: %d"
        % (sum(len(b["runs"]) for b in batches),
           sum(1 for b in batches for r in b["runs"] if r["record_time"] is not None), len(all_replies)))
    say("  empty (0-byte) request files: %d; empty reply files: %d"
        % (sum(1 for q in all_requests if q["bytes"] == 0), sum(1 for q in all_requests if q["reply_state"] == "empty")))
    say("")
    say("waits (file times)")
    say("  measured: %d (ended by a reply: %d; ended by the run record: %d)"
        % (len(measured), sum(1 for q in measured if q["ended_by"] == "reply"),
           sum(1 for q in measured if q["ended_by"] == "run record")))
    say("  not measurable, no saved reply and no run record: %d" % len(unmeasured))
    for q in unmeasured:
        say("    %s (%d bytes, written %s)" % (full_label(q), q["bytes"], iso(q["time"])))
    below = [q["wait"] for q in measured if q["wait"] <= LONG]
    say("  longest wait at or under 15 minutes: %d s; shortest long wait: %d s (file times have 2 s resolution)"
        % (max(below) // NS if below else 0, min(q["wait"] for q in long_waits) // NS if long_waits else 0))
    late = [q for q in measured if q["ended_by"] == "reply" and isinstance(q["batch"]["timeout"], int)
            and q["wait"] > q["batch"]["timeout"] * NS]
    say("  requests answered after more than the timeout setting: %d" % len(late))
    for q in late:
        say("    %s: %d s (timeout %d s; the reply's total_duration counter reads %s s)"
            % (full_label(q), q["wait"] // NS, q["batch"]["timeout"], seconds(q["reply"]["total_duration"], "0.1")))
    counted = [(q["wait"] - q["reply"]["total_duration"], q) for q in measured
               if q["ended_by"] == "reply" and isinstance(q["reply"]["total_duration"], int)]
    apart = [(d, q) for d, q in counted if abs(d) > 4 * NS]
    say("  replies whose wait and own total_duration counter differ by more than 4 s: %d of %d" % (len(apart), len(counted)))
    for d, q in apart:
        say("    %s: wait %d s, counter %s s" % (full_label(q), q["wait"] // NS, seconds(q["reply"]["total_duration"], "0.1")))
    say("")
    say("timed-out requests: %d (interface_error: %d; belief.error: %d)"
        % (len(timed_out), sum(1 for q in timed_out if q["tag"].isdigit()), sum(1 for q in timed_out if not q["tag"].isdigit())))
    over = [q["wait"] // NS - q["batch"]["timeout"] for q in timed_out if isinstance(q["batch"]["timeout"], int)]
    say("  wait minus the timeout setting: at most 4 s: %d; 5 s to 5 minutes: %d; more than 5 minutes: %d"
        % (sum(1 for x in over if x <= 4), sum(1 for x in over if 4 < x <= 300), sum(1 for x in over if x > 300)))
    say("  runs whose record ends in a timeout: %d; of these, the last numbered request has no saved reply: %d"
        % (sum(1 for b in batches for r in b["runs"] if r["ends_in_timeout"]), sum(1 for q in timed_out if q["tag"].isdigit())))
    places = sorted(set(raised_in(q["run"]["error_text"] if q["tag"].isdigit() else q["run"]["belief_error_text"]) for q in timed_out))
    say("  where the timeout was raised (innermost three functions): %s" % " | ".join(places))
    say("")
    say("gaps (reply time stamps)")
    all_gaps = [second["created"] - first["created"] for b in batches for first, second in zip(b["replies"], b["replies"][1:])]
    short = [g for g in all_gaps if g <= LONG]
    say("  reply pairs compared: %d; pairs out of time order: %d" % (len(all_gaps), sum(1 for g in all_gaps if g < 0)))
    say("  gaps of more than 15 minutes: %d (inside one run: %d; between runs: %d)"
        % (len(gaps), sum(1 for g in gaps if g["where"] == "inside one run"), sum(1 for g in gaps if g["where"] == "between runs")))
    say("  longest gap at or under 15 minutes: %s s; shortest long gap: %s s"
        % (seconds(max(short), "0.1") if short else "", seconds(min(g["gap"] for g in gaps), "0.1") if gaps else ""))
    say("  holding at least one long wait: %d; holding none: %d"
        % (sum(1 for g in gaps if g["long_inside"]), sum(1 for g in gaps if not g["long_inside"])))
    say("")
    say("check of the two measures against each other")
    with_gap = [q for q in long_waits if q["gap"] is not None]
    say("  long waits that lie inside a listed gap: %d of %d" % (sum(1 for q in with_gap if gap_is_listed(q)), len(long_waits)))
    say("  long waits with no saved reply before or after them in the batch: %d" % (len(long_waits) - len(with_gap)))
    say("  long waits whose gap differs from the wait by more than 1 minute: %d"
        % sum(1 for q in with_gap if abs(q["gap"] - q["wait"]) > 60 * NS))
    idle_between, idle_within = [], []
    for b in batches:
        for earlier, later in zip(b["runs"], b["runs"][1:]):
            if earlier["record_time"] is not None and later["requests"]:
                idle_between.append((later["requests"][0]["time"] - earlier["record_time"], earlier, later))
        for run in b["runs"]:
            for q1, q2 in zip(run["requests"], run["requests"][1:]):
                if q1["reply_time"] is not None:
                    idle_within.append(q2["time"] - q1["reply_time"])
    say("  time from a reply file to the next request file of the same run: at most %d s over %d pairs"
        % (max(idle_within) // NS if idle_within else 0, len(idle_within)))
    slow = [x for x in idle_between if x[0] > 4 * NS]
    say("  time from a run record to the first request of the next run: more than 4 s in %d of %d pairs"
        % (len(slow), len(idle_between)))
    for d, earlier, later in slow:
        say("    %s %s: %d s after %s, before %s" % (earlier["batch"]["study"], earlier["batch"]["name"], d // NS,
                                                   earlier["name"], later["name"]))
    say("")
    say("overlapping pairs of batches: %d" % len(overlap_rows))
    say("  pairs that do not overlap but lie less than 2 s apart (the file-time resolution): %d" % near)
    say("")
    say("checks of the UTC+5:30 offset (manifest time minus 5:30, compared with a UTC time from another source)")
    d1 = [b["batch_json_time"] - b["start"] for b in batches]
    say("  batch.json file time minus the start stamp in the folder name: %s s to %s s over %d batches"
        % (seconds(min(d1), "0.1"), seconds(max(d1), "0.1"), len(d1)))
    d2 = [(r["file_time"] - r["created"], r) for r in all_replies]
    say("  reply file time minus the reply's created_at: %s s to %s s over %d replies"
        % (seconds(min(d for d, _ in d2), "0.1"), seconds(max(d for d, _ in d2), "0.1"), len(d2)))
    odd = [(d, r) for d, r in d2 if d < -2 * NS or d >= 2 * NS]
    say("  replies where the two differ by 2 s or more: %d" % len(odd))
    for d, r in odd:
        say("    %s: file time %s, created_at %s (file %s s later)"
            % (full_label(r["request"]).replace(r["request"]["file"], r["file"]), iso(r["file_time"]),
               r["created_text"], seconds(d, "0.1")))
    d3 = [package[c]["freeze_file_time"] - package[c]["freeze_ns"] for c, _ in STUDIES
          if package[c]["freeze_from_freeze_file"] and package[c]["freeze_ns"] is not None]
    if d3:
        say("  FREEZE.md file time minus the freeze time stated in it: %s s to %s s over %d studies"
            % (seconds(min(d3), "0.1"), seconds(max(d3), "0.1"), len(d3)))
    say("")
    say("deviations logs")
    for code, protocol in STUDIES:
        facts = package[code]
        section = ("; plan section 'Deviations log' at line %d with %d lines of entries"
                   % (facts["plan_heading_line"], facts["plan_entry_lines"])) if facts["plan_heading_line"] != "" else ""
        say("  %-3s %s%s" % (code, facts["deviations_file"] if facts["deviations_file"] != "none"
                             else "no DEVIATIONS.md in lab/%s" % protocol, section))
    say("  copies of DEVIATIONS.md saved in batch folders: %d; copies that are the beginning of the final log: %d"
        % (copies, copies_are_prefixes))
    say("")
    say("timeline.py: summary")
    say("requests examined: %d (numbered: %d; belief: %d)" % (len(all_requests), numbered, len(all_requests) - numbered))
    say("long waits (more than 15 minutes): %d" % len(long_waits))
    say("  ended in a timeout (no reply saved; the error recorded for that request is a timeout): %d" % len(hit))
    say("    the timeout is the run's interface_error: %d" % sum(1 for q in hit if q["tag"].isdigit()))
    say("    the timeout is in belief.error (closing question; the run's outcome was already fixed): %d"
        % sum(1 for q in hit if not q["tag"].isdigit()))
    say("  did not end in a timeout: %d" % len(miss))
    say("    ended by a reply: %d" % sum(1 for q in miss if q["ended_by"] == "reply"))
    say("    run record written when the batch was resumed (ending aborted_not_rerun): %d"
        % sum(1 for q in miss if q["ended_by"] == "run record" and q["run"]["ending"] == "aborted_not_rerun"))
    say("    other: %d" % sum(1 for q in miss if q["ended_by"] == "run record" and q["run"]["ending"] != "aborted_not_rerun"))
    say("  counting by the run record's interface_error alone: ends in a timeout in %d rows, not in %d"
        % (sum(1 for q in long_waits if q["run"]["ends_in_timeout"]), sum(1 for q in long_waits if not q["run"]["ends_in_timeout"])))
    text = "\n".join(out) + "\n"
    with open(os.path.join(out_dir, "summary.txt"), "w", encoding="utf-8", newline="") as f:
        f.write(text)
    if not quiet:
        sys.stdout.write(text)
    return 0


OUTPUT_FILES = ["batches_timeline.csv", "studies_timeline.csv", "long_waits.csv", "long_gaps.csv", "overlaps.csv",
                "timed_out_requests.csv", "log_mentions.csv", "summary.txt"]

# What a pass has to reproduce: the counts found when the record was checked on 6 October 2026
# (see docs/deviations-added-later.md).
EXPECTED = {"requests examined": 6708, "long waits": 24, "long waits that are not in any deviations log": 17,
            "overlapping pairs of batches": 11}

# The long waits that a deviations log does record: (batch folder starts with, run folder starts with).
# Reading the logs is a reader's job; the word search in log_mentions.csv only helps. See
# docs/deviations-added-later.md, entry 1, for the list.
LOGGED = [("gne_core_c1-llama3.1-8b-main-", "ep-064-"), ("gne_core_c1-mistral-7b-controls-", "ep-009-"),
          ("gne_c1m-mistral-7b-main-", "ep-040-"), ("gne_c3-qwen2.5-14b-main-", "ep-001-"),
          ("gne_c6-qwen2.5-7b-main-", "ep-008-"), ("gne_c6-qwen2.5-7b-main-", "ep-055-")]


def main(argv):
    import tempfile
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    args = [a for a in argv[1:] if a != "--write"]
    if len(args) == 2:
        return build(args[0], args[1])
    if args:
        print(__doc__)
        return 2
    kept = os.path.join(repo, "results", "timeline")
    print()
    print("=" * 78)
    print("8. Timeline of the batches and requests that waited too long")
    print("=" * 78)
    with tempfile.TemporaryDirectory(prefix="gne-timeline-") as tmp:
        code = build(repo, tmp, quiet=True)
        if code:
            return code
        if "--write" in argv:
            os.makedirs(kept, exist_ok=True)
            for name in OUTPUT_FILES:
                with open(os.path.join(tmp, name), "rb") as f, open(os.path.join(kept, name), "wb") as g:
                    g.write(f.read())
        ok = True
        for name in OUTPUT_FILES:
            new = open(os.path.join(tmp, name), "rb").read()
            path = os.path.join(kept, name)
            same = os.path.isfile(path) and open(path, "rb").read() == new
            ok = ok and same
            print("%-26s %5d lines   %s" % (name, new.count(b"\n"), "identical to results/timeline/" if same else "DIFFERS from results/timeline/"))
        with open(os.path.join(tmp, "long_waits.csv"), encoding="utf-8", newline="") as f:
            waits = list(csv.DictReader(f))
        with open(os.path.join(tmp, "overlaps.csv"), encoding="utf-8", newline="") as f:
            overlaps = list(csv.DictReader(f))
        summary = open(os.path.join(tmp, "summary.txt"), encoding="utf-8").read()
    examined = int(re.search(r"^requests examined: (\d+)", summary, re.M).group(1))
    unlogged = [w for w in waits if not any(w["batch_folder"].startswith(b) and w["run_folder"].startswith(r) for b, r in LOGGED)]
    found = {"requests examined": examined, "long waits": len(waits),
             "long waits that are not in any deviations log": len(unlogged), "overlapping pairs of batches": len(overlaps)}
    print()
    for what, expected in EXPECTED.items():
        print("%s %-52s %s" % ("ok  " if found[what] == expected else "BAD ", what, found[what] if found[what] == expected
                                else "%s (expected %s)" % (found[what], expected)))
    print()
    print("Waits of more than 15 minutes that no deviations log records (study, run, request, minutes):")
    for w in unlogged:
        print("  %-4s %-44s %-20s %7s  %s" % (w["study"], w["run_folder"], w["request_file"], w["wait_minutes"],
                                              "timed out" if w["this_request_timed_out"] == "yes" else "answered late"))
    ok = ok and found == EXPECTED
    print(("PASS  " if ok else "FAIL  ") + "%d requests examined; %d waited more than 15 minutes, %d of them in no deviations log; %d pairs of batches overlapped"
          % (examined, len(waits), len(unlogged), len(overlaps)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
