#!/usr/bin/env python3
"""Replay ONE batch through its own saved copy of the runner. Called by replay.py.

usage: _replay_batch.py LAB_DIR runs|runs_excluded BATCH_NAME SCRATCH_DIR

What it does
  1. Copies the batch's saved code (the source-* files) into a scratch folder.
  2. Starts that code's own main() in "resume" mode on an empty scratch batch
     folder that holds only the batch.json (seed, schedule, settings).
  3. Replaces the one function the runner uses to reach Ollama. Each time the
     runner sends a request, it is handed the reply that was saved for that
     request in the record. Where no reply was saved because the original call
     failed (a timeout or a refused connection), the same kind of error is
     raised again.
  4. Compares everything the runner then writes (requests, replies, transcripts,
     run records, the progress manifest) with what the record holds.

No network is used and nothing outside SCRATCH_DIR is written.

A run record that holds a Python error trace cannot match byte for byte: the
trace contains file paths of the machine it ran on, and its layout depends on
the Python version. For those the script compares the kind of error, its
message, and each line of the runner's code the error passed through (file
name, line number, function, source text).
"""
import importlib.util
import io
import json
import os
import re
import shutil
import sys

sys.dont_write_bytecode = True

lab, top, batch_name, scratch = sys.argv[1:5]
saved_dir = os.path.join(lab, top, batch_name)
work = os.path.join(scratch, batch_name)
if os.path.exists(work):
    shutil.rmtree(work)
batch = json.load(open(os.path.join(saved_dir, "batch.json"), encoding="utf-8"))
code_dir = os.path.join(work, "pkg", batch["protocol"])   # the folder name matters: traces are matched on it
out_dir = os.path.join(work, "out")
os.makedirs(code_dir)
os.makedirs(out_dir)
for name in os.listdir(saved_dir):
    if name.startswith("source-"):
        shutil.copyfile(os.path.join(saved_dir, name), os.path.join(code_dir, name[len("source-"):]))
shutil.copyfile(os.path.join(saved_dir, "batch.json"), os.path.join(out_dir, "batch.json"))

saved_runs = sorted(d for d in os.listdir(saved_dir) if os.path.isdir(os.path.join(saved_dir, d)))
saved_record = {}
for run in saved_runs:
    p = os.path.join(saved_dir, run, "episode.json")
    if os.path.isfile(p) and os.path.getsize(p) > 0:
        saved_record[run] = json.load(open(p, encoding="utf-8"))
# A run that was cut off when its batch stopped is recorded as "aborted_not_rerun" when the batch resumes.
# The runner writes that record when it finds the run's folder without a record, so give it the folder.
aborted = [run for run, rec in saved_record.items() if rec.get("ending") == "aborted_not_rerun"]
for run in aborted:
    os.makedirs(os.path.join(out_dir, run))


class Halt(BaseException):
    """Stop the replay (not an Exception, so the runner's own error handling does not swallow it)."""


state = {"run": None, "seen": set(), "stood_in": [], "server_checks": 0, "model_calls": 0}


def hooked_print(*args, **kwargs):
    """The runner prints '[3/120] ep-002-...' when it starts a run; that tells us which run is current."""
    m = re.match(r"\[\d+/\d+\] (ep-\S+)", " ".join(str(a) for a in args))
    if m:
        state["run"] = m.group(1)
        state["seen"] = set()


def recorded_error(record, tag):
    trace = (record.get("belief") or {}).get("error") if tag == "belief" else record.get("interface_error")
    return trace.strip().split("\n")[-1] if trace else None


class SavedReplies:
    """Stands in for the HTTP opener the runner would use to reach Ollama."""

    def open(self, request, timeout=None):
        if isinstance(request, str):          # the runner asking the server which models are installed
            state["server_checks"] += 1
            return io.BytesIO(b'{"models": []}')
        state["model_calls"] += 1
        run = state["run"]
        if run not in saved_record:
            raise Halt("run %s has no saved record" % run)
        folder = os.path.join(out_dir, run)
        new = sorted(f for f in os.listdir(folder) if f.startswith("request-") and f not in state["seen"])
        if len(new) != 1:
            raise Halt("cannot tell which request was just written in %s: %r" % (run, new))
        state["seen"].add(new[0])
        tag = new[0][len("request-"):-len(".json")]
        reply = os.path.join(saved_dir, run, "response-%s.json" % tag)
        if os.path.isfile(reply) and os.path.getsize(reply) > 0:
            return io.BytesIO(open(reply, "rb").read())
        # No reply was saved: the original call failed. Raise the same kind of error.
        last = recorded_error(saved_record[run], tag)
        state["stood_in"].append([run, tag, last])
        if last is None:
            raise Halt("no saved reply and no recorded error for %s %s" % (run, tag))
        if last.startswith("TimeoutError: timed out"):
            raise TimeoutError("timed out")
        if last.startswith("urllib.error.URLError: <urlopen error [Errno 111] Connection refused>"):
            import urllib.error
            raise urllib.error.URLError(ConnectionRefusedError(111, "Connection refused"))
        if last.startswith("http.client.RemoteDisconnected: Remote end closed connection without response"):
            import http.client
            raise http.client.RemoteDisconnected("Remote end closed connection without response")
        raise Halt("unhandled recorded error for %s %s: %s" % (run, tag, last))


