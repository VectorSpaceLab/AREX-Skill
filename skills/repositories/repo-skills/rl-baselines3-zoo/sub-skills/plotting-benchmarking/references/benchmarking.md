# Benchmarking workflows

RL Zoo includes a benchmark module that evaluates known trained agents and writes a Markdown performance table. Treat it as an evaluation/reporting workflow, not as a training benchmark suite. It can be useful for smoke-testing trained-agent compatibility, but the published-style table is based on one run per agent and should not be reported as a statistically robust comparison.

## Safe default command

Use the benchmark module form; the console router does not expose a `benchmark` subcommand.

```bash
python -m rl_zoo3.benchmark \
  --log-dir ./rl-trained-agents \
  --benchmark-dir ./benchmark-output \
  --n-timesteps 100 \
  --num-threads 1 \
  --seed 0 \
  --test-mode \
  --no-hub
```

Safety flags:

| Flag | Why it matters |
| --- | --- |
| `--test-mode` | Stops after one experiment and prevents copying the generated table over a root `benchmark.md` file. Use this for smoke tests and skill verification. |
| `--no-hub` | Prevents adding the live Hugging Face model catalog to the candidate list. Use this unless the caller explicitly requested live Hub behavior. |
| `--benchmark-dir` | Keeps reward logs and the generated `benchmark.md` in a caller-controlled output directory. |
| `--n-timesteps` | Bounds evaluation length. Small values are for smoke checks only; they are not meaningful performance estimates. |
| `--num-threads` | Limits PyTorch CPU thread use for reproducible small checks. |

Use the bundled helper to build this command without running it:

```bash
python scripts/plotting_command_builder.py benchmark \
  --log-dir ./rl-trained-agents --benchmark-dir ./benchmark-output \
  --n-timesteps 100 --num-threads 1
```

## Inputs discovered by the benchmark module

The benchmark module discovers local trained agents from `--log-dir`. A model is discoverable only when the folder contains exactly one saved argument file under each model folder:

```text
<log-dir>/<algo>/<env-id>_<exp-id>/<env-id>/args.yml
```

From that file, RL Zoo reads the environment id. It then evaluates the selected model with no rendering and writes reward logs under:

```text
<benchmark-dir>/<model-name>/
```

For result-table metadata, it later expects saved hyperparameters under:

```text
<log-dir>/<algo>/<env-id>_<exp-id>/<env-id>/config.yml
```

and the model selection conventions owned by [`../../evaluation-and-artifacts/SKILL.md`](../../evaluation-and-artifacts/SKILL.md). If model or artifact selection is uncertain, inspect or plan it there before running a benchmark command.

## Outputs

The module writes:

```text
<benchmark-dir>/benchmark.md
```

The table columns are:

| Column | Meaning |
| --- | --- |
| `algo` | RL Zoo algorithm id. |
| `env_id` | Gymnasium environment id read from saved args or Hub metadata. |
| `mean_reward` | Mean episode reward over the evaluation reward log. |
| `std_reward` | Standard deviation of episode rewards. |
| `n_timesteps` | Training budget read from saved hyperparameters and formatted as `k` or `M`. |
| `eval_timesteps` | Final evaluation timestep in the reward log. |
| `eval_episodes` | Number of evaluated episodes. |

When `--test-mode` is omitted, the module also copies the generated table to `benchmark.md` in the current working directory. Avoid that side effect unless the caller explicitly wants to refresh a benchmark report.

## Hub and offline boundaries

`--no-hub` is the correct default for offline work. Without it, the module augments local models with models listed on the Hugging Face Hub, which is a live network dependency and belongs under [`../../integrations-hub-tracking/SKILL.md`](../../integrations-hub-tracking/SKILL.md).

Even with `--no-hub`, ensure local trained-agent folders are complete. If a selected local model lacks saved hyperparameters, RL Zoo may try a Hub download as a fallback to complete the artifact. For strict offline operation, use complete local artifacts and inspect missing files before running. If a task actually requires Hub fallback or downloads, route to the integrations sub-skill for network and credential handling.

## Package-only caveat

The benchmark module is importable as `python -m rl_zoo3.benchmark`, but its evaluation subprocess expects an `enjoy.py` command shim in the current working directory. Many source checkouts have that shim; a pure installed-package workspace may not. If the module fails with a missing `enjoy.py` file, do not copy source files from an original checkout. Instead:

1. Route model selection and no-render evaluation details to [`../../evaluation-and-artifacts/SKILL.md`](../../evaluation-and-artifacts/SKILL.md).
2. Build explicit installed-package evaluation commands with `python -m rl_zoo3.enjoy` for the desired algo/env/model set.
3. Use benchmark output only when the runtime workspace intentionally provides a compatible shim or when a future RL Zoo version removes that subprocess assumption.

## Interpreting benchmark results

- The benchmark is designed to check maximal trained-agent behavior and catch regressions, not to provide statistically rigorous multi-seed comparisons.
- Deterministic policy evaluation is used except for Atari-style behavior handled by RL Zoo evaluation defaults.
- A small `--n-timesteps` smoke command validates command and artifact plumbing only; do not compare algorithms from it.
- MuJoCo/robotics environments are skipped unless `--with-mujoco` is supplied and the environment family is installed/licensed.
- Missing or stale environment versions can make a benchmark fail even if the model artifact layout is correct.

## Native verification candidate

A bounded native-style candidate is:

```bash
python -m rl_zoo3.benchmark -n 100 --benchmark-dir <tmpdir> --test-mode --no-hub
```

Expected observation: exit code 0 in a checkout-like workspace with discoverable local trained-agent fixtures; `<tmpdir>/benchmark.md` exists. If this fails because no local fixture or `enjoy.py` shim is present, treat it as an environment/artifact limitation, not as evidence that plotting workflows are wrong.
