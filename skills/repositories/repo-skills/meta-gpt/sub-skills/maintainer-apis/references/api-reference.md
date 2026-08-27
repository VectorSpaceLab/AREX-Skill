# Maintainer API Reference

This reference lists the internal modules and contracts most likely to change during MetaGPT maintenance. Use repo-relative module paths as edit-point names inside a MetaGPT checkout; the bundled guidance and scripts are self-contained for runtime use.

## Serialization and Schema

| Module / class | Responsibility | Common edit points | Focused checks |
| --- | --- | --- | --- |
| `metagpt/base/base_serialization.py::BaseSerialization` | Pydantic v2 polymorphic serialization base | `__module_class_name`, subclass map registration, unknown subclass errors, `extra='forbid'` compatibility | `tests/metagpt/serialize_deserialize/test_polymorphic.py` |
| `metagpt/schema.py::SerializationMixin` | JSON file save/load wrapper over `model_dump()` and class construction | `get_serialization_path()`, `serialize(file_path)`, `deserialize(file_path)`, fallback JSON writing | `tests/metagpt/serialize_deserialize/test_*_save.py` |
| `metagpt/schema.py::Message` | Core message, routing metadata, instruct content, dump/load, RAG key | validators for `id`, `cause_by`, `sent_from`, `send_to`, `instruct_content`; serializers for `send_to` and `instruct_content` | `tests/metagpt/serialize_deserialize/test_schema.py`, `tests/metagpt/test_message.py` |
| `metagpt/schema.py::Task` / `TaskResult` / `Plan` | Task state, task updates, plan mutations exposed as tools | task result accumulation, reset/finish/replace behavior, default mutable fields | `tests/metagpt/test_schema.py` plus workflow tests if user-facing |
| `metagpt/schema.py::Document` / `Documents` | File/document wrappers used in action contexts and message instruct content | async loading, project-relative metadata, action-output conversion | `tests/metagpt/serialize_deserialize/test_schema.py` |
| `metagpt/schema.py::MessageQueue` | Async queue serialization/deserialization | queue drain/reinsert behavior, JSON list of message dumps, timeout handling | message queue tests or targeted async smoke |
| `metagpt/schema.py::LongTermMemoryItem` | RAG object wrapper for RoleZero long-term memory | `rag_key()` returning message content, created-at sorting | `tests/metagpt/memory/test_role_zero_memory.py` |

### Serialization Contracts

- Polymorphic Pydantic subclasses must include `__module_class_name` in dumps and must be imported before deserializing through the polymorphic base.
- `BaseSerialization` forbids extra fields; compatibility for old JSON belongs in validators/defaults, not by silently allowing unknown keys unless a deliberate migration needs it.
- `SerializationMixin.serialize()` returns the written path or `None` if `handle_exception` catches an error.
- `Message.dump()` uses `model_dump_json(exclude_none=True, warnings=False)`; `Message.load()` preserves an existing `id` after constructing a new message.
- `Message.send_to` serializes as a list but validates back to a set of stringified routes.

## Memory Modules

| Module / class | Responsibility | Key knobs / fields | Common edit points |
| --- | --- | --- | --- |
| `metagpt/memory/memory.py::Memory` | Short-term message storage and action index | `storage`, `index`, `ignore_id` | duplicate behavior, delete/index sync, `get(k)` slicing, `find_news()` semantics |
| `metagpt/memory/memory_storage.py::MemoryStorage` | FAISS-backed persistent role memory | `role_id`, `role_mem_path`, `threshold`, `embedding`, `faiss_engine` | lazy recovery, persist/clean paths, similarity threshold, embedding mocks |
| `metagpt/memory/longterm_memory.py::LongTermMemory` | Role memory that writes watched messages to `MemoryStorage` | `memory_storage`, `rc`, `msg_from_recover` | watch filtering, recovered-message suppression, async long-term filtering |
| `metagpt/memory/brain_memory.py::BrainMemory` | Chat history/knowledge cache and summaries | `history`, `knowledge`, `historical_summary`, `is_dirty`, `cacheable`, `config`, Redis key | config validator, Redis load/dump, summary/rewrite/title LLM calls |
| `metagpt/memory/role_zero_memory.py::RoleZeroLongTermMemory` | RoleZero memory split between recent messages and RAG long-term store | `persist_path`, `collection_name`, `memory_k`, `similarity_top_k`, `use_llm_ranker` | lazy RAG imports, transfer threshold, query construction, sorted retrieval |

