# Snips NLU CLI Reference

This reference is self-contained command-construction guidance for the Snips NLU
CLI. The package exposes two equivalent entry points:

```bash
snips-nlu <command> [options]
python -m snips_nlu <command> [options]
```

Use `python -m snips_nlu` as the examples' default because it follows the active
Python interpreter. Replace it with `snips-nlu` only when the console script is
available in the intended environment.

## Safe Availability Checks

```bash
python -m snips_nlu --help
python -m snips_nlu version
python -m snips_nlu model-version
python -m snips_nlu generate-dataset --help
python -m snips_nlu train --help
python -m snips_nlu parse --help
```

The bundled smoke helper runs these checks plus the remaining subcommand help
screens without training or downloading:

```bash
python scripts/snips_nlu_cli_smoke.py --entrypoint auto
```

## Command Catalog

| Workflow | Verified command grammar | Operational notes |
| --- | --- | --- |
| Generate dataset JSON | `generate-dataset language files...` | Reads one or more intent/entity YAML files and prints JSON to stdout. Redirect stdout to create a dataset file. Dataset schema details are owned by `../dataset-and-resources/SKILL.md`. |
| Train engine | `train [-c CONFIG_PATH] [-r RANDOM_SEED] [-v] dataset_path output_path` | Reads dataset JSON, optional NLU config JSON, trains an engine, and persists a new engine directory. `-v` may be repeated as `-vv`. `output_path` must not already exist. |
| Parse with trained engine | `parse [-q QUERY] [-v] [-f INTENTS_FILTER] training_path` | Loads a persisted engine directory. With `-q`, prints one JSON parse result and exits. Without `-q`, starts an interactive prompt. |
| Download language resources | `download [-d] resource_name [extra_pip_args...]` | Installs compatible language resources by shortcut such as `en` or full package name such as `snips_nlu_en`. `-d` forces a direct download and requires a full resource name with version. |
| Download all languages | `download-all-languages [extra_pip_args...]` | Network-heavy; loops over all supported languages. Avoid unless the task explicitly needs broad language coverage. |
| Download one builtin entity | `download-entity entity language [extra_pip_args...]` | Downloads the language resources first, then the requested builtin gazetteer entity such as `snips/musicArtist`. |
| Download all builtin entities for a language | `download-language-entities language [extra_pip_args...]` | Downloads language resources first, then all supported gazetteer entities for that language. Network-heavy. |
| Link resources manually | `link [-f] origin link_name` | Creates a resource symlink from an installed resource package name or a local resource directory. Use `-f` only to replace an existing symlink. |
| Cross-validation metrics | `cross-val-metrics [-c CONFIG_PATH] [-n NB_FOLDS] [-t TRAIN_SIZE_RATIO] [-s] [-i] [-v] dataset_path output_path` | See `evaluation.md`; requires the optional metrics package at execution time. |
| Train/test metrics | `train-test-metrics [-c CONFIG_PATH] [-s] [-i] [-v] train_dataset_path test_dataset_path output_path` | See `evaluation.md`; requires the optional metrics package at execution time. |
| Package version | `version` | Prints the installed Snips NLU package version. |
| Model version | `model-version` | Prints the persisted-model compatibility version. |

## Dataset Generation

Generate dataset JSON from YAML definitions and validate that the result is
well-formed JSON:

```bash
python -m snips_nlu generate-dataset en intents.yaml entities.yaml > dataset.json
python -m json.tool dataset.json >/dev/null
```

Notes:

- `language` is the dataset language code, for example `en`.
- `files...` can be separate intent/entity YAML files or a smaller number of
  combined YAML files.
- The command writes the dataset to stdout, not to a file path argument.
- If a YAML file references builtin entities or language-specific resources,
  prepare those resources before training/parsing; route schema and resource
  naming questions to `../dataset-and-resources/SKILL.md`.

## Training

Basic training:

```bash
python -m snips_nlu train dataset.json trained_engine
```

Reproducible and more verbose training:

```bash
python -m snips_nlu train -r 42 -v dataset.json trained_engine
```

Training with an engine config JSON:

```bash
python -m snips_nlu train -c nlu_config.json -r 42 dataset.json trained_engine
```

Operational rules:

- `dataset_path` is JSON produced by `generate-dataset` or the equivalent
  dataset API.
- `output_path` is a directory that Snips NLU creates while persisting the
  engine. It must not exist before the command starts.
- `-c/--config_path` points to a JSON representation of the NLU engine
  configuration. Programmatic config construction belongs in
  `../engine-api/SKILL.md`.
- `-r/--random_seed` is an integer seed passed to the training random state.
- `-v/--verbosity` may be repeated (`-vv`) to increase logging.

After training, a quick structural check is:

```bash
test -f trained_engine/nlu_engine.json
python -m snips_nlu parse trained_engine -q "test utterance"
```

The parse check requires the trained engine's resources to be loadable. If this
fails, see `troubleshooting.md` before assuming the dataset is invalid.

## Parsing

One-shot parse:

```bash
python -m snips_nlu parse trained_engine -q "Make me two cups of coffee"
```

Interactive prompt:

```bash
python -m snips_nlu parse trained_engine
```

Increase parse-time logging:

```bash
python -m snips_nlu parse -v trained_engine -q "Make me two cups of coffee"
```

Restrict parsing to a subset of intents:

```bash
python -m snips_nlu parse trained_engine -q "Make me tea" -f MakeTea,MakeCoffee
```

The `-f/--intents-filter` value is parsed as one CSV string. If an intent name
contains a comma, quote that intent inside one shell argument:

```bash
python -m snips_nlu parse trained_engine -q "Make coffee" -f 'MakeTea,"Make,Coffee"'
```

Do not split the filter into multiple `-f` flags; the CLI expects one comma
separated value.

## Resource Download and Linking Commands

Language resource setup usually requires network access and modifies the active
Python environment by invoking pip. Get user approval before downloading in a
managed or shared environment.

Download compatible language resources by shortcut:

```bash
python -m snips_nlu download en
```

Download by full resource package name:

```bash
python -m snips_nlu download snips_nlu_en
```

Force a direct download when you already know the full resource name and
version:

```bash
python -m snips_nlu download -d snips_nlu_en-<version>
```

Pass extra pip arguments after `--` when they start with a dash:

```bash
python -m snips_nlu download en -- --user
python -m snips_nlu download en -- --no-cache-dir
```

Download builtin gazetteer resources:

```bash
python -m snips_nlu download-entity snips/musicArtist en
python -m snips_nlu download-language-entities en
```

Download every supported language only for broad setup tasks:

```bash
python -m snips_nlu download-all-languages
```

Manually link an installed resource package or local resource directory:

```bash
python -m snips_nlu link snips_nlu_en en
python -m snips_nlu link <resources-dir> en
python -m snips_nlu link -f snips_nlu_en en
```

The link name is the resource alias used by Snips NLU resource loading. `-f`
replaces an existing symlink but does not safely overwrite a normal file or
directory.

## Version Commands

```bash
python -m snips_nlu version
python -m snips_nlu model-version
```

Use `version` to confirm package installation. Use `model-version` when a
persisted engine cannot be loaded or when checking compatibility between a
trained engine and the runtime package.
