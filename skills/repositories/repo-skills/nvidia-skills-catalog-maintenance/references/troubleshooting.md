# Troubleshooting Catalog Maintenance

## Purpose

Use this when a catalog maintenance check fails or a sync/release workflow reports dropped skills, stale generated files, invalid metadata, plugin drift, or signature mismatch.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `components.d/*.yml` parse failure | Invalid YAML or non-mapping root | Fix YAML first. Orphan pruning is intentionally skipped on component parse failures. |
| Skill disappears from sync PR | Missing `skill.oms.sig`, `skill-card.md`, eval JSON, or signature drift/mismatch | Check the dropped-skills reason. If source content changed after signing, rerun source signing/NVSkills CI and resync. |
| README table drift | Component registration changed without regeneration | Run the README regeneration script or let the sync workflow regenerate; commit the expected diff when doing local maintenance. |
| `metadata.json` or `skills.sh.json` check fails | New/changed skill requires metadata enrichment, schema drift, or stale generated output | In PR mode, regenerate with a configured enrichment run or adjust checked-in metadata. Never invent controlled taxonomy values outside schema. |
| `benchmarks.json` check fails | Per-skill `BENCHMARK.md` changed or has unsupported layout | Regenerate `benchmarks.json`; if parsing fails, inspect benchmark headings/tables before editing aggregator logic. |
| Plugin drift check fails | Generated plugin tree or marketplace JSON differs from `plugins.d` and `skills/` | Run plugin build from source YAML. Do not hand-edit generated plugin JSON. |
| Plugin version check fails | Plugin payload changed without SemVer bump | Run version helper in plan mode, then apply a patch/minor bump or make an intentional version edit. |
| Content integrity failure reports hash mismatch | Files no longer match the `skill.oms.sig` resource manifest | Re-sign the exact skill directory after final content changes; do not modify files after signing. |
| `model_signing verify` fails for a consumer | Signature missing, stale, wrong certificate path, or unsigned local edits | Re-download or resync a signed skill. Use strict verification unless a policy explicitly allows unsigned additions. |
| Local generator asks for AI config | `--no-ai` was not used and enrichment is needed | For deterministic local checks use `--check --no-ai`. For enrichment, run the configured CI/dispatch workflow with repository secrets. |
| `yq` missing locally | Some shell scripts require `yq` | Use Python helpers for read-only inspection, install `yq`, or run the check in CI. Do not rewrite scripts to silently skip schema parsing. |
| User asks to install an NVIDIA skill | Wrong route for this skill | Switch to `nvidia-skill-finder`; do not use catalog maintenance workflows for consumer discovery. |

## Recovery Order

1. Classify the failure: source YAML/schema, generated-file drift, missing artifacts, stale signature, CI secret/config, or external source repo state.
2. Preserve unrelated dirty files and current generated evidence.
3. Fix the smallest source-of-truth input.
4. Regenerate/check the affected output only.
5. Re-run the relevant profile and summarize remaining CI-only gates.
