#!/usr/bin/env bash
# C2M driver: the C2 design for mistral:7b with the text-call adapter. Run from the project root with the venv active.
#   bash gne_c2m/c2m.sh check                     # tests + installed models (no generation)
#   bash gne_c2m/c2m.sh diag MODEL                # step 0, before the freeze: can the model make native tool calls?
#   bash gne_c2m/c2m.sh freeze MODEL [MODEL ...]  # once: records code hashes and the planned model list
#   bash gne_c2m/c2m.sh controls MODEL            # 12 episodes: can the model make each target call when asked?
#   bash gne_c2m/c2m.sh probe MODEL               # 30 single calls: does the model now rate P17 differently?
#   bash gne_c2m/c2m.sh main MODEL                # 120 episodes; runs even if the gate failed (the gate only governs the competence reading)
#   bash gne_c2m/c2m.sh all MODEL                 # controls -> probe -> gate -> main, stopping at the gate
#   bash gne_c2m/c2m.sh resume BATCH_FOLDER MODEL
#   bash gne_c2m/c2m.sh analyze                   # every real C2 batch, per model, then a table
set -euo pipefail
PKG=gne_c2m
OLLAMA="${OLLAMA:-http://127.0.0.1:11434}"
[ -d "$PKG" ] || { echo "STOP: run from the project root ($PKG not found)."; exit 1; }
hashes() { (cd "$PKG" && sha256sum run.py analyze_c2m.py stats.py test_c2m.py c2m.sh diag.py PREREGISTRATION.md); }
frozen() {
  [ -e "$PKG/FREEZE.md" ] || { echo "STOP: freeze first."; exit 1; }
  [ "$(hashes)" = "$(sed -n 's/^    = //p' "$PKG/FREEZE.md")" ] || { echo "STOP: files changed since the freeze."; exit 1; }
}
slugof() { echo "$1" | tr ':/' '--'; }
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
stage() {  # stage MODEL STAGE
  local M="$1" S="$2" slug; slug=$(slugof "$1"); mkdir -p logs
  if ls -d runs/${PKG}-${slug}-${S}-real-* >/dev/null 2>&1; then
    echo "STOP: a $S batch already exists for $M. Use resume on it, never a rerun."; exit 1; fi
  python "$PKG/run.py" --real --model "$M" --stage "$S" --ollama "$OLLAMA" 2>&1 | tee "logs/c2m_${slug}_${S}.log"
}
case "${1:-}" in
check)
  echo "== Tests (expect: OK)"; python -m unittest discover -s "$PKG" -p 'test_c2m.py' 2>&1 | tail -3
  echo "== Installed models at $OLLAMA"; models
  echo "== Hashes"; hashes
  echo "== CPUs, memory and disk"; nproc; free -h | head -2; df -h . | tail -1 ;;
freeze)
  shift; [ $# -ge 1 ] || { echo "usage: c2m.sh freeze MODEL [MODEL ...]"; exit 1; }
  [ -e "$PKG/FREEZE.md" ] && { echo "STOP: already frozen."; exit 1; }
  python -m unittest discover -s "$PKG" -p 'test_c2m.py' >/dev/null 2>&1 || { echo "STOP: tests fail"; exit 1; }
  installed=$(models)
  for m in "$@"; do echo "$installed" | grep -q " $m[ :]" || echo "$installed" | grep -q " $m:latest " || { echo "STOP: $m not installed (ollama pull $m)"; exit 1; }; done
  { echo "# C2M freeze record"; echo; echo "- Frozen (UTC): $(date -u '+%Y-%m-%d %H:%M:%S')"
    echo "- Planned models (every model started is reported): $*"
    echo "- Installed models:"; echo "$installed" | sed 's/^/  /'
    echo "- Host: $(hostname), $(nproc) CPUs, $(free -g | awk '/Mem:/{print $2}') GiB RAM, Ollama at $OLLAMA"
    echo "- SHA-256:"; hashes | sed 's/^/    = /'; } > "$PKG/FREEZE.md"
  cat "$PKG/FREEZE.md"; echo "FROZEN." ;;
diag)
  M="${2:?usage: c2m.sh diag MODEL}"; mkdir -p logs
  python "$PKG/diag.py" --model "$M" --ollama "$OLLAMA" 2>&1 | tee "logs/c2m_$(slugof "$M")_diag.log" ;;
controls)
  M="${2:?usage: c2m.sh controls MODEL}"; frozen; stage "$M" controls ;;
all)
  M="${2:?usage: c2m.sh all MODEL}"; frozen
  for S in controls probe main; do
    if ls -d runs/${PKG}-$(slugof "$M")-${S}-real-* >/dev/null 2>&1; then echo "SKIP: $S batch exists for $M (resume it if unfinished)"; continue; fi
    bash "$0" "$S" "$M"
  done ;;
probe)
  M="${2:?usage: c2m.sh probe MODEL}"; frozen; stage "$M" probe
  python "$PKG/analyze_c2m.py" --gate "$M" runs/${PKG}-$(slugof "$M")-probe-real-* || true ;;
main)
  M="${2:?usage: c2m.sh main MODEL}"; frozen
  ls -d runs/${PKG}-$(slugof "$M")-probe-real-* >/dev/null 2>&1 || { echo "STOP: run the probe for $M first."; exit 1; }
  python "$PKG/analyze_c2m.py" --gate "$M" runs/${PKG}-$(slugof "$M")-probe-real-* || \
    echo "NOTE: probe gate failed for $M. C2M runs main anyway (preregistered): the competence reading is not made; interface and written-action results are."
  stage "$M" main ;;
resume)
  frozen; python "$PKG/run.py" --real --resume "${2:?folder}" --model "${3:?model}" 2>&1 | tee -a logs/c2m_resume.log ;;
analyze)
  ls -d runs/${PKG}-*-real-* >/dev/null 2>&1 || { echo "STOP: no real C2M batches."; exit 1; }
  python "$PKG/analyze_c2m.py" runs/${PKG}-*-real-* ;;
*) sed -n '2,8p' "$0"; exit 1 ;;
esac
