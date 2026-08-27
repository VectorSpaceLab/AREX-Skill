# Sacred reproducibility and capture reference

This reference distills Sacred 0.8.7 behavior for reproducibility-critical random seeding, source/dependency discovery, capture settings, and optional TensorFlow logdir capture.

## API surface to keep in view

| API | Reproducibility/capture use |
| --- | --- |
| `Experiment(name=None, ingredients=(), interactive=False, base_dir=None, additional_host_info=None, additional_cli_options=None, save_git_info=True)` | Constructs the run root, discovers sources/dependencies immediately, and optionally records Git metadata. Use `interactive=True` only when no script source is available; this weakens source capture. Use `save_git_info=False` only when Git metadata is intentionally unavailable. |
| `Experiment.run(command_name=None, config_updates=None, named_configs=(), info=None, meta_info=None, options=None)` | Programmatic run entry point. Fix root seed with `config_updates={"seed": 123}`. Set run options such as `options={"--capture": "sys", "--loglevel": "WARNING"}`. |
| `Experiment.run_commandline(argv=None)` | CLI entry point. Supports `with seed=...`, `print_dependencies`, `-e/--enforce_clean`, `-C/--capture`, `-l/--loglevel`, and related flags. |
| `Ingredient(path, ingredients=(), interactive=False, _caller_globals=None, base_dir=None, save_git_info=True)` | Reusable component with its own captured functions and hierarchical seed stream. Its `base_dir` and construction context affect source discovery. |
| `Ingredient.capture(function=None, prefix=None)` / `Ingredient.command(function=None, prefix=None, unobserved=False)` | Captured functions/commands can receive `_seed`, `_rnd`, `_log`, `_run`, and config values. `_seed`/`_rnd` are generated only for functions whose signatures request them. |
| `SETTINGS` | Process-global settings object. Set discovery and capture defaults before construction/run. Keys are frozen; unknown settings or replacing nested groups raises a setting error. |
| `sacred.stflow.LogFileWriter(experiment)` | Optional TensorFlow helper. Inside a running experiment, intercepts `tensorflow.summary.FileWriter` construction in a decorator/context scope and appends logdirs to `experiment.info["tensorflow"]["logdirs"]`. |

## Root seed, `_seed`, and `_rnd`

- Every run has a root `seed` in its final config. If the caller does not provide one, Sacred generates one.
- A fixed root seed is the central reproducibility control: use `with seed=123` on the CLI or `config_updates={"seed": 123}` with `Experiment.run`.
- At run start, Sacred seeds global PRNGs from the root seed:
  - Python `random.seed(seed)` always.
  - `numpy.random.seed(seed)` when NumPy is available.
  - TensorFlow `set_random_seed(seed)` only if TensorFlow is already imported in the process cache.
  - PyTorch `manual_seed(seed)`, and CUDA seeds when available, only if PyTorch is already imported in the process cache.
- Captured functions that accept `_seed` or `_rnd` receive per-call values derived from the root seed.
- `_seed` is a fresh integer for that invocation. `_rnd` is a PRNG initialized from that `_seed`.
- Each captured function receives its own deterministic seed stream during run initialization. Calling one captured function does not consume another captured function's stream. Reordering calls to different captured functions is therefore more stable than sharing one global PRNG.
- Repeated calls to the same captured function do consume that function's stream sequentially; adding/removing calls to that same function can change later `_seed`/`_rnd` values for that function.
- Ingredients are seeded hierarchically from parent or root streams, so ingredient sub-components get deterministic but separate streams.
- If NumPy is installed, `_rnd` is usually a NumPy generator in modern environments. If `SETTINGS.CONFIG.NUMPY_RANDOM_LEGACY_API` is `True`, `_rnd` is a legacy NumPy random state. Without NumPy, `_rnd` is a Python `random.Random` object. Write helper code that handles the RNG type instead of assuming one method name.

Minimal deterministic pattern:

```python
from sacred import Experiment

ex = Experiment("deterministic", save_git_info=False)

@ex.capture
def draw(_seed, _rnd):
    try:
        value = int(_rnd.integers(0, 1000))
    except AttributeError:
        value = int(_rnd.randint(0, 1000))
    return {"seed": int(_seed), "value": value}

@ex.main
def main(_run):
    return {"root_seed": _run.config["seed"], "first": draw(), "second": draw()}

run_a = ex.run(config_updates={"seed": 123}, options={"--loglevel": "WARNING"})
run_b = ex.run(config_updates={"seed": 123}, options={"--loglevel": "WARNING"})
assert run_a.result == run_b.result
```

## Avoiding accidental nondeterminism

- Do not create module-level PRNG objects that are consumed before `Run.__call__` starts; Sacred seeds globals at run start, not at import time.
- Prefer `_rnd` over a global PRNG when a function's output should be stable under unrelated call-order changes.
- If using a library that Sacred does not seed globally, pass `seed` or `_seed` into that library's seeding API inside the main function or a captured function.
- If using TensorFlow or PyTorch global seeding through Sacred, import the framework before the run starts or seed it manually inside the run. Sacred only auto-seeds those frameworks when they are already imported when global seeding happens.
- For GPU libraries, data loaders, multiprocessing, and low-level kernels, Sacred records and propagates seeds but cannot by itself make all underlying algorithms deterministic.

