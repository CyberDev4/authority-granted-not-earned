#!/usr/bin/env python3
"""Check that lab/ is exactly the record listed in manifest/MANIFEST.tsv.

Every file in lab/ must be listed, every listed file must be present, and every
SHA-256 must match. manifest/SHA256SUMS, the same list in the format that the
sha256sum tool reads, must say the same as the manifest. With --zip ARCHIVE the
script also checks each listed hash against the entry of the same path inside the
original archive.

Cache files that Python or pytest write when a reader runs code inside lab/ are
not part of the record. They are left out of the comparison and counted in a
note: compiled files (*.pyc) inside a __pycache__ folder, and the files of a
.pytest_cache folder. Any other unlisted file fails the check.

Usage:  python3 verify/check_manifest.py [--zip agentscope_full_20261006T035010.zip]
"""
import hashlib
import os
import sys
import zipfile

sys.dont_write_bytecode = True  # set before the imports below, so no __pycache__ is left behind
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import LAB, REPO, banner, sha256_file, verdict

PYTEST_CACHE_FILES = {".gitignore", "CACHEDIR.TAG", "README.md"}


def is_cache_file(rel):
    """True for a file that Python or pytest writes on its own when code inside lab/ is run."""
    parts = rel.split("/")
    if "__pycache__" in parts[:-1] and parts[-1].endswith(".pyc"):
        return True
    if ".pytest_cache" in parts[:-1]:
        inside = parts[parts.index(".pytest_cache") + 1:]
        return inside[0] == "v" or (len(inside) == 1 and inside[0] in PYTEST_CACHE_FILES)
    return False


def read_manifest():
    rows = {}
    with open(os.path.join(REPO, "manifest", "MANIFEST.tsv"), encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        assert header == ["sha256", "bytes", "exec", "archive_time", "path"], header
        for line in f:
            digest, size, x, when, path = line.rstrip("\n").split("\t")
            rows[path] = (digest, int(size))
    return rows


def main(argv):
    banner("1. Is lab/ the record listed in the manifest?")
    rows = read_manifest()
    on_disk = set()
    cache_files = 0
    for d, dirs, files in os.walk(LAB):
        for name in files:
            rel = os.path.relpath(os.path.join(d, name), REPO).replace(os.sep, "/")
            if is_cache_file(rel):
                cache_files += 1
            else:
                on_disk.add(rel)
    missing = sorted(set(rows) - on_disk)
    extra = sorted(on_disk - set(rows))
    changed = []
    for path in sorted(set(rows) & on_disk):
        digest, size = rows[path]
        full = os.path.join(REPO, *path.split("/"))
        if os.path.getsize(full) != size or sha256_file(full) != digest:
            changed.append(path)
    total = sum(size for _, size in rows.values())
    print("manifest lists %d files, %d bytes" % (len(rows), total))
    for label, items in (("missing from lab/", missing), ("in lab/ but not in the manifest", extra), ("content differs", changed)):
        if items:
            print("  %s: %d" % (label, len(items)))
            for p in items[:10]:
                print("     ", p)
            if len(items) > 10:
                print("      ... and %d more" % (len(items) - 10))
    if cache_files:
        print("  note: %d cache files under lab/ (compiled Python files, pytest cache) were left out of the comparison" % cache_files)
    ok = verdict(not (missing or extra or changed),
                 "%d of %d files present and identical; %d unlisted" % (len(rows) - len(missing) - len(changed), len(rows), len(extra)))
    sums = {}
    with open(os.path.join(REPO, "manifest", "SHA256SUMS"), encoding="utf-8") as f:
        for line in f:
            digest, path = line.rstrip("\n").split("  ", 1)
            sums[path] = digest
    same_list = sums == {path: digest for path, (digest, size) in rows.items()}
    ok = verdict(same_list, "manifest/SHA256SUMS lists the same %d files and hashes as the manifest" % len(sums)) and ok
    if "--zip" in argv:
        archive = argv[argv.index("--zip") + 1]
        expect = open(os.path.join(REPO, "manifest", "ARCHIVE.txt"), encoding="utf-8").read().split("sha256")[1].split()[0]
        got = sha256_file(archive)
        ok = verdict(got == expect, "archive SHA-256 %s" % ("matches the original archive" if got == expect else "differs: " + got)) and ok
        bad = 0
        with zipfile.ZipFile(archive) as z:
            names = set(z.namelist())
            for path, (digest, size) in rows.items():
                entry = "agentscope/" + path[len("lab/"):]
                if entry not in names or hashlib.sha256(z.read(entry)).hexdigest() != digest:
                    bad += 1
        ok = verdict(bad == 0, "%d of %d manifest entries equal the archive's own entries" % (len(rows) - bad, len(rows))) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
