# CLI Reference

## Top-Level Commands

Installed CLI commands in 0.0.12:

- `opyrator call`
- `opyrator export`
- `opyrator deploy`
- `opyrator launch-api`
- `opyrator launch-ui`

This sub-skill only owns the first three commands. Route `launch-api` and `launch-ui` to the API/UI sub-skills.

## `opyrator call`

Help surface:

```text
Usage: opyrator call [OPTIONS] OPYRATOR INPUT_DATA
```

Arguments:

- `OPYRATOR`: required callable import string, such as `my_module:hello_world`
- `INPUT_DATA`: required JSON string

Behavior from source:

- Adds the current working directory to `sys.path` before resolving the callable.
- Builds `Opyrator(opyrator)` and immediately calls it with the provided JSON string.
- Prints `output.json(indent=4)` when the returned object is truthy.
- Prints `Nothing returned!` when the returned object is falsy.
- Catches `pydantic.error_wrappers.ValidationError` and prints the validation text to stderr.

Practical notes:

- Use single quotes around the JSON payload on POSIX shells to keep the shell from rewriting double quotes.
- The CLI expects a local importable module or callable instance; it does not start any server.
- When debugging a failed call, inspect stderr first for Pydantic validation text, then inspect import errors and tracebacks.

Example:

```bash
opyrator call my_module:hello_world '{"message": "hello"}'
```

## `opyrator export`

Help surface:

```text
Usage: opyrator export [OPTIONS] OPYRATOR EXPORT_NAME
```

Arguments:

- `OPYRATOR`: required callable import string
- `EXPORT_NAME`: required export target name

Options:

- `--format [docker|pex|zip]` with default `zip`

Observed 0.0.12 behavior:

- `zip` prints the WIP warning for the ZIP placeholder.
- `docker` prints the WIP warning for the Docker placeholder.
- `pex` prints the WIP warning for the PEX placeholder.
- No export artifact is produced by the current implementation.

Safe checks:

```bash
opyrator export --help
opyrator export my_module:hello_world my-opyrator.zip
opyrator export my_module:hello_world my-image:latest --format docker
opyrator export my_module:hello_world my-opyrator.pex --format pex
```

## `opyrator deploy`

Help surface:

```text
Usage: opyrator deploy [OPTIONS] OPYRATOR
```

Arguments:

- `OPYRATOR`: required callable import string

Observed 0.0.12 behavior:

- Prints the same WIP warning every time.
- Does not contact a cloud provider or create a deployment.
- There is no provider argument in the verified CLI surface.

Safe check:

```bash
opyrator deploy --help
opyrator deploy my_module:hello_world
```

## `launch-api` And `launch-ui`

These commands exist in the installed CLI but belong to the API/UI sub-skills.

- `launch-api`: starts the FastAPI server for a wrapped callable.
- `launch-ui`: starts the Streamlit UI for a wrapped callable.

Their help surfaces are useful for command discovery, but do not use this sub-skill to plan or debug their server behavior.

## Expected Help Signals

The verified help output for `call`, `export`, `deploy`, `launch-api`, and `launch-ui` shows the command name, required positional arguments, and the current option surface.

The most important distinction for this sub-skill is:

- `call` executes a local wrapper and prints JSON or a validation message.
- `export` and `deploy` are WIP placeholders.
