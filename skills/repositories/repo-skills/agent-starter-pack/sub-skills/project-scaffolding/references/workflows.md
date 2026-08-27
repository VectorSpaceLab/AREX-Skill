# Scaffolding workflows

## New project creation
Use `create` when the user wants a fresh project.

Typical flow:
1. Pick or discover a template with `list`.
2. Choose the deployment target and any optional data/session settings.
3. Decide whether to create a new directory or template in-place with `--in-folder`.
4. If the template is remote, confirm whether it should be treated as a local path, an ADK samples shortcut, or a generic Git source.
5. Generate the project and then move to maintenance or deployment guidance as needed.

Common `create` signals:
- `--agent` or `-a`
- `--deployment-target` or `-d`
- `--cicd-runner`
- `--datastore` / `-ds`
- `--session-type`
- `--region`
- `--agent-directory` / `-dir`
- `--prototype`
- `--in-folder`
- `--auto-approve` / `--yes` / `-y`
- `--skip-checks`
- `--bq-analytics`
- `--google-api-key` / `--api-key` / `-k`
- `--base-template` for remote templates

### Generation-time defaults to remember
- Auto-approve mode supplies sensible defaults instead of prompting.
- The project name is normalized for cloud-friendly resource naming.
- Data ingestion is enabled automatically for templates that require it.
- Some templates support only a subset of deployment targets.

## Template discovery
Use `list` when the user needs to compare template choices.

Modes:
- Built-in list: no flags.
- Official ADK samples: `--adk`.
- Local or remote source: `--source`.

`list` is a discovery tool, not a generation tool. If the user has already picked a template, skip back to `create`.

## Project shape and output cues
The generated project usually includes:
- A template-specific agent directory.
- A `README.md` with runnable instructions.
- A `Makefile` for local development and deployment commands.
- Optional CI/CD and infrastructure directories when those options are enabled.
- Optional data-ingestion, frontend, or notebook files for templates that need them.

## When to read the remote-template reference
Read `references/remote-templates.md` whenever the user mentions:
- `local@`
- `adk@`
- `adk-py@`
- a Git URL
- a branch, tag, or `@ref`
- `--base-template`
- remote-template version locking

## Handoff points
- If the user wants to enhance an existing project, switch to `project-maintenance`.
- If the user wants deployment setup or Gemini Enterprise registration after generation, switch to `deployment-ops`.
