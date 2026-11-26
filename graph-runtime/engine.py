"""Single-host graph scheduler with SQLite checkpoints and explicit approvals."""

from collections.abc import Mapping
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import contextmanager
from datetime import datetime, timezone
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
import hashlib
import hmac
import json
import os
import secrets
import sqlite3


SQLITE_MAX_INTEGER = (1 << 63) - 1


SCHEMA = """
BEGIN;
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY, version TEXT NOT NULL, graph TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS nodes (
    run_id TEXT NOT NULL REFERENCES runs(id), id TEXT NOT NULL, spec TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING', attempt INTEGER NOT NULL DEFAULT 0,
    revision INTEGER NOT NULL DEFAULT 1, fingerprint TEXT, token TEXT,
    output TEXT, error TEXT, PRIMARY KEY (run_id, id)
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id), node_id TEXT,
    event TEXT NOT NULL, details TEXT NOT NULL, at TEXT NOT NULL
);
PRAGMA user_version = 1;
COMMIT;
"""


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _decode(value):
    return json.loads(value) if value is not None else None


def _approval_token():
    """Return a random approval token that a command line cannot mistake for an option."""
    return "bjm_" + secrets.token_urlsafe(24)


def _validated_graph(graph):
    if not isinstance(graph, dict) or not isinstance(graph.get("version"), str) or not graph["version"].strip():
        raise ValueError("graph.version must be a nonempty string")
    if not isinstance(graph.get("nodes"), list) or not graph["nodes"]:
        raise ValueError("graph.nodes must be a nonempty list")
    nodes = {}
    for entry in graph["nodes"]:
        if not isinstance(entry, dict):
            raise ValueError("each node must be an object")
        node_id = entry.get("id")
        if not isinstance(node_id, str) or not node_id.strip() or node_id in nodes:
            raise ValueError("node IDs must be nonempty and unique")
        kind = entry.get("kind", "task")
        deps, inputs = entry.get("deps", []), entry.get("inputs", {})
        retry_safe = entry.get("retry_safe", False)
        if kind not in ("task", "approval") or not isinstance(retry_safe, bool):
            raise ValueError(f"invalid kind or retry_safe for {node_id}")
        if "retry_on_interrupt" in entry and (kind != "task" or type(entry["retry_on_interrupt"]) is not bool):
            raise ValueError(f"retry_on_interrupt must be a boolean on a task node: {node_id}")
        if not isinstance(deps, list) or not all(isinstance(dep, str) for dep in deps) or len(deps) != len(set(deps)):
            raise ValueError(f"deps must contain unique node IDs for {node_id}")
        if not isinstance(inputs, dict):
            raise ValueError(f"inputs must be an object for {node_id}")
        nodes[node_id] = dict(id=node_id, kind=kind, deps=deps, inputs=inputs, retry_safe=retry_safe)
        if "retry_on_interrupt" in entry:
            nodes[node_id]["retry_on_interrupt"] = entry["retry_on_interrupt"]
    if any(dep not in nodes for node in nodes.values() for dep in node["deps"]):
        raise ValueError("every dependency must name a declared node")
    try:
        tuple(TopologicalSorter({name: node["deps"] for name, node in nodes.items()}).static_order())
    except CycleError as exc:
        raise ValueError("graph has a dependency cycle") from exc
    return {"version": graph["version"], "nodes": list(nodes.values())}


@contextmanager
def _exclusive(lock_path):
    """Process-owned lock. OS releases it if the coordinator dies."""
    with lock_path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)

            def acquire():
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)

            def release():
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            def acquire():
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)

            def release():
                fcntl.flock(handle, fcntl.LOCK_UN)
        try:
            acquire()
        except OSError as exc:
            raise RuntimeError("another coordinator owns this database") from exc
        try:
            yield
        finally:
            release()


class InputRejected(ValueError):
    """The input must change and this attempt produced no external effects."""


def _can_retry_interrupted(spec):
    return spec["retry_safe"] and spec.get("retry_on_interrupt", True)


