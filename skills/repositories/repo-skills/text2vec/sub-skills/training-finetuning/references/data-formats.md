# Data Formats

Use the validators in `../scripts/` before calling any training API. They use only the Python standard library and never download models or datasets.

```bash
python scripts/validate_text_matching_data.py --input-file train.jsonl --format auto --task cosent
python scripts/validate_text_matching_data.py --input-file train.tsv --format tsv --task text-matching
python scripts/validate_bge_jsonl.py --input-file bge_train.jsonl --train-group-size 8
```

## Text-matching and CoSENT pair data

The pair loaders accept either TSV or JSONL. Every logical row needs two texts and one numeric label.

### TSV

Three tab-separated fields, no header:

```text
sentence one<TAB>sentence two<TAB>label
如何更换花呗绑定银行卡<TAB>花呗更改绑定银行卡<TAB>1
一个女孩在给她的头发做发型。<TAB>一个女孩在梳头。<TAB>5
```

If a text itself contains a tab, the built-in loaders see more than three columns and skip the row. Normalize or escape tabs before training.

### JSONL

Each line is a JSON object with one of these field-pair schemas:

```jsonl
{"text1":"如何更换花呗绑定银行卡","text2":"花呗更改绑定银行卡","label":1}
{"sentence1":"一个女孩在给她的头发做发型。","sentence2":"一个女孩在梳头。","label":5}
```

Loader rules:
- Per row, `text1`/`text2` is checked first, then `sentence1`/`sentence2`.
- Mixed files are allowed: one row may use `text1`/`text2` and another may use `sentence1`/`sentence2`.
- A row with neither complete pair is skipped by the package loader. Validate first to avoid silent row loss.
- If a row has both schemas, `text1`/`text2` is the effective pair.

## Label handling

| Training path | Label type | Important conversion |
|---|---|---|
| `SentenceBertModel` and `BertMatchModel` with local files | Class ids, cast with `int(label)` | File paths containing `STS` convert train labels to binary with `int(score > 2.5)`. Other filenames pass integer labels through. |
| `SentenceBertModel` and `BertMatchModel` with Hugging Face datasets | Class ids from the named dataset | STS train labels are binarized with `label > 2.5`; validation/test labels are kept for metric computation. |
| `CosentModel` with local files | Numeric scores, cast with `float(label)` before any STS heuristic | File paths containing `STS` convert labels to binary with `int(score > 2.5)` before flattening. If you want raw 0-5 ranking scores, avoid the `STS` filename heuristic or use a custom loader. |
| `CosentModel` with Hugging Face datasets | Dataset labels used as scores | The CoSENT Hugging Face train adapter flattens labels as provided. |

Practical implications:
- Binary labels `0` and `1` work for all pair-training paths.
- STS-style scores `0` through `5` are fine for CoSENT ranking, but the local-file loaders binarize them when the input path contains `STS`.
- `SentenceBertModel` and `BertMatchModel` default to `num_classes=2`; non-binary labels require constructing the model with a matching `num_classes` or pre-converting labels.
- Text-matching test loaders do not binarize labels, so Spearman/Pearson evaluation can still compare continuous STS scores even when training labels were binary.

## CoSENT flattening

CoSENT local-file training starts from pair rows but trains over flattened `(text, score)` records.

Input JSONL row:

```json
{"text1":"a","text2":"b","label":1.0}
```

Effective CoSENT train list:

```python
[("a", 1.0), ("b", 1.0)]
```

That means each valid pair doubles the number of CoSENT training items. Labels represent relative ranking/similarity scores across texts inside a batch.

## BGE JSONL triples

BGE fine-tuning uses contrastive query/passage groups. Each line must be:

```jsonl
{"query":"一个男人正在往锅里倒油。","pos":["一个男人正在往锅里倒油。"],"neg":["厨师往锅里倒油。","一个人倒汽油。","配有木制家具的优雅餐厅。"]}
```

Required fields:
- `query`: non-empty string.
- `pos`: non-empty list of positive passage strings.
- `neg`: non-empty list of negative passage strings.

Sampling behavior:
- `BgeTrainDataset` selects one positive at random from `pos`.
- It selects `train_group_size - 1` negatives from `neg`.
- If a row has fewer negatives than `train_group_size - 1`, the negative list is repeated and sampled so the group is filled. This is valid but reduces negative diversity; the BGE validator warns about it.

Length controls:
- `BgeModel(max_seq_length=...)` sets query max length.
- `BgeModel(passage_max_len=...)` sets positive/negative passage max length.
- Short query lengths such as 32 and passage lengths between 64 and 128 are the source recipe defaults; increase only if truncation loses essential meaning.

## BGE data-building recipe

The source BGE recipe builds triples in two stages:
1. Convert positive STS-style pairs into `query`/`pos` rows, then sample random negatives from the pair corpus.
2. Optionally mine hard negatives by encoding queries and a candidate corpus, searching nearest neighbors with FAISS, filtering positives/query duplicates, and topping up with random negatives when too few hard negatives remain.

Hard-negative mining is optional and may require `faiss`, a sentence encoder model, model downloads, and substantial memory. A valid random-negative JSONL file can be trained directly.
