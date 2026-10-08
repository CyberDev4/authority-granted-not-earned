#!/usr/bin/env bash
# C4 queue: every preregistered model, one at a time, in the preregistered order.
# A failed gate stops that model's main stage (by design) but never stops the queue.
cd "$(dirname "$0")/.." || exit 1
for M in command-r7b mistral-nemo:12b gpt-oss:20b; do
  echo "=== $(date -u '+%F %T') START $M"
  bash gne_c4/c4.sh all "$M" || echo "=== $M: stopped at the gate or an error (see logs/c4_*); continuing"
  ollama stop "$M" 2>/dev/null || true
  echo "=== $(date -u '+%F %T') END $M"
done
echo "=== $(date -u '+%F %T') QUEUE DONE"
