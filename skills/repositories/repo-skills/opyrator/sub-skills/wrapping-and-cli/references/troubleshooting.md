# Wrapping And CLI Troubleshooting

Use this reference for callable construction, import-string resolution, local CLI calls, and WIP export/deploy confusion. If the package itself is missing, the CLI entry point is unavailable, or version/Pydantic pins look wrong, first use the root troubleshooting guide at `../../../references/troubleshooting.md`.

## Invalid Callable Path

Symptoms:

- `ValueError: The callable path MUST specify the function.`
- `ModuleNotFoundError: No module named ...`
- `AttributeError: module ... has no attribute ...`

Likely causes:

- The import string has no callable separator.
- The shell is not running from a directory where the module is importable.
- The wrong object name was placed after `:` or the final `.`.

Fixes:

- Prefer `module:callable`, for example `my_opyrator:hello_world`.
- Run `python -c "import my_opyrator; print(my_opyrator.hello_world)"` from the same directory before using the CLI.
- Put the module directory on `PYTHONPATH` if it is not the current working directory.
- Expose callable-class instances as module globals, for example `greeter = Greeter()` and call `my_module:greeter`.

## Provided Object Is Not Callable

Symptoms:

- `ValueError: The provided function parameters is not a callable.`

Cause: the import target exists but is not callable, such as a model class, data object, or constant.

Fix: point the import string at a function or callable instance.

## Uninitialized Class Rejected

Symptoms:

- `ValueError: The provided callable is an uninitialized Class. This is not allowed.`

Cause: the target is a class object, not an instance.

Fix:

```python
class Greeter:
    def __call__(self, input: Input) -> Output:
        return Output(message=input.message)

greeter = Greeter()  # import this instance, not Greeter
```

Then use `my_module:greeter`.

## Missing Input Annotation

Symptoms:

```text
The callable MUST have a parameter with the name `input` with typing annotation. For example: `def my_opyrator(input: InputModel) -> OutputModel:`.
```

Cause: there is no annotated parameter named exactly `input`.

Fix:

```python
def hello_world(input: Input) -> Output:
    ...
```

Do not rename the parameter to `data`, `payload`, or `request` unless you also wrap it in a new Opyrator-compatible function with `input`.

## Input Type Is Not Compatible

Symptoms:

```text
The `input` parameter MUST be a subclass of the Pydantic BaseModel or a list of Pydantic models.
```

Cause: the annotation is a primitive, `dict`, arbitrary class, or unsupported container.

Fix: define a Pydantic model and annotate the `input` parameter with it.

```python
class Input(BaseModel):
    text: str
```

## Missing Return Annotation

Symptoms:

```text
The return type of the callable MUST be annotated with type hints.For example: `def my_opyrator(input: InputModel) -> OutputModel:`.
```

Cause: the function has no `-> OutputModel` annotation.

Fix: add an annotated Pydantic output type.

## Return Type Is Not Compatible

Symptoms:

```text
The return value MUST be a subclass of the Pydantic BaseModel or a list of Pydantic models.
```

Cause: the return annotation is a primitive, dict, arbitrary class, or unsupported container.

Fix: return a Pydantic output model. For repeated values that should print cleanly from the CLI, use a Pydantic wrapper/root model rather than a raw Python list.

## CLI JSON Validation Error

Symptoms:

- Validation text is printed to stderr.
- The error mentions required fields, wrong types, invalid JSON, or enum choices.

Cause: `opyrator call` passes the second positional argument as a JSON string and Pydantic parses it as the callable input model.

Fixes:

- Validate shell quoting by echoing the payload or using a small Python JSON dump.
- Match field names exactly to the `Input` model.
- Remember that the CLI catches Pydantic validation errors and writes them to stderr; do not rely only on the process return code.

Good payload:

```bash
opyrator call my_opyrator:hello_world '{"message": "hello"}'
```

Bad payload for the hello-world model:

```bash
opyrator call my_opyrator:hello_world '{"wrong": "hello"}'
```

## Runtime Error During Wrapped Function

Symptoms:

- Python traceback from inside the target function.
- Import succeeds and validation passes, but the function fails.

Cause: Opyrator does not sandbox or normalize arbitrary function exceptions.

Fixes:

- Reproduce with the direct Python API using a model or dict input.
- Add ordinary function-level error handling if the wrapped callable should return structured errors.
- Keep server/API exception handling questions in `../../api-services/SKILL.md`.

## List Output Does Not Print Cleanly From CLI

Symptoms:

- Direct Python call returns a list, but `opyrator call` raises an attribute error around `.json(...)`.

Cause: the CLI prints `output.json(indent=4)`. A raw list does not have a `.json` method even though the type validator accepts list-of-model annotations.

Fixes:

- Wrap the list in a Pydantic output model, often with `__root__`.
- Or call the wrapper from Python and serialize the list yourself.

## Export Or Deploy Does Not Produce Anything

Symptoms:

- Command prints `[WIP] This feature is not finalized yet...`.
- No zip, Docker image, PEX file, or cloud deployment appears.

Cause: in 0.0.12, `export` and `deploy` are placeholders.

Fixes:

- Treat the WIP warning as expected behavior, not an environment failure.
- Do not retry expecting a side effect.
- If the user needs real packaging or deployment, explain that this package version does not implement it and route any server-level workaround to the API/UI sub-skills as appropriate.

## README Or Aspirational Feature Confusion

Symptoms:

- A user asks for zip-based CLI calls, HTTP endpoint calls through `opyrator call`, or provider-specific deploy arguments.

Cause: some public-facing documentation describes intended features, while the verified 0.0.12 source and CLI show local callable execution plus WIP placeholders.

Fixes:

- Use the verified local form `opyrator call module:callable JSON` for this sub-skill.
- Use `opyrator <command> --help` to confirm the installed option surface.
- Do not promise zip/URL call or real deploy behavior unless a refreshed skill verifies a newer package version.
