# Repo Development Troubleshooting

Use this reference for source-checkout failures that are not normal PyPI runtime issues.

## Fast Triage

Run these first from the Pyserini checkout:

```bash
git status --short
git submodule status tools
python --version
java -version
python -m pip show pyserini
python -m pip check
```

Then choose targeted checks:

```bash
python -c "import pyserini; print('pyserini import ok')"
python -c "from pyserini.search.lucene import LuceneSearcher; print('Lucene import ok')"
python scripts/select_safe_tests.py --list-categories
```

## Missing `tools` Submodule

Symptoms:

- Paths under `tools/eval` or `tools/topics-and-qrels` are missing.
- Eval tests cannot find qrels such as `qrels.covid-round1.txt`.
- `trec_eval` or `ndeval` build commands fail because source directories do not exist.

Confirm:

```bash
git submodule status tools
ls tools/eval
```

Fix:

```bash
git submodule update --init --recursive tools
```

If the submodule is checked out at a different commit than the parent repository records, report that before comparing expected metrics.

## Eval Tool Build Failures

Symptoms:

- `python -m pyserini.eval.trec_eval` fails in a source checkout.
- `tests/base/test_eval.py` or `tests/base/test_trectools.py` fails before assertions.
- Native tool binaries under `tools/eval` are missing.

Fix:

```bash
(cd tools/eval && tar xvfz trec_eval.9.0.4.tar.gz && cd trec_eval.9.0.4 && make)
(cd tools/eval/ndeval && make)
```

If `make` or a compiler is missing, install build tools through the user's normal system or conda package manager before changing Pyserini code.

## Missing Anserini Fatjar

Symptoms:

- Lucene-backed imports fail with `No matching jar file found`.
- `from pyserini.search.lucene import LuceneSearcher` fails in editable mode.
- Source checkout imports work for pure Python modules but fail for Java-backed search/index/eval/server paths.

Confirm:

```bash
ls pyserini/resources/jars/anserini-*-fatjar.jar
python -c "from pyserini.search.lucene import LuceneSearcher; print('Lucene import ok')"
```

Fix choices:

1. Build a matching Anserini checkout and copy `target/anserini-*-fatjar.jar` into `pyserini/resources/jars/`.
2. Or set `ANSERINI_CLASSPATH` to a directory containing the fatjar before starting Python.
3. Restart the Python process if PyJNIus already started the JVM before the classpath was fixed.

Do not commit private fatjar paths or machine-specific environment settings.

## Java or JVM Mismatch

Symptoms:

- Java import/class errors after the fatjar exists.
- PyJNIus errors mention classpath, unsupported class version, or an already-running JVM.
- Commands behave differently across shells.

Checks:

```bash
java -version
echo "$JAVA_HOME"
python -c "import jnius_config; print('jnius_config ok')"
```

Recovery:

- Use JDK 21 for current Pyserini/Anserini.
- Set `JAVA_HOME` only to the user's actual JDK location and avoid writing it into reusable files.
- Start Pyserini Java-backed imports before other PyJNIus users in the same process.
- Restart the Python process after changing `JAVA_HOME`, `ANSERINI_CLASSPATH`, or fatjar files.

## Editable Install Points at the Wrong Package

Symptoms:

- Source edits do not affect imports.
- `python -m pip show pyserini` points to a different install than expected.
- Tests import an older PyPI package instead of the checkout.

Checks:

```bash
python -c "import pyserini; print(pyserini.__file__)"
python -m pip show pyserini
```

Fix:

```bash
python -m pip uninstall -y pyserini
python -m pip install -e .
python -c "import pyserini; print(pyserini.__file__)"
```

Ask before uninstalling if the user is reusing a shared environment.

## Broad Tests Download Data or Models

Symptoms:

- A focused test unexpectedly downloads CACM, prebuilt indexes, Hugging Face models, qrels, or remote run files.
- Tests hang on network access or fill cache directories.
- Dense/Faiss tests fail because optional packages or GPU resources are missing.

Avoid by default:

- Whole-directory discovery under `tests`, `integrations`, or `optional`.
- Prebuilt-index tests and index-download tests.
- Search, analysis, index-reader, encoder CLI, and dense model tests whose setup downloads resources.
- `tests/core/test_fusion.py` as a class, because class setup opens prebuilt sparse/dense/Faiss resources before individual simple tests run.
- Job manifests under `scripts/jobs*.txt` unless heavyweight validation is explicitly requested.

Use `scripts/select_safe_tests.py --list-excluded` to explain why candidates are skipped.

## Mutating Docs Checks

Symptoms:

- A test rewrites `docs/prebuilt-indexes.md`.
- A docs-only change produces a large generated diff.

Cause:

`tests/base/test_generate_prebuilt_index_docs.py` is a generator-style test. It writes generated documentation from prebuilt-index metadata.

Recovery:

- Run it only when updating prebuilt-index metadata or intentionally regenerating docs.
- Review the diff and discard unrelated generated changes.
- Do not run remote URL verification unless the user approved network checks.

## Server Development Resource Failures

Symptoms:

- REST/MCP tests fail importing Faiss or Java-backed searchers.
- Config-only changes fail because full server tests open prebuilt indexes.
- MCP tool tests fail with missing eval resources.

Recovery:

- Start with `tests/core/test_server_config.py` for YAML and alias rules.
- Use exact REST/OpenAPI methods that do not search when checking schema or docs changes.
- Install Faiss only for server paths that need Faiss-backed imports.
- Ensure eval jars/tools and the Anserini fatjar exist before MCP/eval-backed server checks.

## Safe Failure Report Template

When handing back a dev failure, include:

- Active Python version and whether the package is editable.
- Java major version and whether the JVM had already started.
- `tools` submodule state.
- Whether eval binaries and the Anserini fatjar are present.
- Exact focused test command run.
- Skipped heavyweight candidates with `skip-network`, `skip-model`, `skip-expensive`, `skip-resource`, or `skip-mutating` reason.
