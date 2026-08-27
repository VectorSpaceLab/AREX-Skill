# Dataset preparation workflow

This workflow turns distant-supervision rows aligned from Wikidata relations and Chinese Wikipedia sentences into the JSON files consumed by the PCNN relation-extraction code. It is working-directory sensitive and combines long-running upstream alignment with local, deterministic preprocessing.

## Boundary and prerequisites

This sub-skill starts at relation-training rows and owns the `relationExtraction/data` preprocessing plus the `relationExtraction/algorithm` dataset layout. It does not own general Wikidata crawling, Wikidata relation CSV conversion, Neo4j graph import, or the Django/Mongo annotation UI.

Before using the original source scripts, confirm these artifacts exist in the checkout or have been intentionally substituted with tiny fixtures:

| Artifact | Used by | Notes |
| --- | --- | --- |
| `filter_train_data_all_deduplication.txt` | `dosomething.py filter_dataset` | Six-column training TSV after alignment, filtering, and deduplication. |
| `entities.txt` | `filter_dataset`, `entity2id` | Whitespace-separated `entity label_id`; entity labels `0` and `16` are filtered out by `filter_dataset`. |
| `country-code.json` | `filter_dataset` | JSON list with `cn` country names; rows where both entities are countries are filtered out. |
| `sgns.wiki.bigram-char` | `preprocessing.py word2vecjson` | Large Chinese word-vector text file; conversion loads and rewrites the whole file. |
| `NA_SAMPLE.txt` | `preprocessing.py na_datasetjson` | Optional NA relation rows; `dataset_split` assumes at least 2,500 NA examples unless constants are edited. |

## Upstream row generation summary

The original alignment workflow is long-running and service-heavy:

1. Prepare a Chinese Wikipedia extraction under the expected `wikiextractor/extracted` tree.
2. Import Wikidata relation CSVs into Neo4j so relation lookups are available.
3. Run the alignment code in the training-data directory to scan Wikipedia text, identify entity mentions, query relations, and emit rows with fields `entity1Pos`, `entity1`, `entity2Pos`, `entity2`, `statement`, `relation`.
4. Filter non-English or empty relation names from the raw aligned rows.
5. Deduplicate rows before copying them into the relation-extraction data directory.

For new work, prefer a small approved corpus or a previously generated row file. Do not start the full alignment scan without explicit approval; it can run for a very long time and depends on Neo4j data, THULAC resources, and local corpus layout.

## Safer deduplication

The original shell helper accepts one input file, sorts it, and appends results to a derived filename. Its `uniq -u` behavior drops every row that appears more than once instead of keeping one representative.

Use the bundled helper when you need a deterministic, explicit-output deduplication step:

```bash
sub-skills/relation-extraction-pipeline/scripts/deduplicate_training_rows.sh \
  --mode keep-first \
  filter_train_data_all.txt \
  filter_train_data_all_deduplication.txt
```

Available modes:

- `keep-first`: preserve input order and keep the first copy of each exact row.
- `sort-unique`: sort rows and keep one copy of each exact row.
- `drop-all-duplicates`: match the original `sort | uniq -u` style by removing all rows that have duplicates.

Use `--has-header` only when the input file really includes a header row. The downstream `preprocessing.py datasetjson` command does not skip headers, so remove or preserve headers deliberately.

## Local preprocessing command sequence

Run these commands from the relation data directory in a source checkout. The current working directory determines all input and output paths.

```bash
cd relationExtraction/data

# Optional: inspect relation counts in the deduplicated six-column TSV.
python dosomething.py sentence_relation_number

# Create filtered_data.txt from filter_train_data_all_deduplication.txt.
python dosomething.py filter_dataset

# Create entity2id.json from entities.txt.
python preprocessing.py entity2id

# Create rel2id.json. This command hard-codes the selected relation set plus NA.
python preprocessing.py rel2json

# Create dataset.json from filtered_data.txt and entity2id.json.
python preprocessing.py datasetjson

# Convert the large text vector file to word2vec.json.
python preprocessing.py word2vecjson

# Optional: create NA_dataset.json from NA_SAMPLE.txt.
python preprocessing.py na_datasetjson

# Split dataset.json plus NA_dataset.json into train_dataset.json/test_dataset.json.
python preprocessing.py dataset_split
```

Important command-name traps:

- The repository README shows command names like `rel2id` and `dataset.json`, but the Fire map in the script exposes `rel2json`, `datasetjson`, `word2vecjson`, `na_datasetjson`, `entity2id`, and `dataset_split`.
- `filter_dataset` is exposed by `dosomething.py`, not by `preprocessing.py`.
- `get_rel_json` does not read `staticResult.txt`; it writes a hard-coded relation set: `NA`, `instance of`, `has part`, `subclass of`, `parent taxon`, `material used`, `natural product of taxon`.

## Expected output placement

After preprocessing, copy or generate these files under the algorithm dataset directory named `agriculture`:

```text
relationExtraction/algorithm/data/agriculture/
├── entity2id.json
├── rel2id.json
├── test_dataset.json
├── train_dataset.json
└── word2vec.json
```

The PCNN data loader detects the dataset type from the parent directory name. Keep the directory basename `agriculture` unless you also edit the loader logic and configuration.

## Preflight validation

Before converting or training, validate tiny or newly produced files without TensorFlow:

```bash
python sub-skills/relation-extraction-pipeline/scripts/relation_dataset_schema_check.py \
  --training-tsv relationExtraction/data/filtered_data.txt \
  --rel2id relationExtraction/data/rel2id.json \
  --entity2id relationExtraction/data/entity2id.json \
  --dataset-json relationExtraction/data/dataset.json
```

For a built-in fixture sanity check:

```bash
python sub-skills/relation-extraction-pipeline/scripts/relation_dataset_schema_check.py --self-test
```

Use the schema checker before blaming TensorFlow; most later data-loader failures originate in row width, header leakage, missing entities, inconsistent relation ids, or bad character offsets.
