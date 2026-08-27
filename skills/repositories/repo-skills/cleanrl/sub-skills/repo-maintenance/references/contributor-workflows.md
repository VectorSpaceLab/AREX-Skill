# Contributor Workflows

## CleanRL Maintenance Principles

- CleanRL favors high-quality single-file algorithm implementations. Keep an algorithm variant's implementation details local to its script unless an existing utility already owns that concern.
- Duplication across algorithm scripts is intentional when it makes each variant easier to read, audit, and copy for research. Avoid broad helper extraction, inheritance, or registries that hide algorithm logic.
- Prefer small, explicit edits in the touched script and its directly related docs/tests over repository-wide rewrites.
- Treat generated media, W&B reports, benchmark tables, and requirements snapshots as maintained surfaces: update them only through the appropriate workflow and state when they were not regenerated.

## Change Classification

### Documentation-only

Examples: correcting docs prose, fixing README links, updating mkdocs navigation, adding implementation notes without changing code behavior.

Expected maintenance actions:

- Preview docs when practical with the docs extra installed.
- Keep algorithm page anchors and names aligned with script filenames.
- If adding a new algorithm page, add it to the docs navigation and the overview/README tables.

### Non-performance code

Examples: formatting, typo fixes, safer logging text, help text, dead-code removal, a local utility that does not change algorithm semantics.

Expected maintenance actions:

- Run focused tests for the touched script or utility.
- Run help output checks when dataclass `Args`, `argparse`, defaults, or flag docs changed.
- Run pre-commit before final submission when feasible.

### Performance-impacting code

Examples: changes to update equations, loss construction, action scaling, reward normalization, wrappers, termination/truncation, seeding, replay sampling, hyperparameters, optimizer settings, rollout length, environment vectorization, or benchmark command defaults.

Expected maintenance actions:

- Run the focused smoke tests, but treat them only as crash checks.
- Plan a benchmark and regression comparison using CleanRL's RLOps process before claiming no regression.
- Update the algorithm docs after benchmark results are available: implementation details, logged metrics, result tables, plots, and report links where applicable.
- Note benchmark access needs such as W&B entity/project permissions, Xvfb for video, GPU/TPU needs, or MuJoCo/Atari/Procgen/EnvPool extras.

### Packaging/dependency

Examples: `pyproject.toml`, optional extras, dependency pins, `uv.lock`, requirements files, pre-commit hooks.

Expected maintenance actions:

- Keep `requires-python` compatible with dependency pins. This CleanRL snapshot targets Python `>=3.8,<3.11`.
- Update optional extras in `pyproject.toml` before regenerating matching requirement snapshots.
- Regenerate requirement snapshots with the manual `uv-export` hooks when dependency metadata changes.
- Remember that `requirements-memory_gym.txt` is maintained through the `cleanrl/ppo_trxl` project rather than the root manual export hook.

### Cloud/benchmark

Examples: AWS Batch submission helpers, Docker helpers, W&B metadata, Slurm template docs, benchmark utility commands.

Expected maintenance actions:

- Do not run cloud submissions, W&B-tracked experiments, or Slurm jobs as routine local validation.
- Prefer dry-run/help checks and unit-level tests unless the user explicitly asks for cloud or benchmark execution.
- Check that commands do not expose real credentials in docs or tests.

## Editing Algorithm Scripts

- Keep the `Args` dataclass or existing `argparse` structure close to the script top.
- Keep defaults, comments, and docstrings synchronized: tyro derives CLI help from the dataclass fields and docstrings.
- If adding a CLI flag, add a small smoke command or adapt the relevant focused test so the flag is exercised.
- If changing logged metrics, update the relevant algorithm docs section that explains TensorBoard/W&B metrics.
- If changing environment wrappers, truncation/termination handling, or capture-video behavior, check both script smoke tests and docs usage examples.
- If changing a JAX variant, check related JAX smoke tests and any pure helper tests such as GAE scans.
- If changing an Atari, EnvPool, Procgen, PettingZoo, MuJoCo, dm_control, Isaac Gym, multi-GPU, or memory-gym variant, treat dependency and platform availability as optional/back-end-specific.

## Docs and Navigation Upkeep

CleanRL docs are built with MkDocs Material. The docs navigation is declared in `mkdocs.yml` and algorithm pages live under `docs/rl-algorithms/`.

When adding or renaming an algorithm script:

- Add or update its algorithm page section.
- Update `docs/rl-algorithms/overview.md` and the README algorithm table if the public algorithm catalog changes.
- Add the page to `mkdocs.yml` when a new top-level algorithm page is introduced.
- Include usage, dependency extras, logged metrics, implementation details, and experiment-results expectations.
- Ensure code snippets use the same CLI flags as the script's actual tyro/argparse interface.

## Pre-commit and Requirements Upkeep

Root pre-commit uses:

- `pyupgrade` with a Python-compatibility argument.
- `isort` with Black profile and W&B handling.
- `black` with line length `127` and W&B exclusion.
- `codespell` with project-specific ignored words and skipped generated/static docs assets.
- Manual `uv-export` hooks for root requirement snapshots.

When dependency metadata changes, select the narrowest matching export hook:

- Core dependencies: `uv run pre-commit run "uv-export requirements.txt" --hook-stage manual`.
- Optional extras: run the corresponding manual hook for `atari`, `mujoco`, `dm_control`, `procgen`, `envpool`, `pettingzoo`, `jax`, `optuna`, `docs`, or `cloud`.
- Multiple extras: run each affected export hook and inspect the resulting requirements diff.
- Memory Gym/TRXL: update from inside the TRXL subproject using its own export process, not the root hook.

## RLOps Process for Behavior Changes

For performance-impacting edits, follow this sequence:

1. Run the smallest safe smoke tests for the touched scripts.
2. Benchmark through `cleanrl_utils.benchmark` or the relevant benchmark command with appropriate extras and seeds.
3. Compare new tagged runs against the established baseline with `openrlbenchmark.rlops`.
4. Update docs result tables, plots, and report links only after benchmark data is available.
5. Record skipped or deferred benchmark steps plainly; do not imply smoke tests prove learning performance.

## Cross-linking to Other CleanRL Sub-skills

- For how to run an algorithm as a user, defer to the training/evaluation sub-skill rather than duplicating runbooks here.
- For benchmark interpretation or result recovery, defer to the relevant experiment/RLOps sub-skill if present.
- Use this sub-skill when the task is about changing repository content, deciding checks, or keeping docs/tests/metadata coherent.
