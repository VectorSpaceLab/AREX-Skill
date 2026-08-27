---
name: wrapping-and-cli
description: "Wrap Python callables with Opyrator, validate the Pydantic
  input/output contract, call wrapped functions from JSON/dict or the CLI, and
  recognize export/deploy WIP placeholders."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Opyrator Wrapping And CLI

Use this sub-skill when the user wants to turn a Python callable into an `Opyrator`, resolve an import string such as `my_module:hello_world`, understand why a callable is rejected, call a wrapped function from Python or the `opyrator call` command, or explain why `export` and `deploy` currently only warn that they are unfinished.

For repository-level routing, start at `../../SKILL.md`. For install/import failures, missing CLI entry points, Pydantic/version pins, and stale-package checks, use `../../references/troubleshooting.md` first.

## Route Elsewhere

- FastAPI app creation, `launch-api`, `/call`, `/info`, OpenAPI docs, host/port API serving, and request schemas belong in `../api-services/SKILL.md`.
- Streamlit UI serving, `launch-ui`, generated forms, custom component rendering, and component models belong in `../ui-and-components/SKILL.md`.
- This sub-skill owns only local wrapping, callable validation, Python/CLI calls, callable-string resolution, and the `export`/`deploy` WIP behavior.

## Core Contract To Apply

- Build an Opyrator with `Opyrator(func_or_path)`, where `func_or_path` is either a callable object or an import string.
- Prefer import strings in the form `module:callable`; `get_callable()` also falls back to `module.callable` by splitting on the last separator.
- A compatible callable must expose an annotated parameter named exactly `input` and an annotated return value.
- The `input` annotation and return annotation must each be a Pydantic `BaseModel` subclass or a list type whose element type is a Pydantic model. For CLI-friendly list outputs, prefer a Pydantic wrapper/root model so the output object has `.json(...)`.
- `Opyrator.__call__(input, **kwargs)` accepts a model instance, a `dict`, or a JSON string and converts dict/JSON inputs with Pydantic before calling the wrapped function.
- Function names and callable-class names are converted with `name_to_title()`, for example `hello_world` becomes `Hello World`; descriptions come from function docstrings or callable/class docstrings.
- Passing an uninitialized class is rejected. To wrap a callable class, instantiate it and expose the instance if the CLI needs to import it.

## Fast Path Examples

Minimal function:

```python
from pydantic import BaseModel

class Input(BaseModel):
    message: str

class Output(BaseModel):
    message: str

def hello_world(input: Input) -> Output:
    """Returns the `message` of the input data."""
    return Output(message=input.message)
```

Python call:

```python
from opyrator import Opyrator

wrapped = Opyrator(hello_world)
assert wrapped.name == "Hello World"
assert wrapped({"message": "hello"}).message == "hello"
assert wrapped('{"message": "hello"}').json(indent=4)
```

CLI call from the directory where `my_opyrator.py` is importable:

```bash
opyrator call my_opyrator:hello_world '{"message": "hello"}'
```

Expected stdout for the hello-world example:

```json
{
    "message": "hello"
}
```

## Export And Deploy Are Placeholders

The installed CLI exposes `call`, `deploy`, `export`, `launch-api`, and `launch-ui`. In the verified 0.0.12 behavior, this sub-skill treats only `call` as an executable local function call workflow. `export` and `deploy` are command stubs that print `[WIP] This feature is not finalized yet...`; do not promise a zip file, Docker image, PEX file, or cloud deployment from those commands.

Safe checks:

```bash
opyrator call --help
opyrator export --help
opyrator deploy --help
opyrator export my_opyrator:hello_world my-opyrator.zip
opyrator deploy my_opyrator:hello_world
```

## References And Helper

- Wrapping and call workflows: `references/workflows.md`
- Command forms and expected CLI output: `references/cli-reference.md`
- Failure-mode map and exact validation messages: `references/troubleshooting.md`
- Safe local smoke helper: `scripts/smoke_call.py`

Run the helper when an environment already has Opyrator importable:

```bash
python sub-skills/wrapping-and-cli/scripts/smoke_call.py
```

The helper creates a temporary module, invokes the same Typer CLI commands in-process, verifies callable-class wrapping through the Python API, and checks that `export`/`deploy` report WIP without starting services or contacting the network.
