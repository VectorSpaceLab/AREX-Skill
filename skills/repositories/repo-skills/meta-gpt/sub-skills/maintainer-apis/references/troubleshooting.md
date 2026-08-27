# Maintainer Troubleshooting

Use this matrix to diagnose common MetaGPT maintainer failures without accidentally running provider, browser, vector-store, or broad dependency workflows.

## Quick Symptom Matrix

| Symptom | Likely cause | First check | Safe response |
| --- | --- | --- | --- |
| `Please set your API key in config2.yaml` during import/test | `Config.default()` or `LLMConfig()` hit placeholder validation | Look for model defaults, global config import, or validator-created config | Construct explicit `Config(llm=LLMConfig(api_key='sk-test'))` or patch `Config.default()` in focused tests |
| `Missing __module_class_name field` | Deserializing through polymorphic base without class metadata | Inspect dumped JSON/model output | Preserve `BaseSerialization` serializer or add migration for old payloads |
| `Trying to instantiate <class>, which has not yet been defined` | Polymorphic subclass not imported/registered before validation | Check import path and subclass registration | Import owning module before deserialize or add safe dynamic-import handling with tests |
| Pydantic `extra_forbidden` / validation errors after schema change | `BaseSerialization` forbids extras or new required field lacks default | Compare old serialized JSON shape | Add defaults/validators/migration tests instead of loosening broadly |
| `KeyError: missing required key to init Message.instruct_content from dict` | `Message.instruct_content` dict lacks `mapping` or `module` | Inspect serialized `instruct_content` dict | Preserve one of the two supported instruct-content payload shapes |
| `cannot pickle 'SSLContext' object` around ActionNode experiences | ActionNode response serialized with generic pickle/string path | Check exp_pool serializer | Use `ActionNodeSerializer` JSON wrapper for `instruct_content` |
| Memory tests try real embeddings | Optional RAG/embedding imports reached before mocks or mocks not applied | Check import traceback and patch paths | Run short-term memory tests first; add mocked embedding patches or skip optional backend |
| RoleZero long-term memory returns no related memories | Capacity/user-message gates not satisfied | Check `k`, latest message role/cause, and `memory_k` count | Build tests that satisfy all `_should_use_longterm_memory_for_get` conditions |
| exp_pool query returns empty | `enabled`, `enable_read`, tag, or query type mismatch | Inspect `ExperiencePoolConfig` and stored `Experience.tag`/`req` | Enable read explicitly; use `QueryType.EXACT` for exact `req` matching |
| Skill manager retrieval fails on import | Chroma/document-store optional dependency missing | Import `SkillManager` and dependency stack only | Route dependency resolution to RAG/tool guidance; skip if dependency install not approved |
| Repo parser Mermaid/dot output fails | `pyreverse`, package `__init__.py`, Graphviz/Mermaid tooling, or dot syntax issue | Run parser unit tests before diagram rebuild | Treat diagram rebuild/render as optional; keep AST parsing healthy first |
| `yaml.safe_load` output causes model error | Empty or placeholder YAML values | Check raw YAML and required fields | Return `{}` for missing files, add empty-file handling if needed, validate placeholders intentionally |
| Pytest collection errors continue | `pytest.ini` uses `--continue-on-collection-errors` | Rerun one file with `--collect-only` | Fix import/optional dependency issue or record explicit skip |

## Config Validation and Placeholder API Keys

`LLMConfig.api_key` rejects `''`, `None`, and `YOUR_API_KEY`. `Config.default()` merges environment variables, repository config, user config, and explicit kwargs, then instantiates `Config`; any placeholder in the resulting LLM config can fail before a test fixture has a chance to run.

Avoid this in maintainer tests:

```python
from metagpt.config2 import Config
cfg = Config.default()
```

Prefer explicit config:

```python
from metagpt.config2 import Config
from metagpt.configs.llm_config import LLMConfig
cfg = Config(llm=LLMConfig(api_key="sk-test"))
```

If code under test calls `Config.default()` internally, patch it:

```python
def test_uses_default_config(mocker):
    cfg = Config(llm=LLMConfig(api_key="sk-test"))
    mocker.patch("metagpt.config2.Config.default", return_value=cfg)
```

Also check validators that create default config indirectly:

- `BrainMemory.config` validator calls `Config.default()` when no config is provided.
- `ExperienceManager.config` default factory calls `Config.default()`.
- Module-level `metagpt.config2.config = Config.default()` can fail at import time in bad environments.

## Pydantic v2 Serialization Differences

MetaGPT uses Pydantic v2 features in maintainer APIs:

- `@model_serializer(mode='wrap')` in `BaseSerialization` appends `__module_class_name`.
- `@model_validator(mode='wrap')` converts base-class input to the real subclass.
- `@field_validator(..., mode='before')` normalizes `Message` routing fields and instruct content before validation.
- `@field_serializer(..., mode='plain')` controls `Message.send_to` and `Message.instruct_content` dumps.
- `SerializeAsAny[Message]` is used where subclass fields must survive dumps.

Common fix patterns:

- Add defaults for new fields if old serialized JSON should still load.
- Use `model_validate_json()` / `model_dump_json()` in tests rather than Pydantic v1 `parse_raw()` patterns unless compatibility is intentional.
- Keep `SerializeAsAny` on polymorphic lists; without it, subclass-only fields are omitted.
- Avoid mutable class-level defaults in new models; use `Field(default_factory=...)` unless matching existing behavior is intentional.

## Pickle and JSON Compatibility

Some internal objects cannot be safely pickled or stringified with full fidelity:

