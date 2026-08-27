#!/usr/bin/env python3
"""Print a safe dry-run Honcho REST smoke sequence.

This helper does not call Honcho. It expands a small set of identifiers into
copyable curl commands that validate the workspace/peer/session/message/context
flow used by integrations.

Example:
  python rest_smoke_plan.py --workspace my-app --user user-123 --assistant assistant --session thread-123
"""

from __future__ import annotations

import argparse
import json
from textwrap import dedent


def q(value: str) -> str:
    """Return a shell-safe JSON string literal for small command snippets."""
    return json.dumps(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a dry-run Honcho REST smoke plan.")
    parser.add_argument("--base-url", default="https://api.honcho.dev", help="Honcho API base URL")
    parser.add_argument("--workspace", required=True, help="Workspace ID")
    parser.add_argument("--user", required=True, help="User peer ID")
    parser.add_argument("--assistant", required=True, help="Assistant peer ID")
    parser.add_argument("--session", required=True, help="Session ID")
    parser.add_argument("--query", default="What communication style does this user prefer?", help="Example chat query")
    parser.add_argument("--user-message", default="I prefer concise answers.", help="Example user message")
    parser.add_argument("--assistant-reply", default="I will be concise.", help="Example assistant reply")
    args = parser.parse_args(argv)

    workspace = args.workspace
    user = args.user
    assistant = args.assistant
    session = args.session
    base = args.base_url.rstrip("/")

    def peer_payload(peer_id: str) -> str:
        return f'{{"id":{q(peer_id)}}}'

    session_payload = (
        "{"
        f'"id":{q(session)},'
        f'"peers":{{'
        f'{q(user)}:{{"observe_me":true,"observe_others":true}},'
        f'{q(assistant)}:{{"observe_me":false,"observe_others":true}}'
        "}}"
    )
    message_payload = (
        "{"
        f'"messages":[{{"peer_id":{q(user)},"content":{q(args.user_message)}}},'
        f'{{"peer_id":{q(assistant)},"content":{q(args.assistant_reply)}}}]'
        "}"
    )
    chat_payload = (
        "{"
        f'"query":{q(args.query)},'
        f'"target":{q(user)},'
        f'"session_id":{q(session)},'
        '"reasoning_level":"low"'
        "}"
    )

    script = f"""#!/usr/bin/env bash
set -euo pipefail

: "${{HONCHO_API_KEY:?set HONCHO_API_KEY before running these commands}}"
export HONCHO_URL={q(base)}
export WORKSPACE={q(workspace)}
export USER={q(user)}
export ASSISTANT={q(assistant)}
export SESSION={q(session)}

curl -sS -X POST \"$HONCHO_URL/v3/workspaces/$WORKSPACE/peers\" \\
  -H \"Authorization: Bearer $HONCHO_API_KEY\" \\
  -H \"Content-Type: application/json\" \\
  -d {q(peer_payload(user))}

curl -sS -X POST \"$HONCHO_URL/v3/workspaces/$WORKSPACE/peers\" \\
  -H \"Authorization: Bearer $HONCHO_API_KEY\" \\
  -H \"Content-Type: application/json\" \\
  -d {q(peer_payload(assistant))}

curl -sS -X POST \"$HONCHO_URL/v3/workspaces/$WORKSPACE/sessions\" \\
  -H \"Authorization: Bearer $HONCHO_API_KEY\" \\
  -H \"Content-Type: application/json\" \\
  -d {q(session_payload)}

curl -sS -X POST \"$HONCHO_URL/v3/workspaces/$WORKSPACE/sessions/$SESSION/messages\" \\
  -H \"Authorization: Bearer $HONCHO_API_KEY\" \\
  -H \"Content-Type: application/json\" \\
  -d {q(message_payload)}

curl -sS \"$HONCHO_URL/v3/workspaces/$WORKSPACE/sessions/$SESSION/context?summary=true&tokens=4000&peer_target=$USER&peer_perspective=$ASSISTANT\" \\
  -H \"Authorization: Bearer $HONCHO_API_KEY\"

curl -sS -X POST \"$HONCHO_URL/v3/workspaces/$WORKSPACE/peers/$ASSISTANT/chat\" \\
  -H \"Authorization: Bearer $HONCHO_API_KEY\" \\
  -H \"Content-Type: application/json\" \\
  -d {q(chat_payload)}

curl -sS \"$HONCHO_URL/v3/workspaces/$WORKSPACE/sessions/$SESSION/summaries\" \\
  -H \"Authorization: Bearer $HONCHO_API_KEY\"

curl -sS \"$HONCHO_URL/v3/workspaces/$WORKSPACE/webhooks/test\" \\
  -H \"Authorization: Bearer $HONCHO_API_KEY\"
"""

    print(
        dedent(
            f"""# Honcho REST smoke plan
# This file is a dry run. It prints copyable commands for a typical integration.
#
# Workspace: {workspace}
# User peer: {user}
# Assistant peer: {assistant}
# Session: {session}
# Base URL: {base}

{script.rstrip()}
"""
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
