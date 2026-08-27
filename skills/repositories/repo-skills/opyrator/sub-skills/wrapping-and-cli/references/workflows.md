# Wrapping And CLI Workflows

## 1. Author A Compatible Wrapper

Use a Pydantic input model, a Pydantic output model, and a single parameter named `input`.

```python
from pydantic import BaseModel

class Input(BaseModel):
    message: str

class Output(BaseModel):
    message: str


def hello_world(input: Input) -> Output:
    """Echo the message back to the caller."""
    return Output(message=input.message)
```

Validation rules that matter:

- The `input` parameter must exist and be annotated.
- The return value must be annotated.
- Both annotations must resolve to a `BaseModel` subclass or a list of Pydantic models.
- If you need multiple items in the output, prefer a wrapper model with a `__root__` list so the result still behaves like a model object.
- Additional required parameters are not part of the validated contract and will be awkward to satisfy from the CLI, so avoid them.

## 2. Wrap A Callable Instance

Callable objects are supported when you instantiate them first.

```python
class Greeter:
    """Callable wrapper that keeps its own docstring."""

    def __call__(self, input: Input) -> Output:
        return Output(message="hello " + input.message)


greeter = Greeter()
```

Behavior to remember:

- Passing `Greeter` the class itself is rejected as an uninitialized class.
- The callable-class name becomes title case from the class name.
- The description comes from the callable docstring first; if that is generic or missing, the class docstring is used.

## 3. Resolve An Import String

`Opyrator` can load a callable from a string.

Preferred form:

```python
Opyrator("my_module:hello_world")
```

Fallback form:

```python
Opyrator("my_module.hello_world")
```

Resolution notes:

- The loader splits on the last `:` or `.`.
- A path without either separator raises `ValueError` telling you to specify the callable.
- `ModuleNotFoundError` means the module is not importable from the active environment or search path.
- `AttributeError` means the module imported but the named callable was not found.

## 4. Call From Python With A Dict Or JSON String

`Opyrator.__call__` accepts a Pydantic instance, a plain dictionary, or a JSON string.

```python
wrapped = Opyrator(hello_world)
assert wrapped({"message": "hello"}).message == "hello"
assert wrapped('{"message": "hello"}').message == "hello"
```

Use dict input when a caller already has parsed data. Use JSON input when you want to mirror the CLI payload format exactly.

## 5. Call From The CLI

`opyrator call` runs the callable locally and prints the returned model as indented JSON.

```bash
opyrator call my_module:hello_world '{"message": "hello"}'
```

Expected behavior:

- Success prints formatted JSON to stdout.
- A falsy return value prints `Nothing returned!`.
- Pydantic validation errors are caught and written to stderr.
- Other exceptions are not normalized by the CLI, so Python tracebacks can still surface for import and runtime errors.

Use `opyrator call --help` when you only need argument names or want to confirm the installed CLI surface.

## 6. Treat Export And Deploy As WIP

The verified 0.0.12 CLI exposes `export` and `deploy`, but both are placeholders.

```bash
opyrator export my_module:hello_world my-opyrator.zip
opyrator export my_module:hello_world my-image:latest --format docker
opyrator export my_module:hello_world my-opyrator.pex --format pex
opyrator deploy my_module:hello_world
```

Expected behavior:

- Each command prints a bright yellow `[WIP]` message.
- No archive, Docker image, or deployment is produced by these commands.
- `--help` is still useful for checking the exact option surface and help wording.

## 7. Small Hello-World Pattern

The most reusable pattern is:

1. Create a module with a tiny `Input` and `Output` model.
2. Export the callable at module scope.
3. Wrap it with `Opyrator` in Python or reference it with `module:callable` in the CLI.
4. Call it once from Python with a dict, once with JSON, and once through `opyrator call`.
5. Keep export/deploy checks limited to help output and WIP warnings.

## 8. When To Stop And Route Elsewhere

If the user actually needs a running API server, OpenAPI, or UI widgets, route out of this sub-skill:

- API serving and `/call` routes: `../../api-services/SKILL.md`
- Streamlit UI and component rendering: `../../ui-and-components/SKILL.md`

If the problem looks like a package install or pin mismatch, go back to `../../../references/troubleshooting.md` first.
