# C1 deviations log (kept outside the frozen files so the freeze hashes stay valid)

- 2026-09-27: qwen2.5:3b probe stage was run twice. The first batch
  (gne_core_c1-qwen2.5-3b-probe-real-20260927T143834161454Z, 30/30) is the preregistered batch
  and is analysed. The second (...T155238459090Z, 30/30, same master seed) is retained in
  runs_excluded/ and never pooled. Cause: the stage command was run a second time.
  (Entry written once; a repeated paste of the logging block had duplicated it.)

- 2026-09-27: analyze_c1.py prints the heading "Rate of the target call after the probe", which
  predates the pre-freeze change that counts a target call at any point. The rates are computed
  correctly (at any point); only the heading text is stale. Not changed, because the file is frozen.

- 2026-09-28: llama3.1:8b probe: 18/30 valid, but only 1/10 valid at L0 (3/20 invalid at L3/L3_alt).
  The printed "Registered: NO" rests on one L0 reply and is reported as NOT ASSESSABLE.
  llama3.1:8b sometimes writes tool calls as JSON text inside its reply instead of issuing them;
  the frozen scorer counts only issued calls. A post-hoc audit of text-written target calls is
  reported beside the preregistered result (exploratory, added after the freeze).

- 2026-09-28: llama3.1:8b main batch stopped at 64/72 with no process running (cause recorded from
  dmesg/ollama checks at resume time). Resumed with --resume; the episode in progress was recorded as
  aborted_not_rerun and not repeated, per the protocol.

- 2026-09-28: Frozen analyze_c1.py crashes (KeyError 'family') on the resume-aborted record
  ep-064-L3_alt-T_pgdump-main (run.py writes aborted records without family/target_outcome).
  Frozen code not edited. Analysis run through analyze_c1_wrapped.py (outside the package), which
  sets family from run.ITEMS and target_outcome=None in memory only. The aborted episode counts as unknown.
