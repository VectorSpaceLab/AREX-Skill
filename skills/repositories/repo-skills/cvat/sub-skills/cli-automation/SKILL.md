---
name: cli-automation
description: "Operate CVAT through cvat-cli for profiles, auth, task/project
  automation, datasets, backups, frames, auto-annotation, and native functions."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# CVAT CLI automation

Use this sub-skill when the user needs terminal automation with `cvat-cli`: profile/config setup, credential-safe command construction, task/project lifecycle commands, dataset import/export, backup/restore, frame downloads, local auto-annotation, native function commands, JSON list output, or shell scripting patterns.

## Route first

- Use `references/cli-reference.md` for exact global flags, command grammar, argument order, deprecated aliases, and command-to-API ownership.
- Use `references/workflows.md` for copyable end-to-end shell flows and validation checkpoints.
- Use `references/troubleshooting.md` when a command fails, prompts unexpectedly, leaks auth risk into shell history, has profile/config permission errors, or receives server/API/function errors.
- Use `scripts/cvat_cli_command_builder.py` to generate quoted `cvat-cli` commands without executing them.

## Safety defaults

- Prefer Personal Access Tokens through `CVAT_ACCESS_TOKEN` or saved profiles. Do not put token values or passwords into generated command lines, logs, notebooks, or shell history.
- Prefer `--profile NAME` for repeated automation. It is mutually exclusive with `--server-host`, `--server-port`, and `--auth`.
- If password auth is unavoidable, use `--auth USER` with `PASS` set out of band or let the CLI prompt; avoid `--auth USER:PASS` in scripts.
- Add `--org SLUG` when operating in an organization workspace; pass an empty slug only when the user explicitly wants the personal workspace.
- For destructive operations (`task delete`, `project delete`, `function delete`), list and confirm IDs first, and preserve backups when recovery matters.

## Quick command grammar

```bash
cvat-cli <global-options> <resource> <action> <action-options>
```

Resources are `task`, `project`, `profile`, `config`, and `function`. Backward-compatible task aliases such as `cvat-cli ls`, `dump`, `upload`, `export`, and `import` exist but are deprecated; use `cvat-cli task ...` in new automation.

## Minimal examples

```bash
# Save a server/token profile without exposing the token in the command line.
cvat-cli --server-host https://app.cvat.ai profile create --name prod --set-default

# List tasks as JSON for scripts.
cvat-cli --profile prod --org team-slug task ls --json > tasks.json

# Create a task from local files and print the new task ID.
cvat-cli --profile prod task create "demo" --labels labels.json local image1.jpg image2.jpg

# Export annotations, optionally including images.
cvat-cli --profile prod task export-dataset --format "COCO 1.0" --with-images no 42 annotations.zip

# Download selected frames.
cvat-cli --profile prod task frames --outdir frames --quality compressed 42 0 10 20
```

If the task is really about Python SDK scripts, dataset format semantics, auto-annotation function implementation, or server deployment, route to sibling sub-skills rather than expanding this CLI skill.
