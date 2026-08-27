# Indexing API reference

The signatures below are from paperai 2.6.0. The package imports `regex`,
PyYAML, txtai, and staticvectors as appropriate. These methods perform real
I/O; use a synthetic or bounded corpus before a full run.

## `paperai.index.Index`

```python
Index.config(vectors)
Index.stream(dbfile, maxsize, toprank, scoring)
Index.embeddings(dbfile, vectors, maxsize, toprank)
Index.run(path, vectors, maxsize=0, toprank=0)
```

- `config(vectors)` returns the exact dictionary passed to
  `txtai.embeddings.Embeddings`, or `None`.
  - A `dict` is returned unchanged.
  - A string ending in lowercase `.yml` is read with `yaml.safe_load` and its
    result is returned. A missing file or malformed YAML raises before model
    construction. `.yaml` is not treated as a YAML file by this implementation;
    pass a mapping from Python or rename the file to `.yml`.
  - A path recognized by txtai/staticvectors as a word-vector database becomes
    `{"path": path, "scoring": "bm25", "pca": 3, "quantize": True}`.
    Recognition is database-based, not a filename-suffix promise.
  - Any other truthy string becomes `{"path": vectors}`. `None` or an empty
    string becomes `None` and asks txtai for its default behavior.
- `stream` is a generator over `(section_id, text, None)` rows. It always
  requires tagged articles (`articles.tags IS NOT NULL`). A positive `maxsize`
  selects the newest articles by `articles.entry`; it is not a section count.
  A positive `toprank` selects the most-cited article references from
  `citations.reference`. When both are positive, the filters intersect.
  Non-positive values are treated as unbounded by the source.
- `embeddings` constructs `Embeddings(Index.config(vectors))`. If
  `embeddings.isweighted()` is true, it makes one scoring pass and one index
  pass over the generator. Weighted mode tokenizes text and skips section names
  matching the implementation's section filter
  (`background|(?<!.*?results.*?)discussion|introduction|reference`); unweighted
  mode retains all non-empty section text.
- `run` derives `path/articles.sqlite`, builds the index, then calls
  `embeddings.save(path)`. It does not create a separate output directory or
  expose txtai's checkpoint argument. Existing txtai artifacts at `path` may be
overwritten by the new index.

## `paperai.models.Models`

```python
embeddings, db = Models.load(path)
Models.close(db)
```

`load` derives `path/articles.sqlite`, creates an SQLite connection, and loads
an embeddings object only when `path/config` or `path/config.json` exists. A
successful model directory therefore keeps `articles.sqlite` alongside the
configuration and index files. A present config file with missing sibling
artifacts can still fail later during `Embeddings.load`; inspect the whole
directory rather than deleting individual files.

## `paperai.export.Export`

```python
Export.stream(dbfile, output)
Export.run(output, path)
```

`run` derives `path/articles.sqlite`. `stream` selects `Id, Name, Text` from
`sections`, excludes section names matching the same section filter used by
export, skips empty text, and writes each remaining text followed by `\n`.
It does not apply the tagged-article, `maxsize`, or `toprank` filters used by
indexing. The output file is opened with mode `w`, so choose a new path or back
up an existing export.

## `paperai.vectors`

```python
RowIterator(dbfile)
Vectors.tokens(dbfile)
Vectors.run(path, size, mincount, output)
```

`RowIterator` reopens `articles.sqlite` on each iteration and yields token lists
from every `sections.Text` row with non-empty tokenization; it has no article
or section-name filter. `Vectors.tokens` writes those tokens to a temporary
text file and returns its path. `Vectors.run` trains a `StaticVectorsTrainer`
with the requested `size` and `mincount`, writes the model to `output`, and
removes the temporary token file only after training returns. The module CLI
uses size `300` and mincount `4`; use the Python API when those values must
change.

## Live capability boundary

A Python 3.11 package probe imported paperai 2.6.0, txtai 9.12.0,
staticvectors 0.2.0, txtmarker 1.1.0, and PyYAML 6.0.3, with no broken
requirements reported. That proves package import and SQLite/YAML plumbing
only. Constructing a configured dense model is a separate capability check: a
model load in that probe attempted accelerator use and failed with CUDA
out-of-memory. For a real dense run, verify the selected model path/cache and
device explicitly; do not infer model or backend support from the import probe.
