# CLI reference

## Safe discovery commands

These commands only inspect help text and are the safest way to learn the interface:

- `python -m dataflow.cli --help`
- `python -m dataflow.cli init --help`
- `python -m dataflow.cli init repo --help`
- `python -m dataflow.cli chat --help`
- `python -m dataflow.cli eval --help`
- `python -m dataflow.cli eval init --help`
- `python -m dataflow.cli eval api --help`
- `python -m dataflow.cli eval local --help`
- `python -m dataflow.cli pdf2model --help`
- `python -m dataflow.cli pdf2model init --help`
- `python -m dataflow.cli pdf2model train --help`
- `python -m dataflow.cli text2model --help`
- `python -m dataflow.cli text2model init --help`
- `python -m dataflow.cli text2model train --help`
- `python -m dataflow.cli webui --help`

## Root CLI behavior

- `dataflow -v` prints the package version and may also trigger an update check.
- `dataflow env` prints environment details, but it is not safe in a non-TTY shell because the implementation calls `os.get_terminal_size()`.
- The root command groups the major workflows into `env`, `chat`, `webui`, `init`, `eval`, `pdf2model`, and `text2model`.

## `init`

### `dataflow init`

- With no subcommand, the default route is the `base` initializer.
- The base initializer copies built-in pipelines, example data, and playground files into the current working directory.
- It is a file-writing setup step, not a training or serving step.

### `dataflow init repo`

- Creates a new DataFlow repository scaffold in the current working directory.
- Uses the built-in cookiecutter scaffold template.
- `--no-input` disables interactive prompts.
- This command can create or overwrite files and should be treated as a project bootstrap step.

### Placeholder init subcommands

- `operator`
- `pipeline`
- `prompt`

These are present in the CLI but are placeholders.

## `chat`

- Options:
  - `--model PATH`: explicit model or adapter path
  - `--cache PATH`: cache directory, default `.`
- Routing order:
  1. explicit `--model`
  2. adapter files in the current directory
  3. latest cached adapter under `<cache>/.cache/saves`
  4. base model fallback through `llamafactory-cli chat`
- Adapter detection looks for:
  - `adapter_config.json`
  - `adapter_model.bin`
  - `adapter_model.safetensors`
- If the selected path is a fine-tuned adapter, the wrapper launches `llamafactory-cli chat --model_name_or_path <base> --adapter_name_or_path <adapter>`.
- If the selected path is a base model, the wrapper falls back to `llamafactory-cli chat` directly.

## `eval`

### `dataflow eval init`

- Copies `eval_api.py` and `eval_local.py` into the current working directory.
- Prompts before overwriting existing files.
- This is a template bootstrap command, not an evaluation run.

### `dataflow eval api`

- Loads `eval_api.py` from the current working directory.
- Expects that file to export `get_evaluator_config()`.
- Runs the returned configuration through the evaluation pipeline.

### `dataflow eval local`

- Loads `eval_local.py` from the current working directory.
- Expects that file to export `get_evaluator_config()`.
- Runs the returned configuration through the evaluation pipeline.

### Template contract

The evaluation templates use a configuration dictionary that typically includes:

- `JUDGE_MODEL_CONFIG`
- `TARGET_MODELS`
- `BENCH_CONFIG`
- `EVAL_CONFIG`
- `EVALUATOR_RUN_CONFIG`
- `create_judge_serving`
- `create_evaluator`
- `create_storage`

## `pdf2model`

### `dataflow pdf2model init`

- Options:
  - `--cache PATH`
  - `--qa vqa|kbc`
  - `--model TEXT`
  - `--train-backend TEXT`
- `vqa` only supports `--train-backend base`.
- `kbc` supports `base` and registered `dataflex-*` backends.
- This command prepares a PDF-to-model workspace and writes training configuration files.

### `dataflow pdf2model train`

- Options:
  - `--cache PATH`
  - `--lf-yaml PATH`
- Uses the cached training state when available.
- May launch LlamaFactory or a DataFlex backend, depending on the saved workspace state.
- This is a training command with file generation, downloads, and model execution side effects.

## `text2model`

### `dataflow text2model init`

- Options:
  - `--cache PATH`
- Prepares the text-to-model workspace and writes a training config.
- The command is setup-only, but it verifies the environment before proceeding.

### `dataflow text2model train`

- Arguments and options:
  - `INPUT_DIR` positional argument, default `.`
  - `--input-keys TEXT`
  - `--lf-yaml PATH`
- Merges JSON / JSONL inputs and then launches the training workflow.
- Side effects include cache creation, data conversion, and model training.

## `webui`

- Options:
  - `--zip-path PATH`
  - `--webui-path PATH`
  - `--host TEXT`, default `0.0.0.0`
  - `--port INTEGER`, default `8000`
- Without `--zip-path` or `--webui-path`, the command fetches the latest `OpenDCAI/DataFlow-WebUI` release from GitHub.
- It then installs the backend requirements into the current Python environment and launches `uvicorn app.main:app --reload`.
- Browser launch is attempted automatically once the server responds.
- This command has download, install, and service-start side effects and is not a dry run.
