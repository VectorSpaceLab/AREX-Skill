# Maintainer API Workflows

Use these workflows for safe internal maintenance. Start specific, keep provider/network/browser work skipped until prerequisites are explicit, and use focused pytest commands before coverage or broad suites.

## Focused Test Selection

| Change area | Start with | Add when relevant | Skip unless prerequisites exist |
| --- | --- | --- | --- |
| Serialization / schema | `pytest tests/metagpt/serialize_deserialize/test_schema.py -q` | `pytest tests/metagpt/serialize_deserialize -q --ignore-glob='*__pycache__*'` | Async role/action tests that rely on missing response cache or provider config |
| `Message`, `Task`, context models | `pytest tests/metagpt/test_schema.py tests/metagpt/serialize_deserialize/test_schema.py -q` | `pytest tests/metagpt/serialize_deserialize/test_memory.py -q` | Full software-company recovery unless routed through `software-company` |
| Short-term memory | `pytest tests/metagpt/memory/test_memory.py -q` | `pytest tests/metagpt/serialize_deserialize/test_memory.py -q` | Long-term/RAG-backed memory without mocked embeddings |
| Long-term / RoleZero memory | `pytest tests/metagpt/memory/test_role_zero_memory.py -q` | `pytest tests/metagpt/memory/test_memory_storage.py tests/metagpt/memory/test_longterm_memory.py -q` | Real embedding/vector backends unless mocked or explicitly configured |
| Experience pool | `pytest tests/metagpt/exp_pool/test_manager.py -q` | `pytest tests/metagpt/exp_pool/test_context_builders tests/metagpt/exp_pool/test_serializers -q` | `test_decorator.py` or scorer tests if LLM mocks/response cache are unavailable |
| Skill manager | `pytest tests/metagpt/management/test_skill_manager.py -q` | Add import checks for `chromadb`/document-store dependencies | Mutating broad dependency installs |
| Repo parser | `pytest tests/metagpt/test_repo_parser.py -q` | Symbol helper run with `scripts/list_public_symbols.py` | `pyreverse`/Mermaid output unless `pylint`/Graphviz are installed |
| Config models | `pytest tests/metagpt/configs/test_models_config.py -q` | Model construction smoke tests with explicit `LLMConfig(api_key='sk-test')` | `Config.default()` with placeholder keys or user home config assumptions |

`pytest.ini` already enables coverage, doctest modules, `--continue-on-collection-errors`, and many `--ignore` entries. When running a single ignored file explicitly, pytest can still collect it; make that an intentional maintainer decision and expect optional dependencies to matter.

## Serialization and Schema Maintenance

1. Identify the owning model: `BaseSerialization` for polymorphic Pydantic dispatch, `SerializationMixin` for JSON file save/load, `Message` for routing/instruct content, `Task`/`Plan` for task state, and role/action classes for `SerializeAsAny` fields.
2. Preserve the `__module_class_name` contract on polymorphic models. Missing values fail base deserialization; unknown values fail when the subclass has not been imported/registered.
3. For `Message.instruct_content`, preserve both supported payload shapes:
   - ActionNode-created models use `{"class": <schema title>, "mapping": <mapping string>, "value": {...}}`.
   - Normal Pydantic models use `{"class": <schema title>, "module": <module>, "value": {...}}`.
4. For field additions, decide whether old serialized JSON should load without the field. Prefer defaults or compatibility validators over breaking historic serialized teams/messages.
5. Verify with the smallest matching file, then broaden to `tests/metagpt/serialize_deserialize` only if the change touches role/action/team compatibility.

Safe local smoke snippets:

```bash
pytest tests/metagpt/serialize_deserialize/test_schema.py -q
pytest tests/metagpt/serialize_deserialize/test_polymorphic.py -q
pytest tests/metagpt/serialize_deserialize/test_memory.py -q
```

Cross-link: if serialization failures appear while recovering a generated project or `Team`, route the user-facing command flow through `software-company` and return here for internal model fixes.

## Memory Maintenance

1. Separate in-memory behavior from persistence:
   - `Memory` stores `Message` objects, indexes by `cause_by`, and supports role/content/action lookups.
   - `MemoryStorage` persists vector-backed role memory using FAISS through the RAG `SimpleEngine`.
   - `LongTermMemory` extends `Memory` and writes watched messages into `MemoryStorage`.
   - `BrainMemory` stores history/knowledge and can cache through Redis.
   - `RoleZeroLongTermMemory` transfers old messages to a Chroma-backed RAG store and retrieves related long-term messages.
2. For short-term memory changes, avoid embedding/RAG dependencies; test `Memory` first.
3. For `MemoryStorage` and `LongTermMemory`, use mocked embedding tests. Real OpenAI embeddings or vector services are external prerequisites.
4. For `BrainMemory`, construct or mock config explicitly; its `config` validator calls `Config.default()` when no config is provided, which may fail with placeholder API keys.
5. For RoleZero memory, check capacity gates: add transfers when `count() > memory_k`; get combines long-term memory only when `k != 0`, the latest message is a user requirement/team-leader message, and stored count exceeds `memory_k`.

Safe commands:

```bash
pytest tests/metagpt/memory/test_memory.py -q
pytest tests/metagpt/memory/test_role_zero_memory.py -q
pytest tests/metagpt/memory/test_memory_storage.py -q
```

## Experience Pool Maintenance

