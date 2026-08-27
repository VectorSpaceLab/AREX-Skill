# Configuration and Colang

Use this reference when you need to create or repair a guardrails config folder, choose a Colang version, or understand how `RailsConfig` loads YAML and `.co` files.

## Standard folder layout

A practical configuration folder often looks like this:

```text
config/
├── config.yml
├── prompts.yml          # optional; can also live in config.yml
├── config.py            # optional startup initialization
├── actions.py           # optional custom actions
├── rails.co             # common in Colang 1.0
├── main.co              # common in Colang 2.x
├── kb/                  # optional markdown knowledge base
└── shared/              # optional import target via import_paths
```

Common file roles:

| File | Purpose |
| --- | --- |
| `config.yml` | Core config: models, rails, prompts, instructions, knowledge base, caching, tracing, import paths, and custom data. |
| `prompts.yml` | Prompt tasks for self-check, fact-checking, content safety, topic control, and similar rail tasks. |
| `rails.co` / `main.co` | Colang flows. `rails.co` is common in Colang 1.0; `main.co` is the usual 2.x entry point. |
| `actions.py` or `actions/` | Decorated Python actions auto-registered when the config is loaded. |
| `config.py` | Synchronous startup initialization for providers, shared resources, and registered action parameters. |
| `kb/` | Markdown knowledge-base documents for retrieval; plain Markdown is the supported format. |
| `import_paths` targets | Shared config folders that can contribute prompts, flows, actions, or other config pieces. |

## Loading configs

`RailsConfig.from_path(config_path)` loads a file or directory:

- If `config_path` is a YAML file, it loads that file directly.
- If `config_path` is a directory, it loads config recursively, finds `.co` files, and honors `import_paths`.
- If no instructions are provided, the loader fills in the default general instruction.

`RailsConfig.from_content(colang_content=None, yaml_content=None, config=None)` is the in-memory version. Use it for tests, generated fixtures, or small validation examples.

### What `config.yml` commonly contains

- `models`: model definitions such as `main`, `embeddings`, `content_safety`, `topic_control`, or custom task/model types.
  - Put the model name in exactly one place: `model` or `parameters.model` / `parameters.model_name`.
  - `api_key_env_var` is validated when the config loads.
  - `cache` can enable per-model LFU caching and cache statistics.
- `rails`: active rail flows and rail-specific settings.
- `prompts`: task prompts for LLM-backed rails.
- `instructions`: general system-level guidance.
- `sample_conversation`: example dialog.
- `knowledge_base`: folder and embedding-search settings.
- `core.embedding_search_provider`: low-level embedding search settings.
- `custom_data`: app-specific config consumed by `config.py` or actions.
- `import_paths`: extra config folders to merge into the load.
- `colang_version`: `1.0` by default, or `2.x` for the newer Colang runtime.

### Minimal starter shape

```yaml
models:
  - type: main
    engine: openai
    model: gpt-4o-mini

rails:
  input:
    flows:
      - self check input
  output:
    flows:
      - self check output

prompts:
  - task: self_check_input
    content: |
      ...
  - task: self_check_output
    content: |
      ...
```

## Rail sections at a glance

| Section | Typical use |
| --- | --- |
| `rails.input` | Validate, mask, or block user input. |
| `rails.output` | Validate, rewrite, or block model output. |
| `rails.retrieval` | Validate or mask retrieved chunks before they reach prompts. |
| `rails.dialog` | Dialog behavior, including single-call mode and user-message interpretation. |
| `rails.actions` | Control action execution settings. |
| `rails.tool_input` / `rails.tool_output` | Tool-result and tool-call validation; IORails only. |
| `rails.config` | Family-specific settings for built-in or third-party rails. |

## Colang 1.0 vs 2.x

### Colang 1.0

Colang 1.0 uses the classic guardrails syntax:

```text
define user express greeting
  "hello"

define bot express greeting
  "Hello!"

define flow greet
  user express greeting
  bot express greeting
```

Traits:

- `define flow`, `define user`, `define bot`, and `define subflow` are common.
- `execute` invokes actions.
- Flows are generally auto-discovered.
- This is the default Colang version unless you set `colang_version: "2.x"`.

### Colang 2.x

Colang 2.x uses the newer `flow` / `main` style:

```text
import core
import llm

flow main
  activate llm continuation
```

Traits:

- `main` is the entry point.
- `import` is explicit.
- `await` replaces `execute` for actions.
- Variables are local by default; use `global` when needed.
- String interpolation uses braces, such as `"Hello there, {$name}!"`.

### Which version to use

- Use Colang 1.0 when you want the most established guardrail flow syntax or when a config relies on existing 1.0 flows.
- Use Colang 2.x when you are authoring a newer config that depends on `main`, imports, or the newer runtime model.
- If you migrate old configs, review the result manually instead of trusting the conversion tool blindly.

## Migration with `nemoguardrails convert`

The migration command can transform older configs and Colang files:

```bash
nemoguardrails convert ./config --from-version 1.0 --validate
```

Useful flags:

- `--from-version 1.0` or `--from-version 2.0-alpha`
- `--validate`
- `--use-active-decorator`
- `--include-main-flow`

Caveats:

- The tool edits files in place.
- It may create or rewrite generated Colang/config files such as extracted rail flows.
- It covers common syntax rewrites, but not every edge case.
- Always review the migrated files after running it.

## Practical loading notes

- `config.py` is loaded during `LLMRails` initialization, not by `RailsConfig.from_path()` alone.
- `actions.py` files under the config path are auto-registered when the runtime loads the config.
- `import_paths` let you share config fragments, but the referenced folders should still be self-contained and easy to review.
- If you are testing a config fragment in isolation, prefer `RailsConfig.from_content()` first, then instantiate `LLMRails` only if you want to prove the full startup path.
