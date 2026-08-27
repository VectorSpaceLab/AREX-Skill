# BEIR Generation API Reference

BEIR generation has two public workflow classes: `QueryGenerator` for synthetic queries plus training qrels, and `PassageExpansion` for writing an expanded corpus. Both accept a user-provided model object; BEIR's built-in wrappers are `QGenModel` for sequence-to-sequence query generation and `TILDE` for passage expansion.

## Imports

```python
from beir.generation import QueryGenerator, PassageExpansion
from beir.generation.models import QGenModel, TILDE
```

## QueryGenerator

Signature verified from BEIR 2.2.0:

```python
QueryGenerator(model, **kwargs)
```

Primary method:

```python
QueryGenerator.generate(
    corpus,
    output_dir,
    top_p=0.95,
    top_k=25,
    max_length=64,
    ques_per_passage=1,
    prefix="gen",
    batch_size=32,
    save=True,
    save_after=100000,
)
```

Input `corpus` is the standard BEIR corpus dictionary:

```python
{
    "doc1": {"title": "Document title", "text": "Document body"},
}
```

`QueryGenerator` converts the corpus dictionary into a list ordered by document id insertion order, calls `model.generate(...)` by batch, asserts the returned query count equals `batch_size_for_this_batch * ques_per_passage`, de-duplicates generated strings within each passage with `set(q.strip() ...)`, then writes synthetic query ids named `genQ1`, `genQ2`, and so on.

### Query Model Protocol

A compatible query model must implement:

```python
def generate(self, corpus, ques_per_passage, max_length, top_p, top_k):
    return ["query text", ...]
```

Arguments passed by BEIR:

| Argument | Shape | Meaning |
| --- | --- | --- |
| `corpus` | `list[dict[str, str]]` | Batch of documents with `title` and `text`. |
| `ques_per_passage` | `int` | Number of raw sequences expected for each passage before de-duplication. |
| `max_length` | `int` | Maximum generated sequence length forwarded to the model. |
| `top_p` | `float` | Nucleus sampling parameter. |
| `top_k` | `int` | Top-k sampling parameter. |

The returned list length must be exactly `len(corpus) * ques_per_passage`. BEIR asserts this before writing files.

### Query Output Layout

For `prefix="gen"` and `output_dir="dataset"`, `QueryGenerator.save(...)` writes:

```text
dataset/
  gen-queries.jsonl
  gen-qrels/
    train.tsv
```

`gen-queries.jsonl` uses BEIR query JSONL rows with `_id` and `text`. `gen-qrels/train.tsv` has the standard header `query-id<TAB>corpus-id<TAB>score` and score `1` for each generated query's source document.

Use the data-loading sub-skill to load generated query/qrels files:

```python
from beir.datasets.data_loader import GenericDataLoader
corpus, queries, qrels = GenericDataLoader(data_folder="dataset", prefix="gen").load(split="train")
```

Prefix mode changes only query and qrels paths. It still reads `corpus.jsonl` unless you pass a custom `corpus_file`.

### Incremental Save Behavior

`save_after` controls periodic rewrites of the full accumulated generated data. When `len(self.queries) % save_after == 0` and at least `save_after` queries have accumulated, BEIR calls `save(...)` before continuing. The final save always runs at the end. The `save` argument exists in the signature but is not used in BEIR 2.2.0; generation still saves output files.

## Multi-Process Query Generation

Primary method:

```python
QueryGenerator.generate_multi_process(
    corpus,
    pool,
    output_dir,
    top_p=0.95,
    top_k=25,
    max_length=64,
    ques_per_passage=1,
    prefix="gen",
    batch_size=32,
    chunk_size=None,
)
```

`QueryGenerator` delegates all parallel work to `model.generate_multi_process(...)`, then applies the same query-count assertion, per-document de-duplication, `genQ*` id assignment, and output layout as single-process generation.

A compatible multi-process model must implement:

