import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ENGINE = Path(__file__).resolve().parents[1] / "engine.py"
SPEC = importlib.util.spec_from_file_location("bjm_graph_engine", ENGINE)
engine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(engine)


class SchedulingTests(unittest.TestCase):
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
