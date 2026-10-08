#!/usr/bin/env bash
# C4G driver: C4 for gpt-oss:20b with invalid calls answered by an error (preregistered). Run from the project root with the venv active.
#   bash gne_c4g/c4g.sh check                     # tests + installed models (no generation)
#   bash gne_c4g/c4g.sh freeze MODEL [MODEL ...]  # once: records code hashes and the planned model list
#   bash gne_c4g/c4g.sh controls MODEL            # 12 episodes: can the model make each target call when asked?
#   bash gne_c4g/c4g.sh probe MODEL               # 30 single calls: does the model now rate P17 differently?
#   bash gne_c4g/c4g.sh main MODEL                # 120 episodes; refuses unless that model's probe gate passed
#   bash gne_c4g/c4g.sh all MODEL                 # controls -> probe -> gate -> main, stopping at the gate
#   bash gne_c4g/c4g.sh followup MODEL            # 90 single calls: H3, is \"do not call any tools\" ignored more at L3?
#   bash gne_c4g/c4g.sh resume BATCH_FOLDER MODEL
#   bash gne_c4g/c4g.sh analyze                   # every real C4G batch: H4 for gpt-oss
#   bash gne_c4g/c4g.sh audit                     # invented-authorisation audit across ALL main batches (C1 to C4)
set -euo pipefail
PKG=gne_c4g
OLLAMA="${OLLAMA:-http://127.0.0.1:11434}"
[ -d "$PKG" ] || { echo "STOP: run from the project root ($PKG not found)."; exit 1; }
hashes() { (cd "$PKG" && sha256sum run.py analyze_c4g.py audit_authority.py stats.py test_c4g.py c4g.sh PREREGISTRATION.md); }
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
  python "$PKG/run.py" --real --model "$M" --stage "$S" --ollama "$OLLAMA" 2>&1 | tee "logs/c4g_${slug}_${S}.log"
}
case "${1:-}" in
check)
  echo "== Tests (expect: OK)"; python -m unittest discover -s "$PKG" -p 'test_c4g.py' 2>&1 | tail -3
  echo "== Installed models at $OLLAMA"; models
  echo "== Hashes"; hashes
  echo "== CPUs, memory and disk"; nproc; free -h | head -2; df -h . | tail -1 ;;
freeze)
  shift; [ $# -ge 1 ] || { echo "usage: c4g.sh freeze MODEL [MODEL ...]"; exit 1; }
  [ -e "$PKG/FREEZE.md" ] && { echo "STOP: already frozen."; exit 1; }
  python -m unittest discover -s "$PKG" -p 'test_c4g.py' >/dev/null 2>&1 || { echo "STOP: tests fail"; exit 1; }
  installed=$(models)
  for m in "$@"; do echo "$installed" | grep -q " $m[ :]" || echo "$installed" | grep -q " $m:latest " || { echo "STOP: $m not installed (ollama pull $m)"; exit 1; }; done
  { echo "# C4G freeze record"; echo; echo "- Frozen (UTC): $(date -u '+%Y-%m-%d %H:%M:%S')"
    echo "- Planned models (every model started is reported): $*"
    echo "- Installed models:"; echo "$installed" | sed 's/^/  /'
    echo "- Host: $(hostname), $(nproc) CPUs, $(free -g | awk '/Mem:/{print $2}') GiB RAM, Ollama at $OLLAMA"
    echo "- SHA-256:"; hashes | sed 's/^/    = /'; } > "$PKG/FREEZE.md"
  cat "$PKG/FREEZE.md"; echo "FROZEN." ;;
followup)
  M="${2:?usage: c4g.sh followup MODEL}"; frozen; stage "$M" followup ;;
controls)
  M="${2:?usage: c4g.sh controls MODEL}"; frozen; stage "$M" controls ;;
all)
  M="${2:?usage: c4g.sh all MODEL}"; frozen
  for S in controls probe main; do
    if ls -d runs/${PKG}-$(slugof "$M")-${S}-real-* >/dev/null 2>&1; then echo "SKIP: $S batch exists for $M (resume it if unfinished)"; continue; fi
    bash "$0" "$S" "$M"
  done ;;
probe)
  M="${2:?usage: c4g.sh probe MODEL}"; frozen; stage "$M" probe
  python "$PKG/analyze_c4g.py" --gate "$M" runs/${PKG}-$(slugof "$M")-probe-real-* || true ;;
main)
  M="${2:?usage: c4g.sh main MODEL}"; frozen
  ls -d runs/${PKG}-$(slugof "$M")-probe-real-* >/dev/null 2>&1 || { echo "STOP: run the probe for $M first."; exit 1; }
  python "$PKG/analyze_c4g.py" --gate "$M" runs/${PKG}-$(slugof "$M")-probe-real-* || {
    echo "STOP: probe gate failed for $M. By the preregistration, no main stage is run for this model."; exit 1; }
  stage "$M" main ;;
resume)
  frozen; python "$PKG/run.py" --real --resume "${2:?folder}" --model "${3:?model}" 2>&1 | tee -a logs/c4g_resume.log ;;
audit)
  python "$PKG/audit_authority.py" runs/*-main-real-* --review logs/authority_review.txt ;;
analyze)
  ls -d runs/${PKG}-*-real-* >/dev/null 2>&1 || { echo "STOP: no real C4G batches."; exit 1; }
  python "$PKG/analyze_c4g.py" runs/${PKG}-*-real-* ;;
*) sed -n '2,8p' "$0"; exit 1 ;;
esac
