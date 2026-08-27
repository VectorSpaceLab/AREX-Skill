---
name: repo-maintenance
description: "Maintain GPT-Image2-Skill repository surfaces: prompt/gallery
  entries, README/docs, plugin metadata, CLI/package flags,
  release/support/security policy, and offline pre-PR checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# repo-maintenance

Use this sub-skill when the task is to edit or review **GPT-Image2-Skill itself**: contributor-facing docs, gallery records, package metadata, CLI flags, plugin metadata, release/support/security policy, or focused checks before opening a PR.

Do **not** use this sub-skill for ordinary image generation, image editing, prompt selection, or gallery mining. Route those to [`../cli-and-api/SKILL.md`](../cli-and-api/SKILL.md) and [`../prompt-gallery/SKILL.md`](../prompt-gallery/SKILL.md). Import/export or runtime deployment of generated repo skills is out of scope here.

## Start here

- [`references/repository-layout.md`](references/repository-layout.md): repository map, ownership rules, and files to update for each public surface.
- [`references/contributor-workflows.md`](references/contributor-workflows.md): maintainer workflows for gallery, CLI/package, plugin, policy, release, and PR checks.
- [`references/troubleshooting.md`](references/troubleshooting.md): packaging drift, stale gallery indexes, accidental API calls, asset bloat, and runtime-skill path mistakes.
- [`scripts/check_repo_content.py`](scripts/check_repo_content.py): deterministic no-network checker for package entry points, skill frontmatter, gallery links, and image asset inventory.

## Maintenance operating loop

1. **Classify the change**: gallery/prompt, README/docs, CLI/package, plugin metadata, release notes, support/security, issue/PR templates, or generated skill maintenance.
2. **Open the source of truth** for that surface before editing. Use `pyproject.toml` for package identity and entry points; `src/gpt_image_cli/` for CLI behavior; `skills/gpt-image/` and its references for the runtime skill; README files for public install/usage/gallery showcase.
3. **Edit the smallest owning surface**, then update all public mirrors that describe it.
4. **Keep bilingual/public docs aligned**. User-facing gallery or install changes normally require matching `README.md` and `README.zh.md` updates.
5. **Stay offline by default**. Maintainer checks must not call OpenAI Images APIs, must not print API keys, and must not create or modify secret files.
6. **Run focused checks** and report what was verified, what was intentionally not verified, and any follow-up needed.

## Package and entry-point expectations

The repository is packaged as `gpt-image-cli`. The public console command is expected to remain:

```toml
[project.scripts]
gpt-image = "gpt_image_cli.cli:main"
```

When CLI flags, defaults, endpoint behavior, exit codes, or dependencies change, update the implementation under `src/gpt_image_cli/`, `pyproject.toml` if packaging changed, README usage tables/examples, `skills/gpt-image/SKILL.md`, and relevant generated-skill references.

## Files to update by change type

| Change type | Primary files | Mirrors to check |
|---|---|---|
| New or moved gallery entry | `docs/<category-slug>/`, `README.md`, `README.zh.md` | `skills/gpt-image/references/gallery.md`, matching `gallery-*.md`, community prompt index files when applicable |
| CLI flag/default/behavior | `src/gpt_image_cli/cli.py`, `src/gpt_image_cli/__init__.py` | `pyproject.toml`, README parameter/examples, `skills/gpt-image/SKILL.md`, CLI/API sub-skill references |
| Package metadata or entry point | `pyproject.toml` | README install/update text, plugin metadata, changelog |
| Plugin metadata | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | README install text, `pyproject.toml` keywords/description, changelog |
| Support/security/release policy | `SUPPORT.md`, `SECURITY.md`, `CHANGELOG.md`, `CONTRIBUTING.md` | issue templates, PR template, README contribution links |
| Generated runtime skill wording | `skills/gpt-image/`, `skills/disco/gpt-image-cli/` | repository-relative links, no private paths, no review artifact references |

## Safe local checks

Run only checks that do not generate images or contact external APIs unless the maintainer explicitly asks for live runtime validation.

```bash
git diff --check
python3 -m py_compile src/gpt_image_cli/cli.py src/gpt_image_cli/__init__.py
python skills/disco/gpt-image-cli/sub-skills/repo-maintenance/scripts/check_repo_content.py .
uv run gpt-image --help
```

`uv run gpt-image --help` is suitable for confirming the installed CLI surface after packaging or parser changes; it should not require an API key or make an image request.
