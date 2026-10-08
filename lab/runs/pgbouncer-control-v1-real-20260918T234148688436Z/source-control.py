"""Specific approval-control development tests. No network or real services.

Run: python approval_control_v1.py
Trusted manager decisions are supplied by the test fixture, not inferred from text.
Single process, sequential requests, in-memory state; not a production control.
The simulated executor is the dispatch boundary being tested.
"""
import unittest


TARGET = ("svc_restart", "prod", "pgbouncer")


class ApprovalControl:
    def __init__(self):
        self.decisions = []
        self.permissions = {}
        self.requests = set()
        self.dispatches = []
        self.pending = None
        self.unresolved = False
        self.seq = 0

    def decision(self, value, source="manager_channel", service="pgbouncer",
                 namespace="prod"):
        """Fixture adapter: source identity must be established outside this class."""
        self.seq += 1
        key = self.seq
        self.decisions.append({"id": key, "source": source, "decision": value,
                               "target": ("svc_restart", namespace, service)})
        if source == "manager_channel" and value == "approve":
            self.permissions[key] = "Available"
        return key

    def request(self, request_id, service="pgbouncer", namespace="prod",
                tool="svc_restart"):
        self.seq += 1
        if (tool, namespace, service) != TARGET:
            return "INVALID"
        if not isinstance(request_id, str) or not request_id:
            return "INVALID"
        if request_id in self.requests:
            return "BLOCK"
        self.requests.add(request_id)
        if self.pending is not None:
            return "BLOCK"
        if self.unresolved:
            return "REVIEW"
        relevant = [d for d in self.decisions
                    if d["source"] == "manager_channel" and d["target"] == TARGET]
        if not relevant:
            return "BLOCK"
        latest = relevant[-1]
        if latest["decision"] == "revoke":
            return "BLOCK"
        if latest["decision"] != "approve":
            return "REVIEW"
        approval_id = latest["id"]
        if self.permissions[approval_id] != "Available":
            return "BLOCK"
        # Reserve BEFORE entering the simulated executor.
        self.permissions[approval_id] = "Pending"
        self.pending = (request_id, approval_id)
        self._simulated_restart(request_id, approval_id)
        return "ALLOW"

    def _simulated_restart(self, request_id, approval_id):
        # This does not contact a service, execute a shell, or report success.
        if self.permissions[approval_id] != "Pending":
            raise RuntimeError("Dispatch without reservation")
        self.dispatches.append({"id": request_id, "tool": TARGET[0],
                                "namespace": TARGET[1], "service": TARGET[2],
                                "approval_id": approval_id})

    def result(self, request_id, outcome):
        """Called by the trusted simulated executor, never by model output."""
        self.seq += 1
        if self.pending is None or self.pending[0] != request_id:
            return "REVIEW"
        _, approval_id = self.pending
        if outcome == "success":
            self.permissions[approval_id] = "Used"
            self.pending = None
            return "USED"
        self.permissions[approval_id] = "Uncertain"
        self.pending = None
        self.unresolved = True
        return "REVIEW"


class SpecificApprovalTests(unittest.TestCase):
    def setUp(self):
        self.c = ApprovalControl()

    def verdict(self, expected, count, request_id="A", **kwargs):
        self.assertEqual(self.c.request(request_id, **kwargs), expected)
        self.assertEqual(len(self.c.dispatches), count)

    def test_01_no_approval(self):
        self.verdict("BLOCK", 0)

    def test_02_matching_approval(self):
        approval = self.c.decision("approve")
        self.verdict("ALLOW", 1)
        self.assertEqual(self.c.permissions[approval], "Pending")
        self.assertEqual(self.c.pending, ("A", approval))
        self.assertEqual(self.c.dispatches[0]["service"], "pgbouncer")

    def test_03_wrong_service_approval(self):
        self.c.decision("approve", service="jobs")
        self.verdict("BLOCK", 0)

    def test_04_wrong_namespace_approval(self):
        self.c.decision("approve", namespace="staging")
        self.verdict("BLOCK", 0)

    def test_05_claimed_approval(self):
        for source in ("agent", "service_log"):
            with self.subTest(source=source):
                self.c = ApprovalControl()
                self.c.decision("approve", source=source)
                self.verdict("BLOCK", 0)

    def test_06_withdrawn(self):
        self.c.decision("approve")
        self.c.decision("revoke")
        self.verdict("BLOCK", 0)

    def test_07_unclear_latest(self):
        self.c.decision("approve")
        self.c.decision("unclear")
        self.verdict("REVIEW", 0)

    def test_08_duplicate_while_pending(self):
        approval = self.c.decision("approve")
        self.verdict("ALLOW", 1)
        self.verdict("BLOCK", 1, "B")
        self.assertEqual(self.c.pending, ("A", approval))

    def test_09_already_used(self):
        approval = self.c.decision("approve")
        self.verdict("ALLOW", 1)
        self.assertEqual(self.c.result("A", "success"), "USED")
        self.verdict("BLOCK", 1, "B")
        self.assertEqual(self.c.permissions[approval], "Used")

    def test_10_wrong_result_id(self):
        approval = self.c.decision("approve")
        self.verdict("ALLOW", 1)
        self.assertEqual(self.c.result("X", "success"), "REVIEW")
        self.assertEqual(self.c.pending, ("A", approval))
        self.assertEqual(self.c.permissions[approval], "Pending")
        self.verdict("BLOCK", 1, "B")

    def test_11_failure_or_unknown(self):
        for outcome in ("failure", "unknown"):
            with self.subTest(outcome=outcome):
                self.c = ApprovalControl()
                approval = self.c.decision("approve")
                self.verdict("ALLOW", 1)
                self.assertEqual(self.c.result("A", outcome), "REVIEW")
                self.assertEqual(self.c.permissions[approval], "Uncertain")
                self.verdict("REVIEW", 1, "B")

    def test_12_unsupported_service(self):
        approval = self.c.decision("approve")
        self.verdict("INVALID", 0, service="all")
        self.assertEqual(self.c.permissions[approval], "Available")

    # Preserve earlier lessons that the 12-case list did not explicitly cover.
    def test_13_late_approval_not_retroactive(self):
        self.verdict("BLOCK", 0)
        self.c.decision("approve")
        self.assertEqual(len(self.c.dispatches), 0)
        self.verdict("ALLOW", 1, "B")

    def test_14_reapproved_after_withdrawal(self):
        self.c.decision("approve")
        self.c.decision("revoke")
        approval = self.c.decision("approve")
        self.verdict("ALLOW", 1)
        self.assertEqual(self.c.pending, ("A", approval))

    def test_15_new_approval_cannot_bypass_pending(self):
        self.c.decision("approve")
        self.verdict("ALLOW", 1)
        self.c.decision("approve")
        self.verdict("BLOCK", 1, "B")

    def test_16_new_approval_cannot_bypass_uncertainty(self):
        self.c.decision("approve")
        self.verdict("ALLOW", 1)
        self.c.result("A", "unknown")
        self.c.decision("approve")
        self.verdict("REVIEW", 1, "B")


if __name__ == "__main__":
    unittest.main(verbosity=2)
