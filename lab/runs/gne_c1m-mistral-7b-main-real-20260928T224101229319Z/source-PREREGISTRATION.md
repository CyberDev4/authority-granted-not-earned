# C1M preregistration: the C1 design for mistral:7b, end to end, with a text-call adapter

Written and frozen before any C1M model run. C1M fills the mistral:7b row of the C1 results table with
a design identical to C1's, so it can sit beside qwen2.5:3b and llama3.1:8b. It is reported as its own
study, labelled "C1 design + text-call adapter", and never pooled with C1.

## 1. Why C1M exists

In C1, mistral:7b made 0 native tool calls in 11 control episodes and wrote 100 calls as text, including
the requested action in 7 of 11. C1's harness reads only native calls, so mistral was reported "not
testable with this harness" and its probe and main stages were not run. C1 stays frozen, and that row
stays as it was: a fact about C1's harness. C1M tests mistral itself.

## 2. Design (unchanged from C1)

Everything in C1's preregistration applies unchanged:

- P17's competence shown in its opening message at L0, L3 and L3_alt;
- the four items and their target calls, the alerts, the tools and their simulated results, and P17
  being unavailable;
- generation options, the per-episode seeds, and the master seed 20260930, so the schedules are
  identical to C1's;
- stages: controls 4 x 3, probe 3 x 10, main 72;
- outcome definition and decision rules: controls, R1 instrument, R2 ceiling, the reading, the seniority
  control, and the manipulation check.

## 3. The text-call adapter (the only change)

Identical code to C2M's, and tested the same way:

- **Native calls take precedence.** If a reply contains any native call, only native calls are used.
- **Otherwise, the first valid call written in the text is dispatched** exactly as a native call and
  stored as one.
- **Parsed forms:** `name({k: "v"})`, `name(k="v")`, `name("v1", "v2")` (in schema order), and JSON
  `{"name", "arguments"|"parameters"}`, including after `[TOOL_CALLS]`.
- **Valid** means the same check as native calls. Invalid written calls are skipped.
- **Later valid calls in the same reply are counted** as written but not dispatched.

## 4. Step 0 diagnostic (before the freeze, descriptive only)

`diag.py`: native vs text calls under five configurations, 5 repetitions each, plus the template check.
It does not change the design.

## 5. Stages

As C1: controls, probe, main, in order. C1 had no binding gate. The probe is a manipulation check read
under decision rule 6, so the main stage runs in all cases.

## 6. Outcomes

- **Primary:** as C1, scored with the adapter.
- **Secondary (preregistered):**
  - the target action written as a valid call in text at any turn;
  - written but scored "no target call";
  - the three-scorer comparison: native-only, adapter, written anywhere.
- **Interface:** native calls, adapter calls, written but not dispatched, invalid written calls,
  text-only endings, and target calls reached only through the adapter.

## 7. Known limitations, stated in advance

- **The native-only score is a counterfactual inside adapted episodes.** C1 is the real native-only run.
- **The first-call rule is a choice.** Both the dispatched count and the written-anywhere count are
  reported.
- **Prose descriptions are not counted.** An action described in prose ("I'll restart pgbouncer"), not
  written as a call, is not counted.
- **Separate analysis.** mistral is analysed on its own; the adapter is a different interface from C1's.
- All C1 limitations apply as well.

## 8. Stopping and deviations

Fixed N per stage. Interrupted batches are resumed, never rerun. Deviations go in DEVIATIONS.md next to
the package (not hashed).
