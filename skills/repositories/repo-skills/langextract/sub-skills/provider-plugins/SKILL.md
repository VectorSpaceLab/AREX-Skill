---
name: provider-plugins
description: "Create, package, register, test, and troubleshoot custom
  LangExtract provider plugins."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# LangExtract Provider Plugins

Use this sub-skill when a task is about adding a new LangExtract model backend as an external Python package, making it discoverable through the provider router, or debugging plugin discovery/registration/schema integration.

## Route elsewhere

- Built-in Gemini, OpenAI, Ollama, model IDs, API keys, provider kwargs, or batch configuration: use `../providers/SKILL.md`.
- Prompt descriptions, few-shot examples, output schema design for extraction tasks, chunking, resolver, or tokenizer behavior: use `../extraction/SKILL.md`.
- Saving JSONL, loading `AnnotatedDocument` results, or HTML visualization: use `../visualization/SKILL.md`.
- Community provider registry maintenance is out of scope unless explicitly requested; this sub-skill records it as an omission rather than bundling maintainer-only registry validation.

## Authoring workflow

1. Decide whether the user needs a plugin at all. If they only need an existing Gemini/OpenAI/Ollama backend or provider kwargs, route to `../providers/SKILL.md`.
2. Create an external package scaffold, preferably with the bundled generator:
   ```bash
   python scripts/create_provider_plugin.py MyProvider --with-schema --patterns '^my-model' --output-dir ./plugins
   ```
   The generator writes a package under the selected output directory and does not install anything unless `--install-and-test` is explicitly passed.
3. Register the plugin in `pyproject.toml` with `[project.entry-points."langextract.providers"]` pointing to a package object that imports the provider class.
4. Implement a provider class that inherits `langextract.core.base_model.BaseLanguageModel` and whose `infer()` yields one sequence of `langextract.core.types.ScoredOutput` objects for each prompt.
5. Register model-ID regex patterns with `@router.register(...)`. Use narrow patterns and explicit priority choices to avoid conflicts with built-ins.
6. If structured output is required, implement a `BaseSchema` subclass plus `get_schema_class()`, `from_examples()`, `to_provider_config()`, `requires_raw_output`, and `apply_schema(None)` handling.
7. Validate in an isolated user environment: install the plugin, call `langextract.providers.load_plugins_once()`, inspect `router.list_entries()`, resolve by model ID and explicit provider name, and run a mock or credential-gated smoke.

See `references/plugin-authoring.md` for the detailed package/API/schema contract and `references/troubleshooting.md` for discovery, conflict, dependency, and schema failure modes.

## Required safety posture

- Keep plugin packages external to LangExtract; do not edit LangExtract core unless the user is doing maintainer work.
- Do not embed API keys or machine-specific paths in generated plugin files.
- Treat live provider calls as optional credentialed smoke tests; registration, routing, schema, and mock inference can be validated without network access.
- Do not run original LangExtract native tests/examples from this sub-skill. Native evidence candidates for later verification are `tests/provider_plugin_test.py`, `tests/registry_test.py`, and `examples/custom_provider_plugin/test_example_provider.py`.
