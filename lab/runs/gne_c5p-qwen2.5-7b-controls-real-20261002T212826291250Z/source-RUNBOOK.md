# C5P runbook (qwen2.5:7b, about 8 to 10 hours)

Run from the project root. The virtual environment is optional: the script uses `python` if present and
`python3` otherwise. Start it only when no other study is running (`pgrep -af run.py` prints nothing) and
no other model is loaded (`ollama ps` lists nothing). Keep the Windows host awake and plugged in, with
sleep turned off: this run is long enough to cross a night.

1. `bash gne_c5p/c5p.sh check`: 24 tests OK, qwen2.5:7b listed.
2. `bash gne_c5p/c5p.sh freeze qwen2.5:7b`
3. `mkdir -p logs && setsid nohup bash gne_c5p/c5p.sh all qwen2.5:7b > logs/c5p.out 2>&1 < /dev/null &`
   Controls (12), probe (60) with the gate, then main (360) only if the gate passes. The shell prints
   "Done" at once; that is the launcher, and the run continues in the background.
4. Progress: `tail -n 3 logs/c5p.out`
5. When it prints "Batch complete" for main: `bash gne_c5p/c5p.sh analyze | tee logs/c5p_analysis.txt`
   The line to look for is "CORRECTED, LIMIT OR NO LIMIT: REPRODUCED" or "NOT REPRODUCED".
6. `bash gne_c5p/c5p.sh audit`, then confirm any candidates by hand.

Each main episode ends with one extra short call, the belief question. It is saved as
`request-belief.json` and `response-belief.json` in the episode folder.

If Ollama stops answering, the run stops with "STOP: Ollama is not answering" before starting the next
episode. Fix Ollama, then resume.

If a batch stops early (shutdown, sleep, restart):
`setsid nohup bash gne_c5p/c5p.sh resume runs/<batch folder> qwen2.5:7b > logs/c5p_resume.out 2>&1 < /dev/null &`
Never rerun a stage. If main never started because the probe was interrupted, resume the probe batch,
then run `bash gne_c5p/c5p.sh main qwen2.5:7b` the same detached way.

The old C5 batches in `runs/gne_c5-*` are not touched and are not read by C5P's analysis.
