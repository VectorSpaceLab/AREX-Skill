---
name: cli-and-automation
description: "Day-to-day OpenSquilla CLI automation for chat, agent runs,
  sessions, memory, cron, cost, diagnostics, replay, migration, recovery,
  sandbox posture, bundle, dist, reset, init, and uninstall."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# CLI and Automation

Use this sub-skill as the command hub for an existing OpenSquilla user who has already installed the package and is asking how to run, automate, inspect, or clean up ordinary CLI workflows. The evidence for this skill was checked against OpenSquilla 0.5.3 in a CPU-only inspection build where the `opensquilla` entry point and assigned command help surfaces loaded successfully.

## Load This When

- The user asks for `opensquilla chat`, `agent`, `code-task`, `sessions`, `memory`, `agents`, `cron`, `cost`, `diagnostics`, `replay`, `bundle`, `dist`, `migrate`, `recovery`, `sandbox`, `reset`, `init`, or `uninstall` usage.
- The user wants non-interactive CLI patterns with `--json`, `--timeout`, workspace controls, transcripts, usage files, progress events, or bounded retries.
- The user needs a safe sequence for session export/resume, memory indexing/repair/flush, scheduled jobs, cost inspection, diagnostics/replay, migration preview/apply, recovery, or data removal.
- The user is confused about gateway-backed commands versus local/offline commands after first setup.

## Route Elsewhere

- First-run install, onboarding, gateway lifecycle, Web UI launch, or `doctor` readiness basics: [setup-and-gateway](../setup-and-gateway/SKILL.md).
- Provider credentials, model selection, router modes, model catalog, search providers, or raw config precedence: [configuration-and-routing](../configuration-and-routing/SKILL.md).
- Messaging channels, pairings, channel delivery, and MCP bridge setup: [channels-and-integrations](../channels-and-integrations/SKILL.md).
- Skill catalog, skill install/update/publish, or meta-skill runs: [skills-and-meta](../skills-and-meta/SKILL.md).
- Terminal UI renderer selection, OpenTUI behavior, desktop shell startup, or Web UI presentation details: [tui-and-desktop](../tui-and-desktop/SKILL.md).

## Operating Rules

1. Identify whether the command is gateway-backed before prescribing it. Sessions, most memory inspection commands, cron, cost, diagnostics, and `reset` need a reachable gateway; `agent`, `chat --standalone`, `code-task`, `replay`, `dist`, `bundle`, `migrate`, `recovery`, `sandbox`, `init`, and `uninstall` are local/offline or manage their own process as documented in the bundled references.
2. Prefer `--json` and explicit confirmation flags for scripts, but never hide destructive consequences. `uninstall` and `cron remove/run` have confirmation behavior; `code-task solve` requires `--yes` for non-interactive trusted-host use; `migrate` is dry-run until `--apply`.
3. For automation that can touch files, set an explicit `--workspace`; add `--workspace-strict`, `--workspace-lockdown`, and `--scratch-dir` when containment matters. Use per-run transcript, usage, event-stream, and session DB paths when jobs must be reproducible.
4. Keep sharing surfaces redacted. Session exports, diagnostics bundles, replay output, raw diagnostics, and `bundle --include-content` can contain prompts, tool results, private paths, secrets, or channel identifiers.
5. Do not assume the original repository checkout exists at runtime. Use only the command patterns and local references bundled in this generated skill.

## Reference Map

- [Command map](references/command-map.md): command groups, gateway requirements, JSON support, and common examples.
- [Automation patterns](references/automation-patterns.md): non-interactive agent, code-task, cron, event-stream, workspace, and parallel-run patterns.
- [State and data workflows](references/state-and-data-workflows.md): sessions, memory, diagnostics, cost, migration, recovery, bundle/dist, reset, init, sandbox, and uninstall workflows.
- [Troubleshooting](references/troubleshooting.md): gateway dependency failures, session export risk, stale memory index/repair, migration conflicts, uninstall purge safety, sandbox posture confusion, optional dependency gaps, and live-script boundaries.

## Quick Triage

- "Run one prompt and return machine-readable output" → `opensquilla agent --json -m "..."`; see [automation patterns](references/automation-patterns.md#one-shot-agent-runs).
- "Continue or export a prior conversation" → `opensquilla sessions ...`; see [state workflows](references/state-and-data-workflows.md#sessions-and-history).
- "Find or repair durable memory" → `opensquilla memory ...`; see [state workflows](references/state-and-data-workflows.md#memory-index-search-flush-and-repair).
- "Schedule repeated work" → `opensquilla cron ...`; see [automation patterns](references/automation-patterns.md#scheduled-runs).
- "Debug a surprising or costly turn" → `diagnostics`, `cost`, `replay`, and `bundle`; see [state workflows](references/state-and-data-workflows.md#diagnostics-cost-replay-and-bundles).
- "Move state from another runtime or recover profile data" → `migrate` or `recovery`; see [state workflows](references/state-and-data-workflows.md#migration-and-recovery).
- "Remove OpenSquilla or reset data" → start with `uninstall --dry-run`; see [state workflows](references/state-and-data-workflows.md#reset-init-sandbox-and-uninstall).
