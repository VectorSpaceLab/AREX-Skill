---
name: repo-development
description: "Maintain a Pyserini source checkout, build developer resources,
  and choose focused tests without triggering heavyweight experiments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pyserini Repo Development

Use this sub-skill when the user is contributing to Pyserini from a source checkout, fixing tests, preparing an editable install, initializing submodules, building Anserini/evaluation resources, updating docs or prebuilt-index metadata, or deciding which tests are safe for a focused change.

Do not use this sub-skill for normal PyPI installation, user-facing indexing/search/fetch, dense encoding/Faiss workflows, run evaluation/fusion usage, REST/MCP deployment, or public API recipes. Route those tasks to `../install-and-runtime/SKILL.md`, `../index-search-fetch/SKILL.md`, `../dense-encoding/SKILL.md`, `../evaluation-and-fusion/SKILL.md`, or `../serving-and-agent-tools/SKILL.md`.

## Quick Development Flow

1. Confirm the checkout shape before installing:

   ```bash
   git status --short
   git submodule status tools
   python --version
   java -version
   ```

2. If `tools` is missing or uninitialized, initialize only the expected submodule:

   ```bash
   git submodule update --init --recursive tools
   ```

3. Install in editable mode inside a Python 3.12 environment with JDK 21 available:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -e .
   python -m pip check
   python -c "import pyserini; print('editable import ok')"
   ```

4. Build local developer resources only when the target tests need them:

   ```bash
   (cd tools/eval && tar xvfz trec_eval.9.0.4.tar.gz && cd trec_eval.9.0.4 && make)
   (cd tools/eval/ndeval && make)
   mkdir -p pyserini/resources/jars
   cp ../anserini/target/anserini-*-fatjar.jar pyserini/resources/jars/
   ```

   The fatjar copy assumes a sibling Anserini checkout that has already been built. If the user keeps the fatjar elsewhere, set `ANSERINI_CLASSPATH` for the current process before any PyJNIus/JVM import starts.

5. Select tests with the bundled helper before running native tests:

   ```bash
   python scripts/select_safe_tests.py --help
   python scripts/select_safe_tests.py --paths pyserini/server/config.py tests/core/test_server_config.py
   python scripts/select_safe_tests.py --category checkout --include-bounded
   ```

6. Run the smallest matching commands first. Do not run broad `tests`, `integrations`, `scripts/jobs*.txt`, prebuilt-index downloads, model encoders, or two-click reproduction matrices unless the user explicitly approves heavyweight/network work.

## Maintainer Decision Rules

- **Source checkout vs PyPI:** Use editable source installs only for maintainer work or unreleased code. If a user just needs retrieval, prefer the normal runtime install flow.
- **Submodule:** `tools/` is a Git submodule for evaluation tools and topics/qrels resources. Missing files under `tools/eval` or `tools/topics-and-qrels` usually mean the submodule was not initialized.
- **Fatjar:** Lucene-backed imports need an `anserini-*-fatjar.jar` in Pyserini package resources or on `ANSERINI_CLASSPATH` before the JVM starts.
- **Eval tools:** Native eval tests may need built `trec_eval` and `ndeval` binaries from the `tools` submodule; Python import success alone is not enough.
- **Docs/resources:** Updating generated docs or prebuilt-index metadata can intentionally rewrite files. Run those checks only when the task is about generated docs and review the resulting diff.
- **Jobs manifests:** Treat `scripts/jobs.docs-all.txt`, `scripts/jobs.integrations-all.txt`, and `scripts/jobs.regressions-all.txt` as maintainer manifests, not default validation commands.

## What to Read Next

- `references/development-workflows.md` for source checkout, editable install, submodule, eval-tool, fatjar, docs, and job-manifest workflows.
- `references/test-selection.md` for safe test categories, native candidate commands, and skip rules.
- `references/troubleshooting.md` for missing submodules, missing jars, Java/Python mismatches, eval-tool failures, and accidental network/download tests.
- `scripts/select_safe_tests.py --help` for a deterministic command selector that is safe by default.

## Handoff Checklist

- Confirm Python 3.12, JDK 21, editable install, and `pip check` before blaming Pyserini code.
- Check `tools` submodule state before running eval, qrels, or topic tests.
- Check the Anserini fatjar before running Lucene-backed imports or tests.
- Use exact test classes/methods instead of whole directories when the change touches one API surface.
- Record skipped heavyweight tests separately with the reason: network download, model download, optional GPU/Faiss dependency, broad integration, or mutating generated docs.
