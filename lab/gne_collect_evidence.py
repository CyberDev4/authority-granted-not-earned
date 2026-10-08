#!/usr/bin/env python3
"""Collect the run records needed to check every reported number, into one small archive.

Run from the project root (the folder that holds runs/ and the gne_* packages):

    python3 gne_collect_evidence.py                  # finished batches only
    python3 gne_collect_evidence.py --include-interim   # also batches that are still part-way through
    python3 gne_collect_evidence.py --include-interim --skip gne_c6-   # ... but leave out any batch whose
                                                                       # folder name contains "gne_c6-"

It only reads. The one file it writes is gne_evidence_<time>.tar.gz in the current folder.
Standard library only. No model calls, no network.

What goes in:
  - every real batch under runs/ and runs_excluded/: batch.json, manifest.jsonl and each run's
    episode.json. The bulky raw model output is dropped, except for runs with an unknown outcome,
    where it is needed to see why the run could not be scored.
  - each study folder's PREREGISTRATION.md, FREEZE.md, DEVIATIONS.md, RUNBOOK.md and README.md,
    plus the SHA-256 of every file in it, so the frozen hashes can be checked.
  - small text files under logs/ (analysis output, audit review and verdict files).
  - INDEX.txt: one line per batch with its counts.

What stays out:
  - request-*.json and response-*.json (large, and repeated inside episode.json).
  - fake-model batches.
  - main-stage batches that are not finished, unless --include-interim is given. A preregistered
    study should not be looked at by condition before it is complete.
"""
import argparse
import hashlib
import io
import json
import tarfile
import time
from collections import Counter
from pathlib import Path

MAX_LOG_BYTES = 2 * 1024 * 1024
DOC_NAMES = ("PREREGISTRATION.md", "FREEZE.md", "DEVIATIONS.md", "RUNBOOK.md", "README.md")
LOG_SUFFIXES = (".txt", ".out", ".log", ".md")
RAW_KEYS = ("raw_outputs", "raw_output")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def add_bytes(tar, name, data):
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mtime = int(time.time())
    tar.addfile(info, io.BytesIO(data))


def add_text(tar, name, text):
    add_bytes(tar, name, text.encode("utf-8"))


