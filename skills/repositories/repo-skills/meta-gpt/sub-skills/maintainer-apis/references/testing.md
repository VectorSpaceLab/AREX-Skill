# Maintainer Testing Guide

MetaGPT maintainer tests are not safe to run as one broad default. Use explicit focused commands, understand `pytest.ini` collection behavior, and skip provider/network/browser/device work unless prerequisites are present.

## What `pytest.ini` Does

The repository test configuration sets:

- `testpaths = tests` so a bare `pytest` starts from the full test tree.
- `--continue-on-collection-errors` so collection problems do not immediately abort the entire configured run.
- `--doctest-modules` so doctest collection can touch source modules.
- `--cov=./metagpt/`, XML coverage, HTML coverage, and `--durations=20` by default.
- A long list of `--ignore=...` entries for provider, RAG, tool, role, software-company, memory, exp_pool, and many utility tests.
- `norecursedirs` includes `tests/metagpt/serialize_deserialize`, so serialization tests are excluded from normal discovery unless explicitly selected.

Implications:

- A bare `pytest` is broader, slower, and more side-effectful than it looks because coverage/doctest are enabled.
- Ignored files can still be run intentionally by naming the file or directory on the command line.
- `serialize_deserialize` must be named explicitly when validating serialization changes.
- Collection errors can be masked in broad runs; inspect output and rerun focused commands when changing imports.

## Safe Focused Commands

Run from the repository root of a MetaGPT checkout with the package importable.

### Serialization / Schema

```bash
pytest tests/metagpt/serialize_deserialize/test_schema.py -q
pytest tests/metagpt/serialize_deserialize/test_polymorphic.py -q
pytest tests/metagpt/serialize_deserialize/test_memory.py -q
```

Broaden when touching role/action/team serialization:

```bash
pytest tests/metagpt/serialize_deserialize -q
```

Expect some async role/action serialization tests to depend on mocked LLM cache fixtures. If they try to spend real provider calls, stop and check mocks/config before retrying.

### Message / Core Schema

```bash
pytest tests/metagpt/test_schema.py -q
pytest tests/metagpt/test_message.py -q
```

These may be ignored in default config but are appropriate when directly editing `Message`, context models, or schema helpers.

### Memory

```bash
pytest tests/metagpt/memory/test_memory.py -q
pytest tests/metagpt/memory/test_role_zero_memory.py -q
```

Add only after dependency/mocks are present:

```bash
pytest tests/metagpt/memory/test_memory_storage.py tests/metagpt/memory/test_longterm_memory.py -q
pytest tests/metagpt/memory/test_brain_memory.py -q
```

`test_memory_storage.py` and `test_longterm_memory.py` patch OpenAI embedding methods with deterministic mock embeddings. If import errors occur before patching, the RAG/embedding optional stack is missing.

### Experience Pool

```bash
pytest tests/metagpt/exp_pool/test_manager.py -q
pytest tests/metagpt/exp_pool/test_serializers -q
pytest tests/metagpt/exp_pool/test_context_builders -q
pytest tests/metagpt/exp_pool/test_perfect_judges/test_simple_perfect_judge.py -q
```

Add only when mocks/config are healthy:

```bash
pytest tests/metagpt/exp_pool/test_decorator.py -q
pytest tests/metagpt/exp_pool/test_scorers/test_simple_scorer.py -q
```

The decorator/scorer path can involve LLM scoring, RAG storage imports, and global `Config.default()` behavior. Prefer injected manager/scorer/perfect-judge mocks.

### Skill Manager

```bash
pytest tests/metagpt/management/test_skill_manager.py -q
```

This exercises Chroma-backed skill retrieval. If it fails on optional dependencies or persistent store state, diagnose the dependency/store first; do not broaden to full RAG tests automatically.

### Repo Parser

```bash
pytest tests/metagpt/test_repo_parser.py -q
```

This covers AST symbol generation and dot parsing helpers. `RepoParser.rebuild_class_views()` requires `pyreverse`/`pylint` and package `__init__.py` files; treat diagram rebuilds as optional diagnostics.

### Config Models

```bash
pytest tests/metagpt/configs/test_models_config.py -q
```

For direct model smoke tests, avoid `Config.default()` unless user config is known valid:

```bash
python - <<'PY'
from metagpt.config2 import Config
from metagpt.configs.llm_config import LLMConfig
cfg = Config(llm=LLMConfig(api_key='sk-test'))
print(cfg.llm.api_type.value)
PY
```

## Collection Errors and Import Failures

When pytest reports collection errors:

1. Check whether the selected test is normally ignored by `pytest.ini`.
2. Identify whether failure occurs at import time before fixtures can patch providers/embeddings.
3. Reproduce with a single test file and `-q` before adding verbosity.
4. If optional dependencies are missing, record the skip/prerequisite instead of installing broad extras by default.
5. If placeholder config is the cause, construct explicit test config or patch `Config.default()` in tests.

Useful focused diagnostics:

```bash
python -m pytest --collect-only tests/metagpt/serialize_deserialize/test_schema.py -q
python -m pytest --collect-only tests/metagpt/exp_pool/test_manager.py -q
python -m pytest --collect-only tests/metagpt/memory/test_role_zero_memory.py -q
```

## Mock Fixtures and Safe Config Patterns

`tests/conftest.py` provides important safety fixtures:

- `llm_mock` patches base LLM calls and OpenAI code calls through a response-cache mock.
- `context` builds a `MetagptContext`, points `config.project_path` to a temporary git repository, and deletes it after the test.
- `new_filename` patches file-repository filename generation for deterministic LLM prompts.
- Search/browser HTTP fixtures mock `aiohttp`, `curl_cffi`, and `httplib2` for specific tests.

Patterns to use in new maintainer tests:

- Construct `Config(llm=LLMConfig(api_key='sk-test'), ...)` instead of relying on user config.
- Inject `ExperienceManager._storage = mock_storage` when testing manager logic.
- Patch `ExperienceManager._resolve_storage()` when testing lazy initialization.
- Patch embedding methods before invoking memory-storage retrieval if optional packages import successfully.
- Use `tmp_path` for persistence paths and clean generated directories.
- Use `pytest.mark.asyncio` for async memory/exp_pool/schema workflows.

## Ignored and Optional Tests

Default ignored areas include many tests that require or risk:

- Provider credentials: OpenAI, Anthropic, Bedrock, Qianfan, ZhipuAI, Ark, DashScope, search providers.
- Browser/device tooling: Playwright, Selenium, Mermaid CLI, Android/environment integrations.
- RAG/vector stores: FAISS, Chroma, Elasticsearch, Milvus/Qdrant/LanceDB-style dependencies depending on import path.
- Long LLM/project-generation workflows: roles, actions, software-company, DI/RoleZero benchmark paths.
- Broad utility tests with filesystem/network/service assumptions.

Run ignored tests only when the user accepts prerequisites and the change directly affects that area. Make skips explicit in the handoff.

## External Service Skip Rules

Skip rather than failing hard when a test needs:

- Real API keys or non-placeholder user config.
- Network downloads, search APIs, browser automation, Android devices, or external services.
- Broad dependency installation such as `pip install -e .[test]`, Mermaid CLI, or Playwright browser downloads.
- Long LLM runs, project-generation workflows, or benchmark loops.
- Persistent vector stores outside a temporary test path.

Use `pytest.importorskip(...)`, environment-variable guards, or explicit user confirmation for these paths.

## Coverage Strategy

Start without broad coverage:

```bash
pytest <focused-file> -q
```

Then use module-specific coverage when useful:

```bash
pytest tests/metagpt/exp_pool/test_manager.py --cov=metagpt.exp_pool.manager --cov-report=term-missing -q
pytest tests/metagpt/memory/test_memory.py --cov=metagpt.memory.memory --cov-report=term-missing -q
```

Only run broad coverage/report commands after focused tests pass. The original coverage helper is reference-only because it uses parallel pytest, timeout, full reports, and opens HTML output.

## Public Symbol Helper Check

After adding or removing public classes/functions, run the bundled AST helper:

```bash
python sub-skills/maintainer-apis/scripts/list_public_symbols.py --module metagpt.configs --max-depth 2
python sub-skills/maintainer-apis/scripts/list_public_symbols.py --module metagpt.schema --json
```

Because the helper does not import target modules, differences usually indicate AST-level API changes rather than provider/config failures. Pair symbol output with focused tests before updating docs.
