# Provider plugin authoring

This reference distills the LangExtract provider plugin contract for future agents that need to create, package, register, or validate a custom backend. It is based on source evidence from `langextract/providers/README.md`, `scripts/create_provider_plugin.py`, `examples/custom_provider_plugin/`, `langextract/providers/router.py`, `langextract/providers/__init__.py`, `langextract/plugins.py`, `langextract/core/base_model.py`, `langextract/core/schema.py`, and `langextract/core/types.py`, plus installed-package signature inspection. Native verification candidates for a later verifier are `tests/provider_plugin_test.py`, `tests/registry_test.py`, and the optional credentialed example smoke `examples/custom_provider_plugin/test_example_provider.py`.

## External package shape

Create provider plugins as separate Python distributions. A minimal external package should look like:

```text
langextract-myprovider/
  pyproject.toml
  README.md
  LICENSE
  langextract_myprovider/
    __init__.py
    provider.py
    schema.py        # optional, only if the backend supports schema constraints
  test_plugin.py
```

The `pyproject.toml` entry point group must be exactly `langextract.providers`:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "langextract-myprovider"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
  "langextract>=1.0.0",
  # Add the provider SDK dependency here.
]

[project.entry-points."langextract.providers"]
myprovider = "langextract_myprovider:MyProviderLanguageModel"
```

The entry point can point at a class or a module-level object. The important requirement is that loading the entry point imports code that registers the provider class with LangExtract's router.

## Provider class contract

Prefer current core imports instead of compatibility aliases:

```python
from collections.abc import Iterator, Sequence
from typing import Any

from langextract.core import base_model, exceptions, types
from langextract.providers import router