```python
def generate_multi_process(
    self,
    corpus,
    pool,
    ques_per_passage,
    max_length,
    top_p,
    top_k,
    chunk_size=None,
    batch_size=32,
):
    return ["query text", ...]
```

The `pool` object is model-defined. BEIR's `QGenModel.start_multi_process_pool()` returns a dictionary with `input`, `output`, and `processes` keys.

## QGenModel

Signature verified from BEIR 2.2.0:

```python
QGenModel(model_path, gen_prefix="", use_fast=True, device=None, **kwargs)
```

`QGenModel` downloads/loads a Hugging Face tokenizer with `AutoTokenizer.from_pretrained(model_path)` and a sequence-to-sequence model with `AutoModelForSeq2SeqLM.from_pretrained(model_path)`. It uses CUDA when available unless `device` is provided.

`QGenModel.generate(...)` builds each input as:

```python
gen_prefix + doc["title"] + " " + doc["text"]
```

It calls the Transformers model with sampling enabled and `num_return_sequences=ques_per_passage`, then returns decoded strings. If `temperature` is provided to `QGenModel.generate(...)` directly, it uses temperature sampling instead of top-p; `QueryGenerator.generate(...)` does not expose `temperature`.

Multi-process helpers:

```python
pool = model.start_multi_process_pool(target_devices=None)
model.stop_multi_process_pool(pool)
```

If `target_devices` is omitted, BEIR uses all CUDA devices or four CPU workers when CUDA is unavailable. Use an `if __name__ == "__main__":` guard around multi-process scripts.

## PassageExpansion

Signature verified from BEIR 2.2.0:

```python
PassageExpansion(model, **kwargs)
```

Primary method:

```python
PassageExpansion.expand(
    corpus,
    output_dir,
    top_k=200,
    max_length=350,
    prefix="gen",
    batch_size=32,
    sep=" ",
)
```

`PassageExpansion` calls `model.generate(corpus=batch, max_length=max_length, top_k=top_k)` and expects one expansion string per input document. It writes a new corpus dictionary where each row preserves the original `title` and appends `sep + expansion` to the original `text`.

### Expansion Model Protocol

A compatible expansion model must implement:

```python
def generate(self, corpus, max_length, top_k):
    return ["expansion tokens", ...]
```

Arguments passed by BEIR:

| Argument | Shape | Meaning |
| --- | --- | --- |
| `corpus` | `list[dict[str, str]]` | Batch of documents with `title` and `text`. |
| `max_length` | `int` | Maximum tokenized passage length forwarded to the model. |
| `top_k` | `int` | Number of expansion terms requested per passage. |

BEIR 2.2.0 does not assert expansion count. Custom expansion models should still return exactly one string per input document to avoid index errors or missing expanded documents.

### Expansion Output Layout

For `prefix="gen"` and `output_dir="dataset"`, `PassageExpansion.save(...)` writes:

```text
dataset/
  gen-corpus.jsonl
```

To load this as the active corpus, route to data-loading and pass `corpus_file="gen-corpus.jsonl"`. Prefix mode alone does not select a prefixed corpus file.

## TILDE

Signature verified from BEIR 2.2.0:

```python
TILDE(model_path, gen_prefix="", use_fast=True, device=None, **kwargs)
```

`TILDE` loads `BertTokenizer.from_pretrained("bert-base-uncased")`, `BertLMHeadModel.from_pretrained(model_path)`, and NLTK English stopwords. It encodes each input as `gen_prefix + title + " " + text`, scores vocabulary terms from the first position, removes stopwords, punctuation-like tokens, tokens already present in the passage, and the `##s` token, then decodes the top expansion terms.

TILDE requires Transformers, PyTorch, model files, and the NLTK `stopwords` corpus. It is best treated as a real-model workflow, not a smoke-test dependency.

## Source Evidence

This reference distills these BEIR package files as provenance evidence: `beir/generation/generate.py`, `beir/generation/models/auto_model.py`, `beir/generation/models/tilde.py`, `beir/util.py`, `beir/datasets/data_loader.py`, and the generation example scripts under `examples/generation/`.
