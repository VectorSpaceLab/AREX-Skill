# DeepKE data-preparation workflows

This reference explains which data-preparation path to choose before DeepKE supervised NER, RE, or AE work. Use the bundled scripts from this sub-skill directory; they are standalone adapters and do not require a DeepKE source checkout.

## Choose the smallest adequate workflow

### 1. Manual annotation first

Choose this when labels need human judgment, relation direction is ambiguous, offsets must be gold quality, or dictionary/triple coverage is poor.

For NER, create a sequence-labeling project with span labels such as `PER`, `LOC`, `ORG`, or the project-specific entity types. Export JSON/JSONL records with raw `text` and `entities` that contain character offsets. Convert to DeepKE BIO text with:

```bash
python scripts/convert_supervised_data.py json2txt annotated.jsonl train.txt --input-format doccano --json-lines
```

For RE, annotate entity spans and directed relations. DeepKE standard RE examples are easiest to train after each row has one candidate pair: `sentence`, `head`, `tail`, offsets, and `relation`. If the annotation export contains many spans or many relations per sentence, flatten it into one row per candidate pair before training.

### 2. Convert already labeled supervised data

Choose this when the labels already exist and only the container format needs changing.

- NER JSON or DOCX to DeepKE BIO text:

```bash
python scripts/convert_supervised_data.py json2txt ner.json train.txt
python scripts/convert_supervised_data.py docx2txt ner.docx train.txt
```

- RE or AE JSON/XLSX to CSV:

```bash
python scripts/convert_supervised_data.py json2csv examples.json train.csv
python scripts/convert_supervised_data.py xlsx2csv examples.xlsx train.csv
```

Use this path for high-precision data. It does not infer labels; it only normalizes known labels into formats DeepKE loaders commonly consume.

### 3. NER weak supervision from a dictionary

Choose this when you have unlabeled text plus a reliable entity surface-form dictionary, and you accept noisy BIO labels that should usually be reviewed before final training.

Dictionary CSV rows must contain entity text and label. Header names `entity,label` are accepted, as are two-column headerless CSV files.

```bash
python scripts/prepare_weaksupervised_data.py \
  --language cn \
  --source-dir source_texts \
  --dict-file vocab_dict.csv \
  --output-dir prepared_ner \
  --output-prefix deepke_weak
```

The generated helper uses deterministic longest-match dictionary labeling. This is safer for a standalone skill than relying on a local tokenizer state, but it means dictionary normalization, casing, punctuation, and overlapping mentions must be checked explicitly.

### 4. RE distant supervision from triples

Choose this when candidate `(sentence, head, tail)` rows already exist and a triple table can assign a relation label by exact entity-pair match.

```bash
python scripts/ds_label_data.py \
  --language en \
  --source-file source_pairs.json \
  --triple-file triples.csv \
  --output-dir prepared_re \
  --output-prefix deepke_ds_labeled
```

The labeler preserves existing fields, writes a `relation` key, and assigns `None` when no triple matches. Relation direction matters by default: `(head=A, tail=B)` does not match `(head=B, tail=A)` unless you choose bidirectional matching.

### 5. Validation-only pass

Choose this when files already appear DeepKE-ready but training fails immediately, labels are missing, or split files are empty.

Practical checks:

1. Count rows or sentence blocks in each split.
2. Verify that all labels appear in the target config or label vocabulary.
3. Spot-check entity offsets by slicing the raw sentence.
4. Check that RE rows have exactly one candidate pair unless the downstream loader explicitly supports many pairs.
5. Confirm that CSV headers match the field names used by the intended DeepKE example.

## Split expectations

DeepKE examples commonly expect separate train/dev/test files. A default `0.8/0.1/0.1` split is convenient for moderate datasets, but it can create tiny or empty dev/test files on very small corpora. For quick smoke tests, use explicit rates such as `--train-rate 0.34 --dev-rate 0.33 --test-rate 0.33` on at least three examples, or merge very small validation/test splits only for smoke checks.

## Quality expectations

- Weak NER labels are high recall only when dictionary coverage is good and aliases are listed.
- Distant RE labels are only as accurate as the triple table and candidate-pair extraction.
- Manual annotation exports still need offset and label validation before training.
- A successful converter run proves syntax and schema, not model-ready label quality.
