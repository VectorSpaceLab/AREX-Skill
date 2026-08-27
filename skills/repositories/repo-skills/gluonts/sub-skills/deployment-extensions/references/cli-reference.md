# GluonTS CLI reference

## Package CLI

The installed package exposes a Click command group through:

```bash
python -m gluonts --help
python -m gluonts version
```

Expected shape:

- `--help` lists the `version` command.
- `version` prints `gluonts.__version__` for the installed distribution.
- If `click` is missing, the CLI exits before running the command. Installing the `shell` extra normally brings Click transitively through Flask; otherwise install Click in the active environment.

Use this command as the first runtime sanity check when the user asks which GluonTS version is active. The inspected package reported `0.18.0.dev0`, but future agents should rely on the target environment command instead of assuming that exact value.

## Shell CLI

The deployment shell command group is:

```bash
python -m gluonts.shell --help
python -m gluonts.shell train --help
python -m gluonts.shell serve --help
```

The command group imports `click` and `waitress`; serving imports Flask through the shell package. Install `gluonts[shell]` when help or serving fails because `flask` or `waitress` is missing.

### `train` command

```bash
python -m gluonts.shell train --data-path DATA_PATH --forecaster FULLY.QUALIFIED.CLASS
```

Options:

| Option | Environment variable | Meaning |
| --- | --- | --- |
| `--data-path` | `SAGEMAKER_DATA_PATH` | Root of SageMaker-style mounted folders; defaults to the standard container data root. |
| `--forecaster` | `GLUONTS_FORECASTER` | Fully qualified import path of an `Estimator` or `Predictor`. If omitted, the shell reads `forecaster_name` from hyperparameters. |

The class name is resolved with Python import lookup. Prefer full import paths such as `gluonts.model.trivial.mean.MeanPredictor` or `gluonts.ext.prophet.ProphetPredictor` rather than ambiguous aliases.

### `serve` command

```bash
python -m gluonts.shell serve --data-path DATA_PATH --forecaster FULLY.QUALIFIED.PREDICTOR
```

Options:

| Option | Environment variable | Meaning |
| --- | --- | --- |
| `--data-path` | `SAGEMAKER_DATA_PATH` | Root of model/output folders; defaults to the standard container data root. |
| `--forecaster` | `GLUONTS_FORECASTER` | Enables dynamic mode: construct a predictor per request from `configuration`. |
| `--force-static / --no-force-static` | `GLUONTS_FORCE_STATIC` | Force static mode even when a forecaster is configured. |

Static mode deserializes an already trained predictor from the model directory. Dynamic mode requires a predictor class whose `from_hyperparameters` constructor can consume the request `configuration`.

## Recommended preflight sequence

1. `python -m gluonts version` to confirm the installed package.
2. `python -m gluonts.shell --help` to confirm shell dependencies.
3. `python -m gluonts.shell train --help` and `python -m gluonts.shell serve --help` to confirm dispatch commands.
4. Validate a representative inference request with `shell_payload_validator.py` before sending it to a local or hosted endpoint.
