---
name: cli-sdk-workflows
description: "Operate on Transformer Lab Typer CLI, Textual job monitor, CLI
  config/auth/profiles, asset transfer helpers, Python SDK
  facade/resources/storage, and tfl-remote-trap workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# CLI and SDK Workflows

Use this sub-skill when a task touches Transformer Lab's Python CLI package, the interactive job monitor TUI, CLI authentication/profile/config state, asset upload/download helpers, the Python SDK facade/resource/storage layers, or the remote task wrapper used by launched jobs.

## Route first

- CLI command parsing, output formats, profile/auth/config, task/job command flows, asset helpers, and Textual monitor behavior: read [CLI reference](references/cli-reference.md).
- SDK task-script APIs, resource classes, storage/organization context, artifact/model/dataset/checkpoint helpers, and `tfl-remote-trap`: read [SDK reference](references/sdk-reference.md).
- Common failures and debugging playbooks: read [Troubleshooting](references/troubleshooting.md).
- Backend API route implementation and service internals belong to `../backend-api-services/SKILL.md`.
- Job lifecycle, queue/provider semantics, remote launch contracts, and compute-provider behavior belong to `../task-execution-compute/SKILL.md`.
- React browser UI behavior belongs to `../frontend-web-app/SKILL.md`.

## Operating rules

1. Keep CLI changes Typer-first unless the workflow truly needs a human interactive TUI. The Textual job monitor is not an automation interface for agents.
2. Preserve root global option ordering: root flags such as `--format`, `--profile`, and root `--no-interactive` must appear immediately after `lab` and before a command group.
3. Preserve both pretty and machine-readable output for non-interactive CLI commands. JSON mode must not mix Rich spinners, tables, prompts, or update-check text into stdout.
4. Keep the CLI independent from the SDK. The CLI talks to the API through its HTTP utility layer; task code running inside jobs imports the SDK.
5. For SDK task examples and generated task templates, call `lab.init()` before logging, progress, or save helpers, and pass final scores as dictionaries, not scalars.
6. Do not solve provider orchestration or backend API behavior in this sub-skill. Route across sibling skills once a question moves below the CLI/SDK facade boundary.

## Fast validation anchors

- CLI package version: `transformerlab-cli` `0.0.68`.
- SDK package version: `transformerlab` `0.1.46`.
- Verified SDK signatures: `Lab.init(self, experiment_id: str | None = None, config: Optional[Dict[str, Any]] = None)` and `Lab.finish(self, message: str = "Job completed successfully", score: Optional[Dict[str, Any]] = None, additional_output_path: Optional[str] = None, plot_data_path: Optional[str] = None)`.
- CLI tests use `typer.testing.CliRunner` with mocked API calls; SDK tests use pytest around isolated workspace/storage state.
