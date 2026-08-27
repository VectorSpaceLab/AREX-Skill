---
name: cli
description: "Guides safe modification and operation of the Observal Python CLI,
  including Typer registration, output and error contracts, noninteractive
  behavior, bundled skill synchronization, and CLI-focused tests."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Observal CLI Sub-skill

Use this sub-skill when the task touches the Python `observal` CLI surface: Typer command registration, command groups, command help, table or JSON output, categorized errors, noninteractive automation, CLI/API client behavior, bundled Observal skill synchronization, or CLI-specific tests.

## Route the task

| Task | Read |
| --- | --- |
| Understand where a command is registered, which module owns it, or how output/errors flow | [CLI architecture](references/cli-architecture.md) |
| Add, rename, remove, or use commands under `auth`, `config`, `scan`, `doctor`, `registry`, `agent`, `ops`, `admin`, `server`, or related groups | [Command workflows](references/command-workflows.md) |
| Change CLI paths, flags, examples, docs, or agent-facing behavior that must be reflected in bundled skills | [Bundled skills](references/bundled-skills.md) |
| Debug install/import failures, dirty JSON mode, API failures, config issues, optional dependency failures, telemetry/harness command failures, or unsafe retries | [Troubleshooting](references/troubleshooting.md) |
| Quickly inspect the imported CLI app and bundled-skill presence | Run `scripts/check_cli_contract.py --help` |

Read the selected reference before editing. Do not depend on repository docs or tests for the operating contract; this sub-skill distills the relevant rules and names.

## Operating rules

1. Keep the canonical CLI entry point as `observal_cli.main:app`; add new top-level groups only when no existing group fits.
2. Use the existing Typer app for the relevant domain module and verify the final command path with help or static introspection before documenting it.
3. Structured commands support `--output table|json` using `OutputMode`; JSON mode must write machine JSON only and must not print Rich tables, prompts, spinners, banners, or progress text.
4. API-backed commands use the shared `observal_cli.client` functions and the shared error contract in `observal_cli.errors`; add audited labels in `observal_cli.error_context` for every new client call site.
5. Agent and CI workflows must be noninteractive: expose required inputs as arguments or options, require explicit confirmation flags for destructive JSON mutations, and use dry-run when a multi-resource preview is meaningful.
6. Mutations are sent once. After a timeout or connection failure following a mutation, read current state before retrying.
7. When a path, flag, output shape, example, or behavior changes, update the matching `docs/cli` page and every affected bundled skill under `observal_cli/skills`, then regenerate the generated command reference.
8. Verify with the narrow CLI tests plus static contract checks before declaring the change complete.

## Boundaries

- The root `observal` repo skill owns high-level routing, installation summary, provenance, and cross-cutting smoke checks.
- This `cli` sub-skill owns the Python CLI hierarchy and bundled Observal skill behavior.
- `server` owns FastAPI routes, data models, migrations, jobs, insights, and server-side auth/admin implementation.
- `harness-telemetry` owns harness registry entries, adapters, hook specs, session parsers, and telemetry delivery internals.
- `web` owns the Vite/React/TanStack Router frontend and Playwright guidance.
- `repo-development` owns contributor policy, lint/test/release/compliance workflows, and change-review mechanics.
