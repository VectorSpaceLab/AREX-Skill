# Reproducibility and capture troubleshooting

Use this guide when a Sacred run is not reproducible, metadata is missing, or captured output does not match expectations.

## Quick triage order

1. Confirm Sacred version and the root seed recorded in `run.config["seed"]`.
2. Run `print_dependencies` and inspect dependencies, source hashes, and VCS dirty state.
3. Check whether stochastic code uses `_seed`/`_rnd` or an uncontrolled global PRNG.
4. Check `SETTINGS` values before experiment construction and run options before execution.
5. Reproduce with `--loglevel=CRITICAL --capture=sys` to reduce logging and file-descriptor complications.
6. Only then investigate optional libraries, parallelism, GPU kernels, or observer backends.

## Symptom matrix

| Symptom | Likely cause | What to inspect | Fix |
| --- | --- | --- | --- |
| Same `seed`, different results | Randomness comes from a library Sacred does not seed, a framework imported after Sacred's global seeding point, multiprocessing/GPU nondeterminism, data order, or module-level PRNG state created before the run. | `run.config["seed"]`; whether functions accept `_seed`/`_rnd`; imports before run start; library-specific determinism flags. | Move stochastic work into captured functions, pass `_seed` to external libraries, manually seed unsupported libraries inside the run, import TensorFlow/PyTorch before run start if relying on Sacred global seeding, and enable library-specific deterministic modes. |
| Results change after adding an unrelated random call | Shared global PRNG stream was consumed in a different order. | Calls to `random`, `numpy.random`, framework global RNGs, and long-lived generator objects. | Use per-call `_rnd`/`_seed` in captured functions. Keep unrelated stochastic components in separate captured functions or ingredients. |
| `_rnd` has unexpected methods | NumPy is installed or `SETTINGS.CONFIG.NUMPY_RANDOM_LEGACY_API` changed. | Type of `_rnd`; `SETTINGS.CONFIG.NUMPY_RANDOM_LEGACY_API`. | Write RNG adapters that support NumPy generator, legacy random state, and Python `random.Random`; avoid hardcoding one API. |
| No captured output in `run.captured_out` | No observer was attached and no explicit capture mode was set, so Sacred defaulted to `no` capture. | `run.capture_mode`; run options; observer list. | Pass `options={"--capture": "sys"}` or CLI `-C sys`, or attach an observer when storage is desired. |
| Python `print` is captured but subprocess/C output is missing | Capture mode is `sys`. | `--capture` option and platform. | Use `fd` on a platform where file-descriptor capture is reliable, or redirect subprocess/native output into Python and print it. |
| `fd` capture hangs, is flaky, or misses output | File-descriptor capture depends on OS support, tee-like subprocesses, and harness behavior. | Platform, notebooks, test harness capture, availability of `tee`, warnings from capture code. | Use `sys` for pure-Python tests; reserve `fd` for supported shell/script execution; avoid asserting exact fd behavior in brittle harnesses. |
| Progress bars flood stored output | Captured output stores control characters literally. | `run.captured_out`; presence of `\r`, `\b`, or repeated progress lines. | Set `ex.captured_out_filter`, for example a filter that applies terminal-like backspace/carriage-return behavior or truncates output intentionally. |
| Logs appear in captured output and break exact-output tests | Sacred logger or `_log` writes to captured stdout/stderr. | `--loglevel`; custom logger handlers; capture mode. | Use `--loglevel=CRITICAL` for exact-output tests, or assert substrings rather than exact output. |
| `print_dependencies` misses local source files | Experiment was constructed before imports, wrong `base_dir`, interactive mode lacks a main file, or discovery setting is too narrow. | Construction order; `SETTINGS.DISCOVER_SOURCES`; `base_dir`; `interactive=True`; printed `Sources`. | Import local modules before constructing the experiment, set `DISCOVER_SOURCES="dir"` when appropriate, choose an explicit `base_dir`, run from a script instead of interactive mode, or manually add source files. |
| `print_dependencies` misses package versions | Package metadata is absent, module-to-distribution mapping failed, or dependency strategy is too narrow. | `SETTINGS.DISCOVER_DEPENDENCIES`; installed metadata; printed `Dependencies`. | Try `DISCOVER_DEPENDENCIES="sys"` or `"pkg"` before construction, install packages with metadata, or manually add package dependencies. |
| Import fails with `pkg_resources` or setuptools error | Sacred's dependency discovery imports `pkg_resources`, historically provided by setuptools. Newer setuptools releases may remove that API. | Python environment has setuptools; setuptools version compatibility; package metadata. | Install or repair setuptools in the active environment. If `pkg_resources` is absent, use a setuptools release that still provides it, then rerun. If package metadata is broken, pin/repair the package or manually add dependencies. |
| `--enforce_clean` says no version control detected | Git metadata was not collected. | `save_git_info`; GitPython/Git availability; source discovery; interactive mode; `print_dependencies` version-control section. | Run from tracked script files, install GitPython and Git, keep `save_git_info=True`, and confirm `print_dependencies` shows the repository before using `--enforce_clean`. |
| `--enforce_clean` fails because repository is dirty | Sacred detected uncommitted changes in a source repository. | Version-control section from `print_dependencies`; dirty marker. | Commit/stash/revert changes, or intentionally rerun without clean enforcement. |
| Git metadata collection fails before the run | GitPython or Git is unavailable while `save_git_info=True`. | Constructor error message; environment packages. | Install GitPython/Git, or pass `save_git_info=False` when Git metadata and `--enforce_clean` are not required. |
| Interactive notebook/repl experiment warns or loses sources | No reliable `__file__` main source exists. | Use of `interactive=True`; `run.experiment_info["sources"]`. | For reproducible runs, move the experiment to a script. If interactive use is unavoidable, explicitly name the experiment, accept weaker source capture, and add sources/dependencies manually. |
| TensorFlow `LogFileWriter` raises on import/use | TensorFlow is optional, missing, too old, or does not expose the expected v1 `summary.FileWriter` API. | TensorFlow import; `sacred.optional.has_tensorflow`; TensorFlow version; availability of `tensorflow.compat.v1.summary.FileWriter`. | Install a compatible TensorFlow, or skip `LogFileWriter`. Sacred's compatibility helper deprecates TensorFlow 1.12 and older and uses `compat.v1` for newer versions. |
| TensorFlow logdir list remains empty | `LogFileWriter` scope was entered outside a running experiment or the `FileWriter` call happened outside the decorator/context. | Placement of `LogFileWriter(ex)`; `ex.current_run`; `_run.info`. | Enter `LogFileWriter` only inside an active run and wrap the exact code that constructs `FileWriter` objects. |

