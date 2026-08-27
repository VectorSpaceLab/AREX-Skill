# Repository layout

This repository is intentionally lightweight: a Python CLI, a repo-owned runtime skill, public README/gallery material, and small community/release policy files. Use this map to decide where a maintenance change belongs.

| Area | Files | Owns | Maintainer notes |
|---|---|---|---|
| Package metadata | `pyproject.toml` | project name, version, Python floor, dependencies, keywords, URLs, console scripts | keep `gpt-image` mapped to `gpt_image_cli.cli:main` unless deliberately changing the public command |
| CLI package | `src/gpt_image_cli/` | parser flags, endpoint routing, output handling, exit behavior, key-loading behavior | update docs and skills whenever flags/defaults or public behavior change |
| Public docs | `README.md`, `README.zh.md` | install/update instructions, quick usage, selected gallery showcase, contribution links | keep English/Chinese public-facing changes aligned |
| Gallery assets | `docs/` | generated example images, community prompt data and indexes | prefer `docs/<category-slug>/<short-slug>.png`; avoid accidental root-level image drops |
| Runtime skill | `skills/gpt-image/` | published agent runbook, references, and helper scripts for normal GPT Image use | sync when CLI behavior, prompt gallery routing, or safety policy changes |
| Generated repo skill | `skills/disco/gpt-image-cli/` | DisCo operating skill tree and sub-skills for repo-aware use | keep self-contained, repository-relative, and free of review artifact paths |
| Plugin metadata | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | plugin name, description, version, keywords, homepage/repository metadata | sync with package/README install story when discovery text changes |
| GitHub community files | `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/*.yml` | contributor prompts, triage fields, PR verification checklist | update when review expectations or supported issue types change |
| Policy/release files | `CONTRIBUTING.md`, `CHANGELOG.md`, `SECURITY.md`, `SUPPORT.md`, `CODE_OF_CONDUCT.md` | contribution rules, release notes, vulnerability/support policy, conduct | keep public policy consistent with README and templates |

## Surface ownership rules

- **Gallery entry or category changes** start in the gallery source files: image assets under `docs/`, both READMEs, and the relevant `skills/gpt-image/references/gallery*.md` files.
- **CLI behavior changes** start in `src/gpt_image_cli/cli.py`; update `pyproject.toml` only when packaging, dependencies, Python support, or the entry point changes.
- **Install/discovery changes** must keep README install text, package metadata, plugin JSON, and release notes aligned.
- **Support/security changes** belong in the policy files first, then GitHub templates and README links.
- **Runtime skill wording changes** must preserve repository-relative links. Do not rely on any particular checkout location when writing generated skill text.

## Common synchronization sets

### Add or move a prompt/gallery entry

Check and update:

- `docs/<category-slug>/<short-slug>.png` for the image asset;
- `README.md` and `README.zh.md` for the selected showcase, numbering, image path, and count;
- `skills/gpt-image/references/gallery.md` for the category table and total prompt range;
- the matching `skills/gpt-image/references/gallery-<category>.md` for the concrete prompt and metadata;
- `docs/community-prompt-picks.json` and `docs/community-prompt-index.md` if the entry comes from the community-picks set.

### Change CLI flags, defaults, or endpoint behavior

Check and update:

- `src/gpt_image_cli/cli.py` and, if needed, `src/gpt_image_cli/__init__.py`;
- `README.md` / `README.zh.md` parameter tables and examples;
- `skills/gpt-image/SKILL.md` and CLI/API references that advertise flags or safety behavior;
- `pyproject.toml` only for entry point, dependency, or package metadata changes;
- `CHANGELOG.md` for user-visible behavior.

### Change plugin/package discovery

Check and update:

- `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`;
- `pyproject.toml` keywords/description/URLs if public package discovery changes;
- README install/update sections;
- `CHANGELOG.md` for visible release notes.

### Change release, support, or security policy

Check and update:

- `CHANGELOG.md`, `SUPPORT.md`, `SECURITY.md`, and `CONTRIBUTING.md`;
- `.github/PULL_REQUEST_TEMPLATE.md` and issue templates if contributor prompts or verification fields changed;
- README contribution/support links when public guidance changed.

## Generated skill boundary

The generated `skills/disco/gpt-image-cli/` tree is a runtime operating graph, not the source repository itself. It should explain how to maintain the repository, but it must not contain private local paths, test/review artifact references, or instructions to import/export the generated skill tree.
