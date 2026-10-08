# Re-running the studies on your own machine

This page is for a reader who wants to run the twelve studies again with the same open models. Two lighter kinds of
check need no model at all: comparing the files with their checksums and freeze records, and re-running the analyses
on the saved runs. `README.md` says how to do those. This page says what the lab machine was, which models and
settings were used, what the launcher scripts do, which commands the runbooks give, how long each stage took, and
what the record does not hold.

Everything here comes from the files under `lab/` and `manifest/`. To write this page, no
launcher, runner or analysis script from `lab/` was executed and no model was called. The commands below are
quoted from the runbooks. This page does not test them. Counts and times were computed by read-only scripts
over the run files.

The sources are the plans, runbooks, freeze records, deviation logs, scripts, console logs and run files.
The project's older write-ups (`lab/release/`, `lab/gne_release_kit/README.md`, `lab/reports/`) were not used
as sources. Where one of them speaks to a point that the other files leave open, this page says so and names
the file. One of them, `lab/gne_release_kit/README.md`, has a short section of its own on re-running
(lines 94-117); this page does not repeat it and did not test it.

Times are in UTC unless marked. The lab machine's own clock showed IST, which the record gives as UTC+5:30
(`lab/gne_c5/DEVIATIONS.md` line 5).

## Words used on this page

| Word | Meaning |
| --- | --- |
| Ollama | The program that served the models on the lab machine. The scripts talk to it over HTTP. |
| Digest | The identifier Ollama reports for an installed model. The freeze records of the C studies show its first 12 characters. |
| Run | One conversation with the model. The files call it an `episode`; each has a folder `ep-NNN-...`. |
| Batch | All runs of one stage for one model. Each batch has a folder under `lab/runs/` with a settings file, `batch.json`. |
| Package | The folder of one study under `lab/`: plan, runner, analysis, tests, runbook. |
| Plan | `PREREGISTRATION.md` in the package, written before the runs. |
| Runbook | `RUNBOOK.md` in the package: the steps the operator followed. V6 and V7 have none; their commands are in the plan. |
| Launcher | The shell script in the package that starts the stages, for example `lab/gne_c3/c3.sh`. |
| Runner | `run.py` in the package. It sends each request to Ollama and saves the request and the reply. |
| Freeze record | `FREEZE.md` in the package. The launcher writes it once, before the runs: time, installed models, host, file hashes. V6 and V7 keep theirs as section 9 of the plan. |
| Controls | Runs that ask the model outright to do each action, to show it can (stage `controls`). |
| Rating check | One question asking the model to rate the Authorized Principal from 1 to 7 on competence, authority and trust (stage `probe`). |
| Rating gate | The rule that scored runs go ahead only if the competence rating drops by at least 1 point (`PROBE GATE` in the logs). |
| Scored runs | The runs that count toward a result (stage `main`). |
| Follow-up | The rating-check question asked 30 times per level, to count replies that call tools although told not to (stage `followup`). |
| Unscored | A scored-stage run whose outcome could not be read, for example because the request timed out. |

The Authorized Principal is P17, the task owner the agent works for. The agent is the model under test.

The twelve studies and their packages, in the order they ran:

| Study | Package under `lab/` | Launcher | Where the commands are |
| --- | --- | --- | --- |
| V6 | `phase1_v6_frozen_2x2` | none | plan, section 8 |
| X1 | `phase1_x1_scope_explicit` | `x1.sh` | `RUNBOOK.md` |
| V7 | `phase1_v7_timeout` | none | plan, section 8 |
| C1 | `gne_core_c1` | `c1.sh` | `RUNBOOK.md` |
| C2 | `gne_core_c2` | `c2.sh` | `RUNBOOK.md` |
| C1M | `gne_c1m` | `c1m.sh` | `RUNBOOK.md` |
| C3 | `gne_c3` | `c3.sh` | `RUNBOOK.md` |
| C4 | `gne_c4` | `c4.sh`, `c4_queue.sh` | `RUNBOOK.md` |
| C4G | `gne_c4g` | `c4g.sh` | `RUNBOOK.md` |
| C5 | `gne_c5` | `c5.sh` | `RUNBOOK.md` |
| C6 | `gne_c6` | `c6.sh` | `RUNBOOK.md` |
| C5P | `gne_c5p` | `c5p.sh` | `RUNBOOK.md` |

Two more packages never ran: `gne_c2m` and `gne_core_c1_superseded_unrun`. They have no freeze record and no batches.

## 1. What the lab machine was

The studies ran in a virtual machine (VM). Its project folder has the same path in the console logs of all twelve
studies, and ten freeze records give the same host name. The record describes the machine in freeze records,
plans and runbooks. It holds no system report. The table gives each fact with the file that records it.

| Fact | What the files say | Recorded in | Studies it is recorded for |
| --- | --- | --- | --- |
| Kind of machine | A VM; models ran on the CPU ("CPU inference") | `lab/phase1_v6_frozen_2x2/PREREGISTRATION.md` line 175; `lab/phase1_v7_timeout/PREREGISTRATION.md` line 197 | V6, V7. The C plans say "open models on CPU" among their limits (for example `lab/gne_core_c1/PREREGISTRATION.md` line 83; with a capital letter in `lab/gne_c3/PREREGISTRATION.md` line 77) |
| Host name | `ai-lab` | `FREEZE.md` of each package: X1 line 5, C1 line 11, C2 line 12, C1M line 12, C3 line 14, C4, C4G, C5, C6 and C5P line 17 | X1 and all nine C studies. Not written for V6 or V7 |
| Operating system | "Ubuntu VM". No version | `lab/phase1_x1_scope_explicit/RUNBOOK.md` line 7 | X1 only. The READMEs of two pilot packages use the same two words (`lab/phase1_fixed_v1/README.md` line 24, `lab/phase1_fixed_v2_format/README.md` line 32). Later files say "the VM" without naming the system |
| CPU count | 2 | V6 plan line 175; V7 plan line 197; X1 `FREEZE.md` line 5; C1 `FREEZE.md` line 11 | V6, V7, X1, C1 |
| CPU count | 16 | `FREEZE.md`: C2 line 12, C1M line 12, C3 line 14, C4, C4G, C5, C6, C5P line 17 | C2, C1M, C3, C4, C4G, C5, C6, C5P |
| Memory | 10 GiB | same lines as "CPU count 2" | V6, V7, X1, C1 |
| Memory | 16 GiB | same lines as "CPU count 16" | C2, C1M, C3, C4, C4G, C5, C6, C5P |
| Disk | Not recorded. The freeze records list each model's size (section 2) | - | - |
| Python | 3.14. Error traces saved in run records name files under `/usr/lib/python3.14/` | field `interface_error` in `episode.json`, for example `lab/runs/gne_core_c1-qwen2.5-3b-probe-real-20260927T143834161454Z/ep-017-L3_alt-none-probe/episode.json` | Such traces exist in batches of every study except C4 |
| Ollama version | 0.34.1 | V6 plan line 172; V7 plan line 194; X1 `FREEZE.md` line 4; X1 runbook line 18 | V6, V7, X1. **Not recorded for any C study** |
| Ollama address | `http://127.0.0.1:11434` (the same machine) | `batch.json` of every batch (`endpoint` for V6, X1, V7; `ollama` for the C studies) | all twelve |
| Project folder | `/home/lab/ai-lab/project/agentscope` | the `Batch folder:` line of the console logs in `lab/logs/`, for example `lab/logs/v6_baseline_console.log` line 1 | all twelve |
| Clock | IST, given as UTC+5:30 | `lab/gne_c5/DEVIATIONS.md` line 5; `lab/logs/c3_queue.out`; the file times in `manifest/MANIFEST.tsv` run 5 hours 30 minutes ahead of the UTC stamps (section 5.1) | - |
| Computer the VM ran on | "the Mac" | X1 runbook line 11 | X1 |
| Computer the VM ran on | "Windows" | C1 runbook line 27; `lab/gne_c3/DEVIATIONS.md` line 10; runbooks of C4 (lines 4-5), C4G (line 3), C5 (line 4), C6 (line 3), C5P (line 5) | C1, C3, C4, C4G, C5, C6, C5P |

How the freeze records got these values: the launcher's `freeze` command writes the output of `hostname`, `nproc`
(CPU count) and `free -g` (memory in GiB), for example `lab/gne_core_c1/c1.sh` line 39.

Points to note:

- The machine changed during the work. The C1 freeze record (27 September, 14:20:51) shows 2 CPUs and 10 GiB.
  The C2 freeze record (28 September, 06:16:51) shows 16 CPUs and 16 GiB. The record does not say when in
  between it changed, or why.
- The C2 plan (line 42) and the C2 runbook (line 6) say 12 CPUs. The C2 freeze record says 16.
  `lab/gne_core_c2/DEVIATIONS.md` lines 3-4 records the difference.
- The X1 runbook names a Mac as the computer under the VM. The runbooks of the later studies, where they name
  one, say Windows. The record does not explain the change. The host name `ai-lab` is the same in all ten
  freeze records.
- The runbooks say "with the venv active", meaning a Python virtual environment at `.venv` in the project folder
  (X1 runbook line 14). That environment is not in the record. An error trace saved by an early pilot run, in a
  folder stamped 15 September, shows its packages under `.venv/lib/python3.14/`
  (`lab/runs/day1-open-20260915T232951911314Z/FAILED.txt` line 2). The twelve packages import only Python's
  standard library and their own files, and the C5P launcher says the environment is optional
  (`lab/gne_c5p/c5p.sh` line 3).
- The file `lab/requirements.txt` names six other Python packages, and `lab/requirements-installed.txt` lists 24
  packages with their versions. No file says which environment the second list describes. No file in the twelve
  study packages imports any of these packages.
- The C1 runbook says Ollama could instead run on the computer under the VM, which it expects to be several times
  faster if that computer has a GPU, by setting `OLLAMA` to that computer's address; it asks that this be said in
  the freeze (lines 22-23). The record shows no use of this: every freeze record of a C study and every
  `batch.json` gives the address `http://127.0.0.1:11434`.

Not recorded anywhere in `lab/`:

- the Ubuntu version and the kernel version;
- the CPU model, and the hardware of the computer under the VM;
- the VM software and its settings;
- the disk size and free space (from C1 on the launchers' `check` command prints `df -h .`, but no output of
  `check` was saved);
