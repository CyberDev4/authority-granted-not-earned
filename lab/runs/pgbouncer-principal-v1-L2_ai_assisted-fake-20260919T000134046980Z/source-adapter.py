"""Separate short B0 pilot. Uses simulated GNE tools and local Ollama only."""
import argparse
import copy
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, ProxyHandler, build_opener


"""Strict parsing and explicit Qwen-style rendering for a separate pilot."""
import json
import re


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_raw(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Empty generated text")
    if any(tag in text for tag in ("<|im_start|>", "<|im_end|>")):
        raise ValueError("Unexpected chat delimiter in generated text")
    tokens = list(re.finditer(r"</?tool_call\b[^>]*>", text))
    spans, calls = [], []
    start = None
    for token in tokens:
        tag = token.group()
        if tag == "<tool_call>" and start is None:
            start = token
        elif tag == "</tool_call>" and start is not None:
            call = json.loads(text[start.end():token.start()], object_pairs_hook=unique_keys)
            if not isinstance(call, dict) or set(call) != {"name", "arguments"}:
                raise ValueError("Unexpected tool-call structure")
            if not isinstance(call["name"], str) or not isinstance(call["arguments"], dict):
                raise ValueError("Invalid tool name or arguments")
            calls.append({"function": call})
            spans.append((start.start(), token.end()))
            start = None
        else:
            raise ValueError("Nested, unmatched or unsupported tool-call tag")
    if start is not None:
        raise ValueError("Unclosed tool-call tag")
    pieces, position = [], 0
    for first, last in spans:
        pieces.append(text[position:first])
        position = last
    pieces.append(text[position:])
    content = "".join(pieces)
    if re.search(r"</?tool_call\b", content):
        raise ValueError("Malformed tool-call tag")
    return {"role": "assistant", "content": content,
            "tool_calls": calls, "raw_text": text}


def render_raw(messages, tools):
    if not messages or messages[0]["role"] != "system":
        raise ValueError("Expected initial system message")
    tool_text = "\n".join(json.dumps(t, separators=(",", ":")) for t in tools)
    instructions = (
        "\n\n# Tools\n\n"
        "You may call one or more functions to assist with the user query.\n\n"
        "You are provided with function signatures within <tools></tools> XML tags:\n"
        "<tools>\n" + tool_text + "\n</tools>\n\n"
        "For each function call, return a json object with function name and "
        "arguments within <tool_call></tool_call> XML tags:\n"
        "<tool_call>\n"
        '{"name": <function-name>, "arguments": <args-json-object>}\n'
        "</tool_call>"
    )
    parts = ["<|im_start|>system\n" + messages[0]["content"] + instructions + "<|im_end|>\n"]
    for message in messages[1:]:
        role = message["role"]
        if role == "tool":
            parts.append("<|im_start|>user\n<tool_response>\n" + message["content"]
                         + "\n</tool_response><|im_end|>\n")
        elif role == "assistant":
            text = message.get("raw_text")
            if text is None:
                text = message.get("content", "")
                for call in message.get("tool_calls", []):
                    text += "\n<tool_call>\n" + json.dumps(call["function"]) + "\n</tool_call>"
            parts.append("<|im_start|>assistant\n" + text + "<|im_end|>\n")
        elif role == "user":
            parts.append("<|im_start|>user\n" + message["content"] + "<|im_end|>\n")
        else:
            raise ValueError("Unsupported message role")
    return "".join(parts) + "<|im_start|>assistant\n"


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
            messages.append({"role": "assistant", "content": text, "tool_calls": calls, "raw_text": message.get("raw_text")})

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
    out = root / "runs" / f"B0_short_raw_v1_t0-{label}-{stamp}"
    out.mkdir(parents=True, exist_ok=False)

    def save(name, data):
        (out / name).write_text(json.dumps(data, indent=2), encoding="utf-8")

    for name in ("gne/env.py", "gne/grade.py", "scenarios/backlog_cleanup.json",
                 "items/competence.json", "items/scope.json"):
        destination = out / "source" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((root / name).read_bytes())
    (out / "run_short_b0_raw.py").write_bytes(Path(__file__).read_bytes())
    config = {"protocol": "B0_short_raw_v1_t0", "mode": label, "model": opts.model,
              "competence": "L0", "item": item["id"], "grant_turn": 1,
              "probe_turn": 2, "max_turns": 6, "temperature": 0.0,
              "num_ctx": 16384, "num_predict": 1024, "num_thread": 2,
              "endpoint": "http://127.0.0.1:11434/api/generate",
              "compaction": False, "handoff": False, "awareness_question": False,
              "automatic_retries": 0, "provider_seed": None, "renderer": "manual_qwen_style_v1",
              "parser": "strict_tool_tags_v1", "tool_dispatch": "simulated_only"}
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
            raw_payload = {"model": opts.model,
                           "prompt": render_raw(messages, payload["tools"]),
                           "raw": True, "stream": False, "keep_alive": 0,
                           "options": payload["options"]}
            save(f"raw-request-{turn:02d}.json", raw_payload)
            request = Request(config["endpoint"], data=json.dumps(raw_payload).encode(),
                              headers={"Content-Type": "application/json"}, method="POST")
            with opener.open(request, timeout=180) as response:
                raw_result = json.load(response)
            save(f"raw-response-{turn:02d}.json", raw_result)
            if raw_result.get("done") is not True or raw_result.get("done_reason") != "stop":
                raise ValueError("Raw generation incomplete or truncated")
            if raw_result.get("thinking"):
                raise ValueError("Unexpected separate thinking output")
            result = {"done": True, "done_reason": "stop",
                      "message": parse_raw(raw_result.get("response"))}
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
