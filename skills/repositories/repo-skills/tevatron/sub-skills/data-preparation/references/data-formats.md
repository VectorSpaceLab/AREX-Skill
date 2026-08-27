# Tevatron Data Formats

Tevatron uses Hugging Face `datasets.load_dataset` for public datasets and local JSON/JSONL files. The relevant installed data arguments include `dataset_name='json'`, `dataset_split='train'`, `dataset_path=None`, `corpus_name=None`, `corpus_path=None`, `corpus_split='train'`, `train_group_size=8`, `query_max_len=32`, `passage_max_len=128`, `encode_is_query=False`, `encode_output_path=None`, and text/image/audio/video encoding enabled by default.

## Loader Modes

### Local JSONL

Use the generic Hugging Face JSON loader for local JSONL:

```bash
--dataset_name json --dataset_path train.jsonl --dataset_split train
```

For corpus-ID training rows, also provide a corpus loader:

```bash
--dataset_name json --dataset_path train.jsonl \
--corpus_name json --corpus_path corpus.jsonl --corpus_split train
```

Do not pass a local file path as `--dataset_name`; Tevatron forwards that value to `load_dataset`. Use `--dataset_path` for files and reserve `--dataset_name` for `json`, a dataset script/directory, or a hosted dataset name.

### Hugging Face Datasets

Use hosted datasets when Tevatron already publishes the desired schema:

```bash
--dataset_name Tevatron/msmarco-passage-aug --dataset_split train
--dataset_name Tevatron/msmarco-passage --dataset_split dev --encode_is_query
--dataset_name Tevatron/msmarco-passage-corpus --dataset_split train
--dataset_name Tevatron/bright --dataset_config biology --dataset_split test
--dataset_name Tevatron/bright-corpus --dataset_config biology --dataset_split train
```

Hosted datasets may download from the network unless cached. Do not combine a hosted dataset with `--dataset_path` unless intentionally overriding `data_files` for a compatible loader.

### Multiple Training Datasets

The multi-dataset loader treats YAML/list entries ending in `.jsonl` as local JSON files, directories as saved datasets, and other strings as dataset names. Each dataset entry must align with a corpus entry when using ID-list rows. Corpus entries can also carry an `assets_path` used for video/audio path resolution.

## Retriever Training Schemas

### New Corpus-ID Format

Use this shape when training rows should store document references instead of repeating full passage text.

Training JSONL row:

```json
{"query_id":"q1","query_text":"what is dense retrieval?","query_image":null,"positive_document_ids":["d1"],"negative_document_ids":["d2","d3"],"answer":null,"source":"custom"}
```

Required fields:

- `query_id`: stable query identifier.
- `positive_document_ids`: non-empty list of corpus `docid` strings.
- `negative_document_ids`: list of corpus `docid` strings, usually at least `train_group_size - 1` usable negatives per query.

Common optional fields:

- `query_text`: query text. Tevatron treats missing/null query text as an empty string, which is only sensible for multimodal query data.
- `query_image`, `query_audio`, `query_video`: optional query-side media fields.
- `answer` or `answers`: optional QA supervision metadata.
- `source`: optional dataset/source tag.

Corpus JSONL row:

```json
{"docid":"d1","title":"optional title","text":"document body","image":null,"audio":null,"video":null,"source":"custom"}
```

Required field:

- `docid`: stable document identifier matching train rows, rankings, qrels, and rerank inputs.

Common content fields:

- `text`: document body. Tevatron uses an empty string when missing/null; that is only appropriate when a supported media field carries the document content.
- `title`: optional title prepended to `text` for text encoding.
- `image`: optional image object/path depending on dataset backend.
- `audio`: optional object with an `array` key or a `.mp3` path.
- `video`: optional path, typically relative to `--assets_path`.
- `score`: optional teacher score used by distillation-style data.

The dataset loader builds a `docid` to corpus-row map and resolves every selected positive/negative ID through it. Missing corpus IDs fail later as lookup errors, so validate `--corpus` before training.

### Legacy Passage-List Format

Retriever training also supports older records with full positive and negative passage objects embedded in each row:

```json
{"query_id":"q1","query":"what is dense retrieval?","positive_passages":[{"docid":"d1","title":"Dense retrieval","text":"..."}],"negative_passages":[{"docid":"d2","title":"BM25","text":"..."}]}
```

Required fields:

- `query`: query text.
- `positive_passages`: non-empty list of passage objects.
- `negative_passages`: list of passage objects.

Passage object fields:

