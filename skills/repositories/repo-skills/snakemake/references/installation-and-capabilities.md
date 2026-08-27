# Installation and Capability Notes

This reference summarizes Snakemake 9.23.1 installation checks and capability boundaries for agents using this skill.

## Basic Installation Checks

Use these before diagnosing workflow logic:

```bash
python -m snakemake --help
snakemake --help
python - <<'PY'
import importlib.metadata as md
import snakemake
print(md.version("snakemake"))
PY
```

If the executable and Python module disagree, resolve the environment first. A common mismatch is running `snakemake` from one environment while `python` imports another or cannot import Snakemake at all.

## Core Capabilities in a Standard Install

A standard Snakemake 9.23.1 install supports:

- authoring and parsing Snakefiles;
- local, dry-run, and touch executor modes from the default CLI help;
- dry-runs, DAG/rulegraph/filegraph/summary inspection, linting, and report commands;
- workflow configuration from Snakefiles, config files, CLI config values, profiles, envvars, pathvars, and YTE-templated YAML;
- Python API usage through `snakemake.api` and settings dataclasses in `snakemake.settings.types`;
- optional PEP metadata and report-related imports when the corresponding extras are installed.

## Optional and Environment-Dependent Capabilities

Do not assume these are usable until verified:

- **Conda deployment** needs a usable conda-compatible frontend and may create environments.
- **Apptainer/Singularity deployment** needs the container runtime and image access.
- **Env modules** need site-specific module tooling.
- **Remote storage providers** need provider plugins, credentials, and often network access.
- **Cluster/cloud executors** need executor plugins, profiles, credentials, shared filesystem decisions, and scheduler-specific policies.
- **Reports and notebooks** may need optional rendering, notebook, or language dependencies beyond core execution.
- **CWL export and wrappers** may require ecosystem tools, wrappers, or network access depending on workflow content.

## Version-Specific Notes

- Snakemake 9.23.1 rejects `--reason`; remove it from copied commands and profiles.
- Dry-run job output already includes reasons such as missing outputs or updated inputs.
- Default CLI help exposes `--executor {local,dryrun,touch}`; other executors are plugin-dependent.
- Settings dataclasses use immutable mapping and frozenset defaults in several places. Construct new dicts/sets instead of mutating defaults.

## Capability-to-Sub-Skill Map

| Need | Route |
| --- | --- |
| Rule syntax, wildcards, checkpoints, modules | `sub-skills/workflow-authoring/` |
| Safe execution commands, profiles, resources | `sub-skills/execution-cli/` |
| Config/schema/sample table/PEP/pathvars/envvars | `sub-skills/configuration-data/` |
| Conda, containers, storage, archives, executor deployment | `sub-skills/deployment-storage/` |
| Lint, DAG graphs, reports, notebooks, unit tests, benchmarks | `sub-skills/debugging-reporting/` |
| Python API, settings objects, plugin settings | `sub-skills/python-api-plugins/` |
