# SR configurations and runtime choices

## Preset choice

`physo.SR` defaults to the SR `config0` preset when no `run_config` is provided.
For repeatable experiments, pass an explicit deep copy and keep the original
imported preset untouched.

| Preset | Best fit in this sub-skill | Key evidence-backed difference | Notes |
| --- | --- | --- | --- |
| `physo.config.config0.config0` | Short demos, smoke checks, first one-dataset SR attempt | `MAX_LENGTH=35`, `batch_size=1000`, LBFGS free-constant optimization `n_steps=15` | Default for `physo.SR`; light and fast relative to larger presets. |
| `physo.config.config0b.config0b` | One-dataset SR with free constants when the same search needs more constant-optimization patience | Same config family but LBFGS free-constant optimization `n_steps=30` | Documented as the Class SR `b` variant, but structurally compatible with `SR`; use only when the extra constant fitting cost is justified. |

The package also ships heavier config families. Use them only after the quick
SR route is working and the user explicitly wants a more expensive search or a
paper/benchmark-style setting. Do not claim a longer preset is a correctness
guarantee.

## Copy before editing

`physo.SR` delegates to `physo.ClassSR` internally and the argument handler
updates the run configuration with dataset/library, logger, visualiser, reward,
parallel, and epoch information. Avoid sharing one mutable imported config
object across unrelated runs.

```python
import copy
import physo

run_config = copy.deepcopy(physo.config.config0.config0)
run_config["learning_config"]["batch_size"] = 256  # smoke/debug tweak

expression, logs = physo.SR(X, y, run_config=run_config, epochs=5)
```

If you edit `learning_config["max_time_step"]`, also update the `HardLengthPrior`
entry in `priors_config` so its `max_length` is not larger than `max_time_step`.
A mismatch fails before training with a prior assertion.

## Budget and stopping controls

- `epochs`: preferred short-run budget knob. Passing `epochs=<int>` overrides
  `run_config["learning_config"]["n_epochs"]` for that call.
- `stop_reward`: early-stop reward threshold. With free constants, the source
  docstring recommends using a threshold such as `1 - 1e-5` when exact reward
  `1.0` is too strict.
- `stop_after_n_epochs`: additional epochs after early-stop reward is reached;
  default is `10`.
- `max_n_evaluations`: cap on unique expression evaluations. It is not the same
  as `batch_size * epochs` because dimensionally invalid candidates may not be
  evaluated.

For a quick health check, lower `epochs` first and optionally lower `batch_size`
in a deep-copied config. The bundled smoke defaults to `config0` and also
accepts `--preset config0b` when you want to exercise the longer
free-constant-optimization variant without changing the script. For a real
experiment, tune on a validation plan rather than merely increasing every
budget.

## Operator and prior alignment

The default SR operator list is:

```python
["mul", "add", "sub", "div", "inv", "n2", "sqrt", "neg",
 "exp", "log", "sin", "cos"]
```

Reducing `op_names` is useful when the physical grammar is known, but configs
also contain priors that refer to some operator families. The native SR test
confirms that a reduced list such as `["mul", "add", "sub", "div"]` can still
run; warnings may appear and prior construction can ignore a prior that cannot
be instantiated with the available tokens. If the warnings are unexpected,
either restore the missing operator or copy the config and remove the irrelevant
prior.

When using dimensioned variables, be careful with nonlinear operators:
`exp`, `log`, and trigonometric functions require dimensionless arguments, while
powers change units. The unit vectors assigned to free constants often decide
whether a candidate expression can become physically valid.

## Candidate-wrapper configuration

`candidate_wrapper` is independent of the run preset. It must be callable as
`wrapper(func, X)` and return predictions with the sample dimension expected by
`y`. For free constants, make it torch-differentiable; otherwise LBFGS constant
optimization can fail or silently score candidates poorly.

When `parallel_mode=True`, avoid lambdas and closures because the wrapper is
attached to program objects used by multiprocessing. Prefer a top-level function
in a script.

## Parallel and device policy

The verified skill environment is CPU-only. Use this default for smoke and
notebook work:

```python
expression, logs = physo.SR(
    X, y,
    parallel_mode=False,
    n_cpus=1,
    device="cpu",
)
```

`parallel_mode=True` is documented for Python scripts rather than notebooks and
can be faster for expensive free-constant optimization, but it adds process
startup and pickling overhead. Test with the actual dataset before assuming a
speedup.

Do not claim CUDA behavior from this skill. If a user separately installs a CUDA
PyTorch build, `device="cuda"` is an application decision outside the verified
CPU scope, and parallel-mode expectations may differ.

## Logging choices

- For no persistent output, pass `RunLogger(..., do_save=False)` and
  `get_run_visualiser=lambda: None` or a visualiser with `do_save=False`.
- For reproducible inspection, provide explicit relative output names and set
  both logger and visualiser `do_save=True`. The visualiser writes Pareto pkl and
  CSV files derived from its `save_path` stem.
- Use `logs.get_pareto_front()` immediately after a run even when no files are
  saved.
