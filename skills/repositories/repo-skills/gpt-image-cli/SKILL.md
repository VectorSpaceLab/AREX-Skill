---
name: gpt-image-cli
description: "Use GPT-Image2-Skill and the gpt-image-cli package for OpenAI GPT
  Image 2 CLI/API workflows, prompt-gallery guidance, and repository
  maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# gpt-image-cli

Use this repo skill when a task names GPT-Image2-Skill, `gpt-image-cli`, `gpt-image`, GPT Image 2 / `gpt-image-2`, OpenAI image generation/editing, image prompt galleries, or maintenance of this package's CLI/agent-skill surfaces.

This skill is a **self-contained operating guide** for the repo. It does not import itself into any live router, does not export to Codex/Claude, and does not run billable OpenAI Images API calls by default.

## Start with the task route

| User task | Read |
|---|---|
| Build, preflight, or troubleshoot `gpt-image` commands; map CLI flags to OpenAI SDK calls; handle reference edits, masks, output files, formats, size, quality, or exit codes | [`sub-skills/cli-and-api/SKILL.md`](sub-skills/cli-and-api/SKILL.md) |
| Choose/adapt gallery prompts; create prompt skeletons for research figures, UI mockups, posters, typography, photography, anime/game/product styles, diagrams, or edit instructions | [`sub-skills/prompt-gallery/SKILL.md`](sub-skills/prompt-gallery/SKILL.md) |
| Edit the repository itself: add gallery entries, update README/docs/plugin metadata, change CLI flags, review PR readiness, or keep public mirrors aligned | [`sub-skills/repo-maintenance/SKILL.md`](sub-skills/repo-maintenance/SKILL.md) |

## Package facts

- Distribution/package name: `gpt-image-cli`.
- Import package: `gpt_image_cli`.
- Console script: `gpt-image`.
- Python requirement: Python 3.11 or newer.
- Runtime dependencies: `openai` and `python-dotenv`.
- Current verified package version for this skill: `0.2.0`.
- Default model in the CLI: `gpt-image-2`.

Minimal import and CLI checks:

```bash
python - <<'PY'
import gpt_image_cli
from gpt_image_cli import cli
print(cli.DEFAULT_MODEL)
print(cli.resolve_size("portrait"))
PY

gpt-image --help
```

If the package is not installed, install from the public package source for the target environment, then re-run `gpt-image --help`. Do not create or overwrite API-key files during setup.

## Safety and cost boundary

Real generation or edit calls require `OPENAI_API_KEY`, network access, and may bill the user's OpenAI account. Ask before running real API calls unless the user has already made the execution request and accepted the credential/cost boundary. Never print secret values. For dry-run checks, use [`scripts/check_install.py`](scripts/check_install.py) and the CLI sub-skill helper instead of calling the API.

## Shared references

- [`references/troubleshooting.md`](references/troubleshooting.md): cross-cutting installation, credential, billing, package, and router issues.
- [`references/repo-provenance.md`](references/repo-provenance.md): source snapshot used to generate this skill; read before deciding whether to refresh it.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json): structured scenario metadata for a future managed repo-skill import.

## Shared script

- [`scripts/check_install.py`](scripts/check_install.py): safe no-network package/CLI inspection; use it before deeper CLI/API troubleshooting or after installing the package.

## Non-goals

- Do not use this skill to bypass a host runtime's native image-generation tool when the user explicitly wants that native path.
- Do not run full image generation/editing as verification; use help, parser, import, and file-validation checks unless the user requests live API execution.
- Do not import this generated repo skill automatically; this production run was requested with **not import**.
