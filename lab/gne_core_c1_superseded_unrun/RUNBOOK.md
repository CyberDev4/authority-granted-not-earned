# C1 runbook: Granted, Not Earned core pilot on open models

Run in the VM from `~/ai-lab/project/agentscope` with the venv active. Read PREREGISTRATION.md first.
Run one model at a time; nothing else on the VM.

## Which models

Open models with tool support that fit a 10 GiB VM (about 5 GB each on disk). Official Ollama tags only,
because C1 uses each model's own chat template; custom models such as `day1-qwen25-3b` may lack tool
support.

| Order | Model | Why |
|---|---|---|
| 1 | `qwen2.5:3b` | Fastest; same family as V1-X2; use it to shake out problems |
| 2 | `qwen2.5:7b` | Larger model of the same family |
| 3 | `llama3.1:8b` | Different family (Meta) |
| 4 | `mistral:7b` | Different family (Mistral) |

Pull before the freeze, one at a time: `ollama pull qwen2.5:3b` (check `df -h` first).

Time per model, all three stages (114 model calls or episodes): roughly 1-2 h for 3B and 4-8 h for 7-8B
on 2 CPUs. Two days fits about three models. Running Ollama natively on the Mac (GPU) is several
times faster: set `OLLAMA=http://<mac-ip>:11434` before every c1.sh command, and say so in the freeze.

## Steps

0. Mac Terminal, leave open: `caffeinate -dimsu`.
1. Install: copy `gne_core_c1.zip` from `/media/sf_AI-Lab-Transfer`, check its SHA-256 against the value
   given with the download, `unzip -q gne_core_c1.zip`.
2. Check: `bash gne_core_c1/c1.sh check`. Pass: `Ran 18 tests` then `OK`, and your models are listed.
3. Freeze, naming the models in the order you will run them:
   `bash gne_core_c1/c1.sh freeze qwen2.5:3b qwen2.5:7b llama3.1:8b`
4. Run one model: `bash gne_core_c1/c1.sh run qwen2.5:3b` (controls, then probe, then main).
   Watch the controls: if most control episodes end in `interface_failure`, the model cannot use
   the tools; stop that model (it is still reported) and go to the next.
   If interrupted: `bash gne_core_c1/c1.sh resume <batch folder> <model>`; never start a second batch.
5. Analyse at any point: `bash gne_core_c1/c1.sh analyze`. Incomplete main batches print INTERIM.
6. Read each model's result with PREREGISTRATION.md section 4, in order: controls, R1 instrument,
   R2 ceiling, then the reading. Report every model started.
