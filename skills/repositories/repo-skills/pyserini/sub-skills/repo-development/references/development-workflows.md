# Development Workflows

This reference distills Pyserini maintainer setup from the source checkout evidence. Use it for contribution tasks, source-only failures, docs/resource updates, and native validation planning.

## Source Checkout Baseline

Pyserini development expects:

- Python 3.12 for the project runtime.
- JDK 21 for Anserini/Lucene access through PyJNIus.
- Maven when building Anserini outside the Pyserini checkout.
- A Git submodule at `tools/` for evaluation tools, topics, qrels, and shared resources.
- An editable install with `python -m pip install -e .`.
- An Anserini fatjar available to Pyserini before Lucene-backed imports start.

Start with checks that do not mutate the checkout:

```bash
git status --short
git submodule status tools
python --version
java -version
python -m pip --version
```

If the environment is not Python 3.12 or Java is not JDK 21, fix that before interpreting Pyserini test failures.

## Initialize the `tools` Submodule

A clone without submodules can import Pyserini but fail eval and qrels/topic tests. The checkout should include the `tools` submodule from the Anserini tools repository.

```bash
git submodule update --init --recursive tools
git submodule status tools
```

Treat a leading `-` in `git submodule status tools` as uninitialized. Treat a leading `+` as checked out at a different commit than the parent repository records; that may be intentional during maintenance, but report it before comparing results.

## Editable Install

Install the source checkout after the interpreter and Java are selected:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip check
python -c "import pyserini; print('pyserini import ok')"
```

Use `python -m pip`, not bare `pip`, so the editable install targets the active interpreter. If imports resolve to a different installation, inspect `python -c "import pyserini; print(pyserini.__file__)"` in the user's active environment and reinstall into the intended environment.

## Build Evaluation Tools

The `tools` submodule contains source archives and directories for native evaluation tools. Build them only when tests or workflows need native eval binaries:

```bash
(cd tools/eval && tar xvfz trec_eval.9.0.4.tar.gz && cd trec_eval.9.0.4 && make)
(cd tools/eval/ndeval && make)
```

After building, eval-focused tests can use qrels under `tools/topics-and-qrels` and fixture runs under `tests/resources`. If compilation fails, check for a C compiler and `make` before changing Pyserini code.

## Provide the Anserini Fatjar

Lucene-backed Pyserini imports configure a classpath from either `ANSERINI_CLASSPATH` or `pyserini/resources/jars/anserini-*-fatjar.jar`. A source checkout may not include that jar.

Recommended maintainer flow:

```bash
# In a matching Anserini checkout, build the fatjar with Maven using that project's build instructions.
# Then, from the Pyserini checkout:
mkdir -p pyserini/resources/jars
cp ../anserini/target/anserini-*-fatjar.jar pyserini/resources/jars/
python -c "from pyserini.search.lucene import LuceneSearcher; print('Lucene import ok')"
```

Alternative for one shell session:

```bash
export ANSERINI_CLASSPATH=/path/to/directory-containing-anserini-fatjar
python -c "from pyserini.search.lucene import LuceneSearcher; print('Lucene import ok')"
```

Set `ANSERINI_CLASSPATH` before any PyJNIus or Java-backed Pyserini import starts. If the JVM already started with the wrong classpath, restart the Python process.

## Focused Native Tests

Use `scripts/select_safe_tests.py` to map a change to a small candidate set. Typical escalation:

1. Pure Python or mocked tests that cannot download data.
2. Bounded Java/fatjar tests that use local fixtures or skip when resources are missing.
3. Eval-tool tests after `tools` is initialized and eval binaries are built.
4. Server tests that validate config or OpenAPI behavior without opening prebuilt indexes.
5. Broad integrations or job manifests only after explicit approval.

Avoid `python -m unittest discover -s tests` as the first command. The full tree contains tests that download CACM indexes, prebuilt indexes, qrels, model assets, or remote run files.

## Docs and Metadata Updates

Docs-only edits usually need static review plus the narrow tests for any code snippets or config schemas they touch. Generated docs and prebuilt-index metadata are different:

- `tests/base/test_generate_prebuilt_index_docs.py` rewrites `docs/prebuilt-indexes.md` intentionally.
- Prebuilt-index metadata changes can imply remote URL checks or cache behavior; do not run link/download verification by default.
- For docs that add retrieval commands, route command correctness through the sibling workflow skill that owns the API surface.

After a generated docs update, review the diff and avoid committing unrelated regenerated sections.

## Job Manifests and Integration Suites

The repository contains maintainer manifests for broad validation:

- `scripts/jobs.docs-all.txt` launches many dense/model documentation jobs through `bin/run-*.sh` and writes logs.
- `scripts/jobs.integrations-all.txt` runs `unittest discover` across `integrations/core/*` suites.
- `scripts/jobs.regressions-all.txt` runs two-click reproduction modules across many collections.

Use these manifests as inventory and CI planning aids. They are not safe default commands because they can download indexes, models, corpora, qrels, and run large experiments. Prefer dry-run or display-only modes when a reproduction module supports them, and ask before running network-heavy jobs.

## Source-Resource Change Checklist

When changing code under source modules, update or verify the corresponding resources:

- `pyserini/search`, `pyserini/index`, or `pyserini/analysis`: check Lucene fatjar availability and choose bounded Lucene tests.
- `pyserini/eval`, `pyserini/fusion`, or `pyserini/trectools`: check `tools` submodule and eval binaries; use fixture run files.
- `pyserini/server`: run server config tests before REST/MCP tests that open indexes.
- `pyserini/encode` or dense search modules: assume model/Faiss downloads are possible and route to dense-specific validation planning.
- `docs/` and prebuilt-index metadata: decide whether generated docs should be rewritten, and review diffs carefully.
