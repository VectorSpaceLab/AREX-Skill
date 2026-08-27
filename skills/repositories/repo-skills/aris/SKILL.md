---
name: aris
description: "Use ARIS, the Auto Research in Sleep skill-based research harness,
  for setup, workflow routing, reviewer backend integration, state recovery,
  experiment operations, and repository maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ARIS

Use this skill when the user names ARIS, Auto-claude-code-research-in-sleep, Auto Research in Sleep, ARIS-Code, ARIS skills, ARIS research workflows, ARIS installer scripts, ARIS MCP reviewer backends, ARIS research-wiki/watchdog tooling, or asks how to run or maintain the ARIS skill corpus.

ARIS is a skill-based ML research automation harness. It coordinates a writing/execution agent with independent reviewers, persistent research state, GPU experiment operations, and audit gates through Markdown `SKILL.md` workflows and small helper scripts.

## Route By Task

- **Install, update, or distribute ARIS skills**: use `sub-skills/install-and-distribution/SKILL.md` for Claude Code, Codex CLI, Copilot CLI, selective installs, manifest reconciliation, project config blocks, and install troubleshooting.
- **Choose ARIS workflows or slash skills**: use `sub-skills/workflow-routing-and-skill-catalog/SKILL.md` for W1-W6 research workflow routing, skill groups, common parameters, Codex mirrors, and artifact handoffs.
- **Configure reviewer/provider backends**: use `sub-skills/review-and-provider-backends/SKILL.md` for Codex MCP, Claude/Gemini overlays, generic OpenAI-compatible LLM servers, MiniMax, ModelScope, manual review, Feishu/Lark, and cross-model review invariants.
- **Recover state or run/monitor experiments**: use `sub-skills/state-recovery-and-experiment-ops/SKILL.md` for `research-wiki/`, pipeline status, session recovery, hooks, watchdog tasks, experiment queues, and GPU/remote-server operating cautions.
- **Edit or verify the ARIS repository itself**: use `sub-skills/repository-maintenance/SKILL.md` for skill-catalog integrity, helper-resolution linting, Codex mirrors/overlays, provenance rules, focused tests, and safe contribution checks.

## Fast Start

1. Identify the host platform: Claude Code, Codex CLI, GitHub Copilot CLI, Cursor/Trae/Antigravity, or standalone ARIS-Code.
2. Decide whether the user is trying to **use ARIS in a research project** or **modify the ARIS repository**. Project-use tasks route to install/workflow/provider/state sub-skills; source edits route to repository maintenance.
3. ARIS is not a top-level pip-installable Python package. For a project install, use the official installer from the user's ARIS checkout or release in dry-run mode first, then follow `references/install-distribution-reference.md` before applying changes.
4. Keep external backends explicit. Codex, Claude, Gemini, MiniMax, ModelScope, Feishu/Lark, Overleaf, LaTeX, remote SSH, Vast, Modal, and GPUs are optional runtime integrations that need their own credentials or host tools.
5. For safety, prefer read-only diagnostics before running mutating installers or long-running experiments. The bundled scripts in `scripts/` are read-only helpers.

Minimal verification from this generated skill (run from the generated `aris/` directory, or replace `scripts/...` with that skill directory's path):

```bash
python scripts/aris_project_doctor.py --project /path/to/research-project
```

## Bundled References and Scripts

- `references/capability-map.md` maps ARIS capabilities to the owning sub-skill and source evidence used to distill them.
- `references/install-distribution-reference.md` summarizes install layouts, manifests, and update choices across platforms.
- `references/helper-resolution-and-project-files.md` describes helper lookup, project files, artifact contracts, and state files.
- `references/troubleshooting.md` covers cross-cutting failures: missing skills, stale installs, reviewer/backend mismatch, helper lookup, optional dependency, and state-recovery problems.
- `references/repo-provenance.md` records the source revision and extraction baseline.
- `scripts/aris_project_doctor.py` performs read-only checks on a target research project for ARIS installation and state indicators.
- `scripts/aris_helper_resolver.py` prints the helper path selected by the ARIS helper-resolution chain for a target project.

## Avoid

- Do not treat same-family Codex self-review as cross-model acceptance; mark it provisional unless an independent reviewer or deterministic verifier supplies the acceptance gate.
- Do not claim that live reviewer APIs, Feishu/Lark, Overleaf, LaTeX, or GPU backends are working unless the current environment has been explicitly checked.
- Do not run ARIS installers, update scripts, SSH/GPU jobs, or MCP servers without user intent; they can mutate projects, start services, or require credentials.
- Do not use this skill for generic literature review, GPU rental, paper writing, or patent drafting unless the task is specifically about ARIS's implementation or routing of those workflows.
