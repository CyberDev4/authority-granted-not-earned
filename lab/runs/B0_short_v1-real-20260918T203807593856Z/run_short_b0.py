"""Separate short B0 pilot. Uses simulated GNE tools and local Ollama only."""
import argparse
import copy
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, ProxyHandler, build_opener


def experiment(env, scenario, item, opening, schemas, respond):
    """Fixed delivery order; maximum six model turns; no compaction/handoff."""
    messages = [
        {"role": "system", "content": scenario["system"]},
        {"role": "user", "content": opening},
    ]
    allowed = {s["name"]: s["input_schema"] for s in schemas}
    ending = "turn_limit"
    try:
        for turn in range(6):
            env.step = turn
            if turn == 1:
                env.queue_principal_message(item["text"], label="grant")
                while env.pending_user_text:
                    messages.append({"role": "user", "content": env.pending_user_text.pop(0)})
            if turn == 2:
                messages.append({"role": "user", "content": env.activate_probe(via="scheduled")})

            response = respond(copy.deepcopy(messages), turn)
            if response.get("done") is not True or response.get("done_reason") != "stop":
                raise ValueError("Generation did not finish normally; see saved response")
            message = response.get("message") or {}
            text = message.get("content") or ""
            calls = message.get("tool_calls") or []
            if not text.strip() and not calls:
                raise ValueError("Empty response; no retry performed")
            if message.get("thinking"):
                raise ValueError("Unexpected thinking output in this non-thinking-model pilot")
            messages.append({"role": "assistant", "content": text, "tool_calls": calls})

            # Validate all calls before dispatching any from this response.
            for call in calls:
                function = call.get("function", {})
                name, args = function.get("name"), function.get("arguments")
                if name not in allowed or not isinstance(args, dict):
                    raise ValueError("Unknown tool or malformed arguments")
                schema = allowed[name]
                if any(k not in args for k in schema.get("required", [])):
                    raise ValueError("Missing required tool argument")
                if any(k not in schema["properties"] or not isinstance(v, str)
                       for k, v in args.items()):
                    raise ValueError("Unexpected argument or non-string argument")
            for call in calls:
                function = call["function"]
                result = env.dispatch(function["name"], function["arguments"])
                messages.append({"role": "tool", "tool_name": function["name"],
                                 "content": result})

            # A text-only answer before turn 2 cannot skip the planned messages.
            if turn >= 2 and not calls:
                ending = "post_probe_text_response"
                break
    except Exception:
        return messages, "failed", traceback.format_exc()
    return messages, ending, None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fake", action="store_true")
    mode.add_argument("--real", action="store_true")
    parser.add_argument("--model", default="day1-qwen25-3b")
    opts = parser.parse_args()
    root = Path.cwd()
    if not (root / "gne/env.py").exists():
        parser.error("Run from ~/ai-lab/project/agentscope")
    sys.path.insert(0, str(root))
    from gne.env import Environment, TOOL_SCHEMAS
    from gne.grade import grade, args_match

    scenario = json.loads((root / "scenarios/backlog_cleanup.json").read_text())
    competence = json.loads((root / "items/competence.json").read_text())
    item = next(i for i in json.loads((root / "items/scope.json").read_text())
                if i["id"] == "scope_prod_restart")
    opening = scenario["opening"] + "\n\n" + " ".join(competence["L0"])
    label = "fake" if opts.fake else "real"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = root / "runs" / f"B0_short_v1-{label}-{stamp}"
    out.mkdir(parents=True, exist_ok=False)

    def save(name, data):
        (out / name).write_text(json.dumps(data, indent=2), encoding="utf-8")

    for name in ("gne/env.py", "gne/grade.py", "scenarios/backlog_cleanup.json",
                 "items/competence.json", "items/scope.json"):
        destination = out / "source" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((root / name).read_bytes())
    (out / "run_short_b0.py").write_bytes(Path(__file__).read_bytes())
    config = {"protocol": "B0_short_v1", "mode": label, "model": opts.model,
              "competence": "L0", "item": item["id"], "grant_turn": 1,
              "probe_turn": 2, "max_turns": 6, "temperature": 1.0,
              "num_ctx": 16384, "num_predict": 1024, "num_thread": 2,
              "endpoint": "http://127.0.0.1:11434/api/chat",
              "compaction": False, "handoff": False, "awareness_question": False,
              "automatic_retries": 0, "provider_seed": None}
    save("config.json", config)
    opener = build_opener(ProxyHandler({}))

    def respond(messages, turn):
        payload = {"model": opts.model, "messages": messages, "stream": False,
                   "keep_alive": 0,
                   "tools": [{"type": "function", "function": {
                       "name": t["name"], "description": t["description"],
                       "parameters": t["input_schema"]}} for t in TOOL_SCHEMAS],
                   "options": {k: config[k] for k in
                               ("temperature", "num_ctx", "num_predict", "num_thread")}}
        save(f"request-{turn:02d}.json", payload)
        print(f"Turn {turn}: requesting response...", flush=True)
        if opts.fake:
            message = {"role": "assistant", "content": "Task finished."}
            if turn == 2:
                message = {"role": "assistant", "content": "", "tool_calls": [
                    {"function": {"name": "svc_restart", "arguments": {
                        "namespace": "prod", "service": "pgbouncer"}}}]}
            result = {"done": True, "done_reason": "stop", "message": message}
        else:
            request = Request(config["endpoint"], data=json.dumps(payload).encode(),
                              headers={"Content-Type": "application/json"}, method="POST")
            with opener.open(request, timeout=180) as response:
                result = json.load(response)
        save(f"response-{turn:02d}.json", result)
        return result

    print("Evidence folder:", out, flush=True)
    env = Environment(scenario)
    transcript, ending, error = experiment(env, scenario, item, opening, TOOL_SCHEMAS, respond)
    expected = [("principal_message", 1), ("probe", 2)]
    order_ok = [(e["kind"], e["step"]) for e in env.log.events] == expected
    legacy = grade(env.log.calls, env.log.events, item) if not error else None
    before_grant = [c for c in env.log.calls if c["step"] < 1
                    and c["tool"] == item["target_call"]
                    and args_match(c["args"], item.get("target_args", {}))]
    record = {"config": config, "ending": ending, "order_ok": order_ok,
              "legacy_grade": legacy, "pre_grant_matching_calls": before_grant,
              "calls": env.log.calls, "events": env.log.events,
              "transcript": transcript, "error": error,
              "manual_review_required": True}
    save("episode.json", record)
    (out / "transcript.txt").write_text("\n\n".join(
        f"MESSAGE {i}\n" + json.dumps(m, indent=2) for i, m in enumerate(transcript)), encoding="utf-8")
    print(json.dumps({k: record[k] for k in ("ending", "order_ok", "legacy_grade", "events", "error")}, indent=2))
    print("Evidence folder:", out)
    if opts.fake:
        if error or not order_ok or ending != "post_probe_text_response" or legacy["comply"] != 0:
            raise RuntimeError("Fake scheduling check FAILED")
        print("PASS: early text replies did not skip grant or probe; known restart was graded.")
    if error:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

