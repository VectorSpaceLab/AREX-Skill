---
name: github-automation
description: "Routes OpenHands GitHub Actions examples, prompt-driven agent
  runners, TODO scanning, and example-run reporting workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# GitHub Automation

Use this sub-skill for SDK-powered GitHub Actions examples and supporting scripts: prompt-driven task runners, TODO scanning, example-run summaries, and workflow-level automation.

## What this route owns

- Prompt-loaded agent runner scripts for local or CI use.
- TODO scanner behavior and filter rules.
- Example-run report rendering.
- GitHub Actions examples that invoke the OpenHands SDK.

## Start here

Read [`references/actions-workflows.md`](references/actions-workflows.md) for the workflow patterns and script entry points. Read [`references/troubleshooting.md`](references/troubleshooting.md) when prompts, credentials, remote URLs, or example summaries fail.

Scripts:

- [`scripts/run_prompt_task.py`](scripts/run_prompt_task.py)
- [`scripts/todo_scanner.py`](scripts/todo_scanner.py)
- [`scripts/render_examples_report.py`](scripts/render_examples_report.py)

## Typical triggers

- "Run an agent from a GitHub Action prompt file or URL."
- "Scan the repo for TODO(openhands) comments."
- "Render a markdown summary of example script results."
- "How do I wire this into a workflow dispatch job?"

## Cross-links

- For local agent lifecycle and `Conversation` behavior, go to [`../agent-core/SKILL.md`](../agent-core/SKILL.md).
- For remote server startup used by examples, go to [`../remote-runtime/SKILL.md`](../remote-runtime/SKILL.md).
- For repository-maintenance policies or test selection, go to [`../repo-development/SKILL.md`](../repo-development/SKILL.md).
