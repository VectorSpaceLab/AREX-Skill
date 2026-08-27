# Indexing troubleshooting

Diagnose the earliest failing layer: filesystem/SQLite, YAML normalization,
model/vector construction, or index persistence. Keep the original
`articles.sqlite` until a replacement index has loaded successfully.

## Install and import failures

Use the same interpreter for installation and execution:

```bash
python --version                 # must satisfy Python >= 3.10
python -m pip install "paperai==2.6.0"
python -m pip check
python -c "import paperai, txtai, yaml, staticvectors; print('imports ok')"
```

`ModuleNotFoundError` usually means `pip` targeted another interpreter. Do not
solve a dense-model failure by claiming that this import probe passed. The
paperai package declares PyYAML, regex, rich, staticvectors[train], txtai[api],
and txtmarker among its runtime dependencies; install the matching extras in
the same environment.

## Missing database or schema

Typical symptoms include `unable to open database file`, `no such table:
sections`, `no such table: articles`, or `no such table: citations`.
Confirm the source artifact and schema without loading txtai:

```bash
python scripts/inspect_corpus.py ./corpus --maxsize 10 --toprank 0
python - <<'PY'
import sqlite3
with sqlite3.connect("./corpus/articles.sqlite") as db:
    for table in ("articles", "sections", "citations"):
        print(table, db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone())
PY
```

`articles` and `sections` are required for every index. `citations` is required
when `toprank > 0`; set `toprank=0` for a corpus that intentionally has no
citation table, or add the table as part of the upstream data preparation.
Check that `sections.article` values actually match `articles.id` and that
`articles.tags` is non-NULL for records intended for indexing. A valid but
empty result is often a tag mismatch, all-empty text, or a section filter
rather than a txtai failure.

## Invalid YAML or vector configuration

`Index.config` treats only a string ending in lowercase `.yml` as YAML. A
missing file raises `FileNotFoundError`; malformed YAML raises a YAML parser
error; a list or scalar may survive `safe_load` but fail when txtai expects a
mapping. Parse and shape-check first:

```bash
python scripts/inspect_corpus.py ./corpus --config ./index.yml
```

Start with a small mapping and add backend options one at a time:

```yaml
path: /absolute/or/local/model
content: true
gpu: false
```

For a staticvectors path, verify that it is a readable database produced by
staticvectors rather than relying on a `.magnitude` or other suffix. The
source's automatic word-vector mapping is:

```text
path=<vector-db>, scoring=bm25, pca=3, quantize=true
```

If a custom mapping contains `scoring`, `pca`, `quantize`, or `faiss`, remember
that paperai passes it through to the installed txtai version. An option valid
in another txtai release or backend can fail at construction or indexing.

## Model download, cache, and device failures

A model identifier may trigger a network download during `Embeddings` creation
or the first index pass. Before a long run:

- Prefer a complete local model directory or an already populated, writable
  model cache for offline/reproducible work.
- Check the path, permissions, available disk, and any authentication required
  by a private model outside the paperai process.
- Use `gpu: false` in YAML when a CPU run is intended. This is a txtai setting,
  not a guarantee that every model operation is CPU-compatible.
- If a model load reports CUDA/accelerator out-of-memory, lower model/batch
  resource requirements or run on a machine with adequate memory; do not treat
  `import paperai` or `Index.config` as evidence that the model/backend works.
- Keep model/cache diagnostics separate from corpus diagnostics. A valid
  `articles.sqlite` cannot repair an unavailable model.

A package probe used for this skill imported paperai 2.6.0 and reported clean
dependencies, but a dense model construction attempted CUDA and hit
out-of-memory. That is a concrete reminder to test the chosen model and device
in the target environment before full indexing.

## Memory, time, and long-running runs

Indexing is a streaming database read, but dense encoding, ANN construction,
scoring, PCA, quantization, and txtai persistence still consume memory and
scratch space. Weighted indexing intentionally reads the selected generator
twice. Static-vector training separately creates a full-corpus token file.
Use these controls:

```bash
# newest-entry subset, no citation table required
python -m paperai.index ./corpus ./index.yml 1000 0

# citation-ranked subset, requires citations.reference
python -m paperai.index ./corpus ./index.yml 0 100
```

Reduce the positive bounds, choose a smaller model/vector dimension, set
`gpu: false` when appropriate, and monitor disk as well as RAM. `maxsize` is
an article bound and section filtering can produce fewer or more rows than a
naive document estimate. There is no paperai wrapper option for txtai's
checkpoint parameter, so an interrupted `Index.run` should be treated as a
partial replacement: inspect artifacts, preserve the database, and rerun with
safe bounds rather than assuming resume support.

For a full-corpus failure, first reproduce on a tiny synthetic or bounded
corpus. If the bounded run works, increase one bound at a time. If it fails at
model construction, fix model/cache/device issues before changing SQLite. If
it fails during save, check free space and write permissions and remove only a
known-partial index artifact after preserving the source database.

## Partial or corrupt model directory

`Models.load` attempts a load when either `config` or `config.json` exists. A
stale config beside missing `embeddings`, `documents`, `scoring`, `lsa`, or
`ids` files can therefore fail after the initial directory check. Compare the
configuration with the files actually emitted by the selected txtai backend;
do not copy one artifact in isolation. Rebuild into a fresh directory when
possible, then copy/retain `articles.sqlite` with the newly saved artifacts.

If only `articles.sqlite` is present, it is a corpus, not a queryable index.
Use `inspect_corpus.py` for the corpus and `paperai.index` for construction.

## Export and vector-training surprises

- `Export.run(output, path)` takes output first. `python -m paperai.export`
  follows that order; reversing it can produce a confusing file/path error.
- Export is not the same selection as a weighted index: it does not require
  tags, does not honor `maxsize`/`toprank`, and applies its own section-name
  filter to every section.
- `Vectors.run` has no bounds. It tokenizes every section, creates temporary
  token text, and trains staticvectors. Use a prepared reduced database for a
  bounded experiment and ensure `output` is a writable model directory.
- If vector training fails before cleanup, look for temporary files in the
  interpreter's temporary directory and remove only files identified as the
  failed run after confirming no active training process remains.
