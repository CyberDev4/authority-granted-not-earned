# C5 runbook

Run after C4 has finished and been analysed. Run from the project root with the venv active. Start
long runs with `setsid nohup ... < /dev/null &`. Keep the Windows host awake.

1. `bash gne_c5/c5.sh check`: 16 tests OK, qwen2.5:7b listed.
2. Read C4's analysis. Note every model with "H4 ... SUPPORTED" in the Holm block. These join C5.
3. Freeze with qwen2.5:7b plus those models, for example:
   `bash gne_c5/c5.sh freeze qwen2.5:7b` or `bash gne_c5/c5.sh freeze qwen2.5:7b command-r7b`
4. For each frozen model, one at a time:
   `setsid nohup bash gne_c5/c5.sh all qwen2.5:7b > logs/c5_qwen7b.out 2>&1 < /dev/null &`
   About 8-9 h for qwen2.5:7b (12 controls, 60 probe calls, 360 main runs).
5. `bash gne_c5/c5.sh analyze`, then `bash gne_c5/c5.sh audit` and confirm candidates by hand.

If a batch stops early: `bash gne_c5/c5.sh resume runs/<batch folder> MODEL`. Never rerun a stage.
