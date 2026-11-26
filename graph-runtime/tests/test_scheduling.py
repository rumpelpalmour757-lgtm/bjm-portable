import importlib.util
from pathlib import Path
import tempfile
from threading import Event
import unittest
from unittest.mock import patch


ENGINE = Path(__file__).resolve().parents[1] / "engine.py"
SPEC = importlib.util.spec_from_file_location("bjm_graph_engine", ENGINE)
engine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(engine)


def peak_in_flight(events, nodes):
    """Most of the given nodes recorded as running at once, counted from STARTED to their outcome."""
    running, peak = set(), 0
    for event in events:
        if event["node_id"] not in nodes:
            continue
        if event["event"] == "STARTED":
            running.add(event["node_id"])
        elif event["event"] in ("SUCCEEDED", "FAILED", "UNCERTAIN", "REJECTED"):
            running.discard(event["node_id"])
        peak = max(peak, len(running))
    return peak


class SchedulingTests(unittest.TestCase):
    def test_capped_reviews_leave_a_worker_available_for_independent_tasks(self):
        reviews = ("review-a", "review-b", "review-c")
        graph = {"version": "mixed", "nodes": [
            *({"id": node, "inputs": {"operation": "claude-review"}} for node in reviews),
            {"id": "local", "inputs": {"operation": "draft"}},
        ]}
        local_inspected = Event()

        with tempfile.TemporaryDirectory() as directory:
            runner = engine.Engine(Path(directory) / "workflow.db")
            runner.init("mixed", graph)

            def handle(spec, inputs):
                if spec["id"] == "review-a":
                    return {"saw_local_task": local_inspected.wait(30)}
                if spec["id"] == "local":
                    try:
                        snapshot = runner.status("mixed")["nodes"]
                        return {name: {field: snapshot[name][field]
                                       for field in ("status", "attempt", "fingerprint")}
                                for name in reviews}
                    finally:
                        local_inspected.set()
                return {"reviewed": spec["id"]}

            result = runner.run("mixed", handle, workers=3, worker_limits={"claude-review": 1})
            nodes = result["nodes"]
            self.assertTrue(nodes["review-a"]["output"]["saw_local_task"])
            snapshot = nodes["local"]["output"]
            self.assertEqual(snapshot["review-a"]["status"], "RUNNING")
            for queued in reviews[1:]:
                self.assertEqual(snapshot[queued], {"status": "PENDING", "attempt": 0, "fingerprint": None})
            self.assertTrue(all(node["status"] == "SUCCEEDED" for node in nodes.values()))
            self.assertTrue(all(node["attempt"] == 1 for node in nodes.values()))

            events = [(event["node_id"], event["event"]) for event in runner.events("mixed")]
            self.assertLess(events.index(("local", "STARTED")), events.index(("review-a", "SUCCEEDED")))
            for previous, next_review in zip(reviews, reviews[1:]):
                self.assertLess(events.index((previous, "SUCCEEDED")), events.index((next_review, "STARTED")))

    def test_a_capped_task_that_does_not_succeed_frees_its_slot(self):
        outcomes = {"review-a": "FAILED", "review-b": "UNCERTAIN", "review-c": "REJECTED", "review-d": "SUCCEEDED"}
        graph = {"version": "failing", "nodes": [
            {"id": node, "inputs": {"operation": "claude-review"}, "retry_safe": node != "review-b"}
            for node in outcomes
        ]}

        def handle(spec, inputs):
            if spec["id"] in ("review-a", "review-b"):
                raise TimeoutError("simulated timeout")
            if spec["id"] == "review-c":
                raise engine.InputRejected("simulated rejection")
            return {"reviewed": spec["id"]}

        with tempfile.TemporaryDirectory() as directory:
            runner = engine.Engine(Path(directory) / "workflow.db")
            runner.init("failing", graph)
            nodes = runner.run("failing", handle, workers=2, worker_limits={"claude-review": 1})["nodes"]
            for node, status in outcomes.items():
                with self.subTest(node=node):
                    self.assertEqual(nodes[node]["status"], status)
                    self.assertEqual(nodes[node]["attempt"], 1)
            self.assertEqual(peak_in_flight(runner.events("failing"), outcomes), 1)

    def test_the_worker_pool_and_the_operation_limit_both_hold(self):
        reviews = ("review-a", "review-b", "review-c")
        local = ("local-a", "local-b", "local-c")
        graph = {"version": "both", "nodes": [
            *({"id": node, "inputs": {"operation": "claude-review"}} for node in reviews),
            *({"id": node, "inputs": {"operation": "draft"}} for node in local),
        ]}

        with tempfile.TemporaryDirectory() as directory:
            runner = engine.Engine(Path(directory) / "workflow.db")
            runner.init("both", graph)
            nodes = runner.run("both", lambda spec, inputs: spec["id"], workers=2,
                               worker_limits={"claude-review": 1})["nodes"]
            self.assertTrue(all(node["status"] == "SUCCEEDED" and node["attempt"] == 1 for node in nodes.values()))
            events = runner.events("both")
            self.assertEqual(peak_in_flight(events, reviews + local), 2)
            self.assertEqual(peak_in_flight(events, reviews), 1)

    def test_invalid_worker_limits_stop_before_the_database_changes(self):
        graph = {"version": "invalid", "nodes": [{"id": "review", "inputs": {"operation": "claude-review"}}]}
        calls = []

        with tempfile.TemporaryDirectory() as directory:
            runner = engine.Engine(Path(directory) / "workflow.db")
            runner.init("invalid", graph)
            status, events = runner.status("invalid"), runner.events("invalid")
            for limits in ({"claude-review": 0}, {"claude-review": -1}, {"claude-review": True},
                           {"claude-review": 1.0}, {1: 1}, "claude-review", 1, [("claude-review", 1)]):
                with self.subTest(limits=limits):
                    with self.assertRaisesRegex(ValueError, "positive integers"):
                        runner.run("invalid", lambda spec, inputs: calls.append(spec["id"]), worker_limits=limits)
            self.assertEqual(calls, [])
            self.assertEqual(runner.status("invalid"), status)
            self.assertEqual(runner.events("invalid"), events)

    def test_fingerprints_only_dispatched_tasks_and_unblocked_approvals(self):
        branches = [f"branch-{index}" for index in range(16)]
        graph = {"version": "wide", "nodes": [
            {"id": "source"},
            *({"id": node, "deps": ["source"]} for node in branches),
            {"id": "approval", "kind": "approval", "deps": ["source"]},
        ]}

        def handle(spec, inputs):
            if spec["id"] == "source":
                return "x" * (256 * 1024)
            return len(inputs["source"])

        with tempfile.TemporaryDirectory() as directory:
            runner = engine.Engine(Path(directory) / "workflow.db")
            runner.init("wide", graph)
            with patch.object(runner, "_fingerprint", wraps=runner._fingerprint) as fingerprint:
                nodes = runner.run("wide", handle, workers=1)["nodes"]
            self.assertEqual(fingerprint.call_count, 18)
            for branch in branches:
                self.assertEqual(nodes[branch]["status"], "SUCCEEDED")
                self.assertEqual(nodes[branch]["output"], 256 * 1024)
            self.assertEqual(nodes["approval"]["status"], "AWAITING_APPROVAL")
            events = [(entry["node_id"], entry["event"]) for entry in runner.events("wide")]
            approval = events.index(("approval", "AWAITING_APPROVAL"))
            self.assertLess(events.index((branches[0], "STARTED")), approval)
            self.assertLess(approval, events.index((branches[0], "SUCCEEDED")))
