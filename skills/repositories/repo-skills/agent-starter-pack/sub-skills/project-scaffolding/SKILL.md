---
name: project-scaffolding
description: "Guides creation and discovery of new Agent Starter Pack projects
  from built-in, local, or remote templates."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Project scaffolding

Use this sub-skill when the user wants to start a new project from Agent Starter Pack or explore which template to use.

## Covers
- `create` for new projects from built-in, local, or remote templates.
- `list` for browsing built-in templates, the official ADK samples, or a local/remote template source.
- Template choice, agent selection, and generation-time options such as deployment target, datastore, session type, agent directory, `--prototype`, `--in-folder`, `--auto-approve`, `--skip-checks`, `--base-template`, `--bq-analytics`, and `--google-api-key`.
- Remote-template syntax, version locking, and base-template overrides.
- Generated-project shape: template-driven `README.md`, `Makefile`, agent directory, optional CI/CD scaffolding, and optional data-ingestion/session wiring.

## Excludes
- In-place project edits, extraction, and upgrades belong in `project-maintenance`.
- CI/CD provisioning, deployment, and Gemini Enterprise registration belong in `deployment-ops`.

## Read first
- `../../references/cli-reference.md` for command routing.
- `../../references/template-catalog.md` for the built-in template map.
- `../../references/package-overview.md` for install and sanity-check guidance.
- `references/workflows.md` for the end-to-end creation flow.
- `references/remote-templates.md` for `local@`, `adk@`, and remote repository syntax.
- `references/troubleshooting.md` for template-selection and creation failures.

## Common workflow
1. Confirm the package is installed with the bundled sanity checker when needed.
2. Use `list` when the user is still choosing a template.
3. Use `create` for new project generation.
4. If the user provides a remote template, read the remote-template reference before selecting `--base-template` or assuming the template is local.
5. After generation, hand off deployment or maintenance questions to the owning sub-skill instead of expanding this one.

## Useful signals
- Built-in templates: `adk`, `adk_a2a`, `adk_live`, `agentic_rag`, `langgraph`, `adk_go`, `adk_java`, `adk_ts`.
- Remote-template cues: `local@`, `adk@`, `adk-py@`, GitHub shorthand, or a full Git URL.
- Project-shape cues: `--agent-directory`, `--session-type`, `--datastore`, `--prototype`, `--in-folder`, and `--base-template`.
- Runtime constraints: project name length, agent-directory validity, template availability, and version-lock compatibility.

## Validation mindset
- Prefer a read-only install sanity check and command discovery before a real generation run.
- Treat remote-template fetches as optional or networked work, not as the default verification path.
- Do not route maintenance or cloud-deployment troubleshooting back here unless the issue is truly template selection or generation-time configuration.
