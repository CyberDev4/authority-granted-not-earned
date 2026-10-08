# C4G runbook (gpt-oss:20b, about 1-2 h)

Run from the project root with the venv active. Keep the Windows host awake. Nothing else running.

1. `bash gne_c4g/c4g.sh check`: 34 tests OK, gpt-oss:20b listed.
2. `bash gne_c4g/c4g.sh freeze gpt-oss:20b`
3. `setsid nohup bash gne_c4g/c4g.sh all gpt-oss:20b > logs/c4g.out 2>&1 < /dev/null &`
   Controls (12), probe (30) with the gate, then main (120) only if the gate passes.
4. Progress: `tail -n 5 logs/c4g.out`
5. When it prints "Batch complete" for main: `bash gne_c4g/c4g.sh analyze`

If a batch stops early: `bash gne_c4g/c4g.sh resume runs/<batch folder> gpt-oss:20b`. Never rerun a stage.
