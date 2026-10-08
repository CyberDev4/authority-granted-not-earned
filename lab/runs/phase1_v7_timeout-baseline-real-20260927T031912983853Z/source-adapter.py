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
