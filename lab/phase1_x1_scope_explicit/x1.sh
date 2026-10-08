#!/usr/bin/env bash
# X1 driver. Run from the project root (~/ai-lab/project/agentscope) with the venv active.
#   bash phase1_x1_scope_explicit/x1.sh check      # tests + model identity, no model generation
#   bash phase1_x1_scope_explicit/x1.sh freeze     # writes FREEZE.md once, then read-only
#   bash phase1_x1_scope_explicit/x1.sh run        # the real 40-episode batch
#   bash phase1_x1_scope_explicit/x1.sh resume <batch folder>
#   bash phase1_x1_scope_explicit/x1.sh analyze [batch folder]   # default: latest real batch
set -euo pipefail
PKG=phase1_x1_scope_explicit
MODEL=day1-qwen25-3b
EXPECTED_ID=7ad55ddc88cd
[ -d "$PKG" ] || { echo "STOP: run from the project root (folder $PKG not found here)."; exit 1; }

model_info() {
python - "$MODEL" <<'PY'
import json, sys
from urllib.request import ProxyHandler, build_opener
o = build_opener(ProxyHandler({}))
try:
    tags = json.load(o.open("http://127.0.0.1:11434/api/tags", timeout=10))
    ver = json.load(o.open("http://127.0.0.1:11434/api/version", timeout=10)).get("version")
except Exception as e:
    print("OLLAMA_UNREACHABLE", e); sys.exit(0)
name = sys.argv[1]
m = [x for x in tags.get("models", []) if x.get("name") in (name, name + ":latest")]
print("MODEL", m[0]["name"], m[0]["digest"], "ollama", ver) if m else print("MODEL_MISSING", name)
PY
}

hashes() { (cd "$PKG" && sha256sum adapter.py analyze.py analyze_x1.py run.py test_x1.py x1.sh PREREGISTRATION.md); }

case "${1:-}" in
check)
  echo "== 1. Tests (expect: Ran 14 tests ... OK)"
  python -m unittest discover -s "$PKG" -p 'test_x1.py' 2>&1 | tail -3
  echo "== 2. Model identity (expect digest starting $EXPECTED_ID)"
  info=$(model_info); echo "$info"
  case "$info" in MODEL*"$EXPECTED_ID"*) echo "PASS: model identity";; *) echo "STOP: model missing, unreachable or different"; exit 1;; esac
  echo "== 3. File hashes (compare with RUNBOOK.md)"; hashes
  echo "== 4. Free memory"; free -h | head -2
  echo "CHECK DONE. No model generation was run." ;;
freeze)
  [ -e "$PKG/FREEZE.md" ] && { echo "STOP: FREEZE.md already exists; the protocol is frozen."; exit 1; }
  python -m unittest discover -s "$PKG" -p 'test_x1.py' >/dev/null 2>&1 || { echo "STOP: tests fail"; exit 1; }
  info=$(model_info)
  case "$info" in MODEL*"$EXPECTED_ID"*) ;; *) echo "STOP: $info"; exit 1;; esac
  { echo "# X1 freeze record"; echo; echo "- Frozen (UTC): $(date -u '+%Y-%m-%d %H:%M:%S')";
    echo "- $info"; echo "- Host: $(hostname), $(nproc) CPUs, $(free -g | awk '/Mem:/{print $2}') GiB RAM";
    echo "- SHA-256:"; hashes | sed 's/^/    /'; } > "$PKG/FREEZE.md"
  cat "$PKG/FREEZE.md"
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    { git add "$PKG/"*.py "$PKG/"*.md "$PKG/x1.sh" && git commit -qm "X1 freeze" && git tag -a x1-freeze -m "X1 frozen before any X1 model run" && echo "git tag x1-freeze created"; } || echo "(git commit/tag skipped: FREEZE.md and its timestamp are the record)"
  else echo "(not a git repo: keep FREEZE.md and its timestamp as the record)"; fi
  echo "FROZEN." ;;
run)
  [ -e "$PKG/FREEZE.md" ] || { echo "STOP: freeze first."; exit 1; }
  now=$(hashes); frozen=$(sed -n 's/^    //p' "$PKG/FREEZE.md")
  [ "$now" = "$frozen" ] || { echo "STOP: files changed since the freeze. Nothing run."; exit 1; }
  ls -d runs/${PKG}-scope-real-* >/dev/null 2>&1 && { echo "STOP: a real X1 batch already exists. Use: x1.sh resume <folder>"; exit 1; }
  mkdir -p logs
  python "$PKG/run.py" --real --stage scope 2>&1 | tee "logs/x1_run_$(date -u +%Y%m%dT%H%M%SZ).log" ;;
resume)
  [ -n "${2:-}" ] || { echo "usage: x1.sh resume <batch folder>"; exit 1; }
  mkdir -p logs
  python "$PKG/run.py" --real --resume "$2" 2>&1 | tee -a "logs/x1_resume_$(date -u +%Y%m%dT%H%M%SZ).log" ;;
analyze)
  B="${2:-$(ls -dt runs/${PKG}-scope-real-* 2>/dev/null | head -1)}"
  [ -n "$B" ] || { echo "STOP: no real X1 batch found."; exit 1; }
  python "$PKG/analyze_x1.py" "$B" ;;
*) sed -n '2,8p' "$0"; exit 1 ;;
esac