class Engine:
    def __init__(self, db_path, *, initialize=True):
        self.db_path = Path(db_path).resolve()
        self.lock_path = self.db_path.with_name(self.db_path.name + ".lock")
        schema_version = 0
        if self.db_path.exists():
            with self._connect() as db:
                schema_version = db.execute("PRAGMA user_version").fetchone()[0]
        if schema_version == 0:
            if not initialize:
                raise ValueError("database is not initialized; run init first")
            with _exclusive(self.lock_path), self._connect() as db:
                db.execute("PRAGMA journal_mode = WAL")
                db.executescript(SCHEMA)
        elif schema_version != 1:
            raise ValueError(f"unsupported database schema version: {schema_version}")

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.db_path)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys = ON")
            with db:
                yield db
        finally:
            db.close()

    @contextmanager
    def _write(self):
        with _exclusive(self.lock_path), self._connect() as db:
            yield db

    @staticmethod
    def _run_info(db, run_id):
        row = db.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise ValueError(f"unknown run: {run_id}")
        return row

    @staticmethod
    def _nodes(db, run_id):
        rows = db.execute("SELECT * FROM nodes WHERE run_id = ? ORDER BY rowid", (run_id,))
        return {row["id"]: dict(row) for row in rows}

    @staticmethod
    def _event(db, run_id, node_id, event, **details):
        db.execute(
            "INSERT INTO events(run_id,node_id,event,details,at) VALUES (?,?,?,?,?)",
            (run_id, node_id, event, _json(details), datetime.now(timezone.utc).isoformat()),
        )

    @staticmethod
    def _update(db, run_id, node_id, **fields):
        names = ", ".join(f"{name} = ?" for name in fields)
        db.execute(f"UPDATE nodes SET {names} WHERE run_id = ? AND id = ?",
                   (*fields.values(), run_id, node_id))

    @staticmethod
    def _node(nodes, node_id):
        if node_id not in nodes:
            raise ValueError(f"unknown node: {node_id}")
        return nodes[node_id]

    @staticmethod
    def _fingerprint(run_id, version, row, spec, nodes):
        payload = {
            "run": run_id, "version": version, "node": spec, "revision": row["revision"],
            "deps": {dep: [nodes[dep]["fingerprint"], nodes[dep]["output"]] for dep in spec["deps"]},
        }
        return hashlib.sha256(_json(payload).encode()).hexdigest()

    @staticmethod
    def _approval_content(spec, nodes):
        """Digest what a reviewer sees: the approval's own inputs and its dependencies' outputs.

        Unlike the fingerprint it leaves out revisions, so the same content keeps the same digest
        after edits that change something and then change it back.
        """
        payload = {"inputs": spec["inputs"], "deps": {dep: nodes[dep]["output"] for dep in spec["deps"]}}
        return hashlib.sha256(_json(payload).encode()).hexdigest()

    @staticmethod
    def _rejected_revision(db, run_id, node_id, content):
        """Return the revision at which a reviewer rejected this exact content, or None."""
        rows = db.execute("SELECT details FROM events WHERE run_id = ? AND node_id = ? AND event = ? ORDER BY id",
                          (run_id, node_id, "APPROVAL_REJECTED"))
        for row in rows:
            details = _decode(row["details"])
            if isinstance(details, dict) and details.get("content_sha256") == content:
                return details.get("revision")
        return None

    @staticmethod
    def _queued(nodes):
        """Task specs still to run, in database order: pending, or interrupted and safe to start again."""
        queued = []
        for row in nodes.values():
            spec = _decode(row["spec"])
            if spec["kind"] == "task" and (row["status"] == "PENDING" or (
                    row["status"] == "RUNNING" and _can_retry_interrupted(spec))):
                queued.append(spec)
        return queued

    @staticmethod
    def _runnable(nodes, queued):
        """The queued tasks this run can start.

        A task behind an approval, or behind a node that stays failed, uncertain or rejected for the
        whole run, cannot start in this run and is left out.
        """
        deps = {spec["id"]: spec["deps"] for spec in queued}
        runnable = set()
        for name in TopologicalSorter(deps).static_order():
            if name in deps and all(nodes[dep]["status"] == "SUCCEEDED" or dep in runnable for dep in deps[name]):
                runnable.add(name)
        return [spec for spec in queued if spec["id"] in runnable]

    def init(self, run_id, graph, *, check=None):
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("run_id must be a nonempty string")
        graph = _validated_graph(graph)
        if check is not None:
            check(graph["nodes"])
        encoded = _json(graph)
        with self._write() as db:
            existing = db.execute("SELECT graph FROM runs WHERE id = ?", (run_id,)).fetchone()
            if existing is not None:
                if existing["graph"] != encoded:
                    raise ValueError("run already exists with a different graph; choose a new run ID")
            else:
                db.execute("INSERT INTO runs VALUES (?,?,?)", (run_id, graph["version"], encoded))
                db.executemany("INSERT INTO nodes(run_id,id,spec) VALUES (?,?,?)",
                               [(run_id, node["id"], _json(node)) for node in graph["nodes"]])
                self._event(db, run_id, None, "RUN_CREATED", graph_version=graph["version"])
        return self.status(run_id)

    def status(self, run_id):
        with self._connect() as db:
            db.execute("BEGIN")
            version = self._run_info(db, run_id)["version"]
            rows = self._nodes(db, run_id)
        nodes = {}
        for name, row in rows.items():
            node = {key: row[key] for key in ("status", "attempt", "revision", "token", "fingerprint", "error")}
            node["output"] = _decode(row["output"])
            nodes[name] = node
        return {"run_id": run_id, "graph_version": version, "nodes": nodes}

    def events(self, run_id, *, after=None, limit=None):
        """Read one run's ordered event rows, optionally from an exclusive cursor."""
        if after is not None and (type(after) is not int or not 0 <= after <= SQLITE_MAX_INTEGER):
            raise ValueError("after must be a nonnegative SQLite integer")
        if limit is not None:
            if after is None:
                raise ValueError("limit requires an after cursor")
            if type(limit) is not int or not 1 <= limit <= SQLITE_MAX_INTEGER:
                raise ValueError("limit must be a positive SQLite integer")

        query = "SELECT * FROM events WHERE run_id = ?"
        parameters = [run_id]
        if after is not None:
            query += " AND id > ?"
            parameters.append(after)
        query += " ORDER BY id"
        if limit is not None:
            query += " LIMIT ?"
            parameters.append(limit)

        with self._connect() as db:
            self._run_info(db, run_id)
            rows = db.execute(query, parameters)
            return [dict(row, details=_decode(row["details"])) for row in rows]

    def _recover(self, db, run_id, nodes):
        for node_id, row in nodes.items():
            if row["status"] != "RUNNING":
                continue
            safe = _can_retry_interrupted(_decode(row["spec"]))
            state = "PENDING" if safe else "UNCERTAIN"
            self._update(db, run_id, node_id, status=state, error="coordinator interrupted")
            self._event(db, run_id, node_id, "RECOVERED" if safe else "UNCERTAIN", attempt=row["attempt"])
        db.commit()

    def run(self, run_id, handler, workers=2, *, preflight=None, worker_limits=None):
        """Dispatch tasks with an optional concurrency limit per inputs.operation."""
        if type(workers) is not int or workers < 1:
            raise ValueError("workers must be a positive integer")
        limits = {} if worker_limits is None else worker_limits
        if not isinstance(limits, Mapping) or any(
                not isinstance(name, str) or type(limit) is not int or limit < 1
                for name, limit in limits.items()):
            raise ValueError("operation worker limits must be positive integers")
        limits = dict(limits)
        with self._write() as db, ThreadPoolExecutor(max_workers=workers) as pool:
            version = self._run_info(db, run_id)["version"]
            nodes = self._nodes(db, run_id)
            if preflight is not None:
                queued = self._queued(nodes)
                preflight(queued, self._runnable(nodes, queued))
            self._recover(db, run_id, nodes)
            futures = {}
            in_flight = dict.fromkeys(limits, 0)
            while True:
                nodes = self._nodes(db, run_id)
                for node_id, row in nodes.items():
                    if row["status"] != "PENDING":
                        continue
                    spec = _decode(row["spec"])
                    if any(nodes[dep]["status"] != "SUCCEEDED" for dep in spec["deps"]):
                        continue
                    group = None
                    if spec["kind"] == "task":
                        if len(futures) >= workers:
                            continue
                        operation = spec["inputs"].get("operation")
                        if isinstance(operation, str) and operation in limits:
                            if in_flight[operation] >= limits[operation]:
                                continue
                            group = operation
                    fingerprint = self._fingerprint(run_id, version, row, spec, nodes)
                    if spec["kind"] == "approval":
                        content = self._approval_content(spec, nodes)
                        rejected_at = self._rejected_revision(db, run_id, node_id, content)
                        if rejected_at is not None:
                            # A reviewer already turned this exact content down; do not ask again.
                            error = f"ApprovalRejected: the same content was rejected at revision {rejected_at}"
                            self._update(db, run_id, node_id, status="REJECTED", fingerprint=fingerprint,
                                         token=None, error=error)
                            self._event(db, run_id, node_id, "REJECTION_KEPT", fingerprint=fingerprint,
                                        revision=row["revision"], content_sha256=content,
                                        rejected_revision=rejected_at)
                        else:
                            token = _approval_token()
                            self._update(db, run_id, node_id, status="AWAITING_APPROVAL", fingerprint=fingerprint,
                                         token=token)
                            self._event(db, run_id, node_id, "AWAITING_APPROVAL", fingerprint=fingerprint)
                        db.commit()
                    else:
                        attempt = row["attempt"] + 1
                        self._update(db, run_id, node_id, status="RUNNING", attempt=attempt,
                                     fingerprint=fingerprint, error=None)
                        self._event(db, run_id, node_id, "STARTED", attempt=attempt, fingerprint=fingerprint)
                        db.commit()
                        inputs = {dep: _decode(nodes[dep]["output"]) for dep in spec["deps"]}
                        futures[pool.submit(handler, spec, inputs)] = (node_id, attempt, spec["retry_safe"], group)
                        if group is not None:
                            in_flight[group] += 1
                if not futures:
                    break
                finished, _ = wait(futures, return_when=FIRST_COMPLETED)
                for future in finished:
                    node_id, attempt, safe, group = futures.pop(future)
                    if group is not None:
                        in_flight[group] -= 1
                    try:
                        output = _json(future.result())
                        output.encode("utf-8")
                    except Exception as exc:
                        if isinstance(exc, InputRejected):
                            state = "REJECTED"
                        else:
                            state = "FAILED" if safe else "UNCERTAIN"
                        # Adapters write InputRejected messages themselves, so they are kept to say what to fix.
                        error = f"InputRejected: {exc}" if state == "REJECTED" else type(exc).__name__
                        self._update(db, run_id, node_id, status=state, error=error)
                        self._event(db, run_id, node_id, state, attempt=attempt, error=error)
                    else:
                        self._update(db, run_id, node_id, status="SUCCEEDED", output=output)
                        self._event(db, run_id, node_id, "SUCCEEDED", attempt=attempt)
                    db.commit()
        return self.status(run_id)

    def retry(self, run_id, node_id):
        with self._write() as db:
            row = self._node(self._nodes(db, run_id), node_id)
            # A retry-safe node is UNCERTAIN only after an interruption with retry_on_interrupt false.
            if row["status"] not in ("FAILED", "UNCERTAIN") or not _decode(row["spec"])["retry_safe"]:
                raise ValueError("retry requires a failed or interrupted retry-safe node")
            self._update(db, run_id, node_id, status="PENDING", error=None)
            self._event(db, run_id, node_id, "RETRY_REQUESTED", attempt=row["attempt"], previous=row["status"])
        return self.status(run_id)

    def resolve(self, run_id, node_id, output):
        encoded = _json(output)
        with self._write() as db:
            row = self._node(self._nodes(db, run_id), node_id)
            if row["status"] != "UNCERTAIN":
                raise ValueError("resolve requires an uncertain node with an externally verified result")
            self._update(db, run_id, node_id, status="SUCCEEDED", output=encoded, error=None)
            self._event(db, run_id, node_id, "RESOLVED", attempt=row["attempt"])
        return self.status(run_id)

    def approve(self, run_id, node_id, token):
        return self._decide_approval(run_id, node_id, token, approved=True)

    def reject(self, run_id, node_id, token):
        return self._decide_approval(run_id, node_id, token, approved=False)

    def _decide_approval(self, run_id, node_id, token, *, approved):
        with self._write() as db:
            version = self._run_info(db, run_id)["version"]
            nodes = self._nodes(db, run_id)
            row = self._node(nodes, node_id)
            spec = _decode(row["spec"])
            # Name the state first, so an operator is not sent looking for a mistyped token.
            if spec["kind"] != "approval":
                raise ValueError(f"{node_id} is not an approval node")
            if row["status"] == "REJECTED":
                raise ValueError(f"{node_id} was rejected; revise what it approves, then run again for a new token")
            if row["status"] == "SUCCEEDED":
                raise ValueError(f"{node_id} is already approved")
            if row["status"] != "AWAITING_APPROVAL":
                raise ValueError(f"{node_id} is not awaiting a decision; run the workflow until it issues a token")
            if (not isinstance(row["token"], str) or not isinstance(token, str)
                    or not hmac.compare_digest(row["token"].encode(), token.encode())
                    or any(nodes[dep]["status"] != "SUCCEEDED" for dep in spec["deps"])
                    or row["fingerprint"] != self._fingerprint(run_id, version, row, spec, nodes)):
                raise ValueError("stale or invalid approval token")
            content = self._approval_content(spec, nodes)
            if approved:
                # run issues no token for rejected content, but an older version may have issued this one.
                rejected_at = self._rejected_revision(db, run_id, node_id, content)
                if rejected_at is not None:
                    raise ValueError(f"{node_id}: the same content was rejected at revision {rejected_at}; "
                                     "revise what it approves, then run again for a new token")
                output = _json({"approved": True, "fingerprint": row["fingerprint"]})
                self._update(db, run_id, node_id, status="SUCCEEDED", token=None, output=output)
                self._event(db, run_id, node_id, "APPROVED", fingerprint=row["fingerprint"])
            else:
                self._update(db, run_id, node_id, status="REJECTED", token=None, output=None,
                             error="ApprovalRejected")
                self._event(db, run_id, node_id, "APPROVAL_REJECTED", fingerprint=row["fingerprint"],
                            revision=row["revision"], content_sha256=content)
        return self.status(run_id)

    def edit(self, run_id, node_id, inputs):
        if not isinstance(inputs, dict):
            raise ValueError("inputs must be an object")
        with self._write() as db:
            nodes = self._nodes(db, run_id)
            row = self._node(nodes, node_id)
            spec = _decode(row["spec"])
            if _json(spec["inputs"]) != _json(inputs):
                affected = {node_id}
                remaining = set(nodes) - affected
                while True:
                    added = {name for name in remaining if affected.intersection(_decode(nodes[name]["spec"])["deps"])}
                    if not added:
                        break
                    affected.update(added)
                    remaining.difference_update(added)
                if any(nodes[name]["status"] in ("RUNNING", "UNCERTAIN") for name in affected):
                    raise ValueError("resolve in-flight or uncertain external work, or retry it if it is "
                                     "retry-safe, before editing affected nodes")
                for name in affected:
                    previous = _decode(nodes[name]["spec"])
                    if (nodes[name]["status"] == "SUCCEEDED" and previous["kind"] == "task"
                            and not previous["retry_safe"]):
                        raise ValueError(f"editing would repeat completed external work: {name}; start a new run")
                spec["inputs"] = inputs
                self._update(db, run_id, node_id, spec=_json(spec))
                for name in sorted(affected):
                    revision = nodes[name]["revision"] + 1
                    self._update(db, run_id, name, status="PENDING", revision=revision, token=None,
                                 output=None, fingerprint=None, error=None)
                    self._event(db, run_id, name, "INVALIDATED", changed_node=node_id, revision=revision)
        return self.status(run_id)