1. Start with `ExperiencePoolConfig`: `enabled` gates the decorator, `enable_read` gates retrieval, `enable_write` gates save/delete, `persist_path` selects storage location, `retrieval_type` selects BM25 or Chroma, `use_llm_ranker` adds an LLM ranker, and `collection_name` names Chroma collections.
2. `ExperienceManager` lazily resolves storage. Inject `manager._storage` in focused tests to avoid initializing RAG backends.
3. `query_exps(req, tag='', query_type=SEMANTIC)` retrieves nodes, extracts `metadata['obj']`, filters by tag, then exact-matches `exp.req` for `QueryType.EXACT`.
4. `exp_cache` requires `req` as a keyword argument. It serializes the request, optionally returns a perfect experience, otherwise runs the function, scores, and saves an `Experience`.
5. Serializer changes must keep response round-trip behavior explicit: `SimpleSerializer` stringifies everything; `ActionNodeSerializer` avoids pickling an `ActionNode` by preserving `instruct_content.model_dump_json()`; RoleZero serializer filters command context for relevant editor reads.
6. Context builder changes must not mutate the original request unless they deliberately deep-copy first. RoleZero context builder copies and replaces `EXPERIENCE_MASK` content.

Safe commands:

```bash
pytest tests/metagpt/exp_pool/test_manager.py -q
pytest tests/metagpt/exp_pool/test_serializers -q
pytest tests/metagpt/exp_pool/test_context_builders -q
pytest tests/metagpt/exp_pool/test_perfect_judges/test_simple_perfect_judge.py -q
```

Run `tests/metagpt/exp_pool/test_decorator.py` only when LLM mocks, RAG imports, and config fixtures are healthy. It is ignored by the default pytest configuration for a reason.

## Skill Manager and Repo Parser Updates

### Skill Manager

1. Treat `SkillManager` as a thin Action-skill registry backed by a Chroma document store named `skill_manager`.
2. `add_skill(skill)` stores by `skill.name` and indexes `skill.desc` with metadata `name`/`desc`.
3. `del_skill(skill_name)` removes both the in-memory skill and vector-store entry; guard missing keys if changing behavior.
4. `retrieve_skill(desc, n_results=2)` returns the first ID list from Chroma search; `retrieve_skill_scored(...)` returns the full search dictionary.
5. If tests fail on Chroma/import/storage setup, route dependency analysis to `rag-and-tools`; do not install broad dependencies without user approval.

Safe command:

```bash
pytest tests/metagpt/management/test_skill_manager.py -q
```

### Repo Parser

1. `RepoParser.generate_symbols()` walks `*.py`, parses AST, and emits `RepoFileInfo` with classes, functions, globals, and `page_info` code-block metadata.
2. `generate_structure(mode='json'|'csv')` writes a structure file under the parsed base directory unless an output path is given.
3. Dot/Mermaid class-view parsing uses `DotClassAttribute`, `DotClassMethod`, `DotReturn`, `DotClassInfo`, and `DotClassRelationship`; test their parsing helpers before touching `rebuild_class_views`.
4. `rebuild_class_views(path)` shells out to `pyreverse`, writes under `__dot__`, parses `classes.dot`, and repairs namespaces. This needs `pylint`/pyreverse and can fail if the target lacks `__init__.py`.
5. Mermaid rendering issues usually belong to downstream visualization utilities; repo parser fixes should preserve dot parsing first.

Safe commands:

```bash
pytest tests/metagpt/test_repo_parser.py -q
python sub-skills/maintainer-apis/scripts/list_public_symbols.py --module metagpt.repo_parser --json
```

## Config Model Changes

1. `YamlModel` reads with `yaml.safe_load`, validates through Pydantic, and writes `model_dump()` with `yaml.dump`.
2. `YamlModelWithoutDefault` rejects any incoming value containing `YOUR`; use this for required secret/service configs such as Redis or S3.
3. `Config.default()` merges environment variables, repository config, user config, and explicit kwargs; it caches by default paths. Use `reload=True` when a test intentionally changes config files.
4. `LLMConfig.api_key` rejects `''`, `None`, and `YOUR_API_KEY`. Placeholder failures are expected when a caller instantiates default config without test fixtures.
5. `WorkspaceConfig` creates its workspace path and appends a timestamp/uuid when `use_uid` is true; tests that construct it may write directories.
6. `ModelsConfig.default()` reads model maps from config files and uses model names as defaults if model fields are omitted.

Safe commands:

```bash
pytest tests/metagpt/configs/test_models_config.py -q
python - <<'PY'
from metagpt.config2 import Config
from metagpt.configs.llm_config import LLMConfig
cfg = Config(llm=LLMConfig(api_key='sk-test'))
print(cfg.llm.api_type.value, cfg.exp_pool.enabled)
PY
```

## Public Symbol Inventory

Use the bundled AST helper when a user asks for a public API inventory or when config-model/API changes need documentation updates. The helper intentionally does not import the target package, so it avoids provider configuration, optional dependencies, and import-time side effects.

Examples:

```bash
python sub-skills/maintainer-apis/scripts/list_public_symbols.py --module metagpt.configs --max-depth 2
python sub-skills/maintainer-apis/scripts/list_public_symbols.py --module metagpt.exp_pool --json
python sub-skills/maintainer-apis/scripts/list_public_symbols.py metagpt/schema.py --include-private --json
```

Use the output to map added/removed classes and functions to tests and docs. Do not use the original shell helper for runtime diagnostics; this Python script is the maintained bundled replacement.

## Coverage and Reports

The original coverage helper runs coverage over repo tests with parallel pytest, a timeout, HTML output, and attempts to open `htmlcov/index.html`. Treat that as reference-only because it can run broad tests, require plugins, write reports, and open a browser.

Safer progression:

```bash
pytest <focused-test-file-or-dir> -q
pytest <focused-test-file-or-dir> --cov=metagpt.<module> --cov-report=term-missing -q
pytest -q --maxfail=1 <expanded-area>
```

Run broad coverage only after focused maintainer tests pass and the user accepts the cost/optional dependency risk. Keep generated coverage directories, caches, and reports out of runtime skill content.