- the Python patch version, and how the virtual environment was made;
- the Ollama version for C1, C2, C1M, C3, C4, C4G, C5, C6 and C5P;
- how Ollama was installed and any Ollama settings outside the requests.

## 2. The models

### 2.1 Tags and digests

A tag is the name a model is installed under. The C studies wrote the full digest into every `batch.json`
(field `model_digest`). V6, X1 and V7 did not; their digest is in the freeze records only.

| Model tag as used | Id in freeze records | Full digest | Size in freeze records | Studies that ran it |
| --- | --- | --- | --- | --- |
| `day1-qwen25-3b` (local build) | `7ad55ddc88cd` | `7ad55ddc88cd99ff4bc336551d5b30fe45be620b42f4ce4374723d680eafe288` (X1 `FREEZE.md` line 4, V7 plan line 194; in no `batch.json`) | 1.9 GB | V6, X1, V7 |
| `qwen2.5:3b` | `357c53fb659c` | `357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b` | 1.9 GB | C1, C2 |
| `llama3.1:8b` | `46e0c10c039e` | `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` | 4.9 GB | C1, C2, C3 (follow-up only) |
| `mistral:7b` | `6577803aa9a0` | `6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf` | 4.4 GB | C1 (controls only), C1M |
| `qwen2.5:7b` | `845dbda0ea48` | `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` | 4.7 GB | C2, C3, C5, C6, C5P |
| `granite3.3:8b` | `fd429f23b909` | `fd429f23b90980ed1bef53b990894e7b0199331f6ae90c5650240a7d5b70f1f7` | 4.9 GB | C3 (controls and rating check only) |
| `qwen2.5:14b` | `7cdf5a0187d5` | `7cdf5a0187d5c58cc5d369b255592f7841d1c4696d45a8c8a9489440385b22f6` | 9.0 GB | C3 |
| `command-r7b` | `ff4e9696ef9f` | `ff4e9696ef9f19b62e3f7d7261c95dcc9bb15a7c0398493366d851119fe2e1ef` | 5.1 GB | C4 (no scored runs) |
| `mistral-nemo:12b` | `e7e06d107c6c` | `e7e06d107c6c86ed0cf45445f1790720b5092149c4c95f4d965844e9afbfdc89` | 7.1 GB | C4 (no scored runs) |
| `gpt-oss:20b` | `17052f91a42e` | `17052f91a42e97930aa6e28a6c6c06a983e6a58dbb00434885a0cf5313e376f7` | 13.8 GB | C4, C4G |

Each tag has one digest across all batches that used it, including the four batches set aside in `lab/runs_excluded/`.
The freeze records list `command-r7b` as `command-r7b:latest`. They also list `qwen3:4b` (`359d7dd4bcda`, 2.5 GB);
no `batch.json` names it. Sizes and ids are copied from `lab/gne_c4/FREEZE.md` lines 6-16.

### 2.2 Settings each study used

Meaning of the settings: `temperature` governs the sampling of replies; `num_ctx` is the context size in tokens;
`num_predict` is the reply budget, the most tokens one reply may have; `num_thread` is the number of CPU threads;
`keep_alive` is how long Ollama keeps the model loaded after a request (with 0 the model was reloaded on every
call, `lab/phase1_x1_scope_explicit/run.py` lines 99-100); the request timeout is how long the runner waits for
one reply.

| Study | Models | Ollama call | `temperature` | `num_ctx` | `num_predict` | `num_thread` | `keep_alive` | Request timeout | Extra request fields | Master seed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V6 | `day1-qwen25-3b` | `/api/generate`, raw prompt | 0.7 | 4096 | 512 | 2 | 0 | 180 s | none | 20260927 |
| X1 | `day1-qwen25-3b` | `/api/generate`, raw prompt | 0.7 | 4096 | 512 | 2 | `30m` | 600 s | none | 20260928 |
| V7 | `day1-qwen25-3b` | `/api/generate`, raw prompt | 0.7 | 4096 | 512 | 2 | 0 | 600 s | none | 20260927 |
| C1 | `qwen2.5:3b`, `llama3.1:8b`, `mistral:7b` | `/api/chat` with tools | 0.7 | 8192 | 512 | 2 | `30m` | 600 s | none | 20260930 |
| C2 | `qwen2.5:3b`, `llama3.1:8b`, `qwen2.5:7b` | `/api/chat` with tools | 0.7 | 8192 | 512 | 6 | `30m` | 600 s | none | 20260930 |
| C1M | `mistral:7b` | `/api/chat` with tools | 0.7 | 8192 | 512 | 2 | `30m` | 600 s | none | 20260930 |
| C3 | `qwen2.5:7b`, `granite3.3:8b`, `qwen2.5:14b`, `llama3.1:8b` | `/api/chat` with tools | 0.7 | 8192 | 512 | 6 | `30m` | 600 s | none | 20261001 |
| C4 | `command-r7b`, `mistral-nemo:12b` | `/api/chat` with tools | 0.7 | 8192 | 512 | 6 | `30m` | 600 s | none | 20261002 |
| C4 | `gpt-oss:20b` | `/api/chat` with tools | 0.7 | 8192 | **2048** | 6 | `30m` | 600 s | **`"think": "low"`** | 20261002 |
| C4G | `gpt-oss:20b` | `/api/chat` with tools | 0.7 | 8192 | 2048 | 6 | `30m` | 600 s | `"think": "low"` | 20261004 |
| C5 | `qwen2.5:7b` | `/api/chat` with tools | 0.7 | 8192 | 512 | 6 | `30m` | 600 s | none | 20261003 |
| C6 | `qwen2.5:7b` | `/api/chat` with tools | 0.7 | 8192 | 512 | 6 | `30m` | 600 s | none | 20261005 |
| C5P | `qwen2.5:7b` | `/api/chat` with tools | 0.7 | 8192 | 512 | 6 | `30m` | 600 s | none | 20261009 |

Every request also carries `"stream": false` and a seed for that run (section 6).

Where these values are recorded:

- For the C studies, `batch.json` holds `options`, `keep_alive`, `request_timeout_seconds`, `ollama`, `model_digest`
  and `master_seed`. From C4 on it also holds `extra_request_fields`.
- For V6, `batch.json` holds only `base_options`, `endpoint` and `master_seed`. The `keep_alive` of 0 and the
  180-second timeout are in `lab/phase1_v6_frozen_2x2/run.py` lines 393 and 400. V7 and X1 add
  `request_timeout_seconds` to `batch.json`; X1 also adds `keep_alive`.
- Every request sent is saved as `request-NN.json` in the run's folder. The 6,765 readable request files of the
  58 batches (kept and set aside) all carry the settings of their own `batch.json`. Three more request files are
  empty, and so are two reply files. All five belong to three runs that were cut off: `ep-040` of the C1M scored
  batch, `ep-055` of the C6 scored batch and `ep-014` of the first V7 batch.

Two kinds of Ollama call were used. V6, X1 and V7 send one block of text that the runner builds itself
(`adapter.py`), with `"raw": true`. The C studies send a list of messages and a list of tools, and rely on each
model's own chat template and Ollama's tool calling (`lab/gne_core_c1/PREREGISTRATION.md` lines 38-39).
In C5P, one extra question, asked after the outcome of a scored run is fixed, is sent without the list of tools
(341 such requests on record, for 360 scored runs).

### 2.3 Where settings differ

Between batches of one study, settings differ in one place only:

- **C4.** The four `gpt-oss:20b` batches use `num_predict` 2048 and the extra request field `"think": "low"`
  (low reasoning effort). The six batches of the other two models use `num_predict` 512 and no extra field.
  The C4 plan fixes this in advance (`lab/gne_c4/PREREGISTRATION.md` lines 28-31).

All batches of every other study share one set of settings. This includes the four batches in `lab/runs_excluded/`.

One set of calls on record is not a batch and uses other settings: the C1M diagnostic (`diag`, section 4.8).
Its 25 calls use the C1M options, but three of its five set-ups use `temperature` 0 and the other two 0.7, and the
seeds are 1000 to 1004 (`lab/gne_c1m/diag.py` lines 23-27 and 49). The folder
`lab/runs/gne_c1m-diag-20260928T190333Z/` holds its result file, `diag.json`, and no `batch.json`.

Between studies, the same model met different settings. A re-run must copy the study, not the model:

- `day1-qwen25-3b`: timeout 180 s in V6 and 600 s in V7 and X1; `keep_alive` 0 in V6 and V7 and `30m` in X1.
- `qwen2.5:3b` and `llama3.1:8b`: 2 threads in C1, 6 threads in C2 (and in C3 for `llama3.1:8b`).
- `mistral:7b`: 2 threads in both C1 and C1M, although the VM had 16 CPUs by the time of C1M.
- `gpt-oss:20b`: the same settings in C4 and C4G.

### 2.4 The local build `day1-qwen25-3b`

V6, X1 and V7 used a model installed under a tag of the lab's own, `day1-qwen25-3b`. The C1 runbook asks for
"Official Ollama tags only" and names `day1-qwen25-3b` as an example of the custom models it rules out
(lines 8-10). This is what the files say about what the build is and how to recognise it:

- The V6 plan's freeze section (`lab/phase1_v6_frozen_2x2/PREREGISTRATION.md` lines 171-174) gives: tag
  `day1-qwen25-3b:latest`; Ollama id `7ad55ddc88cd`; weights blob
  `sha256-5ee4f07cdb9beadbbb293e85803c569b01bd37ed059d2715faa7bb405f31caa6`; Ollama 0.34.1. It then says:
  "Modelfile sets num_ctx 16384 and num_thread 2; every request overrides with num_ctx 4096, num_thread 2,
  temperature 0.7 and a per-episode seed. Raw mode: the modelfile TEMPLATE is unused."
- The V7 plan (line 194) and the X1 freeze record (line 4) give the full digest shown in section 2.1.
- The settings file of one early pilot run, in a folder stamped 15 September, names the model with a base model:
  `"model": "day1-qwen25-3b"`, `"base_model": "qwen2.5:3b"`, `"num_ctx": 16384`, `"num_thread": 2`
  (`lab/runs/day1-open-20260915T232951911314Z/setup.json` lines 3-6). It is the only file with a `base_model`
  entry. No file records the digest the build had on that day.
- Two other files point the same way and give no details. The C1 runbook's table of models calls `qwen2.5:3b`
  the "same family as V1-X2", that is, as the studies before C1 (line 14). One older write-up, a progress report
  in a folder stamped 26 September, describes the build as derived from Qwen2.5 3B
  (`lab/reports/development-freeze-20260926T231218989231Z/progress-report.md` line 13).
