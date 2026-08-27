# ESM Model Embeddings API Reference

This reference summarizes the stable embedding-related APIs verified for `fair-esm` 2.0.1. PyTorch is required for all model execution.

## Model Loading

| Goal | API | Notes |
| --- | --- | --- |
| Load by public model name or local `.pt` path | `esm.pretrained.load_model_and_alphabet(model_name_or_path)` | Public names download model weights through Torch Hub. Paths ending in `.pt` use local loading. |
| Load a local checkpoint explicitly | `esm.pretrained.load_model_and_alphabet_local(model_location)` | For contact prediction, a sibling `*-contact-regression.pt` file is expected for models that use regression weights. |
| Load a named model function | `esm.pretrained.esm2_t33_650M_UR50D()` | Returns `(model, alphabet)`. Model functions are convenient but may download weights. |
| Build an alphabet without weights | `esm.Alphabet.from_architecture(name)` | Valid architectures include `ESM-1`, `ESM-1b`, `MSA Transformer`, and `msa_transformer`. |

Common embedding model names:

| Family | Example names | Typical use |
| --- | --- | --- |
| ESM-2 | `esm2_t6_8M_UR50D`, `esm2_t12_35M_UR50D`, `esm2_t30_150M_UR50D`, `esm2_t33_650M_UR50D`, `esm2_t36_3B_UR50D`, `esm2_t48_15B_UR50D` | General sequence embeddings and contacts; prefer smaller models for CPU/smoke tests. |
| ESM-1b | `esm1b_t33_650M_UR50S` | Legacy single-sequence embeddings and contacts. |
| ESM-1v | `esm1v_t33_650M_UR90S_1` through `_5` | Variant-effect workflows use these, but raw embeddings can be extracted like other single-sequence models. |
| MSA Transformer | `esm_msa1b_t12_100M_UR50S` | MSA embeddings/contacts through Python API only; not supported by `esm-extract`. |

Do not route `esmfold_*` or `esm_if1_*` models through this sub-skill unless the user only needs their language-model-style loader behavior. Use the structure-prediction or inverse-folding sibling routes for their primary tasks.

## Single-Sequence Tokenization

```python
import torch
import esm

model, alphabet = esm.pretrained.load_model_and_alphabet("esm2_t33_650M_UR50D")
model.eval()
batch_converter = alphabet.get_batch_converter(truncation_seq_length=1022)

data = [
    ("protein1", "MKTVRQERLKSIVRIL"),
    ("masked", "KALTA<mask>ISQP"),
    ("spaced", "K A <mask> I S Q"),
]
labels, seqs, tokens = batch_converter(data)
```

Important details:

- Raw batches are sequences of `(label, sequence)` tuples.
- `<mask>` is recognized as a special token.
- Space-separated residues are accepted because the tokenizer splits normal text while preserving special tokens.
- `truncation_seq_length` trims encoded residues before adding BOS/EOS tokens.
- Padding tokens use `alphabet.padding_idx`; non-padding lengths are commonly computed with `(tokens != alphabet.padding_idx).sum(1)`.
- For ESM-1b and ESM-2-style alphabets, token index `0` is the beginning-of-sequence token and residue tokens start at index `1`.

## Representation Calls

```python
with torch.no_grad():
    out = model(tokens, repr_layers=[0, 32, 33], return_contacts=True)

logits = out["logits"]
layer_33 = out["representations"][33]
contacts = out["contacts"]
```

Output keys:

| Key | Present when | Shape pattern |
| --- | --- | --- |
| `logits` | Always | Single-sequence models: `(batch, tokens, vocab)` |
| `representations` | Always, but only requested layers are populated | Layer map: `layer_index -> tensor`; single-sequence tensors are `(batch, tokens, hidden_dim)` |
| `attentions` | `return_contacts=True` or `need_head_weights=True` | Single-sequence attentions include layer/head/token dimensions. |
| `contacts` | `return_contacts=True` | Single-sequence contact maps are `(batch, residues, residues)` after contact head processing. |

Layer selection rules:

- `0` is the embedding layer before transformer blocks.
- Positive indices select transformer layers up to `model.num_layers`.
- `model.num_layers` is the final layer for most embedding use.
- The `esm-extract` CLI accepts negative indices such as `-1` and normalizes them to the final layer; raw Python model calls expect valid non-negative layer indices.

Mean pooling example:

```python
batch_lens = (tokens != alphabet.padding_idx).sum(1)
token_representations = out["representations"][model.num_layers]
sequence_representations = []
for row, tokens_len in enumerate(batch_lens):
    sequence_representations.append(token_representations[row, 1 : tokens_len - 1].mean(0))
```

For ESM-1b/ESM-2 alphabets, exclude BOS at token `0` and EOS/padding at the end when averaging residue embeddings.

## MSA Transformer API

MSA Transformer uses the same loader family but a different input shape.

```python
import torch
import esm

model, alphabet = esm.pretrained.esm_msa1b_t12_100M_UR50S()
model.eval()
batch_converter = alphabet.get_batch_converter()
msa = [
    ("seq1", "MKTVRQG"),
    ("seq2", "MKTVRQA"),
    ("seq3", "MKTVRQS"),
]
labels, strs, tokens = batch_converter(msa)

with torch.no_grad():
    out = model(tokens, repr_layers=[12], return_contacts=True)
```

MSA details:

- `alphabet.use_msa` is true for MSA Transformer alphabets, so `get_batch_converter()` returns `MSABatchConverter`.
- A single MSA can be passed as a sequence of `(label, aligned_sequence)` tuples; the converter wraps it into batch size `1`.
- A batch of MSAs is a sequence where each item is one MSA.
- Tokens are 3D: `(batch, alignments, tokens)`.
- All sequences within one MSA must have equal aligned length; otherwise the converter raises `RuntimeError: Received unaligned sequences for input to MSA...`.
- MSA Transformer can return `row_attentions`, `col_attentions`, and `contacts` when requested.
- `model.max_tokens_per_msa_(value)` can tune automatic attention batching for large MSAs under `torch.no_grad()`.

## FASTA Utilities

`esm.FastaBatchedDataset.from_file(fasta_file)` reads ordinary FASTA into labels and sequence strings. It asserts that all labels are unique.

```python
from esm import FastaBatchedDataset

dataset = FastaBatchedDataset.from_file("input.fasta")
batches = dataset.get_batch_indices(toks_per_batch=4096, extra_toks_per_seq=1)
```

`esm.data.read_fasta(path, keep_gaps=True, keep_insertions=True, to_upper=False)` yields `(description, sequence)` records and is useful when you need custom FASTA preprocessing before tokenization.
