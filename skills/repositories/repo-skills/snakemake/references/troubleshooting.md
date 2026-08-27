# Cross-Cutting Troubleshooting

Use this reference for failures that span multiple Snakemake workflows. For workflow-specific errors, continue into the nearest sub-skill troubleshooting reference.

## `snakemake` Command Not Found

Symptoms:

- `snakemake: command not found`.
- `python -m snakemake --help` works, but `snakemake --help` does not.

Actions:

1. Confirm the intended Python environment.
2. Run `python -m snakemake --help` as a fallback.
3. Reinstall or expose the console script in the environment that should own workflow execution.
4. Use `scripts/check_snakemake_install.py --python python --command snakemake` to compare executable and import behavior.

## Python Import Mismatch

Symptoms:

- CLI works but Python API code raises `ModuleNotFoundError: No module named 'snakemake'`.
- `python -m snakemake --help` and `snakemake --help` report different versions.

Actions:

1. Check both `python -m snakemake --help` and `snakemake --version` or `snakemake --help`.
2. Keep the CLI executable and Python API code in the same environment.
3. Avoid mixing system Python, conda Python, and workflow-created conda environments when embedding the API.

## Legacy `--reason` Commands

Symptoms:

- Argument parser error for `--reason`.
- Old command templates include `--dry-run --reason --printshellcmds`.
- Profiles contain `reason: true`.

Actions:

1. Remove `--reason` from commands and `reason: true` from profiles.
2. Keep `--dry-run --printshellcmds` for safe previews.
3. Read the normal dry-run job blocks; Snakemake 9.23.1 prints reasons without a flag.

## Optional Dependency or Plugin Missing

Symptoms:

- Errors mention missing storage provider, executor plugin, report renderer, PEP dependency, notebook tooling, conda frontend, or Apptainer/Singularity.
- A workflow parses locally but fails when storage, containers, profiles, or reports are enabled.

Actions:

1. Identify whether the missing piece is a Python extra, Snakemake interface plugin, external binary, credential, or site-specific profile.
2. Re-run a core dry-run without that optional surface to separate workflow logic from integration setup.
3. Route storage/deployment failures to `sub-skills/deployment-storage/SKILL.md`.
4. Route report/notebook/lint/unit-test failures to `sub-skills/debugging-reporting/SKILL.md`.
5. Route Python API plugin settings failures to `sub-skills/python-api-plugins/SKILL.md`.

## Workflow Mutates Data Unexpectedly

Symptoms:

- A command starts executing jobs when the user expected inspection only.
- Outputs are overwritten, temp files removed, or cache/storage changes occur.

Actions:

1. Stop and rebuild the command from `sub-skills/execution-cli/SKILL.md` with `--dry-run`, explicit targets, and low `--cores`.
2. Avoid `--force`, `--forceall`, `--delete-all-output`, `--delete-temp-output`, cleanup flags, or real executor/storage flags until the user accepts the effect.
3. For conda/container/storage commands, inspect deployment and storage side effects before execution.

## Stale Skill Risk

Refresh this skill if any of these are true:

- Snakemake version differs materially from 9.23.1.
- `snakemake --help` no longer matches the documented flags.
- `snakemake.api` signatures or settings dataclasses changed.
- Executor/storage/report plugin interfaces changed.
- Docs/tests/examples reveal new primary workflows not routed by the root skill.
