# W&B Sweeps

## When to use sweeps

Use W&B Sweeps when the user needs W&B to coordinate hyperparameter search runs. A sweep has two parts:

1. A sweep configuration that declares the search method, optimized metric, and parameter space.
2. One or more agents that poll W&B for assignments and run the training entry point.

For basic metrics logging inside the training script, route to the experiment-tracking material instead of this sub-skill.

## Minimal sweep config shape

A practical sweep config should include:

```yaml
method: bayes
metric:
  name: val_loss
  goal: minimize
parameters:
  learning_rate:
    min: 0.0001
    max: 0.1
  batch_size:
    values: [16, 32, 64]
program: train.py
```

Key rules:

- `method` is required for normal sweeps. Common values include `grid`, `random`, `bayes`, and `custom`.
- `metric` should be a mapping with at least `name`; include `goal: minimize` or `goal: maximize` for optimization methods.
- `parameters` must be a mapping from parameter names to specs.
- Each parameter spec should use one of the supported shapes such as `value`, `values`, `min`/`max`, or distribution-style keys.
- `program` is needed when the agent launches a process from the config. Omit it when you call `wandb.agent(..., function=train)` from Python.
- To prevent accidental unbounded work, add an agent `count`; do not try to limit total runs solely by leaving agents unattended.

Run the bundled offline validator before registration:

```bash
python scripts/validate_sweep_config.py sweep.yaml
```

The validator checks only safe structural requirements; W&B may still reject backend-specific or advanced sweep options during registration.

## Python SDK workflow

Use `wandb.sweep(sweep, entity=None, project=None, prior_runs=None) -> str` to register a sweep and receive a sweep ID.

```python
import wandb

sweep_config = {
    "method": "random",
    "metric": {"name": "val_accuracy", "goal": "maximize"},
    "parameters": {
        "learning_rate": {"min": 1e-5, "max": 1e-2},
        "dropout": {"values": [0.0, 0.1, 0.2]},
    },
}

sweep_id = wandb.sweep(sweep_config, entity="team", project="project")
```

Use `wandb.agent(sweep_id, function=None, entity=None, project=None, count=None, forward_signals=False) -> None` to run assignments. Prefer a finite `count` during development:

```python
def train():
    with wandb.init() as run:
        config = run.config
        # Build/train/evaluate using config.learning_rate, config.dropout, etc.
        run.log({"val_accuracy": 0.91})

wandb.agent(sweep_id, function=train, entity="team", project="project", count=5)
```

Important SDK details:

- `wandb.sweep` accepts a config dictionary or a no-argument callable that returns one.
- If `project` is omitted and the sweep config has `project`, the SDK can use the config value.
- `prior_runs` attaches existing run IDs to a new sweep.
- `forward_signals` is documented on `wandb.agent`, but signal forwarding is only supported by the CLI agent; use `wandb agent --forward-signals` for process signal propagation.

## CLI workflow

Create a sweep from YAML:

```bash
wandb sweep -p project -e entity sweep.yaml
```

Useful creation/update flags:

- `--project` / `-p`: set the project; defaults to `Uncategorized` if not otherwise configured.
- `--entity` / `-e`: set the entity; defaults to the current authenticated user/team settings.
- `--name`: set a display name.
- `--program`: override the training program in the config.
- `--prior_run` / `-R`: attach existing run IDs; repeat for multiple runs.
- `--controller`: start a local sweep controller after creating the sweep.
- `--update SWEEP_ID`: update an existing sweep from a config.

Manage existing sweeps by passing a sweep ID or `entity/project/sweep_id`:

```bash
wandb sweep --pause entity/project/sweep_id
wandb sweep --resume entity/project/sweep_id
wandb sweep --stop entity/project/sweep_id
wandb sweep --cancel entity/project/sweep_id
```

Run agents:

```bash
wandb agent --count 10 -p project -e entity entity/project/sweep_id
```

Useful agent flags:

- `--count INTEGER`: maximum runs this agent executes. If omitted, it continues until the sweep completes, stops, or is cancelled.
- `--project` / `-p` and `--entity` / `-e`: override destination scope.
- `--forward-signals` / `-f`: forward SIGINT/SIGTERM-style signals to child runs for cleaner shutdown.

## Choosing `program` versus `function`

Use a config `program` when:

- The user already has a runnable training script.
- The agent will be started with the CLI.
- The sweep config should be portable between machines or workers.

Use a Python `function` when:

- The sweep is started from a notebook, test harness, or local Python driver.
- The user wants to call a function directly without spawning a script.
- The training function owns `wandb.init()` and reads `run.config`.

Avoid mixing these expectations. A CLI sweep without `program` often cannot launch work; a Python `wandb.agent(..., function=train)` does not need `program`.

## Repairing an indefinite sweep YAML

If a user provides a valid config but asks to avoid runaway execution, do not add a nonstandard top-level `count` and assume W&B will enforce it. Keep the sweep config focused on search definition, then bound the agent:

```bash
wandb sweep sweep.yaml
wandb agent --count 20 entity/project/sweep_id
```

For Python:

```python
sweep_id = wandb.sweep(sweep_config, project="project")
wandb.agent(sweep_id, function=train, count=20)
```
