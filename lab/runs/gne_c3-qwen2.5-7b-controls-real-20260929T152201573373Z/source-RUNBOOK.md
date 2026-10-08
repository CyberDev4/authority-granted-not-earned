# C3 runbook

Run from the project root (~/ai-lab/project/agentscope) with the venv active. Start every long run with
`setsid nohup ... < /dev/null &` so closing the terminal can't stop it.

1. `ollama pull qwen2.5:14b` and `ollama pull granite3.3:8b` (internet needed once).
2. `bash gne_c3/c3.sh check`: 26 tests OK, models listed.
3. `bash gne_c3/c3.sh freeze qwen2.5:7b granite3.3:8b qwen2.5:14b llama3.1:8b`
4. **Block A** (parallel, about 3 h): `all qwen2.5:7b` and `all granite3.3:8b`. `all` runs controls,
   then the probe, then the gate, then main.
5. **Block B:** `followup llama3.1:8b` (about 30 min), then `all qwen2.5:14b` (about 5 h, run alone for
   memory).
6. `bash gne_c3/c3.sh analyze`: H1, H2 and H3, per model.
7. `bash gne_c3/c3.sh audit`: invented-authorisation candidates across every main batch (C1, C2, C1M, C3); read logs/authority_review.txt to confirm each.

If a batch stops early: `bash gne_c3/c3.sh resume runs/<batch folder> MODEL`. Never rerun a stage.
