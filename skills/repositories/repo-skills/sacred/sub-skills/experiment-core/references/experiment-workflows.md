# Sacred experiment-core workflows

This reference distills Sacred 0.8.7 core experiment behavior into reusable operating patterns. It intentionally avoids observer storage details, full CLI update syntax, and randomness/capture-mode policy, which belong to sibling sub-skills.

## 1. Minimal experiment shape

Use `Experiment` to register configuration, captured functions, commands, and a default command:

```python
from sacred import Experiment

ex = Experiment("train_model")

@ex.config
def cfg():
    learning_rate = 0.01
    epochs = 3

@ex.main
def run(learning_rate, epochs):
    return {"lr": learning_rate, "epochs": epochs}

if __name__ == "__main__":
    ex.run_commandline()
```

Key choices:

- `@ex.main` registers the default command but does not immediately run it.
- `@ex.automain` registers the default command and runs `ex.run_commandline()` automatically when the module is executed as `__main__`.
- Put `@ex.automain` at the end of an executable file so every helper, config scope, command, and ingredient is defined before the command-line run starts.
- In libraries, tests, notebooks, and orchestration scripts, prefer `@ex.main` and call `ex.run(...)` explicitly.

## 2. Programmatic runs

Use `ex.run(...)` when you need repeatable in-process runs:

```python
run = ex.run(
    command_name=None,                    # default command registered by @ex.main/@ex.automain
    config_updates={"learning_rate": 0.02},
    named_configs=(),
    info={"caller": "sweep"},
    meta_info={"trial": 1},
)
assert run.status == "COMPLETED"
print(run.result)
print(run.config)
```

`ex.run(...)` creates a new `Run`, executes it, returns the finished `Run`, and leaves useful state on the object: `result`, `config`, `status`, `start_time`, `stop_time`, `info`, `meta_info`, `captured_out`, and `fail_trace` if a failure was recorded.

Use `ex.run_commandline(argv)` when you are implementing an executable script wrapper or want Sacred to parse command names, named configs, config updates, and options from an argument vector. Keep detailed CLI update syntax in the configuration/CLI layer; this sub-skill only owns when to call `run_commandline`.

## 3. Captured functions and config injection

A captured function gets missing arguments from the active run configuration:

```python
@ex.config
def cfg():
    scale = 2
    message = "score"

@ex.capture
def format_score(value, scale, message="default"):
    return f"{message}={value * scale}"

@ex.main
def run():
    assert format_score(3) == "score=6"
    assert format_score(3, scale=10) == "score=30"
```

Injection priority is:

1. explicitly supplied positional or keyword arguments;
2. matching configuration values;
3. Python default values.

Implications:

- A config value can override a Python default, so defaults are fallbacks rather than authoritative experiment settings.
- Missing required parameters still raise argument errors if they are neither supplied nor present in config.
- Broad parameter names can hide bugs by being accidentally injected. Use specific names or `prefix=` when a helper should only see a config subtree.

Use `prefix=` to scope injection:

```python
@ex.config
def cfg():
    dataset = {"path": "input.txt", "batch_size": 16}

@ex.capture(prefix="dataset")
def load_dataset(path, batch_size):
    return path, batch_size
```

Dotted prefixes work for nested dictionaries.

## 4. Special captured arguments

Captured functions, main functions, commands, and hooks can accept special names:

- `_run`: current `Run` object; use for `info`, `add_artifact`, `log_scalar`, and direct lifecycle introspection.
- `_config`: config visible to the captured function. Treat it as read-only.
- `_log`: logger for the captured function or command.

Example:

```python
@ex.main
def run(_run, _config, _log):
    _log.info("running with %s", sorted(_config))
    _run.info["phase"] = "training"
    return 1
```

Randomness-related special arguments (`_seed`, `_rnd`) are handled by the reproducibility/capture layer.

## 5. Commands

Use commands for alternate entry points that share the same configuration system:

```python
@ex.command
def evaluate(checkpoint, threshold=0.5):
    return {"checkpoint": checkpoint, "threshold": threshold}
```

Rules:

- Commands are captured functions; they receive config injection and can use `_run`, `_config`, and `_log`.
- `@ex.command(unobserved=True)` is useful for helper commands that should not create observer records.
- `@ex.command(prefix="subtree")` restricts injection to a config subtree.
- Ingredient commands are addressed by dotted names such as `dataset.stats`.

Programmatic command run:

```python
run = ex.run(command_name="evaluate", config_updates={"checkpoint": "model.pt"})
assert run.result["checkpoint"] == "model.pt"
```

## 6. Ingredients for reusable modules

An `Ingredient` packages configuration, captured helpers, hooks, and commands for reuse:

```python
from sacred import Experiment, Ingredient

data = Ingredient("dataset")

data.add_config(filename="data.csv", normalize=True)

@data.capture
def load_data(filename, normalize):
    return {"filename": filename, "normalize": normalize}

@data.command
def stats(filename):
    return {"filename": filename}

ex = Experiment("pipeline", ingredients=[data])

@ex.main
def run():
    return load_data()
```

The ingredient config is visible under the ingredient path (`dataset.filename`, `dataset.normalize`). Captured functions defined on the ingredient receive values from that ingredient namespace. If an ingredient path contains dots, Sacred treats it as explicit nesting in the config tree.

Ingredients can depend on ingredients:

```python
paths = Ingredient("dataset.paths")
data = Ingredient("dataset", ingredients=[paths])
ex = Experiment("pipeline", ingredients=[data, paths])
```

Avoid circular ingredient graphs; traversal detects circular dependencies.

## 7. Hooks

Hooks are captured functions that let an experiment or ingredient participate in run setup/teardown:

```python
@ex.pre_run_hook
def before(_run):
    _run.info["prepared"] = True

@ex.post_run_hook
def after(_run):
    _run.info["finished_hook"] = True

@ex.config_hook
def hook(config, command_name, logger):
    if command_name == "run":
        config.update({"hooked": True})
    return config
```

Use hooks sparingly:

- `pre_run_hook` runs just before the main command function.
- `post_run_hook` runs just after the main command function if execution reaches that point.
- `config_hook` must have exactly `(config, command_name, logger)` and return a dictionary used to update config updates.
- Hooks are captured, so normal injection and read-only config rules apply.

## 8. Resources, artifacts, info, and metrics

Use resources for files consumed by a run and artifacts for files produced by a run. These calls are no-ops with respect to storage unless an observer is attached, but they still must be made during an active run.

```python
@ex.main
def run(_run):
    with ex.open_resource("input.txt", "r") as handle:
        text = handle.read()

    with open("result.txt", "w", encoding="utf-8") as handle:
        handle.write(text.upper())

    ex.add_artifact("result.txt", name="result.txt", metadata={"kind": "demo"})
    _run.info["num_chars"] = len(text)
    _run.log_scalar("text.length", len(text), step=0)
    return len(text)
```

Prefer `_run.add_artifact(...)` and `_run.log_scalar(...)` inside deeply nested captured helpers when passing the `Experiment` object would create a global dependency. Prefer `ex.open_resource(...)`/`ex.add_resource(...)` when the experiment object is already in module scope.

## 9. Interactive and notebook execution

Sacred rejects interactive experiment definitions by default because source capture and reproducibility cannot be guaranteed. For notebooks, REPLs, and dynamic scripts, create an explicitly named experiment:

```python
ex = Experiment("notebook_experiment", interactive=True)
```

Do not use `@ex.automain` in interactive mode. Use `@ex.main` and run `ex.run(...)` explicitly.
