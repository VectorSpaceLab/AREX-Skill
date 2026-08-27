# Testing Guide

## Test environment and collection contract

The active root pytest configuration collects `tests/test_*.py`, classes named
`Test*`, and functions named `test_*`. It enables strict markers, a 300-second
timeout, verbose output, short tracebacks, and these markers:

- `slow`: long-running or model/data-heavy;
- `openai`: requires an OpenAI API key;
- `integration`: requires a live service such as Ollama or LM Studio.

Install tools without assuming every project optional dependency is present:

```bash
uv sync --group test
```

For metadata-only checks, a tool-only environment is enough:

```bash
uv sync --only-group test
uv run --only-group test pytest tests/test_cpu_only_install.py -q
```

For core/backend/app tests, install the affected local packages and their
required dependencies first. A test collection failure is not proof that the
changed code failed; determine whether the missing import is an owned dependency,
an optional app/backend dependency, or environment skew.

Do not rely on these weak checks alone:

- `tests/test_basic.py::test_imports` has no import assertions;
- the package-import body in `tests/test_ci_minimal.py` is a placeholder;
- version assertions ending in `or True` do not enforce a version contract.

Prefer `tests/test_readme_examples.py::test_readme_imports`, direct backend
imports, the bundled version checker, and behavior tests with assertions.

## Selection matrix

| Change | Minimum focused checks | Add when applicable | Skip/record explicitly |
|---|---|---|---|
| Package metadata, CPU constraints, internal dependency pins | `pytest tests/test_cpu_only_install.py -q`; bundled version checker | clean resolver or wheel-install smoke | native/app suites if code is untouched |
| Public exports or core API | `pytest tests/test_readme_examples.py::test_readme_imports -q` plus the specific API test module | one prepared backend build/search case | unprepared DiskANN/CUDA/MPS |
| Array build path | `pytest tests/test_build_from_arrays.py -q` | HNSW/IVF case selected by changed backend | model-download tests not needed by change |
| Metadata filtering | `pytest tests/test_metadata_filtering.py -q` | CLI metadata-filter parser case | live provider tests |
| Passage IDs/rebuild persistence | `pytest tests/test_passage_id_scheme.py tests/test_rebuild_cli.py -q` | incremental backend regression | unrelated apps |
| CLI parser/commands | the owning `tests/test_cli_*.py` file | `tests/test_readme_examples.py::test_readme_imports`; CLI help smoke | model/service integration unless command launches it |
| Sync/watch/change detection | `pytest tests/test_sync.py tests/test_watch_sync_scope.py -q` | lightweight cases in `test_incremental_build.py`; HNSW fallback regression | model-loading incremental tests unless intentionally provisioned |
| HNSW Python/rebuild logic | `pytest tests/test_hnsw_rebuild_fallback.py -q`; direct HNSW import | deterministic HNSW build/search case; embedding-server manager tests when server code changed | DiskANN/IVF/GPU suites |
| HNSW CMake/binding/native code | core public import; direct HNSW import/registry; deterministic HNSW build/search | build and install one wheel for the changed host/Python ABI; inspect repaired wheel in release work | other platform ABIs are CI/manual matrix evidence, not locally proven |
| IVF backend/incremental logic | direct IVF import/registry; relevant lightweight sync/CLI tests | selected IVF incremental test in an environment that already has model/cache and `faiss-cpu` | HNSW/DiskANN/GPU |
| DiskANN native/backend code | direct DiskANN import/registry after a successful native build | selected `test_diskann_partition.py` case with sufficient memory/time | never substitute HNSW success |
| FlashLib/FlashLib IVF | import/registry under compatible CUDA torch/FlashLib | `pytest tests/test_flashlib_ivf_backend.py -q` on an authorized CUDA host | CPU result cannot validate this backend |
| Embedding batch/token/prompt behavior | `test_embedding_batch_size.py`, `test_embedding_prompt_template.py`, `test_token_truncation.py`, or `test_prompt_template_persistence.py` | integration-marked service tests only when service is running | credentialed/live tests by default |
| Chat provider | owning provider test module with its non-live mocked tests | live class only with explicit credentials and network authorization | other providers |
| RAG app or data source | owning app test, help/parser, or standalone reader test | integration case if external SDK/service/data is available | all unrelated apps and downloads |
| MCP/OpenClaw protocol | standalone protocol/schema tests | subprocess/E2E only when CLI, model, Docker/service prerequisites are prepared | slow/integration cases by default |

