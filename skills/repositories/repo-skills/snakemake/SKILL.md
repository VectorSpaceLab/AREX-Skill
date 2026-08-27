---
name: snakemake
description: "Create, run, debug, deploy, and programmatically inspect Snakemake
  9.23.1 workflows, including Snakefile authoring, CLI execution,
  configuration/data validation, deployment/storage, reporting/testing, and
  Python API/plugin usage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Snakemake

Use this skill when a user asks for help with Snakemake workflows: writing or refactoring Snakefiles, constructing safe execution commands, validating configs and sample metadata, using conda/containers/storage/executors, generating diagnostics/reports/tests, or embedding Snakemake through its Python API.

## Start Here

1. Identify whether the user is changing a workflow definition, running an existing workflow, validating inputs, configuring deployment/storage, debugging/reporting, or writing Python integration code.
2. Confirm the installed Snakemake generation when commands or APIs matter: this skill targets Snakemake 9.23.1.
3. Prefer non-mutating checks first: `snakemake --cores 1 --dry-run --printshellcmds`, `snakemake --lint`, DAG/rulegraph/summary commands, or the bundled smoke scripts.
4. Do not add the legacy `--reason` flag. Snakemake 9.23.1 rejects it; dry-run output already prints job reasons.
5. Keep workflow-generated artifacts separate from DisCo artifacts; Snakemake unit-test outputs such as `.tests/unit` are user workflow files, not repo-skill review files.

## Route by Task

- **Write or refactor Snakefiles**: use `sub-skills/workflow-authoring/SKILL.md` for rules, wildcards, directives, helper functions, modules, checkpoints, includes, scripts, notebooks, wrappers, CWL hooks, and authoring-time failures.
- **Run or scale workflows from CLI**: use `sub-skills/execution-cli/SKILL.md` for dry-runs, targets, cores/jobs/local cores, profiles, resources, batches, groups, DAG/rulegraph/summary inspection, schedulers, reruns, locks, and smoke checks.
- **Configure workflows and validate data**: use `sub-skills/configuration-data/SKILL.md` for `configfile`, `--config`, `--configfile`, profiles as config sources, schemas, sample tables, PEP metadata, pathvars, envvars, YTE, and data-driven helpers.
- **Deploy software or storage**: use `sub-skills/deployment-storage/SKILL.md` for conda, Apptainer/Singularity, env modules, storage providers/prefixes, shared filesystem usage, executor/jobscript surfaces, archives, and deployment caches.
- **Debug, report, and test**: use `sub-skills/debugging-reporting/SKILL.md` for linting, DAG/rulegraph/filegraph outputs, reports, notebooks, generated unit tests, benchmarking, runtime profiles, failed logs, and diagnostic bundles.
- **Embed Snakemake in Python**: use `sub-skills/python-api-plugins/SKILL.md` for `SnakemakeApi`, `WorkflowApi`, `DAGApi`, settings dataclasses, plugin settings, and CLI-to-API translation.

## Install Baseline

For a new public environment, start with `pip install snakemake` or the user's package-manager equivalent, then verify both the console script and Python module before running workflow commands. Optional integrations such as PEP metadata, reports, storage plugins, executor plugins, conda, and containers can require extras, separate plugins, external binaries, credentials, or site profiles.

## Shared References

- Read `references/installation-and-capabilities.md` before making environment, optional dependency, CLI availability, or plugin capability claims.
- Read `references/troubleshooting.md` for cross-cutting install/import, optional dependency, CLI/API, and version-mismatch failures.
- Read `references/repo-provenance.md` when deciding whether this skill is stale relative to a checked-out Snakemake repository.
- Run `scripts/check_snakemake_install.py --help` to inspect a candidate Snakemake executable or Python module without depending on any original repository examples.

## Safety Defaults

- Use dry-runs, explicit targets, low `--cores`, and temporary workdirs before modifying outputs.
- Avoid executing workflows that download data, create conda environments, start containers, access remote storage, require credentials, or run long benchmarks unless the user explicitly approves.
- Treat cloud/storage/executor integrations as plugin- and credential-dependent; verify the plugin and credential surface before promising execution.
- Route shell/script/notebook failures to the owning workflow sub-skill first, then use debugging/reporting for lint, graphs, reports, or generated tests.

## Minimal Checks

```bash
python -m snakemake --help
snakemake --help
snakemake --cores 1 --dry-run --printshellcmds
python scripts/check_snakemake_install.py --command snakemake
```

For Python API checks, use `sub-skills/python-api-plugins/scripts/api_dryrun_example.py` in an environment where `snakemake` is importable.
