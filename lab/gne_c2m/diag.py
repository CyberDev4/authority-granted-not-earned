"""C2M step 0 diagnostic: can mistral:7b make NATIVE tool calls through Ollama at all, and when?

Descriptive only, run before the freeze. It does not score anything and does not change the design.
Writes runs/gne_c2m-diag-<stamp>/diag.json and prints a summary table.

Usage: python gne_c2m/diag.py --model mistral:7b [--reps 5] [--ollama http://127.0.0.1:11434]
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, ProxyHandler, build_opener

import run

MINIMAL = [{"role": "user", "content": "Check the status of the service pgbouncer in the namespace prod."}]
ONE_TOOL = [t for t in run.TOOLS if t["function"]["name"] == "svc_status"]


def configs():
    full = run.initial_messages("none", "S_restart", "control")
    return [
        ("D1 minimal ask, 1 tool, temp 0", MINIMAL, ONE_TOOL, 0.0),
        ("D2 minimal ask, all 8 tools, temp 0", MINIMAL, run.TOOLS, 0.0),
        ("D3 full C2 control prompt, temp 0", full, run.TOOLS, 0.0),
        ("D4 full C2 control prompt, temp 0.7 (C2 setting)", full, run.TOOLS, 0.7),
        ("D5 full prompt, no system message, temp 0.7", full[1:], run.TOOLS, 0.7),
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--ollama", default=run.DEFAULT_OLLAMA)
    a = ap.parse_args()
    opener = build_opener(ProxyHandler({}))
    show = json.load(opener.open(Request(a.ollama + "/api/show", data=json.dumps({"model": a.model}).encode(),
                                         headers={"Content-Type": "application/json"}, method="POST"), timeout=60))
    template = show.get("template", "")
    info = {"model": a.model, "capabilities": show.get("capabilities"),
            "template_mentions_tools": ".Tools" in template or "AVAILABLE_TOOLS" in template,
            "template_mentions_TOOL_CALLS": "TOOL_CALLS" in template, "results": []}
    print("Model %s | capabilities %s | template has tools block: %s | has [TOOL_CALLS]: %s" % (
        a.model, info["capabilities"], info["template_mentions_tools"], info["template_mentions_TOOL_CALLS"]))
    for label, messages, tools, temp in configs():
        native = text = 0
        for rep in range(a.reps):
            options = dict(run.BASE_OPTIONS, temperature=temp, seed=1000 + rep)
            payload = {"model": a.model, "messages": messages, "tools": tools, "stream": False,
                       "keep_alive": run.KEEP_ALIVE, "options": options}
            req = Request(a.ollama + "/api/chat", data=json.dumps(payload).encode(),
                          headers={"Content-Type": "application/json"}, method="POST")
            out = json.load(opener.open(req, timeout=run.REQUEST_TIMEOUT_SECONDS))
            msg = out.get("message") or {}
            n_native = len(msg.get("tool_calls") or [])
            written = run.parse_text_calls(msg.get("content", ""))
            native += n_native > 0
            text += n_native == 0 and any(w["valid"] for w in written)
            info["results"].append({"config": label, "rep": rep, "native_calls": msg.get("tool_calls"),
                                    "content_head": (msg.get("content") or "")[:300],
                                    "written": written, "done_reason": out.get("done_reason")})
        print("  %-50s native %d/%d | valid text call only %d/%d" % (label, native, a.reps, text, a.reps))
    out_dir = Path("runs") / ("gne_c2m-diag-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    out_dir.mkdir(parents=True)
    (out_dir / "diag.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print("Saved:", out_dir / "diag.json")


if __name__ == "__main__":
    main()
