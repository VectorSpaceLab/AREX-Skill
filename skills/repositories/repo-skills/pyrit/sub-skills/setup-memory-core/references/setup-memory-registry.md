# Setup, memory, registry, and output workflows

This reference distills PyRIT setup behavior for agents that need a safe local session, persistent memory, registry inspection, or rendered results. All snippets assume `pyrit` is already installed and imported from the active Python environment.

## Initialization decision table

| Need | Use | Why |
|---|---|---|
| Fast no-secret code path, tests, or examples | `await initialize_pyrit_async(memory_db_type="InMemory", load_defaults=False, env_files=[], silent=True)` | Avoids persistent database state, skips default `.env` loading, and avoids default target/technique initializers. |
| Normal notebook/API use with known environment files | `await initialize_pyrit_async(memory_db_type="InMemory" or "SQLite", env_files=[...])` | Lets the caller choose backend and explicit env-file ordering. |
| Persistent team/user setup with a real config file | `await initialize_from_config_async(config_path)` | Loads YAML configuration, resolves registered initializers, and initializes memory in one call. |
| Config layering with programmatic overrides | `ConfigurationLoader.load_with_overrides(...); await config.initialize_pyrit_async()` | Merges default config if present, explicit config, then keyword overrides. |
| Scanner/backend command behavior | Route to `../cli-backend-scanner/SKILL.md` | CLI flags and backend server lifecycle are owned by the scanner sub-skill. |

### Direct initialization

```python
from pyrit.setup import IN_MEMORY, SQLITE, initialize_pyrit_async

# No-secret smoke/test session: no default env files, no default initializers.
await initialize_pyrit_async(
    memory_db_type=IN_MEMORY,
    env_files=[],
    load_defaults=False,
    silent=True,
)

# Persistent SQLite session with a caller-owned database file.
await initialize_pyrit_async(
    memory_db_type=SQLITE,
    db_path="./pyrit-session.db",
    silent=True,
)
```

Important direct-init behavior:

1. Azure Key Vault refs, when supplied, are loaded first.
2. Environment files are loaded after AKV refs, so later `.env` sources override earlier ones.
3. Default values are reset.
4. The selected memory backend is constructed and assigned to `CentralMemory`.
5. Initializers run after memory is ready.
6. If neither `initializers` nor `initialization_scripts` is supplied and `load_defaults=True`, PyRIT runs its built-in default initializer set for core techniques and available default targets. Set `load_defaults=False` for a deliberately empty/no-secret setup.

## File-driven setup

Default persistent user files live under `~/.pyrit/`:

```text
~/.pyrit/
  .pyrit_conf   # YAML setup: memory_db_type, initializers, env_files, server, etc.
  .env          # base credentials and endpoint variables
  .env.local    # personal/local overrides; loaded after .env when defaults are used
```

A minimal `.pyrit_conf` pattern:

```yaml
memory_db_type: sqlite
initializers:
  - name: target
    args:
      tags:
        - default
        - scorer
  - name: scorer
  - name: technique
silent: false
```

Fields agents most often need:

| Field | Meaning | Safe guidance |
|---|---|---|
| `memory_db_type` | `in_memory`, `sqlite`, or `azure_sql`; case-insensitive and accepts PascalCase forms through loaders. | Use `in_memory` for scratch runs, `sqlite` for local persistence, `azure_sql` only with approved credentials. |
| `initializers` | Names or `{name, args}` dictionaries resolved via `InitializerRegistry`. Names normalize to snake case. | Keep order explicit. Use `target` before `scorer` when scorers need registered targets. |
| `initialization_scripts` | Optional Python files containing `PyRITInitializer` subclasses. | Use only trusted scripts; loading arbitrary initializer scripts executes Python code. |
| `env_files` | If omitted/null, default `.env` and `.env.local` are loaded when present. If `[]`, no env files are loaded. If a list, only those files are loaded in order. | For no-secret checks, use `env_files=[]`. For real runs, pass explicit files or rely on `~/.pyrit` only if expected. |
| `env_akv_ref` | Azure Key Vault secret URLs whose values are parsed as `.env` contents. | Optional; requires Azure packages and credentials. Local env files loaded afterward can override AKV values. |
| `server` | Backend client URL/startup timeout used by scanner workflows. | Route scanner-specific commands to `cli-backend-scanner`. |
| `silent` | Suppresses initialization and migration print messages. | Use `silent=True` in automation unless human console progress is helpful. |

`initialize_from_config_async()` expects the requested config file to exist. When the task needs fallback/override layering, use `ConfigurationLoader.load_with_overrides()` instead of assuming a missing default config is harmless.

## Secrets and environment precedence

- System environment variables are the baseline.
- With default env-file behavior, `~/.pyrit/.env` loads first, then `~/.pyrit/.env.local` overrides it.
- With explicit `env_files=[...]`, only those files load, in the order supplied; later files override earlier files.
- With `env_akv_ref=[...]`, AKV secret contents load before env files, so local/custom env files can override secret values.
- Do not commit real `.env` or `.env.local` content. Keep only placeholder examples in repositories.
- Route target/scorer credential names and service-specific auth details to `../targets-scorers/SKILL.md` unless the task is only about loading environment values.

## Memory backend selection

