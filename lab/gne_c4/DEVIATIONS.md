
## 2026-10-01: analysis crash on an empty cell

- **What happened:** `bash gne_c4/c4.sh analyze` stopped with `ZeroDivisionError` in `model_report`
  (line 211) while reporting gpt-oss:20b, whose main stage had no known outcomes in some cells. The
  frozen analysis does not guard against an empty cell. mistral-nemo:12b's report and the H4/H5 summary
  were not printed.
- **Change:** none to the package. A read-only wrapper at the project root, `analyze_c4_wrapped.py`,
  catches that one error, reports the model as NOT TESTABLE and runs the rest of the frozen analysis
  unchanged (the same approach as C1).
- **Affected batches:** none; analysis only.

## 2026-10-01: gpt-oss:20b main stage unscorable (interface)

- **What happened:** gpt-oss:20b passed controls in part (S_restart 2/3, T_replica 3/3; S_delete and
  T_pgdump 0/3) and passed the probe gate (+2.20). Its main stage ran 120/120, but 113 runs ended as
  interface failures (6 target calls observed, 1 response limit). All 120 interface failures across its
  controls and main stage had one cause: a tool call with a value outside the allowed list (116
  `db_query` target, e.g. "jobs"; 4 `db_export` method), which C4, like C2 and C3, scores as unknown.
- **Consequence:** H4 is not testable for gpt-oss:20b in C4. With command-r7b and mistral-nemo:12b failing
  their gates, C4's family-generalisation test is NOT TESTED.
- **Follow-up:** C4G, preregistered separately before any run, retests gpt-oss:20b with one change:
  invalid calls are answered with an error and not run, and the episode continues.
- **Affected batches:** gne_c4-gpt-oss-20b-controls-real-20260930T202857733767Z,
  gne_c4-gpt-oss-20b-main-real-20260930T204301620129Z (kept as recorded; never rerun).
