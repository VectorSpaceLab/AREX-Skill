---
name: nvidia-skills-catalog-maintenance
description: "Maintain the NVIDIA skills catalog repository: components.d
  registrations, generated README tables, plugin bundles, marketplace metadata,
  benchmark aggregation, signatures, and release/integrity checks. Use only for
  catalog maintainer workflows, not for discovering or installing NVIDIA
  skills."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# NVIDIA Skills Catalog Maintenance

## Purpose

Use this skill when maintaining a checkout of the NVIDIA Agent Skills catalog: onboarding or removing component registrations, checking catalog skill artifacts, regenerating README and marketplace metadata, rebuilding plugin bundles, triaging signature drift, and preparing release or sync PRs.

This is a maintainer workflow skill. It is not the catalog discovery router. For user requests such as "which NVIDIA skill should I use", "install a skill", or "find a skill for CUDA/Jetson/RAG", use `nvidia-skill-finder` instead.

## When To Use

Use this skill for tasks that mention one or more of these catalog-maintenance surfaces:

- `components.d/*.yml`, `catalog-exceptions.yml`, `.github/scripts/manual-components.yml`, or sync onboarding.
- Root `README.md` skill/help tables, `skills/README.md`, `docs/*.mdx`, or Fern docs publishing.
- `plugins.d/*.yml`, generated `plugins/<name>/`, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `.cursor-plugin/marketplace.json`, or plugin version bumps.
- `.github/scripts/marketplace/metadata.json`, root `skills.sh.json`, `benchmarks.json`, `BENCHMARK.md`, or metadata generation failures.
- `skill.oms.sig`, `skill-card.md`, eval datasets, signature drift, content integrity, `/nvskills-ci`, DCO, author, or release gates.

## Do Not Use

Do not use this skill to recommend, install, or operate a product skill from the NVIDIA catalog. Use `nvidia-skill-finder` for discovery and the matched product skill for product-specific work.

Do not hand-edit generated product skill mirrors under `skills/<catalog_dir>/` unless the task is an intentional direct catalog exception or generated DisCo output. Product skills are normally maintained in their source repos and mirrored by automation.

## Fast Route Map

| Maintainer task | Read first | Useful bundled helper |
| --- | --- | --- |
| Understand what is hand-edited vs generated | `references/catalog-layout.md` | `scripts/inspect_catalog.py --summary` |
| Add, remove, or repair a component registration | `references/maintainer-workflows.md` | `scripts/inspect_catalog.py --json` |
| Rebuild plugin manifests or marketplace entries | `references/plugin-packaging.md` | `scripts/run_catalog_checks.py --profile plugins --plan` |
| Regenerate metadata, `skills.sh.json`, or `benchmarks.json` | `references/metadata-release-integrity.md` | `scripts/run_catalog_checks.py --profile metadata --plan` |
| Triage `skill.oms.sig`, missing artifact, or integrity failure | `references/metadata-release-integrity.md` and `references/troubleshooting.md` | `scripts/run_catalog_checks.py --profile integrity --plan` |
| Prepare a PR or release review | `references/maintainer-workflows.md` and `references/metadata-release-integrity.md` | `scripts/run_catalog_checks.py --profile pre-pr --plan` |

## Core Operating Rules

1. Start from the source-of-truth map, not from generated output. Edit `components.d/` for synced catalog membership and `plugins.d/` for catalog-driven plugin packaging; rebuild generated files afterward.
2. Treat `skill.oms.sig`, `skill-card.md`, eval JSON, and `BENCHMARK.md` as release gates. Missing or stale artifacts are not cosmetic problems.
3. Prefer check-only commands before mutating files. Use `scripts/run_catalog_checks.py --plan` to see the exact repo commands, then add `--execute` only after confirming the working tree and intended profile.
4. Preserve unrelated dirty files. In this production run, `skills/skills.log` was already dirty and is not part of generated runtime content.
5. Never paste credentials, API keys, PATs, or inference tokens into commands or reports. Sync and AI-enrichment workflows consume repository secrets in CI; local agents should not invent them.
6. When a check fails, identify whether the failure is source YAML/schema drift, generated-file drift, missing publication artifacts, stale signature content, or external CI/source-repo state before editing.

## Bundled References

- `references/catalog-layout.md` explains the repository layout, hand-edited inputs, generated outputs, and catalog skill artifact shape.
- `references/maintainer-workflows.md` gives step-by-step onboarding, removal, README, docs, and PR maintenance workflows.
- `references/plugin-packaging.md` covers plugin source YAML, generated plugin trees, marketplace manifests, copy vs symlink materialization, and version policy.
- `references/metadata-release-integrity.md` covers metadata generation, benchmark aggregation, signature/content-integrity gates, skill cards, evaluation, and release checks.
- `references/troubleshooting.md` maps common catalog-maintenance symptoms to causes and recovery steps.
- `references/repo-provenance.md` records the source checkout baseline used to create this skill.

## Bundled Scripts

- `scripts/inspect_catalog.py` performs read-only catalog shape and artifact checks against any checkout of this repository.
- `scripts/run_catalog_checks.py` prints or runs the safe local check command sets for metadata, plugins, integrity, and pre-PR review.

## Common Signals

- If the task names `components.d`, `catalog-exceptions.yml`, or the sync workflow, start with `references/catalog-layout.md`.
- If the task mentions `plugins.d`, generated `plugins/<name>/`, or marketplace JSON, start with `references/plugin-packaging.md`.
- If the task mentions metadata, `skills.sh.json`, `benchmarks.json`, signing, or release gates, start with `references/metadata-release-integrity.md`.
- If the task mentions `README.md` table regeneration or PR maintenance, start with `references/maintainer-workflows.md`.
- If the task is a failure report, start with `references/troubleshooting.md` and identify whether the issue is source drift, generated drift, or missing publication artifacts.

## Typical Start

```bash
python <this-skill>/scripts/inspect_catalog.py --repo-root /path/to/nvidia-skills --summary
python <this-skill>/scripts/run_catalog_checks.py --repo-root /path/to/nvidia-skills --profile pre-pr --plan
```

If the user asks you to change catalog files, inspect first, make the smallest source-of-truth edit, run the relevant check profile, then summarize changed files and any unresolved CI-only gates.