@router.register(r"^my-model", r"^myprovider/", priority=10)
class MyProviderLanguageModel(base_model.BaseLanguageModel):
    def __init__(self, model_id: str = "my-model-default", api_key: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.model_id = model_id
        self.api_key = api_key
        self._extra_kwargs = kwargs.copy()
        # Initialize the backend SDK client here.

    def infer(self, batch_prompts: Sequence[str], **kwargs: Any) -> Iterator[Sequence[types.ScoredOutput]]:
        effective_kwargs = self.merge_kwargs(kwargs)
        for prompt in batch_prompts:
            # Replace this with the backend call.
            output_text = "..."
            yield [types.ScoredOutput(score=1.0, output=output_text)]
```

Installed API facts to preserve:

- `BaseLanguageModel.__init__(constraint=None, **kwargs)` stores `_constraint`, schema state, fence-output override, and `_extra_kwargs`.
- `BaseLanguageModel.infer(batch_prompts: Sequence[str], **kwargs) -> Iterator[Sequence[ScoredOutput]]` is abstract.
- `ScoredOutput(score: float | None = None, output: str | None = None)` is the expected output item.
- `BaseLanguageModel.infer_batch()` simply collects `infer()` output; implement `infer()` first.
- `BaseLanguageModel.merge_kwargs(runtime_kwargs)` lets provider-level kwargs be overridden at inference time.

Shape mistakes matter: returning a bare string, a single `ScoredOutput`, or one list for the whole batch breaks callers. Yield one ranked sequence per input prompt. A single-best provider should yield `[ScoredOutput(score=1.0, output=text)]` for each prompt.

Use LangExtract exceptions for configuration/runtime failures when possible:

- Missing SDK, missing API key, invalid endpoint, or unsupported model configuration: raise `langextract.core.exceptions.InferenceConfigError`.
- Backend call failures after configuration succeeds: raise `langextract.core.exceptions.InferenceRuntimeError` with the original exception when useful.

## Router registration patterns and priorities

The router API facts are:

- `router.register(*patterns, priority=0)` decorates a provider class and registers compiled regex patterns.
- `router.register_lazy(*patterns, target="module:Class", priority=0)` registers without importing the provider until resolution.
- `router.resolve(model_id)` returns the provider class for a model ID; higher priority entries win.
- `router.resolve_provider(provider_name)` resolves explicit providers by exact class-name pattern, case-insensitive partial class-name match, or matching provider pattern.
- `router.list_providers()` and `router.list_entries()` are safe debugging helpers.

Built-in provider patterns are registered lazily with priority `10` for Gemini (`^gemini`), OpenAI/GPT (`^gpt-4`, `^gpt4\.`, `^gpt-5`, `^gpt5\.`), and many Ollama/local/Hugging Face style patterns. Plugin defaults should normally use narrow patterns and priority `10` or lower unless they intentionally override a built-in. To intentionally override a built-in pattern such as `^gemini`, use a higher priority and document the override; otherwise tell users to pass an explicit provider:

```python
import langextract as lx

config = lx.factory.ModelConfig(
    model_id="gemini-3.5-flash",
    provider="CustomGeminiProvider",
    provider_kwargs={"api_key": "..."},
)
model = lx.factory.create_model(config)
```

Do not rely on equal-priority ordering for conflicts. Prefer one of these:

1. Avoid the conflict with a more specific pattern, such as `^myprovider-gemini`.
2. Require explicit provider selection with `factory.ModelConfig(provider="ClassName")`.
3. Use a higher priority only when the plugin is intended to take precedence.

## Plugin discovery lifecycle

`langextract.providers.load_plugins_once()` discovers installed distributions via Python entry points in the `langextract.providers` group. It is idempotent. Factory model creation calls both `load_builtins_once()` and `load_plugins_once()` before resolving providers, so normal `lx.extract()` and `factory.create_model()` calls trigger lazy discovery when needed.

Important behavior:

- Discovery is lazy; tests can call `langextract.providers.load_plugins_once()` explicitly before inspecting `router.list_entries()`.
- `LANGEXTRACT_DISABLE_PLUGINS=1`, `true`, or `yes` disables plugin discovery for that process. Built-ins still load.
- Plugin import errors are caught and logged, so one bad plugin should not prevent built-ins from working.
- If an entry-point-loaded class implements `get_model_patterns()`, `load_plugins_once()` can also register those patterns with `pattern_priority` defaulting to `20`; however, the recommended path is still a visible `@router.register(...)` decorator in the provider module.
- Router resolution is cached. Tests that clear or re-register providers should use `router.clear()` in a fresh process or test fixture; ordinary plugin users should not mutate router state mid-process.

## Schema support lifecycle

Implement schema support only when the backend can steer structured output. The core API facts are:

- `BaseLanguageModel.get_schema_class() -> type | None` advertises schema support.
- `BaseSchema.from_examples(examples_data, attribute_suffix="_attributes")` builds a schema from `ExampleData` examples.
- `BaseSchema.from_schema_dict(output_schema)` must be implemented to support user-authored `output_schema`.
- `BaseSchema.to_provider_config() -> dict[str, Any]` returns provider kwargs such as `response_schema`, `response_mime_type`, `json_mode`, or similar backend-specific settings.
- `BaseSchema.output_schema_reserved_provider_kwargs()` defaults to the keys of `to_provider_config()` and should include provider kwargs that conflict with `output_schema`.
- `BaseSchema.requires_raw_output` controls fence behavior. `True` means the provider emits raw JSON/YAML without Markdown fences; `False` means LangExtract should use fences.
- `BaseLanguageModel.apply_schema(schema_instance)` stores or clears the active schema. Providers with cached schema fields must override it and handle `None`.

Lifecycle with example-derived constraints:

1. The caller sets `use_schema_constraints=True` and supplies examples.
2. The factory resolves the provider class and calls `provider_class.get_schema_class()`.
3. If a schema class exists, LangExtract calls `Schema.from_examples(examples)`.
4. LangExtract calls `schema.to_provider_config()` and merges those kwargs with user `provider_kwargs`; caller-supplied values win for example-derived schemas.
5. LangExtract instantiates the provider, calls `schema.sync_with_provider_kwargs(effective_kwargs)`, then calls `model.apply_schema(schema_instance)`.
6. `model.requires_fence_output` is computed from `not schema.requires_raw_output` unless the caller explicitly overrides `fence_output`.

Lifecycle with user-authored `output_schema`:

1. The caller passes `output_schema=...` to `factory.create_model()` or a higher-level extraction path.
2. `fence_output=True` is invalid with `output_schema`; output schema also requires JSON format semantics.
3. LangExtract calls `Schema.from_schema_dict(output_schema)` and marks the schema as coming from output schema.
4. Provider kwargs listed by `output_schema_reserved_provider_kwargs()` cannot also be supplied by the caller, because that would make schema ownership ambiguous.
5. The provider receives the schema config and must produce raw JSON that matches the LangExtract output envelope.

A robust schema-enabled provider should include:

```python
class MyProviderSchema(core_schema.BaseSchema):
    def __init__(self, schema_dict: dict[str, Any], raw_output: bool = True) -> None:
        self._schema_dict = schema_dict
        self._raw_output = raw_output

    @classmethod
    def from_examples(cls, examples_data, attribute_suffix="_attributes"):
        # Build a backend-specific JSON schema or format contract from examples.
        return cls({"type": "object", "properties": {"extractions": {"type": "array"}}})

    @classmethod
    def from_schema_dict(cls, output_schema):
        return cls(dict(output_schema), raw_output=True)

    def to_provider_config(self):
        return {"response_schema": self._schema_dict, "structured_output": True}

    @property
    def requires_raw_output(self):
        return self._raw_output

    @property
    def schema_dict(self):
        return self._schema_dict
```

And the provider should clear schema state correctly:

```python
class MyProviderLanguageModel(base_model.BaseLanguageModel):
    @classmethod
    def get_schema_class(cls):
        return MyProviderSchema

    def apply_schema(self, schema_instance):
        super().apply_schema(schema_instance)
        if schema_instance is None:
            self.response_schema = None
            self.structured_output = False
            return
        config = schema_instance.to_provider_config()
        self.response_schema = config.get("response_schema")
        self.structured_output = bool(config.get("structured_output"))
```

## Bundled generator script

Use `scripts/create_provider_plugin.py` from this sub-skill when the user wants a scaffold:

```bash
python scripts/create_provider_plugin.py MyProvider --with-schema --patterns '^my-model' '^myprovider/' --output-dir ./plugins
```

Useful options:

- `--output-dir DIR`: create the plugin under `DIR` instead of the current directory.
- `--package-name NAME`: choose the distribution suffix; the generated distribution is `langextract-NAME` and the module is `langextract_NAME` with hyphens normalized to underscores.
- `--patterns REGEX ...`: regex model-ID patterns for `@router.register(...)`.
- `--priority INT`: router priority for generated registrations.
- `--with-schema`: include a `BaseSchema` implementation and schema validation in `test_plugin.py`.
- `--force`: allow overwriting the generator's predictable output files when the target directory already exists.
- `--install-and-test`: explicitly run `pip install -e` and `python test_plugin.py` after generation. This mutates the active Python environment, so use a throwaway environment.

Default behavior is safe: the generator writes files only and does not install packages, call model APIs, or require the original LangExtract checkout.

## Validation checklist

For non-live validation, do all of the following in the environment where the plugin package is installed:

```bash
python -m pip install -e ./langextract-myprovider --no-deps
python - <<'PY'
import langextract as lx
from langextract.providers import router

lx.providers.load_plugins_once()
print(router.list_entries())
cls = router.resolve("my-model-test")
print(cls.__name__)
model = lx.factory.create_model(
    lx.factory.ModelConfig(model_id="my-model-test", provider=cls.__name__)
)
print(type(model).__name__)
print(list(model.infer(["hello"]))[0][0])
PY
python ./langextract-myprovider/test_plugin.py
```

If the plugin wraps a credentialed SDK, split tests into:

- registration and mock inference tests that require no secrets or network;
- optional live smoke guarded by environment variables and explicit user approval.

## Omitted maintainer workflow

`validate_community_providers.py` and community registry table maintenance are not bundled into this operating sub-skill. They are maintainer/release workflows rather than plugin authoring for ordinary users. If the user explicitly asks to update a provider registry, treat that as a separate maintenance task and validate the relevant registry file in that repository context.