| Backend | PyRIT value | What it is | Use when | Avoid when |
|---|---|---|---|---|
| In-memory | `"InMemory"` or config `in_memory` | A process-local `SQLiteMemory(db_path=":memory:")` assigned to `CentralMemory`. | Tests, smoke checks, examples, and no-persistence tasks. | You need results after process exit. |
| SQLite | `"SQLite"` or config `sqlite` | Local persistent `SQLiteMemory`; accepts `db_path`, `verbose`, `skip_schema_migration`, `silent`. | Reproducible local runs, small/medium result stores, offline review. | Multiple writers/users need a shared central database. |
| Azure SQL | `"AzureSQL"` or config `azure_sql` | Credentialed `AzureSQLMemory` plus Azure Blob storage for result payloads. | Shared team memory and server-backed scenarios. | No Azure SQL/ODBC/storage credentials, or no explicit requirement for shared state. |

For manual memory setup:

```python
from pyrit.memory import CentralMemory, SQLiteMemory

memory = SQLiteMemory(db_path=":memory:", silent=True)
CentralMemory.set_memory_instance(memory)
assert CentralMemory.get_memory_instance() is memory
```

`CentralMemory.get_memory_instance()` raises a `ValueError` until something calls `CentralMemory.set_memory_instance(...)` or `initialize_pyrit_async(...)` succeeds.

## Memory operations agents commonly need

Prompt targets and scorers usually write to memory automatically. Manual code can use the memory object for inspection, filtering, updates, and result retrieval.

```python
from pyrit.memory import CentralMemory
from pyrit.models import IdentifierFilter, IdentifierType

memory = CentralMemory.get_memory_instance()

# Label lookup for prompts/responses.
pieces = memory.get_message_pieces(labels={"operation": "demo"})

# Conversation reconstruction.
messages = memory.get_conversation_messages(conversation_id="conversation-id")

# Identifier-backed lookup, e.g. target class name.
target_filter = IdentifierFilter(
    identifier_type=IdentifierType.TARGET,
    property_path="$.class_name",
    value="TextTarget",
)
pieces_for_text_target = memory.get_message_pieces(identifier_filters=[target_filter])

# Scores by scorer identity.
scorer_filter = IdentifierFilter(
    identifier_type=IdentifierType.SCORER,
    property_path="$.class_name",
    value="SubStringScorer",
)
scores = memory.get_scores(identifier_filters=[scorer_filter])

# Attack results by labels or result ids.
results = memory.get_attack_results(labels={"operation": "demo"}, limit=20)
```

Label guidance:

- `GLOBAL_MEMORY_LABELS` can apply process-wide labels such as `operator` and `operation` to attack sends.
- Explicit labels passed to attack execution take precedence on key collisions.
- Label keys are meant to be simple names; avoid spaces, control characters, or ad-hoc punctuation. Use stable keys such as `operator`, `operation`, `stage`, `technique`, `harm_category`, or `language`.
- If a lookup returns nothing, verify whether labels are attached to prompts, attack results, or scenario results; PyRIT has separate query surfaces for each domain.

## Registry workflow

PyRIT registries have two layers:

1. A buildable class catalog: discover names, get metadata, and construct new instances by exact registered class name.
2. An optional `.instances` registry: store preconfigured named component instances, tags, and metadata.

```python
from pyrit.registry import ConverterRegistry

registry = ConverterRegistry(lazy_discovery=True)
class_names = registry.get_class_names()        # exact class names, e.g. Base64Converter
base64 = registry.create_instance("Base64Converter")

registry.instances.register(base64, name="offline_base64", tags=["offline"])
assert registry.instances.get("offline_base64") is base64
```

Registry rules to remember:

- Class catalog names are exact names such as `Base64Converter`, not snake-case aliases.
- `create_instance(name, **kwargs)` builds an object but does not store it in `.instances`.
- Unknown component names raise `KeyError` with available names.
- Unknown constructor parameters raise `ValueError`.
- Reference parameters can resolve by instance name from another registry; for example, an LLM-backed converter can resolve a `converter_target` from `TargetRegistry.instances`.
- Registering a second instance with the same instance name overwrites the earlier entry; choose names deliberately.
- Target/scorer instance selection and credentials belong in `../targets-scorers/SKILL.md`; converter schemas belong in `../converters-datasets/SKILL.md`.

## Output helper workflow

PyRIT output helpers render existing PyRIT model objects. They do not run attacks or create targets.

```python
from pathlib import Path
from pyrit.output import FileSink, output_conversation_async, output_score_async

# Render messages already retrieved from memory.
await output_conversation_async(messages, include_scores=True)

# Render scores to a caller-approved file.
sink = FileSink(path=Path("pyrit-scores.txt"), mode="w")
await output_score_async(scores, sink=sink)
```

Common helper ownership:

| Helper | Input | Formats | Notes |
|---|---|---|---|
| `output_attack_async` | `AttackResult` | `pretty`, `markdown` | Can include auxiliary/pruned/adversarial conversations; can blur image output for reviewer exposure reduction. |
| `output_scenario_async` | `ScenarioResult` | `pretty` only | Can sort groups by success rate. |
| `output_scorer_async` | scorer identifier | `pretty` only | Displays scorer metrics/information from memory. |
| `output_conversation_async` | list of `Message` | `pretty` only | Can include scores and reasoning summaries. |
| `output_score_async` | list of `Score` | `pretty` only | Simple score rendering. |

Sinks:

- `StdoutSink` prints to stdout.
- `FileSink(path=Path(...), mode="w" or "a")` writes UTF-8 text to an approved path.
- `IPythonMarkdownSink` renders Markdown in notebooks and falls back to printing outside notebooks.

When output appears empty or raises lookup errors, check that `CentralMemory` points at the database that contains the conversation/result ids being rendered.
