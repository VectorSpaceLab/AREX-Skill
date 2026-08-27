---
name: workflow
description: "Use this sub-skill for the end-to-end Google Agents CLI lifecycle:
  requirements clarification, recipe study, scaffolding, building, evaluating,
  deploying, publishing, observing, command routing, and operational rules."
metadata:
  disco-role: operating
  author: Google
  license: Apache-2.0
  version: 1.3.1
  requires:
    bins:
      - agents-cli
    install: "uv tool install google-agents-cli"
disable-model-invocation: true
license: Apache 2.0
---

# Agents CLI Lifecycle Workflow

Use this sub-skill inside the `google-agents-cli` repo skill. It is a router plus operating checklist; move into the bundled references for full command flags, schemas, and examples.

## When to Use

- The user wants an end-to-end ADK agent build plan.
- The task mentions requirements, spec, lifecycle phases, command routing, or safe coding-agent behavior.
- You need to decide which Agents CLI sub-skill to load next.

## Workflow

1. Clarify the user goal and constraints before mutating a project.
2. Write or update the project spec when building a new agent.
3. Route to scaffold, adk-code, eval, deploy, publish, or observability at the phase boundary.
4. Ask before cloud, git remote, skill-install, or irreversible operations.

## Read These References

- `references/workflow-guide.md` — read for workflow guide details.
- `references/brainstorming.md` — read for brainstorming details.
- `references/commands.md` — read for commands details.
- `references/internals.md` — read for internals details.
- `references/spec-template.md` — read for spec template details.
- `references/terminology.md` — read for terminology details.

## Verification and Safety

Safe checks: `agents-cli --help`, `agents-cli info` inside a project, and root `scripts/inspect_cli_tree.py`.

## Boundaries

- Does not replace the detailed command/flag references in narrower sub-skills.
- Does not create or mutate projects until the relevant sub-skill confirms inputs.

## Related Sub-Skills

- `../workflow/SKILL.md` — lifecycle routing and approval gates.
- `../scaffold/SKILL.md` — project creation/enhancement.
- `../adk-code/SKILL.md` — ADK Python implementation patterns.
- `../eval/SKILL.md` — evaluation loops and metrics.
- `../deploy/SKILL.md` — deployment and infrastructure.
- `../publish/SKILL.md` — Gemini Enterprise registration.
- `../observability/SKILL.md` — logging, tracing, and analytics.
