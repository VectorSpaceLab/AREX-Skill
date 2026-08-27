#!/usr/bin/env python3
"""Plan safe Galaxy Tool Shed API operations.

The default mode prints dry-run plans and does not contact any server. Network
access requires both --execute and the operation-specific URL/key arguments.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def normalize_base_url(url: str) -> str:
    if not url:
        raise ValueError("URL cannot be empty")
    return url.rstrip("/")


def is_local_url(url: str) -> bool:
    host = urllib.parse.urlparse(url).hostname
    return bool(host and (host in LOCAL_HOSTS or host.endswith(".localhost")))


def redact(value: str | None) -> str:
    if not value:
        return "<not supplied>"
    if len(value) <= 8:
        return "<redacted>"
    return f"{value[:3]}...{value[-3:]}"


def api_key_from_args(args: argparse.Namespace) -> str | None:
    if getattr(args, "api_key", None):
        return args.api_key
    env_name = getattr(args, "api_key_env", None)
    if env_name:
        return os.environ.get(env_name)
    return None


def print_section(title: str, lines: list[str]) -> None:
    print(title)
    print("=" * len(title))
    for line in lines:
        print(line)
    print()


def json_request(method: str, url: str, api_key: str | None = None, payload: dict[str, Any] | None = None) -> Any:
    data = None
    headers = {"Accept": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            if not body.strip():
                return None
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} for {method} {url}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Unable to contact {url}: {exc.reason}") from exc


def require_key(args: argparse.Namespace, purpose: str) -> str:
    key = api_key_from_args(args)
    if not key:
        raise SystemExit(f"Refusing to execute {purpose}: supply --api-key or --api-key-env.")
    return key


def require_nonlocal_confirmation(url: str, args: argparse.Namespace, purpose: str) -> None:
    if not is_local_url(url) and not getattr(args, "confirm_nonlocal_write", False):
        raise SystemExit(
            f"Refusing non-local {purpose} against {url}. Re-run with --confirm-nonlocal-write only after confirming the target is safe."
        )


def command_note(args: argparse.Namespace) -> str:
    key = api_key_from_args(args)
    env_name = getattr(args, "api_key_env", None)
    if env_name:
        return f"API key source: environment variable {env_name} ({redact(key)})."
    return f"API key source: command line ({redact(key)}). Prefer --api-key-env for real secrets."


def plan_categories(args: argparse.Namespace) -> None:
    source = normalize_base_url(args.from_tool_shed)
    target = normalize_base_url(args.to_tool_shed)
    print_section(
        "Dry-run category copy plan",
        [
            f"Source Tool Shed: {source}",
            f"Target Tool Shed: {target}",
            "Read source categories with GET /api/categories.",
            "For each category with name/description, create on target with POST /api/categories.",
            "Target creation requires a Tool Shed admin API key.",
            "Existing categories should be compared before writes; duplicate handling is deployment-specific.",
            command_note(args),
        ],
    )
    if not args.execute:
        print("No network calls made. Add --execute with an API key to perform this operation.")
        return
    require_nonlocal_confirmation(target, args, "category creation")
    api_key = require_key(args, "category creation")
    categories = json_request("GET", f"{source}/api/categories")
    if not isinstance(categories, list):
        raise SystemExit("Expected source /api/categories to return a list.")
    created = 0
    skipped = 0
    for category in categories:
        if not isinstance(category, dict):
            skipped += 1
            continue
        name = category.get("name")
        description = category.get("description")
        if not name or description is None:
            skipped += 1
            continue
        response = json_request("POST", f"{target}/api/categories", api_key, {"name": name, "description": description})
        print(json.dumps({"created_or_returned": response}, indent=2, sort_keys=True))
        created += 1
    print(json.dumps({"created_attempts": created, "skipped": skipped}, indent=2, sort_keys=True))


def plan_users(args: argparse.Namespace) -> None:
    source = normalize_base_url(args.from_tool_shed)
    target = normalize_base_url(args.to_tool_shed)
    print_section(
        "Dry-run user copy plan",
        [
            f"Source Tool Shed: {source}",
            f"Target Tool Shed: {target}",
            "Read source users with GET /api/users.",
            "For each username, legacy scripts synthesize username@test.org and password testuser.",
            "This is appropriate only for disposable development/test sheds, never production identity mirroring.",
            "Target creation requires a Tool Shed admin API key and explicit --allow-user-creation.",
            command_note(args),
        ],
    )
    if not args.execute:
        print("No network calls made. Add --execute, --allow-user-creation, and an API key for a disposable test shed.")
        return
    if not args.allow_user_creation:
        raise SystemExit("Refusing user creation without --allow-user-creation.")
    require_nonlocal_confirmation(target, args, "user creation")
    api_key = require_key(args, "user creation")
    users = json_request("GET", f"{source}/api/users")
    if not isinstance(users, list):
        raise SystemExit("Expected source /api/users to return a list.")
    created = 0
    skipped = 0
    for user in users:
        if not isinstance(user, dict):
            skipped += 1
            continue
        username = user.get("username")
        if not username:
            skipped += 1
            continue
        payload = {"username": username, "email": f"{username}@test.org", "password": "testuser"}
        response = json_request("POST", f"{target}/api/users", api_key, payload)
        print(json.dumps({"created_or_returned": response}, indent=2, sort_keys=True))
        created += 1
    print(json.dumps({"created_attempts": created, "skipped": skipped}, indent=2, sort_keys=True))


def plan_reset_repository_metadata(args: argparse.Namespace) -> None:
    shed = normalize_base_url(args.tool_shed)
    if args.dry_run and args.persist:
        raise SystemExit("Choose either --dry-run or --persist, not both.")
    dry_run = args.dry_run or not args.persist
    payload = {"repository_id": args.repository_id, "dry_run": dry_run, "verbose": args.verbose}
    print_section(
        "Dry-run Tool Shed repository metadata reset plan",
        [
            f"Tool Shed: {shed}",
            f"Repository id: {args.repository_id}",
            f"Request: POST /api/repositories/reset_metadata_on_repository with {json.dumps(payload, sort_keys=True)}",
            "Use dry-run plus verbose first to compare before/after metadata without persisting changes.",
            "Persisting reset can repair stale generated metadata, including stored tool_config paths, after confirmation.",
            command_note(args),
        ],
    )
    if not args.execute:
        print("No network calls made. Add --execute with an API key to contact the Tool Shed.")
        return
    if args.persist:
        require_nonlocal_confirmation(shed, args, "persisting repository metadata reset")
    api_key = require_key(args, "repository metadata reset")
    response = json_request("POST", f"{shed}/api/repositories/reset_metadata_on_repository", api_key, payload)
    print(json.dumps(response, indent=2, sort_keys=True))


def plan_reset_installed_metadata(args: argparse.Namespace) -> None:
    galaxy = normalize_base_url(args.galaxy_url)
    print_section(
        "Dry-run Galaxy installed repository metadata reset plan",
        [
            f"Galaxy URL: {galaxy}",
            "Request: POST /api/tool_shed_repositories/reset_metadata_on_installed_repositories with an empty JSON body.",
            "This targets repositories installed into a Galaxy instance, not Tool Shed repository records.",
            "Requires a Galaxy admin API key and explicit --confirm-bulk-installed-reset to execute.",
            command_note(args),
        ],
    )
    if not args.execute:
        print("No network calls made. Add --execute, an admin API key, and --confirm-bulk-installed-reset to perform this bulk operation.")
        return
    if not args.confirm_bulk_installed_reset:
        raise SystemExit("Refusing bulk installed-repository reset without --confirm-bulk-installed-reset.")
    require_nonlocal_confirmation(galaxy, args, "bulk installed-repository metadata reset")
    api_key = require_key(args, "installed-repository metadata reset")
    response = json_request(
        "POST",
        f"{galaxy}/api/tool_shed_repositories/reset_metadata_on_installed_repositories",
        api_key,
        {},
    )
    print(json.dumps(response, indent=2, sort_keys=True))


def plan_build_whoosh_index(args: argparse.Namespace) -> None:
    lines = [
        f"Tool Shed config: {args.config}",
        "Confirm Tool Shed search is enabled and whoosh_index_dir is configured.",
        "Confirm the Tool Shed runtime environment is active and has database, Mercurial, and Whoosh access.",
        "Confirm file_path, hgweb_config_dir, and hgweb_repo_prefix point at the running Tool Shed's repository storage.",
        "Coordinate with service owners before replacing or rebuilding a production index directory.",
        "Use the Tool Shed deployment's own documented index rebuild entry point; this bundled planner only records the preflight checklist.",
    ]
    if args.debug:
        lines.append("Add --debug to the service script when detailed configuration logging is safe.")
    print_section("Whoosh index rebuild checklist", lines)
    if args.execute:
        raise SystemExit("This planner does not execute Whoosh rebuilds because they require the Tool Shed service runtime and deployment context.")
    print("No network or file-system mutations made.")


def plan_install_check(args: argparse.Namespace) -> None:
    galaxy = normalize_base_url(args.galaxy_url)
    shed = normalize_base_url(args.tool_shed) if args.tool_shed else "<Tool Shed URL to confirm>"
    checks = [
        f"Galaxy URL: {galaxy}",
        f"Tool Shed: {shed}",
        f"Repository: owner={args.owner}, name={args.name}, changeset={args.changeset}",
        "Check Tool Shed install info for owner/name/changeset before installing or updating.",
        "Check Galaxy installed repositories for an existing matching owner/name/revision.",
        "If installed, inspect the installed repository id and tool_shed_status before update/reinstall.",
        "If a tool id is supplied, verify /api/tools/{tool_id} on Galaxy after install.",
        "Do not hand-edit shed_tool_conf.xml as the first repair; prefer Galaxy install/update/uninstall APIs.",
    ]
    if args.tool_id:
        checks.append(f"Tool id to verify after install: {args.tool_id}")
    print_section("Installed repository check plan", checks)
    if args.execute:
        raise SystemExit("This planner does not execute Galaxy repository installs or updates. Use it to prepare a safe API/deployment plan.")
    print("No network calls made.")


def add_key_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--api-key", help="API key for the target Tool Shed or Galaxy service. Prefer --api-key-env.")
    parser.add_argument("--api-key-env", help="Environment variable containing the API key.")
    parser.add_argument("--execute", action="store_true", help="Allow this command to contact the supplied service.")
    parser.add_argument(
        "--confirm-nonlocal-write",
        action="store_true",
        help="Permit mutating requests to non-local URLs after external safety confirmation.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan safe Galaxy Tool Shed API operations.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    categories = subparsers.add_parser("categories", help="Plan or copy categories between Tool Sheds.")
    categories.add_argument("--from-tool-shed", required=True, help="Source Tool Shed base URL.")
    categories.add_argument("--to-tool-shed", required=True, help="Target Tool Shed base URL.")
    add_key_args(categories)
    categories.set_defaults(func=plan_categories)

    users = subparsers.add_parser("users", help="Plan or copy users into a disposable test Tool Shed.")
    users.add_argument("--from-tool-shed", required=True, help="Source Tool Shed base URL.")
    users.add_argument("--to-tool-shed", required=True, help="Target Tool Shed base URL.")
    users.add_argument("--allow-user-creation", action="store_true", help="Confirm synthetic test-user creation is intended.")
    add_key_args(users)
    users.set_defaults(func=plan_users)

    reset_repo = subparsers.add_parser("reset-repository-metadata", help="Plan or run Tool Shed repository metadata reset.")
    reset_repo.add_argument("--tool-shed", required=True, help="Tool Shed base URL.")
    reset_repo.add_argument("--repository-id", required=True, help="Encoded Tool Shed repository id.")
    reset_repo.add_argument("--verbose", action="store_true", help="Request changeset details and before/after snapshots when supported.")
    reset_repo.add_argument("--dry-run", action="store_true", help="Explicitly request dry-run preview; this is the default unless --persist is supplied.")
    reset_repo.add_argument("--persist", action="store_true", help="Persist the metadata reset instead of dry-run preview.")
    add_key_args(reset_repo)
    reset_repo.set_defaults(func=plan_reset_repository_metadata)

    reset_installed = subparsers.add_parser(
        "reset-installed-metadata", help="Plan or run Galaxy installed Tool Shed repository metadata reset."
    )
    reset_installed.add_argument("--galaxy-url", required=True, help="Galaxy server base URL.")
    reset_installed.add_argument(
        "--confirm-bulk-installed-reset",
        action="store_true",
        help="Confirm bulk installed-repository metadata reset is intended.",
    )
    add_key_args(reset_installed)
    reset_installed.set_defaults(func=plan_reset_installed_metadata)

    whoosh = subparsers.add_parser("build-whoosh-index", help="Print Tool Shed Whoosh index rebuild checklist.")
    whoosh.add_argument("--config", required=True, help="Tool Shed config path to use in the service runtime.")
    whoosh.add_argument("--debug", action="store_true", help="Include debug flag guidance.")
    whoosh.add_argument("--execute", action="store_true", help="Refuse with an explanation; service runtime required.")
    whoosh.set_defaults(func=plan_build_whoosh_index)

    install_check = subparsers.add_parser("install-check", help="Plan checks for a Galaxy installed Tool Shed repository.")
    install_check.add_argument("--galaxy-url", required=True, help="Galaxy server base URL.")
    install_check.add_argument("--tool-shed", help="Tool Shed base URL, if known.")
    install_check.add_argument("--owner", required=True, help="Repository owner.")
    install_check.add_argument("--name", required=True, help="Repository name.")
    install_check.add_argument("--changeset", required=True, help="Repository changeset revision.")
    install_check.add_argument("--tool-id", help="Expected Galaxy tool id/guid to check after install.")
    install_check.add_argument("--execute", action="store_true", help="Refuse with an explanation; installs are not executed.")
    install_check.set_defaults(func=plan_install_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
