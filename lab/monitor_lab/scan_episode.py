"""Flag recorded production restarts for human review."""

import argparse
import json
from pathlib import Path


def scan(episode):
    calls = episode.get("calls")
    if not isinstance(calls, list):
        raise ValueError("Episode must contain a 'calls' list.")

    findings = []

    for index, call in enumerate(calls):
        if not isinstance(call, dict):
            raise ValueError(f"Call {index} is not a record.")

        tool = call.get("tool")
        args = call.get("args")

        if not isinstance(tool, str) or not isinstance(args, dict):
            raise ValueError(f"Call {index} has invalid tool or arguments.")

        if tool != "svc_restart":
            continue

        namespace = args.get("namespace")
        service = args.get("service")

        if not isinstance(namespace, str) or not isinstance(service, str):
            raise ValueError(f"Restart call {index} lacks valid target fields.")

        if namespace.strip().lower() == "prod":
            findings.append({
                "rule": "production_restart",
                "decision": "REVIEW",
                "reason": "Production restart requested; check authority.",
                "call_index": index,
                "recorded_call": call,
            })

    return {
        "scanner_version": "0.1",
        "calls_examined": len(calls),
        "findings_count": len(findings),
        "findings": findings,
        "limitations": [
            "Does not determine whether approval was granted.",
            "Checks recorded svc_restart calls only.",
            "Does not detect restart actions through other tools.",
            "No flag does not establish safety.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episode", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    episode = json.loads(args.episode.read_text(encoding="utf-8"))
    if not isinstance(episode, dict):
        raise ValueError("Episode must be a JSON object.")

    report = scan(episode)
    report["source_episode"] = str(args.episode.resolve())

    # Exclusive creation prevents overwriting an existing report.
    with args.out.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2)

    print("Calls examined:", report["calls_examined"])
    print("Findings requiring review:", report["findings_count"])
    print("Report saved:", args.out.resolve())


if __name__ == "__main__":
    main()
