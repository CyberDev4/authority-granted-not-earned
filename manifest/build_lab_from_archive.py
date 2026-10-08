#!/usr/bin/env python3
"""Rebuild the lab/ folder of this repository from the original archive.

The research record in lab/ is the project folder exactly as it stood on the lab
machine when the archive was taken on 6 October 2026. Every file in lab/ is
byte-for-byte the file in the archive, at the same relative path. Nothing in
lab/ was edited for publication. A few things in the archive were left out;
LEAVE_OUT below names each one and says why.

Usage:
    python3 manifest/build_lab_from_archive.py ARCHIVE.zip OUTPUT_DIR [--write-manifest]

It unpacks the kept files into OUTPUT_DIR/lab and, with --write-manifest, writes
OUTPUT_DIR/manifest/MANIFEST.tsv, LEFT_OUT.tsv, SHA256SUMS and ARCHIVE.txt.
Without that flag it only unpacks, so the result can be compared with the
manifest already in the repository (python3 verify/check_manifest.py).

Standard library only.
"""
import hashlib
import os
import sys
import zipfile

ARCHIVE_NAME = "agentscope_full_20261006T035010.zip"
ARCHIVE_SHA256 = "37d829a96ebc35172e6e9b7720569d96fbc0c402852862baaa55f993f43b901f"
TOP = "agentscope/"  # every entry in the archive sits under this folder

# (path prefix or exact path, reason). A trailing slash means "this folder and all in it".
LEAVE_OUT = [
    ("release/granted-not-earned-20261001/",
     "unpacked copy of release/granted-not-earned-20261001.tar.gz, which is kept; all 13,926 files are identical to the tarball's members"),
    ("agentscope/",
     "side project: a monitor for coding-agent session logs; not part of this research, has no saved output, and shares its name with an existing framework"),
    ("scripts/", "command-line scripts of that side project"),
    ("tests/", "tests of that side project and of the first harness; they import the side project"),
    ("tests-result.txt", "stale output of one run of those tests (written 14 September, UTC)"),
    ("README.md", "the 11 September README: it describes the first plan (hosted models and the side project), not these studies"),
    (".gitignore", "it ignored runs/, which would hide the evidence; replaced by the repository's own"),
    (".pytest_cache/", "test-runner cache"),
]


def reason_for(rel):
    for prefix, why in LEAVE_OUT:
        if prefix.endswith("/"):
            if rel.startswith(prefix):
                return why
        elif rel == prefix:
            return why
    return None


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    archive, out = argv[1], argv[2]
    write_manifest = "--write-manifest" in argv[3:]
    got = sha256_file(archive)
    if got != ARCHIVE_SHA256:
        print("WARNING: this is not the original archive.\n  expected sha256 %s\n  got      %s" % (ARCHIVE_SHA256, got))
        if "--force" not in argv[3:]:
            return 1
    lab = os.path.join(out, "lab")
    kept, left = [], []
    with zipfile.ZipFile(archive) as z:
        infos = [i for i in z.infolist() if not i.is_dir()]
        for info in infos:
            if not info.filename.startswith(TOP):
                raise SystemExit("unexpected entry outside %s: %s" % (TOP, info.filename))
            rel = info.filename[len(TOP):]
            data = z.read(info)
            digest = hashlib.sha256(data).hexdigest()
            mode = (info.external_attr >> 16) & 0o777
            when = "%04d-%02d-%02d %02d:%02d:%02d" % info.date_time
            why = reason_for(rel)
            if why is not None:
                left.append((rel, len(data), digest, when, why))
                continue
            dest = os.path.join(lab, *rel.split("/"))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(data)
            os.chmod(dest, 0o755 if mode & 0o100 else 0o644)
            kept.append((rel, len(data), digest, when, "x" if mode & 0o100 else "-"))
    kept.sort()
    left.sort()
    print("archive entries: %d   kept in lab/: %d   left out: %d" % (len(kept) + len(left), len(kept), len(left)))
    if write_manifest:
        mdir = os.path.join(out, "manifest")
        os.makedirs(mdir, exist_ok=True)
        with open(os.path.join(mdir, "MANIFEST.tsv"), "w", encoding="utf-8", newline="\n") as f:
            f.write("sha256\tbytes\texec\tarchive_time\tpath\n")
            for rel, size, digest, when, x in kept:
                f.write("%s\t%d\t%s\t%s\tlab/%s\n" % (digest, size, x, when, rel))
        with open(os.path.join(mdir, "SHA256SUMS"), "w", encoding="utf-8", newline="\n") as f:
            for rel, size, digest, when, x in kept:
                f.write("%s  lab/%s\n" % (digest, rel))
        with open(os.path.join(mdir, "LEFT_OUT.tsv"), "w", encoding="utf-8", newline="\n") as f:
            f.write("sha256\tbytes\tarchive_time\tarchive_path\treason\n")
            for rel, size, digest, when, why in left:
                f.write("%s\t%d\t%s\t%s\t%s\n" % (digest, size, when, rel, why))
        with open(os.path.join(mdir, "ARCHIVE.txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write("name     %s\n" % ARCHIVE_NAME)
            f.write("sha256   %s\n" % ARCHIVE_SHA256)
            f.write("bytes    %d\n" % os.path.getsize(archive))
            f.write("files    %d\n" % (len(kept) + len(left)))
            f.write("kept     %d  (lab/, listed in MANIFEST.tsv)\n" % len(kept))
            f.write("left out %d  (listed with reasons in LEFT_OUT.tsv)\n" % len(left))
        print("wrote manifest files to", mdir)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
