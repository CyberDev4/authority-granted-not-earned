# C1M runbook (mistral:7b, C1 design + text-call adapter)

Run from the project root (~/ai-lab/project/agentscope) with the venv active. Nothing touches C1, C2 or C2M.

1. `bash gne_c1m/c1m.sh check`: 23 tests OK, mistral:7b listed.
2. `bash gne_c1m/c1m.sh diag mistral:7b`: step 0, 25 single calls, descriptive.
3. `bash gne_c1m/c1m.sh freeze mistral:7b`
4. One stage at a time, in the background, validating each:
   `nohup bash gne_c1m/c1m.sh stage mistral:7b controls > logs/c1m_controls.out 2>&1 &`
   `nohup bash gne_c1m/c1m.sh stage mistral:7b probe > logs/c1m_probe.out 2>&1 &`
   `nohup bash gne_c1m/c1m.sh stage mistral:7b main > logs/c1m_main.out 2>&1 &`
5. If a batch stops early: `bash gne_c1m/c1m.sh resume runs/<batch folder> mistral:7b`. Never rerun.
6. `bash gne_c1m/c1m.sh analyze`

Then C2M (gne_c2m) runs the C2 design for mistral the same way; its diag step can be skipped (same
diagnostic). Record that in gne_c2m/DEVIATIONS.md.
