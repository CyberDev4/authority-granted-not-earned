#!/usr/bin/env bash
# C1 driver: Granted, Not Earned core pilot on open models. Run from the project root with the venv active.
#   bash gne_core_c1/c1.sh check                     # tests + installed models (no generation)
#   bash gne_core_c1/c1.sh freeze MODEL [MODEL ...]  # once: records code hashes and the planned model list
#   bash gne_core_c1/c1.sh run MODEL                 # controls -> probe -> main for one model
#   bash gne_core_c1/c1.sh resume BATCH_FOLDER MODEL
#   bash gne_core_c1/c1.sh analyze                   # every real C1 batch, per model, then a table
set -euo pipefail
PKG=gne_core_c1
OLLAMA="${OLLAMA:-http://127.0.0.1:11434}"
[ -d "$PKG" ] || { echo "STOP: run from the project root ($PKG not found)."; exit 1; }
hashes() { (cd "$PKG" && sha256sum run.py analyze_c1.py stats.py test_c1.py c1.sh PREREGISTRATION.md); }
models() { python - "$OLLAMA" <<'PY'
import json, sys
from urllib.request import ProxyHandler, build_opener
try:
    tags = json.load(build_opener(ProxyHandler({})).open(sys.argv[1] + "/api/tags", timeout=10))
except Exception as e:
    print("OLLAMA_UNREACHABLE", e); sys.exit(0)
for m in tags.get("models", []):
    print("  %-28s %s  %.1f GB" % (m["name"], m["digest"][:12], m.get("size", 0) / 1e9))
PY
}
case "${1:-}" in
check)
  echo "== Tests (expect: Ran 18 tests ... OK)"; python -m unittest discover -s "$PKG" -p 'test_c1.py' 2>&1 | tail -3
  echo "== Installed models at $OLLAMA"; models
  echo "== Hashes"; hashes
  echo "== Memory and disk"; free -h | head -2; df -h . | tail -1 ;;
freeze)
  shift; [ $# -ge 1 ] || { echo "usage: c1.sh freeze MODEL [MODEL ...]"; exit 1; }
  [ -e "$PKG/FREEZE.md" ] && { echo "STOP: already frozen."; exit 1; }
  python -m unittest discover -s "$PKG" -p 'test_c1.py' >/dev/null 2>&1 || { echo "STOP: tests fail"; exit 1; }
  installed=$(models)
  for m in "$@"; do echo "$installed" | grep -q " $m[ :]" || echo "$installed" | grep -q " $m:latest " || { echo "STOP: $m not installed (ollama pull $m)"; exit 1; }; done
  { echo "# C1 freeze record"; echo; echo "- Frozen (UTC): $(date -u '+%Y-%m-%d %H:%M:%S')"
    echo "- Planned models, in run order (every model started is reported): $*"
    echo "- Installed models:"; echo "$installed" | sed 's/^/  /'
    echo "- Host: $(hostname), $(nproc) CPUs, $(free -g | awk '/Mem:/{print $2}') GiB RAM, Ollama at $OLLAMA"
    echo "- SHA-256:"; hashes | sed 's/^/    = /'; } > "$PKG/FREEZE.md"
  cat "$PKG/FREEZE.md"
  { git rev-parse --is-inside-work-tree >/dev/null 2>&1 && git add "$PKG"/*.py "$PKG"/*.md "$PKG"/c1.sh && git commit -qm "C1 freeze" && git tag -a c1-freeze -m "C1 frozen" && echo "git tag c1-freeze created"; } || echo "(no git tag: FREEZE.md is the record)"
  echo "FROZEN." ;;
run)
  M="${2:?usage: c1.sh run MODEL}"
  [ -e "$PKG/FREEZE.md" ] || { echo "STOP: freeze first."; exit 1; }
  [ "$(hashes)" = "$(sed -n 's/^    = //p' "$PKG/FREEZE.md")" ] || { echo "STOP: files changed since the freeze."; exit 1; }
  grep -q "Planned models.*\b$M\b" "$PKG/FREEZE.md" || echo "NOTE: $M was not in the planned list; it will be reported as an added model."
  slug=$(echo "$M" | tr ':/' '--'); mkdir -p logs
  for stage in controls probe main; do
    if ls -d runs/${PKG}-${slug}-${stage}-real-* >/dev/null 2>&1; then echo "SKIP: $stage batch exists for $M (use resume)"; continue; fi
    python "$PKG/run.py" --real --model "$M" --stage "$stage" --ollama "$OLLAMA" 2>&1 | tee "logs/c1_${slug}_${stage}.log"
  done ;;
resume)
  python "$PKG/run.py" --real --resume "${2:?folder}" --model "${3:?model}" 2>&1 | tee -a logs/c1_resume.log ;;
analyze)
  ls -d runs/${PKG}-*-real-* >/dev/null 2>&1 || { echo "STOP: no real C1 batches."; exit 1; }
  python "$PKG/analyze_c1.py" runs/${PKG}-*-real-* ;;
*) sed -n '2,8p' "$0"; exit 1 ;;
esac
