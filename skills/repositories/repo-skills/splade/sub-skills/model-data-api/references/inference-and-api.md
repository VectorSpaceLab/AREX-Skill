# Inference and API Workflows

This reference distills safe, programmatic SPLADE inspection workflows. It avoids full training and does not require original repository files.

## Inspect an Installed SPLADE Package

Use the bundled script when the package is installed and you need versions/signatures without model downloads:

```bash
python sub-skills/model-data-api/scripts/inspect_splade_api.py --json
```

The script imports known SPLADE modules and reports class/function signatures. It does not instantiate `Splade`, `SPLADE`, or `DPR`, because constructors call HuggingFace `from_pretrained` and may download weights.

## Validate a Small Dataset Root

Use the bundled data validator against a root containing SPLADE-style subdirectories, for example `full_collection/raw.tsv`, `val_queries/raw.tsv`, `qrel/qrel.json`, or `scores/toy.json`:

```bash
python sub-skills/model-data-api/scripts/validate_splade_toy_data.py /path/to/dataset-root
```

Useful options:

```bash
python sub-skills/model-data-api/scripts/validate_splade_toy_data.py /path/to/dataset-root --json
python sub-skills/model-data-api/scripts/validate_splade_toy_data.py /path/to/dataset-root --documents full_collection --queries val_queries --qrels qrel/qrel.json --scores scores/toy.json
python sub-skills/model-data-api/scripts/validate_splade_toy_data.py /path/to/dataset-root --allow-missing
```

The validator is generic: it only uses Python standard-library modules and does not import SPLADE.

## Notebook-Style Bag-of-Expanded-Words Inspection

The original inference notebook demonstrates this concept:

1. Load a SPLADE model by model id or local checkpoint.
2. Tokenize a document.
3. Call the classic model with `d_kwargs`.
4. Find nonzero vocabulary dimensions.
5. Map vocabulary ids back to tokens and sort by weight.

Minimal pattern:

```python
import torch
from transformers import AutoTokenizer
from splade.models.transformer_rep import Splade

model_id = "naver/splade-cocondenser-ensembledistil"
model = Splade(model_id, agg="max")
model.eval()
tokenizer = AutoTokenizer.from_pretrained(model_id)
reverse_vocab = {value: key for key, value in tokenizer.vocab.items()}

text = "The Manhattan Project developed the first atomic weapons."
with torch.no_grad():
    rep = model(d_kwargs=tokenizer(text, return_tensors="pt"))["d_rep"].squeeze()
indices = torch.nonzero(rep, as_tuple=False).squeeze(-1).tolist()
weights = rep[indices].cpu().tolist()
expanded_terms = sorted(
    ((reverse_vocab[idx], round(weight, 4)) for idx, weight in zip(indices, weights)),
    key=lambda item: item[1],
    reverse=True,
)
print(expanded_terms[:25])
```

Caveats:

- This code may download model weights and tokenizer files unless `model_id` is already cached or points to a local checkpoint.
- Use `model.eval()` and `torch.no_grad()` for inspection.
- The output dimension is the tokenizer/model vocabulary size, not the number of input tokens.
- Token strings may include wordpiece prefixes such as `##`.

## Safe Offline API Smoke Pattern

If model downloads are not allowed, inspect APIs without constructing models:

```python
import inspect
from splade.models import transformer_rep
from splade.hf import args as hf_args

print(inspect.signature(transformer_rep.Splade))
print(inspect.signature(transformer_rep.SpladeDoc))
print(hf_args.ModelArguments.__dataclass_fields__.keys())
```

This is what the bundled `inspect_splade_api.py` automates.

## Classic Model Call Patterns

### Encode Documents

```python
batch = tokenizer(["doc text"], padding=True, truncation=True, return_tensors="pt")
out = model(d_kwargs=batch)
doc_vectors = out["d_rep"]
```

### Encode Queries

```python
batch = tokenizer(["query text"], padding=True, truncation=True, return_tensors="pt")
out = model(q_kwargs=batch)
query_vectors = out["q_rep"]
```

### Score Aligned Query/Document Pairs

```python
q_tokens = tokenizer(["query"], return_tensors="pt")
d_tokens = tokenizer(["document"], return_tensors="pt")
out = model(q_kwargs=q_tokens, d_kwargs=d_tokens)
score = out["score"]
```

### Score Query Batch Against Document Batch

```python
out = model(q_kwargs=q_tokens, d_kwargs=d_tokens, score_batch=True)
score_matrix = out["score"]
```

### Score One Query With Multiple Negatives

```python
out = model(q_kwargs=q_tokens, d_kwargs=d_tokens, nb_negatives=4)
negative_scores = out["score"]
```

## HF Trainer Model Call Pattern

HF Trainer models use a different input layout. For `n_negatives=2`, each training group has one query, one positive document, and two negatives. After tokenization, the wrapper reshapes the flat batch into groups:

```python
from splade.hf.models import SPLADE

model = SPLADE(model_type_or_dir="local-or-hf-model", tokenizer=tokenizer, n_negatives=2)
queries, docs = model(input_ids=input_ids, attention_mask=attention_mask)
# queries shape: (batch, 1, vocab_size)
# docs shape: (batch, 3, vocab_size)
```

Use this only to understand model behavior. Command execution and training setup belong to `hf-training-reranking`.

## Small In-Memory Inverted Index Pattern

For unit-scale reasoning, `IndexDictOfArray` can be used without a path:

```python
import numpy as np
from splade.indexing.inverted_index import IndexDictOfArray

index = IndexDictOfArray()
index.add_batch_document(
    row=np.array([0, 0, 1], dtype=np.int32),
    col=np.array([10, 20, 10], dtype=np.int32),
    data=np.array([0.8, 0.2, 0.5], dtype=np.float32),
    n_docs=2,
)
print(index.nb_docs())
print(index.index_doc_id[10])
```

Full retrieval uses numba and evaluator classes; route end-to-end index/retrieve execution to `hydra-pipelines`.

## Interpreting Sparse Vectors

- SPLADE representations are dense tensors shaped `(batch, vocab_size)` with many zeros.
- Nonzero coordinates correspond to tokenizer vocabulary ids, not terms from a separate learned dictionary.
- Values are positive weights after `log(1 + relu(logits))` and aggregation.
- `SpladeTopK` zeros all but the largest `top_d` or `top_q` values.
- `SpladeLexical` can multiply SPLADE activations by a cleaned bag-of-words mask so only input lexical terms survive on the configured side.