- `ActionNode` can include objects such as SSL contexts through nested fields; use `ActionNodeSerializer` to preserve `instruct_content.model_dump_json()` and reconstruct a minimal `ActionNode`.
- `SimpleSerializer` intentionally converts request/response values with `str()`, so types are not round-tripped.
- `Message.instruct_content` supports Pydantic model reconstruction only when serialized with `class` plus either `mapping` or `module`.
- `SerializationMixin.serialize()` writes JSON with fallback behavior; failures may be swallowed by `handle_exception` and return `None`.

When a deserialize test fails, inspect the exact dumped payload before changing validators.

## Memory Persistence Issues

### Short-Term Memory

Symptoms:

- Duplicate messages do not add.
- `get_by_action()` returns empty.
- Deleting a message leaves stale index entries.

Checks:

- `Message.__eq__` through Pydantic value equality can treat identical messages as duplicates.
- `ignore_id=True` rewrites IDs to the ignored ID before add/delete.
- `cause_by` is string-normalized; compare with `any_to_str(ActionClass)`.

### `MemoryStorage` / `LongTermMemory`

Symptoms:

- Missing FAISS/vector files.
- Similarity search returns surprising empty/non-empty results.
- Real embedding calls occur during tests.

Checks:

- `recover_memory(role_id)` initializes path, cache directory, and FAISS engine.
- Existing `default__vector_store.json` selects `SimpleEngine.from_index`; absence selects `from_objs([])`.
- `search_similar()` keeps items whose score is lower than `threshold`.
- `LongTermMemory.add()` writes only messages whose `cause_by` is watched by the role context and not during recovery.

Safe response:

- Use temporary persistence paths and mocked embedding methods.
- Route generic RAG/vector-store dependency diagnosis to `rag-and-tools`.

### `BrainMemory`

Symptoms:

- Redis connection/config errors.
- Placeholder config errors.
- Summary/title/rewrite tries LLM calls.

Checks:

- Pass explicit `config` with Redis settings only when Redis is available.
- `dumps()` no-ops if `is_dirty` is false or redis key is empty.
- `summarize()`, `get_title()`, `is_related()`, and `rewrite()` can call an LLM unless using `MetaGPTLLM` branches.

## Experience Pool Storage Issues

Symptoms:

- No experiences retrieved.
- Stored experiences not persisted.
- BM25/Chroma initialization fails.
- LLM ranker imports or calls fail.

Checks:

- `config.exp_pool.enabled` must be true for `exp_cache` to do anything.
- `enable_read` must be true for `query_exps()` to return results.
- `enable_write` must be true for `create_exp()` and `delete_all_exps()` to mutate storage.
- `retrieval_type` must be `BM25` or `CHROMA`; BM25 checks for `docstore.json` under `persist_path`.
- `use_llm_ranker=True` adds `LLMRankerConfig`, which may require valid LLM config.
- Tags default to `ClassName.method_name` for methods or function name for functions.

Safe response:

- Inject mock storage for manager logic.
- Use `QueryType.EXACT` in tests that should not depend on vector similarity.
- Disable `use_llm_ranker` unless explicitly validating ranker integration.
- Use temp `persist_path` and clear it after tests.

## Optional Dependencies and Provider Failures

Common optional stacks:

- RAG/vector stores for memory, exp_pool, document stores, and skill manager.
- Provider SDKs/API keys for LLMs, embeddings, search, speech/image, and cloud APIs.
- Browser/Mermaid/Graphviz tooling for diagrams and browser tests.
- Redis/S3 for external storage configs.

Rules:

- Treat missing optional dependencies as skips unless the user asks to prepare the environment.
- Do not run broad install scripts without explicit approval; they can install test extras, global npm packages, and browser dependencies.
- Keep provider keys out of tests, docs, generated skill content, and logs.
- For import-only diagnostics, prefer AST helpers and `importlib.util.find_spec()` over importing deep modules that instantiate config.

## Generated Files and Cache Issues

Expected generated outputs during maintainer work can include:

- `cov.xml`, `htmlcov/`, `.coverage*` from coverage.
- `*-structure.json` / `*-structure.csv` from `RepoParser.generate_structure()`.
- `__dot__/` from `RepoParser.rebuild_class_views()`.
- Role memory/vector-store directories from memory tests.
- Chroma/BM25 persistence directories from exp_pool/skill manager tests.
- Response cache JSON updates from LLM mock fixtures.

Safe cleanup:

- Prefer `tmp_path` in tests so cleanup is automatic.
- If a generated output appears in the source tree, confirm it is test output before deleting.
- Do not include coverage, cache, vector-store, or review artifacts in public runtime skill files.

## Repo Parser Mermaid/Dot Issues

Symptoms:

- `ValueError: Failed to import module __init__...`
- `pyreverse` command failure.
- Empty class/relationship output.
- Mermaid rendering breaks after dot parsing changes.

Checks:

- Target path exists and contains `__init__.py` when calling `rebuild_class_views()`.
- `pyreverse` from `pylint` is installed and executable.
- Dot parsing helpers still pass unit tests for class lines, method signatures, relationships, `Literal[...]`, and generic type strings.
- Mermaid rendering is downstream of dot parsing; fix parser output before renderer behavior.

Safe response:

```bash
pytest tests/metagpt/test_repo_parser.py -q
python sub-skills/maintainer-apis/scripts/list_public_symbols.py --module metagpt.repo_parser --json
```

Only run pyreverse/Mermaid/browser rendering when the required local tools are installed and the user accepts generated files.
