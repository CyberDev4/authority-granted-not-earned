# C1M deviations (append only; not hashed)

- 2026-09-29: main batch gne_c1m-mistral-7b-main-real-20260928T224101229319Z stopped at 40/72 when the VM
  shut down uncleanly (last write 12:30, VM boot 12:38 local; ep-040 left response-01.json and
  request-02.json empty). All 40 finished episode.json files verified as valid JSON. Resumed with
  --resume; ep-040 recorded as aborted_not_rerun per protocol.

- 2026-09-29: the first resume (started 15:32 IST) stopped silently at 15:37 during ep-041 (no traceback;
  process gone). ep-041 has request-00/01 and response-00 only. Resumed again, detached from the terminal
  session (setsid); ep-041 recorded as aborted_not_rerun per protocol.
