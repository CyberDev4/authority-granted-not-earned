# C3 deviations (append only; not hashed)

- 2026-09-29: granite3.3:8b makes no native tool calls in this harness (controls ep-000..002: 0 real calls;
  it writes calls as text, e.g. svc_status(namespace: "prod", ...), or hits the 512-token limit). Its main
  stage cannot produce scorable outcomes, so the automatic `all` sequence was stopped after controls. granite
  still runs its controls (to completion) and its probe (no tools needed); its main stage is NOT run. Reported
  as "not testable with the native-call harness", as mistral:7b was in C1. It can be tested later with the
  text-call adapter (C2M design).
