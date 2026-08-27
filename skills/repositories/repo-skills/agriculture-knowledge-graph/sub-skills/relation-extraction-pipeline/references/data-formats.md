# Relation extraction data formats

The relation-extraction pipeline uses two layers of data: six-column sentence rows and JSON files consumed by the PCNN data loader. Validate formats before launching expensive conversion or training.

## Six-column training TSV

Used as `filter_train_data_all_deduplication.txt` and `filtered_data.txt`.

| Column | Type | Meaning | Required checks |
| --- | --- | --- | --- |
| `entity1Pos` | integer string | Character offset of entity 1 in `statement`. | Non-negative; should point to the first character of `entity1`. |
| `entity1` | string | Head entity mention. | Non-empty; should appear at `entity1Pos`. |
| `entity2Pos` | integer string | Character offset of entity 2 in `statement`. | Non-negative; should point to the first character of `entity2`. |
| `entity2` | string | Tail entity mention. | Non-empty; should appear at `entity2Pos`. |
| `statement` | string | Chinese sentence containing both entity mentions. | Non-empty; must not contain raw tabs or accidental embedded newlines. One pair of outer quotes is common in older rows. |
| `relation` | string | Relation label. | For PCNN training, should be `NA` or one of the labels in `rel2id.json`. |

Example tiny row:

```text
0	小麦	3	植物	小麦是植物。	instance of
```

Format traps:

- Some upstream scripts write a header row. Remove it before `preprocessing.py datasetjson`; that function attempts to parse every line as data.
- The source alignment code may wrap statements in double quotes. This is acceptable if offsets still refer to the unwrapped sentence text.
- Tabs inside a sentence break the six-column split and will become a `ValueError` during JSON conversion.
- Entity positions are character offsets, not token offsets. The data loader later uses these positions to find segmented entity tokens and raises a position error when they do not align.

## `entities.txt`

Whitespace-separated entity-to-label rows:

```text
小麦 6
水稻 6
氮肥 7
```

`filter_dataset` removes rows where either entity has label `0` or `16`; `entity2id` assigns ids from the first whitespace-delimited token on each line. Avoid spaces inside entity names unless the script is adapted.

## `country-code.json`

`filter_dataset` expects a JSON list of objects with a `cn` field:

```json
[
  {"cn": "中国"},
  {"cn": "法国"}
]
```

Rows where both entities are in this country list are skipped.

## `rel2id.json`

Object mapping relation labels to non-negative integer ids:

```json
{
  "NA": 0,
  "instance of": 1,
  "has part": 2,
  "subclass of": 3,
  "parent taxon": 4,
  "material used": 5,
  "natural product of taxon": 6
}
```

The PCNN code treats relation id `0` as the NA class in evaluation loops and class weighting. Keep `NA: 0` unless you audit the model and metrics code.

## `entity2id.json`

Object mapping entity text to integer ids:

```json
{
  "小麦": 0,
  "植物": 1
}
```

`dataset.json` stores these ids as strings in the `head.id` and `tail.id` fields. The loader sorts by those string ids when building bag scopes.

## `dataset.json`, `train_dataset.json`, and `test_dataset.json`

List of relation instances:

```json
[
  {
    "head": {"pos": "0", "word": "小麦", "id": "0"},
    "relation": "instance of",
    "sentence": "小麦是植物。",
    "tail": {"pos": "3", "word": "植物", "id": "1"}
  }
]
```

Required fields:

- Top level: `head`, `tail`, `relation`, `sentence`.
- `head` and `tail`: `pos`, `word`, `id`.
- `pos` should be an integer-like character offset.
- `relation` should exist in `rel2id.json`; unknown labels are mapped to `NA` by the loader, which can hide data-preparation mistakes.
- `sentence` is tokenized by Jieba for the agriculture dataset after whitespace is replaced with underscores.

`train_dataset.json` and `test_dataset.json` have the same schema. The original split function concatenates positive examples with hard-coded counts of NA examples: 2,000 for train and 500 for test.

## `NA_dataset.json`

Same object schema as `dataset.json`, with `relation` normally set to `NA`. If fewer than 2,500 NA examples are available, edit the split constants or create a smaller custom split script; otherwise the source split loop will run past the available data.

## `word2vec.json`

List of word-vector objects generated from a text embedding file:

```json
[
  {"word": "小麦", "vec": ["0.1", "0.2", "0.3"]},
  {"word": "植物", "vec": ["0.0", "0.4", "0.5"]}
]
```

The source converter writes vectors as strings. The loader later assigns them into a float NumPy matrix. Every `vec` must have the same length and contain numeric values.

Large-vector cautions:

- Full Chinese word-vector files can be huge. Conversion reads the source text, creates a large JSON list, then the loader reads the JSON and writes `_processed_data/*_mat.npy`.
- For smoke tests, use a tiny word-vector fixture with only the tokens needed by the tiny dataset.
- If the vector dimension or `max_length` changes, delete stale `_processed_data` before rerunning the loader.

## Algorithm processed cache

When the loader first reads `train_dataset.json` or `test_dataset.json`, it creates an `_processed_data` directory in the current training working directory. It contains NumPy arrays for words, positions, masks, lengths, relation labels, scopes, the word-vector matrix, and `word2id`.

Delete `_processed_data` when any of these change:

- `train_dataset.json` or `test_dataset.json` contents.
- `word2vec.json` contents or vector dimensions.
- `rel2id.json` labels or ids.
- `config.model.max_length`.
- Dataset directory basename, especially if moving files out of `data/agriculture`.

## Validator usage

Use the bundled checker for deterministic schema validation without TensorFlow:

```bash
python sub-skills/relation-extraction-pipeline/scripts/relation_dataset_schema_check.py \
  --training-tsv relationExtraction/data/filtered_data.txt \
  --rel2id relationExtraction/data/rel2id.json \
  --entity2id relationExtraction/data/entity2id.json \
  --dataset-json relationExtraction/data/dataset.json \
  --word2vec-json relationExtraction/data/word2vec.json
```

Relax position checks only when auditing legacy rows that are known to need cleanup:

```bash
python sub-skills/relation-extraction-pipeline/scripts/relation_dataset_schema_check.py \
  --training-tsv legacy_rows.tsv \
  --allow-position-mismatch
```

Do not treat a relaxed pass as training-ready; it only helps triage malformed legacy files.