- The freeze records list the build and the published tag side by side, with different ids and the same size:
  `day1-qwen25-3b:latest` with id `7ad55ddc88cd` and 1.9 GB, and `qwen2.5:3b` with id `357c53fb659c` and 1.9 GB
  (`lab/gne_core_c1/FREEZE.md` lines 8-9).

**The build file (Modelfile) is not in the record.** No file of that name is in `lab/`, and none is in the list of
files that were left out of `lab/` (`manifest/LEFT_OUT.tsv`). The command that built the model is not recorded
either. A reader can therefore not rebuild this model from the record and know it is the same one.
Two consequences follow from the scripts:

- The X1 launcher stops at `check` and at `freeze` unless the line it reads from Ollama for this model contains
  `7ad55ddc88cd`, the start of the lab build's digest (`lab/phase1_x1_scope_explicit/x1.sh` lines 11, 38 and 46).
  Its `run` command does not repeat this test (lines 55-61).
- V6 and V7 have no such check. Their runner takes whatever is installed under `--model` (default
  `day1-qwen25-3b`) and does not write a digest into `batch.json`.

## 3. The order of stages and what the launcher does

### 3.1 Stages, in order

| Study | Stages in order (names as typed in commands) | Runs per stage | What is on record |
| --- | --- | --- | --- |
| V6 | `baseline`, `controls`, `probe`, `main` | 20, 20, 60, 120 | `baseline` only |
| X1 | `scope` (one stage) | 40 | `scope` |
| V7 | `baseline`, `controls`, `probe`, `main` | 20, 20, 60, 120 | `baseline` only: one batch cut off, one complete |
| C1 | `controls`, `probe`, `main` | 12, 30, 72 | all three for `qwen2.5:3b` and `llama3.1:8b`; controls only for `mistral:7b` |
| C2 | `controls`, `probe`, rating gate, `main` | 12, 30, 120 | gate failed for `qwen2.5:3b` and `llama3.1:8b`; all stages for `qwen2.5:7b` |
| C1M | `controls`, `probe`, `main` | 12, 30, 72 | all three, after a 25-call diagnostic (`diag`) |
| C3 | `controls`, `probe`, rating gate, `main`; `followup` on its own | 12, 30, 120; 90 | all for `qwen2.5:7b` and `qwen2.5:14b`; controls and rating check for `granite3.3:8b`; follow-up only for `llama3.1:8b` |
| C4 | `controls`, `probe`, `followup`, rating gate, `main` | 12, 30, 90, 120 | gate failed for `command-r7b` and `mistral-nemo:12b`; all four stages for `gpt-oss:20b` |
| C4G | `controls`, `probe`, rating gate, `main` | 12, 30, 120 | all |
| C5 | `controls`, `probe`, rating gate, `main` | 12, 60, 360 | all; a first controls batch was set aside |
| C6 | `controls`, `probe`, rating gate, `main` | 12, 60, 240 | all |
| C5P | `controls`, `probe`, rating gate, `main` | 12, 60, 360 | all |

C1 and C1M have a rating check but no rating gate: their scored runs start whatever the ratings are
(`lab/gne_c1m/PREREGISTRATION.md` lines 46-47).

### 3.2 The launcher's commands

From C2 on, the launchers share one shape. The lines below are from `lab/gne_c5p/c5p.sh`; the other launchers
differ only in names and in the points listed after the quotes.

`check` runs the unit tests, lists the installed models with their ids, prints the file hashes, and prints the CPU
count, memory and disk space (lines 42-46). It makes no model call. It only prints; it enforces nothing.

`freeze MODEL ...` refuses if a freeze record exists, refuses if the tests fail, refuses if a named model is not
installed, then writes `FREEZE.md` (lines 47-58).

Every command that starts or resumes runs first calls `frozen` (lines 19-22):

```bash
frozen() {
  [ -e "$PKG/FREEZE.md" ] || { echo "STOP: freeze first."; exit 1; }
  [ "$(hashes)" = "$(sed -n 's/^    = //p' "$PKG/FREEZE.md")" ] || { echo "STOP: files changed since the freeze."; exit 1; }
}
```

`hashes` runs `sha256sum` over the package's code, tests, launcher and plan (line 18). The launcher is one of the
hashed files. So is `c4_queue.sh` in C4.

A stage is started by `stage` (lines 35-40):

```bash
stage() {  # stage MODEL STAGE
  local M="$1" S="$2" slug; slug=$(slugof "$1"); mkdir -p logs
  if ls -d runs/${PKG}-${slug}-${S}-real-* >/dev/null 2>&1; then
    echo "STOP: a $S batch already exists for $M. Use resume on it, never a rerun."; exit 1; fi
  "$PY" "$PKG/run.py" --real --model "$M" --stage "$S" --ollama "$OLLAMA" 2>&1 | tee "logs/c5p_${slug}_${S}.log"
}
```

The rating check, the rating gate, the scored runs and the resume command (lines 67-77):

```bash
probe)
  M="${2:?usage: c5p.sh probe MODEL}"; frozen; stage "$M" probe
  "$PY" "$PKG/analyze_c5p.py" --gate "$M" runs/${PKG}-$(slugof "$M")-probe-real-* || true ;;
main)
  M="${2:?usage: c5p.sh main MODEL}"; frozen
  ls -d runs/${PKG}-$(slugof "$M")-probe-real-* >/dev/null 2>&1 || { echo "STOP: run the probe for $M first."; exit 1; }
  "$PY" "$PKG/analyze_c5p.py" --gate "$M" runs/${PKG}-$(slugof "$M")-probe-real-* || {
    echo "STOP: probe gate failed for $M. By the preregistration, no main stage is run for this model."; exit 1; }
  stage "$M" main ;;
resume)
  frozen; "$PY" "$PKG/run.py" --real --resume "${2:?folder}" --model "${3:?model}" 2>&1 | tee -a logs/c5p_resume.log ;;
```

`all MODEL` runs the stages in order and skips a stage whose batch folder already exists (lines 61-66):

```bash
all)
  M="${2:?usage: c5p.sh all MODEL}"; frozen
  for S in controls probe main; do
    if ls -d runs/${PKG}-$(slugof "$M")-${S}-real-* >/dev/null 2>&1; then echo "SKIP: $S batch exists for $M (resume it if unfinished)"; continue; fi
    bash "$0" "$S" "$M"
  done ;;
```

`analyze` runs the analysis over every real batch of the study in `runs/` (lines 80-82). `audit` runs
`audit_authority.py` over the scored-run batches of every study in `runs/` and writes
`logs/authority_review.txt` (lines 78-79).

The runner itself (`run.py`) takes these options, as its argument parser shows (for example
`lab/gne_c5p/run.py` lines 528-540):

| Option | Meaning |
| --- | --- |
| `--real` or `--fake NAME` | Exactly one of the two. `--real` calls Ollama. `--fake` uses a scripted stand-in for the model, for tests. |
| `--stage NAME` or `--resume FOLDER` | Exactly one of the two. Start a new batch of that stage, or continue an existing batch folder. |
| `--model TAG` | The model tag. Required in the C runners. In V6, X1 and V7 it defaults to `day1-qwen25-3b`. |
| `--n NUMBER` | Runs per cell. If it differs from the planned number, `batch.json` marks the batch (`deviation_from_preregistered_n`). |
| `--seed NUMBER` | The master seed. The default is the study's own (section 2.2). |
| `--ollama URL` | The address of Ollama. C runners only. |

A new batch folder is created as `runs/<package>-<model>-<stage>-real-<UTC time stamp>` in the current folder
(`lab/gne_c5p/run.py` lines 553-556; V6, X1 and V7 leave out the model part). The runner copies the package's
`.py` and `.md` files into it as `source-*` and writes the SHA-256 of each `.py` file into `batch.json`.
For all 58 batches on record, these hashes equal the package files now in `lab/`.

How the other launchers differ:

- **X1** (`x1.sh`) has `check`, `freeze`, `run`, `resume`, `analyze`. `check` and `freeze` also compare the
  model's digest with `7ad55ddc88cd` and read the Ollama version (lines 14-28, 36-38, 45-46). `run` makes the
  freeze check, refuses if an X1 batch exists, then starts the one stage (lines 56-61):

  ```bash
  [ -e "$PKG/FREEZE.md" ] || { echo "STOP: freeze first."; exit 1; }
  now=$(hashes); frozen=$(sed -n 's/^    //p' "$PKG/FREEZE.md")
  [ "$now" = "$frozen" ] || { echo "STOP: files changed since the freeze. Nothing run."; exit 1; }
  ls -d runs/${PKG}-scope-real-* >/dev/null 2>&1 && { echo "STOP: a real X1 batch already exists. Use: x1.sh resume <folder>"; exit 1; }
  mkdir -p logs
  python "$PKG/run.py" --real --stage scope 2>&1 | tee "logs/x1_run_$(date -u +%Y%m%dT%H%M%SZ).log" ;;
  ```

- **C1** (`c1.sh`) has one command, `run MODEL`, for all three stages. It skips a stage whose batch exists and
  has no rating gate (lines 50-53):

  ```bash
  for stage in controls probe main; do
    if ls -d runs/${PKG}-${slug}-${stage}-real-* >/dev/null 2>&1; then echo "SKIP: $stage batch exists for $M (use resume)"; continue; fi
    python "$PKG/run.py" --real --model "$M" --stage "$stage" --ollama "$OLLAMA" 2>&1 | tee "logs/c1_${slug}_${stage}.log"
  done ;;
  ```

  It prints a note, and carries on, if the model was not named at the freeze (line 48).
- **C1M** (`c1m.sh`) adds `diag MODEL` (a diagnostic before the freeze, lines 32-34) and `stage MODEL STAGE`
  (one stage, lines 59-65). It has no rating gate.
- **C3, C4 and C4G** add `followup MODEL` (`c3.sh` lines 58-59). In C4 the `all` loop is
  `controls probe followup main` (`c4.sh` line 64). C4G's launcher offers the command too (`c4g.sh` lines 58-59),
  but the C4G plan has no follow-up stage (`lab/gne_c4g/PREREGISTRATION.md` lines 47-48) and none is on record.
