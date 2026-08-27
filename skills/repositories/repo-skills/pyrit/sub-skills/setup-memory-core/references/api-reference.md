# Setup, Memory, Registry, Models, and Output API Reference

Read this when writing PyRIT initialization or persistence code. The signatures below were verified from the installed PyRIT package for this skill baseline.

## Initialization

| API | Use | Verified signature notes |
|---|---|---|
| `pyrit.setup.initialize_pyrit_async` | Programmatic bootstrap for a process. | `initialize_pyrit_async(memory_db_type, *, initialization_scripts=None, initializers=None, load_defaults=True, env_files=None, env_akv_ref=None, silent=False, **memory_instance_kwargs)` |
| `pyrit.setup.initialize_from_config_async` | Load PyRIT from a config file, normally from PyRIT home or an explicit path. | `initialize_from_config_async(config_path=None) -> ConfigurationLoader` |
| `PyRITInitializer` subclasses | Register default targets, scorers, datasets, or techniques. | Initializers are ordered and may be supplied directly or through config. |

Use `InMemory` for short no-persistence runs, `SQLite` for local persistence, and `AzureSQL` only when the caller has explicitly supplied service configuration and credentials.

## Memory

| API | Use | Notes |
|---|---|---|
| `CentralMemory()` | Singleton-style access to the current memory instance after initialization. | Use after successful initialization; stale process globals are a common source of surprising reads. |
| `SQLiteMemory(*args, **kwargs)` | Local SQLite implementation of the memory interface. | Use a caller-approved database path or a temporary path for tests. |
| `MemoryInterface` methods | Store/retrieve prompts, scores, attack results, conversations, scenario results, and identifiers. | Prefer model objects over ad-hoc dicts so serialization is stable. |

Memory owns persistence only; it does not decide prompts, conversions, scoring, or attack branching.

## Registry and identifiers

PyRIT registries discover and instantiate components. Use class registries for available component types and instance registries for named configured objects.

- `ConverterRegistry(lazy_discovery=True)` discovers converter classes and builds converter instances.
- Parallel registries exist for targets, scorers, scenarios, initializers, and attack techniques.
- Identifier models under `pyrit.models.identifiers` encode component names/config hashes so memory and results can be compared across runs.
- When a registry lookup fails, check the registered name, the class-vs-instance distinction, and whether the initializer that registers custom objects actually ran.

## Core models

Important models include `Message`, `MessagePiece`, `Score`, seed models, `AttackResult`, and `ScenarioResult`. Use constructors from `pyrit.models` rather than free-form dicts when passing data between components.

`Score` requires a `score_value`, `score_type`, `message_piece_id`, and related metadata. `SeedPrompt` supports `value`, metadata fields, `data_type`, `parameters`, and template flags.

## Output helpers

Use `pyrit.output.helpers` to render attack results, scenario results, conversations, scorers, and scores. Format/sink selection is separated from PyRIT memory retrieval; avoid direct `print()` inside reusable workflows except through explicit user-facing sinks.

## Safe inspection

Run `scripts/setup_memory_smoke.py --json` from this sub-skill to verify that the installed package exposes the expected APIs without contacting external services or writing persistent state.
