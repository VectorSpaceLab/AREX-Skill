---
name: configuration-data
description: "Route Snakemake configuration, sample metadata, schema validation,
  pathvars, envvars, YTE, PEP, and data-driven helper tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Configuration Data

Use this sub-skill when a Snakemake task involves `configfile`, CLI config overrides, profile-provided config, JSON/YAML config loading, `config` mutation, sample tables, `snakemake.utils.validate`, PEP metadata, `envvars`, `pathvars`, YTE-templated YAML, or data-driven helpers such as `lookup`, `branch`, `evaluate`, `collect`, `subpath`, and `exists`.

## Route by Need

- Config sources, precedence, CLI quoting, profiles, YTE, `envvars`, `pathvars`, PEP, and helper patterns: read [configuration-reference.md](references/configuration-reference.md).
- JSON Schema validation for dictionaries, pandas tables, Polars tables, defaults, and relative `$ref`: read [data-validation.md](references/data-validation.md).
- Common failures and diagnostic signals for invalid config, schema errors, optional dependencies, pathvar cycles, and helper misuse: read [troubleshooting.md](references/troubleshooting.md).
- Standalone preflight for config/sample schemas before a full run: use [validate_config_schema.py](scripts/validate_config_schema.py).

## Fast Workflow

1. Inventory every config source: Snakefile `configfile`, included files, CLI `--configfile`, CLI `--config`, profiles, workflow profile, and any top-level Python `update_config(config, ...)`.
2. Resolve precedence before editing rules: later config files recursively extend earlier files, `--config` wins over config files, and `--replace-workflow-config` discards workflow-defined config keys not provided by CLI config files.
3. Validate early, before rule definitions consume values: `from snakemake.utils import validate`; then `validate(config, "schemas/config.schema.yaml")` and validate any sample tables.
4. Keep secrets out of config files: assert names with `envvars:` and pass required values explicitly through `params` rather than assuming shell commands receive them.
5. Run `snakemake --cores 1 --dry-run --printshellcmds` after config/pathvar/schema changes. Do not add `--reason`; it is not a valid Snakemake 9.23.1 flag.

## Boundaries

- Route rule graph syntax, wildcard design, module structure, and rule directives to `../workflow-authoring/SKILL.md`; this sub-skill only owns the data/config semantics feeding them.
- Route command execution strategy, profile selection, cores, dry-runs, and executor flags to `../execution-cli/SKILL.md`; this sub-skill covers only config-related CLI arguments.
- Route storage-provider setup to deployment/storage guidance; this sub-skill only notes that `exists()` respects Snakemake storage settings.
- Route report rendering and metadata display to debugging/reporting guidance unless the issue is config data feeding report metadata.