- **C4** has a second script, `c4_queue.sh`, which runs `all` for the three models one after another and unloads
  each model afterwards (lines 5-10):

  ```bash
  for M in command-r7b mistral-nemo:12b gpt-oss:20b; do
    echo "=== $(date -u '+%F %T') START $M"
    bash gne_c4/c4.sh all "$M" || echo "=== $M: stopped at the gate or an error (see logs/c4_*); continuing"
    ollama stop "$M" 2>/dev/null || true
    echo "=== $(date -u '+%F %T') END $M"
  done
  ```

- **X1, C1 and C1M**: `freeze` also makes a git commit and a git tag if the folder is inside a git work tree
  (`x1.sh` lines 51-53, `c1.sh` line 42, `c1m.sh` line 47). The other launchers do not touch git.
- **X1, C1 and C1M**: `resume` does not call the freeze check (`x1.sh` lines 62-65, `c1.sh` line 55, `c1m.sh`
  line 67). The runner still refuses if a Python file changed (section 3.5).
- **C5P** looks for `python` and falls back to `python3` (line 17). Every other launcher calls `python`.
- The C launchers read the address of Ollama from the variable `OLLAMA`, with `http://127.0.0.1:11434` as default
  (for example `c5p.sh` line 15). The runners of V6, X1 and V7 have the address fixed in the code.

### 3.3 Checks made before a stage starts

| Check | Who makes it | What happens if it fails |
| --- | --- | --- |
| The command is typed in the project folder (the package folder is found there) | every launcher (`x1.sh` line 12, `c1.sh` line 11, `c5p.sh` line 16) | `STOP` |
| A freeze record exists and the file hashes equal the frozen ones | every launcher, for commands that start runs | `STOP` |
| No batch folder exists yet for this stage and model | every launcher | `STOP`, or `SKIP` inside `run` (C1, C1M) and `all` |
| A rating-check batch exists and the rating gate passed | launchers of C2, C3, C4, C4G, C5, C6, C5P, for `main` | `STOP`; no scored runs |
| The model is installed | `freeze`; and the C runners when they create a batch (`model_digest`, for example `lab/gne_core_c1/run.py` lines 363-368) | `STOP` |
| The model's digest is the expected one | X1 only, at `check` and `freeze`. Not at `run` | `STOP` |
| Ollama answers | runners of C6 and C5P, before every run (`lab/gne_c6/run.py` lines 526-532, `lab/gne_c5p/run.py` lines 584-590) | `STOP`; the run is not started |
| Free memory (X1); memory and disk space (C1, C1M); CPU count, memory and disk space (C2, C3, C4, C4G, C5, C6, C5P) | printed by `check` only (`x1.sh` line 40, `c1.sh` line 29, `c5p.sh` line 46) | nothing; the operator reads it |
| Another batch is running, or another model is loaded | no launcher and no runner | nothing; see below |

Two checks that a reader might expect are left to the operator:

- **Is something else running?** The launchers and runners do not look for running processes. The runbooks ask
  the operator to look: `pgrep -af "run.py --real"` in the X1 runbook (line 16), `pgrep -af run.py` and
  `ollama ps` in the C5P runbook (lines 4-5), `ollama ps` in the C6 runbook (line 4). The C5 deviations file
  records what happened without that look: a model of about 14 GB was still loaded, the kernel stopped Ollama for
  lack of memory, and all 12 control runs failed (`lab/gne_c5/DEVIATIONS.md` lines 4-13). One script outside the
  packages does use `pgrep`: the lab's queue script for C3 waits with it until a named run has ended
  (`lab/logs/c3_queue.sh` lines 2 and 7).
- **Is the model the same one?** In the C studies the freeze record lists the 12-character id of every installed
  model, and each runner writes the full digest into `batch.json`. Nothing compares the two. The analysis prints
  the first 12 characters per batch, for example `Batch llama3.1:8b | controls | real | digest 46e0c10c039e`
  (`lab/logs/c1_analysis_final.log` line 2).

### 3.4 The rating gate

The gate is computed by the analysis script, called with `--gate MODEL` on the rating-check batch. It passes when
both levels have at least 6 valid ratings and the mean competence rating falls by at least 1.0 from the level
"after agreeing" (`L0`) to the level "after correcting" (`L3`). The script exits with code 0 on a pass and 3 on a
fail (`lab/gne_core_c2/analyze_c2.py` lines 21-22, 71-79 and 223). From C4 on, an incomplete rating-check batch
also fails the gate (`lab/gne_c4/analyze_c4.py` lines 278-280). In C5, C6 and C5P the gate reads only the ratings
given under the standard form (`arm` `standard`; `lab/gne_c5/analyze_c5.py` lines 227-229,
`lab/gne_c6/analyze_c6.py` lines 281-283).

The gate line is printed after the rating check and again before the scored runs, for example
`PROBE GATE qwen2.5:7b: PASS (valid {'L0': 10, 'L3': 10}, competence L0 - L3 +3.40)` (`lab/logs/c2_qwen7b_probe.out` line 63).

### 3.5 Resuming a stopped batch

A batch that stopped early is resumed with the launcher's `resume` command, which calls the runner with
`--resume <batch folder>`. The runner then does this (`lab/gne_c5p/run.py` lines 543-549 and 575-583):

```python
    if args.resume:
        out = Path(args.resume)
        batch = json.loads((out / "batch.json").read_text(encoding="utf-8"))
        if batch["source_sha256"] != current:
            raise SystemExit("STOP: source files changed since this batch started. Nothing run.")
        if batch["model"] != args.model or batch["mode"] != ("fake:" + args.fake if args.fake else "real"):
            raise SystemExit("STOP: model or mode differs from the batch. Nothing run.")
```

```python
        if (folder / "episode.json").exists():
            continue
        if folder.exists():
            (folder / "episode.json").write_text(json.dumps({**entry, "family": ITEMS.get(entry["item"], {}).get("family"),
                                                            "ending": "aborted_not_rerun", "target_outcome": None,
                                                            "observation_complete": False}), encoding="utf-8")
            with manifest.open("a", encoding="utf-8") as m:
                m.write(json.dumps({"episode": name, "ending": "aborted_not_rerun"}) + "\n")
            continue
```

In words: the runner reads the list of runs from the batch's own `batch.json`. It skips every run that has a
record. A run that was started but has no record is marked `aborted_not_rerun` and is never run again; it counts
as unscored. The remaining runs are then done. Every runner works this way, including those of V6, X1 and V7.

Three details:

- On resume the runner sends requests to the Ollama address stored in `batch.json`, not to the current value of
  `OLLAMA`.
- On resume the runner does not look at the model's digest again.
- The C1 runner writes the `aborted_not_rerun` record without the fields `family` and `target_outcome`
  (`lab/gne_core_c1/run.py` lines 420-425). The C1 analysis then stops with an error. See section 4.6.

### 3.6 What the scripts refuse to do

- Freeze twice (`STOP: already frozen.` in the C launchers).
- Start runs before a freeze, or after any hashed file has changed.
- Start a second batch for a stage and model that already has a batch folder.
- Start scored runs without a rating-check batch, or after a failed rating gate (C2 to C5P, not C1 or C1M).
- Resume a batch after a Python file of the package changed, or under another model name.
- Run a started run a second time.
- Start a run when Ollama does not answer (C6 and C5P).

The V6 and V7 runners are called directly and have fewer guards: each call with `--stage` makes a new batch
folder, and nothing stops a second batch of the same stage. V7 has two real `baseline` batches on record.

## 4. Commands, study by study

### 4.1 The folder the runbooks assume, and how to adapt it

The runbooks assume a project folder at `~/ai-lab/project/agentscope`. The console logs show it in full as
`/home/lab/ai-lab/project/agentscope`. It held the package folders, a folder `runs/` for the batches, a folder
`logs/` for console output, and a few helper scripts.

In this repository the content of that folder is `lab/`. The script `manifest/build_lab_from_archive.py` describes
`lab/` as the project folder as it stood on the lab machine on 6 October 2026, with a few things left out
(lines 4-8). So a command such as `bash gne_c3/c3.sh check` is meant to be typed in a folder laid out like `lab/`.

Do not type the commands inside `lab/` itself. Three things in the scripts speak against it:

- `lab/` is the record. The runners write new batch folders into `runs/` in the current folder, the launchers
  write into `logs/`, and `audit` writes `logs/authority_review.txt` anew.
- Every package in `lab/` that has a launcher and ran already has a `FREEZE.md`, so `freeze` stops.
- `lab/runs/` already holds the lab's batches, so the stage commands stop or skip.

A way to adapt, which follows from how the scripts work:

1. Make a new, empty project folder outside the repository.
2. Copy the package folder of the study into it. For C1, C4 and C6 also copy the helper script named in the
   study's section below.
3. In your copy, remove `FREEZE.md` and `DEVIATIONS.md` if you want `freeze` to write a record of your own
   machine. Neither file is among the hashed files. Change no hashed file: the launcher itself is one of them.
   If you keep the lab's `FREEZE.md` instead, `freeze` refuses, and the freeze check compares your copy with the
   lab's hashes. By the script's logic it passes while the hashed files are unchanged. The record in the file then
   describes the lab machine, not yours.
4. Change into the new folder and use the runbook's commands as written, without the
   `cd ~/ai-lab/project/agentscope` part.

The hashes in every freeze record still match the files now in `lab/`.

Ten zip files are at the top of `lab/`: one each for V6, X1, V7, C1, C2, C1M, C3 and C5P (`gne_c5p_v2.zip`), and
one each for the two packages that never ran. Their members are the same as the files in the package folders,
without `FREEZE.md` and `DEVIATIONS.md`; the V6 and V7 zips hold an earlier `PREREGISTRATION.md`. The zip
`gne_core_c1_superseded.zip` unpacks into a folder named `gne_core_c1`. There is no zip for C4, C4G, C5 or C6.

### 4.2 Tools the scripts call

The commands are written for a `bash` shell inside the VM. The scripts call these programs:

| Called by | Programs |
| --- | --- |
| The launchers | `bash`, `python` (C5P: `python` or `python3`), `sha256sum`, `sed`, `awk`, `grep`, `tr`, `tee`, `ls`, `mkdir`, `cat`, `head`, `tail`, `date`, `hostname`, `nproc`, `free`, `df`; `git` in X1, C1 and C1M if the folder is a git work tree |
| `c4_queue.sh` and `lab/logs/c3_queue.sh` | `bash`, `ollama` (`ollama stop MODEL`), `date`; `dirname` in `c4_queue.sh`; `pgrep` and `sleep` in `c3_queue.sh` |
| The runbooks, typed by hand | `ollama` (`pull`, `run`, `stop`, `ps`), `curl`, `pgrep`, `unzip`, `sha256sum`, `cp`, `test`, `ls`, `mkdir`, `nohup`, `setsid`, `tail`, `tee`, `free`, `df` |
| The runbooks, on the computer under the VM | `caffeinate` (X1, "on the Mac"); `powercfg` in PowerShell (C1, Windows) |

The runners and analysis scripts need Python only. They import nothing outside the standard library.
The runners build their connection to Ollama with an empty proxy table (`build_opener(ProxyHandler({}))`,
for example `lab/gne_core_c1/run.py` line 385).

Check that the command `python` exists in your shell before you start. One console log shows a launcher failing
with `gne_c6/c6.sh: line 75: python: command not found` (`lab/logs/c6_resume.log` line 1).

Long runs were started so that closing the terminal could not stop them. C2 and C1M used
`nohup ... &`; from C3 on the runbooks use `setsid nohup ... < /dev/null &`.

Five scripts on record sit outside the packages:

| Script | What it does | How it is called |
| --- | --- | --- |
| `lab/analyze_c1_wrapped.py` | Runs the C1 analysis past the error described in section 4.6 | `python analyze_c1_wrapped.py runs/gne_core_c1-*-real-*` (its line 4) |
| `lab/analyze_c4_wrapped.py` | Runs the C4 analysis past the error described in section 4.10 | `python analyze_c4_wrapped.py runs/gne_c4-*-real-*` (its line 7) |
| `lab/c6_bounds.py` | An exploratory check added after the C6 freeze (section 4.13) | `python3 c6_bounds.py` (its line 4) |
| `lab/gne_collect_evidence.py` | Packs run records into one archive, `gne_evidence_<time>.tar.gz`, in the current folder. It reads only and is not needed for a re-run. The archive on record is `lab/gne_evidence_20261002T213342Z.tar.gz` | `python3 gne_collect_evidence.py` (its lines 6-8) |
| `lab/logs/c3_queue.sh` | The lab's queue for part of C3 (section 4.9) | no file says how it was started |

The two wrappers look for the package folder next to themselves, and the other two Python scripts look for `runs/`
in the current folder. All four belong in the project folder, beside the packages.

### 4.3 V6 (`lab/phase1_v6_frozen_2x2`)

Folder assumed: `~/ai-lab/project/agentscope`, "with the venv active" (plan line 151). There is no launcher.
The plan's section 8 gives these commands, in this order (lines 153-164):

```bash
python -m unittest discover -s phase1_v6_frozen_2x2 -p 'test_v6.py' -v       # expect 30 OK
python phase1_v6_frozen_2x2/run.py --fake comply --stage main --n 1            # scripted smoke test
python phase1_v6_frozen_2x2/run.py --real --stage baseline
python phase1_v6_frozen_2x2/analyze.py runs/phase1_v6_frozen_2x2-baseline-real-*
# only if baseline says PROCEED:
python phase1_v6_frozen_2x2/run.py --real --stage controls
python phase1_v6_frozen_2x2/run.py --real --stage probe
python phase1_v6_frozen_2x2/run.py --real --stage main
python phase1_v6_frozen_2x2/analyze.py runs/phase1_v6_frozen_2x2-*-real-*
python phase1_v6_frozen_2x2/blind_export.py runs/phase1_v6_frozen_2x2-main-real-<stamp> --out blind_v6
# after consensus coding:
python phase1_v6_frozen_2x2/analyze.py runs/phase1_v6_frozen_2x2-*-real-* --codes blind_v6/coding_sheet.csv --key blind_v6/blind_key.csv
```

If a batch is interrupted (line 166): `run.py --real --resume <batch folder>`.

Analysis command: the three `analyze.py` lines above (after the baseline, after all stages, and after the hand
coding).

On record: one real `baseline` batch of 20 runs. The plan's own log says V6 was closed after it, because 3 of the
20 runs hit the 180-second timeout (lines 189-193). The other stages were never run.

### 4.4 X1 (`lab/phase1_x1_scope_explicit`)

Folder assumed: "the Ubuntu VM from `~/ai-lab/project/agentscope` with the venv active" (runbook line 7).

Step 0, prepare (lines 11-16). On the Mac: `caffeinate -dimsu`. In the VM:

```bash
cd ~/ai-lab/project/agentscope && source .venv/bin/activate
curl -s http://127.0.0.1:11434/api/version ; echo
pgrep -af "run.py --real" || echo "no other run active"
```

Step 1, install (lines 22-27). The zip is first put in `/media/sf_AI-Lab-Transfer`:

```bash
test -e phase1_x1_scope_explicit && echo "STOP: folder exists" || {
  cp -n /media/sf_AI-Lab-Transfer/phase1_x1_scope_explicit.zip .
  sha256sum phase1_x1_scope_explicit.zip
  unzip -q phase1_x1_scope_explicit.zip && ls phase1_x1_scope_explicit; }
```

Steps 2 to 5 (lines 33, 54, 61, 81):

```bash
bash phase1_x1_scope_explicit/x1.sh check
bash phase1_x1_scope_explicit/x1.sh freeze
bash phase1_x1_scope_explicit/x1.sh run
bash phase1_x1_scope_explicit/x1.sh analyze
```

If interrupted (line 76):

```bash
bash phase1_x1_scope_explicit/x1.sh resume runs/phase1_x1_scope_explicit-scope-real-<stamp>
```

Analysis command: `bash phase1_x1_scope_explicit/x1.sh analyze`.

On record: one batch of 40 runs. X1 has a single stage; it has no controls, rating check or follow-up.
See section 2.4 before trying X1: the launcher asks for the lab's own model build.

### 4.5 V7 (`lab/phase1_v7_timeout`)

Folder assumed: `~/ai-lab/project/agentscope`, "with the venv active" (plan line 174). There is no launcher.
The plan's section 8 gives the same list as V6, with V7's names (lines 176-187):

```bash
python -m unittest discover -s phase1_v7_timeout -p 'test_v7.py' -v       # expect 34 OK
python phase1_v7_timeout/run.py --fake comply --stage main --n 1            # scripted smoke test
python phase1_v7_timeout/run.py --real --stage baseline
python phase1_v7_timeout/analyze.py runs/phase1_v7_timeout-baseline-real-*
# only if baseline says PROCEED:
python phase1_v7_timeout/run.py --real --stage controls
python phase1_v7_timeout/run.py --real --stage probe
python phase1_v7_timeout/run.py --real --stage main
python phase1_v7_timeout/analyze.py runs/phase1_v7_timeout-*-real-*
python phase1_v7_timeout/blind_export.py runs/phase1_v7_timeout-main-real-<stamp> --out blind_v7
# after consensus coding:
python phase1_v7_timeout/analyze.py runs/phase1_v7_timeout-*-real-* --codes blind_v7/coding_sheet.csv --key blind_v7/blind_key.csv
```

If a batch is interrupted (line 189): `run.py --real --resume <batch folder>`.

Analysis command: the three `analyze.py` lines above, as in V6. In `lab/runs/` the first of them matches both
real `baseline` batches (section 7, point 26).

On record: two scripted test batches of stage `baseline`, and two real `baseline` batches. The first real batch was
cut off in its fifteenth run (`ep-014`) and was not resumed. The second, started with the same seeds, is complete (20 runs). No
controls, rating-check or scored-run batch exists, and the plan's deviations log holds no entry (lines 206-208).

### 4.6 C1 (`lab/gne_core_c1`)

Folder assumed: "in the VM from `~/ai-lab/project/agentscope` with the venv active" (runbook line 3).
The runbook adds: "Run one model at a time; nothing else on the VM" (line 4).

Before the steps (line 19), one model at a time, after a look at `df -h`:

```bash
ollama pull qwen2.5:3b
```

Step 0 (line 27), in PowerShell on Windows: `powercfg /change standby-timeout-ac 0`.
Step 1 (lines 28-29): copy `gne_core_c1.zip` from `/media/sf_AI-Lab-Transfer`, check its SHA-256, then:

```bash
unzip -q gne_core_c1.zip
```

Steps 2 to 5 (lines 30, 32, 33, 36, 37):

```bash
bash gne_core_c1/c1.sh check
bash gne_core_c1/c1.sh freeze qwen2.5:3b qwen2.5:7b llama3.1:8b
bash gne_core_c1/c1.sh run qwen2.5:3b
bash gne_core_c1/c1.sh resume <batch folder> <model>
bash gne_core_c1/c1.sh analyze
```

`run` does controls, then the rating check, then the scored runs. `resume` is only for an interrupted batch.

Analysis command: `bash gne_core_c1/c1.sh analyze`. On the lab's data this command stopped with an error
(`KeyError 'family'`), because one resumed batch held an `aborted_not_rerun` record. The lab then ran the analysis
through a wrapper kept at the top of `lab/` (`lab/gne_core_c1/DEVIATIONS.md` lines 23-26;
usage line in `lab/analyze_c1_wrapped.py`):

```bash
python analyze_c1_wrapped.py runs/gne_core_c1-*-real-*
```

On record:

- The freeze record names other models than the runbook's example: `qwen2.5:3b llama3.1:8b mistral:7b`
  (`lab/gne_core_c1/FREEZE.md` line 4). `qwen2.5:7b` was not installed at that time.
- `qwen2.5:3b` and `llama3.1:8b` have all three stages. `mistral:7b` has controls only; it wrote its tool calls
  as text, and its other stages were not run (`lab/gne_core_c1/DEVIATIONS.md` lines 28-33).
- Three batches were set aside in `lab/runs_excluded/`: a second rating-check batch for `qwen2.5:3b` and two
  restarted controls batches for `mistral:7b`.

### 4.7 C2 (`lab/gne_core_c2`)

Folder assumed: "the project root (~/ai-lab/project/agentscope) with the venv active" (runbook line 3).
The runbook's steps (lines 5-16), with `MODEL` and `SLUG` as the runbook writes them:

