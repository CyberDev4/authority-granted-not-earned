"""Shared helpers for the checking scripts. Standard library only."""
import hashlib
import math
import os
import sys

sys.dont_write_bytecode = True  # never leave __pycache__ folders next to the record

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
LAB = os.path.join(REPO, "lab")

# The twelve studies that ran, in the order they ran, with the package folder of each.
STUDIES = [
    ("V6", "phase1_v6_frozen_2x2"),
    ("X1", "phase1_x1_scope_explicit"),
    ("V7", "phase1_v7_timeout"),
    ("C1", "gne_core_c1"),
    ("C2", "gne_core_c2"),
    ("C1M", "gne_c1m"),
    ("C3", "gne_c3"),
    ("C4", "gne_c4"),
    ("C4G", "gne_c4g"),
    ("C5", "gne_c5"),
    ("C6", "gne_c6"),
    ("C5P", "gne_c5p"),
]
STUDY_OF = {pkg: name for name, pkg in STUDIES}


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def clean_env():
    """Environment for child Python processes: no bytecode files, no user site, fixed locale."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONUTF8"] = "1"            # the same text encoding on every system
    env["PYTHONIOENCODING"] = "utf-8"
    env["LC_ALL"] = "C.UTF-8"
    env["LANG"] = "C.UTF-8"
    env.pop("PYTHONPATH", None)
    return env


def banner(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def verdict(ok, text):
    print(("PASS  " if ok else "FAIL  ") + text)
    return ok


# ---------------------------------------------------------------- statistics

def hypergeom_pmf(k, K, n, N):
    """P(X = k) when n items are drawn from N of which K are 'successes'."""
    if k < max(0, n - (N - K)) or k > min(K, n):
        return 0.0
    return math.comb(K, k) * math.comb(N - K, n - k) / math.comb(N, n)


def fisher_one_sided(k1, n1, k2, n2):
    """One-sided Fisher exact test that group 1's rate is higher than group 2's.

    k1 of n1 against k2 of n2. Returns P(at least k1 in group 1 | margins).
    """
    if not n1 or not n2:
        return float("nan")
    N, K = n1 + n2, k1 + k2
    return min(1.0, sum(hypergeom_pmf(x, K, n1, N) for x in range(k1, min(K, n1) + 1)))


def fisher_two_sided(k1, n1, k2, n2):
    """Two-sided Fisher exact test: total probability of all tables no more likely than the one seen."""
    if not n1 or not n2:
        return float("nan")
    N, K = n1 + n2, k1 + k2
    p_obs = hypergeom_pmf(k1, K, n1, N)
    lo, hi = max(0, n1 - (N - K)), min(K, n1)
    return min(1.0, sum(p for p in (hypergeom_pmf(x, K, n1, N) for x in range(lo, hi + 1)) if p <= p_obs * (1 + 1e-9)))


def wilson(k, n, z=1.959963984540054):
    """95% Wilson interval for k of n."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))
