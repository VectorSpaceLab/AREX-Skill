# Plugin Packaging Reference

## Purpose

Use this when a task mentions `plugins.d`, generated plugin folders, Claude/Codex/Cursor marketplace JSON, plugin curation, or plugin version checks.

## Source And Outputs

`plugins.d/<name>.yml` is the source of truth for catalog-driven plugins. `_defaults.yml` provides shared fields such as author, repository, license, brand color, capabilities, and default `skill_files` behavior. Files beginning with `_` are includes, not plugins.

The build script regenerates:

- `plugins/<name>/.claude-plugin/plugin.json`
- `plugins/<name>/.codex-plugin/plugin.json`
- `plugins/<name>/.cursor-plugin/plugin.json`
- `plugins/<name>/skills/<skill>/`
- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`
- `.cursor-plugin/marketplace.json`

Treat those as generated outputs. Change the YAML source, rebuild, and review the diff.

## Copy Vs Symlink

`skill_files: copy` materializes real files in the plugin. This is the default and is required for Codex local marketplace install behavior.

`skill_files: symlink` creates relative links back to the canonical `skills/` catalog. It can be useful for Claude-only or local workflows but is not compatible with Codex local install. Do not switch modes without understanding the target marketplace.

## NVIDIA Skills Plugin Shape

The `nvidia-skills` plugin is discovery-first. It intentionally bundles only `nvidia-skill-finder`, which routes users to the live catalog rather than loading hundreds of product skills into context.

Do not add broad product skill lists to the plugin just because they exist in the catalog. That would increase context cost and couple plugin releases to unrelated skill updates.

## Rebuild And Check

Use the bundled helper to print the relevant command set:

```bash
python <this-skill>/scripts/run_catalog_checks.py --repo-root <repo> --profile plugins --plan
```

Typical commands are:

```bash
.github/scripts/build-plugins.sh --check
.github/scripts/version-plugins.sh --check
```

To intentionally regenerate plugin outputs, run the build script without `--check`. To apply automatic version bumps, run the version script with `--apply` after reviewing the planned change.

## Version Policy

Plugin versions are SemVer strings in plugin YAML. The versioning script compares current plugin payloads with a base ref:

- no payload change -> keep version;
- content-only change -> patch bump;
- structural change -> minor bump;
- major bumps remain builder-owned.

If a maintainer manually changed a version, the script validates mechanical safety but does not decide whether the magnitude is semantically ideal. Reviewers should inspect the payload diff.

## Troubleshooting Plugin Drift

If the plugin drift check fails, rebuild from `plugins.d` and commit the regenerated tree and marketplace JSON. If the version check fails, run the version helper in plan mode first; then apply a bump or intentionally edit the YAML version. Do not patch generated plugin JSON directly to satisfy a drift check.
