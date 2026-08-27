#!/usr/bin/env python3
"""Print self-contained mcp-agent Temporal skeleton files.

This script only prints templates. It does not connect to Temporal, start a
worker, call providers, or write files unless the shell redirects output.
"""

from __future__ import annotations

import argparse
import re
import sys
import textwrap


def slug_to_identifier(value: str) -> str:
    identifier = re.sub(r"\W+", "_", value.strip().lower()).strip("_")
    if not identifier:
        identifier = "durable_app"
    if identifier[0].isdigit():
        identifier = f"app_{identifier}"
    return identifier


def class_name(value: str) -> str:
    pieces = re.split(r"[^A-Za-z0-9]+", value.strip())
    result = "".join(piece[:1].upper() + piece[1:] for piece in pieces if piece)
    if not result:
        result = "DurableApproval"
    if result[0].isdigit():
        result = f"Workflow{result}"
    if not result.endswith("Workflow"):
        result = f"{result}Workflow"
    return result


def render_config(app_name: str, task_queue: str, namespace: str, host: str) -> str:
    return f"""\
# mcp-agent Temporal configuration
execution_engine: temporal

# Optional: preload modules that define static @workflow_task activities.
# workflow_task_modules:
#   - {slug_to_identifier(app_name)}_tasks

# Optional: tune Temporal retry behavior per activity.
workflow_task_retry_policies:
  provider.request_completion:
    maximum_attempts: 2
    non_retryable_error_types:
      - AuthenticationError
      - PermissionDeniedError
      - BadRequestError
      - NotFoundError
      - UnprocessableEntityError

temporal:
  host: "{host}"
  namespace: "{namespace}"
  task_queue: "{task_queue}"
  max_concurrent_activities: 10

logger:
  transports: [console]
  level: info

# Add provider defaults and MCP servers for your app here.
# Keep secrets in mcp_agent.secrets.yaml or environment placeholders.
"""


def render_app(app_name: str, workflow_name: str) -> str:
    identifier = slug_to_identifier(app_name)
    workflow_class = class_name(workflow_name)
    return f'''\
from __future__ import annotations

from mcp_agent.app import MCPApp
from mcp_agent.executor.errors import WorkflowApplicationError
from mcp_agent.executor.workflow import Workflow, WorkflowResult

app = MCPApp(name="{identifier}")


@app.workflow
class {workflow_class}(Workflow[dict]):
    """A local-or-Temporal workflow with durable pause/resume semantics."""

    @app.workflow_run
    async def run(self, request: dict) -> WorkflowResult[dict]:
        draft = await self.prepare_draft(request)

        try:
            approval = await app.context.executor.wait_for_signal(
                signal_name="resume",
                workflow_id=self.id,
                run_id=self.run_id,
                signal_description="Waiting for human approval.",
                timeout_seconds=3600,
                signal_type=dict,
            )
        except TimeoutError as exc:
            raise WorkflowApplicationError(
                "Timed out waiting for resume signal.",
                type="SignalTimeout",
                non_retryable=True,
            ) from exc

        if not approval or approval.get("decision") != "approved":
            return WorkflowResult(
                value={{"status": "rejected", "draft": draft, "approval": approval}}
            )

        final = await self.finalize_draft(draft, approval)
        return WorkflowResult(value={{"status": "approved", "result": final}})

    @app.workflow_task(
        name="{identifier}.prepare_draft",
        retry_policy={{"maximum_attempts": 2}},
    )
    async def prepare_draft(self, request: dict) -> str:
        topic = request.get("topic", "untitled")
        return f"Draft for {{topic}}"

    @app.workflow_task(
        name="{identifier}.finalize_draft",
        retry_policy={{"maximum_attempts": 1}},
    )
    async def finalize_draft(self, draft: str, approval: dict) -> str:
        reviewer = approval.get("reviewer", "unknown")
        notes = approval.get("notes", "")
        return f"{{draft}}\\nApproved by: {{reviewer}}\\nNotes: {{notes}}"
'''


