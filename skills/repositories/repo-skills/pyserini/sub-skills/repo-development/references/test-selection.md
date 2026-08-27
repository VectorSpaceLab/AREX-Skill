# Test Selection

Pyserini's test tree mixes safe unit tests with Java-backed fixture tests, source-resource tests, prebuilt-index downloads, model downloads, server integration tests, and broad benchmark suites. Select tests by change surface and resource requirement instead of running whole directories.

## Default Algorithm

1. List changed paths and classify them by workflow surface.
2. Run the selector without gated candidates:

   ```bash
   python scripts/select_safe_tests.py --paths pyserini/server/config.py tests/core/test_server_config.py
   ```

3. Add `--include-bounded` only when local prerequisites are available and the user accepts Java/eval/server fixture tests.
4. Add `--include-mutating` only for tasks that intentionally regenerate docs or metadata.
5. Add `--include-network` only after explicit approval for downloads, prebuilt indexes, models, or broad integrations.

The selector prints commands but never runs them.

## Safe-by-Default Candidates

| Change surface | Candidate commands | Notes |
| --- | --- | --- |
| General checkout/import | `python -m pip check`; `python -c "import pyserini; print('pyserini import ok')"`; `python -m unittest tests.base.test_jvm.TestJvmStartup` | Mocked JVM tests check classpath selection without requiring a real fatjar. |
| Server config or YAML schema | `python -m unittest tests.core.test_server_config` | Parses temp configs and validates alias rules without starting REST/MCP services. |
| REST document formatting | `python -m unittest tests.base.test_document_format` | Pure Python formatter tests; useful for REST response shape changes. |
| Eval/fusion fixture utilities | `python -m unittest tests.base.test_trectools.TestTrecTools.test_trec_run_read`; selected pure `TrecRun` methods | Avoid class-level tests that invoke `trec_eval` until eval tools are ready. |
| Selector sanity | `python scripts/select_safe_tests.py --list-categories`; `python scripts/select_safe_tests.py --format json` | Confirms the bundled selector works without importing Pyserini. |

## Bounded Candidates Requiring Local Resources

Use these only with `--include-bounded` or after manually checking prerequisites.

| Resource | Candidate commands | Prerequisites |
| --- | --- | --- |
| Anserini fatjar and Java | `python -m unittest tests.base.test_jvm.TestJvmStartupIntegration`; `python -m unittest tests.base.test_index_otf.TestIndexOTF` | JDK 21, PyJNIus, and an `anserini-*-fatjar.jar` in resources or `ANSERINI_CLASSPATH`. |
| Eval tools and qrels | `python -m unittest tests.base.test_eval`; `python -m unittest tests.base.test_trectools` | Initialized `tools` submodule, built `trec_eval`, and local qrels/resources. |
| Server stack | exact non-search REST/OpenAPI methods, or `python -m unittest tests.core.test_server_config` first | Full REST/MCP classes can open prebuilt indexes; start with config-only tests. |
| Lucene API changes | `tests/base/test_index_otf.py` before download-heavy search/index-reader tests | Uses local fixture docs but still needs Java and the fatjar. |

## Candidates to Skip by Default

Skip these unless the user explicitly asks for heavyweight validation:

- `python -m unittest discover -s tests`: the tree includes network, model, and prebuilt-index cases.
- `integrations/core` and `integrations/optional`: maintained integration suites, not quick checks.
- `scripts/jobs.docs-all.txt`: runs many `bin/run-*.sh` dense/model jobs.
- `scripts/jobs.integrations-all.txt`: broad integration discovery across core suites.
- `scripts/jobs.regressions-all.txt`: two-click reproduction modules across many collections.
- `tests/base/test_search.py`, `tests/base/test_analysis.py`, `tests/base/test_index_reader.py`, and `tests/base/encoder/test_encode_cli.py`: setup downloads CACM indexes or model-related artifacts.
- `tests/base/test_prebuilt_index.py` and `tests/base/test_index_download.py`: intentionally exercise prebuilt-index download and URL behavior.
- `tests/core/test_fusion.py` as a whole: even simple fixture methods share class setup that opens prebuilt sparse/dense/Faiss indexes and encoder resources.
- Dense encoder model tests under `tests/base/encoder/test_encoder_model_*` and optional multimodal tests: can require Hugging Face/OpenAI assets, optional extras, GPU, or cached models.

## Common Change-to-Test Mapping

| Changed area | First candidates | Escalation |
| --- | --- | --- |
| `pyproject.toml`, install docs, runtime imports | pip/import checks, mocked JVM tests | Runtime checker from `../../install-and-runtime/SKILL.md`, then Lucene import with fatjar. |
| `.gitmodules`, `tools`, eval packaging | submodule status, eval-tool build commands | `tests/base/test_eval`, `tests/base/test_trectools`. |
| `pyserini/server/config.py` | `tests/core/test_server_config` | Exact REST auth/config methods, then MCP only if dependencies/resources are ready. |
| `pyserini/server/document_format.py` | `tests/base/test_document_format` | Selected REST document endpoint tests only if index resources are available. |
| `pyserini/search/lucene`, `pyserini/index/lucene`, `pyserini/analysis` | mocked JVM tests, then `tests/base/test_index_otf` | Search/index-reader tests only after approving CACM/prebuilt downloads. |
| `pyserini/eval`, `pyserini/trectools` | pure `TrecRun` tests | Full eval tests after `tools` and eval binaries are ready. |
| `pyserini/fusion` | fixture-level command recreated outside `TestFusion` or sibling validator | Avoid `TestFusion` class setup unless prebuilt/dense resources are approved. |
| `pyserini/encode`, `pyserini/search/faiss`, dense models | selector warning plus dense workflow planning | Add Faiss/model/GPU-specific checks from the dense sub-skill. |
| `docs/prebuilt-indexes.md` or prebuilt metadata | static diff review | Generated docs test with `--include-mutating`, remote URL checks only with network approval. |

## Reporting Skips

When skipping a candidate, record the concrete reason:

- `skip-network`: would download indexes, qrels, runs, or remote docs.
- `skip-model`: would download or initialize encoder/model assets.
- `skip-expensive`: broad integration, benchmark, or reproduction matrix.
- `skip-resource`: missing local `tools`, eval binaries, fatjar, Java, Faiss, or optional extras.
- `skip-mutating`: test rewrites generated docs or metadata.

A good handoff says which focused tests passed, which candidates were intentionally skipped, and what resource would be needed to run each skipped candidate.
