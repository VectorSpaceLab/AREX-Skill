---
name: "project-workflows"
description: "Operate spaCy project.yml workflows safely with local validation,
  dry runs, and explicit network boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# project-workflows

Use this sub-skill for project-level spaCy orchestration: cloning templates, fetching assets, running commands and workflows, generating docs, generating DVC config, and pushing or pulling outputs from remotes.

## Read or run these first
- [`references/project-workflows.md`](references/project-workflows.md) — read this for the command map, safe vs side-effect boundaries, dependency/output tracking, and workflow order.
- [`references/project-yml-reference.md`](references/project-yml-reference.md) — read this for `project.yml` keys, command and asset field rules, and requirements checks.
- [`references/troubleshooting.md`](references/troubleshooting.md) — read this when clone, assets, run, document, push, pull, or DVC fails or warns.
- [`scripts/validate_project_yml.py`](scripts/validate_project_yml.py) — run this on a local project file before any networked or remote command.

## Default operating order
1. Validate the project file locally.
2. Inspect or generate documentation.
3. Use `project run --dry` before the first real run.
4. Fetch assets only when you know whether `--extra` is needed.
5. Run the narrowest command that covers the change.
6. Use `push`, `pull`, and `dvc` only after remotes or DVC are confirmed.

## Route elsewhere when the work shifts
- If the project command centers on training config, `spacy train`, `spacy convert`, `spacy evaluate`, or `spacy package`, use `training-and-cli`.
- If the issue is package import, installation, or model download, use `install-and-inspect`.
- If a project script defines custom pipeline components or factories, use `pipeline-components`.

## Verification focus
- `project-document-dry-run`: local temp project, `project document`, and `project run --dry`.
- `project-assets-remote`: help-only and skip-network checks for `project assets`, `push`, and `pull`.

## Boundaries
- Do not treat external template cloning as a validation step.
- Do not assume remote storage, credentials, or network access are available.
- Do not move into training internals or model-serving integrations here.
