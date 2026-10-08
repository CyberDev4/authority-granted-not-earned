# C1 deviations log (kept outside the frozen files so the freeze hashes stay valid)

- 2026-09-27: qwen2.5:3b probe stage was run twice. The first batch
  (gne_core_c1-qwen2.5-3b-probe-real-20260927T143834161454Z, 30/30) is the preregistered batch
  and is analysed. The second (...T155238459090Z, 30/30, same master seed) is retained in
  runs_excluded/ and never pooled. Cause: the stage command was run a second time.
  (Entry written once; a repeated paste of the logging block had duplicated it.)
