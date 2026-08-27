# DreamerV3 Cross-Cutting Troubleshooting

Use this reference for failures that happen before a task clearly belongs to one
sub-skill. After identifying the failing layer, switch to the linked sub-skill
for detailed commands and checks.

## First diagnostic sequence

1. Verify the package imports and the chosen JAX backend:

   ```bash
   python scripts/check_dreamerv3_install.py --backend cpu
   python scripts/check_dreamerv3_install.py --backend auto --json
   ```

2. If import/backend checks pass, run the smallest CLI dry run before training:

   ```bash
   python sub-skills/train-configure/scripts/smoke_train_debug.py --dry-run-config
   ```

3. If the task uses an optional environment suite, check optional modules:

   ```bash
   python sub-skills/results-ops/scripts/check_optional_env_imports.py --task dmc_walker_walk
   ```

4. If the failure involves a custom env, replay, driver, or stream contract:

   ```bash
   python sub-skills/embodied-dataflow/scripts/check_embodied_contracts.py --all
   ```

5. If the failure involves model dimensions, dtype, JAX platform, loss scales,
   or checkpoint compatibility:

   ```bash
   python sub-skills/jax-models/scripts/inspect_model_config.py defaults debug size1m
   ```

## Import or package metadata failures

**Symptoms**

- `ModuleNotFoundError: No module named 'dreamerv3'`
- `ModuleNotFoundError: No module named 'embodied'`
- `PackageNotFoundError: dreamer`

**Likely causes**

- The `dreamer` distribution is not installed in the active Python.
- A checkout is on `PYTHONPATH` but package metadata is missing.
- Python is too new or dependency wheels do not support it; the README-tested
  baseline is Python 3.11+ and ML dependencies are safest on Python 3.11.

**Recovery**

- Install the package in an isolated Python 3.11 environment using the repository
  metadata, then rerun `scripts/check_dreamerv3_install.py`.
- For local development only, pass `--repo-root` to bundled scripts instead of
  relying on the current working directory.
- Do not diagnose training quality until import metadata and the dummy-env check
  pass.

## JAX backend, CUDA, or memory failures

**Symptoms**

- `Unknown backend cuda`, `Unable to initialize backend 'cuda'`, XLA library
  errors, CUDA driver/runtime mismatch, or `RESOURCE_EXHAUSTED`/out-of-memory.
- Errors surface late in training but the first stack trace mentions JAX, CUDA,
  or allocation.

**Likely causes**

- CPU-only JAX installed while config asks for CUDA.
- CUDA wheel/driver mismatch, missing GPU visibility, or container runtime not
  exposing devices.
- The run is too large for memory; DreamerV3 defaults are production-oriented.

**Recovery**

- First prove CPU debug mode works:

  ```bash
  JAX_PLATFORM_NAME=cpu python scripts/check_dreamerv3_install.py --backend cpu
  python sub-skills/train-configure/scripts/smoke_train_debug.py --jax-platform cpu --dry-run-config
  ```

- For CUDA, use the repo-declared JAX CUDA requirements or a compatible updated
  JAX/CUDA pair, then run `python scripts/check_dreamerv3_install.py --backend cuda`.
- For OOM, lower `batch_size`, choose `debug` or a smaller `size*` preset, set
  `jax.prealloc=False`, and inspect config with
  `sub-skills/jax-models/scripts/inspect_model_config.py`.
- See `sub-skills/results-ops/references/install-and-backends.md` for Docker and
  optional system packages.

## Config, CLI, and task failures

**Symptoms**

- `KeyError` for a config block or task suite.
- `NotImplementedError(config.script)`.
- Optional environment `ImportError` during `make_env`.
- Training starts but creates an unexpected logdir or fails to resume.

**Likely causes**

- Config blocks after `--configs` were misspelled or ordered incorrectly.
- Dotted overrides target the wrong config path.
- The `task` prefix selects an optional suite whose package/system dependency is
  not installed.
- The checkpoint/logdir was reused after changing model shape.

**Recovery**

- Read `sub-skills/train-configure/references/cli-and-config.md` and use the
  smoke helper's dry run to inspect the translated CLI.
- Use `sub-skills/results-ops/scripts/check_optional_env_imports.py --task <task>`
  before installing every optional environment package.
- Start a fresh logdir when changing size presets, observation/action spaces,
  bins, RSSM dimensions, or model head shapes.

## Env, replay, and dataflow failures

**Symptoms**

- Assertions about missing `reset`, `is_first`, `is_last`, `is_terminal`, or
  dtype/shape bounds.
- Replay never samples, `len(replay)` stays too small, or sequences mix workers.
- Parallel driver subprocesses die after an environment exception.

**Likely causes**

- Custom env does not implement the `embodied.Env` contract.
- Driver callback ignored the `worker` id when adding transitions to replay.
- Replay capacity is smaller than `batch_size * batch_length` or sequence length
  requirements.
- Optional env constructor failed inside a worker process.

**Recovery**

- Read `sub-skills/embodied-dataflow/SKILL.md` and run
  `sub-skills/embodied-dataflow/scripts/check_embodied_contracts.py`.
- Add `UnifyDtypes` and `CheckSpaces` during debugging.
- Reduce parallelism with debug/single-env settings until the env contract is
  clean, then scale up.

## Metrics, plotting, Scope, and result files

**Symptoms**

- No `metrics.jsonl` or `scores.jsonl` yet.
- Scope viewer cannot start or logs are hard to inspect without the viewer.
- Plotting scripts fail on malformed JSONL, missing keys, or missing plotting
  dependencies.

**Likely causes**

- The run has not reached a log interval or episode end.
- Logger outputs were changed from defaults.
- Result schema differs between scalar metrics and gzipped benchmark score
  artifacts.

**Recovery**

- Summarize log files with:

  ```bash
  python sub-skills/results-ops/scripts/metrics_summary.py --input <logdir>/metrics.jsonl --list-keys
  python sub-skills/results-ops/scripts/metrics_summary.py --input <logdir>/scores.jsonl --key episode/score
  ```

- Read `sub-skills/results-ops/references/results-and-plotting.md` for logdir
  schema, Scope viewer commands, and plotting/dataframe dependency notes.

## When to stop and ask for approval

Stop before:

- installing host-level GPU/system packages, Java, DMLab, MineRL, ROMs, or Xvfb;
- launching benchmark-scale or long-running training;
- downloading external datasets or ROMs;
- using cloud credentials, W&B accounts, GCP metadata, or private log storage;
- deleting or rewriting an existing logdir/checkpoint.
