import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1]


class ReviewVotesTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.manifest = self.root / "roster.json"
        self.digest = hashlib.sha256(b"one published blind-review packet").hexdigest()

    def write_roster(self, *reviewers):
        roster = {name: {"packet_sha256": self.digest, "vote_file": f"{name}.json"}
                  for name in reviewers}
        self.manifest.write_text(json.dumps({"reviewers": roster}), encoding="utf-8")
        return roster

    def write_vote(self, file_owner, *, reviewer=None, digest=None, choice="A"):
        path = self.root / f"{file_owner}.json"
        path.write_text(json.dumps({"reviewer": reviewer or file_owner,
                                    "packet_sha256": digest or self.digest, "choice": choice}),
                        encoding="utf-8")
        return path

    def run_cli(self, expected):
        result = subprocess.run(
            [sys.executable, "-B", str(PACKAGE / "scripts/check_review_votes.py"), str(self.manifest)],
            cwd=PACKAGE, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, expected, result.stderr)
        return json.loads(result.stdout) if expected != 2 else result.stderr

    def test_collects_all_bad_receipts_without_requeueing_valid_votes(self):
        self.write_roster("left", "right", "absent", "partial", "old")
        first = self.write_vote("left")
        second = self.write_vote("right", choice="tie")
        kept = [first.read_bytes(), second.read_bytes()]
        (self.root / "partial.json").write_text('{"reviewer":', encoding="utf-8")
        self.write_vote("old", digest="0" * 64)

        report = self.run_cli(1)
        self.assertEqual(report, {"accepted": ["left", "right"], "needs_ballot": {
            "absent": "missing", "partial": "invalid_json", "old": "packet_mismatch",
        }})
        for name in report["needs_ballot"]:
            self.write_vote(name, choice="B")
        completed = self.run_cli(0)
        self.assertEqual(completed["needs_ballot"], {})
        self.assertEqual(len(completed["accepted"]), 5)
        self.assertEqual([first.read_bytes(), second.read_bytes()], kept)

    def test_swapped_and_invalid_votes_are_listed_together(self):
        self.write_roster("first", "second", "third", "duplicate")
        self.write_vote("first", reviewer="second")
        self.write_vote("second", choice="candidate")
        (self.root / "third.json").mkdir()
        duplicate = self.write_vote("duplicate")
        duplicate.write_text(duplicate.read_text().replace('"choice": "A"', '"choice": "A", "choice": "B"'))
        self.assertEqual(self.run_cli(1)["needs_ballot"], {
            "first": "reviewer_mismatch", "second": "invalid_ballot", "third": "unreadable",
            "duplicate": "invalid_json",
        })
        link = self.root / "third.json"
        link.rmdir()
        try:
            link.symlink_to(link)
        except (NotImplementedError, OSError):
            return
        self.assertEqual(self.run_cli(1)["needs_ballot"]["third"], "unreadable")

    def test_rejects_invalid_manifest_and_duplicate_paths(self):
        roster = self.write_roster("left", "right")
        roster["right"]["vote_file"] = "left.json"
        for reviewers, message in (({}, "nonempty"), (roster, "distinct"),
                                   ({"left": {"packet_sha256": "old"}}, "SHA-256")):
            with self.subTest(message=message):
                self.manifest.write_text(json.dumps({"reviewers": reviewers}), encoding="utf-8")
                self.assertIn(message, self.run_cli(2))
        self.manifest.write_text('{"reviewers":{"left":{},"left":{}}}', encoding="utf-8")
        self.assertIn("duplicate JSON key", self.run_cli(2))

    def test_byte_order_mark_is_accepted_and_deep_nesting_is_reported(self):
        self.write_roster("marked", "nested")
        marked = self.write_vote("marked")
        marked.write_bytes(b"\xef\xbb\xbf" + marked.read_bytes())
        (self.root / "nested.json").write_text("[" * 100000 + "]" * 100000, encoding="utf-8")
        self.assertEqual(self.run_cli(1), {"accepted": ["marked"], "needs_ballot": {"nested": "invalid_json"}})

        self.manifest.write_bytes(b"\xef\xbb\xbf" + self.manifest.read_bytes())
        self.assertEqual(self.run_cli(1)["accepted"], ["marked"])
        self.manifest.write_text('{"reviewers": ' + "[" * 100000 + "]" * 100000 + "}", encoding="utf-8")
        error = self.run_cli(2)
        self.assertIn("nested too deeply", error)
        self.assertNotIn("Traceback", error)

    def test_consumes_digest_from_existing_blind_packet_key(self):
        for name, text in (("brief", "Judge clarity."), ("base", "Open at nine."),
                           ("candidate", "Hours start at 09:00.")):
            (self.root / f"{name}.txt").write_text(text, encoding="utf-8")
        key = self.root / "key.json"
        packet = subprocess.run(
            [sys.executable, "-B", str(PACKAGE / "scripts/blind_review.py"),
             str(self.root / "base.txt"), str(self.root / "candidate.txt"),
             "--brief", str(self.root / "brief.txt"), "--key-out", str(key)],
            capture_output=True, check=True, timeout=10,
        ).stdout
        self.digest = json.loads(key.read_bytes())["packet_sha256"]
        self.assertEqual(self.digest, hashlib.sha256(packet).hexdigest())
        self.write_roster("judge")
        self.write_vote("judge")
        self.assertEqual(self.run_cli(0), {"accepted": ["judge"], "needs_ballot": {}})
