# Dataset Formats for Flair Training

This reference maps common local training data layouts to public pip-installed Flair corpus readers. CPU and local-file inspection are the verified baseline. Prepared dataset constructors may download public data when cache entries are missing, so keep cache and download approval explicit.

## Corpus object basics

The installed API includes these core signatures:

```python
Corpus(train=None, dev=None, test=None, name="corpus", sample_missing_splits=True, random_seed=None)
Corpus.downsample(percentage=0.1, downsample_train=True, downsample_dev=True, downsample_test=True, random_seed=None)
Corpus.make_label_dictionary(label_type, min_count=1, add_unk=True, add_dev_test=False)
MultiCorpus(corpora, task_ids=None, name="multicorpus", **corpusargs)
```

Operational rules:

- A `Corpus` has `train`, `dev`, and `test` splits; not every reader requires all three files.
- Use `sample_missing_splits=False` when benchmark reporting must not silently derive dev/test splits from train.
- Use `sample_missing_splits=True` for small experiments where missing dev/test splits may be sampled automatically.
- Some installed corpus paths accept string modes such as `"only_dev"`; verify behavior before relying on them.
- Use a fixed `random_seed` for reproducible sampling and `downsample(...)` smoke runs.
- Call `make_label_dictionary(...)` for the exact target layer. Common values include `"ner"`, `"upos"`, `"pos"`, `"class"`, `"topic"`, `"sentiment"`, `"relation"`, and `"nel"`.
- Use `add_dev_test=True` only when the evaluation contract permits labels from dev/test to enter the dictionary.

## ColumnCorpus: local sequence labeling

Use `ColumnCorpus` for CoNLL-like sequence labeling: one token per non-empty line, annotation columns beside it, and blank lines between sentences.

Example file:

```text
George NNP B-PER
Washington NNP I-PER
visited VBD O
Seattle NNP B-LOC

Ada NNP B-PER
Lovelace NNP I-PER
wrote VBD O
notes NNS O
```

Reader pattern:

```python
from flair.datasets import ColumnCorpus

columns = {0: "text", 1: "pos", 2: "ner"}
corpus = ColumnCorpus(
    data_folder="data/ner",
    column_format=columns,
    train_file="train.txt",
    dev_file="dev.txt",
    test_file="test.txt",
    autofind_splits=False,
    sample_missing_splits=False,
)
label_dictionary = corpus.make_label_dictionary(label_type="ner", add_unk=False)
```

Useful options supported by the underlying installed reader include:

- `column_delimiter`: default is whitespace regex; use `"\t"` for tab-separated corpora.
- `comment_symbol`: comment prefix. `ColumnCorpus` defaults to `"# "`; `MultiFileColumnCorpus` defaults to `None`.
- `skip_first_line=True`: skip a header row.
- `document_separator_token`: preserve document boundaries for contextual embeddings.
- `every_sentence_is_independent=True`: disable cross-sentence context.
- `documents_as_sentences=True`: aggregate document sections as sentence objects when paired with a separator.
- `banned_sentences=[...]`: drop unwanted markers such as `-DOCSTART-`.
- `space-after` column: preserve original whitespace for offset-sensitive tasks.
- `use_tokenizer=...`: retokenize after reading. This can alter span alignment, so inspect examples after using it.
- `in_memory=False`: lower memory by storing raw lines instead of all parsed `Sentence` objects.

## MultiFileColumnCorpus: many local sequence files

Use `MultiFileColumnCorpus` when a logical split is spread across several files or domains. Import it from `flair.datasets.sequence_labeling` for maximum compatibility.

```python
from flair.datasets.sequence_labeling import MultiFileColumnCorpus

corpus = MultiFileColumnCorpus(
    column_format={0: "text", 1: "ner"},
    train_files=["data/ner/train_a.txt", "data/ner/train_b.txt"],
    dev_files=["data/ner/dev.txt"],
    test_files=["data/ner/test_news.txt", "data/ner/test_forum.txt"],
    column_delimiter="\t",
    sample_missing_splits=False,
)
```

