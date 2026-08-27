---
name: install-and-distribution
description: "Install, update, reconcile, uninstall, and verify ARIS skills
  across Claude Code, Codex CLI, GitHub Copilot CLI, and related project-local
  layouts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Install and Distribution

Use this sub-skill when the task is about installing ARIS, updating skill links, selecting skill groups, reconciling manifests, configuring host project files, migrating old layouts, or diagnosing why ARIS slash skills are not discovered.

## Route Here

- Install ARIS into a research project for Claude Code, Codex CLI, Cursor, Trae, Antigravity, or GitHub Copilot CLI.
- Choose between all-skills install, group install, explicit skill install, excludes, and new-skill reconciliation.
- Explain or troubleshoot `.claude/skills`, `.agents/skills`, `.github/skills`, `.aris/installed-skills*.txt`, `.aris/tools`, and declined-skill files.
- Preview or audit installer changes before running mutating commands.
- Decide how Codex mirrors and Claude/Gemini overlays should be installed.

## Reroute

- Workflow or slash-skill choice after installation: `../workflow-routing-and-skill-catalog/SKILL.md`.
- MCP reviewer/provider environment variables and model routing: `../review-and-provider-backends/SKILL.md`.
- Research Wiki, session recovery, watchdog, or experiment state after install: `../state-recovery-and-experiment-ops/SKILL.md`.
- Editing installer source or running native installer tests in the ARIS repository: `../repository-maintenance/SKILL.md`.

## Safe Install Pattern

1. Identify the target research project and host platform.
2. Run a read-only inspection first:

   ```bash
   python scripts/aris_project_doctor.py --project /path/to/project
   ```

3. If the user wants installation, use the official ARIS installer from the user's ARIS checkout or release. This generated skill intentionally does not vendor large mutating installers.
4. Prefer `--dry-run` before a first install into a non-empty project.
5. Use a named `--replace-link` or `--adopt-existing` only after verifying the exact symlink target and manifest ownership.
6. Restart the host agent after changing skills or MCP configuration.

## Reference Map

- `references/setup-workflows.md` gives platform-specific install/update recipes and validation steps.
- `references/installer-safety.md` explains manifests, symlink rules, stale locks, migration, and why the installer refuses some paths.
- `references/troubleshooting.md` covers missing slash commands, stale manifests, declined skills, overlay confusion, and helper-link problems.
- Root `../../references/install-distribution-reference.md` summarizes platform layouts and common flags.

## Verification Signals

For repository maintenance or after a generated fix, use the native candidate set in the verification report: installer help probes, selective installer tests, link replacement tests, `.aris/tools` symlink tests, and Codex/Copilot fixture tests. Do not validate installer behavior by experimenting on a real user project unless the user explicitly approves the mutation.
