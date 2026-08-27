#!/usr/bin/env python3
"""Safe planning skeleton for Argilla v1/Rubrix -> Argilla 2.x migration.

This template is intentionally side-effect free: it does not import Argilla,
open network connections, read credentials from the environment, or mutate any
server. It only parses arguments and renders a checklist/template with TODO
hooks. To turn it into a real migration utility, copy/edit the TODO hooks after
reviewing the bundled migration references and after obtaining explicit approval
for any server writes.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from textwrap import dedent
from typing import Any


TODO_HOOKS: dict[str, str] = {
    "connect_legacy": "TODO: import argilla.v1 as rg_v1 and call rg_v1.init(api_url=..., api_key=...).",
    "fetch_legacy_users": "TODO: call rg_v1.User.list() with owner/admin legacy credentials.",
    "fetch_legacy_workspaces": "TODO: call rg_v1.Workspace.list() and preserve name/ID mapping.",
    "load_legacy_settings": "TODO: call rg_v1.load_dataset_settings(dataset_name, workspace=...).",
    "load_legacy_records": "TODO: call rg_v1.load(...).to_datasets() and export before target writes.",
    "connect_target": "TODO: import argilla as rg and build rg.Argilla(api_url=..., api_key=...).",
    "recreate_target_identities": "TODO: create rg.Workspace and rg.User resources, choosing new passwords.",
    "build_v2_settings": "TODO: create rg.Settings with fields, questions, metadata, and vectors.",
    "map_records": "TODO: convert each legacy row to rg.Record with suggestions/responses.",
    "log_records": "TODO: call dataset.records.log(records, batch_size=...) only after dry-run validation.",
}


@dataclass(slots=True)
class MigrationPlan:
    mode: str
    source_url: str | None
    target_url: str | None
    dataset_name: str | None
    workspace: str | None
    export_first: bool
    preserve_ids: bool
    preserve_passwords: bool
    safety_notes: list[str]
    todo_hooks: dict[str, str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="legacy_migration_skeleton.py",
        description="Render a safe Argilla v1/Rubrix to Argilla 2.x migration plan/template without contacting servers.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--source-url", help="Legacy Argilla v1/Rubrix API URL; only echoed in the plan.")
    parser.add_argument("--source-api-key", help="Legacy API key; accepted only to remind you one is needed, never printed.")
    parser.add_argument("--target-url", help="Current Argilla 2.x API URL; only echoed in the plan.")
    parser.add_argument("--target-api-key", help="Current API key; accepted only to remind you one is needed, never printed.")
    parser.add_argument("--dataset-name", help="Legacy dataset name to migrate, if doing dataset migration.")
    parser.add_argument("--workspace", help="Workspace name used by the legacy dataset and/or target dataset.")
    parser.add_argument(
        "--mode",
        choices=("users", "datasets", "both"),
        default="both",
        help="Which migration path the rendered plan should emphasize.",
    )
    parser.add_argument(
        "--preserve-ids",
        action="store_true",
        help="Record that the plan requires stable user/workspace/dataset IDs.",
    )
    parser.add_argument(
        "--preserve-passwords",
        action="store_true",
        help="Record that the user asked for password preservation; the plan will warn that passwords cannot be recovered.",
    )
    parser.add_argument(
        "--no-export-first",
        action="store_true",
        help="Remove the export-first reminder from the rendered plan. Use only if an export already exists.",
    )
    parser.add_argument("--json", action="store_true", help="Render the plan as JSON instead of text.")
    parser.add_argument("--template", action="store_true", help="Render a commented code skeleton instead of the checklist.")
    parser.add_argument("--out", type=Path, help="Optional file path for the rendered plan/template.")
    return parser


def build_plan(args: argparse.Namespace) -> MigrationPlan:
    safety_notes = [
        "Back up source and target servers before writes.",
        "Keep legacy and current API URLs/API keys separate.",
        "Do not print or store API keys in logs or generated migration reports.",
        "Passwords cannot be recovered from the legacy server; choose new passwords for fresh v2 recreation.",
        "Keep argilla-v1 and old optional integrations out of the current Argilla 2.x server environment.",
        "Use server-ops, not this template, for deployment, proxy, database, search, Redis, or reindex operations.",
    ]
    if not args.no_export_first:
        safety_notes.insert(0, "Export or snapshot legacy data before creating target resources.")
    if args.preserve_ids:
        safety_notes.append("ID preservation requested: test on a tiny subset or prefer a same-server/temporary-copy upgrade path.")
    if args.preserve_passwords:
        safety_notes.append("Password preservation requested: passwords are not recoverable; prefer a same-server upgrade path.")

    return MigrationPlan(
        mode=args.mode,
        source_url=args.source_url,
        target_url=args.target_url,
        dataset_name=args.dataset_name,
        workspace=args.workspace,
        export_first=not args.no_export_first,
        preserve_ids=args.preserve_ids,
        preserve_passwords=args.preserve_passwords,
        safety_notes=safety_notes,
        todo_hooks=TODO_HOOKS,
    )


def _masked(value: str | None, label: str) -> str:
    return "provided but not printed" if value else f"<{label}>"


def render_plan(plan: MigrationPlan, source_api_key: str | None, target_api_key: str | None) -> str:
    steps: list[str] = []
    if plan.mode in {"users", "both"}:
        steps.extend(
            [
                "Extract legacy users/workspaces with rg_v1.User.list() and rg_v1.Workspace.list().",
                "Create target rg.Workspace resources before rg.User resources.",
                "Create new passwords and keep a secure external handoff.",
                "Rebuild workspace memberships using exact workspace names or an explicit ID/name map.",
            ]
        )
    if plan.mode in {"datasets", "both"}:
        steps.extend(
            [
                "Load settings with rg_v1.load_dataset_settings(name, workspace).",
                "Load/export records with rg_v1.load(name, workspace).to_datasets().",
                "Build current rg.Settings with TextField/ImageField/etc., the correct question type, metadata, and vectors.",
                "Map legacy predictions to rg.Suggestion and annotations to rg.Response with matching question_name values.",
                "Create rg.Dataset and call dataset.records.log(records) only after validating a dry-run subset.",
            ]
        )

    text = [
        "Argilla legacy migration skeleton plan",
        "======================================",
        "",
        f"Mode: {plan.mode}",
        f"Legacy source URL: {plan.source_url or '<legacy server URL>'}",
        f"Legacy API key: {_masked(source_api_key, 'legacy API key')}",
        f"Current target URL: {plan.target_url or '<current Argilla 2.x server URL>'}",
        f"Current API key: {_masked(target_api_key, 'current API key')}",
        f"Dataset: {plan.dataset_name or '<dataset name>'}",
        f"Workspace: {plan.workspace or '<workspace name>'}",
        "",
        "Safety notes:",
    ]
    text.extend(f"- {note}" for note in plan.safety_notes)
    text.extend(["", "Planned steps:"])
    text.extend(f"{idx}. {step}" for idx, step in enumerate(steps, start=1))
    text.extend(["", "TODO hooks to implement before any real migration run:"])
    text.extend(f"- {name}: {description}" for name, description in plan.todo_hooks.items())
    text.extend(
        [
            "",
            "This script has not contacted any server and has not mutated data.",
            "If the source is a FeedbackDataset, do not run the legacy schema mapping; use server-ops for search reindex questions.",
        ]
    )
    return "\n".join(text)


def render_code_template() -> str:
    return dedent(
        """
        # TODO-based migration code skeleton. This is printed as text; it is not executed.
        # Fill in these hooks only after backups/export and explicit approval for target writes.

        # import argilla.v1 as rg_v1
        # import argilla as rg

        # 1. Legacy extraction
        # rg_v1.init(api_url=LEGACY_API_URL, api_key=LEGACY_API_KEY)
        # users_v1 = list(rg_v1.User.list())
        # workspaces_v1 = list(rg_v1.Workspace.list())
        # settings_v1 = rg_v1.load_dataset_settings(DATASET_NAME, workspace=WORKSPACE_NAME)
        # records_v1 = rg_v1.load(DATASET_NAME, workspace=WORKSPACE_NAME)
        # hf_dataset = records_v1.to_datasets()

        # 2. Current target connection
        # client = rg.Argilla(api_url=CURRENT_API_URL, api_key=CURRENT_API_KEY, timeout=60, retries=5)

        # 3. Target identities
        # for workspace in workspaces_v1:
        #     rg.Workspace(id=workspace.id, name=workspace.name, client=client).create()
        # for user in users_v1:
        #     user_v2 = rg.User(
        #         id=user.id, username=user.username, first_name=user.first_name,
        #         last_name=user.last_name, role=user.role, password=NEW_PASSWORD,
        #         client=client,
        #     ).create()
        #     # TODO: add workspace memberships.

        # 4. Target settings
        # settings = rg.Settings(
        #     fields=[rg.TextField(name="text")],
        #     questions=[rg.LabelQuestion(name="label", labels=settings_v1.label_schema)],
        #     metadata=[],
        #     vectors=[],
        # )

        # 5. Record mapping
        # users_by_name = {user.username: user for user in client.users}
        # current_user = client.me
        # records = []
        # for data in hf_dataset:
        #     # TODO: choose single-label, multi-label, span, or text-generation mapping.
        #     # TODO: build rg.Suggestion and rg.Response objects with matching question_name.
        #     records.append(rg.Record(
        #         id=data["id"],
        #         fields=data.get("inputs", {"text": data.get("text")}),
        #         metadata=data.get("metadata") or {},
        #         vectors=data.get("vectors") or {},
        #         suggestions=[],
        #         responses=[],
        #     ))

        # 6. Target dataset write, only after dry-run validation and approval
        # dataset = rg.Dataset(name=DATASET_NAME, workspace=WORKSPACE_NAME, settings=settings, client=client)
        # dataset.create()
        # dataset.records.log(records, batch_size=256)
        """
    ).strip()


# Placeholder hooks for agents/users who prefer editing this file into a real utility.
# They are intentionally not called by main().
def connect_legacy(*_args: Any, **_kwargs: Any) -> Any:
    raise NotImplementedError(TODO_HOOKS["connect_legacy"])


def fetch_legacy_users(*_args: Any, **_kwargs: Any) -> Any:
    raise NotImplementedError(TODO_HOOKS["fetch_legacy_users"])


def fetch_legacy_workspaces(*_args: Any, **_kwargs: Any) -> Any:
    raise NotImplementedError(TODO_HOOKS["fetch_legacy_workspaces"])


def load_legacy_settings(*_args: Any, **_kwargs: Any) -> Any:
    raise NotImplementedError(TODO_HOOKS["load_legacy_settings"])


def load_legacy_records(*_args: Any, **_kwargs: Any) -> Any:
    raise NotImplementedError(TODO_HOOKS["load_legacy_records"])


def connect_target(*_args: Any, **_kwargs: Any) -> Any:
    raise NotImplementedError(TODO_HOOKS["connect_target"])


def recreate_target_identities(*_args: Any, **_kwargs: Any) -> Any:
    raise NotImplementedError(TODO_HOOKS["recreate_target_identities"])


def build_v2_settings(*_args: Any, **_kwargs: Any) -> Any:
    raise NotImplementedError(TODO_HOOKS["build_v2_settings"])


def map_records(*_args: Any, **_kwargs: Any) -> Any:
    raise NotImplementedError(TODO_HOOKS["map_records"])


def log_records(*_args: Any, **_kwargs: Any) -> Any:
    raise NotImplementedError(TODO_HOOKS["log_records"])


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    plan = build_plan(args)

    if args.template:
        output = render_code_template()
    elif args.json:
        output = json.dumps(asdict(plan), indent=2, sort_keys=True)
    else:
        output = render_plan(plan, source_api_key=args.source_api_key, target_api_key=args.target_api_key)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
        print(f"Wrote migration skeleton output to {args.out}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
