"""Check which blind-review ballots still need to be collected."""

import argparse
import json
from pathlib import Path
import re


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def read_json(path):
    # utf-8-sig accepts the byte order mark that Windows PowerShell 5.1 writes for "UTF8".
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_keys)


def load_roster(manifest_path):
    manifest = read_json(manifest_path)
    reviewers = manifest.get("reviewers") if isinstance(manifest, dict) else None
    if not isinstance(reviewers, dict) or not reviewers:
        raise ValueError("manifest requires a nonempty reviewers object")

    roster = {}
    paths = set()
    for name, entry in reviewers.items():
        if not name.strip() or not isinstance(entry, dict):
            raise ValueError("reviewers require a nonempty ID and an object")
        digest = entry.get("packet_sha256")
        filename = entry.get("vote_file")
        if not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
            raise ValueError(f"{name}: packet_sha256 must be a lowercase SHA-256 digest")
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError(f"{name}: vote_file must be a nonempty path")
        path = manifest_path.parent / filename
        try:
            path = path.resolve()
        except (OSError, RuntimeError):
            path = path.absolute()
        if path in paths:
            raise ValueError("vote files must be distinct")
        paths.add(path)
        roster[name] = (path, digest)
    return roster


def ballot_problem(name, path, digest):
    try:
        ballot = read_json(path)
    except FileNotFoundError:
        return "missing"
    except OSError:
        return "unreadable"
    except (ValueError, RecursionError):
        return "invalid_json"
    if not isinstance(ballot, dict) or ballot.get("choice") not in ("A", "B", "tie"):
        return "invalid_ballot"
    if ballot.get("reviewer") != name:
        return "reviewer_mismatch"
    if ballot.get("packet_sha256") != digest:
        return "packet_mismatch"
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="manager's frozen reviewer roster")
    args = parser.parse_args()
    try:
        roster = load_roster(args.manifest)
    except RecursionError:
        parser.exit(2, "review votes: manifest JSON is nested too deeply\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"review votes: {exc}\n")

    accepted = []
    needs_ballot = {}
    for name, (path, digest) in roster.items():
        problem = ballot_problem(name, path, digest)
        if problem is None:
            accepted.append(name)
        else:
            needs_ballot[name] = problem
    print(json.dumps({"accepted": accepted, "needs_ballot": needs_ballot}, ensure_ascii=True, indent=2))
    return int(bool(needs_ballot))


if __name__ == "__main__":
    raise SystemExit(main())