## Source and dependency discovery

Sacred gathers experiment metadata when an `Experiment` or `Ingredient` is constructed.

What is collected:

- Main source file, when `__file__` is available.
- Local source files discovered from imported modules or directories, depending on settings.
- Package dependencies with versions, using installed package metadata.
- Git repository URL/path, commit hash, and dirty flag when Git integration is enabled.

Settings that control discovery:

| Setting | Values | Default | Effect |
| --- | --- | --- | --- |
| `SETTINGS.DISCOVER_SOURCES` | `"none"`, `"imported"`, `"sys"`, `"dir"` | `"imported"` | Chooses how local Python source files are discovered. `imported` scans modules referenced from construction globals; `sys` scans loaded modules; `dir` scans Python files under the base directory; `none` leaves only explicitly known main/source files. |
| `SETTINGS.DISCOVER_DEPENDENCIES` | `"none"`, `"imported"`, `"sys"`, `"pkg"` | `"imported"` | Chooses how package dependencies are detected. `pkg` records installed working-set packages, excluding broken `0.0.0` metadata. |
| `base_dir` constructor argument | path-like | caller file directory | Defines the local-source boundary for discovery and relative source serialization. |
| `save_git_info` constructor argument | `True`/`False` | `True` | Controls Git metadata collection. If enabled, GitPython and Git must be importable/usable. |

Practical rules:

1. Import modules that should be discovered before constructing the experiment, or manually add source/dependency metadata.
2. Set `DISCOVER_SOURCES` and `DISCOVER_DEPENDENCIES` before constructing the experiment.
3. Ensure the environment provides `pkg_resources` through a compatible setuptools release, because Sacred imports it for package metadata.
4. Use `base_dir` when the experiment entry point sits below a package tree and local source discovery needs a wider or narrower boundary.
5. Avoid `interactive=True` for production reproducibility. It allows interactive environments but there may be no main source file to store.
6. When Git metadata is unnecessary or unavailable, pass `save_git_info=False`; do not combine that with `enforce_clean` because clean enforcement needs repository metadata.

## Inspecting dependencies with `print_dependencies`

Each experiment automatically registers a `print_dependencies` command. It is unobserved and prints:

- `Dependencies`: package names and versions.
- `Sources`: discovered source file names and MD5 digests.
- `Version Control`: discovered Git repository identity, commit, and dirty state. A leading `M` marks a dirty repository.

CLI patterns:

```bash
python experiment.py print_dependencies
python experiment.py print_dependencies with seed=123
```

Programmatic equivalent:

```python
run = ex.run(command_name="print_dependencies", options={"--loglevel": "WARNING"})
```

Use this before a reproducibility-sensitive run to confirm that expected local sources and package dependencies are visible. If sources are missing, adjust construction order, `base_dir`, or discovery settings before the `Experiment` is constructed.

## Enforcing a clean repository

The `-e` / `--enforce_clean` option fails a run if Sacred detected no version-control repositories or if any detected repository is dirty.

Use it when:

- The experiment is run from tracked source files.
- GitPython and Git are available.
- The `print_dependencies` output shows the expected repository and commit.

Do not use it when:

- Running intentionally from an unpacked script without Git metadata.
- `save_git_info=False` was used.
- Running interactively without reliable source capture.

Typical failure modes:

- `No version control detected`: no repository metadata was collected. Confirm source discovery, `save_git_info`, GitPython/Git availability, and non-interactive construction.
- `Uncommited changes`: the repository dirty flag is true. Commit, stash, or intentionally rerun without the clean-enforcement option.

## `SETTINGS` groups that affect reproducibility and capture

`SETTINGS` supports both dict and attribute notation:

```python
from sacred import SETTINGS
SETTINGS.CAPTURE_MODE = "sys"
SETTINGS.HOST_INFO.INCLUDE_GPU_INFO = False
SETTINGS["DISCOVER_SOURCES"] = "dir"
```

Settings keys are frozen. Unknown keys and replacing nested groups are rejected; modify leaf keys instead.

Important groups and leaves:

| Setting | Meaning |
| --- | --- |
| `SETTINGS.CAPTURE_MODE` | Default capture mode when output capture is active and no run-specific capture option overrides it. Default is `fd` on Linux/macOS and `sys` on Windows. |
| `SETTINGS.DEFAULT_BEAT_INTERVAL` | Default seconds between heartbeat events. Heartbeats propagate captured output and info to observers. |
| `SETTINGS.DISCOVER_SOURCES` | Source discovery strategy; set before experiment construction. |
| `SETTINGS.DISCOVER_DEPENDENCIES` | Dependency discovery strategy; set before experiment construction. |
| `SETTINGS.CONFIG.READ_ONLY_CONFIG` | Makes config containers read-only in captured functions where possible. |
| `SETTINGS.CONFIG.NUMPY_RANDOM_LEGACY_API` | Chooses legacy NumPy `RandomState` for `_rnd` instead of newer generator behavior when NumPy is installed. |
| `SETTINGS.CONFIG.ENFORCE_KEYS_*` | Controls config-key compatibility checks for MongoDB/jsonpickle/Python identifiers/string keys/no equals signs. Route detailed config mechanics elsewhere. |
| `SETTINGS.HOST_INFO.INCLUDE_GPU_INFO` / `INCLUDE_CPU_INFO` | Host-info collection toggles. Disabling can reduce startup overhead. |
| `SETTINGS.HOST_INFO.CAPTURED_ENV` | Explicit list of environment variable names to copy into host info. Keep secrets out of this list. |
| `SETTINGS.COMMAND_LINE.STRICT_PARSING` | Makes CLI config parsing stricter. |
| `SETTINGS.COMMAND_LINE.SHOW_DISABLED_OPTIONS` | Controls whether disabled CLI options are shown. |

