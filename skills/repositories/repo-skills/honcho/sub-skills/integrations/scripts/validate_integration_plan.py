#!/usr/bin/env python3
"""Validate a proposed Honcho integration plan without calling Honcho.

This helper checks common integration design errors before coding: unstable or
unsafe IDs, sessions missing peers, message authors not attached to sessions,
invalid read paths, conclusion query filters missing observer/observed pairs,
and webhook URL issues. It uses only the Python standard library.

Example:
  python validate_integration_plan.py --example > plan.json
  python validate_integration_plan.py plan.json
  python validate_integration_plan.py - < plan.json

Plan schema is intentionally small and permissive; unknown keys are ignored so
teams can keep product-specific notes in the same file.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")
REASONING_LEVELS = {"minimal", "low", "medium", "high", "max"}
READ_TYPES = {"context", "representation", "chat", "search", "conclusions"}


EXAMPLE_PLAN: dict[str, Any] = {
    "workspace_id": "my-app",
    "peers": [
        {"id": "user-123", "kind": "human", "observe_me": True},
        {"id": "assistant", "kind": "assistant", "observe_me": False},
    ],
    "sessions": [
        {
            "id": "thread-123",
            "peers": [
                {"id": "user-123", "observe_me": True, "observe_others": True},
                {"id": "assistant", "observe_me": False, "observe_others": True},
            ],
            "messages": [
                {"peer_id": "user-123", "content": "I prefer concise answers."},
                {"peer_id": "assistant", "content": "I will be concise."},
            ],
        }
    ],
    "reads": [
        {
            "type": "context",
            "session_id": "thread-123",
            "peer_target": "user-123",
            "peer_perspective": "assistant",
            "tokens": 4000,
        },
        {
            "type": "chat",
            "observer": "assistant",
            "target": "user-123",
            "session_id": "thread-123",
            "query": "How should I adapt to this user?",
            "reasoning_level": "low",
        },
        {
            "type": "conclusions",
            "operation": "query",
            "query": "communication style",
            "filters": {"observer_id": "assistant", "observed_id": "user-123"},
        },
    ],
    "webhooks": [
        {"url": "https://example.com/honcho/webhook", "purpose": "queue.empty hints"}
    ],
    "mcp": {"uses_workspace_header": True},
}


@dataclass
class Finding:
    level: str
    path: str
    message: str


@dataclass
class Validator:
    data: dict[str, Any]
    findings: list[Finding] = field(default_factory=list)

    def error(self, path: str, message: str) -> None:
        self.findings.append(Finding("ERROR", path, message))

    def warn(self, path: str, message: str) -> None:
        self.findings.append(Finding("WARN", path, message))

    def validate(self) -> list[Finding]:
        if not isinstance(self.data, dict):
            self.error("$", "Plan root must be a JSON object")
            return self.findings
        self._validate_workspace()
        peer_ids = self._validate_peers()
        session_ids = self._validate_sessions(peer_ids)
        self._validate_reads(peer_ids, session_ids)
        self._validate_webhooks()
        self._validate_mcp()
        return self.findings

    def _validate_workspace(self) -> None:
        workspace = self.data.get("workspace_id") or self.data.get("workspaceId")
        if not isinstance(workspace, str) or not workspace.strip():
            self.error("workspace_id", "Provide one non-empty workspace_id")
        elif not SAFE_ID.fullmatch(workspace):
            self.warn(
                "workspace_id",
                "Workspace contains characters outside the conservative safe ID set [A-Za-z0-9_-]",
            )

    def _validate_peers(self) -> set[str]:
        peers = self.data.get("peers", [])
        if not isinstance(peers, list) or not peers:
            self.error("peers", "Define at least one peer")
            return set()
        seen: set[str] = set()
        for i, peer in enumerate(peers):
            path = f"peers[{i}]"
            if isinstance(peer, str):
                peer_id = peer
            elif isinstance(peer, dict):
                peer_id = peer.get("id") or peer.get("peer_id") or peer.get("peerId")
                for key in ("observe_me", "observeMe"):
                    if key in peer and not isinstance(peer[key], bool):
                        self.error(f"{path}.{key}", "Observation flags must be booleans")
            else:
                self.error(path, "Peer must be an ID string or object")
                continue
            if not isinstance(peer_id, str) or not peer_id.strip():
                self.error(f"{path}.id", "Peer ID must be a non-empty string")
                continue
            if peer_id in seen:
                self.warn(f"{path}.id", f"Duplicate peer ID {peer_id!r}")
            seen.add(peer_id)
            if not SAFE_ID.fullmatch(peer_id):
                self.error(
                    f"{path}.id",
                    "Peer ID should use only letters, digits, underscore, and hyphen for broad SDK/MCP compatibility",
                )
            if peer_id.lower() in {"user", "default", "anonymous"}:
                self.warn(
                    f"{path}.id",
                    "Generic peer IDs often fragment or mix users; prefer a durable account or channel identity",
                )
        return seen

    def _validate_sessions(self, peer_ids: set[str]) -> set[str]:
        sessions = self.data.get("sessions", [])
        if not isinstance(sessions, list) or not sessions:
            self.error("sessions", "Define at least one session")
            return set()
        seen: set[str] = set()
        for i, session in enumerate(sessions):
            path = f"sessions[{i}]"
            if not isinstance(session, dict):
                self.error(path, "Session must be an object")
                continue
            session_id = session.get("id") or session.get("session_id") or session.get("sessionId")
            if not isinstance(session_id, str) or not session_id.strip():
                self.error(f"{path}.id", "Session ID must be a non-empty string")
                continue
            seen.add(session_id)
            if not SAFE_ID.fullmatch(session_id):
                self.warn(
                    f"{path}.id",
                    "Session ID contains characters outside the conservative safe ID set [A-Za-z0-9_-]",
                )
            session_peer_ids = self._session_peer_ids(session.get("peers"), f"{path}.peers")
            if not session_peer_ids:
                self.warn(f"{path}.peers", "Session has no peers; observations may not be configured as intended")
            for pid in session_peer_ids:
                if peer_ids and pid not in peer_ids:
                    self.warn(f"{path}.peers", f"Peer {pid!r} is used in a session but not declared in top-level peers")
            messages = session.get("messages", [])
            if messages is not None:
                self._validate_messages(messages, path, session_peer_ids)
        return seen

    def _session_peer_ids(self, peers: Any, path: str) -> set[str]:
        ids: set[str] = set()
        if peers is None:
            return ids
        if isinstance(peers, dict):
            iterable = peers.items()
            for peer_id, config in iterable:
                if isinstance(peer_id, str):
                    ids.add(peer_id)
                else:
                    self.error(path, "Peer map keys must be strings")
                if isinstance(config, dict):
                    for key in ("observe_me", "observe_others", "observeMe", "observeOthers"):
                        if key in config and not isinstance(config[key], bool):
                            self.error(f"{path}.{peer_id}.{key}", "Observation flags must be booleans")
        elif isinstance(peers, list):
            for j, item in enumerate(peers):
                p = f"{path}[{j}]"
                if isinstance(item, str):
                    ids.add(item)
                elif isinstance(item, dict):
                    peer_id = item.get("id") or item.get("peer_id") or item.get("peerId")
                    if isinstance(peer_id, str):
                        ids.add(peer_id)
                    else:
                        self.error(f"{p}.id", "Session peer object needs id/peer_id")
                    for key in ("observe_me", "observe_others", "observeMe", "observeOthers"):
                        if key in item and not isinstance(item[key], bool):
                            self.error(f"{p}.{key}", "Observation flags must be booleans")
                elif isinstance(item, list) and item and isinstance(item[0], str):
                    ids.add(item[0])
                else:
                    self.error(p, "Session peer must be a string, object, or [id, config] pair")
        else:
            self.error(path, "Session peers must be a list or object map")
        return ids

    def _validate_messages(self, messages: Any, session_path: str, session_peer_ids: set[str]) -> None:
        if not isinstance(messages, list):
            self.error(f"{session_path}.messages", "Messages must be a list")
            return
        if len(messages) > 100:
            self.warn(f"{session_path}.messages", "Honcho message create accepts batches of at most 100; chunk larger imports")
        for j, msg in enumerate(messages):
            path = f"{session_path}.messages[{j}]"
            if not isinstance(msg, dict):
                self.error(path, "Message must be an object")
                continue
            peer_id = msg.get("peer_id") or msg.get("peerId")
            content = msg.get("content")
            if not isinstance(peer_id, str) or not peer_id:
                self.error(f"{path}.peer_id", "Message needs peer_id")
            elif session_peer_ids and peer_id not in session_peer_ids:
                self.warn(f"{path}.peer_id", f"Message peer {peer_id!r} is not attached to this session")
            if not isinstance(content, str):
                self.error(f"{path}.content", "Message content must be a string")
            elif content.strip() == "" and content != "":
                self.error(f"{path}.content", "Message content cannot be only whitespace")

    def _validate_reads(self, peer_ids: set[str], session_ids: set[str]) -> None:
        reads = self.data.get("reads", [])
        if reads is None:
            return
        if not isinstance(reads, list):
            self.error("reads", "Reads must be a list")
            return
        for i, read in enumerate(reads):
            path = f"reads[{i}]"
            if not isinstance(read, dict):
                self.error(path, "Read must be an object")
                continue
            read_type = read.get("type")
            if read_type not in READ_TYPES:
                self.error(f"{path}.type", f"Read type must be one of {sorted(READ_TYPES)}")
                continue
            session_id = read.get("session_id") or read.get("sessionId")
            if isinstance(session_id, str) and session_ids and session_id not in session_ids:
                self.warn(f"{path}.session_id", f"Read references undeclared session {session_id!r}")
            if read_type == "context":
                peer_target = read.get("peer_target") or read.get("peerTarget")
                peer_perspective = read.get("peer_perspective") or read.get("peerPerspective")
                search_query = read.get("search_query") or read.get("searchQuery")
                if peer_perspective and not peer_target:
                    self.error(path, "Context read with peer_perspective requires peer_target")
                if search_query and not peer_target:
                    self.warn(path, "Session context search only affects peer representation when peer_target is set")
            if read_type in {"representation", "chat"}:
                observer = read.get("observer") or read.get("peer_id") or read.get("peerId")
                target = read.get("target") or read.get("observed")
                for key, value in (("observer", observer), ("target", target)):
                    if value and peer_ids and value not in peer_ids:
                        self.warn(f"{path}.{key}", f"Read references undeclared peer {value!r}")
            if read_type == "chat":
                level = read.get("reasoning_level") or read.get("reasoningLevel")
                if level is not None and level not in REASONING_LEVELS:
                    self.error(f"{path}.reasoning_level", f"Must be one of {sorted(REASONING_LEVELS)}")
                if not isinstance(read.get("query"), str) or not read.get("query"):
                    self.error(f"{path}.query", "Chat read needs a non-empty query")
            if read_type == "conclusions":
                op = read.get("operation", "list")
                filters = read.get("filters") or {}
                if op == "query":
                    has_observer = any(k in filters for k in ("observer", "observer_id"))
                    has_observed = any(k in filters for k in ("observed", "observed_id"))
                    if not (has_observer and has_observed):
                        self.error(path, "Conclusion query requires observer/observed filters")

    def _validate_webhooks(self) -> None:
        webhooks = self.data.get("webhooks", [])
        if webhooks is None:
            return
        if not isinstance(webhooks, list):
            self.error("webhooks", "Webhooks must be a list")
            return
        for i, hook in enumerate(webhooks):
            path = f"webhooks[{i}]"
            if isinstance(hook, str):
                url = hook
            elif isinstance(hook, dict):
                url = hook.get("url")
            else:
                self.error(path, "Webhook must be a URL string or object with url")
                continue
            if not isinstance(url, str):
                self.error(f"{path}.url", "Webhook URL must be a string")
                continue
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                self.error(f"{path}.url", "Webhook URL must be absolute http(s)")
                continue
            host = parsed.hostname
            if host:
                try:
                    ip = ipaddress.ip_address(host)
                except ValueError:
                    ip = None
                if ip is not None and (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_reserved
                    or ip.is_multicast
                    or ip.is_unspecified
                ):
                    self.error(f"{path}.url", "Webhook URL IP literal is private/internal/reserved")

    def _validate_mcp(self) -> None:
        mcp = self.data.get("mcp")
        if mcp is None:
            return
        if not isinstance(mcp, dict):
            self.error("mcp", "MCP section must be an object")
            return
        if not mcp.get("uses_workspace_header") and not (self.data.get("workspace_id") or self.data.get("workspaceId")):
            self.warn("mcp", "Without X-Honcho-Workspace-ID, every MCP tool call must pass workspace_id")


def load_plan(path: str) -> dict[str, Any]:
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Plan root must be a JSON object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Honcho integration plan JSON file.")
    parser.add_argument("plan", nargs="?", help="Path to plan JSON, or '-' for stdin")
    parser.add_argument("--example", action="store_true", help="Print an example plan JSON and exit")
    args = parser.parse_args(argv)

    if args.example:
        print(json.dumps(EXAMPLE_PLAN, indent=2, sort_keys=True))
        return 0
    if not args.plan:
        parser.error("provide a plan path, '-' for stdin, or --example")

    data = load_plan(args.plan)
    findings = Validator(data).validate()
    errors = [f for f in findings if f.level == "ERROR"]
    warnings = [f for f in findings if f.level == "WARN"]

    if not findings:
        print("OK: no integration-plan issues found")
        return 0

    for finding in findings:
        print(f"{finding.level}: {finding.path}: {finding.message}")
    print(f"Summary: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
