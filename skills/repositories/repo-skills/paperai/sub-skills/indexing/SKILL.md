---
name: indexing
description: "Build, inspect, and export bounded paperai indexes from a
  paperetl-style SQLite corpus with txtai-compatible vector configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Indexing

Use this route when the task is to prepare or inspect the searchable model
behind `paperai`: validate a corpus, choose a txtai/vector configuration, build
an embeddings index, train optional static word vectors, or export raw section
text. Start with the no-download checker:

```bash
python scripts/inspect_corpus.py ./corpus --config ./index.yml --maxsize 1000 --toprank 0
```

The checker is bundled at [scripts/inspect_corpus.py](scripts/inspect_corpus.py). Run
that command from this sub-skill directory, or replace `scripts/` with the
path where this runtime skill is installed.

The `./corpus` argument is a user-owned directory containing the source
artifact `articles.sqlite`; `inspect_corpus.py` is only a bundled validation
helper and is not a replacement for `paperai.index`.

## Route the task

1. **Validate inputs first.** Read [data-formats.md](references/data-formats.md)
and run the checker before loading a model. It checks tables, required columns,
counts, bounds, and YAML shape without importing txtai or downloading a model.
2. **Choose configuration.** Use [api-reference.md](references/api-reference.md)
and [workflows.md](references/workflows.md) to distinguish a model reference,
a word-vector database, and a full YAML mapping. Start with a positive
`maxsize` or `toprank` for an exploratory run; `0` means unbounded in the
source implementation.
3. **Build and preserve the directory contract.** `paperai.index` reads
`<path>/articles.sqlite` and saves txtai artifacts back into the same directory.
Do not delete the database when replacing a failed index. Confirm the output
files before handing the directory to another route.
4. **Recover deliberately.** Use [troubleshooting.md](references/troubleshooting.md)
for missing schemas, malformed YAML, model cache/download failures, memory
pressure, and interrupted full-corpus runs. A Python import or a CPU SQLite
check does not prove that a configured model or accelerator can load.
5. **Hand off only after local checks.** Query execution belongs to the sibling
[querying route](../querying/SKILL.md); report task configuration and rendering
belong to [reporting](../reporting/SKILL.md). This route supplies their shared
corpus/model prerequisites, not their presentation behavior.

## Core commands

Install `paperai==2.6.0` in Python 3.10+ and verify imports before attempting a
model load:

```bash
python -m pip install "paperai==2.6.0"
python -c "import paperai, paperai.index, paperai.export; print(paperai.__file__)"
```

The source module accepts these positional forms:

```bash
python -m paperai.index CORPUS_DIR [VECTORS_OR_YML] [MAXSIZE] [TOPRANK]
python -m paperai.export OUTPUT.txt CORPUS_DIR
```

For exact signatures and output artifacts, use the linked references rather
than treating either positional interface as a safe full-corpus default.
