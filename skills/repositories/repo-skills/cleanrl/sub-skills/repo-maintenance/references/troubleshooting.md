# Maintenance Troubleshooting

## Python Version Mismatch

Symptoms:

- Install resolver rejects the active Python.
- JAX, MuJoCo, EnvPool, or older Gym dependencies fail to resolve.
- Isaac Gym or TRXL setup complains about unsupported Python.

Response:

- Check the package metadata target first: this CleanRL snapshot declares Python `>=3.8,<3.11`.
- Do not silently upgrade dependency pins to fit a newer Python unless the task is explicitly a compatibility migration.
- For backend-specific failures, distinguish root CleanRL compatibility from that backend's supported Python range.
- If a user asks for a broad Python-version migration, plan dependency, CI, docs, and smoke-test updates together.

## Optional Extra Tests Skipped or Failing

Symptoms:

- `ModuleNotFoundError` for `ale_py`, `envpool`, `procgen`, `mujoco`, `dm_control`, `pettingzoo`, `jax`, `flax`, `optax`, or `optuna`.
- Platform errors for EnvPool, multi-GPU, Atari ROMs, MuJoCo rendering, or PettingZoo Atari.
- Tests pass locally for classic control but fail for a backend-specific module.

Response:

- Mark the check as optional-backend-gated rather than unrelated.
- Verify the matching optional extra in `pyproject.toml` and requirement snapshot before installing broad extras.
- Prefer focused installation of the needed extra over `all-extras` unless the user explicitly wants the full suite.
- For smoke tests, keep timesteps tiny; these tests are crash checks, not learning validation.
- Record skipped optional checks in the handoff with the missing dependency or platform reason.

## Tyro Help or CLI Warnings

Symptoms:

- Help output changed after editing an `Args` dataclass.
- Docs use a flag name that tyro no longer emits.
- Boolean flags or list flags behave differently than expected.
- Runtime warning text appears during help or short smoke tests.

Response:

- Run the script's `--help` command after changing dataclass fields, defaults, annotations, or docstrings.
- Check docs snippets for renamed flags and tyro's hyphenated flag names.
- Keep `Args` field comments precise; tyro uses them as help text.
- If warnings are expected and harmless, document them in the relevant troubleshooting or docs section; if they hide a real behavior change, add a focused smoke check.

## Docs Mismatch After Script Flag Changes

Symptoms:

- Algorithm docs still mention old defaults or flags.
- README/overview tables list a renamed script incorrectly.
- MkDocs build fails because a new page is missing from nav or a Markdown include path is stale.

Response:

- Compare script help output with usage snippets in the matching algorithm page.
- Update logged-metrics explanations when metric keys or logging conditions changed.
- Update implementation details when algorithm behavior changed, not only usage commands.
- Add new algorithm pages to `mkdocs.yml` and the algorithm overview when public-facing.
- Run a docs build/serve check when docs dependencies are installed.

## Benchmark Regression Process

Symptoms:

- A short smoke test passes but the edit changes algorithm behavior.
- Return curves or runtime look different after a change.
- A contributor asks whether a behavior change is safe to merge.

Response:

- State clearly that smoke tests only prove the script starts and runs briefly.
- Use the RLOps process for performance-impacting changes: benchmark new runs, tag them, compare against baseline runs, then update docs with resulting tables/plots/report links.
- Do not run W&B-tracked or long benchmark jobs without approval, credentials, and hardware/runtime confirmation.
- For new algorithms, compare against reputable baselines or paper/reference results rather than only previous CleanRL tags.
- Keep generated benchmark artifacts out of runtime skill content; maintenance notes can describe the process, but result artifacts belong in project docs or review artifacts.

## Generated Requirements Drift

Symptoms:

- `pyproject.toml` changes but `requirements/requirements*.txt` does not.
- Requirement snapshots change unexpectedly after a resolver update.
- `requirements-memory_gym.txt` is stale relative to TRXL dependencies.

Response:

- Identify which optional extra changed and run only the matching manual `uv-export` hook.
- Inspect requirements diffs for accidental broad upgrades.
- For root extras, use the root manual hooks. For Memory Gym/TRXL, use the TRXL subproject export process.
- If a requirements refresh is impossible in the current environment, leave an explicit gap and do not pretend snapshots are current.

## Cloud Tests and External Services Are Unsafe by Default

Symptoms:

- A test or helper references AWS Batch, Docker tags, Slurm, W&B keys, or benchmark workers.
- A command could create jobs, incur cost, upload data, or require credentials.

Response:

- Do not run cloud submissions, Docker pushes, Slurm `sbatch`, or W&B-tracked benchmarks unless the user explicitly authorizes that action.
- Prefer help/dry-run behavior or tests that use fake credentials and no build/submission path.
- Redact any real secrets from docs, tests, and handoffs.
- If cloud behavior changed, propose a review checklist and ask for a safe execution environment.

## Pre-commit or Formatter Failures

Symptoms:

- Black reformats long command strings or dataclass comments unexpectedly.
- isort moves W&B or backend imports in a way that changes optional import timing.
- codespell flags domain-specific RL terms.

Response:

- Keep imports compatible with optional dependencies; avoid moving heavyweight optional imports to module import time when scripts intentionally import them after flags are parsed.
- Respect the repository's Black line length and isort profile.
- Use project-specific spelling exceptions only when the term is intentional.
- If pre-commit changes generated requirements, verify whether a manual export hook was triggered intentionally.

## Single-file Style Regressions

Symptoms:

- A refactor moves algorithm-specific logic into shared utilities.
- A new algorithm depends on another algorithm script for core logic.
- A future reader must jump across multiple modules to understand a variant.

Response:

- Re-inline algorithm-specific details into the variant script unless the existing utility is already the accepted owner.
- Keep helper functions small and local when they explain a specific variant.
- If shared utilities are necessary, document why duplication would be unsafe or inconsistent with existing repository structure.
- Review docs/tests after re-inlining because CLI flags, imports, and smoke commands may change.
