# Installation and CLI

Use this reference for package install, version checks, and the top-level `python -m deeppavlov` command surface.

## Install

Preferred public install:

```bash
python -m pip install deeppavlov
```

If you are working from a local source checkout, use editable install from that checkout instead of relying on the generated skill tree.

## Verified package facts

- Public distribution name: `deeppavlov`
- Verified version in inspection: `1.7.0`
- The package exposes the `deeppavlov` module and the `python -m deeppavlov` CLI entry point.
- Supported CLI modes in the shipped parser: `train`, `evaluate`, `interact`, `predict`, `riseapi`, `risesocket`, `download`, `install`, `crossval`.

## Minimal smoke check

Run the bundled smoke helper after install:

```bash
python scripts/smoke_deeppavlov_pipeline.py
```

Expected result: a tiny lowercasing/tokenization pipeline that returns `[['hello', 'world']]` for the default input.

## Top-level CLI reminders

- `install <config>` installs requirement files declared by the config and its nested configs.
- `download <config>` downloads resources declared by the config and nested configs.
- `train <config>` trains the configured pipeline; `-d` downloads resources first and `-i` installs requirements first.
- `evaluate <config>` evaluates without training.
- `interact <config>` prompts interactively one input at a time.
- `predict <config>` reads batches from stdin or a file.
- `crossval <config> --folds N` runs fold-based evaluation over the union of train and valid data.
- `paramsearch` is a separate module (`python -m deeppavlov.paramsearch`) and currently implements grid search over `search_choice` values.

## Environment variables that commonly change behavior

- `DP_SETTINGS_PATH`: custom settings directory.
- `DP_ROOT_PATH`: common root for downloaded resources.
- `DP_CONFIGS_PATH`: alternate config tree location.
- `DP_SKIP_NLTK_DOWNLOAD=TRUE`: suppress automatic NLTK downloads.
- `COMPATIBILITY_MODE`: legacy REST response format bridge.

## When to read this

Read this page first when the task is about installing DeepPavlov, confirming the CLI, or deciding which command mode to use before diving into a specific sub-skill.