## Reproducibility repair patterns

### Replace global PRNG use in a captured helper

```python
@ex.capture
def sample_batch(_seed, _rnd):
    try:
        idx = int(_rnd.integers(0, 1000))
    except AttributeError:
        idx = int(_rnd.randint(0, 1000))
    return idx
```

### Seed an unsupported library explicitly

```python
@ex.main
def main(seed):
    # Call the library's own seeding function here using `seed`.
    # Keep the exact library-specific deterministic flags near this call.
    pass
```

### Make captured-output assertions stable

```python
run = ex.run(
    config_updates={"seed": 123},
    options={"--capture": "sys", "--loglevel": "CRITICAL"},
)
assert "expected marker" in run.captured_out
```

### Restore process-global settings in tests

```python
import copy
from sacred import SETTINGS

saved = copy.deepcopy(SETTINGS)
try:
    SETTINGS.DISCOVER_SOURCES = "dir"
    # construct and run experiment here
finally:
    SETTINGS.DISCOVER_SOURCES = saved.DISCOVER_SOURCES
    SETTINGS.DISCOVER_DEPENDENCIES = saved.DISCOVER_DEPENDENCIES
    SETTINGS.CAPTURE_MODE = saved.CAPTURE_MODE
```

## Boundaries

- This guide covers how Sacred records and controls reproducibility-related state. It does not guarantee deterministic algorithms in external ML frameworks.
- Observer-specific files, database schemas, artifact storage, metric storage, and backend service failures belong in the observer/logging skill.
- Config update parsing, named config precedence, and config-file semantics belong in the configuration/CLI skill.
