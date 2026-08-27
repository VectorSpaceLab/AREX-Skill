# Repository Provenance

Schema: `disco.repo-provenance.v1`

This skill was generated from Snakemake repository evidence and installed-package inspection.

| Field | Value |
| --- | --- |
| Source project | Snakemake |
| Generated skill id | `snakemake` |
| Package distribution | `snakemake` |
| Package version | `9.23.1` |
| Import module | `snakemake` |
| CLI entry point | `snakemake` |
| Source commit | `3d933e63e8b51a520d65aac2d3f3b2c19b1b36fd` |
| Source branch | `main` |
| Exact tag | `v9.23.1` |
| Remote URL | `https://github.com/snakemake/snakemake` |
| Working tree state | Dirty: untracked `skills/` generated artifacts were present during skill creation. |

## Evidence Paths

The generated skill distills these repository-relative evidence paths:

- `pyproject.toml`
- `setup.py`
- `README.md`
- `src/snakemake/`
- `docs/getting_started/`
- `docs/tutorial/`
- `docs/snakefiles/`
- `docs/executing/`
- `apidocs/`
- `examples/hello-world/`
- `examples/c/`
- `examples/latex/`
- representative tests under `tests/`, including API, CLI args, schema/config, modules, checkpoints, deployment, storage, reporting, linting, and unit-test generation cases
- existing repo-local guidance under `skills/snakemake/`, used as evidence only

## Verification Baseline

Installed-package inspection verified these public facts:

- `snakemake` imports successfully.
- Distribution metadata reports version `9.23.1`.
- `snakemake --help` and `python -m snakemake --help` run.
- A tiny local workflow dry-runs with `snakemake --cores 1 --dry-run --printshellcmds`.
- Snakemake 9.23.1 does not accept the legacy `--reason` flag; normal dry-run output already includes job reasons.
- Key Python API objects and settings dataclasses exist in `snakemake.api` and `snakemake.settings.types`.

## Refresh Guidance

Refresh this skill when Snakemake's package version, CLI help, Python API signatures, deployment/storage plugin behavior, or workflow-language docs change. Pay special attention to CLI flags, settings dataclass constructor signatures, executor/storage plugin interfaces, and optional dependency behavior.
