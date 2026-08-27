# Testing and Docs Selection

## Check Selection Strategy

Start with the smallest checks that exercise the changed surface, then widen only when the risk justifies it.

1. Always inspect formatting/static checks for touched Python files.
2. Add help checks for CLI changes.
3. Add focused pytest modules for the touched algorithm family or utility.
4. Add docs build/serve checks for docs, README, mkdocs, algorithm catalog, or CLI snippet changes.
5. Add optional backend checks only when the needed extra, platform, and hardware are available.
6. Add benchmark/RLOps checks only for approved performance-impacting changes.

The bundled selector encodes this mapping and prints a conservative checklist:

```bash
python sub-skills/repo-maintenance/scripts/select_native_checks.py cleanrl/ppo.py docs/rl-algorithms/ppo.md --keywords cli docs
```

## Baseline Local Checks

Use these as candidates, not mandatory commands for every edit:

- `uv run pre-commit run --files <changed-files>` for changed tracked files.
- `uv run pre-commit run --all-files` before final submission when a broad formatting/spelling pass is warranted.
- `uv run pytest <focused-test-modules>` for smoke tests relevant to the touched code.
- `uv run python <script> --help` for tyro/argparse script surfaces.
- `uv run mkdocs build --strict` or `uv run mkdocs serve` when docs navigation, includes, algorithm docs, or MkDocs config changed.

If `uv` is unavailable, use the same intent with the active Python environment, but do not rewrite skill guidance to depend on a local environment path.

## Focused Test Map

These pytest modules are smoke checks from the repository's test suite. They usually run short command invocations with tiny timesteps; they do not validate full learning curves.

| Touched surface | Focused tests |
| --- | --- |
| `cleanrl/ppo.py` | `tests/test_classic_control.py` |
| `cleanrl/dqn.py`, `cleanrl/c51.py` | `tests/test_classic_control_gymnasium.py` |
| `cleanrl/dqn_jax.py`, `cleanrl/c51_jax.py` | `tests/test_classic_control_jax_gymnasium.py` |
| `cleanrl/ppo_atari.py`, `cleanrl/ppo_atari_lstm.py` | `tests/test_atari.py` |
| `cleanrl/dqn_atari.py`, `cleanrl/c51_atari.py`, `cleanrl/qdagger_dqn_atari_impalacnn.py`, `cleanrl/rainbow_atari.py`, `cleanrl/sac_atari.py` | `tests/test_atari_gymnasium.py` |
| `cleanrl/dqn_atari_jax.py`, `cleanrl/c51_atari_jax.py`, `cleanrl/qdagger_dqn_atari_jax_impalacnn.py` | `tests/test_atari_jax_gymnasium.py` |
| `cleanrl/ppo_atari_envpool.py`, `cleanrl/ppo_rnd_envpool.py`, `cleanrl/ppo_atari_envpool_xla_jax.py`, `cleanrl/ppo_atari_envpool_xla_jax_scan.py`, `cleanrl/pqn_atari_envpool.py`, `cleanrl/pqn_atari_envpool_lstm.py` | `tests/test_envpool.py`; add targeted manual smoke if the touched PQN EnvPool script has no direct test entry |
| `cleanrl/ppo_atari_multigpu.py` | `tests/test_atari_multigpu.py` |
| `cleanrl/ppo_procgen.py`, `cleanrl/ppg_procgen.py` | `tests/test_procgen.py` |
| `cleanrl/ppo_pettingzoo_ma_atari.py` | `tests/test_pettingzoo_ma_atari.py` |
| `cleanrl/ddpg_continuous_action.py`, `cleanrl/td3_continuous_action.py`, `cleanrl/sac_continuous_action.py`, `cleanrl/ppo_continuous_action.py`, `cleanrl/rpo_continuous_action.py` | `tests/test_mujoco.py` |
| JAX continuous-action variants | `tests/test_mujoco.py` plus JAX dependency availability checks |
| GAE scan/helper logic | `tests/test_jax_compute_gae.py` |
| `cleanrl_utils/tuner.py`, `tuner_example.py` | `tests/test_tuner.py` |
| `cleanrl_utils/submit_exp.py` or cloud submit helpers | `tests/test_utils.py`; avoid real cloud submission |
| `cleanrl_utils/enjoy.py` or `cleanrl/ppo_trxl/enjoy.py` | `tests/test_enjoy.py` where applicable |