`MultiFileColumnCorpus` concatenates datasets inside each split. If separate per-domain metrics matter, train on the merged corpus and run explicit post-training evaluation per held-out file.

## JSONL sequence labeling

Use JSONL readers for character-span annotations. Each line is a JSON object with a text field and a list of `[start_char, end_char, label]` spans. Offsets use Python slice semantics: start inclusive, end exclusive.

```json
{"data":"George Washington visited Seattle.","label":[[0,17,"PER"],[26,33,"LOC"]],"metadata":[["doc_id","demo-1"]]}
```

Reader pattern with the required import caveat:

```python
try:
    from flair.datasets import JsonlCorpus, MultiFileJsonlCorpus
except ImportError:
    from flair.datasets.sequence_labeling import JsonlCorpus, MultiFileJsonlCorpus

corpus = JsonlCorpus(
    data_folder="data/jsonl_ner",
    train_file="train.jsonl",
    dev_file="dev.jsonl",
    test_file="test.jsonl",
    text_column_name="data",
    label_column_name="label",
    metadata_column_name="metadata",
    label_type="ner",
    autofind_splits=False,
    sample_missing_splits=False,
)
```

Use `MultiFileJsonlCorpus` for sharded splits:

```python
corpus = MultiFileJsonlCorpus(
    train_files=["data/jsonl/train_a.jsonl", "data/jsonl/train_b.jsonl"],
    dev_files=["data/jsonl/dev.jsonl"],
    test_files=["data/jsonl/test.jsonl"],
    label_type="ner",
    sample_missing_splits=False,
)
```

Caveats:

- Flair tokenizes the text and aligns char spans to resulting tokens. Badly aligned spans can fail or produce unexpected boundaries.
- Leading/trailing whitespace in spans may be trimmed, but do not rely on trimming as data cleaning.
- Use the same tokenizer choice for training and later inference when span offsets matter.

## ClassificationCorpus: FastText-style text classification

Use `ClassificationCorpus` for one document per line with FastText-style labels at the beginning.

```text
__label__sports Local team wins final match
__label__finance __label__markets Stocks close higher
```

Reader pattern:

```python
from flair.datasets import ClassificationCorpus

corpus = ClassificationCorpus(
    data_folder="data/topics",
    label_type="topic",
    train_file="train.txt",
    dev_file="dev.txt",
    test_file="test.txt",
    memory_mode="partial",
    sample_missing_splits=False,
)
label_dictionary = corpus.make_label_dictionary(label_type="topic")
```

Memory modes:

- `"full"`: keep parsed `Sentence` objects in memory for speed.
- `"partial"`: keep raw lines and parse on access; a good default for larger local corpora.
- `"disk"`: store offsets and re-read from disk; lower memory and slower access.

Useful knobs include `label_name_map`, `skip_labels`, `allow_examples_without_labels`, `truncate_to_max_tokens`, `truncate_to_max_chars`, and `filter_if_longer_than`.

## CSVClassificationCorpus: CSV or TSV classification

Use `CSVClassificationCorpus` when labels and text live in explicit columns.

```python
from flair.datasets import CSVClassificationCorpus

corpus = CSVClassificationCorpus(
    data_folder="data/news_csv",
    column_name_map={0: "text", 1: "label_topic", 2: "label_source"},
    label_type="topic",
    train_file="train.csv",
    dev_file="dev.csv",
    test_file="test.csv",
    skip_header=True,
    delimiter=",",
    sample_missing_splits=False,
)
```

Rules:

- Map one or more text columns to `"text"`; they are concatenated for the document.
- Map label columns to names starting with `"label"`.
- Use `"pair"` columns for paired sentence classification; the reader creates `DataPair` objects.
- `no_class_label` skips a sentinel label value.
- Pass CSV dialect parameters such as `delimiter`, `quotechar`, or `escapechar` for non-standard files.

