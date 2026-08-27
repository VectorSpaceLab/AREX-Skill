---
name: validation-testing
description: "Selects and runs Scientific Agent Skills repository validation and
  tests: skills-ref validate, repo-specific metadata checks, tests/_meta,
  per-skill pytest suites, one-skill-per-process rules, tests/run_all.py,
  --isolated environments, and tests/skill-requirements.toml entries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Validation and Testing

Use this route when a task asks how to validate, test, or diagnose CI for skill changes in this repository.

## First checks

1. Install repository tooling with Python 3.13:

   ```bash
   uv sync --python 3.13
   ```

2. Validate the changed skill's Agent Skills spec:

   ```bash
   uv run skills-ref validate skills/<name>
   ```

3. Run the repo-wide structural guard after local issues are fixed:

   ```bash
   uv run --with pytest python -m pytest tests/_meta -q
   ```

Read `references/validation-and-ci.md` for CI-equivalent checks and `references/test-runner.md` for per-skill and isolated suite behavior. Use `scripts/plan_skill_checks.py` to inspect one skill and print an ordered command plan without executing tests.

## Test-suite rules

- Tests never live under `skills/<name>/`.
- A skill that ships files under `scripts/` needs `tests/<name>/` with at least one `test_*.py` and a `[skills.<name>]` entry in `tests/skill-requirements.toml`.
- Run one skill's suite in one Python process:

  ```bash
  uv run --with pytest python -m pytest tests/<name> -q
  ```

- For isolated dependency environments, use:

  ```bash
  python tests/run_all.py --isolated <name>
  ```

- Do not collect multiple skill suites with one `pytest` process; script module names intentionally collide across skills.

## Escalation guidance

| Change type | Minimum validation |
|---|---|
| `SKILL.md` prose only | `skills-ref validate skills/<name>` and consider `tests/_meta` for links/line count. |
| Skill references/assets changed | `skills-ref validate`, `tests/_meta`, and any touched examples/manual checks. |
| Skill scripts changed or added | `skills-ref validate`, `tests/<name>`, `tests/run_all.py --isolated <name>`, and `tests/_meta`. |
| Shared test contract or runner changed | `tests/_meta` and `python tests/run_all.py`; use isolated selection for affected script-bearing skills. |
| CI workflow changed | Mirror the workflow commands locally and inspect path filters/permissions/timeouts. |

## Troubleshooting

Read `references/troubleshooting.md` when `tests/_meta` reports missing suites, `skill-requirements.toml` entries, broken local links, local paths, or unsafe script patterns.