Because `SETTINGS` is process-global, tests and notebooks should save and restore any changed values.

## Capturing stdout and stderr

Sacred stores captured output in `Run.captured_out` and transmits it to observers during heartbeat/final events. Capture mode can be set with `-C/--capture`, with `Experiment.run(options={"--capture": ...})`, or by changing `SETTINGS.CAPTURE_MODE` before the run.

| Mode | Captures | Limitations | Good use |
| --- | --- | --- | --- |
| `no` | Nothing is stored in `captured_out`. Output still goes to the console. | No observer-visible stdout/stderr. | Local debugging, very verbose runs, or when logs are stored elsewhere. |
| `sys` | Python `sys.stdout` and `sys.stderr` writes, including ordinary `print`, tracebacks, and stream-based logging. | Does not reliably capture subprocess output, C extensions, or writes bypassing Python streams. Default on Windows. | Portable capture for pure-Python experiments and tests. |
| `fd` | File-descriptor-level stdout/stderr, including many subprocess and C-extension writes. | Platform-dependent, uses tee-like subprocesses or a Python fallback, may be unreliable in some notebooks/test harnesses. Default on Linux/macOS when capture is active. | Experiments that emit from subprocesses or native code on supported systems. |

Subtle default: if a run has no observers and no explicit capture mode, Sacred uses `no` capture even if `SETTINGS.CAPTURE_MODE` is `fd` or `sys`. Add an observer or pass `--capture`/`options={"--capture": "sys"}` when you need `Run.captured_out` in a local run.

## Captured-output filters

Captured output behaves like a file, not a terminal. Backspaces, carriage returns, and progress-bar updates are stored literally unless a filter rewrites them.

Use `Experiment.captured_out_filter` for a function that accepts and returns a string:

```python
from sacred import Experiment
from sacred.utils import apply_backspaces_and_linefeeds

ex = Experiment("progress", save_git_info=False)
ex.captured_out_filter = apply_backspaces_and_linefeeds
```

The filter is applied whenever Sacred refreshes `captured_out`, including heartbeat and final capture. If a filter truncates or summarizes output, make that intentional because observers receive the filtered version.

For high-volume runs, a filter can cap output size or replace it with a constant summary to avoid overwhelming observer storage. Route storage-limit details to the observer/logging sub-skill.

## Logging level and capture interaction

Sacred configures a stream logger when no custom logger is supplied. Important interactions:

- `-l LEVEL` / `--loglevel=LEVEL` changes Sacred's root logger level. Programmatically, pass `options={"--loglevel": "ERROR"}` to `Experiment.run`.
- Captured functions can accept `_log`; this is a child logger of the experiment logger.
- If capture mode is `sys` or `fd`, log records emitted to captured stdout/stderr streams can appear in `Run.captured_out`.
- For tests that assert exact captured output, set a high log level such as `CRITICAL` and explicit capture mode such as `sys`.
- Custom loggers with file handlers or external handlers may not be represented in `captured_out`; that is expected because capture follows stdout/stderr, not arbitrary logging backends.

## Optional TensorFlow `LogFileWriter`

Sacred's TensorFlow helper is optional and should be treated as unverified unless the active environment imports TensorFlow successfully.

Behavior:

- Import with `from sacred.stflow import LogFileWriter`.
- Use as a decorator or context manager around code that constructs `tensorflow.summary.FileWriter` objects.
- The experiment must already be in the `RUNNING` state before entering the decorator/context scope.
- Each intercepted `FileWriter` construction appends the supplied logdir string to `experiment.info["tensorflow"]["logdirs"]`.
- Calls outside the decorator/context scope are not recorded.
- TensorFlow 1.12 and older are deprecated by Sacred's compatibility helper. For newer TensorFlow packages, Sacred imports `tensorflow.compat.v1`.

Minimal shape:

```python
from sacred import Experiment
from sacred.stflow import LogFileWriter

ex = Experiment("tf_logs", save_git_info=False)

@ex.main
@LogFileWriter(ex)
def main(_run):
    # Construct TensorFlow FileWriter objects here only after verifying
    # TensorFlow is installed and the v1 summary API is available.
    pass
```

Do not claim TensorFlow logdir capture works in an environment until a tiny local TensorFlow import and `FileWriter` construction has been run there.
