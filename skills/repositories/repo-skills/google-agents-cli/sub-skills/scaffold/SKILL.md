---
name: scaffold
description: "Use this sub-skill when creating or enhancing an ADK project with
  agents-cli scaffold create, scaffold enhance, or scaffold upgrade, including
  template, deployment target, CI/CD, session storage, and prototype-first
  decisions."
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

# Project Scaffolding

Use this sub-skill inside the `google-agents-cli` repo skill. It is a router plus operating checklist; move into the bundled references for full command flags, schemas, and examples.

## When to Use

- The user wants to create a new project, enhance an existing project, or upgrade generated files.
- The task asks about `agents-cli create`, `agents-cli scaffold create`, `enhance`, or `upgrade`.
- You need to map prototype/deployment/session/CI-CD choices to CLI flags.

## Workflow

1. Confirm project name/path and whether prototype-first is desired.
2. Map target architecture to `--deployment-target`, `--session-type`, and `--cicd-runner` flags.
3. Run `scaffold create` only for a new directory; use `scaffold enhance` for an existing project.
4. After scaffolding, load workflow/adk-code/eval for implementation and validation.

## Read These References

- `references/scaffold-guide.md` — read for scaffold guide details.
- `references/flags.md` — read for flags details.

## Verification and Safety

Safe checks: `agents-cli scaffold --help`; project creation/enhance mutates files and needs confirmation.

## Boundaries

- Does not write custom ADK business logic; use adk-code after project creation.
- Does not deploy live resources; use deploy after scaffold files exist.

## Related Sub-Skills

- `../workflow/SKILL.md` — lifecycle routing and approval gates.
- `../scaffold/SKILL.md` — project creation/enhancement.
- `../adk-code/SKILL.md` — ADK Python implementation patterns.
- `../eval/SKILL.md` — evaluation loops and metrics.
- `../deploy/SKILL.md` — deployment and infrastructure.
- `../publish/SKILL.md` — Gemini Enterprise registration.
- `../observability/SKILL.md` — logging, tracing, and analytics.
