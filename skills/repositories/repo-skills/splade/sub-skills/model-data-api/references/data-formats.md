# SPLADE Data Formats

SPLADE uses a few simple file layouts repeatedly. Most API-level failures are id mismatches or files being passed at the wrong directory/file level.

## Collection and Query `raw.tsv`

Classic collection/query datasets expect a directory containing `raw.tsv`:

```text
<id>\t<text>
```

Examples:

```text
0\tThe Manhattan Project and its atomic bomb helped bring an end to World War II.
1048642\ttreating tension headaches without medication
```

Rules:

- The first tab separates the id from the text. Extra tabs after the first are joined back into the text by the classic loader.
- Empty or one-character lines are ignored by SPLADE loaders.
- `CollectionDatasetPreLoad(data_dir, id_style="row_id")` takes a directory path and opens `data_dir/raw.tsv`.
- `splade.hf.datasets.DatasetPreLoad(data_dir, id_style=...)` takes the raw TSV file path directly.
- ids used with `content_id` must match qrel/run/score file ids after string normalization.

## Triplet `raw.tsv`

Classic pair training fixtures expect a directory containing `raw.tsv` with exactly three tab-separated fields:

```text
<query_text>\t<positive_doc_text>\t<negative_doc_text>
```

Distillation pair fixtures add teacher scores:

```text
<query_text>\t<positive_doc_text>\t<negative_doc_text>\t<positive_score>\t<negative_score>
```

HF `TRIPLET_Dataset` expects a raw TSV file path, not a directory, and returns `([query, positive, negative], scores)`.

## Qrel JSON

SPLADE qrels are JSON dictionaries mapping query ids to document ids to relevance values:

```json
{
  "1048642": {
    "45": 1,
    "69": 1
  }
}
```

Rules:

- Treat qid and did as strings in portable tooling, even if files contain numeric-looking ids.
- Positive relevance values are normally integers `>= 1`.
- `L2I_Dataset` filters qrels to positives by keeping relevance values whose integer value is at least 1.
- Missing qid/did keys usually surface later as `KeyError` from content-id collection lookup.

## Score JSON

L2I and reranking score JSON files use this shape:

```json
{
  "1048642": {
    "45": 12.7,
    "69": 10.2,
    "123": -1.4
  }
}
```

Rules:

- Keys are query ids, nested keys are document ids, values are numeric scores.
- SPLADE sorts candidate documents by score when constructing examples.
- Positives may appear in the score dictionary. If a positive score is missing, the HF dataset falls back to the maximum candidate score for the positive.
- The score dictionary must contain enough non-positive candidates for the configured number of negatives. When too few are available, the loader samples with replacement.

## Hard-Negative `pkl.gz`

Some hard-negative score files are gzip-compressed pickles containing a nested dictionary:

```python
{
    qid: {did: score, did: score, ...},
    ...
}
```

Observed variants include integer ids and string ids. SPLADE normalizes many HF training paths to strings, but `MsMarcoHardNegatives` removes positive ids using `int(positive)` and then looks up documents by mixed string/int forms. Portable validators should accept both numeric-looking string ids and integer ids, but should warn when a qrel id has no matching score or collection id after string normalization.

## TREC Run Format

Reranking and training-data readers accept TREC-style whitespace-separated run lines:

```text
<qid> Q0 <did> <rank> <score> <tag>
```

Rules:

- SPLADE readers split on a single space and expect six fields.
- `rank` must parse as an integer when top-k filtering is used.
- `score` must parse as a float.
- Keep ids consistent with content-id query and document collections.

## Row Id vs Content Id

SPLADE exposes two id styles for preloaded collection/query datasets:

| `id_style` | Key used internally | Returned id | Common use |
| --- | --- | --- | --- |
| `row_id` | Integer row offset `0..N-1` | Original first-column id from `raw.tsv` | Indexing with sequential row ids while preserving source ids in `doc_ids.pkl`. |
| `content_id` | The first-column id from `raw.tsv` as a string | The requested content id as a string | Query/doc lookup from qrels, score dictionaries, and reranking run files. |

Debugging rule: if a qrel/run/score id is used to fetch text, the dataset must be loaded as `content_id` and the id must exist in that raw TSV. If a collection is loaded as `row_id`, callers should index by integer rows, not arbitrary qrel document ids.

## Inverted Index Artifacts

`SparseIndexing` and `IndexDictOfArray` produce these artifacts when an `index_dir` is configured:

| File | Producer | Contents |
| --- | --- | --- |
| `array_index.h5py` | `IndexDictOfArray.save()` | HDF5 datasets `dim`, `index_doc_id_<token_dim>`, and `index_doc_value_<token_dim>`. |
| `doc_ids.pkl` | `SparseIndexing.index()` | Ordered mapping from internal row ids to original document ids. |
| `index_dist.json` | `IndexDictOfArray.save()` | Posting-list lengths by token dimension. |
| `index_stats.json` | `SparseIndexing.index(compute_stats=True)` | Average document sparsity/statistics. |

`SparseRetrieval` writes `run.json` as `{qid: {doc_id: score}}`.

## Anserini Export Shapes

`EncodeAnserini` can produce:

- Document JSONL, one object per line: `{"id": <id>, "content": <original text>, "vector": {"token": integer_weight}}`.
- Query TSV: `<id>\t<expanded token repeated by integer weight>`.

Anserini export and pruning workflows belong to `pruning-export-evaluation`; this sub-skill only explains the shape.

## Minimal Validation Checklist

- Every collection/query directory contains readable `raw.tsv` with at least two tab-separated columns per non-empty line.
- Triplet files contain exactly three tab-separated fields per non-empty line.
- Distillation pair files contain exactly five fields and numeric score columns.
- Qrels parse as JSON object of objects, with numeric relevance values.
- Score JSON parses as JSON object of objects, with numeric scores.
- Pickle-gzip scores load to a dictionary of dictionaries with numeric values.
- Every qrel qid exists in the query ids when using `content_id`.
- Every positive qrel did exists in the document ids when using `content_id`.
- Score ids overlap expected qrels and collections after string normalization.