### Memory Data Layouts

- `Memory.storage` is a list of `Message` objects; `index` maps `cause_by` strings to message lists.
- `MemoryStorage.recover_memory(role_id)` stores under a role-memory subdirectory and looks for `default__vector_store.json` to decide whether to load an existing FAISS index.
- `RoleZeroLongTermMemory` stores `LongTermMemoryItem(message=<Message>, created_at=<float>)` in a Chroma-backed RAG engine. Retrieved node metadata must contain `metadata['obj']`.
- `BrainMemory.to_metagpt_history_format()` emits JSON of `SimpleMessage(role, content)` dicts.

## Experience Pool

| Module / class | Responsibility | Key knobs / fields | Common edit points |
| --- | --- | --- | --- |
| `metagpt/configs/exp_pool_config.py::ExperiencePoolConfig` | Configures exp_pool behavior | `enabled`, `enable_read`, `enable_write`, `persist_path`, `retrieval_type`, `use_llm_ranker`, `collection_name` | defaults, YAML parsing, storage mode selection |
| `metagpt/exp_pool/schema.py::Experience` | Stored experience object | `req`, `resp`, `metric`, `exp_type`, `entry_type`, `tag`, `traj`, `timestamp`, `uuid` | tag filtering, RAG key, schema compatibility |
| `metagpt/exp_pool/manager.py::ExperienceManager` | CRUD/query lifecycle over RAG storage | `config`, lazy `_storage`, `is_readable`, `is_writable` | BM25/Chroma initialization, read/write gating, exact/tag filtering |
| `metagpt/exp_pool/decorator.py::exp_cache` | Function decorator for reusable experiences | `query_type`, `manager`, `scorer`, `perfect_judge`, `context_builder`, `serializer`, `tag` | `req` keyword validation, sync/async wrapper, context replacement, save flow |
| `metagpt/exp_pool/serializers/simple.py::SimpleSerializer` | Default request/response stringify serializer | `serialize_req`, `serialize_resp`, `deserialize_resp` | non-string compatibility, type loss is intentional |
| `metagpt/exp_pool/serializers/action_node.py::ActionNodeSerializer` | ActionNode response serializer | `instruct_content.model_dump_json()` wrapper | avoiding pickle failures, reconstructing minimal ActionNode |
| `metagpt/exp_pool/serializers/role_zero.py::RoleZeroSerializer` | Compact RoleZero request serializer | filters `Command Editor.read executed: file_path...`, optional `state_data` | embedding-size reduction, relevant editor-read context |
| `metagpt/exp_pool/context_builders/*` | Builds prompts/contexts from experiences | `SimpleContextBuilder`, `RoleZeroContextBuilder`, `ActionNodeContextBuilder` | deep-copy behavior, `EXPERIENCE_MASK` replacement, empty-experience fallbacks |
| `metagpt/exp_pool/scorers/*` | Scores generated responses | `SimpleScorer` uses LLM JSON output to `Score` | mocked LLM responses, JSON parse failures |
| `metagpt/exp_pool/perfect_judges/*` | Decides whether a stored exp can short-circuit | `SimplePerfectJudge` | exact request/response validity rules |

### Experience Pool Flow

1. `exp_cache` checks global exp_pool enablement.
2. `ExpCacheHandler` validates `req` keyword, resolves defaults, serializes the request, and generates a tag.
3. The manager queries stored experiences by semantic or exact retrieval and optional tag.
4. A perfect judge can return deserialized stored response without calling the wrapped function.
5. Otherwise a context builder injects experiences, the function runs, a serializer captures response, a scorer evaluates it, and the manager saves an `Experience` when writing is enabled.

