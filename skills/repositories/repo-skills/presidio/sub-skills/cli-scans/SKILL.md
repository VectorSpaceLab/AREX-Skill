---
name: cli-scans
description: "Scan files, directories, or stdin for PII with the Presidio CLI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# cli-scans

Use this sub-skill when you need the `presidio` command to scan files, directory trees, or stdin for PII findings.

## Use this for

- recursive file or directory scans
- stdin scans with `-`
- YAML configuration files and inline YAML config data
- ignore and allow lists
- score thresholds and warning suppression
- output formats for local terminals and CI
- locale-sensitive output behavior

## Route elsewhere when you need

- custom recognizers, NLP engines, or entity catalogs: `../analyze-text/SKILL.md`
- anonymizing or deanonymizing detected spans: `../anonymize-text/SKILL.md`
- service deployment, Docker, or HTTP runtime guidance: `../../references/service-and-rest-api.md`

## Start here

- `references/cli-reference.md` for command syntax, formats, and scan behavior
- `references/configuration.md` for `PresidioCLIConfig`, config precedence, and YAML fields
- `references/troubleshooting.md` for common failures and recovery steps
- `scripts/presidio_cli_smoke.sh` for a safe help check and tiny scan smoke test
- `scripts/sample_presidiocli.yaml` for a portable config template

## Operational notes

- Console entry point: `presidio`
- Config loading order: `--config-data`, `--config-file`, current `.presidiocli`, then the bundled default config
- `--threshold` overrides the loaded config for one run
- Ignore patterns use `pathspec` in `gitwildmatch` mode
- `--format auto` prefers GitHub annotations in GitHub Actions, colored output in a TTY, and standard output otherwise
- Use `github` format in CI and `parsable` format for line-oriented machine parsing

## Troubleshooting focus

If a scan fails or behaves unexpectedly, check `references/troubleshooting.md` first. It covers invalid YAML, unknown entity names, missing spaCy model issues, ignore-pattern surprises, threshold confusion, stdin versus file behavior, output-format expectations, and the current exit-code caveat.