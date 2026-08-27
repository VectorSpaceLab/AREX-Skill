---
name: repo-development
description: "Routes OpenHands Software Agent SDK repository maintenance,
  testing, compatibility, CI, and packaging workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Repository Development

Use this sub-skill when the task is to edit, review, test, package, or maintain this monorepo rather than use it as a library.

## What this route owns

- Package and workspace boundaries across `openhands-sdk`, `openhands-tools`, `openhands-workspace`, and `openhands-agent-server`.
- Build, format, lint, pre-commit, and test workflows.
- Import dependency checks and tool-registration checks.
- Persisted-settings compatibility and API/REST compatibility policies.
- Example runner requirements and example discovery rules.
- CI workflows and release-maintenance guardrails.

## Start here

Read [`references/build-test-and-ci.md`](references/build-test-and-ci.md) for the normal checkout commands and test-selection strategy. Read [`references/compatibility-gates.md`](references/compatibility-gates.md) for the public API, REST, and settings compatibility rules. Read [`references/troubleshooting.md`](references/troubleshooting.md) when a repo-level check fails.

Scripts:

- [`scripts/check_import_rules.py`](scripts/check_import_rules.py)
- [`scripts/check_tool_registration.py`](scripts/check_tool_registration.py)

## Typical triggers

- "I changed a package and need the right tests."
- "Why did a compatibility check fail?"
- "How do I run pre-commit on the files I changed?"
- "Which CI or example workflow applies to this repo change?"

## Cross-links

- For local SDK usage, go to [`../agent-core/SKILL.md`](../agent-core/SKILL.md).
- For tool implementations, go to [`../built-in-tools/SKILL.md`](../built-in-tools/SKILL.md).
- For remote runtime and agent-server changes, go to [`../remote-runtime/SKILL.md`](../remote-runtime/SKILL.md).