## Skill Management

| Module / class | Responsibility | Common edit points | Risk |
| --- | --- | --- | --- |
| `metagpt/management/skill_manager.py::SkillManager` | In-memory `Action` registry plus Chroma searchable store | add/delete/get/retrieve behavior, metadata shape, prompt desc generation | optional Chroma/vector dependencies and persistent local store state |
| `Skill = Action` alias | Treats Action subclasses as skills | API compatibility with `Action.name` and `Action.desc` | action constructor/config side effects |

Expected search return shape:

- `retrieve_skill(desc, n_results=2)` returns `store.search(...)["ids"][0]`.
- `retrieve_skill_scored(desc, n_results=2)` returns the full search dict from the store.

## Repository Parser and Diagrams

| Module / class | Responsibility | Common edit points | Focused checks |
| --- | --- | --- | --- |
| `RepoFileInfo` | Per-file classes/functions/globals/page metadata | output shape, model serialization | `test_repo_parser.py::test_repo_parser` |
| `CodeBlockInfo` | AST node metadata for code blocks | supported node types, line number assumptions | parser unit tests |
| `DotClassAttribute` | Parses pyreverse attribute strings | Literal handling, composition extraction, defaults | `test_parse_member` |
| `DotClassMethod` / `DotReturn` | Parses pyreverse method signatures | generic types, italic markers, return type parsing | `test_parse_method` |
| `DotClassInfo` / `DotClassRelationship` | Structured class and relationship metadata | sorting, relationship labels | dot split tests |
| `RepoParser` | AST symbol generation and pyreverse class-view rebuilding | file walking, JSON/CSV output, `pyreverse` command, namespace repair | `tests/metagpt/test_repo_parser.py` |

Generated outputs/caches to expect:

- `generate_structure(mode='json')` writes `<base-name>-structure.json` by default.
- `generate_structure(mode='csv')` writes `<base-name>-structure.csv` by default.
- `rebuild_class_views()` writes temporary dot files under a `__dot__` directory and removes parsed dot files afterward.

## YAML and Config Models

| Module / class | Responsibility | Common edit points | Notes |
| --- | --- | --- | --- |
| `metagpt/utils/yaml_model.py::YamlModel` | YAML read/write plus Pydantic validation | empty YAML handling, model dump shape, encoding | `yaml.safe_load` can return `None`; missing files return `{}` |
| `YamlModelWithoutDefault` | Rejects placeholder secret values | validator over incoming values | only catches direct values containing `YOUR` |
| `metagpt/config2.py::Config` | Global merged config model | merge priority, cache invalidation, CLI fields, defaults | `Config.default()` can fail on placeholder LLM key |
| `CLIParams` | Project path/name/inc CLI params | `project_path` forces `inc=True` and project name | user-facing flow routes to `software-company` |
| `LLMConfig` | Provider-independent LLM config | API type enum, API key validator, timeout default | placeholder keys intentionally raise |
| `ModelsConfig` | Named model map | model-name defaulting, home/repo config merge | `get()` by name or API type |
| `WorkspaceConfig` | Workspace root and uid handling | path conversion, uid/path mutation | creates directories during validation |
| `ExperiencePoolConfig` | Experience pool feature flags and storage mode | BM25/Chroma defaults, LLM ranker flag | exp_pool tests often inject explicit config |
| `RedisConfig` / `S3Config` | Required external service config | placeholder rejection, URL/kwargs helpers | skip without service credentials |

## Diagnostics Scripts

| Bundled script | Purpose | Safety profile |
| --- | --- | --- |
| `scripts/list_public_symbols.py` | AST-based inventory of classes/functions under a module/package path or file | Does not import target modules; safe for config/provider-heavy packages |

Reference-only source scripts:

- Original class/function shell helper: replaced by the bundled Python helper because shell grep is less structured and assumes a checkout layout.
- Coverage helper: useful as provenance for coverage intent, but broad pytest + coverage + browser-open behavior is not a safe default.
- Dependency installer helper: mutates Python/npm/browser environments and should only run with explicit user approval.
