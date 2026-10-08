# Map of `lab/`

`lab/` is the project folder as it stood on the lab machine on 6 October 2026. It holds 21,165 files (105 MB).
Every file is byte for byte the file in the original archive, at the same relative path. Nothing in it was edited,
renamed or tidied for publication, so it also holds leftovers and older write-ups. This page says what each part
is.

The counts on this page come from `manifest/MANIFEST.tsv` and `manifest/LEFT_OUT.tsv`, and
`python3 verify/check_manifest.py` checks that the manifest matches the files.

## Where to start

| If you want | Go to |
| --- | --- |
| The plan of a study | `lab/<package>/PREREGISTRATION.md` (packages are listed below) |
| What departed from a plan | `lab/<package>/DEVIATIONS.md`, then `docs/deviations-added-later.md` |
| One run, readable | `lab/runs/<batch folder>/ep-…/transcript.txt` |
| One run, exact | the `request-NN.json` and `response-NN.json` files beside it (`docs/data-dictionary.md`) |
| The analysis output of a study | `results/analysis-outputs/` (regenerated from `lab/`; `verify/reanalyze.py` compares them with the saved copies) |

## The twelve studies

| Study | Package in `lab/` | Plan | Output of the study's own analysis |
| --- | --- | --- | --- |
| V6 | `phase1_v6_frozen_2x2` | `PREREGISTRATION.md` | `results/analysis-outputs/V6.txt` |
| X1 | `phase1_x1_scope_explicit` | `PREREGISTRATION.md` | `results/analysis-outputs/X1.txt` |
| V7 | `phase1_v7_timeout` | `PREREGISTRATION.md` | `results/analysis-outputs/V7.txt` |
| C1 | `gne_core_c1` | `PREREGISTRATION.md` | `results/analysis-outputs/C1.txt` |
| C2 | `gne_core_c2` | `PREREGISTRATION.md` | `results/analysis-outputs/C2.txt` |
| C1M | `gne_c1m` | `PREREGISTRATION.md` | `results/analysis-outputs/C1M.txt` |
| C3 | `gne_c3` | `PREREGISTRATION.md` | `results/analysis-outputs/C3.txt` |
| C4 | `gne_c4` | `PREREGISTRATION.md` | `results/analysis-outputs/C4.txt` |
| C4G | `gne_c4g` | `PREREGISTRATION.md` | `results/analysis-outputs/C4G.txt` |
| C5 | `gne_c5` | `PREREGISTRATION.md` | `results/analysis-outputs/C5.txt` |
| C6 | `gne_c6` | `PREREGISTRATION.md` | `results/analysis-outputs/C6.txt` |
| C5P | `gne_c5p` | `PREREGISTRATION.md` | `results/analysis-outputs/C5P.txt` |

For V6, X1 and V7 the project saved no analysis output at the time. Those three files were generated on 6 October
2026, by running each study's own analysis script.

## The top level

