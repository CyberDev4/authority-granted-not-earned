#!/usr/bin/env bash
# Builds a publishable release of the Granted, Not Earned studies from the agentscope project root.
# Read-only on the project: copies into release/, never edits packages, runs or logs.
# Usage (from ~/ai-lab/project/agentscope, venv active): bash gne_release_kit/make_release.sh
set -uo pipefail
ROOT=$(pwd); KIT=$(cd "$(dirname "$0")" && pwd)
[ -d gne_core_c1 ] && [ -d gne_c3 ] && [ -d gne_c5 ] || { echo "STOP: run from the agentscope project root."; exit 1; }
STAMP=$(date -u +%Y%m%d); OUT="release/granted-not-earned-$STAMP"
[ -e "$OUT" ] && { echo "STOP: $OUT exists; remove it or wait until tomorrow."; exit 1; }
mkdir -p "$OUT"/{packages,runs,runs_excluded,results,logs}
echo "== 1. Packages (frozen code, preregistrations, freeze records, deviation logs)"
for p in gne_core_c1 gne_core_c2 gne_c1m gne_c2m gne_c3 gne_c4 gne_c4g gne_c5 gne_x2; do
  [ -d "$p" ] && cp -r "$p" "$OUT/packages/" && find "$OUT/packages/$p" -name __pycache__ -prune -exec rm -rf {} + && echo "  $p"
done
[ -f analyze_c1_wrapped.py ] && cp analyze_c1_wrapped.py "$OUT/packages/gne_core_c1/" && echo "  + analyze_c1_wrapped.py (C1 read-only wrapper, logged)"
[ -f analyze_c4_wrapped.py ] && cp analyze_c4_wrapped.py "$OUT/packages/gne_c4/" && echo "  + analyze_c4_wrapped.py (C4 read-only wrapper, logged)"
echo "== 2. Verify freeze hashes (a package whose files changed after its freeze is flagged)"
for p in gne_core_c1 gne_core_c2 gne_c1m gne_c3 gne_c4 gne_c4g gne_c5; do
  F="$OUT/packages/$p/FREEZE.md"; [ -f "$F" ] || { echo "  $p: no FREEZE.md (not frozen)"; continue; }
  ok=1; while read -r h f; do [ "$(sha256sum "$OUT/packages/$p/$f" | cut -d' ' -f1)" = "$h" ] || { ok=0; echo "  $p: MISMATCH $f"; }; done < <(sed -n 's/^    = //p' "$F")
  [ $ok = 1 ] && echo "  $p: all frozen hashes match"
done
echo "== 3. Run data (every real batch; excluded batches kept separately)"
for d in runs/gne_core_c1-* runs/gne_core_c2-* runs/gne_c1m-* runs/gne_c2m-* runs/gne_c3-* runs/gne_c4-* runs/gne_c4g-* runs/gne_c5-*; do [ -d "$d" ] && cp -r "$d" "$OUT/runs/"; done
[ -d runs_excluded ] && cp -r runs_excluded/. "$OUT/runs_excluded/" 2>/dev/null
echo "  $(ls "$OUT/runs" | wc -l) batches, $(ls "$OUT/runs_excluded" 2>/dev/null | wc -l) excluded"
echo "== 4. Analysis outputs (regenerated now, read-only)"
python analyze_c1_wrapped.py runs/gne_core_c1-*-real-*   > "$OUT/results/C1_analysis.txt"  2>&1 || echo "  C1 analysis returned an error (see file)"
python gne_core_c2/analyze_c2.py runs/gne_core_c2-*-real-* > "$OUT/results/C2_analysis.txt" 2>&1 || echo "  C2 analysis returned an error (see file)"
python gne_c1m/analyze_c1m.py runs/gne_c1m-mistral-7b-*-real-* > "$OUT/results/C1M_analysis.txt" 2>&1 || echo "  C1M analysis returned an error (see file)"
python gne_c3/analyze_c3.py runs/gne_c3-*-real-*         > "$OUT/results/C3_analysis.txt"  2>&1 || echo "  C3 analysis returned an error (see file)"
python analyze_c4_wrapped.py runs/gne_c4-*-real-*        > "$OUT/results/C4_analysis.txt"  2>&1 || echo "  C4 analysis returned an error (see file)"
python gne_c4g/analyze_c4g.py runs/gne_c4g-*-real-*      > "$OUT/results/C4G_analysis.txt" 2>&1 || echo "  C4G analysis returned an error (see file)"
python gne_c5/analyze_c5.py runs/gne_c5-*-real-*         > "$OUT/results/C5_analysis.txt"  2>&1 || echo "  C5 analysis returned an error (see file)"
python gne_c5/audit_authority.py runs/*-main-real-* --review "$OUT/results/authority_review.txt" > "$OUT/results/authority_audit.txt" 2>&1
[ -f logs/authority_confirmed.txt ] && cp logs/authority_confirmed.txt "$OUT/results/"
cp -r runs/gne_c1m-diag-* "$OUT/results/" 2>/dev/null
ls "$OUT/results"
echo "== 5. Run logs"
for f in logs/c1_* logs/c2_* logs/c1m_* logs/c3_* logs/c4_* logs/c4g_* logs/c5_* logs/*resume*; do [ -f "$f" ] && cp "$f" "$OUT/logs/"; done
echo "== 6. Scrub local paths from text files"
grep -rl "$HOME" "$OUT" 2>/dev/null | while read -r f; do sed -i "s#$HOME#~#g" "$f"; done
echo "  remaining occurrences of $HOME: $(grep -rl "$HOME" "$OUT" 2>/dev/null | wc -l)"
echo "== 7. Secret scan (review any hits before publishing)"
grep -rIlE "(api[_-]?key|secret|password|token)[\"' ]*[:=]" "$OUT" --exclude-dir=runs --exclude-dir=runs_excluded 2>/dev/null | sed 's/^/  CHECK: /' || true
grep -rIoE "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}" "$OUT" 2>/dev/null | sort -u | head -5 | sed 's/^/  EMAIL: /' || true
echo "== 8. Top-level files"
cp "$KIT/README.md" "$KIT/LICENSE" "$OUT/"
echo "== 9. Archive and checksums"
(cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
tar -czf "$OUT.tar.gz" -C release "$(basename "$OUT")"
sha256sum "$OUT.tar.gz"; du -sh "$OUT" "$OUT.tar.gz"
echo "DONE: $OUT (folder) and $OUT.tar.gz. Read README.md and the secret-scan lines above before publishing."