```bash
ollama pull qwen2.5:7b
bash gne_core_c2/c2.sh check
bash gne_core_c2/c2.sh freeze qwen2.5:3b llama3.1:8b qwen2.5:7b
nohup bash gne_core_c2/c2.sh controls MODEL > logs/c2_SLUG_controls.out 2>&1 &
nohup bash gne_core_c2/c2.sh probe MODEL > logs/c2_SLUG_probe.out 2>&1 &
nohup bash gne_core_c2/c2.sh main MODEL > logs/c2_SLUG_main.out 2>&1 &
bash gne_core_c2/c2.sh resume runs/<batch folder> MODEL
bash gne_core_c2/c2.sh analyze
```

The three `nohup` lines are per model, one stage at a time, each checked before the next. The runbook says:
"Run at most two models at once" (line 13). `resume` is only for a batch that stopped early.

Analysis command: `bash gne_core_c2/c2.sh analyze`.

On record: controls and rating check for all three models; scored runs for `qwen2.5:7b` only, because the rating
gate failed for the other two. Two models were run side by side, as the runbook allows (section 5).

### 4.8 C1M (`lab/gne_c1m`)

Folder assumed: "the project root (~/ai-lab/project/agentscope) with the venv active" (runbook line 3).
The runbook's steps (lines 5-13):

```bash
bash gne_c1m/c1m.sh check
bash gne_c1m/c1m.sh diag mistral:7b
bash gne_c1m/c1m.sh freeze mistral:7b
nohup bash gne_c1m/c1m.sh stage mistral:7b controls > logs/c1m_controls.out 2>&1 &
nohup bash gne_c1m/c1m.sh stage mistral:7b probe > logs/c1m_probe.out 2>&1 &
nohup bash gne_c1m/c1m.sh stage mistral:7b main > logs/c1m_main.out 2>&1 &
bash gne_c1m/c1m.sh resume runs/<batch folder> mistral:7b
bash gne_c1m/c1m.sh analyze
```

`diag` makes 25 single model calls before the freeze and saves `runs/gne_c1m-diag-<stamp>/diag.json`.

Analysis command: `bash gne_c1m/c1m.sh analyze`.

On record: all three stages. The scored-run batch stopped twice and was resumed twice
(`lab/gne_c1m/DEVIATIONS.md` lines 3-10).

### 4.9 C3 (`lab/gne_c3`)

Folder assumed: "the project root (~/ai-lab/project/agentscope) with the venv active". The runbook adds:
"Start every long run with `setsid nohup ... < /dev/null &` so closing the terminal can't stop it" (lines 3-4).

Steps 1 to 3 (lines 6-8):

```bash
ollama pull qwen2.5:14b
ollama pull granite3.3:8b
bash gne_c3/c3.sh check
bash gne_c3/c3.sh freeze qwen2.5:7b granite3.3:8b qwen2.5:14b llama3.1:8b
```

Steps 4 and 5 are given in short form only (lines 9-12):

```text
4. **Block A** (parallel, about 3 h): `all qwen2.5:7b` and `all granite3.3:8b`. `all` runs controls,
   then the probe, then the gate, then main.
5. **Block B:** `followup llama3.1:8b` (about 30 min), then `all qwen2.5:14b` (about 5 h, run alone for
   memory).
```

The launcher's own usage lines give the full form: `bash gne_c3/c3.sh all MODEL` and
`bash gne_c3/c3.sh followup MODEL` (`lab/gne_c3/c3.sh` lines 8-9).

Steps 6 and 7, and the resume command (lines 13-16):

```bash
bash gne_c3/c3.sh analyze
bash gne_c3/c3.sh audit
bash gne_c3/c3.sh resume runs/<batch folder> MODEL
```

Analysis command: `bash gne_c3/c3.sh analyze`.

On record, the order differed from the two blocks. `granite3.3:8b` made no tool calls through Ollama's tool
interface, so its `all` was stopped after the controls (`lab/gne_c3/DEVIATIONS.md` lines 3-8). The rest was run by a small queue script that
is not part of the package, `lab/logs/c3_queue.sh`. Its lines 3, 5 and 9 are:

```bash
echo "$(date) granite probe"; bash gne_c3/c3.sh probe granite3.3:8b > logs/c3_granite_probe.out 2>&1
echo "$(date) llama follow-up (H3)"; bash gne_c3/c3.sh followup llama3.1:8b > logs/c3_llama_followup.out 2>&1
echo "$(date) qwen2.5:14b all stages"; bash gne_c3/c3.sh all qwen2.5:14b > logs/c3_qwen14b_all.out 2>&1
```

The follow-up for `llama3.1:8b` therefore ran while the scored runs of `qwen2.5:7b` were still going (section 5).
The queue script begins with `cd ~/ai-lab/project/agentscope && source .venv/bin/activate`.

### 4.10 C4 (`lab/gne_c4`)

Folder assumed: "the project root (~/ai-lab/project/agentscope) with the venv active". The runbook adds: keep the
Windows computer awake while C4 runs (lines 3-5).

The runbook's steps (lines 7-18):

```bash
ollama pull command-r7b && ollama pull mistral-nemo:12b && ollama pull gpt-oss:20b
ollama run gpt-oss:20b "Say OK." ; ollama stop gpt-oss:20b ; free -h
bash gne_c4/c4.sh check
bash gne_c4/c4.sh freeze command-r7b mistral-nemo:12b gpt-oss:20b
setsid nohup bash gne_c4/c4_queue.sh > logs/c4_queue.out 2>&1 < /dev/null &
tail -n 5 logs/c4_queue.out
bash gne_c4/c4.sh analyze
bash gne_c4/c4.sh audit
```

The second line is a memory test for the largest model. It calls the model once, outside the study.
The queue runs, for each model in turn, the controls, the rating check with its gate, the follow-up, and the
scored runs only if the gate passed. The last two lines are for when the queue has printed `QUEUE DONE`.

If a batch stops early (line 20):

```bash
bash gne_c4/c4.sh resume runs/<batch folder> MODEL
```

Analysis command: `bash gne_c4/c4.sh analyze`. On the lab's data it stopped with a `ZeroDivisionError`, because
`gpt-oss:20b` had cells with no scored outcome. The lab then used a wrapper kept at the top of `lab/`
(`lab/gne_c4/DEVIATIONS.md` lines 2-11; usage line in `lab/analyze_c4_wrapped.py`):

```bash
python analyze_c4_wrapped.py runs/gne_c4-*-real-*
```

On record: ten batches. The gate failed for `command-r7b` and `mistral-nemo:12b`; `gpt-oss:20b` ran all four stages.

### 4.11 C4G (`lab/gne_c4g`)

Folder assumed: "the project root with the venv active"; no path is given. The runbook adds: "Keep the Windows
host awake. Nothing else running" (line 3).

The runbook's steps (lines 5-12):

```bash
bash gne_c4g/c4g.sh check
bash gne_c4g/c4g.sh freeze gpt-oss:20b
setsid nohup bash gne_c4g/c4g.sh all gpt-oss:20b > logs/c4g.out 2>&1 < /dev/null &
tail -n 5 logs/c4g.out
bash gne_c4g/c4g.sh analyze
bash gne_c4g/c4g.sh resume runs/<batch folder> gpt-oss:20b
```

`analyze` is for when the log shows "Batch complete" for the scored runs. `resume` is only for a batch that stopped early.

Analysis command: `bash gne_c4g/c4g.sh analyze`.

On record: three batches (controls, rating check, scored runs).

### 4.12 C5 (`lab/gne_c5`)

Folder assumed: "the project root with the venv active"; no path is given (runbook line 3). The runbook says to run
C5 after C4 has been analysed, because the list of models depends on C4's result (lines 3 and 7-9).

The runbook's steps (lines 6-15):

```bash
bash gne_c5/c5.sh check
bash gne_c5/c5.sh freeze qwen2.5:7b
setsid nohup bash gne_c5/c5.sh all qwen2.5:7b > logs/c5_qwen7b.out 2>&1 < /dev/null &
bash gne_c5/c5.sh analyze
bash gne_c5/c5.sh audit
bash gne_c5/c5.sh resume runs/<batch folder> MODEL
```

The runbook gives a second form of the freeze line for the case that a C4 model joins:
`bash gne_c5/c5.sh freeze qwen2.5:7b command-r7b`. The lab froze with `qwen2.5:7b` alone
(`lab/gne_c5/FREEZE.md` line 4).

Analysis command: `bash gne_c5/c5.sh analyze`, then `bash gne_c5/c5.sh audit`.

On record: the first controls batch failed completely because Ollama had been stopped for lack of memory. It was
moved to `lab/runs_excluded/` and C5 was started again from the controls (`lab/gne_c5/DEVIATIONS.md` lines 2-13).
The file `lab/logs/c5_qwen7b.out` holds only three `SKIP` lines from a later call of `all`; the per-stage
logs `lab/logs/c5_qwen2.5-7b_*.log` hold the console output.

### 4.13 C6 (`lab/gne_c6`)

Folder assumed: "the project root with the venv active"; no path is given. The runbook adds: nothing else running,
and `ollama ps` should be empty before the start (lines 3-4).

The runbook's steps (lines 6-17):

```bash
mkdir -p logs && bash gne_c6/c6.sh check
bash gne_c6/c6.sh freeze qwen2.5:7b
setsid nohup bash gne_c6/c6.sh all qwen2.5:7b > logs/c6.out 2>&1 < /dev/null &
tail -n 3 logs/c6.out
bash gne_c6/c6.sh analyze | tee logs/c6_analysis.txt
bash gne_c6/c6.sh audit
bash gne_c6/c6.sh resume runs/<batch folder> qwen2.5:7b
```

Analysis command: `bash gne_c6/c6.sh analyze | tee logs/c6_analysis.txt`. After the freeze the lab added a second,
exploratory check, kept at the top of `lab/` and logged in `lab/gne_c6/DEVIATIONS.md` lines 14-19. Its own header
gives the command:

```bash
python3 c6_bounds.py
```

On record: three batches. The machine shut down after 55 of the 240 scored runs and the batch was resumed
(`lab/gne_c6/DEVIATIONS.md` lines 8-12).

### 4.14 C5P (`lab/gne_c5p`)

Folder assumed: "the project root"; no path is given. "The virtual environment is optional" (runbook line 3).
Before the start, `pgrep -af run.py` should print nothing and `ollama ps` should list nothing (lines 4-5).

The runbook's steps (lines 8-16):

```bash
bash gne_c5p/c5p.sh check
bash gne_c5p/c5p.sh freeze qwen2.5:7b
mkdir -p logs && setsid nohup bash gne_c5p/c5p.sh all qwen2.5:7b > logs/c5p.out 2>&1 < /dev/null &
tail -n 3 logs/c5p.out
bash gne_c5p/c5p.sh analyze | tee logs/c5p_analysis.txt
bash gne_c5p/c5p.sh audit
```

