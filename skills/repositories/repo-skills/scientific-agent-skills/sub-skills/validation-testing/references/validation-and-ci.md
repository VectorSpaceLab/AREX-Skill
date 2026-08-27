# Validation and CI

## Spec validation

For one skill:

```bash
uv run skills-ref validate skills/<name>
```

For all canonical skills, CI loops over `skills/*/` and validates each directory. The reference validator enforces the Agent Skills specification, including allowed frontmatter fields, name constraints, description/compatibility limits, and strict YAML parsing.

## Repository-specific rules

The skill-spec workflow also checks repository rules that the reference validator does not cover:

- `metadata.version` exists.
- `metadata` scalar values that YAML could coerce are quoted.
- `allowed-tools` is a space-separated string.
- `metadata.openclaw` and `metadata.hermes` remain nested mappings.
- `SKILL.md` over 500 lines is warned.

## Repo-wide structural guard

Run:

```bash
uv run --with pytest python -m pytest tests/_meta -q
```

`tests/_meta` imports no skill code. It parses skill files and scripts to enforce frontmatter conformance, link resolution, no tests under `skills/`, no committed bytecode, script parsing, no `eval`/`exec`/`os.system`, no standard-library script shadowing, no hardcoded local paths, valid shell scripts, and script-suite/manifest coverage.

## CI workflow mapping

| Workflow | Local equivalent |
|---|---|
| `.github/workflows/skill-spec-validation.yml` | `uv sync --python 3.13`; loop `uv run skills-ref validate skills/*/`; run repo metadata check. |
| `.github/workflows/skill-tests.yml` contract job | `uv run --with pytest python -m pytest tests/_meta -q`. |
| `.github/workflows/skill-tests.yml` suites job | `uv run --python 3.13 python tests/run_all.py --isolated <stdlib-only-selected-skills>`; for local focus, name the changed skill. |

Use local commands to diagnose before pushing; CI path filters may skip workflows that do not touch relevant paths.