## Commands for safe focused evidence

### Package metadata and public import

```bash
uv run pytest tests/test_cpu_only_install.py \
  tests/test_readme_examples.py::test_readme_imports -q
```

The first test reads package TOML metadata. The second imports the public
builders/search/chat types. Neither validates a native search.

### Core parser and state logic

```bash
uv run pytest \
  tests/test_cli_ask.py \
  tests/test_metadata_filtering.py \
  tests/test_sync.py \
  tests/test_watch_sync_scope.py -q
```

Narrow this list to the changed module; do not run all four mechanically.

### HNSW deterministic native smoke

```bash
uv run pytest \
  'tests/test_readme_examples.py::test_readme_basic_example[hnsw]' -q
```

This test monkeypatches deterministic embeddings, avoids a model download, and
performs real HNSW build/search when HNSW is installed. It is a stronger native
smoke than registry membership alone. It may be skipped on some CI/macOS paths;
report a skip as a skip, not a pass.

### HNSW rebuild behavior without a native build

```bash
uv run pytest tests/test_hnsw_rebuild_fallback.py -q
```

This uses fakes to assert that a modified file causing HNSW full-rebuild fallback
reloads the complete corpus. It proves core/CLI orchestration, not the C++
binding.

### IVF incremental behavior

The IVF incremental tests are deliberately skipped when `CI=true` because they
load an embedding model and create enough vectors to train IVF. Run only in a
prepared, bounded environment:

```bash
uv run pytest \
  tests/test_incremental_build.py::test_ivf_multiple_incremental_no_duplicates -q
```

Record model/cache, `faiss-cpu`, corpus size, and runtime. Do not remove the skip
condition or force a download merely to make a local gate green.

### Broader non-live run

After focused tests pass and dependencies are complete:

```bash
uv run pytest tests/ -m "not slow and not openai and not integration" --tb=short
```

This filter still does not guarantee zero model downloads because some
repository tests use environment-based skips rather than markers. Review
collection and test bodies for the selected environment before broad execution.

## Difficult case: core API plus HNSW binding changes

Use this minimum escalation, stopping on failure:

1. `python scripts/check_package_versions.py --repo-root <checkout>` from this
   sub-skill's resolved directory. Version skew is a packaging gate independent
   of behavior tests.
2. `pytest tests/test_cpu_only_install.py
   tests/test_readme_examples.py::test_readme_imports -q` for metadata/public
   imports.
3. Direct import and registry probe:

   ```bash
   python - <<'PY'
   import leann_backend_hnsw
   from leann.api import get_registered_backends
   assert "hnsw" in get_registered_backends()
   print("HNSW import and registration passed")
   PY
   ```

4. `pytest tests/test_hnsw_rebuild_fallback.py -q` if API/update orchestration
   changed.
5. `pytest 'tests/test_readme_examples.py::test_readme_basic_example[hnsw]' -q`
   for an actual deterministic native build/search.
6. Build/install one clean HNSW wheel only when CMake, binding, packaging, or ABI
   files changed. Test the wheel in a fresh environment rather than the editable
   build.

DiskANN, IVF, FlashLib, FlashLib IVF, MPS/MLX, credentialed providers, and live
service suites remain skipped unless their code or a shared contract changed.
Explain each skip by scope or unavailable backend; do not say “all backends
passed.”

## Reading outcomes

- **pass:** assertions ran and passed;
- **skip:** prerequisite or repository condition prevented execution; inspect the
  reason and carry optional/required status forward;
- **collection error:** environment/import issue before test execution;
- **timeout/segfault:** native/service/resource failure, not an ordinary assertion;
- **xfail:** expected failure only when declared by the test; do not translate a
  plain failure into an expected one.

Capture exact node IDs, interpreter, installed distribution versions, backend,
and host architecture for any native failure. Avoid global environment workarounds
that make one suite pass while changing CPU/CUDA or editable/wheel identity.