## CoNLL-U and Universal Dependencies

Use `UniversalDependenciesCorpus` for local CoNLL-U files. Prepared UD constructors are convenient but download-capable unless cache state is verified.

```python
from flair.datasets import UniversalDependenciesCorpus

corpus = UniversalDependenciesCorpus(
    data_folder="data/ud_english",
    train_file="train.conllu",
    dev_file="dev.conllu",
    test_file="test.conllu",
    in_memory=True,
    split_multiwords=True,
)
upos_dictionary = corpus.make_label_dictionary(label_type="upos")
```

The CoNLL-U reader creates layers such as `lemma`, `upos`, `pos`, `dependency`, and morphological feature labels. If `split_multiwords=False`, multiword surface tokens are kept and component rows are skipped. Keep the setting consistent across experiments.

## Prepared Flair datasets

Prepared constructors such as `CONLL_03`, `WNUT_17`, `UD_ENGLISH`, or document-classification datasets are useful for public benchmarks, but they can download or unpack resources when data is missing. Treat them as not safe for no-download runs unless cache state is already proven.

The bundled NER CLI lists NER-style dataset class names without instantiating them:

```bash
python scripts/fine_tune_ner.py --list-datasets
```

Pass `--allow-downloads` before using `--dataset-name` for real training.

## MultiCorpus: train over several corpora

Use `MultiCorpus` when a model should train over several compatible corpora.

```python
from flair.data import MultiCorpus

multi = MultiCorpus([english_corpus, german_corpus], task_ids=["en", "de"])
label_dictionary = multi.make_label_dictionary(label_type="upos")
```

Good use cases:

- Multilingual tagging with the same label layer across languages.
- Multi-domain NER with shared labels.
- Multitask preparation when combined with `make_multitask_model_and_corpus(...)` or `MultitaskModel` recipes.

Check label-schema compatibility before merging. A shared layer name such as `"ner"` can hide incompatible BIO schemas or domain-specific labels.

## Custom local split files

Most readers can auto-detect splits, but explicit names are safer for reproducibility:

```python
corpus = ColumnCorpus(
    "data/custom_ner",
    {0: "text", 1: "ner"},
    train_file="train.gold.txt",
    dev_file="validation.gold.txt",
    test_file="heldout.gold.txt",
    autofind_splits=False,
    sample_missing_splits=False,
)
```

If only train data is available, make a deliberate choice:

- `sample_missing_splits=False`: fail or leave missing splits explicit; safest for benchmark reporting.
- `sample_missing_splits=True`: let supported readers derive missing splits for experiments.
- String modes such as `"only_dev"`: possible in some paths, but verify in the active installed version before relying on them.

## Downsampling and smoke corpora

Use `Corpus.downsample(...)` to make a fast smoke run:

```python
small = corpus.downsample(percentage=0.05, random_seed=13)
```

Record whether train/dev/test were downsampled and do not compare downsampled metrics to full-corpus metrics. Prefer deterministic file subsets for final regression cases.

## Label dictionary checklist

Before constructing a model, record:

- Label type string and whether it is token, span, document, relation, or span-classification level.
- Number of labels and whether `<unk>` was added.
- Whether dev/test labels were included.
- A few sample dictionary items.
- Whether label schemas match across all corpora or shards.

Typical calls:

```python
ner_dict = corpus.make_label_dictionary("ner", add_unk=False)
pos_dict = corpus.make_label_dictionary("upos")
class_dict = corpus.make_label_dictionary("topic")
nel_dict = corpus.make_label_dictionary("nel", add_unk=True)
relation_dict = corpus.make_label_dictionary("relation", add_unk=False)
```

If the dictionary is empty or contains unrelated layers, the corpus format, `column_format`, `label_type`, or label-column naming is probably wrong.
