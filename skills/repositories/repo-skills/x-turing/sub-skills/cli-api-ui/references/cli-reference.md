# CLI reference

## Top-level command

`xturing` is a Click group with these visible commands:

- `api`
- `chat`
- `ui`

Help-derived flags:

- `xturing --version`
- `xturing -h`
- `xturing --help`
- `xturing chat -h` / `--help`
- `xturing api -h` / `--help`
- `xturing ui -h` / `--help`

## `xturing chat`

```bash
xturing chat -m <model_name_or_path>
```

Required option:

- `-m`, `--model_name_or_path` — model key or path to a model directory containing `xturing.json`

Behavior:

- if the value is a directory, xTuring loads it as a saved model directory
- otherwise, xTuring treats it as a model key and tries to create a model from the registry
- on success, the command enters a `USER >` / `MODEL >` loop
- on invalid input, the command prints a short invalid-model message and exits

Notes:

- this command is interactive and blocks on stdin
- use the API server when you need automation or remote access

## `xturing api`

```bash
xturing api -m <model_path>
```

Required option:

- `-m`, `--model_path` — path to a model directory containing `xturing.json`

Behavior:

- loads the model once
- starts Uvicorn on port `5000`
- uses one worker
- rejects non-directory paths immediately

Notes:

- this CLI does not expose a port flag
- it is intended for saved xTuring model directories, not bare model keys

## `xturing ui`

```bash
xturing ui
```

Behavior:

- launches the Gradio playground
- takes no CLI options besides help/version on the wrapper
- for a prefilled path in code, use `Playground(model_path="...").launch()`