## Optional Backend Boundaries

Treat these as conditional checks:

- Atari checks require Atari extras, ROM handling, and compatible ALE/Gymnasium dependencies.
- EnvPool checks are platform-sensitive and generally Linux-oriented.
- Procgen checks require the Procgen extra.
- PettingZoo multi-agent Atari checks require both PettingZoo and Atari-related dependencies.
- MuJoCo and dm_control checks require MuJoCo-related extras and may need renderer/display setup.
- JAX checks require the pinned JAX/JAXLIB stack; GPU-specific JAX installs are not a routine maintenance step.
- Multi-GPU checks use `torchrun` and can be platform/hardware-sensitive.
- Isaac Gym style work is special: it can require proprietary/manual installation and Python-version constraints; do not treat it as routine local validation.
- Cloud checks can require AWS credentials, Docker registry access, W&B keys, or Slurm; do not run without explicit approval.

## CLI Help Checks

Most algorithm scripts use tyro dataclass `Args`; a few utilities use `argparse`.

Run help checks when:

- A dataclass field, default, type, or docstring changed.
- A new CLI flag was added.
- Docs mention a CLI command that changed.
- A `parse_args()` function or argparse parser changed.

Useful patterns:

- `uv run python cleanrl/<script>.py --help`
- `uv run python -m cleanrl_utils.benchmark --help`
- `uv run python cleanrl/ppo_trxl/ppo_trxl.py --help` for TRXL work inside its subproject context when dependencies are available.

Tyro renders field names as CLI flags, so a code rename can break docs snippets even when tests still import successfully. Inspect help output for renamed flags, boolean negation forms, and type formatting.

## Docs Checks

Run docs checks when touching:

- `docs/**`, `README.md`, `mkdocs.yml`.
- Algorithm scripts whose usage/defaults/logged metrics changed.
- Benchmark tables, images, result snippets, or Markdown includes.
- Package extras or requirements described in installation docs.

Docs consistency checklist:

- Algorithm page has usage, dependency extras, logged metrics, implementation details, and experiment-results expectations when relevant.
- README and overview list new or renamed public algorithms.
- `mkdocs.yml` includes new pages under the right navigation section.
- Markdown include paths and image paths are relative to the docs tree as MkDocs expects.
- Benchmark result images/tables are updated only after the benchmark/RLOps workflow produces new data.

## Requirements and Lock Checks

When `pyproject.toml` dependency metadata changes:

- Regenerate affected `requirements/requirements*.txt` snapshots with the corresponding manual pre-commit `uv-export` hook.
- Inspect `uv.lock` changes if the lockfile is part of the maintenance task.
- Mention if generated requirements were intentionally not refreshed.
- Keep optional extra names aligned across package metadata, installation docs, tests, and selector warnings.

## Safe vs Unsafe Checks

Safe local checks:

- Formatting/lint pre-commit on changed files.
- Focused pytest modules that use tiny timesteps and local dependencies.
- Help commands.
- MkDocs build/serve when docs dependencies are installed.

Ask first or explicitly gate:

- `uv run install --all-extras` because it can install broad optional backends.
- Full `uv run pytest tests/.` when optional dependencies or runtime are uncertain.
- Benchmarks with `--track`, W&B reports, videos, Xvfb, long timesteps, multiple seeds, or cloud workers.
- AWS Batch, Docker push/build workflows, Slurm submission, or commands requiring real credentials.
