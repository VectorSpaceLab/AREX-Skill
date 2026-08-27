# Package surface for setup checks

Use this page for import discovery and no-provider package health checks. For creating configs or running rails, route to the corresponding workflow sub-skill rather than expanding this page into execution guidance.

## Distribution and version

```python
import nemoguardrails
print(nemoguardrails.__version__)
```

The package distribution and import name are both `nemoguardrails`. Version can also be read with `python -m nemoguardrails --version` or `importlib.metadata.version("nemoguardrails")`.

Importing the top-level package applies the package's asyncio/tokenizer setup and exposes the public API objects below. A top-level import should not call a live provider or download a model.

## Top-level public imports

```python
from nemoguardrails import (
    Guardrails,
    LLMRails,
    RailsConfig,
    ChatMessage,
    LLMModel,
    LLMResponse,
    LLMResponseChunk,
    get_default_framework,
    register_framework,
    register_provider,
    set_default_framework,
)
```

| Name | Basic purpose | Route detailed use to |
| --- | --- | --- |
| `RailsConfig` | Load a guardrails configuration from a path or in-memory content. | `../../configure-rails/SKILL.md` |
| `LLMRails` | Original runtime wrapper for generating/checking with a `RailsConfig`. | `../../run-rails/SKILL.md` |
| `Guardrails` | Newer wrapper that can use the IORails engine when compatible and fall back to `LLMRails` unless required otherwise. | `../../run-rails/SKILL.md` |
| `ChatMessage`, `LLMModel`, `LLMResponse`, `LLMResponseChunk` | Public types used by framework-agnostic LLM integrations and fake-model testing. | `../../run-rails/SKILL.md` for execution; this page for import verification. |
| `register_provider` | Register a custom LLM provider class. | `../../configure-rails/references/custom-actions-and-providers.md` |
| `register_framework`, `set_default_framework`, `get_default_framework` | Select/register the default LLM framework, including LangChain mode. | `../../run-rails/references/integrations.md` |

Environment note: if `NEMO_GUARDRAILS_IORAILS_ENGINE` is set to a truthy value before import, the top-level `LLMRails` symbol aliases `Guardrails` for compatibility. Unset it and reload the package to observe the original `LLMRails` class.

## Configuration loader entry points

For import verification only:

```python
from nemoguardrails import RailsConfig
assert hasattr(RailsConfig, "from_path")
assert hasattr(RailsConfig, "from_content")
```

`RailsConfig.from_path(config_path)` and `RailsConfig.from_content(colang_content=None, yaml_content=None, config=None)` are the key constructors. Use the configure sub-skill for valid YAML/Colang patterns and validation errors.

## Testing helpers

The package exposes deterministic testing utilities:

```python
from nemoguardrails.testing import FakeLLMModel, RecordingHTTPClient, TestChat
```

| Helper | Purpose | Setup-safe note |
| --- | --- | --- |
| `FakeLLMModel` | Framework-agnostic fake LLM implementing the `LLMModel` protocol with scripted responses or scripted exceptions. | Importing it is safe. Constructing it does not call providers. |
| `TestChat` | Conversational assertion harness around a `RailsConfig` and fake completions. | Useful for no-provider smokes, but a naive config can still trigger embeddings setup; use deterministic embeddings in bundled runtime smokes. |
| `RecordingHTTPClient` | Scripted HTTP client that records requests and serves queued responses. | Importing it is safe. Use it to avoid live HTTP calls in tests. |

A pytest plugin is available as `nemoguardrails.testing.fixtures`; opt in from a user's own tests with:

```python
pytest_plugins = ["nemoguardrails.testing.fixtures"]
```

## CLI module surface

Package metadata installs a `nemoguardrails` console command that dispatches to `nemoguardrails.__main__:app`. The module form is the most reliable fallback:

```bash
python -m nemoguardrails --version
python -m nemoguardrails --help
```

Observed command families include:

- `chat`
- `server`
- `convert`
- `actions-server`
- `find-providers`
- `eval`

The `eval` command has subcommands such as `run`, `check-compliance`, `ui`, and `rail`. Treat CLI help/version checks as setup verification only; route actual server, chat, config conversion, or eval execution to the owning sub-skill.

## Optional dependency helpers

The package provides optional import helpers in `nemoguardrails.imports`:

```python
from nemoguardrails.imports import (
    check_optional_dependency,
    get_optional_dependency,
    import_optional_dependency,
    optional_import,
)
```

Behavior distilled for troubleshooting:

- `optional_import(module_name, package_name=None, error="raise", extra=None)` imports a module or raises/warns/returns `None` for a missing optional dependency. When `extra` is supplied, the message includes `pip install 'nemoguardrails[extra]'`.
- `check_optional_dependency(module_name, package_name=None, extra=None)` returns `True` or `False` without raising.
- `import_optional_dependency(name, extra=None, errors="raise", min_version=None)` supports `raise`, `warn`, and `ignore`; it can also raise or warn when an installed module is older than `min_version`.
- `get_optional_dependency(name, errors="raise")` uses package-known extra hints for selected dependencies; not every third-party module maps to a NeMo Guardrails extra.

Common known optional names include `openai`, `langchain`, `langchain_openai`, `langchain_community`, `langchain_nvidia_ai_endpoints`, `torch`, `transformers`, `presidio_analyzer`, `presidio_anonymizer`, and `spacy`. Missing `openai` maps to the `server` extra; many provider/framework packages must be installed directly according to the user's chosen provider stack.
