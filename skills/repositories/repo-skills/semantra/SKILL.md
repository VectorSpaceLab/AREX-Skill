---
name: semantra
description: "Guides Semantra semantic-search CLI, local document indexing,
  embedding model selection, and interactive web search workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Semantra Repo Skill

Use this skill when a task involves the `semantra` Python package: installing or
inspecting the CLI, semantically searching local text/PDF documents, selecting
embedding models, understanding cache artifacts, or operating Semantra's local
browser UI.

## First checks

Run these safe checks in the Semantra environment before constructing an
expensive command:

```sh
semantra --help
semantra --version
semantra --list-models
```

If the CLI is not visible or imports fail, run the bundled diagnostic helper:

```sh
python scripts/inspect_semantra_install.py
```

Read [repo-provenance.md](references/repo-provenance.md) when deciding whether
this skill is aligned with a current Semantra checkout or should be refreshed.

## Install guidance

For normal use, install the public package in an isolated Python environment:

```sh
python -m pip install semantra
```

For a source checkout, install the package from the checkout after reviewing its
current metadata:

```sh
python -m pip install -e .
```

Semantra 0.1.12 imports `pkg_resources`; if the CLI fails because that module is
missing, see [troubleshooting.md](references/troubleshooting.md) before changing
other dependencies.

## Route map

| Task | Read |
| --- | --- |
| Process local `.txt` or `.pdf` files, use `--no-server`, choose `--windows`, inspect cache artifacts, or troubleshoot PDF/text preprocessing. | [document-indexing](sub-skills/document-indexing/SKILL.md) |
| Choose `mpnet`, `minilm`, `sgpt`, `sgpt-1.3B`, `openai`, or a custom Hugging Face model; diagnose OpenAI, CUDA, model downloads, pool sizes, or SVM dependency issues. | [models-and-embeddings](sub-skills/models-and-embeddings/SKILL.md) |
| Use the local web UI, query with `+`/`-`, apply result tags, interpret scores, call local JSON routes, handle port conflicts, or debug PDF/text navigation in the browser. | [interactive-search](sub-skills/interactive-search/SKILL.md) |
| Need a grouped CLI option reference or server route overview before choosing a sub-skill. | [cli-and-server-reference.md](references/cli-and-server-reference.md) |
| Need cross-cutting install/import/dependency/cache/server triage. | [troubleshooting.md](references/troubleshooting.md) |

## Common workflows

### Preprocess documents without starting the UI

```sh
semantra --no-server --semantra-dir ./semantra-cache --model minilm documents/*.txt
```

Read [document-indexing workflows](sub-skills/document-indexing/references/workflows.md)
for cache validation and `--force` handling. The first local transformer run may
download model files; choose the model with
[models-and-embeddings](sub-skills/models-and-embeddings/SKILL.md) first.

### Index and search interactively

```sh
semantra --semantra-dir ./semantra-cache report.pdf notes/*.txt
```

Open the printed localhost URL. Use
[interactive-search](sub-skills/interactive-search/SKILL.md) for query
arithmetic, result tags, server routes, and UI troubleshooting.

### Choose an embedding backend

Default local search uses `mpnet`. Use `minilm` for faster small tests, SGPT
presets for asymmetric semantic-search experiments, a custom
`--transformer-model` for language/domain needs, or `--model openai` only after
privacy, API-key, network, SDK, and cost checks.

## Safety and privacy notes

- Local transformer modes keep document text on the user's machine, but may
  download model files.
- OpenAI mode sends document windows and queries to OpenAI and can incur cost.
- The local Flask server serves document content to clients that can reach it;
  use `--host 0.0.0.0` only after an explicit privacy review.
- Do not delete a user's Semantra cache directory before inspecting which
  document/config group is stale or corrupt.

## Known Semantra 0.1.12 edges

- `pkg_resources` import may require a Setuptools version that still provides
  it, or a Semantra code update.
- `--model openai` uses the legacy OpenAI embedding API and may need
  `openai<1` or package updates with current SDKs.
- `--svm` requires `scikit-learn`, which is not declared in the base package
  dependencies, and is incompatible with asymmetric SGPT presets.

## Runtime boundaries

This generated skill is self-contained. Use its bundled references and scripts
instead of reopening the original repository docs, examples, tests, or source
files during a Researcher task.
