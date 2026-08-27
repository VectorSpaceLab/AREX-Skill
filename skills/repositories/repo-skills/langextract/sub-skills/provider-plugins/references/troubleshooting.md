# Provider plugin troubleshooting

Use this guide after routing confirms that the problem is custom plugin authoring or discovery. For ordinary Gemini/OpenAI/Ollama configuration, route to `../providers/SKILL.md`; for prompt or extraction-output design, route to `../extraction/SKILL.md`.

## Quick triage sequence

1. Confirm the plugin is installed in the same Python environment that runs LangExtract:
   ```bash
   python -m pip show langextract-myprovider
   ```
2. Confirm the entry point exists and is in the exact `langextract.providers` group:
   ```bash
   python - <<'PY'
from importlib import metadata
for ep in metadata.entry_points().select(group="langextract.providers"):
    print(ep.name, "=>", ep.value)
PY
   ```
3. Trigger discovery and inspect registered patterns:
   ```bash
   python - <<'PY'
import langextract as lx
from langextract.providers import router
lx.providers.load_plugins_once()
print(router.list_entries())
PY
   ```
4. Resolve both ways when a model pattern is ambiguous:
   ```python
   from langextract import factory
   model = factory.create_model(factory.ModelConfig(
       model_id="my-model-v1",
       provider="MyProviderLanguageModel",  # explicit disambiguation
       provider_kwargs={},
   ))
   ```
5. Keep live API calls optional. First prove import, registration, factory construction, schema application, and mock inference without credentials.

## Failure modes and fixes

| Symptom | Likely cause | How to confirm | Fix |
| --- | --- | --- | --- |
| `No provider registered for model_id='...'` | Plugin not installed, entry point missing, discovery not triggered, wrong regex, or `LANGEXTRACT_DISABLE_PLUGINS` is active. | Run the entry-point and `router.list_entries()` snippets above. Check `LANGEXTRACT_DISABLE_PLUGINS`. | Install the plugin in the active environment, fix `[project.entry-points."langextract.providers"]`, call `load_plugins_once()` in tests, use a matching regex such as `^my-model`, or unset the disable env var in a fresh process. |
| Plugin package imports manually but model ID still does not resolve. | Entry point imports a module/class but no `@router.register(...)` executes, or `get_model_patterns()` is absent. | After manual import, inspect `router.list_entries()` for the expected pattern. | Add `@router.register(...)` to the provider class or implement `get_model_patterns()` plus `pattern_priority`; ensure the entry point imports that class. |
| Built-ins load but plugin import failure appears in logs. | `load_plugins_once()` catches plugin import exceptions and continues. Missing SDKs or syntax errors commonly cause this. | Load the entry point directly with `ep.load()` or import the plugin module in Python to see the full exception. | Add the SDK dependency to `pyproject.toml`, fix imports, avoid importing optional heavy SDKs at module import time when possible, and raise `InferenceConfigError` from provider `__init__` for missing runtime configuration. |
| `LANGEXTRACT_DISABLE_PLUGINS` was unset but plugins still do not load in a long-running process. | `load_plugins_once()` is idempotent; if discovery was previously disabled, the process may have marked plugins as loaded. | Start a new process and retry the discovery snippet. | In normal usage, restart the Python process after unsetting the env var. Test fixtures can use private reset helpers, but production code should not. |
| Plugin conflicts with Gemini/OpenAI/Ollama and the built-in wins. | Broad patterns such as `^gemini`, `^gpt-4`, or `^gemma` overlap built-ins. Built-ins use priority `10`. | `router.list_entries()` shows multiple matching patterns; `router.resolve(model_id).__name__` shows the selected class. | Prefer narrow plugin-specific model IDs. Otherwise pass `ModelConfig(provider="PluginClassName")`; use priority above `10` only for deliberate overrides. |
| Plugin unexpectedly overrides a built-in. | Plugin pattern is too broad or priority is too high. | Compare pattern and priority in `router.list_entries()`. | Lower the plugin priority, narrow the regex, or document that explicit provider selection is required. |
| `No provider found matching: '...'` with explicit provider. | The provider class never registered, the plugin failed import, or the explicit name does not match the class. | Inspect `router.list_entries()` and try the exact class name. | Ensure the provider class is imported by the entry point and registered; pass the full class name such as `MyProviderLanguageModel` rather than a vague partial name. |
| `ModuleNotFoundError` or missing SDK error during factory construction. | The plugin imports a provider SDK that was not installed, or imports it at module import time. | Import the plugin module directly; run `python -m pip show SDK_PACKAGE`. | Add the SDK to the plugin package dependencies. For optional SDKs, delay import until `__init__` and raise `InferenceConfigError` with a clear install hint. |
| API key or credential error during plugin smoke. | Live backend credentials are absent; the example smoke is credentialed. | Check the provider's documented env vars, but do not print secret values. | Keep registration/mock tests separate from optional live smoke. Skip live smoke unless the user explicitly provides credentials/network permission. |
| `infer()` returns a string or crashes in extraction resolution. | Wrong `infer()` shape. LangExtract expects an iterator of sequences of `ScoredOutput`. | Call `list(model.infer(["one", "two"]))` and inspect shape. | Yield one ranked list per prompt: `yield [types.ScoredOutput(score=1.0, output=text)]`. |
| Schema constraints are ignored. | `get_schema_class()` returns `None`, `from_examples()` is missing, caller omitted `use_schema_constraints=True`, or `to_provider_config()` keys are not consumed by the provider. | Inspect `provider_class.get_schema_class()`, construct `Schema.from_examples(examples)`, and check provider fields after factory creation. | Implement `BaseSchema.from_examples()`, return the schema class from the provider, merge the schema config into provider state, and test with examples. |
| `output_schema` raises unsupported-provider error. | The schema class did not implement `from_schema_dict()`. | Call `ProviderSchema.from_schema_dict({...})` directly. | Implement `from_schema_dict()` for LangExtract's raw output envelope schema, or document that only example-derived constraints are supported. |
| `output_schema` conflicts with provider kwargs. | The caller supplied kwargs such as `response_schema` that the schema also owns. | Error lists reserved/conflicting kwargs. | Add conflicting keys to `output_schema_reserved_provider_kwargs()` and tell callers to choose either `output_schema` or provider-native schema kwargs, not both. |
| JSON is wrapped in fences when the backend promises raw JSON, or raw JSON is expected but fenced output is returned. | `requires_raw_output` is wrong, `fence_output` was forced, or provider schema state is stale. | Check `model.requires_fence_output` after factory creation and inspect raw provider output. | Set `requires_raw_output=True` only when the backend truly emits raw JSON/YAML. If output needs Markdown fences, return `False` or avoid schema mode. Do not combine `output_schema` with `fence_output=True`. |
| Schema from a prior call persists after clearing. | Provider overrides `apply_schema()` but does not handle `None`. | Call `model.apply_schema(None)` and inspect provider schema fields. | Always call `super().apply_schema(schema_instance)` and clear provider-specific fields when `schema_instance is None`. |
| A newly registered provider does not affect `router.resolve()` in a test. | Router resolution is cached for previously resolved model IDs. | The same process resolved the model ID before re-registering. | Use a fresh process for plugin smoke. In tests, call `router.clear()` before re-registering. |
| Generated scaffold overwrites an existing directory. | `--force` was used or the output path was reused. | Inspect the output path before generation. | The bundled generator refuses non-empty targets by default. Use a new output directory; pass `--force` only when replacing the generator's expected files is intentional. |

