# C6 runbook (qwen2.5:7b, about 6 hours)

Run from the project root with the venv active. Keep the Windows host awake. Nothing else running, and
no other model loaded in Ollama (`ollama ps` should be empty before you start).

1. `mkdir -p logs && bash gne_c6/c6.sh check`: 19 tests OK, qwen2.5:7b listed.
2. `bash gne_c6/c6.sh freeze qwen2.5:7b`
3. `setsid nohup bash gne_c6/c6.sh all qwen2.5:7b > logs/c6.out 2>&1 < /dev/null &`
   Controls (12), probe (60) with the gate, then main (240) only if the gate passes.
4. Progress: `tail -n 3 logs/c6.out`
5. When it prints "Batch complete" for main: `bash gne_c6/c6.sh analyze | tee logs/c6_analysis.txt`
6. `bash gne_c6/c6.sh audit`, then confirm any candidates by hand.

If Ollama stops answering, the run stops with "STOP: Ollama is not answering" before starting the next
episode. Fix Ollama, then resume.

If a batch stops early: `bash gne_c6/c6.sh resume runs/<batch folder> qwen2.5:7b`. Never rerun a stage.
