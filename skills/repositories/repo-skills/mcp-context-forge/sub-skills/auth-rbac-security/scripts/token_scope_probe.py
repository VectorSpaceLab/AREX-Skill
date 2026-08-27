#!/usr/bin/env python3
"""Classify ContextForge token-team visibility semantics without verifying secrets.

This helper decodes a JWT payload (without signature verification) or reads a
JSON payload and explains the expected ContextForge visibility scope for API /
legacy tokens or session tokens. It never needs JWT_SECRET_KEY and must not be
used as an authentication verifier.

Examples:
  python token_scope_probe.py --payload '{"is_admin": true, "teams": null}' --token-use api
  python token_scope_probe.py --token "$MCPGATEWAY_BEARER_TOKEN" --token-use session --db-teams team-a,team-b
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from typing import Any


def _b64url_json(segment: str) -> dict[str, Any]:
    padded = segment + "=" * (-len(segment) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # pragma: no cover - defensive CLI branch
        raise SystemExit(f"Could not decode JWT payload segment: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("JWT payload is not a JSON object")
    return data


def load_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.payload:
        try:
            data = json.loads(args.payload)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON payload: {exc}") from exc
        if not isinstance(data, dict):
            raise SystemExit("--payload must be a JSON object")
        return data
    if args.payload_file:
        with open(args.payload_file, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise SystemExit("--payload-file must contain a JSON object")
        return data
    if args.token:
        parts = args.token.split(".")
        if len(parts) != 3:
            raise SystemExit("--token does not look like a compact JWT with three segments")
        return _b64url_json(parts[1])
    raise SystemExit("Provide --token, --payload, or --payload-file")


def parse_db_teams(value: str | None) -> list[str] | None:
    if value is None:
        return None
    value = value.strip()
    if value.lower() in {"admin", "none", "null"}:
        return None
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def normalize_api(payload: dict[str, Any]) -> tuple[str, str]:
    teams_present = "teams" in payload
    teams = payload.get("teams")
    is_admin = bool(payload.get("is_admin"))
    if not teams_present:
        return "[]", "API/legacy token has no teams claim: public-only scope."
    if teams is None:
        if is_admin:
            return "None", "API/legacy token has teams:null and is_admin:true: admin-bypass visibility."
        return "[]", "API/legacy token has teams:null without admin identity: public-only scope."
    if isinstance(teams, list):
        if not teams:
            return "[]", "API/legacy token has teams:[]: public-only scope."
        return json.dumps(teams), "API/legacy token has explicit teams: team plus public visibility."
    return "[]", "Invalid teams type for API/legacy token; ContextForge should fail closed or reject during validation."


def normalize_session(payload: dict[str, Any], db_teams: list[str] | None) -> tuple[str, str]:
    if db_teams is None:
        return "None", "Session token for a DB admin user: admin-bypass visibility; JWT teams do not narrow admin sessions."
    teams_claim = payload.get("teams") if "teams" in payload else None
    if teams_claim in (None, []):
        return json.dumps(db_teams), "Session token with missing/null/empty teams claim: full DB team membership for non-admin user."
    if not isinstance(teams_claim, list):
        return "[]", "Invalid session teams claim type; treat as fail-closed/public-only until validated by the auth layer."
    intersection = [team for team in teams_claim if team in set(db_teams)]
    if not intersection:
        return "[]", "Session JWT teams do not overlap DB teams: public-only fail-closed scope."
    return json.dumps(intersection), "Session JWT teams narrow DB membership to the intersection."


def main() -> int:
    parser = argparse.ArgumentParser(description="Explain ContextForge token-team visibility semantics without verifying a token signature.")
    parser.add_argument("--token", help="Compact JWT to decode without verification. Do not paste secrets into logs.")
    parser.add_argument("--payload", help="JSON object containing token claims.")
    parser.add_argument("--payload-file", help="Path to a JSON object containing token claims.")
    parser.add_argument("--token-use", choices=["api", "legacy", "session"], default="api", help="Token interpretation mode to apply.")
    parser.add_argument("--db-teams", help="For session tokens: comma-separated DB team ids, empty for public-only user, or 'admin' for DB admin.")
    args = parser.parse_args()

    payload = load_payload(args)
    if args.token_use == "session":
        db_teams = parse_db_teams(args.db_teams)
        if args.db_teams is None:
            print("warning: --db-teams not supplied for session token; assuming non-admin user with no DB teams", file=sys.stderr)
            db_teams = []
        scope, reason = normalize_session(payload, db_teams)
    else:
        scope, reason = normalize_api(payload)

    print(json.dumps({"token_use": args.token_use, "expected_token_teams": scope, "reason": reason}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