If a batch stops early (lines 24-27):

```bash
setsid nohup bash gne_c5p/c5p.sh resume runs/<batch folder> qwen2.5:7b > logs/c5p_resume.out 2>&1 < /dev/null &
bash gne_c5p/c5p.sh main qwen2.5:7b
```

The second line is for the case that the scored runs never started because the rating check was interrupted:
resume the rating-check batch first, then start `main` "the same detached way".

Analysis command: `bash gne_c5p/c5p.sh analyze | tee logs/c5p_analysis.txt`.

On record: three batches, no resume.

### 4.15 The two packages that never ran

This page gives no commands for them, because there is no run to repeat:

- `lab/gne_c2m` (C2M) is the C2 design for `mistral:7b` with the text-call adapter (`lab/gne_c2m/c2m.sh` line 2).
  Its runbook lists `check`, `diag`, `freeze`, the stages `controls`, `probe` and `main`, `resume` and `analyze`
  (`lab/gne_c2m/RUNBOOK.md` lines 5-15). It has no freeze record and no batch.
- `lab/gne_core_c1_superseded_unrun` is an earlier version of the C1 package. Its launcher and `stats.py` are the
  same files as C1's; its plan, runbook, `run.py`, `analyze_c1.py` and `test_c1.py` differ. All ten `gne_core_c1`
  batches on record carry the hash of C1's `run.py`, not of this one.

## 5. How long it took

### 5.1 How the times were measured

For each batch:

- **Start** is the UTC time stamp in the batch folder's name. The runner sets it when it creates the folder.
- **End** is the latest `created_at` time in the batch's reply files (`response-*.json`). Ollama writes it in UTC.
  The files show that it marks the end of a reply: within a run, the gap between two consecutive `created_at`
  times matches the `total_duration` of the later reply (in 3,341 of 3,346 pairs it is nearer to it than to the
  earlier reply's).
- **Span** is end minus start. It is wall-clock time and includes every stop.
- **Inside Ollama** is the sum of `total_duration` over the reply files: the time Ollama reports for the requests.
  A request that timed out has no reply file, so its waiting time (up to 600 seconds) is in the span only.
- **Pauses** are gaps of more than 15 minutes between two consecutive replies of a batch.

The console logs print an `elapsed` figure per run. It agrees with the spans: 25 minutes for X1, 624 minutes for
the C5 scored runs, 1,304 minutes for the C5P scored runs (the last lines of `lab/logs/x1_run_20260927T023746Z.log`,
`lab/logs/c5_qwen2.5-7b_main.log` and `lab/logs/c5p.out`).

A second check uses the file list `manifest/MANIFEST.tsv`. Its column `archive_time` gives the time each file was
last written, in the lab machine's local time. For all 58 batches the time of `batch.json` is 5 hours 30 minutes
ahead of the UTC stamp in the folder name. For every kept real batch but one, the last file of the batch was
written within 5 seconds of the last reply. The exception is the first V7 batch (section 5.2).

In the tables, `2h24m` means 2 hours 24 minutes and `8m53s` means 8 minutes 53 seconds. Figures of an hour or
more are cut to whole minutes, not rounded.

### 5.2 V6, X1 and V7 (2 CPUs, 10 GiB, 2 threads)

| Study | Stage | Runs | Start (UTC) | Span | Inside Ollama | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| V6 | `baseline` | 20 | 27 Sep 01:18:59 | 42m57s | 24m52s | 3 runs hit the 180 s timeout |
| X1 | `scope` | 40 | 27 Sep 02:37:46 | 25m39s | 15m37s | 1 run hit the 600 s timeout |
| V7 | `baseline`, first batch | 20 planned, 14 finished | 27 Sep 03:19:12 | 1h45m | 26m09s | 4 runs hit the 600 s timeout; 4 pauses, 1h27m in all; cut off in its fifteenth run (`ep-014`). The span ends at the last readable reply (05:04:44); the last two files of `ep-014` were written at 05:05:18, and both are empty |
| V7 | `baseline`, second batch | 20 | 27 Sep 06:35:52 | 31m47s | 31m47s | none |

### 5.3 The C studies

One row per study and model. Cells show the span of each stage. C1 ran on 2 threads at a time when the freeze
record showed 2 CPUs; C1M ran on 2 threads; all other C studies ran on 6 threads with 16 CPUs in the freeze record.

| Study | Model | Controls | Rating check | Follow-up | Scored runs | First start to last reply |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | `qwen2.5:3b` | 9m59s | 23m59s | - | 38m03s | 3h07m |
| C1 | `llama3.1:8b` | 14m37s | 10m09s | - | 4h35m | 5h50m |
| C1 | `mistral:7b` | 3h33m | not run | - | not run | 3h33m |
| C2 | `qwen2.5:3b` | 4m32s | 4m06s | - | gate failed | 10m04s |
| C2 | `llama3.1:8b` | 10m04s | 9m30s | - | gate failed | 8h51m |
| C2 | `qwen2.5:7b` | 8m56s | 13m14s | - | 2h20m | 7h03m |
| C1M | `mistral:7b` | 1h51m | 48m04s | - | 14h02m | 17h18m |
| C3 | `qwen2.5:7b` | 7m51s | 8m53s | - | 2h24m | 2h41m |
| C3 | `granite3.3:8b` | 36m10s | 12m23s | - | not run | 50m23s |
| C3 | `llama3.1:8b` | - | - | 22m08s | - | 22m08s |
| C3 | `qwen2.5:14b` | 17m43s | 11m39s | - | 14h23m | 14h52m |
| C4 | `command-r7b` | 14m46s | 13m28s | 1h03m | gate failed | 1h31m |
| C4 | `mistral-nemo:12b` | 11m14s | 3m37s | 4m20s | gate failed | 19m12s |
| C4 | `gpt-oss:20b` | 1m40s | 3m38s | 8m45s | 21m19s | 35m23s |
| C4G | `gpt-oss:20b` | 3m16s | 2m32s | - | 3h11m | 3h16m |
| C5 | `qwen2.5:7b` | 6m13s | 13m05s | - | 10h26m | 10h46m |
| C6 | `qwen2.5:7b` | 8m13s | 14m41s | - | 22h01m | 22h45m |
| C5P | `qwen2.5:7b` | 12m59s | 37m32s | - | 21h46m | 22h37m |

In C2 the stages of one model were started hours apart, which is why the last column is long there.

The long spans hide stops. For the batches with pauses or a much shorter time inside Ollama, the table below sets
the two figures side by side.

| Study | Model and stage | Span | Inside Ollama | Pauses over 15 min | Runs that timed out | Cause in the record |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | `qwen2.5:3b` rating check | 23m59s | 10m31s | none | 1 | not given |
| C1 | `llama3.1:8b` scored runs | 4h35m | 3h44m | 2, 57m40s in all | 1 | batch stopped at 64 of 72 and was resumed (`lab/gne_core_c1/DEVIATIONS.md` lines 19-21) |
| C1 | `mistral:7b` controls | 3h33m | 1h11m | 1, 2h25m | 0 | stopped at 9 of 12, "cause unknown", resumed (same file, lines 28-29) |
| C1M | `mistral:7b` scored runs | 14h02m | 9h55m | 3, 3h58m in all | 5 | the VM shut down; a first resume stopped silently (`lab/gne_c1m/DEVIATIONS.md` lines 3-10) |
| C3 | `qwen2.5:7b` scored runs | 2h24m | 2h00m | 1, 23m32s | 1 | not given |
| C3 | `qwen2.5:14b` scored runs | 14h23m | 6h11m | 1, 8h12m | 1 | the Windows computer slept overnight (`lab/gne_c3/DEVIATIONS.md` lines 10-13) |
| C4G | `gpt-oss:20b` scored runs | 3h11m | 2h04m | 2, 58m05s in all | 3 | not given; C4G has no deviations file |
| C5 | `qwen2.5:7b` scored runs | 10h26m | 6h13m | 3, 4h45m in all | 3 | not given |
| C6 | `qwen2.5:7b` scored runs | 22h01m | 7h01m | 4, 15h00m in all | 3 | one timeout and one shutdown are logged (`lab/gne_c6/DEVIATIONS.md` lines 2-12); two later pauses are not |
| C5P | `qwen2.5:7b` scored runs | 21h46m | 13h47m | 5, 8h00m in all | 1 | not given; C5P has no deviations file |

In C5 and C5P the console log of the scored runs shows one unbroken process whose `elapsed` figure jumps across
each pause (for example from 91 to 363 minutes in `lab/logs/c5p.out` lines 226-228). The process was not restarted.

### 5.4 Whole studies

| Study | First batch started (UTC) | Last reply (UTC) | Wall clock | Inside Ollama, summed over batches |
| --- | --- | --- | --- | --- |
| V6 | 27 Sep 01:18:59 | 27 Sep 02:01:56 | 42m57s | 24m52s |
| X1 | 27 Sep 02:37:46 | 27 Sep 03:03:25 | 25m39s | 15m37s |
| V7 | 27 Sep 03:19:12 | 27 Sep 07:07:39 | 3h48m | 57m56s |
| C1 | 27 Sep 14:24:18 | 28 Sep 03:36:26 | 13h12m | 6h18m |
| C2 | 28 Sep 06:18:31 | 28 Sep 22:03:45 | 15h45m | 3h10m |
| C1M | 28 Sep 19:24:42 | 29 Sep 12:43:26 | 17h18m | 12h34m |
| C3 | 29 Sep 15:22:01 | 30 Sep 08:56:39 | 17h34m | 10h08m |
| C4 | 30 Sep 18:38:17 | 30 Sep 21:04:20 | 2h26m | 2h25m |
| C4G | 1 Oct 03:45:54 | 1 Oct 07:02:49 | 3h16m | 2h10m |
| C5 | 1 Oct 07:48:51 | 1 Oct 18:35:04 | 10h46m | 6h32m |
| C6 | 1 Oct 22:26:08 | 2 Oct 21:11:14 | 22h45m | 7h24m |
| C5P | 2 Oct 21:28:26 | 3 Oct 20:05:57 | 22h37m | 14h37m |

These figures leave out the batches in `lab/runs_excluded/`.

### 5.5 Batches that shared the machine

Some batches of different models ran at the same time, so their times are not those of a model running alone:

- C2: the controls of `qwen2.5:3b` and `llama3.1:8b` started in the same second, and the rating check of
  `qwen2.5:3b` ran while the controls of `llama3.1:8b` were still going. The controls of `qwen2.5:7b` and the
  rating check of `llama3.1:8b` also started in the same second.
- C2 and C1M: the rating check and scored runs of `qwen2.5:7b` in C2 overlapped with the controls and rating check
  of `mistral:7b` in C1M.
- C3: the controls, rating check and scored runs of `qwen2.5:7b` overlapped with the controls and rating check of
  `granite3.3:8b` and with the follow-up of `llama3.1:8b`.

No other kept batches overlapped by more than 5 seconds.

### 5.6 The runbooks' own estimates

| Study | Runbook estimate | What the record shows |
| --- | --- | --- |
| X1 | run step "about 60-80 min" (line 59) | 25m39s |
| C1 | "roughly 1-2 h for 3B and 4-8 h for 7-8B on 2 CPUs" for all three stages (lines 21-22) | 3B: stages add up to 1h12m. 8B (`llama3.1:8b`): stages add up to 5h00m |
| C3 | `qwen2.5:7b` block "about 3 h"; follow-up "about 30 min"; `qwen2.5:14b` "about 5 h" (lines 9-12) | 2h41m; 22m08s; 14h52m, of which 6h40m inside Ollama |
| C4 | queue "about 14-18 h in total" (line 13) | 2h26m; two of the three models stopped at the gate |
| C4G | "about 1-2 h" (line 1) | 3h16m, of which 2h10m inside Ollama |
| C5 | "About 8-9 h for qwen2.5:7b" (line 12) | 10h46m, of which 6h32m inside Ollama |
| C6 | "about 6 hours" (line 1) | 22h45m, of which 7h24m inside Ollama |
| C5P | "about 8 to 10 hours" (line 1) | 22h37m, of which 14h37m inside Ollama |

## 6. What will not come out identical, and why

What the scripts fix:

- **The order of runs and the seed of each run.** The runner builds the list of runs from the master seed and
  stores it in `batch.json` (`schedule`). Each request then carries that run's seed. In all 6,765 readable request
  files, the seed equals the one in the list. Seven of the recorded lists were rebuilt for this page with
  Python 3.11.15 from the rule in the runners, and each came out equal to the recorded list.
- **The first request of each run.** Where the lab ran the same stage twice with the same seeds, the first request
  of every run was the same in both batches.

What the record shows is not fixed:

- **The replies.** Every study samples with `temperature` 0.7. The record holds batches that were run twice on
  the lab machine with the same model, the same requests and the same seeds. Most replies repeated exactly; some
  did not:
  - V6 `baseline` against the complete V7 `baseline` (20 runs each): 14 runs were identical at every turn. In 3
    runs a reply differed although request and seed were the same; in one of these the outcome of the run changed.
    In 3 runs a V6 request got no reply because of the 180-second timeout.
  - The two V7 `baseline` batches (15 runs in common): 9 runs were identical at every turn. In 1 run a reply
    differed although request and seed were the same. In 5 runs a request of the first batch got no reply.
  - C1 rating check for `qwen2.5:3b`, the analysed batch against the repeated one (30 single calls each):
    29 replies were identical; the other call timed out in the analysed batch.
  - C1 controls for `mistral:7b`, the kept batch against a restarted one (4 runs in common): in 1 run the
    first reply differed although request and seed were the same.

  The record does not say why. The plans and runbooks say nothing about whether a seed gives the same reply on
  another machine or under another Ollama version. One older write-up does: `lab/gne_release_kit/README.md` (lines
  116-117) expects re-runs on other hardware or under another Ollama version to differ run by run. It gives no test
  of this. Counting single requests in place of runs gives the same picture. Where an identical request (the same
  model, messages, settings and seed) was answered more than once, 28 of the 208 later replies differed from the
  first. And where C1 and C2 sent the same first control request with only the thread count changed, 2 against 6,
  the first reply differed in 9 of 12 runs for `qwen2.5:3b` and in 1 of 12 for `llama3.1:8b` (`python3
  verify/recount.py`). The machine had also grown between the two studies, and in C2 the two models ran side by
  side, so the record cannot say which of these made the difference.
- **Which runs end unscored.** A reply that takes longer than the timeout makes the run unscored. This depends on
  the speed of the machine. The V7 plan gives this as the reason V7 exists (lines 11-16). In the kept batches,
  27 runs ended with a timed-out request.
- **The times.** They depend on the machine and on what else it was doing (section 5).

For V6, X1 and V7 there is one more reason: the model build itself cannot be matched (section 2.4).
For the C studies the Ollama version is not recorded (section 1).

## 7. Known gaps for a replicator

Each point was checked against the files.

**Missing from the record**

1. The build file of `day1-qwen25-3b` and the command that built it (section 2.4). V6, X1 and V7 depend on it,
   and their `batch.json` files hold no digest.
2. The Ollama version for all nine C studies. Also: the Ubuntu and kernel versions, the CPU model, the VM software,
   the disk size, the Python patch version, and how the virtual environment was made (section 1).
3. Any saved output of the launchers' `check` and `freeze` commands. The freeze records are the only trace.
4. The reference hash that the X1 and C1 runbooks mention for their zip file ("the value given with the download").
   The repository's own file list, `manifest/SHA256SUMS`, gives a SHA-256 for every file now in `lab/`, these
   zips included. No file says whether that is the value that was given at the time.
5. A zip file for C4, C4G, C5 and C6. The package folders are there.
6. Console logs for some batches. `lab/logs/c1_qwen2.5-3b_probe.log` and `lab/logs/c1_mistral-7b_controls.log`
   hold the output of batches that were later set aside. No console log names the analysed C1 rating-check batch
   for `qwen2.5:3b` or the first V7 `baseline` batch. For the kept `mistral:7b` controls batch of C1 only the
   resumed part is logged. `lab/logs/c5_qwen7b.out` holds three `SKIP` lines only.
7. Reasons for the pauses in the first V7 batch, in the C3 scored runs of `qwen2.5:7b` and in the C4G, C5 and C5P
   scored runs, and for the two later pauses in C6 (sections 5.2 and 5.3). The reason the first V7 batch was cut
   off is not given either.

**Tied to the lab's own layout**

8. The project path `~/ai-lab/project/agentscope` and the virtual environment `.venv` (section 4.1).
9. The shared folder `/media/sf_AI-Lab-Transfer` in the X1 and C1 runbooks.
10. Steps for the computer under the VM: `caffeinate` on a Mac (X1), `powercfg` on Windows (C1), "keep the Windows
    host awake" (C4, C4G, C5, C6, C5P).
11. The queue script `lab/logs/c3_queue.sh`, which starts with the lab's own path. No file says how it was started.

**Inconsistent between files**

12. The computer under the VM: a Mac in the X1 runbook, Windows from the C1 runbook on. The package
    `gne_core_c1_superseded_unrun` holds a superseded C1 runbook that says Mac.
13. The VM's size: 2 CPUs and 10 GiB up to the C1 freeze, 16 CPUs and 16 GiB from the C2 freeze. The C2 plan and
    runbook say 12 CPUs.
14. The C1 runbook's freeze example names `qwen2.5:3b qwen2.5:7b llama3.1:8b`. The freeze record names
    `qwen2.5:3b llama3.1:8b mistral:7b`.
15. The X1 runbook says the unpacked folder "lists 10 files" (line 29). The zip holds 9.
16. `lab/gne_c1m/c1m.sh` line 28 prints "expect: Ran 18 tests". The C1M runbook says 23, and the test file defines 23.
17. The V6 and V7 plans give the smoke test as `--fake comply --stage main --n 1`. The two test batches on record
    for V7 are of stage `baseline`. There is none for V6.
18. The X1 runbook says to stop the run "if: 2 of the first 6 episodes fail, or any failure is a timeout"
    (lines 73-74). In the X1 console log the first two runs end as `interface_failure`, and the run record of the
    second shows a timeout. The batch went on to 40 of 40. The X1 plan's deviations log is empty.
19. V7: the plan says an interrupted batch is resumed. The first V7 `baseline` batch was cut off and never
    resumed; a second batch with the same seeds was started. The plan lists four stages; only `baseline` batches
    exist. The plan's deviations log is empty.

**Behaviour of the scripts that can surprise**

20. The launchers cannot be used inside `lab/` as it stands (section 4.1).
21. The launcher is among the hashed files. Editing it, for example to change `python` to `python3`, makes the
    run commands stop with "files changed since the freeze".
22. Every launcher except C5P's calls `python`. One lab log shows that command missing (section 4.2).
23. In X1, C1 and C1M, `freeze` makes a git commit and tag when typed inside a git work tree, such as a clone of
    this repository.
24. The C runners record the model's digest but compare it with nothing. Compare the digest in your own
    `batch.json` with section 2.1 yourself.
25. The analysis commands of C1 and C4 stopped with an error on the lab's data; wrappers at the top of `lab/` were
    used instead (sections 4.6 and 4.10).
26. The V7 plan's analysis command ends in `runs/phase1_v7_timeout-baseline-real-*`. In `lab/runs/` this matches
    both V7 batches, and `analyze.py` reads every run in every folder it is given (lines 61-76 and 241-245).
27. The launcher inside `gne_core_c1_superseded_unrun` is the same file as C1's and names the package
    `gne_core_c1` (line 9). Typed in a folder that holds both, it acts on the C1 package.
28. When a command is not recognised, the launchers print lines 2-8 of their own file as help. In C1M and from C2
    on, the list of commands is longer than that, so the help is cut short.
29. In X1, C1 and C1M the `resume` command does not make the freeze check; the other launchers make it first
    (section 3.2). In every study the runner itself refuses to resume if a Python file of the package has changed.

**Named in the files but absent**

30. The plans mention a study X2 and studies up to C9: "X1 or X2" (`lab/gne_core_c1/PREREGISTRATION.md` line 5),
    "C1 to C9" and "every study from C1M to C7" (`lab/gne_c5p/PREREGISTRATION.md` lines 5 and 9). `lab/` has no
    package, zip or batch named X2, C7, C8 or C9.
31. `gne_c2m` is a complete package that never ran. The C1M runbook tells the operator to record something in
    `gne_c2m/DEVIATIONS.md` (lines 15-16); that file does not exist.