- `text`: required by Tevatron formatting.
- `title`: optional; when present, it is prepended to text.
- `docid`: strongly recommended for traceability and hard-negative filtering.
- `score`: optional for distillation datasets. Distillation expects scores on positives and negatives.

If `negative_passages` has fewer than `train_group_size - 1` rows, Tevatron samples with replacement. That can keep a run alive but usually means the prepared data is too shallow.

### Pre-Tokenized Format

Docs also describe pre-tokenized local rows. Use them only when the downstream training/encoding route is known to support already-tokenized values:

```json
{"query":[101,2029],"positives":[[101,3899]],"negatives":[[101,4997]]}
{"text_id":"d1","text":[101,6251,102]}
```

`TEXT_TYPE` can be a list of token IDs or, for some tokenizers, a string. Prefer normal text JSONL unless the user explicitly needs tokenizer-bypassing behavior.

## Retriever Encoding Schemas

### Query Encoding Rows

Use with `--encode_is_query`:

```json
{"query_id":"q1","query_text":"question text"}
```

Accepted text keys are `query_text` first, then legacy `query`. Optional keys are `query_image`, `query_audio`, and `query_video`.

### Corpus Encoding Rows

Use without `--encode_is_query`:

```json
{"docid":"d1","title":"optional title","text":"document body"}
```

Tevatron joins `title` and `text` with a space before applying `passage_prefix`. Optional `image`, `audio`, and `video` fields are retained only when the corresponding encode flag remains enabled. Audio string paths must end in `.mp3`; video/audio relative paths are resolved under `--assets_path` during loading.

## Reranker Data Schemas

### Reranker Training

Reranker training uses the legacy passage-list shape:

```json
{"query":"question text","positive_passages":[{"title":"t","text":"positive"}],"negative_passages":[{"title":"t","text":"negative"}]}
```

Each positive/negative passage should have `title` and `text`; the formatter normalizes dashes in titles and builds one text pair per query-passage candidate. Use `../reranking/` for model commands.

### Reranker Inference

Pairwise rerank input rows use one candidate per line:

```json
{"query_id":"q1","query":"question text","docid":"d1","title":"optional title","text":"candidate passage","score":12.3}
```

`score` can carry the upstream retrieval score for diagnostics. Reranker inference consumes `query_id`, `query`, `docid`, `title`, and `text`.

## Ranking and Qrels Files

Tevatron search-style rankings are whitespace-delimited and usually have three columns:

```text
q1 d1 42.0
q1 d2 17.5
q2 d3 9.0
```

Some bridge scripts or tools produce four-column ranking rows:

```text
q1 d1 1 42.0
```

TREC run rows have at least six columns:

```text
q1 Q0 d1 1 42.0 dense
```

TREC qrels for `trec_eval` have four whitespace-delimited columns:

```text
q1 0 d1 1
```

MS MARCO output uses three tab-delimited columns:

```text
q1	d1	1
```

The source Tevatron converters recompute rank when the query ID changes. The bundled converters preserve that behavior. Sort/group by query before conversion; interleaved query IDs cause rank to restart for repeated query blocks.

## Dataset-Transform Lessons

Tevatron's dataset transformation scripts are reference-only because they are dataset-specific and often download/upload data. Their schema lessons are useful:

- MS MARCO-style training transforms full `positive_passages`/`negative_passages` into `positive_document_ids` and `negative_document_ids`, renames `query` to `query_text`, adds `query_image`, `answer`, and `source`, and casts ID lists as string sequences.
- MS MARCO corpus transforms add optional `image` and `source` fields while keeping `docid`, `title`, and `text`.
- BRIGHT query transforms rename `id` to `query_id`, rename `query` to `query_text`, rename `gold_answer` to `answer`, and initialize empty positive/negative document ID lists for evaluation-only data.
- BRIGHT corpus transforms rename `id` to `docid` and `content` to `text`.
- ColPali-style multimodal transforms create query/corpus ID links, allow `text` to be null for image-only documents, and keep `image` fields in the corpus.

## Quick Validation Examples

From this sub-skill directory:

```bash
python scripts/validate_tevatron_jsonl.py --kind train --input train.jsonl --corpus corpus.jsonl --train-group-size 8
python scripts/validate_tevatron_jsonl.py --kind corpus --input corpus.jsonl --assets-root assets
python scripts/validate_tevatron_jsonl.py --kind query --input queries.jsonl --assets-root assets
python scripts/validate_tevatron_jsonl.py --kind ranking --input rank.tsv --corpus corpus.jsonl
python scripts/validate_tevatron_jsonl.py --kind qrels --input qrels.txt --corpus corpus.jsonl
```
