# Catalog Layout Reference

## Purpose

Read this when deciding which file to edit in the NVIDIA skills catalog. The repository separates hand-maintained source-of-truth files from generated mirrors and marketplace outputs.

## Source Of Truth Map

| Area | Maintained by humans | Generated or mirrored outputs | Notes |
| --- | --- | --- | --- |
| Product registrations | `components.d/*.yml` | `skills/<catalog_dir>/` via sync; README tables | One component file per product avoids merge conflicts. |
| Manual/direct catalog exceptions | `.github/scripts/manual-components.yml`, `catalog-exceptions.yml` | README rows and orphan-prune allow-list | Use only with a documented reason and owner. |
| Product skill payloads | Upstream product repos, except explicit direct PR exceptions | `skills/<catalog_dir>/` | Each catalog skill must carry `SKILL.md`, `skill-card.md`, `skill.oms.sig`, eval JSON, and `BENCHMARK.md`. |
| Plugin packaging | `plugins.d/*.yml`, `plugins.d/_defaults.yml`, plugin assets/README when intentionally hand-maintained | `plugins/<name>/...`, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `.cursor-plugin/marketplace.json` | Rebuild with the bundled check guidance instead of editing generated plugin manifests directly. |
| Catalog metadata | Skill frontmatter, skill cards, `components.d`, metadata schema/config | `.github/scripts/marketplace/metadata.json`, `skills.sh.json` | Pull requests use deterministic `--check --no-ai`; regeneration with AI enrichment is CI/dispatch behavior. |
| Benchmarks | Per-skill `BENCHMARK.md` | Root `benchmarks.json` | Aggregated for dashboards and marketplace consumers. |
| Docs | `docs/*.mdx`, `fern/docs.yml` | Published docs site | Local docs preview uses Node/npm and Fern only when editing docs. |

## Component Registration Rules

A `components.d/<slug>.yml` file must define the display `name`, public GitHub `repo`, one-line `description`, and a `skills:` list. Each skill entry maps a source repo `path` containing a `SKILL.md` to a unique top-level catalog `catalog_dir` under `skills/`.

Prefer the flat layout: one `catalog_dir` per skill. Deprecated bulk layouts are preserved only for existing components.

When removing a skill registration, remember that orphan pruning deletes top-level `skills/<dir>` entries that are no longer declared, unless the directory is listed in `catalog-exceptions.yml` or `.github/scripts/manual-components.yml`. The pruning script has a cap to avoid mass deletion on parse failures.

## Catalog Skill Artifact Contract

Every published catalog skill is expected to ship:

- `SKILL.md` with valid YAML frontmatter and a clear activation purpose.
- `skill-card.md` with owner, use case, risks, output shape, evidence, and version.
- `skill.oms.sig` at the skill root.
- Tier-3 eval data at `evals/evals.json`, `evals/*.json`, `eval/*.json`, or `benchmark/evals.json`.
- `BENCHMARK.md` summarizing evaluation results.

The sync workflow drops or reverts non-compliant skills rather than publishing unsigned, uncarded, or unevaluated content.

## Generated Output Boundaries

Do not edit these as primary source unless the task explicitly targets generated drift:

- `plugins/<name>/.claude-plugin/plugin.json`
- `plugins/<name>/.codex-plugin/plugin.json`
- `plugins/<name>/.cursor-plugin/plugin.json`
- plugin `skills/` materialized copies
- root marketplace JSON files
- root README catalog tables between marker comments
- `.github/scripts/marketplace/metadata.json`
- `skills.sh.json`
- `benchmarks.json`

Regenerate them from source inputs and review the diff.

## Local Inspection

Use the bundled `scripts/inspect_catalog.py` helper to count component files, skill directories, required artifacts, and generated outputs. It is read-only and works from any current working directory when passed `--repo-root`.
