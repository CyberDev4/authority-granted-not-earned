"""One verified approval permits one restart attempt.

Learning example only:
- Approval has already been verified.
- Requests are processed one at a time.
- Results come from a trusted simulator.
"""

permission = {
    "tool": "svc_restart",
    "service": "pgbouncer",
    "namespace": "prod",
    "state": "Available",
    "request_id": None,
}


def check_request(request):
    for field in ("tool", "service", "namespace"):
        if request[field] != permission[field]:
            return "FLAG: request does not match this approval"

    if permission["state"] != "Available":
        return f"FLAG: approval is {permission['state']}"

    # Reserve approval immediately, before a result arrives.
    permission["state"] = "Pending"
    permission["request_id"] = request["id"]
    return "NO FLAG: approval reserved; state is Pending"


def record_result(request_id, outcome):
    if (
        permission["state"] != "Pending"
        or request_id != permission["request_id"]
    ):
        return "REVIEW: result does not match the pending request"

    if outcome == "success":
        permission["state"] = "Used"
    else:
        permission["state"] = "Uncertain"

    return f"Result recorded; state is {permission['state']}"


request_a = {
    "id": "A",
    "tool": "svc_restart",
    "service": "pgbouncer",
    "namespace": "prod",
}
request_b = {**request_a, "id": "B"}
request_c = {**request_a, "id": "C"}

print("Initial state:", permission["state"])
print("Request A:", check_request(request_a))
assert permission["state"] == "Pending"

print("Request B:", check_request(request_b))
assert permission["request_id"] == "A"

print("Result for A:", record_result("A", "success"))
assert permission["state"] == "Used"

print("Request C:", check_request(request_c))
assert permission["state"] == "Used"
