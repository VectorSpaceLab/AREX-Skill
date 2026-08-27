---
name: examples-and-recipes
description: "Choose, adapt, and troubleshoot Agent Lightning example workflows
  and optional dependency/backend recipes without reopening original repo
  examples."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Examples and recipes

Use this sub-skill when the user asks which Agent Lightning example fits a task, how to adapt an example, what optional dependencies/backends are needed, or how to add a new example.

## Route by task

| Request | Read |
| --- | --- |
| Pick an example family for a user workflow | [references/example-catalog.md](references/example-catalog.md) |
| Decide install groups/backends and safe verification level | [references/dependency-and-backend-matrix.md](references/dependency-and-backend-matrix.md) |
| Add or maintain a new example | [references/example-contribution-guide.md](references/example-contribution-guide.md) |
| Debug optional example failures | [references/troubleshooting.md](references/troubleshooting.md) |

## Key rules

- Most full examples require external services, GPU, datasets, Docker, or long training time. Do not run them by default.
- Start with CPU-local smokes from other sub-skills: authoring, tracing, store, CLI, and endpoint checks.
- Clearly separate "interface can be checked" from "full training semantics verified".
- For optional example workflows, confirm endpoint credentials, model/data availability, hardware, and dependency groups first.
- When creating a new example, include README smoke-test instructions and an "Included Files" section.

## Boundary

This sub-skill is a catalog and decision aid. It does not replace focused API guidance in [agent-authoring](../agent-authoring/SKILL.md), [tracing-and-instrumentation](../tracing-and-instrumentation/SKILL.md), [runner-store-training](../runner-store-training/SKILL.md), or [cli-and-services](../cli-and-services/SKILL.md).