## Schema-specific checklist

Before blaming the extraction pipeline, verify the plugin schema lifecycle in isolation:

```python
from langextract import data, factory
from langextract.providers import router
import langextract as lx

lx.providers.load_plugins_once()
provider_cls = router.resolve("my-model-test")
schema_cls = provider_cls.get_schema_class()
assert schema_cls is not None

examples = [data.ExampleData(
    text="Example text",
    extractions=[data.Extraction(extraction_class="entity", extraction_text="Example")],
)]
schema = schema_cls.from_examples(examples)
assert isinstance(schema.to_provider_config(), dict)

model = factory.create_model(
    factory.ModelConfig(model_id="my-model-test", provider=provider_cls.__name__),
    examples=examples,
    use_schema_constraints=True,
)
assert model.schema is not None
```

If `schema.requires_raw_output` is `True`, the provider must produce syntactically valid JSON/YAML without Markdown fences. If it returns fenced JSON, either change the provider output or set `requires_raw_output=False` and use a fence-compatible extraction path.

## Conflict disambiguation patterns

When a plugin deliberately shares a built-in pattern such as `^gemini`, future agents should avoid ambiguous natural-language instructions like "use Gemini". Use explicit provider selection:

```python
import langextract as lx

config = lx.factory.ModelConfig(
    model_id="gemini-3.5-flash",
    provider="CustomGeminiProvider",
    provider_kwargs={"api_key": "..."},
)
model = lx.factory.create_model(config)
```

If the user wants the plugin to win automatically, require an intentional design note explaining the broad regex and priority. Otherwise prefer a plugin-specific model prefix such as `custom-gemini-*`.

## Optional live smoke policy

The example custom provider uses a real SDK and an API key for live inference. Treat that as optional evidence only:

- Passing import/entry-point/router/schema/mock-inference checks is enough to validate plugin packaging mechanics.
- Missing credentials should produce a skip or configuration error, not a failed plugin-authoring result.
- Never print API key values; show only which variable names the provider accepts.
- Run live smoke only after the user confirms credentials, network, model cost, and service availability.
