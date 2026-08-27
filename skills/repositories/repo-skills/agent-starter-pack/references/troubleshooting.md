# Troubleshooting

This page covers cross-cutting package problems. Workflow-specific failures belong in the nearest sub-skill troubleshooting reference.

## Install and import problems
### `agent-starter-pack` is missing or stale
- Confirm the package is installed in the intended environment.
- Re-run `python scripts/check_agent_starter_pack.py`.
- Use `agent-starter-pack --help` and `agent-starter-pack --version` to verify the CLI is discoverable.
- If the package was installed editable, make sure the environment still points at the expected checkout.

### `uvx` or `agent-starter-pack` is not on PATH
- Prefer `uvx agent-starter-pack ...` for zero-install usage.
- For persistent installs, confirm the CLI command is on PATH before blaming the package itself.
- Do not confuse a missing shell command with a broken import.

### `pip check` fails
- Treat a failing `pip check` as a real environment problem.
- Re-run the package sanity helper and fix the environment before drafting guidance.
- Do not assume a successful import is enough if dependency metadata is broken.

## Python compatibility problems
- The package requires Python 3.10 or newer.
- If you see syntax or import issues on older interpreters, the environment is wrong rather than the CLI.
- Use a dedicated inspection prefix instead of mutating a user’s active shell environment.

## CLI misuse
### `create` or `enhance` prompts appear unexpectedly
- `--auto-approve` skips prompts, but it does not skip missing prerequisites.
- `--skip-checks` only skips GCP/Vertex verification in creation flows.
- If the command still prompts, check whether the workflow is designed to ask for project, template, deployment, or datastore choices.

### Remote template syntax is wrong
- `local@...` is for a local path.
- `adk@...` and `adk-py@...` are special remote-template shortcuts.
- If a spec is not recognized, move to the project-scaffolding remote-template reference.

## Data/config validation problems
- A long project name, invalid agent directory, missing metadata, or missing `asp_version` is usually a user-input problem, not a package failure.
- When a workflow says a config file is missing, inspect the generated project metadata and follow the owning sub-skill’s troubleshooting page.

## When to escalate
- If the issue mentions GitHub CLI, gcloud, Terraform, Cloud Build, GitHub Actions, data ingestion, observability, or Gemini Enterprise IDs, jump to `deployment-ops` troubleshooting.
- If the issue mentions `enhance`, `extract`, `upgrade`, or a broken generated project, jump to `project-maintenance` troubleshooting.
- If the issue mentions template selection, remote templates, or first-run creation choices, jump to `project-scaffolding` troubleshooting.
