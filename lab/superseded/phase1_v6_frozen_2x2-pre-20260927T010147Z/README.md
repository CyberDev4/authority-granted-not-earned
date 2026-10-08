# V6: frozen 2x2 (competence x pressure)

Built from phase1_fixed_v1 because the V4 source was not available when this was written.
V4's no-remedy incident text is restored. `adapter.py` is byte-identical to V1.
Read PREREGISTRATION.md first. It is the spec, analysis plan and coding rubric.

Files: run.py (runner, batches, probe), analyze.py (preregistered rules), blind_export.py
(coding sheet), test_v6.py (27 tests), adapter.py (unchanged), CHANGES_vs_v1.patch.

Check against your local V4 before freezing:

    diff phase1_fixed_v4_recommendation/adapter.py phase1_v6_frozen_2x2/adapter.py
    diff phase1_fixed_v4_recommendation/run.py phase1_v6_frozen_2x2/run.py

adapter.py should show no difference. In run.py, anything beyond the changes listed in
PREREGISTRATION.md section 2 and 3 (and batch/probe plumbing) is something V4 had that V6 lacks.
Resolve it before the baseline stage, not after.
