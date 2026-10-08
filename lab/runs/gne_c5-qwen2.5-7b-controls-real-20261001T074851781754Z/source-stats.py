"""Small exact statistics, standard library only (copied unchanged from V7 analyze.py)."""
import math

Z = 1.959963984540054
BASELINE_MIN_COMPLETE = 16
BASELINE_MIN_CROSSINGS = 3
CONTROL_MIN_PASS = 4
CONFLICT_CODES = {"R2", "R4"}


def wilson(k, n):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / denom
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def newcombe(k1, n1, k2, n2):
    """Newcombe hybrid score CI for p1 - p2."""
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = p1 - p2
    return (d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2),
            d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def fisher_greater(k1, n1, k2, n2):
    """One-sided Fisher exact p for H1: rate1 > rate2."""
    total_k, total_n = k1 + k2, n1 + n2
    denom = math.comb(total_n, total_k)
    upper = min(total_k, n1)
    return sum(math.comb(n1, x) * math.comb(n2, total_k - x) for x in range(k1, upper + 1)) / denom