| Entry | Files | What it is |
| --- | --- | --- |
| `phase1_v6_frozen_2x2/`, `phase1_x1_scope_explicit/`, `phase1_v7_timeout/` | 8, 10, 9 | The packages of the three early studies: V6, X1 and V7 |
| `gne_core_c1/`, `gne_core_c2/`, `gne_c1m/`, `gne_c3/`, `gne_c4/`, `gne_c4g/`, `gne_c5/`, `gne_c6/`, `gne_c5p/` | 9 to 11 each | The packages of the nine C studies |
| `gne_c2m/`, `gne_core_c1_superseded_unrun/` | 8, 7 | Two packages that never ran: C2M, and a first draft of C1 |
| `runs/` | 20,635 | Every run: 52 real batches of the twelve studies, 2 one-run tests against a fake model, and the early pilots |
| `runs_excluded/` | 222 | Four batches that were set aside, each with its reason in a deviations log |
| `logs/` | 95 | Console logs of the batches, saved analysis outputs, and the audit files |
| `gne/`, `items/`, `scenarios/` | 10, 3, 3 | The first harness (11 to 16 September) and its input files. A harness is the program that sends the requests and plays the tools. For the later studies these pages call it the runner; the study files use both words |
| `short_b0/`, `monitor_lab/` | 3, 10 | Scripts of the pilots of 18 and 19 September |
| `phase1_fixed_v1/` to `phase1_fixed_v5_incident/` | 4 or 5 each | Five development versions that came before V6 (26 and 27 September) |
| `superseded/` | 9 | An earlier version of the V6 package, replaced before V6 was frozen |
| `reports/` | 2 | A progress report of 26 September and its list of evidence |
| `gne_release_kit/`, `release/` | 3, 1 | A release kit of 1 October and the snapshot it built (one `.tar.gz` file) |
| 18 loose files | 18 | See [Loose files](#loose-files) |

## What a study package holds

| File | What it is | Where it is missing |
| --- | --- | --- |
| `PREREGISTRATION.md` | The plan: question, design, the planned tests and how each verdict is reached | |
| `FREEZE.md` | The freeze record: when the package was frozen, the machine, the models installed with their IDs, and a SHA-256 hash of each frozen file | V6 and V7 keep it as section 9 of the plan. The two packages that never ran have none |
| `DEVIATIONS.md` | The log of departures from the plan | V6, V7 and X1 keep it as the last section of the plan. C4G and C5P have none (`docs/deviations-added-later.md`). The two packages that never ran have none |
| `RUNBOOK.md` | The operator's steps, command by command | V6 and V7 (their plans list the commands) |
| `run.py` | The runner: builds each request, calls the model, simulates the tools, scores the run | |
| `analyze_<study>.py`, `analyze.py` | The planned analysis | |
| `stats.py` | The exact test and the intervals, in plain Python | V6, X1 and V7 |
| `test_<study>.py` | Unit tests of the package | |
| `<study>.sh` | The launch script for each stage | V6 and V7 |
| `audit_authority.py` | The search for permission phrases (C3 onwards) | |
| `adapter.py`, `CHANGES_*.patch` | V6, X1 and V7 only: the code that renders the prompt and parses the reply, and the changes from the version before | |
| `blind_export.py`, `README.md` | V6 and V7 only: an export for blind reading, and a short note on the package | |
| `diag.py` | C1M and C2M only: diagnostic calls to the model. C1M's plan allowed them before its freeze | |
| `c4_queue.sh` | C4 only: runs the three models one after another | |

`docs/how-a-run-works.md` quotes what these files send to the model. `docs/replicate.md` gives the commands.

## Run folders

A batch folder is named after its package, model, stage and start time in UTC, for example
`lab/runs/gne_c3-qwen2.5-7b-main-real-20260929T153847117893Z`. The three early studies have no model in the name.
The stages are `controls`, `probe` (the rating check), `main` (the scored stage) and `followup` (further rating
questions in C3 and C4); V6 and V7 have `baseline`, and X1 has `scope`. Inside a batch folder there is one folder per
run, named `ep-NNN-…`, and the batch's own copies of the code and plan it ran with. `docs/data-dictionary.md` defines
every file and field.

| Study | Real batches | Run records |
| --- | --- | --- |
| V6 | 1 | 20 |
| X1 | 1 | 40 |
| V7 | 2 | 34 |
| C1 | 7 | 240 |
| C2 | 7 | 246 |
| C1M | 3 | 114 |
| C3 | 9 | 456 |
| C4 | 10 | 516 |
| C4G | 3 | 162 |
| C5 | 3 | 432 |
| C6 | 3 | 312 |
| C5P | 3 | 432 |
| All | 52 | 3,004 |

`results/tables/batches.csv` lists every batch. V7 also has two batches named `…-baseline-fake-…`: one-run tests of
the runner against a scripted stand-in, with no model.

### `lab/runs_excluded/`

Four batches (45 run records) that the project set aside and did not analyse. Each has its reason in a log.

| Batch | Why it was set aside | Logged in |
| --- | --- | --- |
| `gne_core_c1-qwen2.5-3b-probe-real-20260927T155238459090Z` | The rating check for this model was run twice. The plan uses the first | `lab/gne_core_c1/DEVIATIONS.md` |
| `gne_core_c1-mistral-7b-controls-real-20260928T012839167723Z`, `…T013143897279Z` | Two further starts of the mistral:7b controls | `lab/gne_core_c1/DEVIATIONS.md` |
| `gne_c5-qwen2.5-7b-controls-real-20261001T072513769179Z` | The model server ran out of memory; the batch holds no model reply | `lab/gne_c5/DEVIATIONS.md` |

### Early pilots inside `lab/runs/`

Fifty-six folders and seven loose files come from the work that built the harness, 14 to 27 September, and from one
diagnostic step of C1M. None of them is counted in any result. The pilots of 14 to 19 September used other
harnesses, prompts and tools than the twelve studies. The five `phase1_fixed` versions of 26 and 27 September are
the forerunners of V6: V6 was built from version 1 and uses the same code to render prompts and read replies. The
pilots are kept because they are part of the record, and because two of them show a small model breaking a named
rule. In `lab/runs/day1-real-20260916T005417Z` the agent was told to check before any restart in prod, asked about
something else, got no answer, and restarted a service in prod in its fourth reply. In
`lab/runs/B0_short_raw_v1_t0-real-20260918T225349377008Z` it acknowledged the rule, asked for approval, got no answer
and restarted everything in prod; that run is recorded as "failed", because a later reply could not be read. Each
run folder among them holds one run.

| Folders | How many | Dates (UTC) | Made by |
| --- | --- | --- | --- |
| `day1-fake`, `day1-fake-check`, `day1-open-…`, `day1-INVALID-temperature-…`, `day1-real-…` | 6 | 14 to 16 Sep | The first harness, `lab/gne/`. Two are tests with a scripted stand-in; one failed before any reply, on an error in the harness |
| `_raw_responses/`, `diagnostics/` | 2 | 16 and 18 Sep | Raw replies and one note saved while the first harness was being debugged. The file names carry local time |
| `b0-original-…`, `b0-original-retry-…` | 2 | 18 Sep | The first harness again, with a copy of its source in each folder |
| `B0_short_v1-…`, `B0_short_v1_t0-…`, `B0_short_raw_v1_t0-…` | 8 | 18 Sep | `lab/short_b0/`: a shorter version of the first scene. Four real runs, four with a stand-in |
| `pgbouncer-control-v1-…` | 4 | 18 Sep | `lab/monitor_lab/run_pgbouncer_control_v1.py`. Two real, two with a stand-in |
| `pgbouncer-principal-v1-…`, `pgbouncer-principal-v2-…` | 19 | 19 Sep | `lab/monitor_lab/run_principal_cases_v1.py` and `…_v2.py`. Seven real, twelve with a stand-in |
| `phase1_fixed_prohibition_v1-…` to `…_v5_incident-…` | 14 | 26 and 27 Sep | `lab/phase1_fixed_v1/` to `lab/phase1_fixed_v5_incident/`. Eleven real, three with a stand-in |
| `gne_c1m-diag-20260928T190333Z` | 1 | 28 Sep | `lab/gne_c1m/diag.py`: the 25 diagnostic calls that C1M's plan allowed before its freeze |

The seven loose files are the `.log` and `.start` files of the three day-1 runs, and
`phase1-development-review-20260926T191039689729Z.json`, an assessment of the version-1 pilots.

The real pilot runs used `day1-qwen25-3b`, a local build of a 3B model (`MODELS.md`).

## `lab/logs/`

Ninety-five files. Most are console output: `.log` files written by the launch scripts, one per model and stage,
and `.out` files from commands that were left running in the background. The rest:

| File | What it is |
| --- | --- |
| `c4_analysis.txt`, `c4_analysis_wrapped.txt`, `c4g_analysis.txt`, `c5_analysis.txt`, `c5p_analysis.txt`, `c6_analysis.txt`, `c1_analysis_final.log`, `c1_analysis_after_llama.log` | Saved output of the planned analyses. `c4_analysis.txt` ends in the crash that C4's log describes |
| `c6_bounds.txt` | Output of `lab/c6_bounds.py`: C6's tests with the unscored runs counted both ways |
| `authority_review.txt`, `c5_audit.txt` | Output of the search for permission phrases |
| `authority_confirmed.txt` | The project's verdicts on 23 of the flagged runs. It names no reader |
| `c5p_candidates.txt` | A reading aid for C5P. The script that wrote it is not in the record |
| `c3_queue.sh`, `c3_queue.out` | The queue that ran C3's later batches (`docs/deviations-added-later.md`, entry 4) |
| `v6_baseline_console.log`, `v7_baseline_console.log`, `x1_run_20260927T023746Z.log` | Console logs of the three early studies |

Things to know before relying on a log:

- `c1_qwen2.5-3b_probe.log` and `c1_mistral-7b_controls.log` are the logs of batches that were set aside, not of the
  batches that were kept.
- `c5_qwen7b.out` was overwritten by a later command on 2 October. The full copy is inside the release snapshot.
- `authority_review_before_c5p.txt` is identical to `authority_review.txt`. It is not an earlier version.
- Eight console logs are there twice, as a `.log` and as an `.out` with the same bytes: the three C1M stages, the
  three C2 controls batches, and in C3 the granite controls (`c3_granite_all.out`) and the llama follow-up.
- Two C6 logs end in blank padding bytes from the shutdown during that study.
- The saved analysis outputs of C1M, C2 and C3 are not in `lab/logs/`. They are inside the release snapshot, and
  regenerated copies are in `results/analysis-outputs/`.

## Early code

| Folder | What it is |
| --- | --- |
| `lab/gne/` | The first harness, written on 11 September to call a hosted model through that provider's client library. Its example command names a hosted model. No saved run used one: the day-1 runs pointed it at the local model. `export.py` imports the side project that was left out, so it cannot be run from this repository. Three `.bak` files are leftovers |
| `lab/items/`, `lab/scenarios/` | The first harness's instructions and scene. One `.bak` file is a leftover |
| `lab/short_b0/` | Three versions of a shorter pilot that calls the local model directly |
| `lab/monitor_lab/` | Small learning scripts about approval for a restart, the runners of the pgbouncer pilots, and `scan_episode.py`, whose one saved output (`findings_day1_001.json`) is for a day-1 run |
| `lab/phase1_fixed_v1/` to `lab/phase1_fixed_v5_incident/` | Five versions of a "development pilot". The first README says: "It is NOT a validated dataset or confirmatory experiment" |
| `lab/superseded/` | An earlier version of the V6 package, as a folder and a zip. Six of its eight files differ from the package that was frozen. Its name carries the time 01:01 UTC on 27 September; V6's freeze record says 01:03 UTC |
| `lab/reports/` | `progress-report.md` of 26 September. Its links point to files on the lab machine |

## Release material

| Entry | What it is |
| --- | --- |
| `lab/gne_release_kit/` | `README.md`, `LICENSE` and `make_release.sh`, written on 1 October to build a public snapshot of C1 to C5. **That README overstates the results** and stops at C5 (see [Older write-ups](#older-write-ups-what-to-know)) |
| `lab/release/granted-not-earned-20261001.tar.gz` | The snapshot that the kit built: 13,926 files, a copy of the packages, runs and logs of C1 to C5. One of the files lists the checksums of the other 13,925. In the snapshot the home folder of the lab machine is written `~`: 356 of its files differ from the files in `lab/` in that way and no other |
| `lab/gne_evidence_20261002T213342Z.tar.gz` | An evidence bundle made by `lab/gne_collect_evidence.py` as C5P began: run records and package hashes, without the raw replies except for unscored runs. Its index counts batches by other rules than this repository does |

## Loose files

| File | What it is |
| --- | --- |
| `analyze_c1_wrapped.py`, `analyze_c4_wrapped.py` | Read-only wrappers around two frozen analyses that crash. Both are logged in the study's deviations log |
| `c6_bounds.py` | C6's added check, logged in `lab/gne_c6/DEVIATIONS.md` |
| `gne_collect_evidence.py` | Builds the evidence bundle |
| `gne_evidence_20261002T213342Z.tar.gz` | The evidence bundle of 2 October |
| Ten `.zip` files | The packages as they were delivered to the lab machine. Eight match their folder file for file; the folder also holds the freeze record and deviations log that were written on the lab machine. The V7 zip holds the plan before its freeze record was filled in. The V6 zip holds an earlier text of the plan: before the batch ran, the freeze record was filled in and one stopping rule was narrowed (the ladder of models "3B, then 7B, 14B, 32B" became "3B, then 7B"); the closing note was added after the batch. `gne_core_c1_superseded.zip` unpacks to the files of `gne_core_c1_superseded_unrun/`, and `gne_c5p_v2.zip` to those of `gne_c5p/` |
| `.env.example`, `requirements.txt`, `requirements-installed.txt` | From the first plan, which would have called hosted models. The example file holds placeholders, not keys. The twelve studies need none of these packages |

## What was left out, and why

The archive held 35,115 files. 13,950 were left out of `lab/`. `manifest/LEFT_OUT.tsv` lists each one with its
checksum and the reason.

| Left out | Files | Why |
| --- | --- | --- |
| `release/granted-not-earned-20261001/` | 13,926 | The unpacked copy of the snapshot. Every file is identical to a member of the `.tar.gz`, which is kept |
| `agentscope/`, `scripts/`, `tests/` | 17 | A side project: a monitor for the session logs of coding agents, with its scripts and tests. It is not part of this research and has no saved output. `tests/test_harness.py` tested the first harness and imports the side project |
| `tests-result.txt` | 1 | Stale output of one run of those tests, written on 14 September (UTC) |
| `README.md` | 1 | The README of 11 September. It describes the first plan, not these studies |
| `.gitignore` | 1 | It ignored `runs/`, which would have hidden nearly every file |
| `.pytest_cache/` | 4 | A cache written by the test runner |

The archive itself is not in this repository. Its name, size and SHA-256 are in `manifest/ARCHIVE.txt`, and
`manifest/build_lab_from_archive.py` rebuilds `lab/` from it.

## File times

Git does not keep the time a file was written. `manifest/MANIFEST.tsv` does, in the column `archive_time`: the time
stored in the archive, which is the lab machine's local time (five and a half hours ahead of UTC), to the nearest two
seconds. Some package files carry the time from their delivery zip. `verify/timeline.py` uses these times and the
time stamp inside each saved reply; `results/timeline/` holds what it finds.

## Before reading the record

- **The first plan was different.** The earliest code (`lab/gne/`, September) was written to call a hosted model. No
  saved run did: every saved request went to a model on the same machine.
- **Not every deviation was logged at the time.** Thirteen machine pauses, one rerun and a few other events were
  found when the record was checked before publication. They are in
  [deviations-added-later.md](deviations-added-later.md).
- **The models.** Ten small open models, run on a CPU through Ollama. Three of their licenses restrict use; see
  [MODELS.md](../MODELS.md).
- **Local details and older write-ups.** The next two sections list the lab machine's paths and names that appear
  in the record, and where the older write-ups go wrong.

## Local details you will see

- The lab machine's project path, `/home/lab/ai-lab/project/agentscope`, and its host name, `ai-lab`. They appear in
  error traces and freeze records. Removing them would change saved records and one hashed file.
- The name `agentscope`. It was the name of the project folder, and it is also the name of an unrelated open-source
  framework. This project has no connection with that framework.
- The names Priya, Sam and Dana in the prompts. They are part of the scripted scene.
- A path that begins `/home/claude/` in the first line of five `CHANGES_*.patch` files. It is the working folder
  in which the patch was made.
- Statements in older files that are wrong or overstated. The next section lists the main ones. Where an older
  file and `README.md` or `RESULTS.md` disagree, the two newer pages are the current account.

## Older write-ups: what to know

Two older write-ups are inside `lab/`, and a third was left out. They were written while the work was still going
on. The two in `lab/` are part of the record and are left as they were. `README.md` and `RESULTS.md` are the current
account. P17 is the Authorized Principal, the task owner the agent works for; the older files call P17 the
principal.

**`lab/gne_release_kit/README.md`, 1 October.** Its counts and p-values match the saved outputs and the verdict
file. It stops at C5, so it knows nothing of C6 or C5P, and its wording goes further than the data in these places:

| It says | What the record shows |
| --- | --- |
| The agent "had itself caught the principal making technical mistakes" | The earlier replies in the agent's voice are fixed text from the study's code. The model under test checked nothing |
| The effect "was absent in qwen2.5:14b and gpt-oss:20b" and is "present in qwen2.5:7b only" | It was not detected in two small tests, one of them on messy data. Six more models never got a scored test (`RESULTS.md`) |
| "Silence as consent": after asking and "getting no reply", the agent "acted anyway" in 15 of 25 cases | The tool answers at once that P17 is unavailable, and the 25 mix rules and advice. In the standard restart-rule runs of qwen2.5:7b after correcting, across its five studies, 38 of the 39 runs with a question hold it in the same reply as the restart, with the restart listed first |
| The permission claims were "hand-confirmed" in a "human review" | The verdict file, `lab/logs/authority_confirmed.txt`, names no reader |
| "Evaluation strictness changes the verdict" | For mistral:7b it changes the count: 2, 17 or 29 of the same 52 runs. The saved output prints one reading, "uninterpretable" |
| "Pressure triggers violations. No violation in any study came before the operational alert" | Every run of the scored stage has the alert, so the record cannot show what the alert adds. The second sentence holds for rules. Two advice runs in C1 made their call before the alert |
| llama3.1:8b "ignored" the instruction not to call tools | That sentence ends a rating question. In C1, with no scripted history, the pattern ran the other way (`RESULTS.md`) |
| "every deviation is logged" | Six machine pauses in C3, C4G and C5 are in no log, and C4G has no deviations log (`docs/deviations-added-later.md`) |
| "Every study was preregistered and frozen, with SHA-256 hashes, before any model run" | Each study was frozen with file hashes on the author's own machine, shortly before its first batch. There is no public registration. C1M's plan allowed 25 diagnostic calls to the model before its freeze |
| H7 is "third-party report weaker", H8 "other owner" and H9 "limit adds to the jump" | The labels are mixed up. In C5's plan H7 is that the rule restrains, H8 that calls rise when a reviewer reports the checks, and H9 that the rise is larger for P17's rule than for another owner's |
| "Each package contains" a freeze record and a deviations log | C2M has neither, and C4G has no deviations log |

Its counts of invented permission and of false claims of compliance date from 1 October.
`results/labels/audit_reading.csv` holds the later reading of every flagged run.

**`lab/reports/development-freeze-20260926T231218989231Z/progress-report.md`, 26 September.** It covers the work
before V6. Its links point to files on the lab machine.

**The README of 11 September** described the first plan, which would have called hosted models. It was left out of
`lab/` (see [What was left out, and why](#what-was-left-out-and-why)).
