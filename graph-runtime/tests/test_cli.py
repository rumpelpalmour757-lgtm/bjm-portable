from contextlib import closing, contextmanager
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


PACKAGE = Path(__file__).resolve().parents[1]
WORKFLOW = PACKAGE / "workflow.py"
TWO_CHAPTERS = PACKAGE / "examples" / "two_chapters.json"
SPEC = importlib.util.spec_from_file_location("bjm_graph_engine", PACKAGE / "engine.py")
engine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(engine)


class WorkflowCLITest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)
        self.command = [
            sys.executable,
            "-B",
            str(WORKFLOW),
            "--db",
            str(self.workspace / "workflow.db"),
            "--run-id",
            "demo",
        ]

    def cli(self, *arguments, expected=0):
        result = subprocess.run(
            [*self.command, *arguments],
            cwd=self.workspace,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(
            result.returncode,
            expected,
            f"{arguments!r}\nstdout: {result.stdout}\nstderr: {result.stderr}",
        )
        if expected:
            self.assertTrue(result.stderr.strip())
            return result.stderr
        return json.loads(result.stdout)

    def write_graph(self, nodes):
        graph = self.workspace / "graph.json"
        graph.write_text(json.dumps({"version": "test-graph", "nodes": nodes}), encoding="utf-8")
        return str(graph)

    def test_only_init_prepares_an_empty_database(self):
        db_path = self.workspace / "workflow.db"
        db_path.touch()
        for args, message in (
            (("status",), "database is not initialized"),
            (("events",), "database is not initialized"),
            (("events", "--after", "-1"), "database is not initialized"),
            (("run",), "database is not initialized"),
            (("retry", "review-b"), "database is not initialized"),
            (("edit", "draft-b", "{}"), "database is not initialized"),
            (("approve", "approve", "--", "bjm_x"), "database is not initialized"),
            (("reject", "approve", "--", "bjm_x"), "database is not initialized"),
            (("resolve", "review-b", "{}"), "database is not initialized"),
            (("run", "--workers", "0"), "--workers must be a positive integer"),
            (("run", "--claude-workers", "0"), "--claude-workers must be a positive integer"),
        ):
            with self.subTest(args=args):
                error = self.cli(*args, expected=2)
                self.assertTrue(error.startswith(f"workflow: {message}"), error)
                self.assertEqual(db_path.read_bytes(), b"")
                self.assertEqual(list(self.workspace.iterdir()), [db_path])

        initialized = self.cli("init", str(TWO_CHAPTERS))
        self.assertEqual(self.cli("status"), initialized)
        self.assertTrue(self.cli("events"))
        self.assertGreater(db_path.stat().st_size, 0)
        self.assertTrue(db_path.with_suffix(".db.lock").is_file())

    @contextmanager
    def running_process(self, node):
        process = subprocess.Popen(
            [*self.command, "run"], cwd=self.workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        try:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                self.assertIsNone(process.poll(), "runner exited before reaching its action")
                if self.cli("status")["nodes"][node]["status"] == "RUNNING":
                    break
                time.sleep(0.02)
            else:
                self.fail("runner did not persist RUNNING before the test deadline")
            yield
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=5)

    def test_timeout_retries_only_the_failed_branch_after_restart(self):
        self.cli("init", str(TWO_CHAPTERS))
        failed = self.cli("run", "--workers", "2", "--fail-before", "review-b")["nodes"]
        self.assertEqual(failed["review-a"]["status"], "SUCCEEDED")
        self.assertEqual(failed["review-b"]["status"], "FAILED")
        self.assertEqual(failed["review-b"]["attempt"], 1)
        self.assertEqual(failed["approve"]["status"], "PENDING")
        self.assertEqual(self.cli("status")["nodes"], failed)
        before = self.cli("events")

        self.cli("retry", "review-b")
        resumed = self.cli("run", "--workers", "2")["nodes"]
        for node in ("draft-a", "draft-b", "review-a"):
            with self.subTest(node=node):
                self.assertEqual(resumed[node], failed[node])
        self.assertEqual(resumed["review-b"]["status"], "SUCCEEDED")
        self.assertEqual(resumed["review-b"]["attempt"], 2)
        self.assertEqual(resumed["approve"]["status"], "AWAITING_APPROVAL")

        after = self.cli("events")
        self.assertTrue(before)
        self.assertEqual(after[: len(before)], before)
        self.assertGreater(len(after), len(before))
        ids = [event["id"] for event in after]
        self.assertEqual(ids, sorted(set(ids)))
        self.assertTrue(any(event["node_id"] == "review-b" for event in after[len(before) :]))

    def test_events_cursor_pages_a_single_run_and_resumes_after_new_events(self):
        self.cli("init", str(TWO_CHAPTERS))
        coordinator = engine.Engine(self.workspace / "workflow.db")
        coordinator.init("another-run", json.loads(TWO_CHAPTERS.read_text(encoding="utf-8")))
        self.cli("run", "--workers", "2", "--fail-before", "review-b")
        original = self.cli("events")
        self.assertGreater(len(original), 2)
        other_id = coordinator.events("another-run")[0]["id"]
        self.assertLess(original[0]["id"], other_id)
        self.assertLess(other_id, original[1]["id"])

        first_page = self.cli("events", "--after", "0", "--limit", "2")
        self.assertEqual(first_page, original[:2])
        self.assertEqual(self.cli("events", "--after", "0", "--limit", "2"), first_page)
        self.assertEqual(self.cli("events", "--after", str(first_page[-1]["id"])), original[2:])
        tail = str(original[-1]["id"])
        self.assertEqual(self.cli("events", "--after", tail, "--limit", "2"), [])

        self.cli("retry", "review-b")
        self.cli("run", "--workers", "2")
        complete = self.cli("events")
        new_events = self.cli("events", "--after", tail)
        self.assertEqual(complete, original + new_events)
        self.assertTrue(new_events)
        self.assertEqual(self.cli("events", "--after", "0", "--limit", "2"), first_page)

        reconstructed = []
        cursor = 0
        for _ in range(len(complete) + 1):
            page = self.cli("events", "--after", str(cursor), "--limit", "2")
            if not page:
                break
            self.assertLess(cursor, page[0]["id"])
            self.assertLessEqual(len(page), 2)
            reconstructed.extend(page)
            cursor = page[-1]["id"]
        else:
            self.fail("event pagination did not reach the tail")
        self.assertEqual(reconstructed, complete)
        self.assertTrue(all(row["run_id"] == "demo" for row in reconstructed))

    def test_event_cursor_options_reject_out_of_range_values(self):
        self.cli("init", str(TWO_CHAPTERS))
        original = self.cli("events")
        too_large = str(1 << 63)
        for args, message in (
            (("--after", "-1"), "after must be"),
            (("--after", too_large), "after must be"),
            (("--limit", "1"), "limit requires an after cursor"),
            (("--after", "0", "--limit", "0"), "limit must be"),
            (("--after", "0", "--limit", "-1"), "limit must be"),
            (("--after", "0", "--limit", too_large), "limit must be"),
        ):
            with self.subTest(args=args):
                self.assertIn(message, self.cli("events", *args, expected=2))
        self.assertEqual(self.cli("events"), original)
        self.assertEqual(self.cli("events", "--after", str((1 << 63) - 1)), [])

        coordinator = engine.Engine(self.workspace / "workflow.db")
        with self.assertRaisesRegex(ValueError, "after must be"):
            coordinator.events("demo", after=True)
        with self.assertRaisesRegex(ValueError, "limit must be"):
            coordinator.events("demo", after=0, limit=False)

    def test_revising_one_chapter_invalidates_its_review_and_old_approval(self):
        self.cli("init", str(TWO_CHAPTERS))
        initial = self.cli("run")["nodes"]
        self.assertEqual(initial["approve"]["status"], "AWAITING_APPROVAL")
        old_token = initial["approve"]["token"]
        self.assertTrue(old_token)
        accepted = self.cli("approve", "approve", "--", old_token)["nodes"]
        self.assertEqual(accepted["approve"]["status"], "SUCCEEDED")

        edited = self.cli("edit", "draft-a", json.dumps({"text": "Revised chapter A."}))["nodes"]
        for node in ("draft-a", "review-a", "approve"):
            with self.subTest(node=node):
                self.assertEqual(edited[node]["status"], "PENDING")
                self.assertGreater(edited[node]["revision"], accepted[node]["revision"])
        self.assertIsNone(edited["approve"]["token"])

        rerun = self.cli("run")["nodes"]
        for node in ("draft-b", "review-b"):
            with self.subTest(node=node):
                self.assertEqual(rerun[node], accepted[node])
        for node in ("draft-a", "review-a"):
            with self.subTest(node=node):
                self.assertEqual(rerun[node]["status"], "SUCCEEDED")
                self.assertEqual(rerun[node]["attempt"], accepted[node]["attempt"] + 1)
                self.assertNotEqual(rerun[node]["fingerprint"], accepted[node]["fingerprint"])

        self.assertEqual(rerun["approve"]["status"], "AWAITING_APPROVAL")
        new_token = rerun["approve"]["token"]
        self.assertTrue(new_token.startswith("bjm_"))
        self.assertNotEqual(new_token, old_token)
        stale = self.cli("approve", "approve", "--", old_token, expected=2)
        self.assertIn("stale or invalid approval token", stale)
        error = self.cli("approve", "approve", "--", "旧审批令牌", expected=2)
        self.assertNotIn("Traceback", error)
        self.assertEqual(self.cli("status")["nodes"]["approve"], rerun["approve"])
        final = self.cli("approve", "approve", "--", new_token)["nodes"]
        self.assertEqual(final["approve"]["status"], "SUCCEEDED")

    def test_approval_tokens_never_start_with_a_dash(self):
        coordinator = engine.Engine(self.workspace / "tokens.db")
        gate = {"id": "gate-0", "kind": "approval", "deps": [], "inputs": {}}
        coordinator.init("pinned", {"version": "token-test", "nodes": [gate]})
        with patch.object(engine.secrets, "token_urlsafe", return_value="-first"):
            pinned = coordinator.run("pinned", handler=None)["nodes"]
        self.assertEqual(pinned["gate-0"]["token"], "bjm_-first")

        many = [{"id": f"gate-{index}", "kind": "approval", "deps": [], "inputs": {}} for index in range(640)]
        coordinator.init("many", {"version": "token-test", "nodes": many})
        tokens = [node["token"] for node in coordinator.run("many", handler=None)["nodes"].values()]
        self.assertEqual(len(tokens), 640)
        self.assertEqual(len(set(tokens)), 640)
        self.assertFalse([token for token in tokens if len(token) <= 4 or not token.startswith("bjm_")])

    def test_a_dash_token_saved_by_an_older_version_is_approved_after_double_dash(self):
        self.cli("init", str(TWO_CHAPTERS))
        token = self.cli("run")["nodes"]["approve"]["token"]
        older = "-A" + token[2:]
        with closing(sqlite3.connect(self.workspace / "workflow.db")) as db, db:
            db.execute("UPDATE nodes SET token = ? WHERE run_id = ? AND id = ?", (older, "demo", "approve"))
        error = self.cli("approve", "approve", older, expected=2)
        self.assertIn("usage:", error)
        self.assertEqual(self.cli("status")["nodes"]["approve"]["status"], "AWAITING_APPROVAL")
        final = self.cli("approve", "approve", "--", older)["nodes"]
        self.assertEqual(final["approve"]["status"], "SUCCEEDED")

    def test_rejection_persists_until_a_new_revision_is_approved(self):
        graph = self.write_graph([
            {"id": "draft", "inputs": {"text": "Original draft"}, "retry_safe": True},
            {"id": "gate", "kind": "approval", "deps": ["draft"]},
            {"id": "release", "deps": ["gate"], "inputs": {"text": "Release the artifact"}},
            {"id": "independent", "inputs": {"text": "Unrelated work"}},
        ])
        self.cli("init", graph)
        initial = self.cli("run")["nodes"]
        first_gate = initial["gate"]
        self.assertEqual(first_gate["status"], "AWAITING_APPROVAL")
        old_token = first_gate["token"]
        before = self.cli("events")
        self.assertIn("stale or invalid approval token", self.cli("reject", "gate", "--", "未知令牌", expected=2))
        self.assertEqual(self.cli("events"), before)

        rejected = self.cli("reject", "gate", "--", old_token)["nodes"]
        self.assertEqual(rejected["gate"], {
            **first_gate, "status": "REJECTED", "token": None, "error": "ApprovalRejected",
        })
        event = self.cli("events")[-1]
        self.assertEqual(event["event"], "APPROVAL_REJECTED")
        self.assertEqual(event["node_id"], "gate")
        self.assertEqual(set(event["details"]), {"fingerprint", "revision", "content_sha256"})
        self.assertEqual(event["details"]["fingerprint"], first_gate["fingerprint"])
        self.assertEqual(event["details"]["revision"], first_gate["revision"])
        self.assertIn("was rejected", self.cli("approve", "gate", "--", old_token, expected=2))
        self.assertIn("was rejected", self.cli("reject", "gate", "--", old_token, expected=2))
        self.cli("retry", "gate", expected=2)
        self.cli("resolve", "gate", '{"approved":true}', expected=2)
        self.cli("edit", "draft", '{"text":"Original draft"}')
        self.assertEqual(self.cli("run")["nodes"], rejected)
        self.assertEqual(self.cli("events"), [*before, event])
        self.assertEqual(rejected["release"]["status"], "PENDING")
        self.assertEqual(rejected["release"]["attempt"], 0)
        self.assertEqual(rejected["independent"], initial["independent"])

        self.cli("edit", "draft", '{"text":"Revised draft"}')
        revised = self.cli("run")["nodes"]
        self.assertEqual(revised["gate"]["status"], "AWAITING_APPROVAL")
        self.assertEqual(revised["gate"]["revision"], first_gate["revision"] + 1)
        self.assertNotEqual(revised["gate"]["fingerprint"], first_gate["fingerprint"])
        new_token = revised["gate"]["token"]
        self.assertNotEqual(old_token, new_token)
        self.cli("reject", "gate", "--", old_token, expected=2)
        self.cli("approve", "gate", "--", old_token, expected=2)
        self.cli("approve", "gate", "--", new_token)
        complete = self.cli("run")["nodes"]
        self.assertEqual(complete["gate"]["status"], "SUCCEEDED")
        self.assertEqual(complete["release"]["status"], "SUCCEEDED")
        self.assertEqual(complete["release"]["attempt"], 1)
        self.assertEqual(complete["independent"], initial["independent"])

    def test_rejects_only_the_selected_approval_and_accepts_a_legacy_token(self):
        graph = self.write_graph([
            {"id": "gate-a", "kind": "approval"},
            {"id": "gate-b", "kind": "approval"},
            {"id": "dependent-b", "deps": ["gate-b"], "inputs": {"text": "Group B"}},
        ])
        self.cli("init", graph)
        first = self.cli("run")["nodes"]
        self.cli("reject", "gate-a", "--", first["gate-b"]["token"], expected=2)
        legacy_token = "-legacy-reject"
        with closing(sqlite3.connect(self.workspace / "workflow.db")) as db, db:
            db.execute("UPDATE nodes SET token=? WHERE run_id=? AND id=?",
                       (legacy_token, "demo", "gate-a"))
        rejected = self.cli("reject", "gate-a", "--", legacy_token)["nodes"]
        self.assertEqual(rejected["gate-a"]["status"], "REJECTED")
        self.assertEqual(rejected["gate-b"], first["gate-b"])
        self.cli("approve", "gate-b", "--", first["gate-b"]["token"])
        finished = self.cli("run")["nodes"]
        self.assertEqual(finished["gate-a"], rejected["gate-a"])
        self.assertEqual(finished["dependent-b"]["status"], "SUCCEEDED")

    def test_a_rejection_stays_with_the_content_it_turned_down(self):
        graph = self.write_graph([
            {"id": "draft", "inputs": {"text": "Original draft"}, "retry_safe": True},
            {"id": "gate", "kind": "approval", "deps": ["draft"]},
            {"id": "release", "deps": ["gate"], "inputs": {"text": "Release the artifact"}},
        ])
        self.cli("init", graph)
        first = self.cli("run")["nodes"]
        self.cli("reject", "gate", "--", first["gate"]["token"])
        (rejection,) = [event for event in self.cli("events") if event["event"] == "APPROVAL_REJECTED"]

        self.cli("edit", "draft", '{"text":"Something else"}')
        other = self.cli("run")["nodes"]["gate"]
        self.assertEqual(other["status"], "AWAITING_APPROVAL")
        # Changing the draft back, or adding an input that leaves its output alone, shows the same content.
        for inputs in ('{"text":"Original draft"}', '{"text":"Original draft","unused":1}'):
            with self.subTest(inputs=inputs):
                self.cli("edit", "draft", inputs)
                state = self.cli("run")["nodes"]
                self.assertEqual(state["draft"]["output"], first["draft"]["output"])
                self.assertEqual(state["gate"]["status"], "REJECTED")
                self.assertIsNone(state["gate"]["token"])
                self.assertEqual(state["gate"]["error"],
                                 "ApprovalRejected: the same content was rejected at revision 1")
                self.assertEqual(state["release"]["status"], "PENDING")
                kept = self.cli("events")[-1]
                self.assertEqual(kept["event"], "REJECTION_KEPT")
                self.assertEqual(kept["details"]["rejected_revision"], 1)
                self.assertEqual(kept["details"]["content_sha256"], rejection["details"]["content_sha256"])
                self.assertEqual(kept["details"]["revision"], state["gate"]["revision"])
                self.assertIn("was rejected", self.cli("approve", "gate", "--", other["token"], expected=2))
                self.assertEqual(self.cli("run")["nodes"], state)

        # Asking the reviewer to look again is explicit: it changes the approval node's own inputs.
        self.cli("edit", "gate", '{"note":"Reviewer asked to see it again"}')
        reopened = self.cli("run")["nodes"]["gate"]
        self.assertEqual(reopened["status"], "AWAITING_APPROVAL")
        self.cli("approve", "gate", "--", reopened["token"])
        self.assertEqual(self.cli("run")["nodes"]["release"]["status"], "SUCCEEDED")

    def test_a_rejection_stays_with_the_approval_node_that_made_it(self):
        graph = self.write_graph([
            {"id": "draft", "inputs": {"text": "Shared draft"}, "retry_safe": True},
            {"id": "legal", "kind": "approval", "deps": ["draft"]},
            {"id": "editor", "kind": "approval", "deps": ["draft"]},
        ])
        self.cli("init", graph)
        first = self.cli("run")["nodes"]
        self.cli("reject", "legal", "--", first["legal"]["token"])
        # Both approvals see the same content; only the one the reviewer turned down stays rejected.
        self.cli("edit", "draft", '{"text":"Shared draft","unused":1}')
        state = self.cli("run")["nodes"]
        self.assertEqual(state["legal"]["status"], "REJECTED")
        self.assertEqual(state["editor"]["status"], "AWAITING_APPROVAL")
        self.assertTrue(state["editor"]["token"])
        self.assertNotEqual(state["editor"]["token"], first["editor"]["token"])

    def test_a_new_run_does_not_inherit_an_earlier_runs_rejection(self):
        graph = self.write_graph([
            {"id": "draft", "inputs": {"text": "Original draft"}, "retry_safe": True},
            {"id": "gate", "kind": "approval", "deps": ["draft"]},
        ])
        self.cli("init", graph)
        self.cli("reject", "gate", "--", self.cli("run")["nodes"]["gate"]["token"])
        self.command[-1] = "second"
        self.cli("init", graph)
        second = self.cli("run")["nodes"]["gate"]
        self.assertEqual(second["status"], "AWAITING_APPROVAL")
        self.assertTrue(second["token"])

    def test_approve_refuses_a_token_for_content_already_rejected(self):
        graph = self.write_graph([
            {"id": "draft", "inputs": {"text": "Original draft"}, "retry_safe": True},
            {"id": "gate", "kind": "approval", "deps": ["draft"]},
            {"id": "release", "deps": ["gate"], "inputs": {"text": "Release the artifact"}},
        ])
        self.cli("init", graph)
        self.cli("reject", "gate", "--", self.cli("run")["nodes"]["gate"]["token"])
        self.cli("edit", "draft", '{"text":"Original draft","unused":1}')
        self.assertEqual(self.cli("run")["nodes"]["gate"]["status"], "REJECTED")
        # A version that does not compare content, such as v1.8.1, issues a token here; model that directly.
        with closing(sqlite3.connect(self.workspace / "workflow.db")) as db, db:
            db.execute("UPDATE nodes SET status = 'AWAITING_APPROVAL', token = ?, error = NULL "
                       "WHERE run_id = ? AND id = ?", ("bjm_older", "demo", "gate"))
        before, events = self.cli("status"), self.cli("events")
        self.assertIn("gate: the same content was rejected at revision 1",
                      self.cli("approve", "gate", "--", "bjm_older", expected=2))
        self.assertEqual(self.cli("status"), before)
        self.assertEqual(self.cli("events"), events)
        self.assertEqual(self.cli("reject", "gate", "--", "bjm_older")["nodes"]["gate"]["status"], "REJECTED")
        self.assertEqual(self.cli("run")["nodes"]["release"]["status"], "PENDING")

    def test_decisions_name_the_state_that_blocks_them(self):
        graph = self.write_graph([
            {"id": "draft", "inputs": {"text": "Draft"}, "retry_safe": True},
            {"id": "gate", "kind": "approval", "deps": ["draft"]},
            {"id": "solo", "kind": "approval"},
        ])
        self.cli("init", graph)
        before = self.cli("events")
        for command in ("approve", "reject"):
            with self.subTest(command=command):
                self.assertIn("not awaiting a decision", self.cli(command, "gate", "--", "bjm_x", expected=2))
                self.assertIn("draft is not an approval node", self.cli(command, "draft", "--", "bjm_x", expected=2))
                self.assertIn("unknown node: nowhere", self.cli(command, "nowhere", "--", "bjm_x", expected=2))
        self.assertEqual(self.cli("events"), before)

        state = self.cli("run")["nodes"]
        self.cli("approve", "solo", "--", state["solo"]["token"])
        self.cli("reject", "gate", "--", state["gate"]["token"])
        settled = self.cli("events")
        for command in ("approve", "reject"):
            with self.subTest(command=command):
                self.assertIn("solo is already approved",
                              self.cli(command, "solo", "--", state["solo"]["token"], expected=2))
                self.assertIn("gate was rejected", self.cli(command, "gate", "--", state["gate"]["token"], expected=2))
        self.assertEqual(self.cli("events"), settled)

    def test_reviews_that_cannot_start_this_run_do_not_need_claude(self):
        review = {"operation": "claude-review", "model": "sonnet", "focus": "dialogue"}
        graph = self.write_graph([
            {"id": "draft", "inputs": {"text": "Draft"}, "retry_safe": True},
            {"id": "gate", "kind": "approval", "deps": ["draft"]},
            {"id": "review", "deps": ["gate"], "inputs": review, "retry_safe": True},
            {"id": "independent", "inputs": {"text": "Unrelated work"}},
        ])
        self.cli("init", graph)
        first = self.cli("run")["nodes"]
        self.assertEqual(first["gate"]["status"], "AWAITING_APPROVAL")
        self.assertEqual(first["independent"]["status"], "SUCCEEDED")
        self.assertEqual(first["review"]["status"], "PENDING")
        self.assertEqual(self.cli("run")["nodes"], first)
        self.cli("reject", "gate", "--", first["gate"]["token"])
        self.assertEqual(self.cli("run")["nodes"]["review"]["status"], "PENDING")

        self.cli("edit", "draft", '{"text":"Revised draft"}')
        token = self.cli("run")["nodes"]["gate"]["token"]
        self.cli("approve", "gate", "--", token)
        before = self.cli("status")
        self.assertIn("Claude review nodes require run --claude", self.cli("run", expected=2))
        self.assertEqual(self.cli("status"), before)

    def test_a_broken_review_declaration_stops_the_run_even_while_the_review_waits(self):
        review = {"operation": "claude-review", "model": "sonnet", "focus": "dialogue"}
        graph = self.write_graph([
            {"id": "draft", "inputs": {"text": "Draft"}, "retry_safe": True},
            {"id": "gate", "kind": "approval", "deps": ["draft"]},
            {"id": "review", "deps": ["gate"], "inputs": review, "retry_safe": True},
            {"id": "independent", "inputs": {"text": "Unrelated work"}},
        ])
        self.cli("init", graph)
        self.cli("edit", "review", json.dumps({**review, "focus": ""}))
        before, events = self.cli("status"), self.cli("events")
        error = self.cli("run", expected=2)
        self.assertIn("review: Claude review requires a nonempty focus; fix its inputs with edit", error)
        self.assertEqual(self.cli("status"), before)
        self.assertEqual(self.cli("events"), events)

        self.cli("edit", "review", json.dumps(review))
        state = self.cli("run")["nodes"]
        self.assertEqual(state["gate"]["status"], "AWAITING_APPROVAL")
        self.assertEqual(state["independent"]["status"], "SUCCEEDED")
        self.assertEqual(state["review"]["status"], "PENDING")

    def test_process_loss_requires_resolution_for_an_unsafe_action(self):
        graph = self.write_graph(
            [
                {
                    "id": "prepare",
                    "kind": "task",
                    "deps": [],
                    "inputs": {"text": "Prepare the external action"},
                    "retry_safe": True,
                },
                {
                    "id": "action",
                    "kind": "task",
                    "deps": ["prepare"],
                    "inputs": {"text": "Simulated external action", "delay_seconds": 10},
                    "retry_safe": False,
                },
                {"id": "confirm", "kind": "approval", "deps": ["action"], "inputs": {}},
            ]
        )
        self.cli("init", graph)
        with self.running_process("action"):
            pass

        resumed = self.cli("run")["nodes"]
        self.assertEqual(resumed["action"]["status"], "UNCERTAIN")
        self.assertEqual(resumed["action"]["attempt"], 1)
        self.assertEqual(resumed["confirm"]["status"], "PENDING")
        self.cli("retry", "action", expected=2)
        self.assertEqual(self.cli("run")["nodes"], resumed)

        receipt = {"receipt": "externally-verified-42"}
        self.cli("resolve", "action", json.dumps(receipt))
        resolved = self.cli("run")["nodes"]
        self.assertEqual(resolved["action"]["status"], "SUCCEEDED")
        self.assertEqual(resolved["action"]["attempt"], 1)
        self.assertEqual(resolved["action"]["output"], receipt)
        self.assertEqual(resolved["confirm"]["status"], "AWAITING_APPROVAL")
        for node in ("prepare", "action"):
            with self.subTest(node=node):
                self.cli("edit", node, json.dumps({"text": "Would repeat the action"}), expected=2)
        self.assertEqual(self.cli("status")["nodes"], resolved)

    def test_process_loss_requeues_a_safe_action(self):
        graph = self.write_graph(
            [
                {
                    "id": "safe",
                    "kind": "task",
                    "deps": [],
                    "inputs": {"text": "Safe simulated step", "delay_seconds": 2},
                    "retry_safe": True,
                },
            ]
        )
        self.cli("init", graph)
        with self.running_process("safe"):
            self.assertEqual(self.cli("status")["nodes"]["safe"]["attempt"], 1)

        resumed = self.cli("run")["nodes"]["safe"]
        self.assertEqual(resumed["status"], "SUCCEEDED")
        self.assertEqual(resumed["attempt"], 2)
        self.assertEqual(resumed["output"]["text"], "Safe simulated step")

    def test_interrupted_node_that_must_not_auto_retry_can_be_retried_by_hand(self):
        graph = self.write_graph(
            [
                {"id": "draft", "inputs": {"text": "Chapter draft"}, "retry_safe": True},
                {
                    "id": "billed",
                    "deps": ["draft"],
                    "inputs": {"text": "Billed but repeatable step", "delay_seconds": 10},
                    "retry_safe": True,
                    "retry_on_interrupt": False,
                },
                {"id": "confirm", "kind": "approval", "deps": ["billed"], "inputs": {}},
            ]
        )
        self.cli("init", graph)
        with self.running_process("billed"):
            pass

        resumed = self.cli("run")["nodes"]
        self.assertEqual(resumed["billed"]["status"], "UNCERTAIN")
        self.assertEqual(resumed["billed"]["attempt"], 1)
        self.assertEqual(self.cli("run")["nodes"], resumed)
        self.cli("edit", "draft", json.dumps({"text": "Revised draft"}), expected=2)
        self.cli("edit", "billed", json.dumps({"text": "Changed step"}), expected=2)

        self.cli("retry", "billed")
        retried = [event for event in self.cli("events") if event["event"] == "RETRY_REQUESTED"]
        self.assertEqual(retried[-1]["details"], {"attempt": 1, "previous": "UNCERTAIN"})
        self.cli("edit", "billed", json.dumps({"text": "Quick repeat"}))
        final = self.cli("run")["nodes"]
        self.assertEqual(final["billed"]["status"], "SUCCEEDED")
        self.assertEqual(final["billed"]["attempt"], 2)
        self.assertEqual(final["draft"], resumed["draft"])
        self.assertEqual(final["confirm"]["status"], "AWAITING_APPROVAL")

    def test_confirmed_input_rejection_requires_an_edit_before_resuming(self):
        for retry_safe in (False, True):
            with self.subTest(retry_safe=retry_safe):
                self.command[-1] = f"reject-{retry_safe}"
                graph = self.write_graph([
                    {"id": "draft", "inputs": {"text": ""}, "retry_safe": retry_safe},
                    {"id": "approve", "kind": "approval", "deps": ["draft"]},
                    {"id": "unrelated", "inputs": {"text": "Keep this branch."}},
                ])
                self.cli("init", graph)
                first = self.cli("run")["nodes"]
                self.assertEqual(first["draft"]["status"], "REJECTED")
                self.assertEqual(first["draft"]["error"], "InputRejected: demo draft requires nonempty text")
                self.assertEqual(first["draft"]["attempt"], 1)
                self.assertEqual(first["approve"]["status"], "PENDING")
                self.assertEqual(first["unrelated"]["status"], "SUCCEEDED")
                self.assertTrue(any(event["event"] == "REJECTED" and event["node_id"] == "draft"
                                    for event in self.cli("events")))
                self.cli("retry", "draft", expected=2)
                self.cli("resolve", "draft", '{"text":"Unverified result"}', expected=2)
                self.cli("edit", "draft", '{"text":""}')
                self.assertEqual(self.cli("run")["nodes"], first)

                self.cli("edit", "draft", '{"text":"Corrected input"}')
                recovered = self.cli("run")["nodes"]
                self.assertEqual(recovered["draft"]["status"], "SUCCEEDED")
                self.assertEqual(recovered["draft"]["attempt"], 2)
                self.assertEqual(recovered["draft"]["output"]["text"], "Corrected input")
                self.assertEqual(recovered["unrelated"], first["unrelated"])
                self.assertEqual(recovered["approve"]["status"], "AWAITING_APPROVAL")

    def test_unconfirmed_adapter_exception_still_requires_resolution(self):
        graph = self.write_graph([
            {"id": "action", "inputs": {"text": "Action with an unknown outcome"}},
        ])
        self.cli("init", graph)
        state = self.cli("run", "--fail-before", "action")["nodes"]["action"]
        self.assertEqual(state["status"], "UNCERTAIN")
        self.assertEqual(state["error"], "TimeoutError")
        self.cli("edit", "action", '{"text":"Different input"}', expected=2)
        self.cli("retry", "action", expected=2)

    def test_active_runner_excludes_a_second_process(self):
        graph = self.write_graph(
            [
                {
                    "id": "active",
                    "kind": "task",
                    "deps": [],
                    "inputs": {"text": "Only one process may start this step", "delay_seconds": 10},
                },
            ]
        )
        self.cli("init", graph)
        with self.running_process("active"):
            error = self.cli("run", expected=2)
            self.assertIn("another coordinator", error)
            active = self.cli("status")["nodes"]["active"]
            self.assertEqual(active["status"], "RUNNING")
            self.assertEqual(active["attempt"], 1)

    def test_rejects_a_cycle_before_initializing_the_run(self):
        graph = self.write_graph(
            [
                {"id": "a", "kind": "task", "deps": ["b"], "inputs": {}},
                {"id": "b", "kind": "task", "deps": ["a"], "inputs": {}},
            ]
        )
        self.cli("init", graph, expected=2)
        self.cli("status", expected=2)
        self.assertEqual(self.cli("init", str(TWO_CHAPTERS))["run_id"], "demo")


if __name__ == "__main__":
    unittest.main()
