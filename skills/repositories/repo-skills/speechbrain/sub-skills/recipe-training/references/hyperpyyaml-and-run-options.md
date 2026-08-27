# HyperPyYAML, `RunOptions`, and `Brain`

Use this reference when modifying hparams files, command-line overrides, runtime options, or recipe scripts.

## Verified key signatures

```python
speechbrain.Brain.__init__(modules=None, opt_class=None, hparams=None, run_opts=None, checkpointer=None)
speechbrain.Brain.fit(epoch_counter, train_set, valid_set=None, progressbar=None, train_loader_kwargs={}, valid_loader_kwargs={})
speechbrain.Brain.evaluate(test_set, max_key=None, min_key=None, progressbar=None, test_loader_kwargs={})
speechbrain.core.create_experiment_directory(experiment_directory, hyperparams_to_save=None, overrides={}, log_config=..., save_env_desc=True)
speechbrain.utils.run_opts.RunOptions.from_command_line_args(arg_list=None)
```

## HyperPyYAML essentials

HyperPyYAML extends YAML with object construction and references. Common tags:

```yaml
seed: !PLACEHOLDER
output_folder: !ref results/<seed>
model: !new:speechbrain.nnet.linear.Linear
    input_size: 40
    n_neurons: 10
optimizer: !name:torch.optim.Adam
    lr: 0.001
```

- `!PLACEHOLDER` must be supplied by CLI override or editing the YAML.
- `!ref <name>` interpolates another YAML value.
- `!new:module.Class` constructs an object.
- `!name:module.symbol` stores a callable/class without constructing it.
- `!apply:module.function` calls a function.

Security rule: loading a HyperPyYAML file can execute Python constructors. Treat untrusted recipes as code.

## Command-line parsing behavior

`RunOptions.from_command_line_args` returns `(filename, run_opts, overrides)`.

Example verified behavior:

```python
from speechbrain.utils.run_opts import RunOptions
filename, run_opts, overrides = RunOptions.from_command_line_args(
    ["params.yaml", "--device=cpu", "--seed=3", "--data_folder", "TIMIT"]
)
assert filename == "params.yaml"
assert run_opts["device"] == "cpu"
assert overrides == "seed: 3\ndata_folder: TIMIT"
```

Known runtime options are stored in `run_opts`; unknown names become HyperPyYAML override text.

## `Brain` subclass pattern

A minimal recipe subclass overrides at least:

```python
class MyBrain(sb.Brain):
    def compute_forward(self, batch, stage):
        batch = batch.to(self.device)
        # compute model outputs
        return outputs

    def compute_objectives(self, predictions, batch, stage):
        # compute loss and optionally metrics
        return loss
```

Common optional hooks:

- `on_stage_start(stage, epoch=None)`
- `on_stage_end(stage, stage_loss, epoch=None)`
- `fit_batch(batch)`
- `evaluate_batch(batch, stage)`
- `on_evaluate_start(max_key=None, min_key=None)`
- `on_fit_start()`

## Experiment directory pattern

Recipes usually call:

```python
sb.create_experiment_directory(
    experiment_directory=hparams["output_folder"],
    hyperparams_to_save=hparams_file,
    overrides=overrides,
)
```

This writes a resolved hparams copy, logging setup, current script copy, and optional environment description. Avoid writing outputs into source directories unless the recipe documents it.

## Common mistakes

- Passing runtime flags before the hparams file.
- Forgetting to replace `!PLACEHOLDER` values.
- Mixing Python booleans and YAML/string overrides (`--skip_prep=True` versus `--skip_prep true`); use the recipe's tested form when available.
- Hard-coding `cuda` in recipe code rather than using `self.device`.
- Changing a Python signature without updating every HyperPyYAML `!new` or `!name` use.
