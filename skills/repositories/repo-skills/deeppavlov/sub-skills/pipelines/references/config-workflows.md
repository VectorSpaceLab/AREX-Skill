# Config Workflows

Use this reference when you need to choose the right DeepPavlov CLI mode,
translate a config into a runnable pipeline, or decide how to shape a training
config before touching model-family-specific details.

## Fast Decision Guide

- Need a trained or inference-ready model object in Python: use `build_model` or
  `train_model`.
- Need only metrics: use `evaluate_model` or
  `train_evaluate_model_from_config(..., to_train=False)`.
- Need a one-off safe config inspection before downloads or installs: run
  `scripts/inspect_config_requirements.py <config>`.
- Need terminal prompting: use `interact`.
- Need stdin or file batch inference: use `predict`.
- Need fold-based evaluation over train/valid data: use `crossval`.
- Need hyperparameter search over config choices: use `python -m
  deeppavlov.paramsearch`.

## CLI Modes

| Mode | Typical command | What happens |
| --- | --- | --- |
| `install` | `python -m deeppavlov install <config>` | Installs requirement files declared by the config and nested configs. |
| `download` | `python -m deeppavlov download <config>` | Downloads resources declared in `metadata.download` and nested configs. |
| `train` | `python -m deeppavlov train <config> [-d] [-i] [--recursive] [-e N]` | Trains the configured pipeline. `-i` installs requirements first, `-d` downloads resources first, and `-e` resumes from the given epoch number. |
| `evaluate` | `python -m deeppavlov evaluate <config> [-d] [-i] [-e N]` | Runs evaluation without training. `-e` sets the starting epoch number when the trainer supports it. |
| `interact` | `python -m deeppavlov interact <config> [-d] [-i]` | Opens a prompt loop and feeds one input sample at a time. |
| `predict` | `python -m deeppavlov predict <config> [-b N] [-f FILE] [-d] [-i]` | Reads batches from stdin or a file and prints JSON lines. |
| `crossval` | `python -m deeppavlov crossval <config> --folds N` | Runs plain cross-validation over the union of train and valid data. |
| `paramsearch` | `python -m deeppavlov.paramsearch <config> --folds N|loo` | Runs grid search over `search_choice` values and writes a best-config file. |

### Practical notes

- `predict` is stream mode, not interactive mode. If the input is a terminal
  TTY, the CLI raises an error telling you to use `interact` instead.
- For multi-input configs, `predict` reads `batch_size × number_of_inputs`
  lines at a time and groups them by input position before calling the model.
- `interact` prompts once per input name and accepts `exit`, `stop`, `quit`, or
  `q` to leave the loop.
- `crossval` via the main CLI requires `--folds >= 2`.
- `paramsearch` currently implements grid search only. Other search types are
  not implemented in the shipped module.
- The parameter-search output file is produced by `Path.with_suffix('.cvbest.json')`.
  If you look for a legacy `_cvbest.json` filename, you may miss the file.

## Minimal Config Shape

A pipeline config must center on a `chainer` section:

```json
{
  "metadata": {
    "variables": {
      "ROOT_PATH": "~/.deeppavlov"
    }
  },
  "chainer": {
    "in": ["x"],
    "pipe": [
      {
        "class_name": "str_lower",
        "in": ["x"],
        "out": ["x_lower"]
      }
    ],
    "out": ["x_lower"]
  }
}
```

Add `dataset_reader`, `dataset_iterator`, and `train` when the pipeline should
train or evaluate on data.

## Nested Configs

Use `config_path` when one component should embed another config or when a
sub-pipeline should be reused.

- `overwrite` applies before the nested config is built.
- Use dot notation such as `chainer.out` or `chainer.pipe.1.class_name`.
- List positions are numeric path segments.
- A nested config may itself contain more `config_path` references.

A good workflow is:

1. Inspect the nested config first.
2. Override only the fields you need.
3. Keep the outer config focused on orchestration.

## Variables and Environment Overrides

DeepPavlov resolves config strings as format strings.

- `metadata.variables` defines named placeholders.
- `DP_<VARIABLE_NAME>` overrides the matching variable.
- `DP_ROOT_PATH` is commonly used to relocate downloaded resources.
- `DP_DEEPPAVLOV_PATH` can override the built-in package root variable when a
  config derives paths from `DEEPPAVLOV_PATH`.

If a path looks right in the JSON but resolves incorrectly at runtime, inspect
those variable layers before changing the model itself.

## Training Configs

Training and evaluation configs usually need:

- `dataset_reader`: how to read the raw dataset.
- `dataset_iterator`: how to batch or split the dataset.
- `train`: trainer options and metrics.

Component-level fields matter too:

- `fit_on` marks estimator inputs.
- `in_y` marks supervised targets.
- `save_path` / `load_path` control persistence.
- `main` identifies the component that should be treated as the pipeline’s main
  trainable output.

If you only need a quick classification-style training layout, the legacy
`dataset` shortcut expands to the built-in basic classification reader and
iterator. Other workflows should use explicit reader and iterator sections.

## Recursive Training

`recursive=True` walks the outer config for nested `config_path` values and
trains those nested configs before the outer one.

Use this when a top-level config is mostly orchestration and the reusable nested
pieces themselves also need training.

Do not use recursive training as a substitute for correct config ownership.
If the nested config is really a model-family concern, route that detail to the
relevant sibling sub-skill instead of burying it here.

## Safe Inspection First

When you only need to understand a config before deciding what to run:

```bash
python scripts/inspect_config_requirements.py <config_path>
```

That helper prints the resolved config path, `chainer` endpoints, discovered
component classes, nested config references, requirement files, and download
references without triggering downloads or installs.
