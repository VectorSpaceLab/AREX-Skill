# Indexing workflows

These recipes separate no-download validation from model construction. Replace
all example directories with user-owned paths. The file `articles.sqlite` is a
source artifact; `inspect_corpus.py` is the bundled helper.

## 1. Install and probe without loading a model

```bash
python -m pip install "paperai==2.6.0"
python -m pip check
python - <<'PY'
import paperai
from paperai.index import Index
from paperai.export import Export
from paperai.models import Models
from paperai.vectors import Vectors
print(paperai.__file__)
print(Index.config(None))
print(Export.run, Models.load, Vectors.run)
PY
```

This confirms package imports and API names only. It does not prove that a
remote/local dense model can load or that a GPU backend is usable.

## 2. Validate a corpus and YAML before model construction

```bash
python scripts/inspect_corpus.py ./corpus --config ./index.yml --maxsize 1000 --toprank 0
```

The helper checks `./corpus/articles.sqlite`, required columns, row counts, and
whether the bounded candidate query can execute. It parses YAML with
`yaml.safe_load` but never constructs `txtai.Embeddings`, resolves a model ID,
or accesses a model cache. Add `--json` for machine-readable output. A
nonzero exit means fix the corpus/config before spending model time.

For a word-vector reference whose model should not be touched by the checker,
pass it as a string:

```bash
python scripts/inspect_corpus.py ./corpus --vectors ./vectors --maxsize 1000
```

The helper reports the reference and whether that local path exists; it does
not infer txtai's database status from its filename and does not download it.

## 3. Build a bounded dense index

Create a `.yml` file only when a mapping is needed. For example:

```yaml
path: sentence-transformers/all-MiniLM-L6-v2
content: true
gpu: false
```

Then run a deliberately bounded build:

```bash
python -m paperai.index ./corpus ./index.yml 1000 0
```

`1000` is a bound on newest `articles.entry` rows before section filtering,
not a guarantee of 1000 indexed sections. `0` leaves citation ranking
unbounded. To use the top citation references instead:

```bash
python -m paperai.index ./corpus ./index.yml 0 100
```

If both values are positive, only the intersection is indexed. The module
writes txtai index files into `./corpus` and can replace an existing index;
copy or snapshot the directory first if the old index matters.

A direct model/vector reference is also accepted:

```bash
python -m paperai.index ./corpus sentence-transformers/all-MiniLM-L6-v2 1000 0
```

Use the YAML form when setting `gpu: false`, `content`, `scoring`, FAISS, or
other txtai options. A model identifier may require network access and cache
space on its first load.

## 4. Build a weighted word-vector index

Train or obtain a staticvectors database first, then use either the direct
path or an explicit mapping:

```python
from paperai.index import Index

Index.run(
    "./corpus",
    {
        "path": "./vectors",
        "scoring": "bm25",
        "pca": 3,
        "quantize": True,
    },
    maxsize=1000,
    toprank=0,
)
```

The API call is intentionally explicit. When `./vectors` is recognized as a
staticvectors database, `Index.config("./vectors")` supplies the same BM25,
PCA, and quantization defaults. Weighted indexing makes two passes over the
selected section generator: one for scoring and one for vector indexing.

## 5. Train static vectors (full-corpus operation)

The source API is:

```python
from paperai.vectors import Vectors
Vectors.run("./corpus", size=300, mincount=4, output="./vectors")
```

The source module entry point is only a convenience wrapper and uses
`size=300`, `mincount=4`:

```bash
python -m paperai.vectors ./corpus ./vectors
```

It streams all `sections.Text` values through tokenization, creates a
full-corpus temporary token file, trains staticvectors, and removes the
temporary file after successful training. It does not use `maxsize` or
`toprank`; make a separate reduced SQLite corpus if a bounded training run is
needed. Ensure the output directory is writable and has enough space for the
vector model. A successful run should leave a non-empty model artifact such
as `model.safetensors` under the requested output directory.

## 6. Export raw searchable text

```bash
python -m paperai.export ./corpus/sections.txt ./corpus
```

The call maps to `Export.run(output, path)`, so output comes first. It opens or
overwrites `sections.txt`, reads `./corpus/articles.sqlite`, filters section
names using the export filter, and writes each non-empty section text followed
by a newline. It does not require an embeddings model and does not use the
indexing bounds or tagged-article restriction. If a destination parent does
not exist, create it first.

The Python form is useful when the SQLite filename is elsewhere:

```python
from paperai.export import Export
Export.stream("./corpus/articles.sqlite", "./exports/sections.txt")
```

## 7. Verify the handoff directory

Use the no-download checker again after a build:

```bash
python scripts/inspect_corpus.py ./corpus
find ./corpus -maxdepth 2 -type f -printf '%P\n' | sort
```

For a local/cached model, test the actual load separately:

```python
from paperai.models import Models
embeddings, db = Models.load("./corpus")
try:
    print("loaded", embeddings is not None)
finally:
    Models.close(db)
```

Do not run this load check against an index whose configuration names an
uncached remote model unless downloading is intended. Once the directory is
usable, route searches to [querying](../../querying/SKILL.md) and report work
to [reporting](../../reporting/SKILL.md); do not add formatting or query
presentation logic here.
