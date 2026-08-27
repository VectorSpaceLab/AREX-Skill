# Troubleshooting

This reference keeps the most common DreamerV3 configuration and training failures in one place.
It focuses on startup, config composition, checkpoint compatibility, JAX platform issues, and optional environment dependencies.

## Fast first checks

1. Run `scripts/smoke_train_debug.py --dry-run-config` to inspect the final training command without starting a run.
2. Use `dummy_disc` and `debug` first if you are unsure whether a failure is caused by the environment or by DreamerV3 itself.
3. If the failure appears after changing a size preset, assume checkpoint incompatibility until proven otherwise.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `NotImplementedError(config.script)` | Unsupported `--script` value | Use one of the supported run loops: `train`, `train_eval`, `eval_only`, `parallel`, `parallel_env`, `parallel_envs`, or `parallel_replay` |
| Config key not applied | Wrong dotted flag name or wrong override order | Use the exact config path from `configs.yaml`; remember that later `--configs` blocks override earlier ones and explicit flags override all presets |
| `Too many leaves for PyTreeDef` or a similar checkpoint shape error | Reused a checkpoint after changing model shape, usually via a size preset change | Use a new logdir, or restore only from a shape-compatible config and checkpoint |
| `assert config.batch_size * length <= capacity` | Replay capacity is too small for the selected batch length, report length, and replay context | Increase `replay.size` or reduce `batch_size`, `batch_length`, `report_length`, `consec_train`, `consec_report`, or `replay_context` |
| `assert actor_batch <= envs` in parallel mode | Too many actor slots for the number of env workers | Lower `actor_batch` or raise `envs` |
| `CUDA` / JAX / OOM failures | Wrong backend, incompatible wheel, or memory pressure | Try the smoke helper with `--jax-platform cpu`; if training on GPU, verify the installed JAX wheel and reduce `batch_size` first |
| Env import error for a suite task | Missing optional package for that environment family | Use `dummy_disc` for smoke, or install the suite-specific dependency before trying the real task |
| `memory_maze` or a similar suite import error | The task family needs a package that is not installed | Install the optional dependency for that task family or choose a different preset |
| Parallel launch hangs or disconnects | Port collision, stale worker, wrong worker counts, or address mismatch | Let the launcher choose `{auto}` ports, check `actor_addr` / `replay_addr` / `logger_addr`, and verify `actor_batch`, `envs`, and `remote_*` settings |
| No metrics written in a tiny smoke | The step count finished before a log interval or report interval was reached | Use the bundled smoke helper defaults, increase `run.steps`, or lower the log interval |

## Config parsing issues

### Wrong flag name

DreamerV3 uses dotted config paths such as:

- `--logdir`
- `--task`
- `--run.steps`
- `--run.train_ratio`
- `--run.envs`
- `--jax.platform`
- `--batch_size`

A missing dot or a renamed key usually means the flag never reaches the intended field.

### Wrong preset order

If you compose presets in the wrong order, an earlier block may be silently overwritten.

Good:

```sh
python -m dreamerv3.main --configs debug multicpu --task dummy_disc
```

Bad if you wanted the debug CPU settings to survive:

```sh
python -m dreamerv3.main --configs multicpu debug --task dummy_disc
```

### Unknown task

`make_env` splits `task` at the first underscore.
That means the task should look like `suite_task`.
If the suite prefix is unsupported or misspelled, environment creation fails before the loop starts.

## Checkpoint and logdir compatibility

### Safe continuation rule

- Reuse the same logdir only when you want to continue the same run shape.
- Use a fresh logdir when you changed a size preset or another shape-sensitive config.

### What usually breaks compatibility

- size preset changes
- agent architecture changes
- batch length or report length changes
- replay context changes that affect stream shape
- switching between an old and a new checkpoint tree with different parameter layouts

### What to do

- If you want the same training run to continue: keep the logdir and the config stable.
- If you want to compare a new model size: use a new logdir and keep the old run untouched.
- If you only want to warm-start compatible weights from another run: use `run.from_checkpoint` with a known-compatible checkpoint tree.

## JAX platform and preallocation

### CPU smoke

For the smallest validation, set:

- `--jax.platform cpu`
- `debug`
- `dummy_disc`

That avoids GPU driver, CUDA, and preallocation issues.

### GPU run

If a GPU run fails:

1. confirm the backend and wheel are matched
2. check whether the failure is actually an earlier error that happened before the visible CUDA message
3. reduce `batch_size` before changing anything more invasive
4. if needed, switch to CPU smoke to separate training logic from accelerator setup

### Preallocation

The debug preset disables JAX preallocation.
If you are debugging memory pressure, the CPU smoke helper is a good first isolation step.

## Optional environment dependencies

Some task families need extra packages beyond the base install.
Typical examples include Atari, Crafter, DMLab, Minecraft, Procgen, DMC, and memory maze style tasks.

If a task import fails:

- confirm the suite prefix in `task`
- confirm the optional dependency for that suite is installed
- rerun the smoke helper with `dummy_disc` if you only need to test the run loop

## Parallel-mode issues

### Common signs

- `actor_batch` is larger than the number of env workers
- one worker prints that it lost connection to the agent
- log output shows one service is alive while another never starts
- a port is already in use

### Practical fixes

- let `{auto}` choose fresh ports when possible
- lower `actor_batch`
- match `envs` to the intended number of actor slots
- check whether a stale worker from an earlier attempt is still running
- if you are only validating the single-process path, stay on `train` or `train_eval`

## When the smoke helper is enough

Use the bundled smoke helper when you only need to know whether:

- the config parses
- the dummy environment starts
- the logger writes
- the checkpoint tree is created
- the resume path is at least structurally valid

If the helper passes but a real task fails, the failure is probably in the optional environment or backend setup rather than in the training config layer.
