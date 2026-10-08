# C4 runbook

Run from the project root (~/ai-lab/project/agentscope) with the venv active. Start every long run with
`setsid nohup ... < /dev/null &` so closing the terminal can't stop it. Keep the Windows host awake
(Power settings: Sleep = Never) while C4 runs.

1. Pull the models (internet needed once):
   `ollama pull command-r7b && ollama pull mistral-nemo:12b && ollama pull gpt-oss:20b`
2. Check gpt-oss fits in memory (not an experiment run; one plain reply):
   `ollama run gpt-oss:20b "Say OK." ; ollama stop gpt-oss:20b ; free -h`
3. `bash gne_c4/c4.sh check`: 29 tests OK, three models listed.
4. `bash gne_c4/c4.sh freeze command-r7b mistral-nemo:12b gpt-oss:20b`
5. Start the queue (about 14-18 h in total):
   `setsid nohup bash gne_c4/c4_queue.sh > logs/c4_queue.out 2>&1 < /dev/null &`
   For each model, in order, it runs controls, probe (with gate), follow-up, then main only if the
   gate passed, then unloads the model.
6. Check progress: `tail -n 5 logs/c4_queue.out`
7. When the queue prints QUEUE DONE: `bash gne_c4/c4.sh analyze`, then `bash gne_c4/c4.sh audit`.

If a batch stops early: `bash gne_c4/c4.sh resume runs/<batch folder> MODEL`. Never rerun a stage.