def slim(record):
    """Drop the raw model output unless the outcome is unknown (then it explains why)."""
    unknown = record.get("target_outcome") is None and record.get("kind") != "probe"
    if unknown or record.get("ending") in ("interface_failure", "aborted_not_rerun"):
        return record
    return {k: v for k, v in record.items() if k not in RAW_KEYS}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--include-interim", action="store_true",
                        help="also collect batches that are not finished (off by default)")
    parser.add_argument("--skip", action="append", default=[], metavar="TEXT",
                        help="leave out any batch whose folder name contains TEXT (can be given more than once)")
    args = parser.parse_args()
    root = Path.cwd()
    if not (root / "runs").is_dir():
        raise SystemExit("STOP: run this from the project root (no runs/ folder here).")

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = root / ("gne_evidence_%s.tar.gz" % stamp)
    index, skipped = [], []
    n_batches = n_eps = 0

    with tarfile.open(out, "w:gz") as tar:
        # 1. Batches
        batch_files = sorted(list((root / "runs").glob("*/batch.json")) + list((root / "runs_excluded").glob("**/batch.json")))
        for bf in batch_files:
            folder = bf.parent
            rel = folder.relative_to(root).as_posix()
            try:
                batch = json.loads(bf.read_text(encoding="utf-8"))
            except Exception as exc:
                skipped.append("%s: batch.json unreadable (%s)" % (rel, exc))
                continue
            if any(text in folder.name for text in args.skip):
                skipped.append("%s: left out by --skip" % rel)
                continue
            if str(batch.get("mode", "")).startswith("fake") or "-fake-" in folder.name:
                skipped.append("%s: fake-model batch" % rel)
                continue
            episodes = sorted(folder.glob("ep-*/episode.json"))
            started = len([p for p in folder.glob("ep-*") if p.is_dir()])
            planned = len(batch.get("schedule") or [])
            finished = bool(planned) and len(episodes) >= planned
            line = "%s | protocol %s | model %s | stage %s | planned %s | finished runs %d | started %d" % (
                rel, batch.get("protocol"), batch.get("model"), batch.get("stage"), planned or "?", len(episodes), started)
            if planned and not finished and not args.include_interim and "runs_excluded" not in rel:
                skipped.append("%s: not finished (%d of %d); left out so it is not looked at early" % (rel, len(episodes), planned))
                index.append(line + " | NOT COLLECTED (interim)")
                continue
            add_bytes(tar, rel + "/batch.json", bf.read_bytes())
            if (folder / "manifest.jsonl").exists():
                add_bytes(tar, rel + "/manifest.jsonl", (folder / "manifest.jsonl").read_bytes())
            endings, outcomes = Counter(), Counter()
            for ep in episodes:
                try:
                    record = json.loads(ep.read_text(encoding="utf-8"))
                except Exception as exc:
                    skipped.append("%s: unreadable (%s)" % (ep.relative_to(root).as_posix(), exc))
                    continue
                endings[str(record.get("ending"))] += 1
                if record.get("kind") == "probe" or "probe_valid" in record:
                    outcomes["probe valid" if record.get("probe_valid") else "probe invalid"] += 1
                else:
                    outcomes[{True: "target made", False: "target not made", None: "unknown"}[record.get("target_outcome")]] += 1
                add_text(tar, ep.relative_to(root).as_posix(), json.dumps(slim(record), ensure_ascii=False))
                n_eps += 1
            n_batches += 1
            index.append(line + " | endings %s | outcomes %s" % (dict(endings), dict(outcomes)))

        # 2. Study folders: plan, freeze record, deviations, and a hash of every file
        hash_lines = []
        for prereg in sorted(root.glob("*/PREREGISTRATION.md")):
            pkg = prereg.parent
            if pkg.name in ("runs", "runs_excluded", "logs"):
                continue
            for name in DOC_NAMES:
                if (pkg / name).is_file():
                    add_bytes(tar, "packages/%s/%s" % (pkg.name, name), (pkg / name).read_bytes())
            for f in sorted(p for p in pkg.iterdir() if p.is_file()):
                hash_lines.append("%s  %s/%s" % (sha256(f), pkg.name, f.name))
        add_text(tar, "packages/SHA256_NOW.txt", "\n".join(hash_lines) + "\n")

        # 3. Small text files in logs/
        logs = root / "logs"
        if logs.is_dir():
            for f in sorted(p for p in logs.rglob("*") if p.is_file()):
                rel = f.relative_to(root).as_posix()
                if f.suffix.lower() not in LOG_SUFFIXES:
                    skipped.append("%s: not a text log" % rel)
                elif f.stat().st_size > MAX_LOG_BYTES:
                    skipped.append("%s: larger than 2 MB" % rel)
                else:
                    add_bytes(tar, rel, f.read_bytes())

        # 4. Index
        text = ["Evidence bundle made %s (UTC) in %s" % (stamp, root),
                "%d batches, %d runs collected." % (n_batches, n_eps), "", "BATCHES"] + index
        text += ["", "LEFT OUT"] + (skipped or ["nothing"])
        add_text(tar, "INDEX.txt", "\n".join(text) + "\n")

    print("\n".join(index))
    print("\nLeft out:")
    print("\n".join("  " + s for s in skipped) or "  nothing")
    print("\nWrote %s" % out.name)
    print("  %d batches, %d runs, %.1f MB" % (n_batches, n_eps, out.stat().st_size / 1e6))
    print("  SHA-256 %s" % sha256(out))
    print("Nothing else was changed.")


if __name__ == "__main__":
    main()
