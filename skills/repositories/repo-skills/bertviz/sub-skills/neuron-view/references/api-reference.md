# API reference

## Public functions

### `bertviz.neuron_view.show`

```python
show(
    model,
    model_type,
    tokenizer,
    sentence_a,
    sentence_b=None,
    display_mode='dark',
    layer=None,
    head=None,
    html_action='view',
)
```

Use `show` when the desired result is the interactive neuron visualization. It computes the attention/query/key payload by calling `get_attention(..., include_queries_and_keys=True)`, builds the layer/head/filter controls, loads BertViz's packaged `neuron_view.js`, and either displays the visualization or returns an `IPython.display.HTML` object.

Parameter notes:

- `model`: a vendored `bertviz.transformers_neuron_view` model instance that returns per-layer dictionaries containing `attn`, `queries`, and `keys`.
- `model_type`: exactly one of `bert`, `gpt2`, `xlnet`, or `roberta`.
- `tokenizer`: matching vendored tokenizer for the selected `model_type`.
- `sentence_a`: required input text.
- `sentence_b`: optional second sentence; supported for BERT and RoBERTa only.
- `display_mode`: passed to the JavaScript renderer; use `dark` or `light`.
- `layer`: optional zero-indexed initial layer selection.
- `head`: optional zero-indexed initial head selection.
- `html_action`: `view` displays in an IPython/Jupyter context; `return` returns an HTML object whose `.data` can be saved.

### `bertviz.neuron_view.get_attention`

```python
get_attention(
    model,
    model_type,
    tokenizer,
    sentence_a,
    sentence_b=None,
    include_queries_and_keys=False,
)
```

Use `get_attention` when the desired result is a Python dictionary for validation, custom inspection, or testing. It tokenizes input text, runs the vendored model in evaluation mode, slices sentence-pair blocks when applicable, formats special tokens for display, and returns JSON-serializable lists.

Valid `model_type` values are:

| `model_type` | Single sentence | Sentence pair | Notes |
| --- | --- | --- | --- |
| `bert` | Supported | Supported | Uses BERT special tokens and `token_type_ids`. |
| `gpt2` | Supported | Not supported | Sentence pairs raise `ValueError`. GPT-2 attention is causal/unidirectional. |
| `xlnet` | Supported | Not implemented | Sentence pairs raise `NotImplementedError`. `XLNetTokenizer` needs SentencePiece. |
| `roberta` | Supported | Supported | Uses RoBERTa special-token layout; no token type embeddings. |

## `show` vs `get_attention`

| Need | Use | Why |
| --- | --- | --- |
| Display in Jupyter/Colab | `show(..., html_action='view')` | Emits IPython display objects and JavaScript. |
| Save HTML | `show(..., html_action='return')` | Returns an HTML object; write `html.data`. |
| Validate tokens, partitions, probabilities, or query/key schema | `get_attention(...)` | Returns a deterministic Python structure before rendering. |
| Avoid notebook display dependencies during tests | `get_attention(...)` | Does not require a browser widget host. |
| Work with already-computed attention tensors | Not this sub-skill | Route to the `attention-views` sibling sub-skill. |

## Output schema

`get_attention` returns a dictionary keyed by attention filter names.

### Single sentence

For `sentence_b=None`, the result contains only `all`:

```python
{
    'all': {
        'attn': [...],
        'left_text': [...],
        'right_text': [...],
        # present only when include_queries_and_keys=True
        'queries': [...],
        'keys': [...],
    }
}
```

### Sentence pair

For supported sentence pairs, the result contains five filters:

```python
{
    'all': {...},  # A+B -> A+B
    'aa': {...},   # A -> A
    'ab': {...},   # A -> B
    'ba': {...},   # B -> A
    'bb': {...},   # B -> B
}
```

Each filter value has:

- `left_text`: source-token display labels, shown on the left side of the visualization.
- `right_text`: target-token display labels, shown on the right side of the visualization.
- `attn`: list of per-layer attention arrays. Each layer has shape `[num_heads, source_seq_len, target_seq_len]` after the batch dimension is removed.
- `queries`: optional list of per-layer query arrays when `include_queries_and_keys=True`. Each layer has shape `[num_heads, source_seq_len, head_vector_size]`.
- `keys`: optional list of per-layer key arrays when `include_queries_and_keys=True`. Each layer has shape `[num_heads, target_seq_len, head_vector_size]`.

For pair filters with query/key data:

| Filter | Queries slice | Keys slice | Attention block |
| --- | --- | --- | --- |
| `all` | all tokens | all tokens | all rows and columns |
| `aa` | sentence A | sentence A | A rows, A columns |
| `ab` | sentence A | sentence B | A rows, B columns |
| `ba` | sentence B | sentence A | B rows, A columns |
| `bb` | sentence B | sentence B | B rows, B columns |

Submatrices are slices of the full attention matrix; they are not renormalized. Rows of `all` should sum to one, while rows of `aa`, `ab`, `ba`, or `bb` generally sum to partial mass. Concatenating `aa` with `ab`, and `ba` with `bb`, reassembles `all` for each layer and head.

## Token partition behavior

`get_attention` performs model-specific tokenization before running the model.

### BERT

Single sentence:

```text
[CLS] tokens(sentence_a) [SEP]
```

Sentence pair:

```text
[CLS] tokens(sentence_a) [SEP] tokens(sentence_b) [SEP]
```

The BERT pair path also creates `token_type_ids`: zeros for the A span including `[CLS]` and the first `[SEP]`, ones for the B span including the final `[SEP]`.

### RoBERTa

Single sentence:

```text
[CLS] tokens(sentence_a) [SEP]
```

Sentence pair:

```text
[CLS] tokens(sentence_a) [SEP] [SEP] tokens(sentence_b) [SEP]
```

RoBERTa does not use token type embeddings in this vendored path. Its tokenizer tokens may include a leading-space marker that BertViz displays as a literal leading space.

### XLNet

Single sentence:

```text
tokens(sentence_a) [SEP] [CLS]
```

Sentence-pair inputs are explicitly not implemented in `get_attention`.

### GPT-2

Single sentence:

```text
tokens(sentence_a)
```

No special tokens are added by `get_attention`. Sentence-pair inputs are rejected before model execution.

## Display token formatting

Before returning results, BertViz replaces tokenizer boundary markers for display:

- `Ġ` and `▁` are replaced by a leading space.
- For non-GPT-2 paths, tokenizer `sep_token` is displayed as `[SEP]` and tokenizer `cls_token` is displayed as `[CLS]`.

Use the returned `left_text` and `right_text` as display labels; do not assume they are byte-for-byte tokenizer internals.