sys.path.insert(0, code_dir)
spec = importlib.util.spec_from_file_location("run", os.path.join(code_dir, "run.py"))
runner = importlib.util.module_from_spec(spec)
sys.modules["run"] = runner
spec.loader.exec_module(runner)
runner.build_opener = lambda *a, **k: SavedReplies()
runner.print = hooked_print
mode = batch["mode"]
sys.argv = ["run.py", "--resume", out_dir, "--model", batch["model"]] + (
    ["--real"] if mode == "real" else ["--fake", mode.split(":", 1)[1]])
halted = None
try:
    runner.main()
except Halt as h:
    halted = str(h)
except SystemExit as s:
    halted = "SystemExit: %s" % (s,)

# ------------------------------------------------------------------ compare
FRAME = re.compile(r'^  File "([^"]+)", line (\d+), in (\S+)$')


def trace_summary(trace):
    """-> the lines of the runner's own code the error passed through, and the error's last line."""
    lines = trace.rstrip("\n").split("\n")
    frames = []
    for i, line in enumerate(lines):
        m = FRAME.match(line)
        if not m:
            continue
        path, number, function = m.group(1), int(m.group(2)), m.group(3)
        if os.path.basename(os.path.dirname(path)) == batch["protocol"]:   # a file of the study package
            source = lines[i + 1].strip() if i + 1 < len(lines) else ""
            frames.append([os.path.basename(path), number, function, source])
    return {"frames": frames, "last": lines[-1]}


def is_trace(value):
    return isinstance(value, str) and value.lstrip().startswith("Traceback (most recent call last)")


def without_traces(obj, found, path=""):
    if isinstance(obj, dict):
        return {k: without_traces(v, found, path + "/" + k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [without_traces(v, found, path + "[%d]" % i) for i, v in enumerate(obj)]
    if is_trace(obj) and not path.startswith("/transcript") and not path.startswith("/raw_output"):
        found[path] = obj
        return "<error trace>"
    return obj


res = {"batch": batch_name, "top": top, "mode": mode, "halted": halted, "records_saved": len(saved_record),
       "aborted": len(aborted), "aborted_equal": 0, "records_equal": 0, "records_differ": [],
       "requests": 0, "requests_equal": 0, "other_files": 0, "other_files_equal": 0, "files_differ": [],
       "files_missing_in_replay": [], "files_extra_in_replay": [], "records_with_trace": 0, "traces": 0,
       "traces_equal": 0, "traces_differ": [], "stood_in": state["stood_in"], "manifest_lines": 0,
       "manifest_equal": None}
for run in saved_runs:
    if run not in saved_record:
        continue                               # cut off in the middle of a request: no record, nothing to rebuild
    a_dir, r_dir = os.path.join(saved_dir, run), os.path.join(out_dir, run)
    if run in aborted:
        same = (os.path.isfile(os.path.join(r_dir, "episode.json")) and
                open(os.path.join(a_dir, "episode.json"), "rb").read() == open(os.path.join(r_dir, "episode.json"), "rb").read())
        res["aborted_equal"] += same
        continue
    for name in sorted(os.listdir(a_dir)):
        a_path, r_path = os.path.join(a_dir, name), os.path.join(r_dir, name)
        if not os.path.isfile(r_path):
            res["files_missing_in_replay"].append([run, name])
            continue
        a_bytes, r_bytes = open(a_path, "rb").read(), open(r_path, "rb").read()
        if name.startswith("request-"):
            res["requests"] += 1
            res["requests_equal"] += (a_bytes == r_bytes)
            if a_bytes != r_bytes:
                res["files_differ"].append([run, name])
        elif name == "episode.json":
            a_tr, r_tr = {}, {}
            a_rec = without_traces(json.loads(a_bytes), a_tr)
            r_rec = without_traces(json.loads(r_bytes), r_tr)
            if a_rec == r_rec:
                res["records_equal"] += 1
            else:
                res["records_differ"].append([run, sorted(k for k in set(a_rec) | set(r_rec) if a_rec.get(k) != r_rec.get(k))])
            if a_tr or r_tr:
                res["records_with_trace"] += 1
            for path in sorted(set(a_tr) | set(r_tr)):
                res["traces"] += 1
                if path in a_tr and path in r_tr and trace_summary(a_tr[path]) == trace_summary(r_tr[path]):
                    res["traces_equal"] += 1
                else:
                    res["traces_differ"].append([run, path])
        else:
            res["other_files"] += 1
            res["other_files_equal"] += (a_bytes == r_bytes)
            if a_bytes != r_bytes:
                res["files_differ"].append([run, name])
    if os.path.isdir(r_dir):
        for name in sorted(os.listdir(r_dir)):
            if not os.path.exists(os.path.join(a_dir, name)):
                res["files_extra_in_replay"].append([run, name])
a_manifest, r_manifest = os.path.join(saved_dir, "manifest.jsonl"), os.path.join(out_dir, "manifest.jsonl")
if os.path.isfile(a_manifest):
    a_lines = open(a_manifest, encoding="utf-8").read().splitlines()
    r_lines = open(r_manifest, encoding="utf-8").read().splitlines() if os.path.isfile(r_manifest) else []
    res["manifest_lines"] = len(a_lines)
    res["manifest_equal"] = (a_lines == r_lines[:len(a_lines)])
json.dump(res, open(os.path.join(work, "result.json"), "w", encoding="utf-8"), indent=1)
