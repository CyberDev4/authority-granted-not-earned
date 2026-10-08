
## 2026-10-01: controls batch lost to an Ollama out-of-memory kill; excluded and restarted

- **What happened:** C5 was frozen at 07:25:13 UTC. gpt-oss:20b (about 14 GB) was still loaded from C4G
  when the controls stage started loading qwen2.5:7b. At 12:58:59 IST (07:28:59 UTC) the kernel's
  out-of-memory killer stopped the Ollama service (journal: "Failed with result 'oom-kill'"). All 12
  control requests got "Connection refused" and were recorded as interface_failure. The probe and main
  stages did not start.
- **Evidence that no model output exists:** the batch contains no response files (0 response-*.json).
- **Change:** the batch gne_c5-qwen2.5-7b-controls-real-20261001T072513769179Z was moved, unchanged, to
  runs_excluded/ (kept for transparency, as with C1's duplicate batches) and C5 was started again from
  the controls stage, with no model loaded beforehand. No package file changed; the freeze stands.
- **Prevention:** before each study, `ollama ps` must show no loaded model.
