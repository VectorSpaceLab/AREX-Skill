# Corpus, configuration, and artifact formats

## Input directory

`paperai.index` and `paperai.export` take a directory, not the SQLite filename.
The source artifact must be exactly:

```text
CORPUS_DIR/
└── articles.sqlite
```

The database is the paperetl-style article store. Indexing directly uses these
columns (SQLite identifiers are case-insensitive):

| Table | Required columns | Why |
|---|---|---|
| `articles` | `id`, `tags`, `entry` | select tagged articles and apply the newest-article bound |
| `sections` | `id`, `article`, `name`, `text` | produce embedding documents and map section IDs to articles |
| `citations` | `reference` | required only when `toprank > 0`; rank article references by citation count |

A realistic store normally has additional article metadata such as `Title`,
`Published`, `Publication`, and `Reference`; those are consumed by query/report
routes, not by the index SQL itself. `sections.article` must point at the
corresponding `articles.id`, and `sections.id` becomes the document ID stored by
txtai. `articles.tags` must be non-NULL for an article to contribute to
`Index.stream`, even if its sections are otherwise valid. A `NULL` tag excludes
the whole article.

The following is a minimal indexing fixture shape, not a replacement for a
paperetl export:

```sql
CREATE TABLE articles (id INTEGER PRIMARY KEY, tags TEXT, entry TEXT);
CREATE TABLE sections (id INTEGER PRIMARY KEY, article INTEGER, name TEXT, text TEXT);
CREATE TABLE citations (reference INTEGER);
```

Use the bundled `inspect_corpus.py` before indexing. It reports missing tables
or columns and does not download or instantiate a model.

## Section selection

The implementation queries `SELECT Id, Name, Text FROM sections` and restricts
rows to tagged articles. With `maxsize > 0`, it additionally restricts article
IDs to `SELECT id FROM articles ORDER BY entry DESC LIMIT maxsize`. With
`toprank > 0`, it restricts article IDs to the top grouped values of
`citations.reference` ordered by `count(*) DESC`. Both constraints are
intersections. `maxsize=0` and `toprank=0` are the documented unbounded values;
negative values also bypass the source's `> 0` checks, but are poor operational
inputs and should be normalized to zero.

When txtai reports a weighted index, `Index.stream` tokenizes section text and
skips lower-cased section names matching the source regex
`background|(?<!.*?results.*?)discussion|introduction|reference`. In practical
terms this excludes background, introduction, reference, and discussion names
unless the preceding text contains `results` in the regex's permitted context.
It also drops rows whose tokenization is empty. For an unweighted/dense index, it
does not apply that section-name filter and drops only empty text. This is why a
weighted build and a raw export do not have identical row counts.

## Vector configuration forms

The second `paperai.index` argument is one of these source-supported forms:

1. **No value**: `None`; txtai's default configuration is used.
2. **Model reference**: a local model directory or a resolvable model identifier,
   for example `sentence-transformers/all-MiniLM-L6-v2`. The source wraps it as
   `{"path": value}`. First use may download model files; use a local,
   pre-populated cache for an offline run.
3. **YAML mapping in a `.yml` file**: every key is passed through to the
   installed txtai `Embeddings` constructor. A minimal dense example is:

   ```yaml
   path: sentence-transformers/all-MiniLM-L6-v2
   content: true
   gpu: false
   ```

   `gpu: false` is an explicit CPU preference for txtai vector backends that
   honor it. It does not make an unavailable model, unsupported operator, or
   missing dependency work.
4. **Static word-vector database**: a path recognized by
   `txtai.vectors.WordVectors.isdatabase`. `Index.config` adds weighted BM25,
   three-component PCA, and quantization:

   ```yaml
   path: /data/vectors
   scoring: bm25
   pca: 3
   quantize: true
   ```

   Passing the vector database path directly applies the same default mapping.

A weighted/custom txtai mapping can add options such as:

```yaml
path: /data/vectors
scoring: bm25
pca: 3
faiss:
  nprobe: 6
  components: IVF100,Flat
```

The mapping is not schema-validated by paperai; txtai validates or rejects
backend-specific keys when the `Embeddings` object is constructed/indexed.
Malformed YAML, a YAML list/scalar where a mapping is expected, an unknown
backend, or an inaccessible local vector path must be fixed before a build.
The source recognizes lowercase `.yml` specifically; a `.yaml` filename is
treated as a model/vector path by `Index.config`.

## Index output directory

After `Index.run(CORPUS_DIR, ...)`, keep the source database and all txtai
artifacts together:

```text
CORPUS_DIR/
├── articles.sqlite              # source artifact; keep it
├── config or config.json        # txtai configuration; required by Models.load
├── embeddings                    # dense ANN data when a dense index exists
├── documents                     # stored text when content is enabled
├── scoring                       # sparse/weighted data when enabled
├── lsa                           # word-vector PCA data when enabled
└── ids                           # IDs when content is disabled
```

The exact optional files depend on txtai configuration and backend. `config`
or `config.json` plus the artifacts referenced by that config are the important
load contract. Do not call a directory a usable index merely because the
SQLite file exists, and do not copy only `embeddings` without its configuration
and companion files.

## Raw section export

`python -m paperai.export OUTPUT.txt CORPUS_DIR` writes non-empty section text
selected by the export filter. It does not require an article tag, so its
output can include sections from articles that `Index.stream` excludes. The
source artifact is `articles.sqlite`; the bundled helper name is
`inspect_corpus.py`, and neither should be confused with an output file. Export
is a plain text stream, not an embeddings index, and embedded newlines in a
section remain embedded newlines.

## Training corpus for static vectors

`paperai.vectors` reads every `sections.Text` row, tokenizes it, and writes a
temporary token corpus before calling `StaticVectorsTrainer`. It does not honor
`maxsize`, `toprank`, tags, or the indexing section filter. `size` controls vector
dimensions and `mincount` controls the minimum token frequency. The module
CLI defaults to `size=300` and `mincount=4`; a successful run should leave a
non-empty model artifact such as `model.safetensors` under the requested output
directory. Training is a full-corpus, memory/time-sensitive operation; use a
separately prepared subset if a bounded experiment is required.
