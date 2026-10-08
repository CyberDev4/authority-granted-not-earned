# V7: V6 with a 600 s request timeout

Identical stimuli to phase1_v6_frozen_2x2 (pinned by tests 28-29). Only change: request timeout
180 s -> 600 s, plus a per-cell failure breakdown in analyze.py. See PREREGISTRATION.md section 0.

Files: run.py, analyze.py, blind_export.py, test_v7.py (34 tests), adapter.py (unchanged since V1).
