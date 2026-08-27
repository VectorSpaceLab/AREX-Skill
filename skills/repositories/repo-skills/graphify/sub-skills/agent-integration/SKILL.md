---
name: agent-integration
description: "Install Graphify assistant skills, always-on guidance, and hooks
  safely across supported agent platforms."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# agent-integration

Use this sub-skill when the user wants to install, inspect, repair, uninstall, or package Graphify's assistant integration layer: packaged `SKILL.md` files, `references/` sidecars, always-on project guidance, PreToolUse/BeforeTool hooks, Git hooks, strict mode, and user-vs-project scope decisions.

Start from the graphify root router when the complete runtime tree includes one and the request may involve non-install workflows too.

## Route here for

- `graphify install`, `graphify uninstall`, `graphify <platform> install`, or `graphify <platform> uninstall`.
- Choosing a supported assistant platform, including aliases such as `--platform skills` for `agents`.
- Deciding user scope versus project scope, and interpreting project-scoped `git add` hints.
- Installing, inspecting, or removing `graphify hook install/status/uninstall` and assistant PreToolUse/BeforeTool hooks.
- Claude strict mode and the `GRAPHIFY_HOOK_STRICT` runtime override.
- Troubleshooting `graphify` not found, wrong PyPI package name, stale installed skill versions, missing `references/` sidecars, Codex's no-op hook, or platform-specific install artifacts.
- Maintainer-only questions about how Graphify renders and packages its platform skill bodies.

## Route elsewhere

- Building, updating, watching, or validating `graphify-out/` graphs: use [graph-building](../graph-building/SKILL.md).
- Querying an existing graph with `query`, `path`, `explain`, MCP serving, or query-first answer behavior: use [query-navigation](../query-navigation/SKILL.md).
- Export, merge, database, PR, or visualization workflows: use [exports-integrations](../exports-integrations/SKILL.md).
- File-format/parser/extractor failures after install succeeds: use [extractor-troubleshooting](../extractor-troubleshooting/SKILL.md).

## Safety defaults

1. **Do not mutate a real HOME or project config unless the user explicitly asked for that install/uninstall scope.** For exploration, use the bundled temp probe from the `graphify` repo-skill root: `python sub-skills/agent-integration/scripts/install_platform_probe.py --platform codex --scope project`.
2. **Distinguish the package name from the command.** Install the official PyPI package as `graphifyy`; the CLI and import package are `graphify`.
3. **Prefer project scope for team-visible assistant guidance.** `graphify install --project --platform <platform>` writes artifacts under the current repository when that platform supports project install and prints `git add` hints.
4. **Use user scope only for personal assistant skills.** `graphify install --platform <platform>` writes under the user's assistant config tree; ask before doing this in a real HOME.
5. **Treat skill-only installs and always-on guidance as related but not identical.** Some `graphify install --platform ...` commands copy only a skill body, while platform subcommands such as `graphify codex install` wire project instructions or hooks.

## Operating workflow

1. **Confirm target and scope.** Identify the assistant platform, user/project scope, whether the user wants skill-only install or always-on guidance, and whether uninstall should also purge `graphify-out/`.
2. **Verify CLI availability.** Run `graphify --help` or `python -m graphify --help`. If missing, use [troubleshooting](references/troubleshooting.md#graphify-command-not-found) before attempting install.
3. **Probe safely when uncertain.** Run [install_platform_probe.py](scripts/install_platform_probe.py) with a temporary HOME/project and inspect the summarized files.
4. **Install with the smallest correct command.** Use [platforms.md](references/platforms.md) to choose the platform command and expected artifacts.
5. **Inspect hooks and always-on files.** Use [always-on-and-hooks.md](references/always-on-and-hooks.md) for hook/strict behavior and `graphify hook status` for Git hooks.
6. **Repair or uninstall precisely.** Use platform-specific uninstall or `graphify uninstall --project --platform <platform>` for project scope; use `graphify uninstall --purge` only when the user also wants graph outputs removed.
7. **For maintainer packaging work only,** load [platform-skill-packaging.md](references/platform-skill-packaging.md).

## Quick command patterns

```bash
# Recommended package install when Graphify is missing.
uv tool install graphifyy

# Skill-only default: Claude Code on Linux/macOS, Windows variant on Windows.
graphify install

# Named user-scope skill install. Ask before using a real HOME.
graphify install --platform codex

# Project-scoped install with commit hints.
graphify install --project --platform codex

# Platform always-on guidance in the current project.
graphify codex install
graphify claude install

# Claude Code project strict mode.
graphify install --project --strict

# Project Git hooks that keep graphify-out fresh after commits/branch switches.
graphify hook install
graphify hook status
graphify hook uninstall

# Remove assistant integrations; add --purge only to delete graphify-out/.
graphify uninstall
graphify uninstall --project --platform codex
graphify uninstall --purge
```

## Verification cues

A healthy progressive platform install has `SKILL.md`, `.graphify_version`, and usually a `references/` sidecar in the platform's `graphify` skill directory. Always-on platforms additionally have a project instruction file such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/graphify.mdc`, `.github/copilot-instructions.md`, `.kiro/steering/graphify.md`, or `.agents/rules/graphify.md`. Hook-enabled platforms have JSON settings, native plugin files, or Git hook files as described in the references.
