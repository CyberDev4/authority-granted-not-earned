# C2 runbook

Run from the project root (~/ai-lab/project/agentscope) with the venv active. Nothing touches C1.

1. `ollama pull qwen2.5:7b` (internet needed once), then disconnect if you prefer.
2. `bash gne_core_c2/c2.sh check`: 21 tests OK, three models listed, 12 CPUs.
3. `bash gne_core_c2/c2.sh freeze qwen2.5:3b llama3.1:8b qwen2.5:7b`: writes FREEZE.md. No package file
   may change after this.
4. Per model, stage by stage (validate each before the next), in the background:
   `nohup bash gne_core_c2/c2.sh controls MODEL > logs/c2_SLUG_controls.out 2>&1 &`
   `nohup bash gne_core_c2/c2.sh probe MODEL > logs/c2_SLUG_probe.out 2>&1 &` (ends with PROBE GATE PASS or FAIL)
   `nohup bash gne_core_c2/c2.sh main MODEL > logs/c2_SLUG_main.out 2>&1 &` (refuses if the gate failed)
   Run at most two models at once.
5. If a batch stops early: `bash gne_core_c2/c2.sh resume runs/<batch folder> MODEL`. Never start that stage again.
6. `bash gne_core_c2/c2.sh analyze`: per-model controls, gate, R1, R2, reading, seniority and
   exploratory measures, then the cross-model table.

Any deviation goes in gne_core_c2/DEVIATIONS.md (not hashed).
