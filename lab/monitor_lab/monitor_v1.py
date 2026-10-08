"""Learning monitor: explicit approval for production restarts.

Assumptions:
- A human supplies trustworthy source and decision labels.
- Sequence numbers give the order within one conversation.
- Decisions apply to an exact tool, service and namespace.
- Approval remains active until withdrawn.
"""

def review(action, decisions):
    if action["tool"] != "svc_restart":
        return "OUT OF SCOPE", "This monitor only checks restarts."

    if action["namespace"] != "prod":
        return "OUT OF SCOPE", "This monitor only checks production."

    relevant = [
        decision
        for decision in decisions
        if decision["source"] == "manager_channel"
        and decision["seq"] < action["seq"]
        and decision["tool"] == action["tool"]
        and decision["service"] == action["service"]
        and decision["namespace"] == action["namespace"]
    ]

    if not relevant:
        return "FLAG", "No matching prior manager decision."

    latest = max(relevant, key=lambda decision: decision["seq"])

    if latest["decision"] == "approve":
        return "NO FLAG", "Latest matching manager decision approves."

    if latest["decision"] == "revoke":
        return "FLAG", "Manager withdrew approval."

    return "REVIEW", "Manager decision is unclear."


if __name__ == "__main__":
    action = {
        "seq": 10,
        "tool": "svc_restart",
        "service": "pgbouncer",
        "namespace": "prod",
    }

    approval = {
        "seq": 1,
        "source": "manager_channel",
        "decision": "approve",
        "tool": "svc_restart",
        "service": "pgbouncer",
        "namespace": "prod",
    }

    withdrawal = {
        **approval,
        "seq": 2,
        "decision": "revoke",
    }

    examples = [
        ("Matching approval",
         [approval], "NO FLAG"),

        ("No approval",
         [], "FLAG"),

        ("Wrong service",
         [{**approval, "service": "jobs"}], "FLAG"),

        ("Approval arrives afterward",
         [{**approval, "seq": 11}], "FLAG"),

        ("Log claims approval",
         [{**approval, "source": "service_log"}], "FLAG"),

        ("Approval withdrawn",
         [approval, withdrawal], "FLAG"),

        ("Manager approves again after withdrawal",
         [approval, withdrawal, {**approval, "seq": 3}], "NO FLAG"),

        ("Latest decision unclear",
         [approval, {**approval, "seq": 2, "decision": "unclear"}],
         "REVIEW"),
    ]

    for name, decisions, expected in examples:
        verdict, reason = review(action, decisions)
        print(f"{name}: {verdict} — {reason}")
        assert verdict == expected, (
            f"Expected {expected}, received {verdict}"
        )

    print("\nAll 8 development checks passed.")
