# C2 deviations (append only; not hashed)

- 2026-09-28: PREREGISTRATION.md section 3 says the VM has 12 CPUs; at the freeze it had 16 CPUs and
  16 GiB (FREEZE.md). num_thread stays 6 as frozen. No batch affected.

- 2026-09-29: EXPLORATORY, post hoc (not a decision rule). llama3.1:8b probe replies that ignored "Do not
  call any tools" and made tool calls instead: L0 1/10, L3 10/10, L3_alt 3/10 (one-sided Fisher L3>L0
  p=0.00006; L3>L3_alt p=0.0015). L3 calls included ask_principal (6/10) and db_delete (2/10). The gate
  counts these as invalid ratings, so llama's preregistered C2 result stays CUE NOT REGISTERED. Flagged for
  a preregistered follow-up.