def render_worker(app_module: str) -> str:
    return f'''\
from __future__ import annotations

import asyncio
import logging

from {app_module} import app
from mcp_agent.executor.temporal import create_temporal_worker_for_app

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    async with create_temporal_worker_for_app(app) as worker:
        await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
'''


def render_launcher(app_module: str, workflow_name: str, task_queue: str) -> str:
    workflow_class = class_name(workflow_name)
    return f'''\
from __future__ import annotations

import asyncio

from {app_module} import app


async def main() -> None:
    async with app.run() as running_app:
        handle = await running_app.executor.start_workflow(
            "{workflow_class}",
            {{"topic": "durable execution"}},
            workflow_id="{slug_to_identifier(workflow_name).replace('_', '-')}-demo",
            task_queue="{task_queue}",
        )
        print("workflow_id=", handle.id)
        print("run_id=", handle.result_run_id or handle.run_id)
        print(await handle.result())


if __name__ == "__main__":
    asyncio.run(main())
'''


def render_resume(app_module: str) -> str:
    return f'''\
from __future__ import annotations

import argparse
import asyncio
import json

from {app_module} import app


async def resume(workflow_id: str, run_id: str, payload: dict) -> None:
    async with app.run() as running_app:
        await running_app.executor.signal(
            signal_name="resume",
            payload=payload,
            workflow_id=workflow_id,
            run_id=run_id,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume a waiting workflow.")
    parser.add_argument("workflow_id")
    parser.add_argument("run_id")
    parser.add_argument(
        "--payload",
        default='{{"decision":"approved","reviewer":"operator","notes":"Proceed."}}',
        help="JSON payload sent with the resume signal.",
    )
    args = parser.parse_args()
    asyncio.run(resume(args.workflow_id, args.run_id, json.loads(args.payload)))


if __name__ == "__main__":
    main()
'''


TEMPLATE_RENDERERS = {
    "config": render_config,
    "app": render_app,
    "worker": render_worker,
    "launcher": render_launcher,
    "resume": render_resume,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print mcp-agent Temporal skeleton templates.")
    parser.add_argument(
        "template",
        choices=["config", "app", "worker", "launcher", "resume", "all"],
        help="Template to print.",
    )
    parser.add_argument("--app-name", default="durable_app", help="MCPApp name.")
    parser.add_argument("--app-module", default="main", help="Python module that exposes app.")
    parser.add_argument("--workflow-name", default="Approval", help="Workflow base name.")
    parser.add_argument("--task-queue", default="mcp-agent", help="Temporal task queue.")
    parser.add_argument("--namespace", default="default", help="Temporal namespace for config.")
    parser.add_argument("--host", default="localhost:7233", help="Temporal host for config.")
    return parser


def print_section(name: str, content: str) -> None:
    print(f"# --- {name} ---")
    print(content.rstrip())
    print()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    selected = ["config", "app", "worker", "launcher", "resume"] if args.template == "all" else [args.template]

    for template in selected:
        if template == "config":
            content = render_config(args.app_name, args.task_queue, args.namespace, args.host)
            print_section("mcp_agent.config.yaml", content) if args.template == "all" else print(content.rstrip())
        elif template == "app":
            content = render_app(args.app_name, args.workflow_name)
            print_section(f"{args.app_module}.py", content) if args.template == "all" else print(content.rstrip())
        elif template == "worker":
            content = render_worker(args.app_module)
            print_section("worker.py", content) if args.template == "all" else print(content.rstrip())
        elif template == "launcher":
            content = render_launcher(args.app_module, args.workflow_name, args.task_queue)
            print_section("launch_workflow.py", content) if args.template == "all" else print(content.rstrip())
        elif template == "resume":
            content = render_resume(args.app_module)
            print_section("resume_workflow.py", content) if args.template == "all" else print(content.rstrip())
        else:  # pragma: no cover - argparse prevents this
            raise AssertionError(template)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
